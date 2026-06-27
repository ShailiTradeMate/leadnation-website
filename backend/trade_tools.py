from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


# Duty Calculator
DUTY_TABLE = {
    # (export, import, category) -> (duty_pct, vat_pct, extra_pct)
    "default": (0.085, 0.05, 0.01),
}
CATEGORY_RATES = {
    "Agriculture & Food": 0.06,
    "Textiles & Apparel": 0.10,
    "Electronics": 0.05,
    "Pharmaceuticals": 0.03,
    "Machinery": 0.075,
    "Chemicals": 0.07,
    "Automobiles & Parts": 0.15,
    "Gems & Jewellery": 0.025,
    "Furniture & Handicrafts": 0.08,
    "Energy & Petrochemicals": 0.04,
}
ROUTE_PREF = {
    # Preferential routes (lower duty)
    ("IN", "AE"): -0.04,
    ("IN", "JP"): -0.03,
    ("IN", "SG"): -0.05,
    ("AE", "IN"): -0.04,
}
VAT_BY_COUNTRY = {
    "IN": 0.18, "AE": 0.05, "US": 0.0, "GB": 0.20, "DE": 0.19, "FR": 0.20,
    "JP": 0.10, "SG": 0.09, "CN": 0.13, "BR": 0.17, "ZA": 0.15, "AU": 0.10,
    "NL": 0.21, "SA": 0.15, "KR": 0.10, "VN": 0.10, "AM": 0.20,
}


class DutyCalcRequest(BaseModel):
    exportCountry: str
    importCountry: str
    category: str
    value: float
    currency: Optional[str] = "USD"


@router.post("/duty-calc")
async def duty_calc(payload: DutyCalcRequest):
    base = CATEGORY_RATES.get(payload.category, 0.075)
    pref = ROUTE_PREF.get((payload.exportCountry.upper(), payload.importCountry.upper()), 0.0)
    duty_pct = max(0.0, base + pref)
    vat_pct = VAT_BY_COUNTRY.get(payload.importCountry.upper(), 0.10)
    customs_handling = 0.005  # 0.5%

    duty = round(payload.value * duty_pct, 2)
    taxes = round((payload.value + duty) * vat_pct, 2)
    handling = round(payload.value * customs_handling, 2)
    landed = round(payload.value + duty + taxes + handling, 2)

    return {
        "exportCountry": payload.exportCountry.upper(),
        "importCountry": payload.importCountry.upper(),
        "category": payload.category,
        "currency": payload.currency,
        "shipmentValue": payload.value,
        "dutyRate": round(duty_pct * 100, 2),
        "vatRate": round(vat_pct * 100, 2),
        "estimatedDuty": duty,
        "estimatedTaxes": taxes,
        "estimatedHandling": handling,
        "estimatedLandedCost": landed,
        "ftaApplied": pref < 0,
        "note": "Indicative only. Real rates depend on HS code, certificates of origin and live tariff schedules.",
        "calculatedAt": datetime.now(timezone.utc).isoformat(),
    }


