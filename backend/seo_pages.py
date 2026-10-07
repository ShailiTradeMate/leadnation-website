"""SEO/GEO page data engine.

Serves the aggregated, source-attributed payload behind the indexable SEO surfaces
(product x country, country, corridor, region) and decides — mechanically — whether a
combination has enough REAL data to deserve indexing.

Nothing here fabricates figures. Every number carries a source and an as-of date:
  * Import duty / preferential rate .. World Bank WITS / UNCTAD TRAINS   (duty_engine)
  * India export benefit ............ DGFT Appendix 4R (RoDTEP)          (duty_engine)
  * World demand / top importers .... OEC World (CEPII BACI / UN Comtrade) (trade_intel)
  * Verified buyers ................. Vametra VBIE (db.entities, public visibility rules)
  * Expos ........................... Vametra expo engine (live feeds)
  * Trade news ...................... Vametra news engine (live feeds)

If a section has no data it is returned as null and the page must not invent it.
"""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Header, HTTPException, Query

from core import db
import duty_engine
import trade_intel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seo", tags=["seo-pages"])

INDIA = "356"

# ---------------------------------------------------------------- catalogues
# Products the owner approved for the first product x country batch.
PRODUCTS = {
    "basmati-rice": {
        "name": "Basmati Rice", "sector": "Agri & Foods",
        "hs": ["100630"], "primaryHs": "100630",
        "aka": ["basmati", "rice", "milled rice"],
    },
    "fresh-vegetables": {
        "name": "Fresh Vegetables", "sector": "Agri & Foods",
        "hs": ["070310", "070200", "070190"], "primaryHs": "070310",
        "aka": ["onion", "tomato", "potato", "vegetables"],
    },
    "fresh-fruits": {
        "name": "Fresh Fruits", "sector": "Agri & Foods",
        "hs": ["080450", "080610", "080390"], "primaryHs": "080450",
        "aka": ["mango", "grapes", "banana", "fruits"],
    },
    "agarbatti": {
        "name": "Agarbatti & Incense Sticks", "sector": "Home & Furnishings",
        "hs": ["330741"], "primaryHs": "330741",
        "aka": ["agarbatti", "incense sticks", "dhoop"],
    },
    "indian-spices": {
        "name": "Indian Spices", "sector": "Agri & Foods",
        "hs": ["091030", "090411", "090930"], "primaryHs": "091030",
        "aka": ["turmeric", "pepper", "cumin", "spices"],
    },
    "cotton-textiles": {
        "name": "Cotton Textiles & Apparel", "sector": "Textiles & Apparel",
        "hs": ["520100", "620342", "630260"], "primaryHs": "620342",
        "aka": ["cotton", "garments", "apparel", "home textiles"],
    },
    "pharmaceuticals": {
        "name": "Pharmaceuticals", "sector": "Pharma & Healthcare",
        "hs": ["300490", "300420"], "primaryHs": "300490",
        "aka": ["medicines", "formulations", "generic drugs"],
    },
    "engineering-machinery": {
        "name": "Engineering Goods & Machinery", "sector": "Industrial Machinery",
        "hs": ["847989", "841989", "730890"], "primaryHs": "847989",
        "aka": ["machinery", "machine parts", "engineering goods", "structures"],
    },
}

REGIONS = {
    "europe": {
        "name": "Europe", "codes": ["826", "276", "250", "380", "528", "724", "643", "616",
                                     "756", "056", "752", "348", "203", "620", "300", "372",
                                     "578", "208", "246", "040"]},
    "middle-east": {
        "name": "Middle East", "codes": ["784", "682", "634", "512", "414", "048", "376", "792", "818"]},
    "asia-pacific": {
        "name": "Asia Pacific", "codes": ["156", "392", "036", "702", "410", "360", "764",
                                           "458", "704", "608", "554", "586", "050", "144"]},
    "americas": {"name": "Americas", "codes": ["842", "124", "076", "484", "032", "152", "170", "604"]},
    "africa": {"name": "Africa", "codes": ["710", "566", "404", "204"]},
}

_SLUG_FIX = {
    "united-states": "usa", "united-arab-emirates": "uae", "united-kingdom": "uk",
    "south-korea": "south-korea", "czechia": "czechia",
}


