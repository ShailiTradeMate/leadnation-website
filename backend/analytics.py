from fastapi import APIRouter, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid, io, csv, logging
from core import db, require_admin, ADMIN_TOKEN

router = APIRouter()


# ----- Analytics event collector (so the website can log events even without GA wired) -----
class AnalyticsEvent(BaseModel):
    name: str
    path: Optional[str] = None
    meta: Optional[dict] = None


@router.post("/track")
async def track_event(payload: AnalyticsEvent):
    doc = payload.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["createdAt"] = datetime.now(timezone.utc).isoformat()
    await db.events.insert_one(doc)
    return {"ok": True}


@router.get("/admin/events")
async def admin_events(_: bool = Depends(require_admin)):
    items = await db.events.find({}, {"_id": 0}).sort("createdAt", -1).to_list(500)
    return items


