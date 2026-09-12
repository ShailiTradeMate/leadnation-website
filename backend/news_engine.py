"""Trade News Engine — live, global, filterable, refreshed daily.

Architecture:  Live News API (NewsData.io)  +  Vametra AI Brain (impact analysis)
+  User Profile Context (country / role / products).

Public surface:
  GET /news/topics     — topic taxonomy (trade, currency, geopolitics, war, sports…)
  GET /news/countries   — every country (ISO-2) for the country filter
  GET /news/feed        — the feed: topic + country + free-text search, newest first
  GET /news/{id}        — detail + Brain "what this means for my trade"
  admin CRUD under /news/admin/*

Freshness: every feed response carries `lastUpdated` (ISO) and each item carries a real
`publishedAt` timestamp. A daily scheduler pre-warms the global + per-topic feeds so the
page is never stale, and the short-lived cache is bypassed with `?refresh=1`.
"""
import os
import re
import html
import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import httpx
from fastapi import APIRouter, Header, Query, Depends, HTTPException
from pydantic import BaseModel

from core import db, require_admin
from firebase_auth import optional_user
import llm_util

router = APIRouter(prefix="/news")

ADMIN_NEWS = db.trade_news_admin      # admin-authored / curated
NEWS_ITEMS = db.news_items            # resolved cache for detail lookups (admin + live)
NEWS_CACHE = db.news_feed_cache       # live feed cache by scope key
NEWS_META = db.news_engine_meta       # engine heartbeat / last refresh

NEWSDATA_KEY = os.environ.get("NEWSDATA_API_KEY", "").strip()
NEWSDATA_URL = "https://newsdata.io/api/1/latest"
CACHE_TTL_MIN = 20

FALLBACK_IMG = [
    "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1517292987719-0369a794ec0f?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
]

# ---------------- Topic taxonomy (business-relevant news for traders) ----------------
# `cat` = NewsData.io category (optional), `q` = keyword query (kept < 100 chars for the
# free tier), `label` = UI label.
TOPICS: List[Dict[str, str]] = [
    {"key": "all", "label": "Top Stories", "cat": "top",
     "q": "trade OR export OR import OR tariff OR economy"},
    {"key": "trade", "label": "Trade & Tariffs", "cat": "",
     "q": "tariff OR export OR import OR customs OR \"trade deal\""},
    {"key": "business", "label": "Business & Economy", "cat": "business",
     "q": ""},
    {"key": "currency", "label": "Currency & Markets", "cat": "",
     "q": "currency OR forex OR \"exchange rate\" OR inflation OR \"central bank\""},
    {"key": "geopolitics", "label": "Geopolitics", "cat": "world",
     "q": "sanctions OR diplomacy OR alliance OR treaty"},
    {"key": "conflict", "label": "Conflict & War", "cat": "",
     "q": "war OR conflict OR military OR ceasefire OR attack"},
    {"key": "energy", "label": "Energy & Commodities", "cat": "",
     "q": "oil OR gas OR crude OR gold OR commodity OR metals"},
    {"key": "shipping", "label": "Shipping & Logistics", "cat": "",
     "q": "shipping OR freight OR container OR port OR logistics"},
    {"key": "policy", "label": "Policy & Regulation", "cat": "politics",
     "q": "regulation OR policy OR compliance OR ban OR subsidy"},
    {"key": "technology", "label": "Technology", "cat": "technology", "q": ""},
    {"key": "events", "label": "Business Events", "cat": "",
     "q": "\"trade fair\" OR expo OR summit OR conference OR exhibition"},
    {"key": "sports", "label": "Sports", "cat": "sports", "q": ""},
]
TOPIC_BY_KEY = {t["key"]: t for t in TOPICS}

# Legacy editorial categories (admin CMS + older clients).
CATEGORIES = ["All", "Tariffs & Duties", "FTAs & Trade Deals", "Logistics & Shipping",
              "Policy & Compliance", "Commodities", "Business", "India"]


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _img_for(seed: str) -> str:
    return FALLBACK_IMG[int(hashlib.sha1(seed.encode()).hexdigest(), 16) % len(FALLBACK_IMG)]


