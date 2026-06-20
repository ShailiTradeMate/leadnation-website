from fastapi import FastAPI, APIRouter, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="LeadNation - Global Trade Intelligence API")
api_router = APIRouter(prefix="/api")


# ---------- Mock data (placeholder engines) ----------
COUNTRIES = [
    {"code": "IN", "name": "India", "flag": "🇮🇳"},
    {"code": "US", "name": "United States", "flag": "🇺🇸"},
    {"code": "CN", "name": "China", "flag": "🇨🇳"},
    {"code": "AE", "name": "United Arab Emirates", "flag": "🇦🇪"},
    {"code": "DE", "name": "Germany", "flag": "🇩🇪"},
    {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧"},
    {"code": "JP", "name": "Japan", "flag": "🇯🇵"},
    {"code": "SG", "name": "Singapore", "flag": "🇸🇬"},
    {"code": "BR", "name": "Brazil", "flag": "🇧🇷"},
    {"code": "ZA", "name": "South Africa", "flag": "🇿🇦"},
    {"code": "AU", "name": "Australia", "flag": "🇦🇺"},
    {"code": "FR", "name": "France", "flag": "🇫🇷"},
    {"code": "NL", "name": "Netherlands", "flag": "🇳🇱"},
    {"code": "SA", "name": "Saudi Arabia", "flag": "🇸🇦"},
    {"code": "KR", "name": "South Korea", "flag": "🇰🇷"},
    {"code": "VN", "name": "Vietnam", "flag": "🇻🇳"},
]

BUSINESS_TYPES = ["Manufacturer", "Wholesaler", "Distributor", "Retailer", "Trading House", "Logistics"]
TRADE_DIRECTIONS = ["Import", "Export", "Supplier"]

PRODUCTS = [
    "Basmati Rice", "Spices & Masala", "Cotton Textiles", "Pharmaceuticals",
    "Cut & Polished Diamonds", "Leather Goods", "Tea", "Coffee Beans",
    "Engineering Goods", "Marine Products", "Handicrafts", "Organic Foods",
    "Electronics", "Steel Products", "Solar Panels", "Auto Components"
]


# ---------- Models ----------
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    country: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website"


class SearchQuery(BaseModel):
    query: str


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "LeadNation API · Global Trade Intelligence", "version": "1.0.0"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(payload: StatusCheckCreate):
    status_obj = StatusCheck(**payload.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ----- Reference data -----
@api_router.get("/countries")
async def list_countries():
    return COUNTRIES


@api_router.get("/business-types")
async def list_business_types():
    return BUSINESS_TYPES


@api_router.get("/trade-directions")
async def list_trade_directions():
    return TRADE_DIRECTIONS


@api_router.get("/products")
async def list_products():
    return PRODUCTS


# ----- Customs & Compliance Engine (placeholder) -----
@api_router.get("/customs-compliance")
async def customs_compliance(country: str = Query(...), direction: str = Query("Import")):
    sample = {
        "country": country,
        "direction": direction,
        "hsCodeExample": "1006.30 — Semi-milled or wholly milled rice",
        "dutyRate": "0% (under FTA)" if country.upper() in {"AE", "SG", "JP"} else "8.5% MFN",
        "regulator": "DGFT (India) · Customs Authority of " + country.upper(),
        "documents": [
            "Commercial Invoice", "Packing List", "Bill of Lading / AWB",
            "Certificate of Origin", "FSSAI / Quality Certificate", "Letter of Credit"
        ],
        "incoterms": ["FOB", "CIF", "DDP"],
        "restrictions": "Standard biosecurity, quality and labeling regulations apply.",
        "averageClearanceTime": "48–72 hours",
        "tip": "Pre-clearance and AEO-certified shipments reduce clearance time by up to 60%.",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return sample


# ----- Trade News Engine (placeholder) -----
@api_router.get("/trade-news")
async def trade_news():
    items = [
        {
            "id": "n1",
            "title": "India's merchandise exports cross record $450B milestone",
            "category": "India · Exports",
            "excerpt": "Engineering goods, electronics and pharmaceuticals drive an all-time high in outbound trade.",
            "image": "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1200&q=80",
            "date": "2 hours ago",
            "source": "LeadNation Intelligence"
        },
        {
            "id": "n2",
            "title": "UAE–India CEPA pushes bilateral trade past $100B",
            "category": "Bilateral",
            "excerpt": "Tariff cuts under the Comprehensive Economic Partnership Agreement open new lanes for SMEs.",
            "image": "https://images.unsplash.com/photo-1517292987719-0369a794ec0f?auto=format&fit=crop&w=1200&q=80",
            "date": "5 hours ago",
            "source": "Trade Wire"
        },
        {
            "id": "n3",
            "title": "Red Sea reroutes lift container rates 38% on Asia-Europe lanes",
            "category": "Logistics",
            "excerpt": "Carriers reroute via Cape of Good Hope; transit times extend by 10–14 days.",
            "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80",
            "date": "9 hours ago",
            "source": "Global Freight"
        },
        {
            "id": "n4",
            "title": "EU CBAM enters reporting phase — exporters must track embedded carbon",
            "category": "Compliance",
            "excerpt": "Steel, cement, aluminum and fertilizer exporters to the EU now face quarterly reporting.",
            "image": "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?auto=format&fit=crop&w=1200&q=80",
            "date": "1 day ago",
            "source": "Regulatory Watch"
        },
        {
            "id": "n5",
            "title": "MSME exporters get 2% interest subvention extension till 2026",
            "category": "India · MSME",
            "excerpt": "RBI and Ministry of Commerce confirm continued support for small exporters.",
            "image": "https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=1200&q=80",
            "date": "1 day ago",
            "source": "MoCI"
        },
        {
            "id": "n6",
            "title": "Singapore launches blockchain-based trade finance corridor with India",
            "category": "FinTech",
            "excerpt": "Cross-border letters of credit settle in under 2 hours through new MAS pilot.",
            "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
            "date": "2 days ago",
            "source": "MAS"
        },
    ]
    return items


# ----- Expo Engine (placeholder) -----
@api_router.get("/expos")
async def expos():
    items = [
        {
            "id": "e1",
            "name": "India International Trade Fair (IITF)",
            "city": "New Delhi",
            "country": "India",
            "date": "14–27 Nov 2026",
            "category": "Multi-sector",
            "image": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80",
            "attendees": "1.5M+"
        },
        {
            "id": "e2",
            "name": "Gulfood Dubai",
            "city": "Dubai",
            "country": "UAE",
            "date": "16–20 Feb 2026",
            "category": "Food & Beverage",
            "image": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80",
            "attendees": "120K+"
        },
        {
            "id": "e3",
            "name": "Canton Fair (China Import & Export Fair)",
            "city": "Guangzhou",
            "country": "China",
            "date": "15 Apr–5 May 2026",
            "category": "Multi-sector",
            "image": "https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&w=1200&q=80",
            "attendees": "200K+"
        },
        {
            "id": "e4",
            "name": "Hannover Messe",
            "city": "Hannover",
            "country": "Germany",
            "date": "20–24 Apr 2026",
            "category": "Industrial Tech",
            "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80",
            "attendees": "215K+"
        },
        {
            "id": "e5",
            "name": "CES Las Vegas",
            "city": "Las Vegas",
            "country": "USA",
            "date": "6–9 Jan 2026",
            "category": "Consumer Electronics",
            "image": "https://images.unsplash.com/photo-1496171367470-9ed9a91ea931?auto=format&fit=crop&w=1200&q=80",
            "attendees": "135K+"
        },
        {
            "id": "e6",
            "name": "Vibrant Gujarat Global Summit",
            "city": "Gandhinagar",
            "country": "India",
            "date": "10–12 Jan 2026",
            "category": "Investment",
            "image": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1200&q=80",
            "attendees": "40K+"
        },
        {
            "id": "e7",
            "name": "Singapore FinTech Festival",
            "city": "Singapore",
            "country": "Singapore",
            "date": "11–13 Nov 2026",
            "category": "Finance",
            "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
            "attendees": "60K+"
        },
        {
            "id": "e8",
            "name": "Pharma Expo India",
            "city": "Mumbai",
            "country": "India",
            "date": "5–7 Mar 2026",
            "category": "Pharma & Health",
            "image": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1200&q=80",
            "attendees": "30K+"
        },
    ]
    return items


# ----- Product Info Engine (placeholder) -----
@api_router.post("/product-info")
async def product_info(payload: dict):
    country = payload.get("country", "India")
    business_type = payload.get("businessType", "Manufacturer")
    direction = payload.get("direction", "Export")
    product = payload.get("product", "Basmati Rice")

    return {
        "product": product,
        "country": country,
        "businessType": business_type,
        "direction": direction,
        "hsCode": "1006.30",
        "marketSize": "$5.4B",
        "yoyGrowth": "+12.8%",
        "topMarkets": ["Saudi Arabia", "Iran", "UAE", "USA", "UK"],
        "topSuppliers": ["KRBL Ltd", "LT Foods", "Kohinoor Foods", "Amira Nature Foods"],
        "averagePrice": "$1,180 / MT (FOB)",
        "minOrderQty": "26 MT (1 FCL)",
        "leadTime": "21–35 days",
        "certifications": ["APEDA", "ISO 22000", "HACCP", "Halal", "Organic NPOP"],
        "incoterms": ["FOB Mundra", "CIF Jebel Ali", "DDP Riyadh"],
        "tariff": "0–8% depending on destination",
        "insights": [
            f"{product} from {country} commands a premium of 14% over alternative origins.",
            "Demand from GCC markets is accelerating at double-digit growth.",
            "MSME exporters can avail 2% interest subvention under RoSCTL."
        ],
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


# ----- Search (placeholder) -----
@api_router.get("/search")
async def search(q: str = Query("", min_length=0)):
    qlow = q.lower().strip()
    results = []
    for p in PRODUCTS:
        if qlow in p.lower():
            results.append({"type": "product", "label": p})
    for c in COUNTRIES:
        if qlow in c["name"].lower() or qlow in c["code"].lower():
            results.append({"type": "country", "label": c["name"], "code": c["code"], "flag": c["flag"]})
    return {"query": q, "results": results[:12]}


# ----- Leads / Contact -----
@api_router.post("/leads")
async def create_lead(payload: LeadCreate):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    await db.leads.insert_one(doc)
    return {"ok": True, "id": doc["id"]}


# ----- India Features -----
@api_router.get("/india-features")
async def india_features():
    return [
        {
            "title": "DGFT Integration",
            "description": "Live IEC, RoSCTL, RoDTEP and FTA benefit calculator for every shipment.",
            "icon": "compass"
        },
        {
            "title": "GST & e-Invoicing",
            "description": "Auto-reconcile export invoices with GSTR-1, GSTR-3B and IRN.",
            "icon": "receipt"
        },
        {
            "title": "MSME Boost",
            "description": "2% interest subvention, MSME Samadhaan and CGTMSE in a click.",
            "icon": "sparkle"
        },
        {
            "title": "APEDA / FIEO / EPCs",
            "description": "Single dashboard for every export promotion council membership.",
            "icon": "buildings"
        },
        {
            "title": "ICEGATE & Shipping Bills",
            "description": "File and track shipping bills directly from your phone.",
            "icon": "package"
        },
        {
            "title": "Hindi · हिंदी Support",
            "description": "Full app and customs guidance available in Hindi and 8 regional languages.",
            "icon": "translate"
        }
    ]


# ---------- PHASE 2 ----------

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


@api_router.post("/duty-calc")
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


# Country Profiles
COUNTRY_PROFILES = {
    "india": {
        "slug": "india", "code": "IN", "flag": "🇮🇳", "name": "India",
        "tagline": "World's fastest-growing major economy · 5th largest by GDP",
        "currency": "INR", "language": "Hindi, English (+22 official)", "capital": "New Delhi",
        "gdp": "$3.9T", "tradeVolume": "$1.16T", "rank": "#15 exporter · #8 importer",
        "overview": "India is the world's fifth-largest economy and a top-tier exporter of engineering goods, pharmaceuticals, IT services, textiles and agri-products. With a young workforce and aggressive FTA expansion (UAE CEPA, Australia ECTA, EFTA TEPA), India is the destination of choice for the next decade of trade growth.",
        "majorExports": ["Refined Petroleum", "Diamonds & Jewellery", "Pharmaceuticals", "Engineering Goods", "Textiles & Apparel", "Rice & Spices", "Auto Components"],
        "majorImports": ["Crude Oil", "Gold", "Electronics", "Industrial Machinery", "Plastics", "Coal", "Fertilizers"],
        "opportunities": [
            "Electronics PLI scheme — $25B incentive pool for global OEMs.",
            "Green Hydrogen mission — $2B subsidy for exporters.",
            "Defense Corridor (UP/TN) — 100% FDI under automatic route.",
            "Semiconductor fabs — $10B incentives across Gujarat & Karnataka."
        ],
        "customs": {"avgDuty": "8.5%", "regulator": "CBIC · DGFT", "icegate": "icegate.gov.in"},
        "compliance": ["GST e-invoicing mandatory above ₹5cr turnover", "IEC code required for every exporter", "Mandatory BIS certification for 350+ products", "Quality control orders on imports"],
        "newsKeywords": ["India exports", "DGFT", "RoDTEP", "MSME"],
        "expoSlugs": ["e1", "e6", "e8"],
        "marketplace": ["GeM (Govt e-Marketplace)", "IndiaMART", "Udaan", "ONDC Network"],
    },
    "uae": {
        "slug": "uae", "code": "AE", "flag": "🇦🇪", "name": "United Arab Emirates",
        "tagline": "Re-export capital of the Middle East · 7 free zones",
        "currency": "AED", "language": "Arabic, English", "capital": "Abu Dhabi",
        "gdp": "$509B", "tradeVolume": "$725B", "rank": "#16 exporter · #15 importer",
        "overview": "The UAE is the trading bridge between Asia, Africa and Europe. Jebel Ali — the world's 9th busiest port — anchors $725B in annual trade. With 50+ free zones, 0% corporate tax in most zones, and CEPA agreements with India, Israel, Indonesia and Turkey, it's the most efficient launchpad for re-exports.",
        "majorExports": ["Refined Petroleum", "Crude Oil", "Gold", "Aluminium", "Polymers", "Re-exported Electronics"],
        "majorImports": ["Gold", "Diamonds", "Cars", "Broadcasting Equipment", "Jewellery"],
        "opportunities": [
            "100% foreign ownership in 50+ free zones.",
            "9% corporate tax (lowest in OECD).",
            "$8.5B India–UAE CEPA bilateral target.",
            "Dubai Industrial Strategy 2030 — $30B push."
        ],
        "customs": {"avgDuty": "5% GCC unified tariff", "regulator": "Federal Customs Authority", "icegate": "fca.gov.ae"},
        "compliance": ["Halal certification for food", "Emirates Quality Mark", "VAT 5% from 2018", "Restricted goods list strictly enforced"],
        "newsKeywords": ["UAE trade", "CEPA", "Jebel Ali", "DMCC"],
        "expoSlugs": ["e2"],
        "marketplace": ["DMCC Tradeflow", "Dubai Chamber", "Etihad Cargo Lanes"],
    },
    "usa": {
        "slug": "usa", "code": "US", "flag": "🇺🇸", "name": "United States",
        "tagline": "World's largest consumer market · $5.1T import volume",
        "currency": "USD", "language": "English", "capital": "Washington D.C.",
        "gdp": "$27.4T", "tradeVolume": "$5.1T", "rank": "#2 exporter · #1 importer",
        "overview": "The United States remains the world's largest consumer market and the deepest trading partner for most exporting nations. With the CHIPS Act, IRA, and re-shoring incentives, the US is rebuilding its supply chains — a $2T opportunity for compliant suppliers worldwide.",
        "majorExports": ["Refined Petroleum", "Aircraft", "Cars", "Pharmaceuticals", "Soybeans", "Integrated Circuits"],
        "majorImports": ["Cars", "Crude Oil", "Computers", "Pharmaceuticals", "Cell Phones"],
        "opportunities": [
            "Inflation Reduction Act — $400B green incentives.",
            "CHIPS Act — $52B semiconductor manufacturing.",
            "Generalized System of Preferences (GSP) for developing exporters.",
            "USMCA & friend-shoring lanes from India & Vietnam."
        ],
        "customs": {"avgDuty": "3.4% MFN avg", "regulator": "CBP · USTR", "icegate": "cbp.gov"},
        "compliance": ["FDA approval for food, pharma, cosmetics", "FCC for electronics", "EPA for chemicals", "Customs bond for shipments >$2,500"],
        "newsKeywords": ["US trade", "USTR", "CBP", "CHIPS Act"],
        "expoSlugs": ["e5"],
        "marketplace": ["Amazon Business", "Alibaba.com US", "ThomasNet", "Faire"],
    },
    "australia": {
        "slug": "australia", "code": "AU", "flag": "🇦🇺", "name": "Australia",
        "tagline": "Resource superpower · ECTA & CPTPP gateway",
        "currency": "AUD", "language": "English", "capital": "Canberra",
        "gdp": "$1.69T", "tradeVolume": "$702B", "rank": "#21 exporter · #22 importer",
        "overview": "Australia is a top supplier of iron ore, coal, LNG, gold and education services. The India–Australia ECTA has slashed duties to zero on 96% of Indian exports. With CPTPP, RCEP and bilateral FTAs with the UK, Japan and Korea, Australia is wired into every major trade lane.",
        "majorExports": ["Iron Ore", "Coal", "Natural Gas", "Gold", "Beef", "Wheat", "Wine"],
        "majorImports": ["Cars", "Refined Petroleum", "Computers", "Cell Phones", "Machinery"],
        "opportunities": [
            "0% duty on 96% of Indian exports under ECTA.",
            "Critical Minerals partnership — $2B fund.",
            "Education sector — 700K+ international students.",
            "Renewable Hydrogen export hub."
        ],
        "customs": {"avgDuty": "3%", "regulator": "Australian Border Force", "icegate": "abf.gov.au"},
        "compliance": ["Strict biosecurity (DAFF)", "Australian Standards for electrical", "TGA for therapeutics", "ACL for consumer goods"],
        "newsKeywords": ["Australia trade", "ECTA", "ABF", "biosecurity"],
        "expoSlugs": [],
        "marketplace": ["eBay Australia", "Catch.com.au", "Amazon AU"],
    },
    "armenia": {
        "slug": "armenia", "code": "AM", "flag": "🇦🇲", "name": "Armenia",
        "tagline": "Caucasus trade bridge · EAEU member · GSP+ with EU",
        "currency": "AMD", "language": "Armenian, Russian, English", "capital": "Yerevan",
        "gdp": "$24.1B", "tradeVolume": "$15B", "rank": "Emerging · high growth",
        "overview": "Armenia sits at the crossroads of Europe, Asia and the Middle East. As a member of the Eurasian Economic Union (EAEU) and a GSP+ beneficiary with the EU, it offers low-duty access to a 200M+ consumer market. Booming sectors include IT, diamonds, brandy, and copper/molybdenum.",
        "majorExports": ["Copper Ore", "Cut Diamonds", "Brandy & Spirits", "Gold", "IT Services"],
        "majorImports": ["Refined Petroleum", "Diamonds (rough)", "Cars", "Pharmaceuticals", "Wheat"],
        "opportunities": [
            "EAEU free trade — 0% duty to Russia, Belarus, Kazakhstan, Kyrgyzstan.",
            "EU GSP+ status — duty-free access to 27 EU countries.",
            "Booming IT sector — 25% YoY growth.",
            "Yerevan FEZ — tax holidays for tech & jewellery."
        ],
        "customs": {"avgDuty": "5% EAEU CET", "regulator": "Armenian Customs Service", "icegate": "petekamutner.am"},
        "compliance": ["EAEU technical regulations", "Halal & Kosher certification possible", "VAT 20% domestically", "Re-export to EAEU permitted"],
        "newsKeywords": ["Armenia trade", "EAEU", "Yerevan", "Caucasus"],
        "expoSlugs": [],
        "marketplace": ["List.am", "EAEU Trade Portal", "ARMEX"],
    },
}


@api_router.get("/country-profiles")
async def list_country_profiles():
    return [
        {"slug": p["slug"], "code": p["code"], "name": p["name"], "flag": p["flag"], "tagline": p["tagline"]}
        for p in COUNTRY_PROFILES.values()
    ]


@api_router.get("/country/{slug}")
async def country_profile(slug: str):
    p = COUNTRY_PROFILES.get(slug.lower())
    if not p:
        return JSONResponse(status_code=404, content={"error": "Country profile not found"})
    return p


# Academy
ACADEMY = {
    "Beginner": [
        {"slug": "international-trade-basics", "title": "International Trade Basics", "duration": "12 min", "lessons": 6, "summary": "What trade really is, who plays the game, and why every business needs an export plan.", "image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=900&q=80"},
        {"slug": "import-process-101", "title": "Import Process 101", "duration": "18 min", "lessons": 8, "summary": "From inquiry to delivery — the 8-step import lifecycle every newcomer must master.", "image": "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=900&q=80"},
        {"slug": "export-process-101", "title": "Export Process 101", "duration": "20 min", "lessons": 9, "summary": "Build your first export shipment — IEC, payment terms, packing, shipping.", "image": "https://images.unsplash.com/photo-1605902711622-cfb43c4437b5?auto=format&fit=crop&w=900&q=80"},
    ],
    "Intermediate": [
        {"slug": "trade-documentation", "title": "Trade Documentation Deep-Dive", "duration": "35 min", "lessons": 12, "summary": "Master the 14 documents that move money and goods across borders.", "image": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=900&q=80"},
        {"slug": "customs-clearance-playbook", "title": "Customs Clearance Playbook", "duration": "28 min", "lessons": 10, "summary": "ICEGATE, AEO, classification disputes, valuation. The full picture.", "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=900&q=80"},
        {"slug": "incoterms-2020", "title": "Incoterms 2020 Mastery", "duration": "22 min", "lessons": 7, "summary": "FOB vs CIF vs DDP — choose the right term and protect your margins.", "image": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=900&q=80"},
    ],
    "Advanced": [
        {"slug": "fta-arbitrage", "title": "FTA Arbitrage & Origin Engineering", "duration": "42 min", "lessons": 14, "summary": "Use rules of origin to legally slash duties by 4–18% per shipment.", "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80"},
        {"slug": "supply-chain-finance", "title": "Supply Chain & Trade Finance", "duration": "38 min", "lessons": 11, "summary": "LCs, factoring, ECGC, supply-chain financing — fund every shipment without your own capital.", "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=900&q=80"},
        {"slug": "global-compliance", "title": "Global Compliance & ESG", "duration": "45 min", "lessons": 13, "summary": "CBAM, modern slavery, REACH, RoHS — pass every audit, win every tender.", "image": "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?auto=format&fit=crop&w=900&q=80"},
    ],
}


@api_router.get("/academy")
async def academy():
    return ACADEMY


# Trade Intelligence Hub
@api_router.get("/intelligence")
async def intelligence():
    # Mock realistic-looking data
    return {
        "commodities": [
            {"name": "Gold", "symbol": "XAU", "price": 2418.50, "unit": "USD / oz", "change": 0.86, "icon": "gold"},
            {"name": "Silver", "symbol": "XAG", "price": 31.22, "unit": "USD / oz", "change": 1.42, "icon": "silver"},
            {"name": "Brent Crude Oil", "symbol": "BRENT", "price": 84.15, "unit": "USD / bbl", "change": -0.34, "icon": "oil"},
            {"name": "WTI Crude Oil", "symbol": "WTI", "price": 80.42, "unit": "USD / bbl", "change": -0.28, "icon": "oil"},
            {"name": "Copper", "symbol": "HG", "price": 4.62, "unit": "USD / lb", "change": 0.91, "icon": "metal"},
            {"name": "Natural Gas", "symbol": "NG", "price": 3.18, "unit": "USD / MMBtu", "change": 2.10, "icon": "gas"},
        ],
        "currencies": [
            {"pair": "USD/INR", "rate": 83.42, "change": 0.08},
            {"pair": "USD/AED", "rate": 3.6725, "change": 0.00},
            {"pair": "EUR/USD", "rate": 1.0852, "change": -0.12},
            {"pair": "GBP/USD", "rate": 1.2735, "change": -0.05},
            {"pair": "USD/JPY", "rate": 157.18, "change": 0.22},
            {"pair": "USD/CNY", "rate": 7.2418, "change": 0.04},
            {"pair": "USD/AUD", "rate": 1.5031, "change": -0.07},
            {"pair": "USD/SGD", "rate": 1.3482, "change": -0.02},
        ],
        "trends": [
            {"title": "Asia-Europe ocean freight up 38% YoY", "detail": "Red Sea reroutes via Cape add 12–18 days transit.", "impact": "high"},
            {"title": "India electronics exports cross $30B", "detail": "Smartphone shipments lead growth — +42% YoY.", "impact": "high"},
            {"title": "GCC food imports projected $70B by 2030", "detail": "Demand outstrips local production by 6x.", "impact": "medium"},
            {"title": "EU CBAM live for 6 commodities", "detail": "Steel, aluminum, cement now require embedded-carbon reports.", "impact": "high"},
            {"title": "Solar panel oversupply pulls prices -42%", "detail": "Chinese export surge reshapes global solar economics.", "impact": "medium"},
            {"title": "Indian rupee remains world's most stable EM currency", "detail": "RBI's reserves cross $670B all-time high.", "impact": "low"},
        ],
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# PHASE 3 & 4 — TOOLS, PRODUCTS, CORRIDORS, HSN, INDUSTRIES,
# BLOG, BUYERS, SUPPLIERS, MARKETPLACE, NETWORK, AI ASSISTANT
# ============================================================

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


@api_router.get("/hsn")
async def list_hsn():
    return [
        {"code": h["code"], "title": h["title"], "category": h["category"], "gst": h["gst"]}
        for h in HSN_DB.values()
    ]


@api_router.get("/hsn/{code}")
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


@api_router.post("/hsn-finder")
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


@api_router.post("/landed-cost")
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


@api_router.post("/export-incentive")
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


@api_router.post("/product-research")
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


@api_router.post("/find-buyers")
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


@api_router.get("/suppliers")
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


@api_router.post("/export-readiness")
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


# ----- AI Assistant (mock) -----
class AiAskRequest(BaseModel):
    question: str


AI_RESPONSES = {
    "export": "Yes — most products can be exported with an IEC code, GST registration and applicable RCMC. The most efficient routes from India are via Mundra (West) and Chennai (South).",
    "document": "Standard export documents: Commercial Invoice, Packing List, Bill of Lading / AWB, Certificate of Origin, FTA Certificate (if applicable), Phytosanitary / Health Certificate, Letter of Credit and Insurance.",
    "country": "Best initial targets for Indian exporters: UAE (zero-duty CEPA), Saudi Arabia, USA (high volumes), Singapore (re-export gateway), UK (post-FTA), Australia (ECTA zero-duty on 96% goods).",
    "certification": "It depends on your product category — Food (FSSAI, APEDA, HACCP), Pharma (CDSCO, GMP), Textiles (Oeko-Tex), Engineering (CE / BIS), Cosmetics (GMP, ISO 22716).",
    "hsn": "Open our HSN Finder tool, paste your product name and description — we'll return the most likely codes with GST and RoDTEP info instantly.",
}


@api_router.post("/ai-ask")
async def ai_ask(payload: AiAskRequest):
    q = payload.question.lower()
    answer = None
    for k, v in AI_RESPONSES.items():
        if k in q:
            answer = v
            break
    if not answer:
        answer = (
            "Great question — based on LeadNation's compliance and trade data, the safest path is to start with an IEC code, "
            "identify your HS code, check applicable FTA benefits and validate your buyer market with our Buyer Discovery tool. "
            "Try one of the suggested prompts on the left for a more specific answer."
        )
    return {
        "question": payload.question,
        "answer": answer,
        "suggestedTools": [
            {"label": "HSN Finder", "to": "/tools/hsn-finder"},
            {"label": "Duty Calculator", "to": "/tools/duty-calculator"},
            {"label": "Find Buyers", "to": "/tools/find-buyers"},
        ],
        "isMock": True,
    }


# ----- Products (rich) -----
PRODUCTS_DB = {
    "basmati-rice": {
        "slug": "basmati-rice", "name": "Basmati Rice", "hsn": "10063020", "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's #1 exporter of Basmati rice — controlling ~75% of global supply. The aromatic long-grain variety is GI-protected and commands a premium of 14% over regular long-grain.",
        "topExporters": ["India", "Pakistan"],
        "topImporters": ["Saudi Arabia", "Iran", "Iraq", "UAE", "USA"],
        "demand": "$5.4B annual global demand, growing 6% YoY.",
        "opportunities": ["GI-tagged origin variants", "Private-label for GCC retail", "Premium organic in EU / USA"],
        "compliance": ["APEDA RCMC", "Phytosanitary", "ISO 22000", "Halal"],
        "certifications": ["APEDA", "Organic NPOP", "Halal", "Kosher"],
        "logistics": "Mundra port preferred. 21-day transit to GCC; 35-day to USA East coast.",
        "category": "Agriculture & Food",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "agarbatti": {
        "slug": "agarbatti", "name": "Agarbatti (Incense Sticks)", "hsn": "33074100", "image": "https://images.unsplash.com/photo-1602874801007-bd45867d505b?auto=format&fit=crop&w=1200&q=80",
        "overview": "Indian agarbatti dominates 90% of global market share. Cities like Bengaluru, Ahmedabad and Mysore are global production hubs.",
        "topExporters": ["India", "Vietnam", "China"],
        "topImporters": ["USA", "UAE", "Malaysia", "UK", "Nigeria"],
        "demand": "$850M global, growing 9% YoY.",
        "opportunities": ["Premium fragrance variants for Western markets", "Halal-certified for GCC", "Private-label drop-shipping"],
        "compliance": ["EPCH RCMC", "MSDS for ingredients", "Halal certificate"],
        "certifications": ["EPCH", "Halal", "FSC paper rolls"],
        "logistics": "Air freight common for smaller orders; FCL for large retailers.",
        "category": "FMCG",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "spices": {
        "slug": "spices", "name": "Indian Spices", "hsn": "09042190", "image": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the largest producer, consumer and exporter of spices. Turmeric, cumin, coriander, cardamom and chilli dominate the basket.",
        "topExporters": ["India", "China", "Vietnam"],
        "topImporters": ["USA", "China", "UAE", "Thailand", "UK"],
        "demand": "$4.1B Indian export turnover.",
        "opportunities": ["Organic + ESG-certified spices", "Private-label blends", "Single-origin GI variants"],
        "compliance": ["Spices Board mandatory registration", "FSSAI", "EU pesticide MRL compliance"],
        "certifications": ["Spices Board", "Organic NPOP", "USDA Organic", "Fairtrade"],
        "logistics": "Cochin, Tuticorin and Mundra dominate spice exports.",
        "category": "Agriculture & Food",
        "relatedCorridors": ["india-to-uae", "india-to-usa"],
    },
    "textiles": {
        "slug": "textiles", "name": "Cotton Textiles & Apparel", "hsn": "62034299", "image": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's 2nd largest textile producer with a $44B export economy. Tirupur, Surat and Ludhiana power the value chain.",
        "topExporters": ["China", "India", "Bangladesh", "Vietnam"],
        "topImporters": ["USA", "EU", "UAE", "UK", "Japan"],
        "demand": "$44B Indian export; global apparel market $1.7T.",
        "opportunities": ["Sustainable cotton + GOTS premium", "Private-label for fast fashion", "Athleisure + recycled fibre"],
        "compliance": ["AEPC RCMC", "RoSCTL", "Oeko-Tex", "GOTS for organic"],
        "certifications": ["AEPC", "Oeko-Tex", "GOTS", "BCI"],
        "logistics": "Chennai and Mundra are primary apparel ports.",
        "category": "Textiles & Apparel",
        "relatedCorridors": ["india-to-usa", "india-to-uae"],
    },
    "pharmaceuticals": {
        "slug": "pharmaceuticals", "name": "Pharmaceuticals", "hsn": "30049099", "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=1200&q=80",
        "overview": "India is the world's 3rd largest pharma exporter ($28B). 60% of global vaccines and 40% of US generics come from Indian factories.",
        "topExporters": ["USA", "Germany", "Switzerland", "India"],
        "topImporters": ["USA", "EU", "Africa", "ASEAN"],
        "demand": "$28B Indian pharma exports; $1.5T global market.",
        "opportunities": ["Biosimilars to USA + EU", "CDMO contracts", "Generic export to Africa"],
        "compliance": ["CDSCO", "USFDA approval for USA", "EMA for EU", "WHO GMP"],
        "certifications": ["WHO GMP", "USFDA", "EU GMP", "Pharmexcil"],
        "logistics": "Cold chain critical — Hyderabad and Mumbai are pharma hubs.",
        "category": "Pharmaceuticals",
        "relatedCorridors": ["india-to-usa"],
    },
}


@api_router.get("/products-catalog")
async def products_catalog():
    return [{"slug": p["slug"], "name": p["name"], "hsn": p["hsn"], "image": p["image"], "category": p["category"]} for p in PRODUCTS_DB.values()]


@api_router.get("/product/{slug}")
async def product_detail(slug: str):
    p = PRODUCTS_DB.get(slug.lower())
    if not p:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    return p


# ----- Trade Corridors -----
CORRIDOR_DB = {
    "india-to-uae": {
        "slug": "india-to-uae", "from": "India", "fromCode": "IN", "to": "UAE", "toCode": "AE",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇪",
        "tagline": "India ↔ UAE · $85B+ bilateral trade · CEPA preferential",
        "exportProcess": "IEC → buyer KYC → invoice → packing → shipping bill via ICEGATE → customs clearance → FCL/LCL booking.",
        "importProcess": "UAE buyer obtains import code → opens LC → Indian customs export → sea/air freight to Jebel Ali → DP World clearance.",
        "customsInfo": "0% duty on 90% of HS lines under India–UAE CEPA. AEO-certified shippers clear in 4–6 hours.",
        "documents": ["Invoice", "Packing List", "Bill of Lading", "Certificate of Origin (CEPA)", "Phytosanitary / Halal / FSSAI as applicable"],
        "dutiesTaxes": "Duty: 0–5% (most goods free under CEPA) · UAE VAT 5%.",
        "opportunities": ["Food & Agri", "Pharma", "Textiles", "Jewellery", "IT services"],
        "popularProducts": ["basmati-rice", "spices", "agarbatti", "textiles"],
        "logistics": "Mundra → Jebel Ali in 4 days (sea) · DEL → DXB 3.5 hrs (air).",
        "image": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-usa": {
        "slug": "india-to-usa", "from": "India", "fromCode": "IN", "to": "USA", "toCode": "US",
        "fromFlag": "🇮🇳", "toFlag": "🇺🇸",
        "tagline": "India ↔ USA · $190B+ bilateral · Largest export destination",
        "exportProcess": "IEC → US importer EIN → ISF 10+2 filing → ocean booking → customs entry → FDA / FCC as applicable.",
        "importProcess": "US buyer files entry via CBP → FDA / EPA / DOT inspection as required → DDP or DAP delivery.",
        "customsInfo": "MFN avg 3.4%. GSP benefits paused; check current tariff schedule. Section 301 surcharges may apply to China-origin re-exports.",
        "documents": ["Invoice", "Packing List", "BOL", "Certificate of Origin", "FDA Prior Notice (food/pharma)", "FCC declaration (electronics)"],
        "dutiesTaxes": "Duty 0–20% by HS · State sales tax 4–9% · No federal VAT.",
        "opportunities": ["Pharma", "Engineering goods", "Textiles", "Jewellery", "Software services"],
        "popularProducts": ["pharmaceuticals", "textiles", "spices", "basmati-rice"],
        "logistics": "Mundra → NY/NJ in 28 days · Chennai → LA via Panama 32 days · Air to JFK 18 hrs.",
        "image": "https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-australia": {
        "slug": "india-to-australia", "from": "India", "fromCode": "IN", "to": "Australia", "toCode": "AU",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇺",
        "tagline": "India ↔ Australia · ECTA delivers 0% duty on 96% of Indian exports",
        "exportProcess": "IEC → ECTA Certificate of Origin → shipping bill → ABF clearance → biosecurity (DAFF) inspection.",
        "importProcess": "Australian importer ABN → ABF import declaration → biosecurity → GST 10%.",
        "customsInfo": "0% duty under ECTA on 96% Indian goods. Strict biosecurity for any plant/animal-based products.",
        "documents": ["Invoice", "Packing List", "BOL", "ECTA Certificate of Origin", "Biosecurity Treatment Certificate"],
        "dutiesTaxes": "Duty 0% (ECTA) · GST 10% on import.",
        "opportunities": ["Textiles", "Engineering", "Food & Agri", "Pharma", "Education services"],
        "popularProducts": ["textiles", "spices", "basmati-rice", "pharmaceuticals"],
        "logistics": "Mundra → Sydney 23 days · Chennai → Melbourne 21 days.",
        "image": "https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?auto=format&fit=crop&w=1200&q=80",
    },
    "india-to-armenia": {
        "slug": "india-to-armenia", "from": "India", "fromCode": "IN", "to": "Armenia", "toCode": "AM",
        "fromFlag": "🇮🇳", "toFlag": "🇦🇲",
        "tagline": "India ↔ Armenia · Caucasus gateway · EAEU re-export potential",
        "exportProcess": "IEC → invoice → shipping bill → multimodal via Bandar Abbas or Black Sea ports → customs clearance in Yerevan.",
        "importProcess": "Armenian importer registers with Armenian Customs Service → EAEU tariff → onward re-export to Russia / Belarus / Kazakhstan.",
        "customsInfo": "EAEU Common External Tariff applies (avg 5%). Re-export to EAEU members is duty-free for Armenian-origin.",
        "documents": ["Invoice", "Packing List", "BOL", "Certificate of Origin", "Quality / Halal as required"],
        "dutiesTaxes": "Duty avg 5% EAEU CET · VAT 20%.",
        "opportunities": ["Pharma", "Textiles", "IT services", "Diamonds (Armenia is global polishing hub)"],
        "popularProducts": ["pharmaceuticals", "textiles", "spices"],
        "logistics": "Sea via Bandar Abbas + rail/road; INSTC corridor cuts time by 40%.",
        "image": "https://images.unsplash.com/photo-1564507004663-b6dfb3c824d5?auto=format&fit=crop&w=1200&q=80",
    },
}


@api_router.get("/corridors")
async def list_corridors():
    return [{"slug": c["slug"], "from": c["from"], "to": c["to"], "fromFlag": c["fromFlag"], "toFlag": c["toFlag"], "tagline": c["tagline"], "image": c["image"]} for c in CORRIDOR_DB.values()]


@api_router.get("/corridor/{slug}")
async def corridor_detail(slug: str):
    c = CORRIDOR_DB.get(slug.lower())
    if not c:
        return JSONResponse(status_code=404, content={"error": "Corridor not found"})
    return c


# ----- Industries -----
INDUSTRY_DB = {
    "agriculture": {"slug": "agriculture", "name": "Agriculture", "icon": "plant", "overview": "$4.1T global agri trade · India is #1 exporter of rice, spices, milk and pulses.", "exports": ["Rice", "Spices", "Tea", "Marine products"], "topMarkets": ["UAE", "USA", "Bangladesh", "Iran", "Saudi Arabia"], "compliance": ["APEDA", "FSSAI", "Spices Board"], "image": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1200&q=80"},
    "food-processing": {"slug": "food-processing", "name": "Food Processing", "icon": "cooking-pot", "overview": "India's processed food exports cross $50B with high-growth in GCC and Africa.", "exports": ["Snacks", "Ready meals", "Dairy", "Beverages"], "topMarkets": ["UAE", "USA", "Saudi Arabia", "UK", "Malaysia"], "compliance": ["FSSAI", "APEDA", "Halal", "Kosher"], "image": "https://images.unsplash.com/photo-1606787366850-de6330128bfc?auto=format&fit=crop&w=1200&q=80"},
    "textiles": {"slug": "textiles", "name": "Textiles & Apparel", "icon": "scissors", "overview": "$44B Indian textile + apparel exports across 100+ countries.", "exports": ["Cotton textiles", "Apparel", "Home furnishings", "Yarn"], "topMarkets": ["USA", "UAE", "UK", "EU", "Australia"], "compliance": ["AEPC", "Oeko-Tex", "GOTS"], "image": "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&w=1200&q=80"},
    "chemicals": {"slug": "chemicals", "name": "Chemicals", "icon": "flask", "overview": "India is the 6th largest chemical producer globally — $220B industry with $30B+ exports.", "exports": ["Dyes & pigments", "Agrochemicals", "Specialty chemicals", "Polymers"], "topMarkets": ["USA", "China", "Brazil", "UAE", "Germany"], "compliance": ["REACH (EU)", "TSCA (USA)", "GHS"], "image": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=1200&q=80"},
    "pharmaceuticals": {"slug": "pharmaceuticals", "name": "Pharmaceuticals", "icon": "pill", "overview": "World's 3rd largest pharma exporter — $28B annual · 60% of global vaccines.", "exports": ["Generics", "Vaccines", "APIs", "Biosimilars"], "topMarkets": ["USA", "EU", "Africa", "ASEAN", "LatAm"], "compliance": ["USFDA", "EMA", "WHO GMP", "CDSCO"], "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=1200&q=80"},
    "engineering": {"slug": "engineering", "name": "Engineering Goods", "icon": "gear", "overview": "India's largest export category — $112B in 2024, growing 14% YoY.", "exports": ["Auto components", "Industrial machinery", "Electrical equipment", "Iron & steel"], "topMarkets": ["USA", "UAE", "China", "Singapore", "Germany"], "compliance": ["BIS", "CE marking", "ISO 9001"], "image": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?auto=format&fit=crop&w=1200&q=80"},
    "handicrafts": {"slug": "handicrafts", "name": "Handicrafts", "icon": "paint-brush", "overview": "India's handicrafts exports cross $4B with high-value buyers in USA, UK, GCC and EU.", "exports": ["Wood crafts", "Brass items", "Embroidered textiles", "Pottery"], "topMarkets": ["USA", "UK", "UAE", "Germany", "France"], "compliance": ["EPCH RCMC", "CITES (for ivory/wood)"], "image": "https://images.unsplash.com/photo-1528465424850-54d22f092f9d?auto=format&fit=crop&w=1200&q=80"},
    "fmcg": {"slug": "fmcg", "name": "FMCG", "icon": "shopping-bag", "overview": "$110B Indian FMCG sector — agarbatti, packaged foods and personal care lead exports.", "exports": ["Agarbatti", "Packaged foods", "Personal care", "Household products"], "topMarkets": ["UAE", "USA", "Saudi Arabia", "UK", "Nepal"], "compliance": ["FSSAI", "BIS", "Halal", "Kosher"], "image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=1200&q=80"},
}


@api_router.get("/industries")
async def list_industries():
    return [{"slug": i["slug"], "name": i["name"], "icon": i["icon"], "overview": i["overview"], "image": i["image"]} for i in INDUSTRY_DB.values()]


@api_router.get("/industry/{slug}")
async def industry_detail(slug: str):
    i = INDUSTRY_DB.get(slug.lower())
    if not i:
        return JSONResponse(status_code=404, content={"error": "Industry not found"})
    return i


# ----- Blog -----
BLOG_DB = [
    {"slug": "complete-guide-to-iec-code-india", "title": "The complete guide to getting your IEC code in India (2026)", "category": "Export Guides", "date": "Jan 12, 2026", "image": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1200&q=80", "excerpt": "An IEC code is the foundation of every Indian exporter's journey. Here's the simplest, free, online process — start to finish.", "readMins": 7},
    {"slug": "rodtep-explained-2026", "title": "RoDTEP, RoSCTL & Duty Drawback explained for 2026", "category": "Compliance", "date": "Jan 10, 2026", "image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80", "excerpt": "Three powerful export incentives, three different rates. Here's exactly which one applies to you — and how to claim it.", "readMins": 9},
    {"slug": "incoterms-2020-cheatsheet", "title": "Incoterms 2020 cheatsheet for exporters", "category": "Trade Intelligence", "date": "Jan 8, 2026", "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80", "excerpt": "FOB or CIF? DDP or DAP? A quick chart that will save you 30% on disputes and 10% on freight.", "readMins": 5},
    {"slug": "india-uae-cepa-product-list", "title": "India–UAE CEPA: full list of products with 0% duty", "category": "Trade News", "date": "Jan 6, 2026", "image": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80", "excerpt": "11,908 products at zero duty. Find yours in 30 seconds — and start saving 5–18% per shipment.", "readMins": 8},
    {"slug": "lcs-vs-da-vs-tt-payment-terms", "title": "LC vs DA vs TT — which payment term protects your margin?", "category": "Logistics", "date": "Jan 4, 2026", "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80", "excerpt": "A practical guide for first-time exporters — when to insist on an LC, when DA is fine, and when never to take TT.", "readMins": 6},
    {"slug": "how-to-find-buyers-in-gcc", "title": "How to find your first buyer in the GCC", "category": "International Marketing", "date": "Jan 2, 2026", "image": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80", "excerpt": "From Gulfood to LinkedIn to LeadNation — the 9 channels that work for new GCC exporters.", "readMins": 10},
]


@api_router.get("/blog")
async def blog_list():
    return BLOG_DB


@api_router.get("/blog/{slug}")
async def blog_detail(slug: str):
    post = next((b for b in BLOG_DB if b["slug"] == slug), None)
    if not post:
        return JSONResponse(status_code=404, content={"error": "Blog post not found"})
    # add body
    full = {**post, "body": [
        "International trade can feel overwhelming when you're just starting. But the principles never change: the right paperwork, the right partner and the right pricing.",
        "In this guide we walk through every step — from registration to shipping bill — with a checklist you can use today.",
        "The most important thing is to start with a small, friendly market and grow incrementally. Most successful Indian exporters did their first shipment to UAE or Singapore.",
        "Want help moving faster? LeadNation's app gives you HSN codes, duty rates, buyers and compliance in one screen.",
    ]}
    return full


# ----- Marketplace & Network (mock previews) -----
@api_router.get("/marketplace")
async def marketplace():
    return {
        "listings": [
            {"id": 1, "title": "Premium Basmati Rice — 1121", "supplier": "KRBL Ltd", "price": "USD 1,180 / MT", "moq": "26 MT", "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=80"},
            {"id": 2, "title": "Agarbatti Bulk — Sandalwood", "supplier": "Mysore Sandal", "price": "USD 2.4 / kg", "moq": "500 kg", "image": "https://images.unsplash.com/photo-1602874801007-bd45867d505b?auto=format&fit=crop&w=900&q=80"},
            {"id": 3, "title": "Cotton Bed Linen Sets", "supplier": "Welspun", "price": "USD 18 / set", "moq": "500 sets", "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80"},
            {"id": 4, "title": "Turmeric Powder — Lakadong", "supplier": "ITC Spices", "price": "USD 4.2 / kg", "moq": "2 MT", "image": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=900&q=80"},
            {"id": 5, "title": "Paracetamol Tablets 500mg", "supplier": "Cipla Exports", "price": "USD 0.012 / tab", "moq": "1M tabs", "image": "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?auto=format&fit=crop&w=900&q=80"},
            {"id": 6, "title": "Auto Parts — Bearings", "supplier": "Mahindra Auto", "price": "USD 6.4 / pc", "moq": "10K pcs", "image": "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?auto=format&fit=crop&w=900&q=80"},
        ],
        "reels": [
            {"id": 1, "title": "Inside Mundra Port — 9M containers/yr", "thumb": "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=600&q=80"},
            {"id": 2, "title": "How Basmati gets to Saudi", "thumb": "https://images.unsplash.com/photo-1605902711622-cfb43c4437b5?auto=format&fit=crop&w=600&q=80"},
            {"id": 3, "title": "First export at 22 — Tirupur founder", "thumb": "https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=600&q=80"},
            {"id": 4, "title": "Inside Jebel Ali Free Zone", "thumb": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=600&q=80"},
        ],
        "buyerRequests": [
            {"id": 1, "title": "RFQ · 50 MT Basmati to Riyadh · Halal certified", "country": "🇸🇦"},
            {"id": 2, "title": "RFQ · 1,000 cartons Agarbatti to Dubai · monthly", "country": "🇦🇪"},
            {"id": 3, "title": "RFQ · 200 MT Turmeric to Houston · USDA Organic", "country": "🇺🇸"},
        ],
    }


@api_router.get("/network")
async def network():
    return {
        "members": [
            {"name": "Rohan Mehta", "role": "Exporter · Basmati Rice", "city": "Karnal, IN", "avatar": "https://i.pravatar.cc/120?img=11"},
            {"name": "Aisha Al-Rashid", "role": "Importer · GCC Wholesale", "city": "Dubai, AE", "avatar": "https://i.pravatar.cc/120?img=25"},
            {"name": "Sundar Iyer", "role": "CHA · Customs House Agent", "city": "Chennai, IN", "avatar": "https://i.pravatar.cc/120?img=33"},
            {"name": "Ana García", "role": "Buyer · Latin America", "city": "São Paulo, BR", "avatar": "https://i.pravatar.cc/120?img=49"},
            {"name": "James O'Connor", "role": "Logistics · NVOCC", "city": "London, GB", "avatar": "https://i.pravatar.cc/120?img=57"},
            {"name": "Priya Sharma", "role": "Export Agent · Pharma", "city": "Hyderabad, IN", "avatar": "https://i.pravatar.cc/120?img=44"},
        ],
        "stats": [
            {"label": "Verified members", "value": "48,200+"},
            {"label": "Countries covered", "value": "92"},
            {"label": "Categories", "value": "112"},
            {"label": "Avg response time", "value": "< 6 hrs"},
        ],
    }


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
