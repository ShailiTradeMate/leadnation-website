from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


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
@router.get("/")
async def root():
    return {"message": "LeadNation API · Global Trade Intelligence", "version": "1.0.0"}


@router.post("/status", response_model=StatusCheck)
async def create_status_check(payload: StatusCheckCreate):
    status_obj = StatusCheck(**payload.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ----- Reference data -----
@router.get("/countries")
async def list_countries():
    return COUNTRIES


@router.get("/business-types")
async def list_business_types():
    return BUSINESS_TYPES


@router.get("/trade-directions")
async def list_trade_directions():
    return TRADE_DIRECTIONS


@router.get("/products")
async def list_products():
    return PRODUCTS