def _slugify(name: str) -> str:
    s = name.lower().replace("&", "and")
    s = "".join(ch if ch.isalnum() else "-" for ch in s)
    while "--" in s:
        s = s.replace("--", "-")
    s = s.strip("-")
    return _SLUG_FIX.get(s, s)


def _build_countries():
    region_of = {}
    for rslug, r in REGIONS.items():
        for c in r["codes"]:
            region_of[c.lstrip("0") or "0"] = rslug
    out = {}
    for code, name in duty_engine.COUNTRIES:
        key = code.lstrip("0") or "0"
        out[_slugify(name)] = {
            "code": code, "name": name, "slug": _slugify(name),
            "region": region_of.get(key, "other"),
        }
    return out


COUNTRIES = _build_countries()
COUNTRY_BY_CODE = {v["code"].lstrip("0"): v for v in COUNTRIES.values()}

# Sufficiency gate — a page is only indexable when the core trade facts are real.
WEIGHTS = {"duty": 40, "demand": 30, "buyers": 15, "expos": 8, "news": 7}
INDEX_THRESHOLD = 70


# ---------------------------------------------------------------- sections
async def _duty_section(hs6: str, destination: str):
    try:
        d = await duty_engine.duty_and_benefits(hs6, origin=INDIA, destination=destination)
    except Exception as exc:
        logger.warning("duty section %s/%s: %s", hs6, destination, exc)
        return None
    if not d.get("ok") or not (d.get("importDuty") or d.get("exportBenefit")):
        return None
    return {
        "hsCode": d["hsCode"],
        "importDuty": d.get("importDuty"),
        "preferential": d.get("preferential"),
        "exportBenefit": d.get("exportBenefit"),
        "indiaBreakdown": d.get("indiaBreakdown"),
        "notes": d.get("notes") or [],
    }


async def _demand_section(hs6: str, country_name: str):
    try:
        s = await trade_intel.trade_stats(hs6)
    except Exception as exc:
        logger.warning("demand section %s: %s", hs6, exc)
        return None
    if not s.get("ok"):
        return None
    detail = None
    if country_name:
        try:
            detail = await trade_intel.importer_detail(hs6, country_name)
        except Exception as exc:
            logger.warning("importer detail %s/%s: %s", hs6, country_name, exc)
    return {
        "source": s.get("source"), "year": (detail or {}).get("year") or s.get("year"),
        "description": s.get("description"),
        "worldImportsUSD": s.get("totalWorldTradeUSD"),
        "countryImportsUSD": (detail or {}).get("countryImportsUSD"),
        "countryShare": (detail or {}).get("countryShare"),
        "countryRank": (detail or {}).get("countryRank"),
        "countriesReporting": (detail or {}).get("countriesReporting"),
        "topImporters": (s.get("topImporters") or [])[:8],
        "topExporters": (s.get("topExporters") or [])[:8],
        "trend": (s.get("trend") or [])[-6:],
    }


async def _buyer_section(country_name: str, hs_list, sector: str):
    """Real counts only. Coverage is currently Europe-heavy — never imply otherwise."""
    try:
        from buyer_membership import PUBLIC_Q
        base = dict(PUBLIC_Q)
        q = {**base, "$or": [{"country_name": country_name}, {"country": country_name}]}
        total = await db.entities.count_documents(q)
        by_hs = 0
        if total:
            fams = sorted({h for hs in hs_list for h in (hs, hs[:4], hs[:2])})
            by_hs = await db.entities.count_documents({**q, "hs_families": {"$in": fams}})
        by_sector = await db.entities.count_documents({**q, "sector": sector}) if total else 0
    except Exception as exc:
        logger.warning("buyer section %s: %s", country_name, exc)
        return {"covered": False, "total": 0, "matchingHs": 0, "matchingSector": 0}
    return {"covered": total > 0, "total": total, "matchingHs": by_hs,
            "matchingSector": by_sector,
            "note": None if total else "Buyer coverage for this market is being ingested — "
                                       "verified records are published only after sanctions screening."}


