"""Smart HS resolution — turns ANY product name (local names, regional spellings, typos:
"brinjal", "bringle", "bhindi", "okra", "ladies finger") into a valid WCO HS6 code.

Tiers, cheapest first:
  1. the HS6 directory in Mongo (exact digits / description match / per-word match)
  2. an LLM classifier (canonical English trade name + candidate HS6 codes, validated
     against the directory — never a made-up code)
  3. a web-grounded lookup (Gemini + Google Search) when the classifier draws a blank

Only the classification is AI/web derived; every duty, demand and buyer figure downstream
still comes from WITS / OEC / the buyer registry for the validated HS6 code.
Results (including misses) are cached in Mongo so each product name is resolved once.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta

from core import db
import trade_intel

logger = logging.getLogger("hs_resolver")

CACHE = db.hs_resolver_cache
HIT_TTL = timedelta(days=180)
MISS_TTL = timedelta(days=3)
STOPWORDS = {"fresh", "dried", "frozen", "whole", "powder", "organic", "raw", "export", "quality",
             "grade", "premium", "indian", "best", "bulk", "natural", "product", "products"}


def _key(product, hs):
    return f"{(product or '').strip().lower()}|{re.sub(r'[^0-9]', '', hs or '')}"


async def _valid_hs6(code):
    """A code only counts when it exists in the HS6 directory."""
    c = re.sub(r"\D", "", code or "")[:6]
    if len(c) < 6:
        return None
    doc = await trade_intel.HS_MAP_COLL.find_one({"hs6": c}, {"_id": 0, "hs6": 1, "desc": 1})
    return {"hs6": doc["hs6"], "description": doc.get("desc", "")} if doc else None


NEGATIVE_DESC = ("except", "other than", "n.e.s", "nesoi")


def _rank(term, rows):
    """Whole-word matches first, exclusion headings ("except rice", "other than…") last."""
    t = term.lower()

    def score(r):
        d = (r.get("description") or "").lower()
        return (0 if re.search(rf"\b{re.escape(t)}", d) else 1,
                1 if any(x in d for x in NEGATIVE_DESC) else 0,
                d.find(t) if t in d else 99,
                len(d))
    return sorted(rows, key=score)


async def _term(term):
    rows = await trade_intel.hs_search(term, limit=12)
    if not rows:
        return None
    best = _rank(term, rows)[0]
    return {"hs6": best["hs6"], "description": best["description"], "via": "directory"}


async def _local(product):
    """Directory search on the full phrase, then on each meaningful word."""
    hit = await _term(product) if product else None
    if hit:
        return hit
    words = [w for w in re.findall(r"[a-z]{4,}", (product or "").lower()) if w not in STOPWORDS]
    for word in sorted(words, key=len, reverse=True):
        hit = await _term(word)
        if hit:
            return hit
    return None


def _chat(system, provider, model, session):
    from emergentintegrations.llm.chat import LlmChat
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return None
    return LlmChat(api_key=key, session_id=session, system_message=system).with_model(provider, model)


def _json(raw):
    raw = re.sub(r"^```(?:json)?|```$", "", (raw or "").strip(), flags=re.M).strip()
    try:
        return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception:
        return {}


CLASSIFY_SYSTEM = (
    "You are a customs classification expert. Given a product name in any language, dialect or "
    "misspelling (Indian/African/Middle-East local names included), identify the commodity and "
    "classify it under the WCO Harmonized System 2022. Return STRICT JSON only: "
    '{"canonical": "English trade name", "aliases": ["local names"], '
    '"hs6": ["most likely HS6 code", "second", "third"], "heading": "official HS heading text of the first code", '
    '"note": "one short sentence on the classification"}. '
    "hs6 must be real 6-digit HS-2022 codes, most likely first. If the input is not a tradable good, "
    'return {"canonical": null, "hs6": []}.'
)


async def _ai_classify(product):
    chat = _chat(CLASSIFY_SYSTEM, os.environ.get("BRAIN_AI_PROVIDER", "openai"),
                 os.environ.get("BRAIN_AI_MODEL", "gpt-5.4-mini"), f"hs-classify-{abs(hash(product)) % 10**9}")
    if not chat:
        return {}
    from emergentintegrations.llm.chat import UserMessage
    try:
        return _json(await chat.send_message(UserMessage(text=f"PRODUCT: {product}")))
    except Exception as exc:
        logger.warning("hs classify failed for %r: %s", product, exc)
        return {}


WEB_SYSTEM = (
    "You are a customs classification expert with live web access. Search the web for the product "
    "name given (it may be a local or misspelled name) and determine the commodity and its WCO HS-2022 "
    "classification. Return STRICT JSON only: "
    '{"canonical": "English trade name", "aliases": [], "hs6": ["code", "code"], '
    '"heading": "official HS heading text of the first code", "note": "one sentence", '
    '"sources": ["url", "url"]}. hs6 must be real 6-digit HS-2022 codes.'
)


async def _web_classify(product):
    chat = _chat(WEB_SYSTEM, "gemini", os.environ.get("HS_WEB_MODEL", "gemini-2.5-flash"),
                 f"hs-web-{abs(hash(product)) % 10**9}")
    if not chat:
        return {}
    from emergentintegrations.llm.chat import UserMessage
    try:
        chat = chat.with_tools([{"googleSearch": {}}])
        return _json(await chat.send_message(UserMessage(text=f"PRODUCT NAME: {product}. What is it and what HS code applies?")))
    except Exception as exc:
        logger.warning("hs web lookup failed for %r: %s", product, exc)
        return {}


GENERIC = {"fresh", "chilled", "frozen", "dried", "other", "others", "vegetable", "vegetables", "fruit",
           "fruits", "prepared", "preserved", "products", "product", "articles", "parts", "mixtures",
           "including", "elsewhere", "specified", "whether", "seeds", "plants", "edible", "food"}
BAD_CANONICAL = ("unidentif", "unknown", "not a ", "no product", "invalid", "n/a", "cannot")


def _usable(out):
    c = (out.get("canonical") or "").strip()
    return bool(out.get("hs6")) and bool(c) and len(c) < 60 and not any(b in c.lower() for b in BAD_CANONICAL)


def _plausible(canonical, ai_desc, dir_desc):
    """Guard against a valid-but-wrong code: the directory heading should mention the
    commodity, the AI's own heading text, or be a residual ("other…") heading."""
    d = (dir_desc or "").lower()
    if not d or any(m in d for m in ("other", "n.e.c", "n.e.s", "nesoi", "not elsewhere")):
        return True
    terms = [t for t in re.findall(r"[a-z]{4,}", f"{canonical or ''} {ai_desc or ''}".lower())
             if t not in STOPWORDS and t not in GENERIC]
    return any(t in d for t in terms) or not terms


