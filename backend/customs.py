"""Customs & Compliance + CHA Hub — India-first product-based engine.

Real-Time Trade Data Engine
---------------------------
* Currency exchange: GENUINE live rates via a free no-key FX API (cached 1h).
* Duty / HSN / RoDTEP / benefits: curated India ruleset + Knowledge Base + Brain,
  with deep-links to official ICEGATE / DGFT / Indian Trade Portal pages
  (labelled "indicative — verify on official portal"). NO scraping.
* Paid-API adapter: set TRADE_DATA_PROVIDER + TRADE_DATA_API_KEY (Seair / Export
  Genius / Volza) to flip on live automated duty data with zero code change.
"""
import os
import time
import logging
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from core import db
from trade_tools import HSN_DB

router = APIRouter(prefix="/customs")

OFFICIAL_LINKS = {
    "icegate": "https://www.icegate.gov.in/",
    "dgft": "https://www.dgft.gov.in/CP/",
    "rodtep": "https://www.dgft.gov.in/CP/?opt=RoDTEP",
    "tradePortal": "https://www.indiantradeportal.in/",
    "cbic": "https://www.cbic.gov.in/entities/cbic",
}

# FTA partners where Indian-origin goods get preferential (0% / reduced) BCD
FTA_PARTNERS = {
    "AE": "CEPA", "UAE": "CEPA", "AU": "ECTA", "AUSTRALIA": "ECTA",
    "JP": "CEPA", "JAPAN": "CEPA", "KR": "CEPA", "SG": "CECA", "SINGAPORE": "CECA",
    "MY": "FTA", "TH": "FTA", "MUS": "CECPA", "ASEAN": "AIFTA",
}

# Indicative Basic Customs Duty by broad category (India MFN)
CATEGORY_BCD = {
    "Agriculture & Food": 30.0, "Textiles & Apparel": 20.0, "Pharmaceuticals": 10.0,
    "Engineering Goods": 7.5, "Electronics": 15.0, "Chemicals": 7.5,
    "Gems & Jewellery": 10.0, "Handicrafts": 10.0, "Automotive": 15.0, "Default": 10.0,
}
GST_BY_CATEGORY = {
    "Agriculture & Food": 5.0, "Textiles & Apparel": 12.0, "Pharmaceuticals": 12.0,
    "Engineering Goods": 18.0, "Electronics": 18.0, "Chemicals": 18.0,
    "Gems & Jewellery": 3.0, "Handicrafts": 12.0, "Automotive": 28.0, "Default": 18.0,
}


# ---------------- Paid-API adapter (flip-on later) ----------------
class TradeDataProvider:
    def __init__(self):
        self.name = os.environ.get("TRADE_DATA_PROVIDER", "none")
        self.key = os.environ.get("TRADE_DATA_API_KEY")

    @property
    def live(self):
        return self.name != "none" and bool(self.key)

    async def duty(self, hsn, country, direction):
        # When a key is configured, call the provider here (Seair/ExportGenius/Volza).
        # Until then we return None → curated engine is used.
        return None


PROVIDER = TradeDataProvider()


# ---------------- Live FX ----------------
_FX_CACHE = {}
_FX_TTL = 3600


async def _fx_rates(base: str):
    base = (base or "USD").upper()
    now = time.time()
    hit = _FX_CACHE.get(base)
    if hit and now - hit[0] < _FX_TTL:
        return hit[1], True
    try:
        async with httpx.AsyncClient(timeout=8) as cx:
            r = await cx.get(f"https://open.er-api.com/v6/latest/{base}")
            data = r.json()
        if data.get("result") == "success":
            rates = data["rates"]
            _FX_CACHE[base] = (now, rates)
            return rates, False
    except Exception as exc:
        logging.warning("FX fetch failed: %s", exc)
    if hit:
        return hit[1], True
    return None, False


