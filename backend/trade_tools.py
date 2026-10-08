"""Free /tools endpoints. Every figure here comes from a real engine:
HS directory (WCO HS-2022 via trade_intel), DGFT RoDTEP + WITS tariffs (duty_engine).
The old category-based mock calculators were removed — the /tools pages now embed the
Customs & Compliance Engine components directly."""
import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

import duty_engine
import trade_intel
from core import db

router = APIRouter()

# Curated compliance knowledge for flagship Indian export lines (documents, benefits,
# customs notes). Used by the Brain knowledge base, site search and /hsn/{code} pages.
HSN_DB = {
    "10063020": {
        "code": "10063020", "title": "Basmati Rice (semi-milled / milled)",
        "gst": "0%", "rodtep": "Eligible", "drawback": "AIR schedule",
        "category": "Agriculture & Food",
        "exportBenefits": ["APEDA support", "RoDTEP scrip", "Interest equalisation 2%"],
        "customsNotes": "FOB Mundra preferred; APEDA Certificate of Authenticity mandatory.",
        "documents": ["Commercial Invoice", "Packing List", "Phytosanitary Certificate", "Certificate of Origin", "APEDA RCMC"],
        "relatedProducts": ["basmati-rice", "spices"],
        "opportunities": "GCC, Iran, USA and the EU are the leading destination markets.",
    },
    "33074100": {
        "code": "33074100", "title": "Agarbatti & similar room fragrances",
        "gst": "5%", "rodtep": "Eligible", "drawback": "AIR schedule",
        "category": "FMCG",
        "exportBenefits": ["EPCH RCMC", "RoDTEP scrip", "MSME interest subvention 2%"],
        "customsNotes": "Classified under Chapter 33 — ensure correct sub-heading on shipping bill.",
        "documents": ["Commercial Invoice", "Packing List", "EPCH Certificate", "Halal (for GCC)", "MSDS"],
        "relatedProducts": ["agarbatti", "handicrafts"],
        "opportunities": "UAE, USA, UK and Malaysia are the leading destination markets.",
    },
    "09024020": {
        "code": "09024020", "title": "Black Tea (in bulk, > 3kg)",
        "gst": "5%", "rodtep": "Eligible", "drawback": "AIR schedule",
        "category": "Agriculture & Food",
        "exportBenefits": ["Tea Board RCMC", "RoDTEP", "Interest equalisation 2%"],
        "customsNotes": "Tea Board export inspection certificate is mandatory.",
        "documents": ["Commercial Invoice", "Phytosanitary", "Tea Board EIC", "Certificate of Origin", "Health Certificate"],
        "relatedProducts": ["spices"],
        "opportunities": "Russia, UAE, UK and Iran are the leading destination markets.",
    },
    "30049099": {
        "code": "30049099", "title": "Pharmaceuticals — other formulations",
        "gst": "12%", "rodtep": "Eligible", "drawback": "AIR schedule",
        "category": "Pharmaceuticals",
        "exportBenefits": ["Pharmexcil RCMC", "RoDTEP", "PLI scheme"],
        "customsNotes": "CDSCO / Form-10 export NOC required for restricted molecules.",
        "documents": ["Commercial Invoice", "Drug Manufacturing License", "GMP Certificate", "Free Sale Certificate", "Pharmexcil RCMC"],
        "relatedProducts": ["pharmaceuticals"],
        "opportunities": "USA, UK and Africa lead; India is among the world's largest generic exporters.",
    },
    "62034299": {
        "code": "62034299", "title": "Men's cotton trousers (woven)",
        "gst": "12%", "rodtep": "Eligible", "drawback": "AIR schedule",
        "category": "Textiles & Apparel",
        "exportBenefits": ["AEPC RCMC", "RoSCTL", "RoDTEP", "MSME"],
        "customsNotes": "Self-certify under FTA; verify yarn-forward rules for UK/EU.",
        "documents": ["Commercial Invoice", "Packing List", "AEPC RCMC", "Certificate of Origin (FTA)", "Inspection Certificate"],
        "relatedProducts": ["textiles"],
        "opportunities": "USA, UK, EU and GCC are the leading destination markets.",
    },
}

STOP = {"the", "and", "for", "with", "of", "a", "an", "in", "to", "or", "other", "fresh", "dried", "long", "grain", "aromatic", "premium", "quality", "export", "indian", "india"}

