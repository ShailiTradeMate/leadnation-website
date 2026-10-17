"""Vametra AI Brain — Explore: on-demand corridor / country / product / industry / region / guide
reports for any lane the static catalogue does not publish. Numbers come only from the live
engines (WITS duty, OEC demand, verified buyers, expos, news); the narrative is AI-written from
that data and clearly labelled. Nothing here creates an indexable page."""
import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
import duty_engine
import trade_intel
from seo_pages import _buyer_section, _expo_section, _news_section, PRODUCTS, COUNTRIES as GUIDE_COUNTRIES, REGIONS, _slugify

logger = logging.getLogger("brain.explore")
router = APIRouter(prefix="/brain", tags=["brain-explore"])

KINDS = ("corridor", "country", "product", "industry", "region", "guide")
CACHE_TTL = timedelta(days=7)
PROFILE_SLUGS = {"india", "uae", "usa", "australia", "armenia"}
CORRIDOR_SLUGS = {"uae", "usa", "australia", "armenia"}
ALIASES = {"uae": "United Arab Emirates", "usa": "United States", "us": "United States", "uk": "United Kingdom",
           "america": "United States", "britain": "United Kingdom", "holland": "Netherlands", "korea": "South Korea"}


class ExploreRequest(BaseModel):
    kind: str
    origin: str | None = None
    destination: str | None = None
    product: str | None = None
    hs: str | None = None
    industry: str | None = None
    region: str | None = None


def _country_code(name):
    if not name:
        return None, None
    n = ALIASES.get(name.strip().lower(), name.strip())
    for code, cname in duty_engine.COUNTRIES:
        if cname.lower() == n.lower() or cname.lower().startswith(n.lower()):
            return code, cname
    return None, n


def _closest_published(product_slug, dest_slug, origin_name, dest_code=None):
    links = []
    if origin_name and origin_name.lower() == "india" and dest_slug in CORRIDOR_SLUGS:
        links.append({"to": f"/corridors/india-to-{dest_slug}", "label": f"India → {dest_slug.upper() if len(dest_slug) <= 3 else dest_slug.title()} corridor"})
    if dest_slug in PROFILE_SLUGS:
        links.append({"to": f"/countries/{dest_slug}", "label": "Country trade profile"})
    if product_slug in PRODUCTS and dest_slug in GUIDE_COUNTRIES:
        links.append({"to": f"/export/{product_slug}/to/{dest_slug}", "label": "Published export guide"})
    elif product_slug in PRODUCTS:
        links.append({"to": f"/export/{product_slug}", "label": f"{PRODUCTS[product_slug]['name']} markets"})
    for r, meta in REGIONS.items():
        if dest_code and dest_code in meta["codes"]:
            links.append({"to": f"/regions/{r}", "label": f"{meta['name']} export hub"})
            break
    return links


async def _resolve_product_hs6(product, hs):
    """Catalogue aliases first (basmati → 100630), then the shared resolver
    (HS directory → AI classification → web lookup) so local names resolve too."""
    import hs_resolver
    p = (product or "").strip().lower()
    for slug, meta in PRODUCTS.items():
        if p and (p == meta["name"].lower() or p == slug.replace("-", " ") or p in [a.lower() for a in meta.get("aka", [])]):
            return {"hs6": meta["primaryHs"], "via": "catalogue", "canonical": meta["name"], "note": "", "sources": []}
    return await hs_resolver.resolve(product, hs)


async def _narrative(ctx: dict) -> dict:
    """AI narrative constrained to the engine data; returns a dict or {} on failure."""
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key or os.environ.get("BRAIN_AI_ENABLED", "false").lower() != "true":
        return {}
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    system = ("You are the Vametra AI Brain, a global trade analyst. Write for an exporter/importer. "
              "Use ONLY the numbers in DATA; never invent tariff rates, buyer counts, demand figures or dates. "
              "Where DATA has no figure, say that it must be confirmed with the customs authority. "
              "General procedural guidance (documents, process steps) is allowed and must be practical. "
              "Return STRICT JSON with keys: tagline (<=160 chars), exportProcess (2-3 sentences), "
              "importProcess (2-3 sentences), customsInfo (2-3 sentences), documents (array of 6-8 short strings), "
              "popularProducts (array of 6 short product names relevant to this lane; [] if a specific product is given), "
              "opportunities (2 sentences), faqs (array of 4 {q,a} objects, answers <=60 words). No markdown.")
    prompt = f"REQUEST: {json.dumps(ctx['request'])}\nDATA: {json.dumps(ctx['data'])[:9000]}"
    try:
        chat = LlmChat(api_key=key, session_id=f"explore-{abs(hash(prompt)) % 10**9}", system_message=system) \
            .with_model(os.environ.get("BRAIN_AI_PROVIDER", "openai"), os.environ.get("BRAIN_AI_MODEL", "gpt-5.4-mini"))
        raw = (await chat.send_message(UserMessage(text=prompt)) or "").strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        out = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        return out if isinstance(out, dict) else {}
    except Exception as exc:
        logger.warning("explore narrative failed: %s", exc)
        return {}


