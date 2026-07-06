from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN
from emailer import notify_admin

router = APIRouter()


from reference import LeadCreate

@router.post("/leads")
async def create_lead(payload: LeadCreate):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    await db.leads.insert_one(doc)
    await notify_admin("admin_new_lead", {
        "name": doc.get("name", ""), "email": doc.get("email", ""), "phone": doc.get("phone", ""),
        "country": doc.get("country", ""), "source": doc.get("source", "website")})
    return {"ok": True, "id": doc["id"]}