# Trade names exporters actually type → official HS6 lines (the WCO text rarely contains them).
TRADE_ALIASES = {
    "basmati": ["100630"], "rice": ["100630", "100640", "100620"], "agarbatti": ["330741"], "incense": ["330741"],
    "dhoop": ["330741"], "turmeric": ["091030"], "haldi": ["091030"], "cumin": ["090931"], "jeera": ["090931"],
    "cardamom": ["090831"], "pepper": ["090411"], "chilli": ["090421", "090422"], "chili": ["090421"],
    "coriander": ["090921"], "ginger": ["091011"], "garlic": ["070320"], "onion": ["070310"],
    "tomato": ["070200"], "potato": ["070190"], "mango": ["080450"], "grapes": ["080610"], "banana": ["080390"],
    "pomegranate": ["081090"], "tea": ["090240", "090230"], "coffee": ["090111"], "sugar": ["170114", "170199"],
    "t-shirt": ["610910"], "tshirt": ["610910"], "tee": ["610910"], "shirt": ["620520", "610510"],
    "trousers": ["620342"], "jeans": ["620342"], "denim": ["520942"], "bedsheet": ["630231"], "bed linen": ["630231"],
    "towel": ["630260"], "saree": ["540752", "500720"], "kurta": ["620640"], "leather bag": ["420221"],
    "shoes": ["640399"], "footwear": ["640399"], "medicine": ["300490"], "tablets": ["300490"], "paracetamol": ["300490"],
    "generic": ["300490"], "ayurvedic": ["300490"], "pump": ["841370"], "valve": ["848180"], "bearing": ["848210"],
    "fastener": ["731815"], "bolt": ["731815"], "steel structure": ["730890"], "auto parts": ["870899"],
    "smartphone": ["851713"], "mobile": ["851713"], "laptop": ["847130"], "jewellery": ["711319"], "jewelry": ["711319"],
    "diamond": ["710239"], "gold": ["710812"], "marble": ["680221"], "granite": ["680293"], "cashew": ["080132"],
    "peanut": ["120242"], "groundnut": ["120242"], "sesame": ["120740"], "soybean": ["120190"], "wheat": ["100199"],
    "maize": ["100590"], "corn": ["100590"], "honey": ["040900"], "ghee": ["040590"], "milk powder": ["040210"],
    "handicraft": ["442090"], "brass": ["741999"], "carpet": ["570110"], "rug": ["570110"], "cement": ["252329"],
    "plastic": ["392690"], "rubber": ["401110"], "tyre": ["401110"], "tire": ["401110"], "solar": ["854143"],
    "cable": ["854449"], "transformer": ["850423"], "motor": ["850152"], "fish": ["030617", "030389"],
    "shrimp": ["030617"], "prawn": ["030617"], "buffalo meat": ["020230"], "beef": ["020230"], "cotton": ["520100"],
    "yarn": ["520512"], "fabric": ["520812"], "sandalwood": ["330129"], "essential oil": ["330129"],
    "castor oil": ["151530"], "coconut": ["080111"], "jute": ["530310"], "silk": ["500720"],
}


def _words(text: str):
    return [w for w in re.findall(r"[a-z]{3,}", (text or "").lower()) if w not in STOP]


async def _directory_match(product: str, description: str, limit: int = 6):
    """Rank HS6 codes: trade-name aliases first, then weighted word overlap with the WCO text."""
    pl = (product or "").lower().strip()
    digits = re.sub(r"\D", "", product or "")
    if len(digits) >= 4:
        rows = await trade_intel.HS_MAP_COLL.find({"hs6": {"$regex": f"^{digits[:6]}"}}, {"_id": 0}).limit(limit).to_list(limit)
        return [{"hs6": r["hs6"], "desc": r.get("desc", ""), "score": 10} for r in rows]
    alias_codes = []
    for alias, codes in TRADE_ALIASES.items():
        if alias in pl or alias in (description or "").lower():
            alias_codes += [c for c in codes if c not in alias_codes]
    pwords, dwords = _words(product), _words(description)
    words = list(dict.fromkeys(pwords + dwords))
    if not words and not alias_codes:
        return []
    ors = [{"desc": {"$regex": re.escape(w), "$options": "i"}} for w in words]
    if alias_codes:
        ors.append({"hs6": {"$in": alias_codes}})
    rows = await trade_intel.HS_MAP_COLL.find({"$or": ors}, {"_id": 0}).limit(400).to_list(400)
    scored = []
    for r in rows:
        d = (r.get("desc") or "").lower()
        score = sum(3 for w in pwords if w in d) + sum(1 for w in dwords if w in d)
        if pl and pl in d:
            score += 3
        if r["hs6"] in alias_codes:
            score += 10 - alias_codes.index(r["hs6"]) * 0.5
        scored.append({"hs6": r["hs6"], "desc": r.get("desc", ""), "score": score - len(d) / 400})
    scored.sort(key=lambda x: -x["score"])
    return scored[:limit]