# ----- HSN Database (mock) -----
HSN_DB = {
    "10063020": {
        "code": "10063020", "title": "Basmati Rice (semi-milled / milled)",
        "gst": "0%", "rodtep": "Eligible · 4.3%", "drawback": "Up to 1.5%",
        "category": "Agriculture & Food",
        "exportBenefits": ["APEDA support", "RoDTEP scrip", "Interest equalisation 2%"],
        "customsNotes": "FOB Mundra preferred; APEDA Certificate of Authenticity mandatory.",
        "documents": ["Commercial Invoice", "Packing List", "Phytosanitary Certificate", "Certificate of Origin", "APEDA RCMC"],
        "relatedProducts": ["basmati-rice", "spices"],
        "opportunities": "GCC + Iran + USA · $5.4B total addressable market.",
    },
    "33074100": {
        "code": "33074100", "title": "Agarbatti & similar room fragrances",
        "gst": "5%", "rodtep": "Eligible · 2.8%", "drawback": "Up to 1.2%",
        "category": "FMCG",
        "exportBenefits": ["EPCH RCMC", "RoDTEP scrip", "MSME interest subvention 2%"],
        "customsNotes": "Often classified under Chapter 33 — ensure correct sub-heading on shipping bill.",
        "documents": ["Commercial Invoice", "Packing List", "EPCH Certificate", "Halal (for GCC)", "MSDS"],
        "relatedProducts": ["agarbatti", "handicrafts"],
        "opportunities": "UAE, USA, UK, Malaysia — $850M global market growing 9% YoY.",
    },
    "09024020": {
        "code": "09024020", "title": "Black Tea (in bulk, > 3kg)",
        "gst": "5%", "rodtep": "Eligible · 3.6%", "drawback": "Up to 1.0%",
        "category": "Agriculture & Food",
        "exportBenefits": ["Tea Board RCMC", "RoDTEP", "Interest equalisation 2%"],
        "customsNotes": "Tea Board export inspection certificate is mandatory.",
        "documents": ["Commercial Invoice", "Phytosanitary", "Tea Board EIC", "Certificate of Origin", "Health Certificate"],
        "relatedProducts": ["spices"],
        "opportunities": "Russia, UAE, UK, Iran — $1.2B Indian export market.",
    },
    "30049099": {
        "code": "30049099", "title": "Pharmaceuticals — other formulations",
        "gst": "12%", "rodtep": "Eligible · 1.7%", "drawback": "Up to 0.8%",
        "category": "Pharmaceuticals",
        "exportBenefits": ["Pharmexcil RCMC", "RoDTEP", "PLI scheme up to 10%"],
        "customsNotes": "CDSCO / Form-10 export NOC required for restricted molecules.",
        "documents": ["Commercial Invoice", "Drug Manufacturing License", "GMP Certificate", "Free Sale Certificate", "Pharmexcil RCMC"],
        "relatedProducts": ["pharmaceuticals"],
        "opportunities": "USA, UK, Africa — India is world's 3rd largest pharma exporter ($28B).",
    },
    "62034299": {
        "code": "62034299", "title": "Men's cotton trousers (woven)",
        "gst": "12%", "rodtep": "Eligible · 4.5%", "drawback": "Up to 2.4%",
        "category": "Textiles & Apparel",
        "exportBenefits": ["AEPC RCMC", "RoSCTL", "RoDTEP", "MSME"],
        "customsNotes": "Self-certify under FTA; verify yarn-forward rules for UK/EU.",
        "documents": ["Commercial Invoice", "Packing List", "AEPC RCMC", "Certificate of Origin (FTA)", "Inspection Certificate"],
        "relatedProducts": ["textiles"],
        "opportunities": "USA, UK, EU, GCC — $44B Indian apparel export pie.",
    },
}


@router.get("/hsn")
async def list_hsn():
    return [
        {"code": h["code"], "title": h["title"], "category": h["category"], "gst": h["gst"]}
        for h in HSN_DB.values()
    ]


@router.get("/hsn/{code}")
async def hsn_detail(code: str):
    h = HSN_DB.get(code)
    if not h:
        return JSONResponse(status_code=404, content={"error": "HSN not found"})
    return h


# ----- HSN finder (search by product) -----
class HsnFindRequest(BaseModel):
    productName: str
    description: Optional[str] = ""
    category: Optional[str] = ""


@router.post("/hsn-finder")
async def hsn_finder(payload: HsnFindRequest):
    q = (payload.productName + " " + (payload.description or "")).lower()
    matches = []
    # naive scoring
    for h in HSN_DB.values():
        score = 0
        if any(w in h["title"].lower() for w in q.split() if w):
            score += 5
        if payload.category and payload.category.lower() in h["category"].lower():
            score += 3
        if score:
            matches.append({**h, "matchScore": score})
    matches.sort(key=lambda m: -m["matchScore"])
    if not matches:
        # always return a sensible default
        sample = HSN_DB["10063020"].copy()
        sample["matchScore"] = 1
        matches = [sample]
    return {"query": payload.productName, "results": matches[:5]}


# ----- Landed cost -----
class LandedCostRequest(BaseModel):
    productCost: float
    freight: float = 0
    insurance: float = 0
    duty: float = 0
    localCharges: float = 0
    currency: Optional[str] = "USD"


@router.post("/landed-cost")
async def landed_cost(payload: LandedCostRequest):
    items = [
        ("Product cost", payload.productCost),
        ("Freight", payload.freight),
        ("Insurance", payload.insurance),
        ("Customs duty", payload.duty),
        ("Local charges (THC, CHA, drayage)", payload.localCharges),
    ]
    total = round(sum(v for _, v in items), 2)
    breakdown = [{"label": k, "amount": round(v, 2), "share": round((v / total * 100) if total else 0, 1)} for k, v in items]
    return {
        "currency": payload.currency,
        "total": total,
        "breakdown": breakdown,
    }


# ----- Export incentive finder -----
class IncentiveRequest(BaseModel):
    product: str
    destination: str


