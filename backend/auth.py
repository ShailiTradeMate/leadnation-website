"""Site Settings control center backend. Admin identity = shared Firebase user
(users.role == 'admin'); passwords live ONLY in Firebase — no separate admin store."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core import db, require_admin

router = APIRouter()

SETTINGS = db.site_settings

DEFAULT_SETTINGS = {
    "_id": "site",
    "accentColor": "#00C2FF",
    "maintenance": False,
    "maintenanceMessage": "We're making improvements — back shortly.",
    "features": {  # nav/feature visibility toggles
        "customs": True, "academy": True, "intelligence": True,
        "blog": True, "trade_news": True, "tools": True, "services": True,
        "brain": True, "expo": True,
    },
    "serviceRates": {},  # slug -> override price string
}


async def seed_settings():
    if not await SETTINGS.find_one({"_id": "site"}):
        await SETTINGS.insert_one(dict(DEFAULT_SETTINGS))


# ---------------- Site settings ----------------
async def _get_settings():
    doc = await SETTINGS.find_one({"_id": "site"})
    if not doc:
        await SETTINGS.insert_one(dict(DEFAULT_SETTINGS))
        doc = dict(DEFAULT_SETTINGS)
    doc.pop("_id", None)
    return doc


@router.get("/settings")
async def public_settings():
    """Public — consumed by the site to apply theme / feature toggles / maintenance."""
    return await _get_settings()


class SettingsUpdate(BaseModel):
    accentColor: str | None = None
    maintenance: bool | None = None
    maintenanceMessage: str | None = None
    features: dict | None = None
    serviceRates: dict | None = None


@router.put("/admin/settings")
async def update_settings(body: SettingsUpdate, claims: dict = Depends(require_admin)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    patch["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await SETTINGS.update_one({"_id": "site"}, {"$set": patch}, upsert=True)
    return await _get_settings()