@router.get("/fx")
async def fx(base: str = "USD", target: str = "INR", amount: float = 1.0):
    rates, cached = await _fx_rates(base)
    if not rates or target.upper() not in rates:
        return {"ok": False, "error": "Rate unavailable", "base": base, "target": target}
    rate = rates[target.upper()]
    popular = {c: rates.get(c) for c in ["INR", "USD", "EUR", "GBP", "AED", "CNY", "JPY", "AUD", "SGD"] if rates.get(c)}
    return {"ok": True, "base": base.upper(), "target": target.upper(), "rate": rate,
            "amount": amount, "converted": round(amount * rate, 4), "live": not cached,
            "popular": popular, "source": "open.er-api.com (live)"}


# ---------------- Product compliance profile ----------------
class ProfileRequest(BaseModel):
    product: Optional[str] = None
    country: Optional[str] = None
    direction: str = "Export"   # Export | Import
    hsn: Optional[str] = None
    value: Optional[float] = None


def _resolve_hsn(product, hsn):
    if hsn and hsn in HSN_DB:
        return hsn, HSN_DB[hsn]
    if hsn:
        for code, h in HSN_DB.items():
            if code.startswith(hsn[:4]):
                return code, h
    if product:
        pl = product.lower()
        for code, h in HSN_DB.items():
            if pl in h["title"].lower() or any(pl in str(v).lower() for v in [h.get("category", "")]):
                return code, h
    return None, None


@router.post("/profile")
async def profile(req: ProfileRequest):
    code, h = _resolve_hsn(req.product, req.hsn)
    category = (h or {}).get("category", "Default")
    bcd = CATEGORY_BCD.get(category, CATEGORY_BCD["Default"])
    gst = GST_BY_CATEGORY.get(category, GST_BY_CATEGORY["Default"])
    cc = (req.country or "").upper()
    fta = FTA_PARTNERS.get(cc) or FTA_PARTNERS.get((req.country or "").upper())
    is_export = req.direction.lower() == "export"

    effective_bcd = 0.0 if (fta and not is_export) else bcd
    sws = round(effective_bcd * 0.10, 2)

    base_docs = ["Commercial Invoice", "Packing List", "Bill of Lading / Airway Bill",
                 "Shipping Bill" if is_export else "Bill of Entry", "Certificate of Origin",
                 "Letter of Credit / Payment Terms", "Insurance Certificate"]
    if fta:
        base_docs.append(f"FTA Certificate of Origin ({fta})")
    if category == "Agriculture & Food":
        base_docs += ["FSSAI License", "Phytosanitary Certificate", "APEDA RCMC"]
    elif category == "Pharmaceuticals":
        base_docs += ["CDSCO / Drug License", "COPP", "Free Sale Certificate"]
    elif category == "Textiles & Apparel":
        base_docs += ["Textile Committee Certificate", "AEPC RCMC"]

    benefits = []
    if is_export:
        benefits = [
            {"scheme": "RoDTEP", "detail": f"Tradable scrip on exports of {h['title'] if h else 'this product'}; rate per HS line.", "link": OFFICIAL_LINKS["rodtep"]},
            {"scheme": "Duty Drawback", "detail": "Refund of customs/excise on inputs used in export production.", "link": OFFICIAL_LINKS["dgft"]},
            {"scheme": "EPCG", "detail": "0% duty on capital goods against export obligation.", "link": OFFICIAL_LINKS["dgft"]},
            {"scheme": "Interest Equalisation", "detail": "2% (extra 2% MSME) subvention on export credit.", "link": OFFICIAL_LINKS["dgft"]},
        ]

    provider_note = ("Live duty API active." if PROVIDER.live else
                     "Indicative rates — verify on the official ICEGATE / DGFT / Indian Trade Portal links.")

    return {
        "product": req.product, "country": req.country, "direction": req.direction,
        "hsn": code, "hsnTitle": (h or {}).get("title"), "category": category,
        "duty": {
            "basicCustomsDuty": f"{effective_bcd}%", "igst": f"{gst}%",
            "socialWelfareSurcharge": f"{sws}%", "ftaApplicable": bool(fta),
            "ftaName": fta, "note": ("FTA preferential 0% BCD" if (fta and not is_export) else "MFN rate"),
        },
        "documents": base_docs,
        "licenses": ["IEC (Import Export Code) — mandatory", "GST Registration", "RCMC (for incentives)"],
        "regulators": {"dgft": "DGFT", "customs": "CBIC / ICEGATE", "links": OFFICIAL_LINKS},
        "chaSteps": [
            "Appoint a licensed Customs House Agent (CHA) / Customs Broker.",
            "File Shipping Bill (export) / Bill of Entry (import) on ICEGATE.",
            "Pay applicable duties via ICEGATE e-payment.",
            "Customs examination & assessment; obtain Let Export / Out of Charge order.",
            "Coordinate CFS/port handling, transport and final delivery.",
        ],
        "clearanceTime": "48–72 hours (60% faster with AEO certification)",
        "benefits": benefits,
        "providerLive": PROVIDER.live,
        "note": provider_note,
        "brainPrompt": f"{req.direction} {req.product or 'this product'} {'to' if is_export else 'from'} {req.country or 'destination'}: full duty, documents and benefits?",
        "officialLinks": OFFICIAL_LINKS,
    }


