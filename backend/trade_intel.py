"""Trade Intelligence engine — REAL global trade statistics.

Two authoritative sources, the freshest wins:
  * OEC World API (CEPII/BACI, derived from UN Comtrade) — FREE, no key. Always on.
  * UN Comtrade direct API — activates when COMTRADE_API_KEY is set (more current).

Exposes:
  * GET /api/trade-intel/stats?hs=330741   → top importers/exporters, world value, trend
  * GET /api/trade-intel/hs-search?q=coffee → resolve product text → HS6 code(s)
  * GET /api/trade-intel/status             → which sources are live
Results are cached (default 14 days — annual data changes slowly; refreshed bi-weekly).
Also importable by the Brain (trade_statistics engine).
"""
import os
import re
import logging
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, Query

from core import db

router = APIRouter(prefix="/trade-intel")

OEC_BASE = "https://api-v2.oec.world/tesseract"
OEC_CUBE = "trade_i_baci_a_22"  # HS6 rev. 2022 (covers 2022–2024)

COMTRADE_KEY = os.environ.get("COMTRADE_API_KEY", "").strip()
COMTRADE_BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

CACHE = db.trade_cache
HS_MAP_COLL = db.trade_hs_map

CACHE_TTL_DAYS = 14
TOP_N = 12

_HS_MAP: dict = {}  # "330741" -> {"id": 6330741, "desc": "Agarbatti..."}


def _now():
    return datetime.now(timezone.utc)


def _norm_hs(hs: str) -> str:
    """Keep digits, pad/truncate to HS6 (BACI granularity)."""
    digits = re.sub(r"\D", "", hs or "")
    return digits[:6] if digits else ""


# ---------------- HS6 directory (built from OEC, cached in Mongo) ----------------
async def _load_hs_map() -> dict:
    global _HS_MAP
    if _HS_MAP:
        return _HS_MAP
    docs = await HS_MAP_COLL.find({}, {"_id": 0}).to_list(20000)
    if docs:
        _HS_MAP = {d["hs6"]: {"id": d["id"], "desc": d["desc"]} for d in docs}
        return _HS_MAP
    # First run — fetch the member list once and persist.
    try:
        async with httpx.AsyncClient(timeout=60) as cx:
            r = await cx.get(f"{OEC_BASE}/members", params={"cube": OEC_CUBE, "level": "HS6"})
            members = r.json().get("members", [])
    except Exception as exc:
        logging.warning("OEC HS member load failed: %s", exc)
        return {}
    bulk, mp = [], {}
    for m in members:
        key = m.get("key")
        if key is None:
            continue
        hs6 = str(key % 1000000).zfill(6)
        desc = m.get("caption", "")
        mp[hs6] = {"id": key, "desc": desc}
        bulk.append({"hs6": hs6, "id": key, "desc": desc})
    if bulk:
        try:
            await HS_MAP_COLL.delete_many({})
            await HS_MAP_COLL.insert_many(bulk)
        except Exception as exc:
            logging.warning("HS map persist failed: %s", exc)
    _HS_MAP = mp
    return mp


async def hs_search(q: str, limit: int = 10):
    """Search the FULL HS6 directory (~16.8k codes) straight from Mongo so results never
    depend on a warm in-memory map."""
    ql = (q or "").strip()
    if not ql:
        return []
    digits = re.sub(r"\D", "", ql)
    if digits:
        cur = HS_MAP_COLL.find({"hs6": {"$regex": f"^{digits[:6]}"}}, {"_id": 0}).limit(limit * 3)
    else:
        safe = re.escape(ql)
        cur = HS_MAP_COLL.find({"desc": {"$regex": safe, "$options": "i"}}, {"_id": 0}).limit(limit * 3)
    rows = await cur.to_list(limit * 3)
    out = [{"hs6": r["hs6"], "description": r.get("desc", "")} for r in rows]
    out.sort(key=lambda x: len(x["description"]))
    return out[:limit]