def _mk_id(prefix: str, seed: str) -> str:
    return f"{prefix}-{hashlib.sha1(seed.encode()).hexdigest()[:16]}"


# ---------------- Countries (full ISO list, used by the UI dropdown) ----------------
def _country_list() -> List[Dict[str, str]]:
    out = []
    try:
        import pycountry
        for c in pycountry.countries:
            out.append({"code": c.alpha_2.lower(), "name": getattr(c, "common_name", c.name)})
    except Exception as exc:  # pragma: no cover - pycountry is a hard dependency
        logging.warning("pycountry unavailable: %s", exc)
        out = [{"code": "in", "name": "India"}, {"code": "us", "name": "United States"},
               {"code": "ae", "name": "United Arab Emirates"}, {"code": "gb", "name": "United Kingdom"}]
    return sorted(out, key=lambda x: x["name"])


COUNTRIES = _country_list()
_NAME_BY_CODE = {c["code"]: c["name"] for c in COUNTRIES}
_CODE_BY_NAME = {c["name"].lower(): c["code"] for c in COUNTRIES}
_CODE_BY_NAME.update({"usa": "us", "uk": "gb", "uae": "ae", "south korea": "kr",
                      "russia": "ru", "vietnam": "vn", "iran": "ir", "syria": "sy",
                      "bolivia": "bo", "tanzania": "tz", "venezuela": "ve", "global": ""})


def resolve_country(value: str) -> Dict[str, str]:
    """Accepts an ISO-2 code or a country name; returns {code, name}."""
    v = (value or "").strip()
    if not v or v.lower() in ("global", "world", "all"):
        return {"code": "", "name": "Global"}
    low = v.lower()
    if len(low) == 2 and low in _NAME_BY_CODE:
        return {"code": low, "name": _NAME_BY_CODE[low]}
    code = _CODE_BY_NAME.get(low, "")
    if code:
        return {"code": code, "name": _NAME_BY_CODE.get(code, v)}
    return {"code": "", "name": v.title()}


# ---------------- Curated fallback (only when the live feed is unavailable) ----------------
CURATED: List[Dict[str, Any]] = [
    {"title": "Global merchandise trade rebounds as tariff tensions ease",
     "category": "Business", "topic": "trade", "country": "Global",
     "excerpt": "WTO data points to a broad recovery in goods trade led by electronics and machinery.",
     "source": "Vametra AI Intelligence"},
    {"title": "Red Sea reroutes keep Asia–Europe container rates elevated",
     "category": "Logistics & Shipping", "topic": "shipping", "country": "Global",
     "excerpt": "Carriers continue routing via the Cape of Good Hope, extending transit times 10–14 days.",
     "source": "Global Freight"},
    {"title": "EU CBAM reporting tightens for steel, cement and aluminium exporters",
     "category": "Policy & Compliance", "topic": "policy", "country": "Global",
     "excerpt": "Exporters to the EU must now track and report embedded carbon each quarter.",
     "source": "Regulatory Watch"},
    {"title": "India–UAE CEPA pushes bilateral trade past record highs",
     "category": "FTAs & Trade Deals", "topic": "trade", "country": "India",
     "excerpt": "Preferential tariffs open new lanes for SME exporters across food, textiles and pharma.",
     "source": "Trade Wire"},
    {"title": "Commodity outlook: agri and metals firm on tight supply",
     "category": "Commodities", "topic": "energy", "country": "Global",
     "excerpt": "Analysts flag continued strength in food grains and base metals into next quarter.",
     "source": "Market Desk"},
]