async def _residual(code):
    """The "other / n.e.c." line inside the same 4-digit heading — the safe landing spot
    for commodities the HS does not name explicitly (okra, most local vegetables)."""
    head = re.sub(r"\D", "", code or "")[:4]
    if len(head) < 4:
        return None
    rows = await trade_intel.HS_MAP_COLL.find(
        {"hs6": {"$regex": f"^{head}"}, "desc": {"$regex": "n\\.e\\.c|n\\.e\\.s|nesoi|other", "$options": "i"}},
        {"_id": 0, "hs6": 1, "desc": 1}).to_list(10)
    if not rows:
        return None
    best = sorted(rows, key=lambda r: r["hs6"], reverse=True)[0]
    return {"hs6": best["hs6"], "description": best.get("desc", "")}


async def _from_ai(out, via, product):
    """Validate AI candidates against the directory; fall back to searching the canonical name."""
    if not _usable(out):
        return None
    canonical = out.get("canonical")
    for code in (out.get("hs6") or [])[:4]:
        v = await _valid_hs6(code)
        if v and _plausible(canonical, out.get("heading"), v["description"]):
            return {**v, "via": via, "canonical": canonical,
                    "aliases": out.get("aliases") or [], "note": out.get("note") or "",
                    "sources": out.get("sources") or []}
    for name in [canonical]:
        if name and name.strip().lower() != (product or "").strip().lower():
            hit = await _local(name)
            if hit:
                return {**hit, "via": f"{via}+directory", "canonical": canonical,
                        "aliases": out.get("aliases") or [], "note": out.get("note") or "",
                        "sources": out.get("sources") or []}
    for code in (out.get("hs6") or [])[:2]:
        res = await _residual(code)
        if res:
            return {**res, "via": f"{via}+heading", "canonical": canonical, "aliases": out.get("aliases") or [],
                    "note": out.get("note") or "", "sources": out.get("sources") or []}
    first = await _valid_hs6((out.get("hs6") or [""])[0])
    if first:
        return {**first, "via": via, "canonical": canonical, "aliases": out.get("aliases") or [],
                "note": out.get("note") or "", "sources": out.get("sources") or []}
    return None


async def resolve(product: str | None, hs: str | None = None, allow_ai: bool = True) -> dict:
    """{"hs6", "description", "canonical", "via", "note", "sources"} — hs6 is None when unresolvable."""
    product = (product or "").strip()
    hs = (hs or "").strip()
    if not product and not hs:
        return {"hs6": None, "via": "empty"}

    if hs:
        direct = await _valid_hs6(hs)
        if direct:
            return {**direct, "via": "code", "canonical": None, "note": "", "sources": []}
        code = re.sub(r"\D", "", hs)[:6]
        if len(code) == 6:
            return {"hs6": code, "description": "", "via": "code", "canonical": None, "note": "", "sources": []}

    cache_id = _key(product, hs)
    cached = await CACHE.find_one({"_id": cache_id})
    if cached:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cached["at"])
        if age < (HIT_TTL if cached["result"].get("hs6") else MISS_TTL):
            return cached["result"]

    phrase = await _term(product)
    result = {**phrase, "canonical": None, "note": "", "sources": []} if phrase else None
    if not result and allow_ai:
        out = await _ai_classify(product)
        result = await _from_ai(out, "ai", product) if out else None
        if not result:
            web = await _web_classify(product)
            result = await _from_ai(web, "web", product) if web else None
    if not result:
        word = await _local(product)
        result = {**word, "canonical": None, "note": "", "sources": []} if word else None
    if not result:
        result = {"hs6": None, "via": "unresolved", "canonical": None, "note": "", "sources": []}

    await CACHE.update_one({"_id": cache_id},
                           {"$set": {"result": result, "at": datetime.now(timezone.utc).isoformat(), "query": product}},
                           upsert=True)
    return result


async def resolve_hs6(product: str | None, hs: str | None = None) -> str | None:
    return (await resolve(product, hs)).get("hs6")


async def search(q: str, limit: int = 10) -> list:
    """Directory search with an AI/web fallback so pickers find local names too."""
    rows = await trade_intel.hs_search(q, limit)
    if rows or len(re.sub(r"[^a-zA-Z]", "", q or "")) < 4:
        return rows
    r = await resolve(q)
    if not r.get("hs6"):
        return []
    return [{"hs6": r["hs6"], "description": r.get("description") or r.get("canonical") or q,
             "via": r.get("via"), "canonical": r.get("canonical")}]
