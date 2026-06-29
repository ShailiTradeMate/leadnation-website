from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN, decode_token

router = APIRouter()


from engines import COUNTRY_PROFILES
from content import PRODUCTS_DB, CORRIDOR_DB, INDUSTRY_DB, BLOG_DB
from trade_tools import HSN_DB

# ----- Admin auth -----
class AdminLoginRequest(BaseModel):
    token: str


@router.post("/admin/login")
async def admin_login(payload: AdminLoginRequest):
    if payload.token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"ok": True, "token": ADMIN_TOKEN}


# ----- Generic content collections (CMS) -----
CMS_COLLECTIONS = {
    "countries": COUNTRY_PROFILES,
    "products": PRODUCTS_DB,
    "corridors": CORRIDOR_DB,
    "hsn_codes": HSN_DB,
    "industries": INDUSTRY_DB,
    "blog": {b["slug"]: b for b in BLOG_DB},
}


async def _seed_collection(name: str, source: dict):
    coll = db[f"cms_{name}"]
    if await coll.count_documents({}) == 0 and source:
        docs = []
        for k, v in source.items():
            doc = {**v, "id": str(uuid.uuid4()), "slug": v.get("slug") or v.get("code") or k, "published": True,
                   "createdAt": datetime.now(timezone.utc).isoformat(),
                   "updatedAt": datetime.now(timezone.utc).isoformat()}
            docs.append(doc)
        if docs:
            await coll.insert_many(docs)




@router.get("/admin/collections")
async def list_collections(_: bool = Depends(require_admin)):
    out = []
    for name in CMS_COLLECTIONS.keys():
        coll = db[f"cms_{name}"]
        out.append({"name": name, "count": await coll.count_documents({})})
    # also expose service requests + leads
    out.append({"name": "leads", "count": await db.leads.count_documents({})})
    out.append({"name": "service_requests", "count": await db.service_requests.count_documents({})})
    return out


@router.get("/admin/collection/{name}")
async def admin_list_items(name: str, _: bool = Depends(require_admin)):
    if name not in CMS_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Unknown collection")
    items = await db[f"cms_{name}"].find({}, {"_id": 0}).to_list(2000)
    return items


@router.post("/admin/collection/{name}")
async def admin_create_item(name: str, payload: dict, _: bool = Depends(require_admin)):
    if name not in CMS_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Unknown collection")
    item = {**payload, "id": str(uuid.uuid4()),
            "published": payload.get("published", True),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()}
    await db[f"cms_{name}"].insert_one(item)
    item.pop("_id", None)
    return item


@router.put("/admin/collection/{name}/{item_id}")
async def admin_update_item(name: str, item_id: str, payload: dict, _: bool = Depends(require_admin)):
    if name not in CMS_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Unknown collection")
    payload["updatedAt"] = datetime.now(timezone.utc).isoformat()
    res = await db[f"cms_{name}"].update_one({"id": item_id}, {"$set": payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await db[f"cms_{name}"].find_one({"id": item_id}, {"_id": 0})
    return item


@router.delete("/admin/collection/{name}/{item_id}")
async def admin_delete_item(name: str, item_id: str, _: bool = Depends(require_admin)):
    if name not in CMS_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Unknown collection")
    res = await db[f"cms_{name}"].delete_one({"id": item_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


# ----- Lead management -----
@router.get("/admin/leads")
async def admin_leads(_: bool = Depends(require_admin)):
    items = await db.leads.find({}, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    return items


@router.get("/admin/leads.csv")
async def admin_leads_csv(token: str = Query(...)):
    from firebase_auth import verify_token
    ok = token == ADMIN_TOKEN
    if not ok:
        claims = verify_token(token)
        if claims:
            u = await db.users.find_one({"uid": claims.get("uid")})
            ok = bool(u and u.get("role") == "admin")
    if not ok:
        raise HTTPException(status_code=401, detail="Unauthorised")
    items = await db.leads.find({}, {"_id": 0}).sort("createdAt", -1).to_list(5000)
    buf = io.StringIO()
    cols = ["createdAt", "name", "email", "phone", "country", "source", "score", "message", "product", "id"]
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for it in items:
        writer.writerow({c: it.get(c, "") for c in cols})
    buf.seek(0)
    return StreamingResponse(iter([buf.read()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=leads.csv"})


@router.get("/admin/service-requests")
async def admin_service_requests(_: bool = Depends(require_admin)):
    items = await db.service_requests.find({}, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    return items


class ServiceAssignRequest(BaseModel):
    status: Optional[str] = None
    assignedCa: Optional[str] = None
    notes: Optional[str] = None


@router.put("/admin/service-requests/{req_id}")
async def admin_update_service_request(req_id: str, payload: ServiceAssignRequest, _: bool = Depends(require_admin)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    update["updatedAt"] = datetime.now(timezone.utc).isoformat()
    res = await db.service_requests.update_one({"id": req_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    item = await db.service_requests.find_one({"id": req_id}, {"_id": 0})
    return item