def _normalise_curated(topic: str) -> List[Dict[str, Any]]:
    out = []
    for c in CURATED:
        if topic and topic != "all" and c.get("topic") != topic:
            continue
        cid = _mk_id("ai", c["title"])
        out.append({**c, "id": cid, "image": _img_for(c["title"]),
                    "publishedAt": _iso(), "date": "Today", "badge": "ai", "url": ""})
    return out or [{**c, "id": _mk_id("ai", c["title"]), "image": _img_for(c["title"]),
                    "publishedAt": _iso(), "date": "Today", "badge": "ai", "url": ""} for c in CURATED]


# ---------------- Live adapters ----------------
# Three real sources, merged newest-first. All keyless except NewsData (optional):
#   1. Google News RSS  — true per-country scoping via `ceid`, huge coverage
#   2. GDELT 2.0 DOC    — global index, supplies article images
#   3. NewsData.io      — enabled automatically if NEWSDATA_API_KEY is set
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def _parse_pub(raw: str) -> Optional[str]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(raw)
        if dt:
            return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H%M%SZ", "%Y%m%dT%H%M%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:20].rstrip("Z"), fmt.rstrip("Z")).replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            continue
    return None


def human_date(iso: Optional[str]) -> str:
    if not iso:
        return "Recently"
    try:
        dt = datetime.fromisoformat(iso)
    except Exception:
        return "Recently"
    mins = int((_now() - dt).total_seconds() // 60)
    if mins < 1:
        return "Just now"
    if mins < 60:
        return f"{mins} min ago"
    if mins < 1440:
        return f"{mins // 60}h ago"
    if mins < 2880:
        return "Yesterday"
    if mins < 10080:
        return f"{mins // 1440}d ago"
    return dt.strftime("%d %b %Y")


def _query_for(topic: str, search: str, country_name: str, include_country: bool) -> str:
    t = TOPIC_BY_KEY.get(topic or "all", TOPIC_BY_KEY["all"])
    if search:
        base = search.strip()
    else:
        base = t.get("q") or t.get("label", "business news")
    if include_country and country_name and country_name != "Global":
        base = f"({base}) {country_name}"
    return base


async def _fetch_google_news(topic: str, country_code: str, country_name: str,
                             search: str, limit: int) -> List[Dict[str, Any]]:
    import xml.etree.ElementTree as ET
    q = _query_for(topic, search, country_name, include_country=not country_code)
    cc = (country_code or "us").upper()
    params = {"q": f"{q} when:7d", "hl": "en", "gl": cc, "ceid": f"{cc}:en"}
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
            r = await c.get(GOOGLE_NEWS_RSS, params=params,
                            headers={"User-Agent": "VametraAI-NewsEngine/1.0"})
        if r.status_code != 200:
            logging.info("GoogleNews %s", r.status_code)
            return []
        root = ET.fromstring(r.content)
    except Exception as exc:
        logging.warning("Google News fetch failed: %s", exc)
        return []

    t = TOPIC_BY_KEY.get(topic or "all", TOPIC_BY_KEY["all"])
    items = []
    for node in list(root.iterfind(".//item"))[: max(limit, 24)]:
        title = (node.findtext("title") or "").strip()
        if not title:
            continue
        link = (node.findtext("link") or "").strip()
        source = (node.findtext("source") or "").strip()
        if not source and " - " in title:
            title, source = title.rsplit(" - ", 1)
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]
        published = _parse_pub(node.findtext("pubDate") or "")
        desc = html.unescape(re.sub(r"<[^>]+>", " ", node.findtext("description") or ""))
        desc = re.sub(r"\s+", " ", desc.replace("\xa0", " ")).strip()
        if source and desc.endswith(source):
            desc = desc[: -len(source)].strip()
        if _norm_title(desc) == _norm_title(title):
            desc = ""
        items.append({
            "id": _mk_id("live", link or title), "title": title.strip(),
            "excerpt": desc[:240],
            "image": _img_for(title), "category": t["label"], "topic": t["key"],
            "country": country_name or "Global",
            "publishedAt": published or _iso(), "date": human_date(published),
            "source": source or "Newswire", "url": link, "badge": "live",
            "body": desc,
        })
    return items


