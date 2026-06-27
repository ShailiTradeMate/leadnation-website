from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


from reference import COUNTRIES, PRODUCTS
from content import BLOG_DB
from trade_tools import HSN_DB
from services import SERVICES_DB

@router.get("/search")
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


# ----- Global search -----
@router.get("/global-search")
async def global_search(q: str = Query(min_length=1)):
    ql = q.lower().strip()
    results = []

    def _add(typ, label, to, sub=""):
        results.append({"type": typ, "label": label, "to": to, "sub": sub})

    # CMS-backed collections (if seeded) — search products
    type_map = {"products": "product", "corridors": "corridor", "countries": "country", "industries": "industry"}

    async def _scan(collection_name, prefix, slug_field="slug", title_field="name"):
        try:
            cursor = db[f"cms_{collection_name}"].find({}, {"_id": 0, slug_field: 1, title_field: 1, "category": 1, "tagline": 1})
            async for d in cursor:
                title = (d.get(title_field) or "").lower()
                if ql in title:
                    _add(type_map.get(collection_name, collection_name), d.get(title_field, ""), f"/{prefix}/{d.get(slug_field, '')}", d.get("tagline") or d.get("category", ""))
        except Exception:
            logging.exception("global search scan failed for %s", collection_name)

    await _scan("products", "products")
    await _scan("corridors", "corridors")
    await _scan("countries", "countries")
    await _scan("industries", "industries")

    # blog
    for b in BLOG_DB:
        if ql in b["title"].lower() or ql in b["category"].lower():
            _add("blog", b["title"], f"/blog/{b['slug']}", b["category"])

    # HSN
    for code, h in HSN_DB.items():
        if ql in code or ql in h["title"].lower():
            _add("hsn", f"HSN {code} · {h['title']}", f"/hsn/{code}", h["category"])

    # Services
    for s in SERVICES_DB.values():
        if ql in s["name"].lower() or ql in s["category"].lower():
            _add("service", s["name"], f"/services/{s['slug']}", s["category"])

    # Tools
    tools = [
        ("HSN Finder", "/tools/hsn-finder"), ("Duty Calculator", "/tools/duty-calculator"),
        ("Landed Cost Calculator", "/tools/landed-cost-calculator"), ("Export Incentive Finder", "/tools/export-incentive-finder"),
        ("Product Research", "/tools/product-research"), ("Find Buyers", "/tools/find-buyers"),
        ("Export Readiness", "/tools/export-readiness"), ("AI Trade Copilot", "/ai-assistant"),
    ]
    for label, to in tools:
        if ql in label.lower():
            _add("tool", label, to, "Free tool")

    return {"query": q, "total": len(results), "results": results[:30]}