async def _expo_section(country_name: str, limit: int = 4):
    now = datetime.now(timezone.utc).isoformat()
    try:
        rows = await db.expo_listings.find(
            {"status": "published", "country": country_name},
            {"_id": 0, "id": 1, "name": 1, "city": 1, "startDate": 1, "sector": 1, "website": 1},
        ).sort("startDate", 1).to_list(limit)
        if not rows:
            rows = await db.expo_events.find(
                {"country": country_name, "starts_at": {"$gte": now}},
                {"_id": 0, "id": 1, "title": 1, "location": 1, "starts_at": 1, "url": 1, "source": 1},
            ).sort("starts_at", 1).to_list(limit)
    except Exception as exc:
        logger.warning("expo section %s: %s", country_name, exc)
        return []
    return rows


async def _news_section(country_name: str, limit: int = 4):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    try:
        rows = await db.news_items.find(
            {"country": country_name, "publishedAt": {"$gte": cutoff}},
            {"_id": 0, "id": 1, "title": 1, "source": 1, "url": 1, "publishedAt": 1, "excerpt": 1},
        ).sort("publishedAt", -1).to_list(limit)
    except Exception as exc:
        logger.warning("news section %s: %s", country_name, exc)
        return []
    return rows


def _score(duty, demand, buyers, expos, news):
    s = 0
    if duty and duty.get("importDuty"):
        s += WEIGHTS["duty"]
    if demand and demand.get("worldImportsUSD"):
        s += WEIGHTS["demand"]
    if buyers and buyers.get("covered"):
        s += WEIGHTS["buyers"]
    if expos:
        s += WEIGHTS["expos"]
    if news:
        s += WEIGHTS["news"]
    return s


# ---------------------------------------------------------------- routes
@router.get("/catalogue")
async def catalogue():
    """Products, countries and regions that the SEO surfaces are allowed to render."""
    return {
        "products": [{"slug": k, **{x: v[x] for x in ("name", "sector", "hs", "primaryHs")}}
                     for k, v in PRODUCTS.items()],
        "countries": sorted(COUNTRIES.values(), key=lambda c: c["name"]),
        "regions": [{"slug": k, "name": v["name"], "countries":
                     [COUNTRY_BY_CODE[c.lstrip("0")]["slug"] for c in v["codes"]
                      if c.lstrip("0") in COUNTRY_BY_CODE]}
                    for k, v in REGIONS.items()],
        "indexThreshold": INDEX_THRESHOLD,
        "weights": WEIGHTS,
    }


