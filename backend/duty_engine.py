"""Duty & Benefits engine — REAL tariffs + India duty + RoDTEP, weekly auto-refresh.

Sources:
  * Global import tariffs: World Bank WITS (UNCTAD TRAINS) — applied/MFN & preferential
    rates by reporter (destination) × partner (origin) × HS6. Free, no key.
  * India import duty: WITS MFN (=BCD) + standard IGST slab + 10% Social Welfare Surcharge.
  * India export benefit: DGFT RoDTEP schedule (Appendix 4R, chapter-level), Mongo-seeded.

Refresh: APScheduler runs weekly (7 days) → clears the tariff cache + restamps
`duty_meta.lastRefresh`. A manual "refresh now" is exposed to admins.
Importable by the Brain (duty_benefits engine). Everything cached in Mongo.
"""
import re
import logging
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, Query, Depends

from core import db, require_admin

router = APIRouter(prefix="/duty")

WITS_BASE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN"

CACHE = db.duty_cache
RODTEP = db.rodtep_rates
META = db.duty_meta

CACHE_TTL_DAYS = 7
REFRESH_DAYS = 7

# ---- Country directory (ISO numeric used by WITS) — major global traders ----
COUNTRIES = [
    ("356", "India"), ("842", "United States"), ("156", "China"), ("784", "United Arab Emirates"),
    ("826", "United Kingdom"), ("276", "Germany"), ("392", "Japan"), ("36", "Australia"),
    ("682", "Saudi Arabia"), ("702", "Singapore"), ("250", "France"), ("380", "Italy"),
    ("124", "Canada"), ("76", "Brazil"), ("410", "South Korea"), ("484", "Mexico"),
    ("528", "Netherlands"), ("724", "Spain"), ("643", "Russia"), ("792", "Turkey"),
    ("360", "Indonesia"), ("764", "Thailand"), ("458", "Malaysia"), ("704", "Vietnam"),
    ("710", "South Africa"), ("818", "Egypt"), ("566", "Nigeria"), ("404", "Kenya"),
    ("586", "Pakistan"), ("050", "Bangladesh"), ("144", "Sri Lanka"), ("608", "Philippines"),
    ("756", "Switzerland"), ("056", "Belgium"), ("616", "Poland"), ("752", "Sweden"),
    ("204", "Benin"), ("634", "Qatar"), ("512", "Oman"), ("414", "Kuwait"),
    ("48", "Bahrain"), ("32", "Argentina"), ("152", "Chile"), ("170", "Colombia"),
    ("604", "Peru"), ("376", "Israel"), ("348", "Hungary"), ("203", "Czechia"),
    ("620", "Portugal"), ("300", "Greece"), ("372", "Ireland"), ("578", "Norway"),
    ("208", "Denmark"), ("246", "Finland"), ("40", "Austria"), ("554", "New Zealand"),
]
NAME_BY_CODE = {c: n for c, n in COUNTRIES}

# ISO numeric country code → local currency (used for auto-detected dual currency).
CURRENCY_BY_CODE = {
    "356": "INR", "842": "USD", "156": "CNY", "784": "AED", "826": "GBP", "276": "EUR",
    "392": "JPY", "36": "AUD", "682": "SAR", "702": "SGD", "250": "EUR", "380": "EUR",
    "124": "CAD", "76": "BRL", "410": "KRW", "484": "MXN", "528": "EUR", "724": "EUR",
    "643": "RUB", "792": "TRY", "360": "IDR", "764": "THB", "458": "MYR", "704": "VND",
    "710": "ZAR", "818": "EGP", "566": "NGN", "404": "KES", "586": "PKR", "050": "BDT",
    "144": "LKR", "608": "PHP", "756": "CHF", "056": "EUR", "616": "PLN", "752": "SEK",
    "204": "XOF", "634": "QAR", "512": "OMR", "414": "KWD", "48": "BHD", "32": "ARS",
    "152": "CLP", "170": "COP", "604": "PEN", "376": "ILS", "348": "HUF", "203": "CZK",
    "620": "EUR", "300": "EUR", "372": "EUR", "578": "NOK", "208": "DKK", "246": "EUR",
    "40": "EUR", "554": "NZD",
}

# ---- India domestic add-ons ----
# IGST slab by HS chapter (2-digit); default 18%.
IGST_BY_CHAPTER = {
    **{f"{c:02d}": 5 for c in range(1, 25)},   # food/agri broadly 5%
    "30": 12, "48": 12, "49": 5, "61": 12, "62": 12, "63": 12, "64": 18,
    "71": 3, "84": 18, "85": 18, "87": 28, "88": 5, "90": 18, "94": 18,
}
SWS_RATE = 10.0  # % of BCD