def _curated(hs6: str):
    return next((h for k, h in HSN_DB.items() if k[:6] == hs6), None)


def _igst(hs6: str):
    c = _curated(hs6)
    if c and c.get("gst", "").rstrip("%").isdigit():
        return int(c["gst"].rstrip("%"))
    return duty_engine.IGST_BY_CHAPTER.get(hs6[:2], 18)


async def _enrich(row: dict, destination: str, with_duty: bool):
    hs6 = row["hs6"]
    rod = await duty_engine.rodtep_rate(hs6)
    section = trade_intel.HS_SECTION_NAMES
    sec_id = None
    try:
        meta = (await trade_intel._load_hs_map()).get(hs6)
        sec_id = int(str(meta["id"])[:-6]) if meta and meta.get("id") else None
    except Exception:
        pass
    duty = None
    if with_duty and destination:
        try:
            duty = await asyncio.wait_for(duty_engine.wits_tariff(destination, "000", hs6), timeout=25)
        except Exception:
            duty = None
    return {
        "code": hs6, "title": row["desc"], "chapter": hs6[:2],
        "section": sec_id, "sectionName": section.get(sec_id, "") if sec_id else "",
        "matchScore": round(max(row.get("score", 0), 0), 1),
        "rodtep": {"rate": rod["rate"], "unit": "% of FOB", "source": rod["source"], "effectiveDate": rod["effectiveDate"]} if rod else None,
        "igstSlab": _igst(hs6),
        "igstSource": "curated line" if _curated(hs6) else "chapter default",
        "importDuty": {"rate": duty["rate"], "type": duty["type"], "year": duty["year"],
                       "destination": duty_engine.NAME_BY_CODE.get(destination, destination),
                       "source": "World Bank WITS / UNCTAD TRAINS"} if duty else None,
    }


class HsnFindRequest(BaseModel):
    productName: str = ""
    description: Optional[str] = ""
    hs6: Optional[str] = ""
    destination: Optional[str] = ""  # ISO numeric, e.g. 784


@router.post("/hsn-finder")
async def hsn_finder(payload: HsnFindRequest):
    if payload.hs6:
        rows = await trade_intel.HS_MAP_COLL.find({"hs6": payload.hs6[:6]}, {"_id": 0}).limit(1).to_list(1)
        matches = [{"hs6": r["hs6"], "desc": r.get("desc", ""), "score": 10} for r in rows]
    else:
        matches = await _directory_match(payload.productName, payload.description or "")
    results = await asyncio.gather(*[_enrich(m, payload.destination or "", i < 3) for i, m in enumerate(matches)])
    meta = await duty_engine.get_meta()
    return {
        "query": payload.productName or payload.hs6, "destination": payload.destination or "",
        "destinationName": duty_engine.NAME_BY_CODE.get(payload.destination or "", ""),
        "results": list(results), "total": len(results),
        "sources": ["WCO HS 2022 nomenclature", "DGFT RoDTEP Appendix 4R", "World Bank WITS / UNCTAD TRAINS"],
        "refreshedAt": meta.get("lastRefresh"),
        "note": "HS6 is the international level; confirm the Indian 8-digit ITC-HS line on your shipping bill. IGST slab is the chapter-level default — verify the exact rate for your line.",
    }