@router.get("/page-data/{product}/{country}")
async def product_country_page(product: str, country: str):
    p = PRODUCTS.get(product)
    c = COUNTRIES.get(country)
    if not p or not c:
        raise HTTPException(status_code=404, detail="Unknown product or country")

    hs = p["primaryHs"]
    duty = await _duty_section(hs, c["code"])
    demand = await _demand_section(hs, c["name"])
    buyers = await _buyer_section(c["name"], p["hs"], p["sector"])
    expos = await _expo_section(c["name"])
    news = await _news_section(c["name"])

    score = _score(duty, demand, buyers, expos, news)
    indexable = bool(score >= INDEX_THRESHOLD and duty and duty.get("importDuty")
                     and demand and demand.get("worldImportsUSD"))

    sources = []
    if duty:
        sources.append({"field": "duty", "name": "World Bank WITS / UNCTAD TRAINS",
                        "asOf": (duty.get("importDuty") or {}).get("year")})
        if duty.get("exportBenefit"):
            sources.append({"field": "exportBenefit", "name": duty["exportBenefit"].get("source"),
                            "asOf": duty["exportBenefit"].get("effectiveDate")})
    if demand:
        sources.append({"field": "demand", "name": demand.get("source"), "asOf": demand.get("year")})
    if buyers and buyers.get("covered"):
        sources.append({"field": "buyers", "name": "Vametra Verified Buyer Intelligence (VBIE)",
                        "asOf": datetime.now(timezone.utc).strftime("%Y-%m-%d")})

    return {
        "ok": True,
        "product": {"slug": product, **{k: p[k] for k in ("name", "sector", "hs", "primaryHs")}},
        "country": c,
        "url": f"/export/{product}/to/{country}",
        "duty": duty, "demand": demand, "buyers": buyers, "expos": expos, "news": news,
        "dataScore": score, "indexable": indexable,
        "sources": sources,
        "disclaimer": "Tariff and incentive figures are the latest officially published rates from the "
                      "sources shown and may lag the current year. Verify against the destination "
                      "customs tariff and DGFT notifications before contracting or shipping.",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/matrix")
async def matrix(min_score: int = Query(0, ge=0, le=100), product: str = None,
                 region: str = None, limit: int = 400, force: bool = False):
    """Score every allowed product x country combination — drives publishing decisions
    and feeds the sitemap (only indexable rows are ever submitted). Cached 24h."""
    import asyncio
    cache_id = f"matrix:{product or 'all'}:{region or 'all'}"
    if not force:
        cached = await db.seo_matrix_cache.find_one({"_id": cache_id})
        if cached and (datetime.now(timezone.utc)
                       - datetime.fromisoformat(cached["at"])).total_seconds() < 86400:
            rows = [r for r in cached["rows"] if r["dataScore"] >= min_score][:limit]
            return {"count": len(rows), "indexable": sum(1 for r in rows if r["indexable"]),
                    "cachedAt": cached["at"], "rows": rows}

    prods = [product] if product else list(PRODUCTS)
    sem = asyncio.Semaphore(8)

    async def row(ps, p, cs, c, demand):
        async with sem:
            duty = await _duty_section(p["primaryHs"], c["code"])
            buyers = await _buyer_section(c["name"], p["hs"], p["sector"])
            expos = await _expo_section(c["name"], 1)
            news = await _news_section(c["name"], 1)
            d_country = None
            if demand:
                try:
                    d_country = await trade_intel.importer_detail(p["primaryHs"], c["name"])
                except Exception:
                    d_country = None
            score = _score(duty, demand, buyers, expos, news)
            return {
                "url": f"/export/{ps}/to/{cs}", "product": ps, "country": cs,
                "region": c["region"], "dataScore": score,
                "indexable": bool(score >= INDEX_THRESHOLD and duty and demand),
                "dutyRate": ((duty or {}).get("importDuty") or {}).get("rate"),
                "countryImportsUSD": (d_country or {}).get("countryImportsUSD"),
                "countryRank": (d_country or {}).get("countryRank"),
                "buyers": (buyers or {}).get("total", 0),
            }

    tasks = []
    for ps in prods:
        p = PRODUCTS.get(ps)
        if not p:
            continue
        demand = await _demand_section(p["primaryHs"], "")
        for cs, c in COUNTRIES.items():
            if (region and c["region"] != region) or c["code"] == INDIA:
                continue
            tasks.append(row(ps, p, cs, c, demand))
    out = [r for r in await asyncio.gather(*tasks, return_exceptions=False)]
    out.sort(key=lambda r: (-r["dataScore"], -(r["countryImportsUSD"] or 0)))
    await db.seo_matrix_cache.replace_one(
        {"_id": cache_id},
        {"_id": cache_id, "rows": out, "at": datetime.now(timezone.utc).isoformat()}, upsert=True)
    rows = [r for r in out if r["dataScore"] >= min_score][:limit]
    return {"count": len(rows), "indexable": sum(1 for r in rows if r["indexable"]), "rows": rows}


@router.post("/refresh-all")
async def refresh_all(x_admin_token: str = Header(default=None)):
    """Admin: force-refresh every live data source behind the SEO pages."""
    import os
    if x_admin_token != os.environ.get("ADMIN_TOKEN", "leadnation-admin-2026"):
        raise HTTPException(status_code=403, detail="admin only")
    report = {}

    try:
        report["dutyAndRodtep"] = await duty_engine.refresh_all()
    except Exception as exc:
        report["dutyAndRodtep"] = f"error: {exc}"
    try:
        await db.trade_cache.delete_many({})
        await db.trade_hs_map.delete_many({})
        trade_intel._HS_MAP = {}
        mp = await trade_intel._load_hs_map()
        report["tradeStats"] = f"cache cleared, HS directory rebuilt ({len(mp)} codes)"
    except Exception as exc:
        report["tradeStats"] = f"error: {exc}"
    try:
        import news_engine
        report["news"] = await news_engine.refresh_news(trigger="admin-refresh-all")
    except Exception as exc:
        report["news"] = f"error: {exc}"
    try:
        import expo_live
        report["expos"] = await expo_live.run_engine(trigger="admin-refresh-all")
    except Exception as exc:
        report["expos"] = f"error: {exc}"

    report["at"] = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "report": report}