@router.post("/export-incentive")
async def export_incentive(payload: IncentiveRequest):
    return {
        "product": payload.product,
        "destination": payload.destination.upper(),
        "rodtep": {"eligible": True, "rate": "3.6%", "scrip": "Tradable on ICEGATE"},
        "dutyDrawback": {"eligible": True, "rate": "Up to 1.5%", "category": "All Industry Rate"},
        "incentives": [
            {"name": "Interest Equalisation Scheme", "benefit": "2% on pre/post shipment credit"},
            {"name": "EPCG Scheme", "benefit": "0% duty on capital goods · 6x export obligation"},
            {"name": "Advance Authorisation", "benefit": "Duty-free import of inputs"},
            {"name": "MSME Subvention", "benefit": "Additional 2% subvention for MSMEs"},
        ],
        "govBenefits": [
            {"name": "Market Access Initiative (MAI)", "detail": "Up to 50% travel + booth grant for trade fairs."},
            {"name": "TIES — Trade Infrastructure", "detail": "Last-mile export infrastructure grant."},
        ],
        "note": "Indicative — final eligibility confirmed via DGFT and Customs.",
    }


# ----- Product research -----
class ResearchRequest(BaseModel):
    product: str
    hsnCode: Optional[str] = None


@router.post("/product-research")
async def product_research(payload: ResearchRequest):
    return {
        "product": payload.product,
        "hsn": payload.hsnCode or "Auto-detected",
        "demandOverview": "Global demand for {p} grew at a 11% CAGR over the last 5 years. India holds ~14% global export share with strong upside in GCC and Africa.".format(p=payload.product),
        "topImporting": [
            {"country": "USA", "share": "18%"},
            {"country": "UAE", "share": "12%"},
            {"country": "Saudi Arabia", "share": "9%"},
            {"country": "UK", "share": "7%"},
            {"country": "Iran", "share": "6%"},
        ],
        "topExporting": [
            {"country": "India", "share": "26%"},
            {"country": "Thailand", "share": "12%"},
            {"country": "Vietnam", "share": "11%"},
            {"country": "Pakistan", "share": "9%"},
            {"country": "USA", "share": "8%"},
        ],
        "opportunity": "$1.4B unmet demand identified across UAE + Saudi + Iraq corridor.",
        "trends": [
            "Premium pricing for organic & GI-tagged origin variants (+22%).",
            "Private-label deals with Carrefour and Lulu dominating volume.",
            "Direct-to-consumer e-commerce growing 35% YoY.",
        ],
    }


# ----- Find buyers -----
class BuyersRequest(BaseModel):
    product: str
    country: Optional[str] = None


SAMPLE_BUYERS = [
    {"company": "Gulf Imports LLC", "country": "AE", "city": "Dubai", "demand": "MT/month", "volume": 240, "fit": "High"},
    {"company": "Riyadh Trading Co.", "country": "SA", "city": "Riyadh", "demand": "MT/month", "volume": 180, "fit": "High"},
    {"company": "British Foods PLC", "country": "GB", "city": "London", "demand": "MT/month", "volume": 95, "fit": "Medium"},
    {"company": "Sunrise Distributors", "country": "US", "city": "Houston", "demand": "MT/month", "volume": 320, "fit": "High"},
    {"company": "Singapore Trade Hub", "country": "SG", "city": "Singapore", "demand": "MT/month", "volume": 60, "fit": "Medium"},
    {"company": "Sydney Imports Pty", "country": "AU", "city": "Sydney", "demand": "MT/month", "volume": 45, "fit": "Medium"},
    {"company": "Tokyo Asia Sourcing", "country": "JP", "city": "Tokyo", "demand": "MT/month", "volume": 110, "fit": "High"},
    {"company": "Cairo Wholesale", "country": "EG", "city": "Cairo", "demand": "MT/month", "volume": 75, "fit": "Medium"},
]


@router.post("/find-buyers")
async def find_buyers(payload: BuyersRequest):
    buyers = SAMPLE_BUYERS
    if payload.country:
        c = payload.country.upper()
        filtered = [b for b in buyers if b["country"] == c]
        buyers = filtered or buyers
    return {
        "product": payload.product,
        "country": payload.country,
        "buyers": buyers[:6],
        "marketPotential": "$3.2B addressable demand across 8 markets.",
        "suggestedRegions": ["GCC", "North America", "Western Europe", "SE Asia"],
        "lockedExtras": True,  # signals UI to gate further details behind signup
    }


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
    return {"suppliers": res, "total": len(res), "lockedExtras": True}


# ----- Export readiness -----
class ReadinessRequest(BaseModel):
    iec: bool = False
    gst: bool = False
    website: bool = False
    packagingReady: bool = False
    certifications: bool = False
    experience: bool = False
    # lead capture
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

    # capture lead if email provided
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
        "recommendations": recs or ["You're export-ready. Connect with buyers on the LeadNation app."],
        "leadCaptured": bool(payload.email),
    }


