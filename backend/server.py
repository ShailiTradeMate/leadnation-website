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