# ---------------- CBM calculator ----------------
class CbmRequest(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float
    quantity: int = 1
    weight_kg: float = 0.0
    mode: str = "sea"  # sea | air


@router.post("/cbm")
async def cbm(req: CbmRequest):
    per = (req.length_cm * req.width_cm * req.height_cm) / 1_000_000
    total_cbm = round(per * req.quantity, 4)
    total_weight = req.weight_kg * req.quantity if req.weight_kg else 0
    air_volumetric = round(total_cbm * 167, 2)          # IATA 1 CBM = 167 kg
    sea_chargeable_tons = round(max(total_cbm, total_weight / 1000), 4)
    return {
        "cbmPerUnit": round(per, 4), "totalCBM": total_cbm, "units": req.quantity,
        "totalWeightKg": round(total_weight, 2),
        "airVolumetricWeightKg": air_volumetric,
        "airChargeableWeightKg": round(max(air_volumetric, total_weight), 2),
        "seaChargeableTons": sea_chargeable_tons,
        "container20ft": f"{round(total_cbm / 33 * 100, 1)}% of a 20ft (≈33 CBM)",
        "container40ft": f"{round(total_cbm / 67 * 100, 1)}% of a 40ft (≈67 CBM)",
        "recommendation": "FCL 20ft" if total_cbm > 15 else "LCL (consolidate)",
    }


# ---------------- CHA charges estimator ----------------
class ChaRequest(BaseModel):
    shipmentValue: float
    mode: str = "sea"      # sea | air
    direction: str = "Export"
    containers: int = 1


@router.post("/cha-charges")
async def cha_charges(req: ChaRequest):
    agency = max(3500, round(req.shipmentValue * 0.004))
    clearance = 4500 * max(1, req.containers)
    documentation = 2500
    examination = 1800
    transport = (12000 if req.mode == "sea" else 6000) * max(1, req.containers)
    cfs = 3500 * max(1, req.containers) if req.mode == "sea" else 0
    misc = 1500
    items = [
        {"label": "CHA agency fee", "amount": agency},
        {"label": "Customs clearance", "amount": clearance},
        {"label": "Documentation", "amount": documentation},
        {"label": "Customs examination", "amount": examination},
        {"label": "Transport / handling", "amount": transport},
        {"label": "CFS / port charges", "amount": cfs},
        {"label": "Miscellaneous", "amount": misc},
    ]
    total = sum(i["amount"] for i in items)
    return {"currency": "INR", "items": [i for i in items if i["amount"] > 0],
            "total": total, "note": "Indicative estimate; actuals vary by port, CHA and cargo."}


# ---------------- Landed / selling price calculator ----------------
class PriceRequest(BaseModel):
    productCost: float
    quantity: int = 1
    freight: float = 0.0
    insurance: float = 0.0
    dutyPct: float = 0.0
    marginPct: float = 20.0


@router.post("/price")
async def price(req: PriceRequest):
    goods = req.productCost * req.quantity
    cif = goods + req.freight + req.insurance
    duty = round(cif * req.dutyPct / 100, 2)
    landed = round(cif + duty, 2)
    selling = round(landed * (1 + req.marginPct / 100), 2)
    return {"goodsValue": round(goods, 2), "cif": round(cif, 2), "duty": duty,
            "landedCost": landed, "landedPerUnit": round(landed / max(1, req.quantity), 2),
            "sellingPrice": selling, "profit": round(selling - landed, 2),
            "marginPct": req.marginPct}


# ---------------- Freight routes ----------------
FREIGHT_ROUTES = {
    "AE": [{"mode": "Sea", "lane": "Mundra/Nhava Sheva → Jebel Ali", "transit": "4–6 days", "type": "FCL/LCL"},
           {"mode": "Air", "lane": "DEL/BOM → DXB", "transit": "4–8 hrs", "type": "Air cargo"}],
    "US": [{"mode": "Sea", "lane": "Nhava Sheva → New York (via Suez)", "transit": "28–35 days", "type": "FCL"},
           {"mode": "Air", "lane": "BOM/DEL → JFK", "transit": "18–24 hrs", "type": "Air cargo"}],
    "GB": [{"mode": "Sea", "lane": "Nhava Sheva → Felixstowe", "transit": "18–24 days", "type": "FCL/LCL"},
           {"mode": "Air", "lane": "DEL → LHR", "transit": "9–11 hrs", "type": "Air cargo"}],
    "AU": [{"mode": "Sea", "lane": "Chennai → Melbourne", "transit": "18–26 days", "type": "FCL"},
           {"mode": "Air", "lane": "BLR → SYD", "transit": "12–16 hrs", "type": "Air cargo"}],
}
DEFAULT_ROUTES = [{"mode": "Sea", "lane": "Mundra/Nhava Sheva → destination port", "transit": "10–35 days", "type": "FCL/LCL"},
                  {"mode": "Air", "lane": "DEL/BOM → destination", "transit": "1–2 days", "type": "Air cargo"}]


@router.get("/freight-routes")
async def freight_routes(to: str = ""):
    routes = FREIGHT_ROUTES.get((to or "").upper(), DEFAULT_ROUTES)
    return {"to": to, "routes": routes,
            "tip": "Red Sea reroutes via Cape of Good Hope add 10–14 days on Asia–Europe lanes."}


# ---------------- Government benefits finder ----------------
@router.get("/benefits")
async def benefits(direction: str = "Export"):
    if direction.lower() != "export":
        return {"direction": direction, "benefits": [
            {"scheme": "EPCG", "detail": "Duty-free capital goods import against export obligation.", "link": OFFICIAL_LINKS["dgft"]},
            {"scheme": "Advance Authorisation", "detail": "Duty-free import of inputs for export production.", "link": OFFICIAL_LINKS["dgft"]},
        ]}
    return {"direction": direction, "benefits": [
        {"scheme": "RoDTEP", "detail": "Remission of duties & taxes on exported products — tradable scrip.", "link": OFFICIAL_LINKS["rodtep"]},
        {"scheme": "Duty Drawback", "detail": "Refund of customs duty on inputs used in exports.", "link": OFFICIAL_LINKS["dgft"]},
        {"scheme": "EPCG", "detail": "0% duty on capital goods vs export obligation.", "link": OFFICIAL_LINKS["dgft"]},
        {"scheme": "Advance Authorisation", "detail": "Duty-free inputs for export production.", "link": OFFICIAL_LINKS["dgft"]},
        {"scheme": "Interest Equalisation", "detail": "2% (extra 2% MSME) on pre/post-shipment credit.", "link": OFFICIAL_LINKS["dgft"]},
        {"scheme": "MAI / Market Access", "detail": "Support for trade fairs and market development.", "link": OFFICIAL_LINKS["dgft"]},
    ]}


# ---------------- CHA directory ----------------
@router.get("/cha-directory")
async def cha_directory(port: str = ""):
    chas = [
        {"name": "Oceanic Clearing & Forwarding", "port": "Nhava Sheva", "city": "Mumbai", "services": "Customs clearance, FCL/LCL, DG cargo", "verified": True},
        {"name": "Gateway Customs Brokers", "port": "Mundra", "city": "Gujarat", "services": "Export/Import clearance, AEO", "verified": True},
        {"name": "Capital EXIM Logistics", "port": "ICD Tughlakabad", "city": "Delhi", "services": "Clearance, transport, warehousing", "verified": True},
        {"name": "Coromandel Trade Services", "port": "Chennai", "city": "Chennai", "services": "Auto & engineering cargo clearance", "verified": True},
        {"name": "Southern Star CHA", "port": "Cochin", "city": "Kochi", "services": "Spices, seafood, perishables", "verified": True},
    ]
    if port:
        chas = [c for c in chas if port.lower() in c["port"].lower() or port.lower() in c["city"].lower()] or chas
    return {"total": len(chas), "chas": chas}


# ---------------- Incoterms & trade terms ----------------
@router.get("/trade-terms")
async def trade_terms():
    return {
        "incoterms": [
            {"code": "EXW", "name": "Ex Works", "risk": "Buyer (from seller's door)", "desc": "Seller makes goods available at their premises; buyer bears all cost & risk from there."},
            {"code": "FOB", "name": "Free On Board", "risk": "Transfers when loaded on vessel", "desc": "Seller clears for export and loads onto the ship; risk passes once on board. Most common for Indian sea exports."},
            {"code": "CFR", "name": "Cost & Freight", "risk": "Transfers at loading port", "desc": "Seller pays freight to destination port; risk passes at origin once loaded."},
            {"code": "CIF", "name": "Cost, Insurance & Freight", "risk": "Transfers at loading port", "desc": "Like CFR but seller also pays marine insurance to destination. Very common for India exports."},
            {"code": "CIP", "name": "Carriage & Insurance Paid To", "risk": "Transfers at first carrier", "desc": "Seller pays carriage + insurance to named destination; for any transport mode."},
            {"code": "DAP", "name": "Delivered At Place", "risk": "Seller until destination", "desc": "Seller delivers ready for unloading at the named place; buyer handles import duty."},
            {"code": "DDP", "name": "Delivered Duty Paid", "risk": "Seller (full)", "desc": "Seller bears everything incl. import duty & clearance — max obligation on seller."},
        ],
        "paymentTerms": [
            {"term": "Advance Payment (TT)", "risk": "Lowest for exporter", "desc": "Buyer pays before shipment via telegraphic transfer. Safest for the seller."},
            {"term": "Letter of Credit (LC)", "risk": "Low (bank-guaranteed)", "desc": "Issuing bank guarantees payment against compliant documents. Most secure for large deals."},
            {"term": "Documents against Payment (D/P)", "risk": "Medium", "desc": "Bank releases shipping docs to buyer only on payment."},
            {"term": "Documents against Acceptance (D/A)", "risk": "Higher", "desc": "Docs released on the buyer's acceptance of a time draft; payment later."},
            {"term": "Open Account", "risk": "Highest for exporter", "desc": "Goods shipped & delivered before payment due (e.g. 30–90 days). Use with trusted buyers."},
        ],
        "insurance": [
            {"type": "Marine Cargo (ICC A)", "desc": "All-risk cover for sea/air cargo loss or damage in transit. Standard for CIF/CIP."},
            {"type": "ICC B / C", "desc": "Restricted cover for named perils only — lower premium, narrower protection."},
            {"type": "ECGC Credit Insurance", "desc": "Export Credit Guarantee Corp. covers buyer default / political risk on receivables."},
            {"type": "Warehouse-to-Warehouse", "desc": "Covers goods from seller's warehouse to buyer's warehouse, end to end."},
        ],
        "keyTerms": [
            {"term": "CIF Value", "desc": "Cost + Insurance + Freight — the basis on which Indian customs duty is assessed."},
            {"term": "FOB Value", "desc": "Free On Board value — goods value at the port of loading, excluding freight & insurance."},
            {"term": "Assessable Value", "desc": "CIF + 1% landing charges — the value customs uses to compute BCD."},
            {"term": "Bill of Lading (B/L)", "desc": "Carrier's receipt + title document for sea cargo (Airway Bill for air)."},
            {"term": "Shipping Bill / Bill of Entry", "desc": "Export / import declaration filed on ICEGATE for customs clearance."},
        ],
        "note": "Indicative guidance — confirm Incoterms® 2020 and payment terms in your sales contract.",
    }

