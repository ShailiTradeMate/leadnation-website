"""Admin authentication (JWT) + Site Settings control center backend."""
import bcrypt
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core import db, create_access_token, require_admin

router = APIRouter()

ADMINS = db.admin_users
SETTINGS = db.site_settings

DEFAULT_USERNAME = "00001"
DEFAULT_PASSWORD = "Shiv@12345"

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


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _verify(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


async def seed_admin():
    existing = await ADMINS.find_one({"username": DEFAULT_USERNAME})
    if not existing:
        await ADMINS.insert_one({
            "username": DEFAULT_USERNAME, "passwordHash": _hash(DEFAULT_PASSWORD),
            "role": "superadmin", "createdAt": datetime.now(timezone.utc).isoformat(),
        })
    if not await SETTINGS.find_one({"_id": "site"}):
        await SETTINGS.insert_one(dict(DEFAULT_SETTINGS))


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/admin/login")
async def admin_login(payload: LoginRequest):
    user = await ADMINS.find_one({"username": payload.username.strip()})
    if not user or not _verify(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(sub=user["username"], role="admin")
    return {"token": token, "username": user["username"], "role": user.get("role", "admin")}


@router.get("/auth/admin/me")
async def admin_me(claims: dict = Depends(require_admin)):
    return {"username": claims.get("sub"), "role": claims.get("role")}


class PasswordChange(BaseModel):
    newPassword: str


@router.post("/auth/admin/password")
async def change_password(body: PasswordChange, claims: dict = Depends(require_admin)):
    if len(body.newPassword) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    await ADMINS.update_one({"username": claims.get("sub")},
                            {"$set": {"passwordHash": _hash(body.newPassword)}})
    return {"ok": True}


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