HS_SECTION_NAMES = {
    1: "Animals & animal products", 2: "Vegetable products", 3: "Fats & oils",
    4: "Prepared foodstuffs, beverages & tobacco", 5: "Mineral products",
    6: "Chemicals & allied industries", 7: "Plastics & rubber", 8: "Hides, skins & leather",
    9: "Wood & wood products", 10: "Pulp, paper & paperboard", 11: "Textiles & apparel",
    12: "Footwear & headgear", 13: "Stone, cement, ceramics & glass",
    14: "Pearls, precious stones & metals", 15: "Base metals & articles",
    16: "Machinery & electrical equipment", 17: "Vehicles, aircraft & vessels",
    18: "Optical, medical & precision instruments", 19: "Arms & ammunition",
    20: "Miscellaneous manufactured articles", 21: "Works of art & antiques",
}


async def ensure_hs_directory():
    """Startup: index the directory and build it once if missing/partial."""
    try:
        await HS_MAP_COLL.create_index("hs6", unique=True)
        await HS_MAP_COLL.create_index("desc")
        count = await HS_MAP_COLL.count_documents({})
        if count < 5000:
            global _HS_MAP
            _HS_MAP = {}
            await HS_MAP_COLL.delete_many({})
            mp = await _load_hs_map()
            logging.info("HS directory built: %s codes", len(mp))
        else:
            logging.info("HS directory ready: %s codes", count)
    except Exception as exc:
        logging.warning("HS directory init failed: %s", exc)


@router.get("/hs-directory")
async def hs_directory(q: str = Query("", description="code prefix or description text"),
                       chapter: str = Query(""), section: int = Query(0),
                       limit: int = Query(50, le=500), offset: int = Query(0, ge=0)):
    """Complete HS6 directory with search + paging — powers every HS picker on the site."""
    query: dict = {}
    digits = re.sub(r"\D", "", q or "")
    if digits:
        query["hs6"] = {"$regex": f"^{digits[:6]}"}
    elif q.strip():
        query["desc"] = {"$regex": re.escape(q.strip()), "$options": "i"}
    if chapter:
        ch = re.sub(r"\D", "", chapter)[:2].zfill(2)
        query["hs6"] = {"$regex": f"^{ch}"}
    if section:
        query["id"] = {"$gte": section * 1000000, "$lt": (section + 1) * 1000000}
    total = await HS_MAP_COLL.count_documents(query)
    rows = await HS_MAP_COLL.find(query, {"_id": 0}).sort("hs6", 1).skip(offset).limit(limit).to_list(limit)
    return {
        "total": total, "limit": limit, "offset": offset,
        "results": [{"hs6": r["hs6"], "chapter": r["hs6"][:2],
                     "section": int(str(r["id"])[:-6]) if r.get("id") else None,
                     "description": r.get("desc", "")} for r in rows],
        "source": "World Customs Organization HS 2022 nomenclature (via OEC/BACI directory)",
    }


@router.get("/hs-chapters")
async def hs_chapters():
    """All 97 HS chapters with code counts — for grouped dropdowns."""
    pipeline = [{"$group": {"_id": {"$substr": ["$hs6", 0, 2]}, "count": {"$sum": 1},
                            "sample": {"$first": "$desc"}, "sid": {"$first": "$id"}}},
                {"$sort": {"_id": 1}}]
    rows = await HS_MAP_COLL.aggregate(pipeline).to_list(200)
    return {"count": len(rows),
            "chapters": [{"chapter": r["_id"], "codes": r["count"], "example": r["sample"],
                          "section": int(str(r["sid"])[:-6]) if r.get("sid") else None,
                          "sectionName": HS_SECTION_NAMES.get(
                              int(str(r["sid"])[:-6]) if r.get("sid") else 0, "")}
                         for r in rows]}


# ---------------- OEC source (free) ----------------
async def _oec_query(cx, drilldowns, hs_id, year=None):
    params = {"cube": OEC_CUBE, "drilldowns": drilldowns,
              "measures": "Trade Value", "HS6": hs_id}
    if year:
        params["Year"] = year
    r = await cx.get(f"{OEC_BASE}/data.jsonrecords", params=params)
    return r.json().get("data", [])