# ---- RoDTEP chapter-level schedule (DGFT Appendix 4R, indicative) ----
RODTEP_BY_CHAPTER = {
    "03": 2.5, "07": 1.4, "08": 1.7, "09": 1.4, "10": 1.0, "13": 1.0, "15": 1.0,
    "16": 2.5, "17": 1.4, "18": 1.4, "19": 2.0, "20": 2.4, "21": 2.0, "22": 2.0,
    "25": 0.8, "27": 0.5, "28": 1.0, "29": 1.4, "30": 0.7, "32": 1.4, "33": 1.4,
    "34": 1.4, "38": 1.4, "39": 1.0, "40": 1.4, "41": 1.4, "42": 2.4, "44": 1.5,
    "48": 1.4, "49": 1.0, "52": 2.4, "54": 2.4, "55": 2.4, "57": 2.6, "58": 2.6,
    "61": 4.3, "62": 4.3, "63": 2.8, "64": 2.5, "68": 1.4, "69": 2.0, "70": 1.7,
    "71": 0.5, "72": 1.4, "73": 1.4, "74": 1.4, "76": 1.4, "82": 1.4, "83": 1.4,
    "84": 1.0, "85": 1.4, "87": 1.4, "90": 1.4, "94": 2.0, "95": 2.0, "96": 2.4,
}


def _now():
    return datetime.now(timezone.utc)


def _hs6(hs):
    return re.sub(r"\D", "", hs or "")[:6]


# ---------------- WITS tariff (parsed from SDMX XML) ----------------
async def _wits_obs(reporter, partner, hs6):
    """Return (rate%, tariffType, year) for the latest year with data, or None."""
    this_year = _now().year
    years = [this_year - y for y in range(2, 8)]  # WITS lags ~2yr; cap window for latency
    async with httpx.AsyncClient(timeout=20) as cx:
        for yr in years:
            url = f"{WITS_BASE}/reporter/{reporter}/partner/{partner}/product/{hs6}/year/{yr}/datatype/reported"
            try:
                r = await cx.get(url)
            except Exception:
                continue
            if r.status_code != 200 or "NoRecordsFound" in r.text:
                continue
            obs = re.findall(r'<Obs\b[^>]*OBS_VALUE="([0-9.]+)"[^>]*?TARIFFTYPE="([A-Z]+)"', r.text)
            if obs:
                val, ttype = obs[0]
                return round(float(val), 2), ttype, yr
    return None


async def wits_tariff(reporter, partner, hs6):
    key = f"wits:{reporter}:{partner}:{hs6}"
    cached = await CACHE.find_one({"_id": key})
    if cached and (_now() - datetime.fromisoformat(cached["at"])).days < CACHE_TTL_DAYS:
        return cached["val"]
    res = await _wits_obs(reporter, partner, hs6)
    val = None
    if res:
        rate, ttype, yr = res
        val = {"rate": rate, "type": ttype, "year": yr}
    await CACHE.replace_one({"_id": key}, {"_id": key, "val": val, "at": _now().isoformat()}, upsert=True)
    return val


# ---------------- RoDTEP ----------------
async def seed_rodtep(force=False):
    if not force and await RODTEP.count_documents({}) > 0:
        return
    await RODTEP.delete_many({})
    docs = [{"chapter": ch, "rate": rate, "source": "DGFT Appendix 4R (RoDTEP schedule)",
             "effectiveDate": "2026-05-01"} for ch, rate in RODTEP_BY_CHAPTER.items()]
    if docs:
        await RODTEP.insert_many(docs)


async def rodtep_rate(hs6):
    ch = hs6[:2]
    doc = await RODTEP.find_one({"chapter": ch}, {"_id": 0})
    if not doc:
        return None
    return {"rate": doc["rate"], "chapter": ch, "source": doc["source"],
            "effectiveDate": doc["effectiveDate"]}