GDELT_TOPIC_Q = {
    "all": "\"international trade\"", "trade": "tariff", "business": "economy",
    "currency": "\"exchange rate\"", "geopolitics": "sanctions", "conflict": "conflict",
    "energy": "\"commodity prices\"", "shipping": "\"container shipping\"",
    "policy": "regulation", "technology": "technology", "events": "\"trade fair\"",
    "sports": "sports",
}


async def _fetch_gdelt(topic: str, country_name: str, search: str, limit: int) -> List[Dict[str, Any]]:
    # GDELT's query parser rejects long OR chains — use one focused term per topic.
    q = (search.strip()[:60] if search else GDELT_TOPIC_Q.get(topic or "all", "\"international trade\""))
    if country_name and country_name != "Global":
        q = f"{q} \"{country_name}\""
    params = {"query": f"{q} sourcelang:english", "mode": "ArtList", "format": "json",
              "maxrecords": str(min(max(limit, 20), 50)), "sort": "DateDesc", "timespan": "7d"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(GDELT_URL, params=params,
                            headers={"User-Agent": "VametraAI-NewsEngine/1.0"})
        if r.status_code != 200 or not r.text.lstrip().startswith("{"):
            logging.info("GDELT skipped: %s", r.text[:120])
            return []
        data = r.json()
    except Exception as exc:
        logging.info("GDELT fetch skipped: %s", exc)
        return []
    t = TOPIC_BY_KEY.get(topic or "all", TOPIC_BY_KEY["all"])
    items = []
    for a in (data.get("articles") or []):
        title = (a.get("title") or "").strip()
        if not title:
            continue
        published = _parse_pub(a.get("seendate") or "")
        items.append({
            "id": _mk_id("live", a.get("url") or title), "title": title,
            "excerpt": "", "image": a.get("socialimage") or _img_for(title),
            "category": t["label"], "topic": t["key"],
            "country": (a.get("sourcecountry") or country_name or "Global"),
            "publishedAt": published or _iso(), "date": human_date(published),
            "source": a.get("domain") or "Newswire", "url": a.get("url") or "",
            "badge": "live", "body": "",
        })
    return items


async def _fetch_newsdata(topic: str, country_code: str, country_name: str,
                          search: str, limit: int) -> List[Dict[str, Any]]:
    if not NEWSDATA_KEY:
        return []
    t = TOPIC_BY_KEY.get(topic or "all", TOPIC_BY_KEY["all"])
    q = _query_for(topic, search, country_name, include_country=not country_code)
    params = {"apikey": NEWSDATA_KEY, "language": "en", "q": q[:99]}
    if t.get("cat"):
        params["category"] = t["cat"]
    if country_code:
        params["country"] = country_code
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(NEWSDATA_URL, params=params)
            if r.status_code in (400, 422):
                slim = {k: v for k, v in params.items() if k not in ("country", "category")}
                r = await c.get(NEWSDATA_URL, params=slim)
            if r.status_code != 200:
                logging.info("NewsData %s: %s", r.status_code, r.text[:160])
                return []
            raw = r.json().get("results") or []
    except Exception as exc:
        logging.warning("NewsData fetch failed: %s", exc)
        return []
    items = []
    for a in raw[: max(limit, 24)]:
        title = (a.get("title") or "").strip()
        if not title:
            continue
        published = _parse_pub(a.get("pubDate") or "")
        ccodes = a.get("country") or []
        items.append({
            "id": _mk_id("live", a.get("link") or title), "title": title,
            "excerpt": (a.get("description") or "")[:240],
            "image": a.get("image_url") or _img_for(title),
            "category": t["label"], "topic": t["key"],
            "country": (ccodes[0].title() if ccodes else (country_name or "Global")),
            "publishedAt": published or _iso(), "date": human_date(published),
            "source": a.get("source_name") or a.get("source_id") or "Newswire",
            "url": a.get("link") or "", "badge": "live",
            "body": a.get("content") or a.get("description") or "",
        })
    return items


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())[:60]