@router.get("/hsn/{code}")
async def hsn_detail(code: str):
    digits = re.sub(r"\D", "", code)
    hs6 = digits[:6]
    curated = HSN_DB.get(digits) or next((h for k, h in HSN_DB.items() if k[:6] == hs6), None)
    rows = await trade_intel.HS_MAP_COLL.find({"hs6": hs6}, {"_id": 0}).limit(1).to_list(1) if len(hs6) == 6 else []
    if not rows and not curated:
        return JSONResponse(status_code=404, content={"error": "HSN not found"})
    desc = rows[0].get("desc", "") if rows else curated["title"]
    real = await _enrich({"hs6": hs6, "desc": desc, "score": 10}, "", False)
    defaults = {
        "gst": f"{real['igstSlab']}% (IGST slab)", "drawback": "AIR schedule — verify line",
        "category": real.get("sectionName") or f"HS chapter {hs6[:2]}",
        "exportBenefits": ["RoDTEP e-scrip (DGFT Appendix 4R)", "Duty Drawback (AIR)", "Interest Equalisation (eligible MSMEs)"],
        "documents": ["Commercial Invoice", "Packing List", "Shipping Bill", "Certificate of Origin", "Bill of Lading / Airway Bill"],
        "customsNotes": "HS6 is the international level — confirm the Indian 8-digit ITC-HS line and any product-specific certificates with your CHA.",
        "opportunities": "Use Product Research for live import demand by country and the Duty Calculator for the applied tariff at your destination.",
        "relatedProducts": [],
    }
    out = {**defaults, **(curated or {}), **real, "code": digits if len(digits) == 8 else hs6, "hs6": hs6,
           "title": curated["title"] if curated else desc, "hsDescription": desc}
    if real.get("rodtep"):
        out["rodtep"] = f"Eligible · {real['rodtep']['rate']}% of FOB (DGFT Appendix 4R, chapter-level)"
    return out


# ----- Suppliers (sample directory; marked as such in the payload) -----
SAMPLE_SUPPLIERS = [
    {"company": "KRBL Ltd", "country": "IN", "city": "New Delhi", "verified": True, "category": "Agriculture & Food", "products": "Basmati Rice"},
    {"company": "Mysore Sandal Soaps", "country": "IN", "city": "Bengaluru", "verified": True, "category": "FMCG", "products": "Agarbatti · Soaps"},
    {"company": "ITC Spices", "country": "IN", "city": "Cochin", "verified": True, "category": "Agriculture & Food", "products": "Spices"},
    {"company": "Welspun Cotton", "country": "IN", "city": "Anjar", "verified": True, "category": "Textiles", "products": "Home Textiles"},
    {"company": "Cipla Exports", "country": "IN", "city": "Mumbai", "verified": True, "category": "Pharmaceuticals", "products": "Generic Pharma"},
    {"company": "Mahindra Auto Components", "country": "IN", "city": "Pune", "verified": True, "category": "Engineering", "products": "Auto Parts"},
]


@router.get("/suppliers")
async def suppliers(q: str = "", country: str = "", category: str = ""):
    res = SAMPLE_SUPPLIERS
    if q:
        ql = q.lower()
        res = [s for s in res if ql in s["company"].lower() or ql in s["products"].lower()]
    if country:
        res = [s for s in res if s["country"].upper() == country.upper()]
    if category:
        res = [s for s in res if category.lower() in s["category"].lower()]
    return {"suppliers": res, "total": len(res), "lockedExtras": True, "sample": True}


# ----- Export readiness -----
class ReadinessRequest(BaseModel):
    iec: bool = False
    gst: bool = False
    website: bool = False
    packagingReady: bool = False
    certifications: bool = False
    experience: bool = False
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


@router.post("/export-readiness")
async def export_readiness(payload: ReadinessRequest):
    flags = [payload.iec, payload.gst, payload.website, payload.packagingReady, payload.certifications, payload.experience]
    score = int(sum(1 for f in flags if f) / len(flags) * 100)
    band = "Beginner" if score < 40 else "Intermediate" if score < 75 else "Export-ready"
    recs = []
    if not payload.iec: recs.append("Apply for an IEC code at DGFT — it's free and the foundational requirement.")
    if not payload.gst: recs.append("Get your GST registration — mandatory for tax credit on inputs.")
    if not payload.website: recs.append("Build a credible website — international buyers search for you before they call.")
    if not payload.packagingReady: recs.append("Upgrade packaging — export-grade cartons, labels, multilingual instructions.")
    if not payload.certifications: recs.append("Earn one anchor certification — ISO 22000 / GMP / Halal / Organic.")
    if not payload.experience: recs.append("Start with a trial 1-MT shipment to a friendly market like UAE.")

    if payload.email:
        await db.leads.insert_one({
            "id": str(uuid.uuid4()),
            "name": payload.name, "email": payload.email, "phone": payload.phone,
            "source": "export-readiness",
            "score": score, "createdAt": datetime.now(timezone.utc).isoformat(),
        })

    return {
        "score": score,
        "band": band,
        "summary": f"You scored {score}/100 — {band}.",
        "recommendations": recs or ["You're export-ready. Connect with buyers on the Vametra AI app."],
        "leadCaptured": bool(payload.email),
    }