# ---------------- Unified lookup ----------------
async def duty_and_benefits(hs6, origin=None, destination=None):
    hs6 = _hs6(hs6)
    if len(hs6) < 6:
        return {"ok": False, "error": "Enter a valid 6-digit HS code."}

    origin = origin or ""
    destination = destination or "356"  # default destination India
    out = {
        "ok": True, "hsCode": hs6,
        "origin": {"code": origin, "name": NAME_BY_CODE.get(origin, "")},
        "destination": {"code": destination, "name": NAME_BY_CODE.get(destination, "")},
        "importDuty": None, "preferential": None, "indiaBreakdown": None,
        "exportBenefit": None, "notes": [],
    }

    # Import duty levied by destination (MFN baseline)
    mfn = await wits_tariff(destination, "000", hs6)
    if mfn:
        out["importDuty"] = {"rate": mfn["rate"], "type": "MFN (applied)", "year": mfn["year"],
                             "source": "World Bank WITS / UNCTAD TRAINS"}
    # Preferential rate for the specific origin (if any)
    if origin and origin != destination:
        pref = await wits_tariff(destination, origin, hs6)
        if pref and (not mfn or pref["rate"] < mfn["rate"]):
            out["preferential"] = {"rate": pref["rate"], "type": pref["type"], "year": pref["year"],
                                   "source": "World Bank WITS / UNCTAD TRAINS"}

    # India import breakdown (BCD + IGST + SWS)
    if destination == "356":
        bcd = (out["preferential"] or out["importDuty"] or {}).get("rate")
        if bcd is not None:
            igst = IGST_BY_CHAPTER.get(hs6[:2], 18)
            sws = round(bcd * SWS_RATE / 100, 2)
            out["indiaBreakdown"] = {
                "basicCustomsDuty": bcd, "socialWelfareSurcharge": sws, "swsRate": SWS_RATE,
                "igst": igst, "note": "BCD from WITS applied rate; IGST standard slab; SWS = 10% of BCD. IGST is creditable for registered importers.",
            }

    # India export benefit (RoDTEP) when origin is India
    if origin == "356":
        rb = await rodtep_rate(hs6)
        if rb:
            out["exportBenefit"] = {"scheme": "RoDTEP", "rate": rb["rate"], "unit": "% of FOB",
                                    "source": rb["source"], "effectiveDate": rb["effectiveDate"],
                                    "note": "Remission of Duties & Taxes on Exported Products — tradable e-scrip. Confirm exact 8-digit rate in Appendix 4R."}

    if not out["importDuty"] and not out["exportBenefit"]:
        out["notes"].append("No tariff record found for this combination — try World as origin or a different year/country.")
    meta = await get_meta()
    out["refreshedAt"] = meta.get("lastRefresh")
    out["sources"] = ["World Bank WITS / UNCTAD TRAINS", "DGFT RoDTEP (Appendix 4R)"]
    return out


# ---------------- Meta + refresh ----------------
async def get_meta():
    doc = await META.find_one({"_id": "duty"}, {"_id": 0})
    if not doc:
        doc = {"lastRefresh": _now().isoformat(),
               "nextRefresh": (_now() + timedelta(days=REFRESH_DAYS)).isoformat(),
               "sources": ["World Bank WITS / UNCTAD TRAINS", "DGFT RoDTEP (Appendix 4R)"]}
        await META.replace_one({"_id": "duty"}, {"_id": "duty", **doc}, upsert=True)
    return doc


async def refresh_all():
    """Weekly job + manual: clear stale tariff cache, reseed RoDTEP, restamp."""
    try:
        await CACHE.delete_many({})
        await seed_rodtep(force=True)
        stamp = {"lastRefresh": _now().isoformat(),
                 "nextRefresh": (_now() + timedelta(days=REFRESH_DAYS)).isoformat(),
                 "sources": ["World Bank WITS / UNCTAD TRAINS", "DGFT RoDTEP (Appendix 4R)"]}
        await META.replace_one({"_id": "duty"}, {"_id": "duty", **stamp}, upsert=True)
        logging.info("Duty & Benefits data refreshed at %s", stamp["lastRefresh"])
        return stamp
    except Exception as exc:
        logging.warning("Duty refresh failed: %s", exc)
        return await get_meta()


_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler:
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(refresh_all, "interval", days=REFRESH_DAYS, id="duty_refresh",
                           next_run_time=_now() + timedelta(minutes=1))
        _scheduler.start()
        logging.info("Duty refresh scheduler started (every %d days)", REFRESH_DAYS)
    except Exception as exc:
        logging.warning("Could not start duty scheduler: %s", exc)


# ---------------- Routes ----------------
@router.get("/countries")
async def countries():
    return {"countries": [{"code": c, "name": n} for c, n in sorted(COUNTRIES, key=lambda x: x[1])]}


@router.get("/meta")
async def meta_route():
    return await get_meta()


@router.get("/lookup")
async def lookup(hs: str = Query(...), origin: str = Query(""), destination: str = Query("356")):
    return await duty_and_benefits(hs, origin=origin, destination=destination)


@router.post("/refresh")
async def manual_refresh(_: dict = Depends(require_admin)):
    return await refresh_all()