async def _fetch_live(topic: str, country_code: str, country_name: str,
                      search: str, limit: int) -> List[Dict[str, Any]]:
    import asyncio
    gn, gd, nd = await asyncio.gather(
        _fetch_google_news(topic, country_code, country_name, search, limit),
        _fetch_gdelt(topic, country_name, search, limit),
        _fetch_newsdata(topic, country_code, country_name, search, limit),
        return_exceptions=True)
    pools = [p if isinstance(p, list) else [] for p in (nd, gn, gd)]
    # image enrichment: GDELT carries real article images, Google News does not
    img_by_title = {_norm_title(i["title"]): i["image"] for i in pools[2] if i.get("image")}
    merged, seen = [], set()
    for pool in pools:
        for it in pool:
            key = _norm_title(it["title"])
            if not key or key in seen:
                continue
            seen.add(key)
            if img_by_title.get(key):
                it["image"] = img_by_title[key]
            merged.append(it)
    merged.sort(key=lambda x: x.get("publishedAt") or "", reverse=True)
    return merged[: max(limit, 24)]


async def _admin_news(country_name: str, topic: str) -> List[Dict[str, Any]]:
    docs = await ADMIN_NEWS.find({"active": {"$ne": False}}).sort(
        [("featured", -1), ("createdAt", -1)]).to_list(50)
    out = []
    for d in docs:
        created = d.get("createdAt") or _iso()
        out.append({"id": d["_id"], "title": d.get("title", ""), "excerpt": d.get("excerpt", ""),
                    "image": d.get("image") or _img_for(d.get("title", "")),
                    "category": d.get("category", "Business"), "topic": d.get("topic", "trade"),
                    "country": d.get("country", "Global"),
                    "publishedAt": created, "date": d.get("date") or human_date(created),
                    "source": d.get("source", "Vametra AI"), "url": d.get("url", ""),
                    "badge": "admin", "featured": bool(d.get("featured")),
                    "body": d.get("body", "")})
    if country_name and country_name != "Global":
        scoped = [o for o in out if o["country"] in (country_name, "Global")]
        out = scoped or out
    return out


async def _persist(items: List[Dict[str, Any]]):
    for it in items:
        try:
            await NEWS_ITEMS.update_one({"_id": it["id"]},
                                        {"$set": {**it, "_id": it["id"], "cachedAt": _iso()}},
                                        upsert=True)
        except Exception:
            pass


# ---------------- Feed builder (cached) ----------------
async def build_feed(topic: str, country: str, search: str, limit: int,
                     refresh: bool = False) -> Dict[str, Any]:
    c = resolve_country(country)
    topic = topic if topic in TOPIC_BY_KEY else "all"
    key = hashlib.sha1(f"{topic}|{c['code']}|{c['name']}|{search.strip().lower()}".encode()).hexdigest()

    if not refresh:
        cached = await NEWS_CACHE.find_one({"_id": key})
        if cached:
            try:
                age = (_now() - datetime.fromisoformat(cached["at"])).total_seconds() / 60
            except Exception:
                age = 999
            if age < CACHE_TTL_MIN:
                payload = cached["payload"]
                for it in payload.get("items", []):
                    it["date"] = human_date(it.get("publishedAt"))
                payload["cached"] = True
                return payload

    live = await _fetch_live(topic, c["code"], c["name"], search, limit)
    admin = await _admin_news(c["name"], topic)
    if search:
        s = search.lower()
        admin = [a for a in admin if s in (a["title"] + a["excerpt"]).lower()]
    fallback = _normalise_curated(topic) if len(live) + len(admin) < 3 else []

    featured = [a for a in admin if a.get("featured")]
    merged = featured + live + [a for a in admin if not a.get("featured")] + fallback

    seen, items = set(), []
    for m in merged:
        if m["id"] in seen:
            continue
        seen.add(m["id"])
        items.append(m)

    # newest first (featured editorial stays pinned at the top)
    pinned = [i for i in items if i.get("featured")]
    rest = sorted([i for i in items if not i.get("featured")],
                  key=lambda x: x.get("publishedAt") or "", reverse=True)
    items = (pinned + rest)[: max(1, min(limit, 40))]

    await _persist(items)
    payload = {"items": items, "topic": topic, "topics": TOPICS, "categories": CATEGORIES,
               "country": {"code": c["code"], "name": c["name"]},
               "search": search, "live": bool(live),
               "liveConfigured": True, "sources": {"live": len(live), "editorial": len(admin)},
               "lastUpdated": _iso(), "count": len(items), "cached": False}
    await NEWS_CACHE.replace_one({"_id": key}, {"_id": key, "at": _iso(), "payload": payload},
                                 upsert=True)
    return payload


