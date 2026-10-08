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


# ---------------------------------------------------------------- region hubs
REGION_HUBS = {
    "europe": {
        "name": "Europe", "demonym": "European",
        "intro": ("Europe is the deepest verified-buyer market on Vametra AI and the most "
                  "document-driven: EU import duty is set by the Union's Common Customs Tariff, "
                  "so the rate is identical in every member state, while VAT, labelling and "
                  "product-conformity rules are national. Pick a country below to see the real "
                  "applied tariff for your product, the market's own import demand and the "
                  "verified importers we hold."),
        "facts": [
            "EU member states share one external tariff (Common Customs Tariff), so the duty rate is the same whichever member state clears the goods.",
            "Import VAT, labelling and conformity requirements are national — always check the destination state, not just 'the EU'.",
            "Agri-food consignments need SPS/phytosanitary documentation and EU-registered establishments for products of animal origin.",
            "The UK and Switzerland are outside the EU customs union — they set their own tariffs.",
        ],
    },
    "middle-east": {
        "name": "Middle East", "demonym": "Middle Eastern",
        "intro": ("The Gulf is the fastest-moving re-export and consumption hub for Asian and "
                  "African exporters: GCC states apply a 5% common external tariff on most goods "
                  "and 5% VAT in most members, and India's CEPA with the UAE removes duty on a "
                  "large share of tariff lines. Verified buyer records for this region are still "
                  "being ingested — demand figures below are real; buyer coverage is labelled "
                  "honestly per country."),
        "facts": [
            "GCC customs union applies a 5% common external tariff on most goods, with exemptions for many foodstuffs and medicines.",
            "VAT is 5% in the UAE, Bahrain, Oman and Qatar (0% on some goods) and 15% in Saudi Arabia.",
            "India–UAE CEPA removes or reduces duty on a large share of tariff lines — check the preferential rate before quoting.",
            "Saudi Arabia requires SABER/SASO conformity for regulated products; the UAE requires ESMA/MoIAT conformity for many categories.",
        ],
    },
    "asia-pacific": {
        "name": "Asia Pacific", "demonym": "Asia-Pacific",
        "intro": ("Asia Pacific holds the largest import volumes on earth and the widest tariff "
                  "spread — from zero-duty Singapore and Hong Kong to heavily protected "
                  "agri-food lines. It is also the densest FTA network in the world (ASEAN, "
                  "RCEP, CPTPP, bilateral CEPAs), so the preferential rate for your origin often "
                  "matters more than the MFN rate."),
        "facts": [
            "Tariffs vary enormously by country and product — always check the specific destination, not a regional average.",
            "RCEP, ASEAN and bilateral CEPAs can cut duty to zero for qualifying origin — certificates of origin are decisive.",
            "Japan, South Korea and Australia enforce strict food-safety, labelling and quarantine rules on agri-food imports.",
            "Singapore and Hong Kong are low/zero-duty re-export hubs rather than final-consumption markets.",
        ],
    },
}

REGION_INDEX_MIN_GUIDES = 3


async def _region_rows(slug: str):
    """Matrix rows for a region, from the 24h matrix cache (computed on demand)."""
    cached = await db.seo_matrix_cache.find_one({"_id": "matrix:all:all"})
    fresh = cached and (datetime.now(timezone.utc)
                        - datetime.fromisoformat(cached["at"])).total_seconds() < 86400
    if fresh:
        return [r for r in cached["rows"] if r.get("region") == slug], cached["at"]
    own = await db.seo_matrix_cache.find_one({"_id": f"matrix:all:{slug}"})
    if own and (datetime.now(timezone.utc)
                - datetime.fromisoformat(own["at"])).total_seconds() < 86400:
        return own["rows"], own["at"]
    if cached:  # stale but real — serve it rather than block the page
        return [r for r in cached["rows"] if r.get("region") == slug], cached["at"]
    built = await matrix(region=slug, limit=1000)
    return built["rows"], datetime.now(timezone.utc).isoformat()


@router.get("/regions")
async def region_index():
    out = []
    for slug, hub in REGION_HUBS.items():
        rows, at = await _region_rows(slug)
        per_country = {}
        for r in rows:
            per_country[r["country"]] = max(per_country.get(r["country"], 0), r.get("buyers") or 0)
        out.append({
            "slug": slug, "name": hub["name"], "url": f"/regions/{slug}",
            "countries": len({r["country"] for r in rows}),
            "guides": sum(1 for r in rows if r["indexable"]),
            "buyers": sum(per_country.values()),
            "dataAsOf": at,
        })
    return {"total": len(out), "regions": out}


