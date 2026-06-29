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
    mp = await _load_hs_map()
    ql = (q or "").strip().lower()
    if not ql:
        return []
    digits = re.sub(r"\D", "", ql)
    out = []
    if digits:  # numeric → prefix match on code
        for hs6, v in mp.items():
            if hs6.startswith(digits[:6]):
                out.append({"hs6": hs6, "description": v["desc"]})
    else:  # text → match description
        for hs6, v in mp.items():
            if ql in v["desc"].lower():
                out.append({"hs6": hs6, "description": v["desc"]})
    out.sort(key=lambda x: len(x["description"]))
    return out[:limit]


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