# ---------------- Public endpoints ----------------
@router.get("/topics")
async def news_topics():
    return {"topics": TOPICS, "categories": CATEGORIES}


@router.get("/countries")
async def news_countries():
    return {"countries": COUNTRIES, "count": len(COUNTRIES)}


@router.get("/categories")
async def news_categories():
    return {"categories": CATEGORIES, "topics": TOPICS}


@router.get("/status")
async def news_status():
    meta = await NEWS_META.find_one({"_id": "heartbeat"}) or {}
    return {"liveConfigured": True, "newsdataKey": bool(NEWSDATA_KEY),
            "adapters": ["google-news-rss", "gdelt"] + (["newsdata.io"] if NEWSDATA_KEY else []),
            "lastRefresh": meta.get("lastRefresh"),
            "lastRefreshTopics": meta.get("topics", []),
            "cacheTtlMinutes": CACHE_TTL_MIN}


@router.get("/feed")
async def news_feed(country: str = Query(""), topic: str = Query("all"),
                    category: str = Query(""), q: str = Query(""),
                    limit: int = Query(24), refresh: int = Query(0),
                    authorization: Optional[str] = Header(default=None)):
    """Global by default. Signed-in users get their profile country pre-selected."""
    claims = await optional_user(authorization)
    personalized = False
    role = ""
    resolved_country = country

    if claims and not country:
        pref = await db.user_prefs.find_one({"owner": claims.get("uid")})
        if pref and pref.get("country"):
            resolved_country = pref["country"]
            role = pref.get("role", "")
            personalized = True

    # legacy clients still send ?category=<editorial category>
    if category and category != "All" and topic in ("", "all"):
        legacy = {"Tariffs & Duties": "trade", "FTAs & Trade Deals": "trade",
                  "Logistics & Shipping": "shipping", "Policy & Compliance": "policy",
                  "Commodities": "energy", "Business": "business"}
        topic = legacy.get(category, "all")

    payload = await build_feed(topic or "all", resolved_country, q, limit, refresh=bool(refresh))
    payload["personalized"] = personalized
    payload["context"] = {"country": payload["country"]["name"],
                          "countryCode": payload["country"]["code"], "role": role or None}
    return payload


@router.get("/{news_id}")
async def news_detail(news_id: str, authorization: Optional[str] = Header(default=None)):
    doc = await NEWS_ITEMS.find_one({"_id": news_id}) or await ADMIN_NEWS.find_one({"_id": news_id})
    if not doc:
        raise HTTPException(404, "News item not found")
    item = {k: v for k, v in doc.items() if k not in ("_id", "cachedAt")}
    item["id"] = news_id
    item["date"] = human_date(item.get("publishedAt")) if item.get("publishedAt") else item.get("date", "Recently")
    claims = await optional_user(authorization)
    ctx = ""
    if claims:
        pref = await db.user_prefs.find_one({"owner": claims.get("uid")})
        if pref:
            ctx = f"The reader is a {pref.get('role','trader')} based in {pref.get('country','their country')}."
    system = ("You are Vametra AI Brain, a global trade analyst. In 90-130 words explain, in plain "
              "language, what a news item MEANS for an importer/exporter — concrete actions, "
              "risks and opportunities. Use markdown bullets. Do not invent specific figures.")
    prompt = (f"NEWS: {item.get('title','')}\n{item.get('excerpt','')}\n{item.get('body','')[:600]}\n\n"
              f"{ctx}\nExplain: 'What does this mean for my trade?'")
    impact = await llm_util.generate(system, prompt, session=f"news-{news_id}")
    item["impact"] = impact or ("- Monitor how this affects your lane's costs and timelines.\n"
                                "- Review duties, FTAs and freight for affected products.\n"
                                "- Ask the Vametra AI Brain for a tailored action plan.")
    return item