@router.post("/explore")
async def explore(req: ExploreRequest):
    kind = (req.kind or "").lower()
    if kind not in KINDS:
        raise HTTPException(400, f"kind must be one of {KINDS}")
    origin = (req.origin or ("India" if kind in ("corridor", "guide") else "")).strip()
    destination = (req.destination or "").strip()
    product = (req.product or req.industry or "").strip()
    if kind in ("corridor", "country", "guide") and not destination:
        raise HTTPException(400, "destination country is required")
    if kind in ("product", "guide") and not (product or req.hs):
        raise HTTPException(400, "product name or HS code is required")
    if kind == "region" and not (req.region or destination):
        raise HTTPException(400, "region or country is required")
    if kind == "industry" and not product:
        raise HTTPException(400, "industry is required")

    cache_id = f"v2|{kind}|{origin.lower()}|{destination.lower()}|{product.lower()}|{(req.hs or '').strip()}|{(req.region or '').lower()}"
    cached = await db.brain_explore_cache.find_one({"_id": cache_id}, {"_id": 0})
    if cached and datetime.fromisoformat(cached["generatedAt"]) > datetime.now(timezone.utc) - CACHE_TTL:
        return {**cached["report"], "cached": True}

    resolution = await _resolve_product_hs6(product, req.hs) if (product or req.hs) else {}
    hs6 = (resolution or {}).get("hs6")
    o_code, o_name = _country_code(origin)
    d_code, d_name = _country_code(destination)
    region_meta = REGIONS.get(_slugify(req.region)) if req.region else None
    region_countries = [duty_engine.NAME_BY_CODE.get(c) for c in (region_meta or {}).get("codes", []) if duty_engine.NAME_BY_CODE.get(c)]

    duty = demand = None
    notes = []
    if hs6 and d_code:
        try:
            d = await duty_engine.duty_and_benefits(hs6, origin=o_code or "", destination=d_code)
            if d.get("ok"):
                duty = {k: d.get(k) for k in ("hsCode", "importDuty", "preferential", "exportBenefit", "indiaBreakdown", "notes")}
        except Exception as exc:
            logger.warning("explore duty %s: %s", hs6, exc)
    elif hs6 and destination and not d_code:
        notes.append(f"{d_name} is not among the {len(duty_engine.COUNTRIES)} tariff-reporting countries in World Bank WITS, so no applied duty is shown — confirm with the national customs tariff.")
    if hs6:
        try:
            s = await trade_intel.trade_stats(hs6)
            if s.get("ok"):
                detail = None
                if d_name:
                    try:
                        detail = await trade_intel.importer_detail(hs6, d_name)
                    except Exception:
                        detail = None
                demand = {"source": s.get("source"), "year": (detail or {}).get("year") or s.get("year"),
                          "description": s.get("description"), "worldImportsUSD": s.get("totalWorldTradeUSD"),
                          "countryImportsUSD": (detail or {}).get("countryImportsUSD"),
                          "countryShare": (detail or {}).get("countryShare"), "countryRank": (detail or {}).get("countryRank"),
                          "topImporters": (s.get("topImporters") or [])[:8], "topExporters": (s.get("topExporters") or [])[:8],
                          "trend": (s.get("trend") or [])[-6:]}
        except Exception as exc:
            logger.warning("explore demand %s: %s", hs6, exc)
    elif product:
        notes.append("No HS code could be resolved for that product name — pick a code with the HS finder for duty and demand figures.")
    if hs6 and (resolution or {}).get("via", "").startswith(("ai", "web", "alias")):
        label = resolution.get("canonical") or product
        via = resolution["via"]
        src = "web search" if "web" in via else "Vametra's learned product names" if via == "alias" else "the Brain's classifier"
        notes.append(f"\"{product}\" was identified as {label} and classified under HS {hs6} by {src}"
                     + (f" — {resolution['note'].rstrip('. ')}" if resolution.get("note") else "")
                     + ". Confirm the 8-digit national code with your customs broker before filing.")

    market = d_name or (region_meta or {}).get("name")
    buyers = await _buyer_section(d_name, [hs6] if hs6 else [], "") if d_name else None
    expos = await _expo_section(d_name) if d_name else []
    news = await _news_section(d_name) if d_name else []

    request_ctx = {"kind": kind, "origin": o_name or origin or None, "destination": d_name or destination or None,
                   "product": product or None, "productCanonical": (resolution or {}).get("canonical"),
                   "hs6": hs6, "hsDescription": (resolution or {}).get("description"),
                   "region": (region_meta or {}).get("name") or req.region}
    data_ctx = {"duty": duty, "demand": demand, "buyers": buyers, "expos": expos[:4], "news": news[:4],
                "regionCountries": region_countries or None, "notes": notes}
    narrative = await _narrative({"request": request_ctx, "data": data_ctx})
    ai_live = bool(narrative)
    if not narrative:
        narrative = {
            "tagline": f"{product or kind.title()} — {o_name or origin or 'any origin'} → {market or 'any market'}: live duty, demand and buyer data.",
            "exportProcess": "Classify to HS6, confirm the applied and preferential duty, build landed cost, then qualify buyers before quoting.",
            "importProcess": "Confirm destination import licensing, labelling and standards; duty and VAT/GST are assessed on the customs value at clearance.",
            "customsInfo": "Preferential rates require rules-of-origin proof at clearance — price the applied rate unless origin documentation is in hand.",
            "documents": ["Commercial invoice", "Packing list", "Bill of lading / airway bill", "Certificate of origin", "Insurance certificate", "Import licence (if applicable)"],
            "popularProducts": [], "opportunities": "", "faqs": [],
        }

    title_market = market or "any market"
    subject = product or (f"HS {hs6}" if hs6 else "Products")
    titles = {
        "corridor": (f"{o_name or origin} → {title_market} trade corridor", f"Export from {o_name or origin} to {title_market} — duty, FTA and shipping"),
        "country": (f"{title_market} trade profile", f"{title_market} trade profile — tariffs, imports and verified buyers"),
        "product": (f"{subject} export intelligence", f"{subject} — HS code, duty, demand and buyers"),
        "industry": (f"{product} exports from {o_name or origin or 'India'}", f"{product} exports — markets, duty and buyers"),
        "region": (f"Export to {title_market}", f"Export to {title_market} — duty, demand and buyers by market"),
        "guide": (f"{subject} to {title_market}", f"Export {subject} from {o_name or origin} to {title_market}"),
    }
    sources = [{"name": "World Bank WITS / UNCTAD TRAINS", "for": "applied & preferential tariffs"} if duty else None,
               {"name": (demand or {}).get("source") or "OEC World (CEPII BACI)", "for": "import demand"} if demand else None,
               {"name": "Vametra AI Buyer Intelligence (official registries)", "for": "verified buyer counts"} if buyers else None,
               {"name": "Vametra AI Brain classifier" + (" + web search" if "web" in (resolution or {}).get("via", "") else ""),
                "for": f"HS classification of \"{product}\""} if hs6 and (resolution or {}).get("via", "").startswith(("ai", "web", "alias")) else None,
               {"name": "Vametra AI Brain (LLM)", "for": "narrative — verify procedures with the authority"}]
    report = {
        "kind": kind, "title": titles[kind][0], "h1": titles[kind][1],
        "origin": o_name or origin or None, "destination": d_name or destination or None,
        "product": product or None, "hs6": hs6, "hsResolution": resolution or None,
        "region": (region_meta or {}).get("name"),
        "regionCountries": region_countries or None,
        "duty": duty, "demand": demand, "buyers": buyers, "expos": expos, "news": news,
        "narrative": narrative, "faqs": narrative.get("faqs") or [], "notes": notes,
        "sources": [s for s in sources if s], "aiGenerated": True, "aiLive": ai_live,
        "closestPublished": _closest_published(_slugify(product) if product else None, _slugify(d_name or destination) if (d_name or destination) else None, o_name or origin, d_code),
        "disclaimer": "Generated on demand by the Vametra AI Brain. Figures are read live from the named sources; "
                      "procedural text is AI-written guidance and must be confirmed with the relevant customs authority before you ship.",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.brain_explore_cache.update_one({"_id": cache_id}, {"$set": {"report": report, "generatedAt": report["generatedAt"]}}, upsert=True)
    return {**report, "cached": False}