async def _oec_stats(hs6: str):
    mp = await _load_hs_map()
    meta = mp.get(hs6)
    if not meta:
        return None
    hs_id, desc = meta["id"], meta["desc"]
    try:
        async with httpx.AsyncClient(timeout=20) as cx:
            trend_rows = await _oec_query(cx, "Year", hs_id)
            if not trend_rows:
                return None
            trend = sorted(({"year": int(r["Year"]), "value": round(r["Trade Value"], 2)}
                            for r in trend_rows), key=lambda x: x["year"])
            latest = trend[-1]["year"]
            total = next((t["value"] for t in trend if t["year"] == latest), 0)

            imp = await _oec_query(cx, "Importer Country", hs_id, latest)
            exp = await _oec_query(cx, "Exporter Country", hs_id, latest)
    except Exception as exc:
        logging.warning("OEC stats failed for %s: %s", hs6, exc)
        return None

    def top(rows, label):
        rows = [r for r in rows if r.get("Trade Value")]
        rows.sort(key=lambda r: r["Trade Value"], reverse=True)
        return [{"country": r[label], "value": round(r["Trade Value"], 2),
                 "share": round(100 * r["Trade Value"] / total, 1) if total else 0}
                for r in rows[:TOP_N]]

    return {
        "source": "OEC World (BACI / UN Comtrade)",
        "sourceKey": "oec",
        "year": latest,
        "description": desc,
        "totalWorldTradeUSD": total,
        "topImporters": top(imp, "Importer Country"),
        "topExporters": top(exp, "Exporter Country"),
        "trend": trend,
    }


# ---------------- UN Comtrade source (key) ----------------
async def _comtrade_call(cx, flow, hs6, year):
    params = {"cmdCode": hs6, "flowCode": flow, "partnerCode": 0,
              "period": year, "reporterCode": "all", "includeDesc": "true"}
    r = await cx.get(COMTRADE_BASE, params=params,
                     headers={"Ocp-Apim-Subscription-Key": COMTRADE_KEY})
    if r.status_code != 200:
        return None
    return r.json().get("data", [])


async def _comtrade_stats(hs6: str):
    if not COMTRADE_KEY:
        return None
    this_year = _now().year
    candidates = [this_year - 1, this_year - 2, this_year - 3]
    try:
        async with httpx.AsyncClient(timeout=25) as cx:
            imp = exp = None
            used_year = None
            for y in candidates:
                imp = await _comtrade_call(cx, "M", hs6, y)
                if imp:
                    used_year = y
                    exp = await _comtrade_call(cx, "X", hs6, y) or []
                    break
            if not imp or used_year is None:
                return None
    except Exception as exc:
        logging.warning("Comtrade stats failed for %s: %s", hs6, exc)
        return None

    def rows_to_top(rows):
        clean = [{"country": r.get("reporterDesc"), "value": round(r.get("primaryValue") or 0, 2)}
                 for r in rows if (r.get("primaryValue") or 0) > 0 and r.get("reporterDesc") not in (None, "World")]
        clean.sort(key=lambda x: x["value"], reverse=True)
        return clean

    importers = rows_to_top(imp)
    exporters = rows_to_top(exp or [])
    total = sum(i["value"] for i in importers)
    for i in importers:
        i["share"] = round(100 * i["value"] / total, 1) if total else 0

    return {
        "source": "UN Comtrade",
        "sourceKey": "comtrade",
        "year": used_year,
        "description": "",
        "totalWorldTradeUSD": round(total, 2),
        "topImporters": importers[:TOP_N],
        "topExporters": exporters[:TOP_N],
        "trend": [],
    }