@router.get("/region/{slug}")
async def region_page(slug: str):
    hub = REGION_HUBS.get(slug)
    if not hub:
        raise HTTPException(status_code=404, detail="Unknown region")
    rows, at = await _region_rows(slug)
    if not rows:
        raise HTTPException(status_code=503, detail="Region data is being built — try again shortly")

    try:
        import content, engines
        corridor_slugs = set(content.CORRIDOR_DB.keys())
        profile_slugs = set(engines.COUNTRY_PROFILES.keys())
    except Exception:
        corridor_slugs, profile_slugs = set(), set()

    by_country = {}
    for r in rows:
        c = by_country.setdefault(r["country"], {"rows": [], "buyers": 0})
        c["rows"].append(r)
        c["buyers"] = max(c["buyers"], r.get("buyers") or 0)

    countries = []
    for cslug, agg in by_country.items():
        meta = COUNTRIES.get(cslug) or {}
        best = max(agg["rows"], key=lambda r: (r["indexable"], r.get("countryImportsUSD") or 0,
                                               r["dataScore"]))
        duties = [r["dutyRate"] for r in agg["rows"] if r.get("dutyRate") is not None]
        countries.append({
            "slug": cslug, "name": meta.get("name", cslug.replace("-", " ").title()),
            "code": meta.get("code", ""),
            "guides": [{"url": r["url"], "product": PRODUCTS[r["product"]]["name"],
                        "dutyRate": r["dutyRate"], "importsUSD": r.get("countryImportsUSD"),
                        "rank": r.get("countryRank")}
                       for r in sorted(agg["rows"], key=lambda r: -(r.get("countryImportsUSD") or 0))
                       if r["indexable"]][:4],
            "indexableGuides": sum(1 for r in agg["rows"] if r["indexable"]),
            "topImportsUSD": best.get("countryImportsUSD"),
            "topProduct": PRODUCTS[best["product"]]["name"],
            "dutyRange": ({"min": min(duties), "max": max(duties)} if duties else None),
            "buyers": agg["buyers"],
            "buyerCoverage": bool(agg["buyers"] > 0),
            "profileUrl": f"/countries/{cslug}" if cslug in profile_slugs else None,
            "corridorUrl": (f"/corridors/india-to-{cslug}"
                            if f"india-to-{cslug}" in corridor_slugs else None),
            "dutyToolUrl": f"/tools/duty-calculator?from={INDIA}&to={meta.get('code', '')}",
            "landedCostUrl": f"/tools/landed-cost-calculator?from={INDIA}&to={meta.get('code', '')}",
            "buyersUrl": f"/buyers?country={meta.get('name', '')}",
        })
    countries.sort(key=lambda c: (-(c["indexableGuides"]), -(c["topImportsUSD"] or 0)))

    products = {}
    for r in rows:
        p = products.setdefault(r["product"], {"slug": r["product"],
                                               "name": PRODUCTS[r["product"]]["name"],
                                               "sector": PRODUCTS[r["product"]]["sector"],
                                               "importsUSD": 0, "guides": 0, "markets": []})
        p["importsUSD"] += r.get("countryImportsUSD") or 0
        if r["indexable"]:
            p["guides"] += 1
            p["markets"].append({"url": r["url"], "country": (COUNTRIES.get(r["country"]) or {})
                                 .get("name", r["country"]),
                                 "importsUSD": r.get("countryImportsUSD")})
    product_list = sorted(products.values(), key=lambda p: -p["importsUSD"])
    for p in product_list:
        p["markets"] = sorted(p["markets"], key=lambda m: -(m["importsUSD"] or 0))[:5]

    indexable_guides = sum(1 for r in rows if r["indexable"])
    total_imports = sum(r.get("countryImportsUSD") or 0 for r in rows)
    buyer_total = sum(c["buyers"] for c in countries)
    indexable = bool(indexable_guides >= REGION_INDEX_MIN_GUIDES and total_imports > 0)

    return {
        "slug": slug, "name": hub["name"], "url": f"/regions/{slug}",
        "intro": hub["intro"], "facts": hub["facts"],
        "stats": {"countries": len(countries), "guides": indexable_guides,
                  "importsUSD": total_imports, "buyerRecords": buyer_total,
                  "buyerCoveredCountries": sum(1 for c in countries if c["buyerCoverage"])},
        "countries": countries, "products": product_list,
        "indexable": indexable,
        "indexNote": (None if indexable else
                      "This hub is not submitted for indexing yet — it needs at least "
                      f"{REGION_INDEX_MIN_GUIDES} product-market guides backed by real tariff and demand data."),
        "sources": [
            {"name": "World Bank WITS / UNCTAD TRAINS", "field": "import duty", "asOf": at[:10]},
            {"name": "OEC World (CEPII BACI / UN Comtrade)", "field": "import demand", "asOf": at[:10]},
            {"name": "Vametra Verified Buyer Intelligence (VBIE)", "field": "buyers", "asOf": at[:10]},
        ],
        "disclaimer": ("Tariff and demand figures carry the reporting year of their source and can lag "
                       "the current year. Verified buyer coverage differs by country and is stated per "
                       "country below — where it reads 'coverage expanding' we hold no screened records "
                       "for that market yet. Confirm duty and compliance in the destination's own tariff "
                       "schedule before contracting."),
        "dataAsOf": at,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