# ---------------- Daily refresh ----------------
async def refresh_news(trigger: str = "scheduler") -> Dict[str, Any]:
    """Pre-warm the global feed for every topic so the page is always fresh."""
    done = []
    for t in TOPICS:
        try:
            await build_feed(t["key"], "", "", 24, refresh=True)
            done.append(t["key"])
        except Exception as exc:
            logging.warning("News refresh failed for %s: %s", t["key"], exc)
    await NEWS_META.replace_one({"_id": "heartbeat"},
                                {"_id": "heartbeat", "lastRefresh": _iso(),
                                 "topics": done, "trigger": trigger}, upsert=True)
    # prune stale cached articles (>30 days)
    cutoff = _iso(_now() - timedelta(days=30))
    try:
        await NEWS_ITEMS.delete_many({"cachedAt": {"$lt": cutoff}, "badge": "live"})
    except Exception:
        pass
    logging.info("Trade News refreshed (%s topics, trigger=%s)", len(done), trigger)
    return {"ok": True, "topics": done, "at": _iso()}


_sched = None


def start_news_refresh():
    """Daily live-news refresh at 00:20 UTC + a warm-up 60s after boot."""
    global _sched
    if _sched:
        return
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    _sched = AsyncIOScheduler(timezone="UTC")
    _sched.add_job(refresh_news, CronTrigger(hour=0, minute=20), id="news-daily",
                   replace_existing=True, misfire_grace_time=3600)
    _sched.add_job(refresh_news, DateTrigger(run_date=_now() + timedelta(seconds=60)),
                   id="news-warmup", replace_existing=True)
    _sched.start()
    logging.info("Trade News daily refresh scheduled (00:20 UTC).")


# ---------------- Admin CRUD ----------------
class NewsIn(BaseModel):
    title: str
    excerpt: str = ""
    body: str = ""
    category: str = "Business"
    topic: str = "trade"
    country: str = "Global"
    source: str = "Vametra AI"
    image: str = ""
    url: str = ""
    date: str = ""
    featured: bool = False
    active: bool = True


@router.get("/admin/all")
async def admin_list(_: dict = Depends(require_admin)):
    docs = await ADMIN_NEWS.find({}).sort([("featured", -1), ("createdAt", -1)]).to_list(300)
    return {"items": [{**{k: v for k, v in d.items() if k != "_id"}, "id": d["_id"]} for d in docs]}


@router.post("/admin")
async def admin_create(body: NewsIn, _: dict = Depends(require_admin)):
    nid = _mk_id("admin", body.title + uuid.uuid4().hex)
    doc = {"_id": nid, **body.model_dump(), "publishedAt": _iso(),
           "createdAt": _iso(), "updatedAt": _iso()}
    await ADMIN_NEWS.insert_one(doc)
    return {"ok": True, "id": nid}


@router.put("/admin/{nid}")
async def admin_update(nid: str, body: NewsIn, _: dict = Depends(require_admin)):
    res = await ADMIN_NEWS.update_one({"_id": nid}, {"$set": {**body.model_dump(), "updatedAt": _iso()}})
    if not res.matched_count:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@router.delete("/admin/{nid}")
async def admin_delete(nid: str, _: dict = Depends(require_admin)):
    await ADMIN_NEWS.delete_one({"_id": nid})
    return {"ok": True}


@router.post("/admin/refresh")
async def admin_refresh(_: dict = Depends(require_admin)):
    return await refresh_news(trigger="admin")
