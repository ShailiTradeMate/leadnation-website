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