# ---------------- Orchestration: freshest source wins ----------------
async def trade_stats(hs: str, force: bool = False):
    hs6 = _norm_hs(hs)
    if len(hs6) < 6:
        return {"ok": False, "error": "Enter a valid 6–8 digit HS code (or search a product first)."}

    cache_id = f"stats:{hs6}"
    if not force:
        cached = await CACHE.find_one({"_id": cache_id})
        if cached and (_now() - datetime.fromisoformat(cached["refreshedAt"])).days < CACHE_TTL_DAYS:
            return cached["result"]

    oec = await _oec_stats(hs6)
    comtrade = await _comtrade_stats(hs6)

    sourcesAvailable = [s for s, ok in (("oec", bool(oec)), ("comtrade", bool(comtrade))) if ok]
    chosen = None
    if oec and comtrade:
        chosen = comtrade if comtrade["year"] >= oec["year"] else oec
    else:
        chosen = comtrade or oec

    if not chosen:
        return {"ok": False, "hsCode": hs6,
                "error": "No trade data found for this HS code. Try a different code."}

    # backfill description from the OEC directory if Comtrade didn't provide one
    if not chosen.get("description"):
        mp = await _load_hs_map()
        chosen["description"] = (mp.get(hs6) or {}).get("desc", "")

    result = {
        "ok": True,
        "hsCode": hs6,
        "description": chosen["description"],
        "source": chosen["source"],
        "sourceKey": chosen["sourceKey"],
        "year": chosen["year"],
        "totalWorldTradeUSD": chosen["totalWorldTradeUSD"],
        "topImporters": chosen["topImporters"],
        "topExporters": chosen["topExporters"],
        "trend": chosen["trend"],
        "sourcesAvailable": sourcesAvailable,
        "comtradeEnabled": bool(COMTRADE_KEY),
        "refreshedAt": _now().isoformat(),
    }
    await CACHE.replace_one({"_id": cache_id},
                            {"_id": cache_id, "result": result, "refreshedAt": _now().isoformat()},
                            upsert=True)
    return result


# ---------------- Routes ----------------
@router.get("/status")
async def status():
    mp = await _load_hs_map()
    return {"ok": True, "comtradeEnabled": bool(COMTRADE_KEY),
            "alwaysOn": "OEC World", "hsCodesIndexed": len(mp)}


@router.get("/hs-search")
async def hs_search_route(q: str = Query("", min_length=0), limit: int = 10):
    return {"results": await hs_search(q, limit)}


@router.get("/stats")
async def stats_route(hs: str = Query(...), force: bool = False):
    return await trade_stats(hs, force=force)


# ---------------- Full importer table (country-level detail for SEO pages) ----------------
async def importer_table(hs6: str, force: bool = False):
    """Every importing country for the latest year, cached. Lets a page show its own
    country's real import value and world rank instead of only a global top-N."""
    hs6 = _norm_hs(hs6)
    meta = (await _load_hs_map()).get(hs6)
    if not meta:
        return None
    cache_id = f"imptable:{hs6}"
    if not force:
        cached = await CACHE.find_one({"_id": cache_id})
        if cached and (_now() - datetime.fromisoformat(cached["refreshedAt"])).days < CACHE_TTL_DAYS:
            return cached["result"]
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cx:
            years = await _oec_query(cx, "Year", meta["id"])
            if not years:
                return None
            latest = max(int(r["Year"]) for r in years)
            rows = await _oec_query(cx, "Importer Country", meta["id"], latest)
    except Exception as exc:
        logging.warning("OEC importer table failed for %s: %s", hs6, exc)
        return None
    clean = [{"country": r.get("Importer Country"), "value": round(r.get("Trade Value") or 0, 2)}
             for r in rows if (r.get("Trade Value") or 0) > 0]
    clean.sort(key=lambda r: -r["value"])
    total = sum(r["value"] for r in clean)
    for i, r in enumerate(clean, 1):
        r["rank"] = i
        r["share"] = round(100 * r["value"] / total, 2) if total else 0
    result = {"year": latest, "total": total, "count": len(clean), "rows": clean,
              "source": "OEC World (CEPII BACI / UN Comtrade)"}
    await CACHE.replace_one({"_id": cache_id},
                            {"_id": cache_id, "result": result, "refreshedAt": _now().isoformat()},
                            upsert=True)
    return result


async def importer_detail(hs6: str, country_name: str):
    table = await importer_table(hs6)
    if not table:
        return None
    row = next((r for r in table["rows"] if (r["country"] or "").lower() == (country_name or "").lower()), None)
    return {"year": table["year"], "worldImportsUSD": table["total"], "countriesReporting": table["count"],
            "source": table["source"],
            "countryImportsUSD": (row or {}).get("value"),
            "countryShare": (row or {}).get("share"),
            "countryRank": (row or {}).get("rank")}
