"""Shared user accounts — ONE Firebase identity + ONE Atlas DB (leadnation).

Mirrors the mobile app exactly:
  * Join key = Firebase uid (users.uid == profiles.uid).
  * Human key = customer_id (00001, 00002…) allocated idempotently via the shared
    `_counters` atomic counter (one uid → one customer_id, never duplicated).
  * Passwords live ONLY in Firebase. Mongo stores profile/account data.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import ReturnDocument

from core import db
from firebase_auth import require_user, delete_user as fb_delete_user, set_email_verified

router = APIRouter()

TEST_OTP = os.environ.get("TEST_OTP", "123456")

BUSINESS_ROLES = {"exporter", "importer", "supplier", "manufacturer",
                  "farmer", "cha", "export_agent", "consultant"}


def _now():
    return datetime.now(timezone.utc).isoformat()


async def allocate_customer_id() -> str:
    doc = await db["_counters"].find_one_and_update(
        {"_id": "customer_id"}, {"$inc": {"seq": 1}},
        upsert=True, return_document=ReturnDocument.AFTER)
    return f"{doc['seq']:05d}"


# ---------------- Models ----------------
class RegisterBody(BaseModel):
    full_name: Optional[str] = ""
    role: Optional[str] = "exporter"          # business role
    mobile_number: Optional[str] = ""
    provider: Optional[str] = "password"      # password | google
    country: Optional[str] = ""
    country_code: Optional[str] = ""
    business_name: Optional[str] = ""


class ResolveBody(BaseModel):
    customer_id: str


# ---------------- Onboarding (idempotent Customer-ID allocation) ----------------
@router.post("/onboarding/register")
async def register(body: RegisterBody, claims: dict = Depends(require_user)):
    uid = claims["uid"]
    email = claims.get("email", "")
    provider = body.provider or ("google" if (claims.get("firebase", {}).get("sign_in_provider") == "google.com") else "password")

    existing = await db.users.find_one({"uid": uid})
    if existing:
        # already onboarded → return as-is (idempotent), ensure a profile exists
        if not await db.profiles.find_one({"uid": uid}):
            await _create_profile(uid, existing.get("customer_id"), existing, body)
        return {"ok": True, "customer_id": existing.get("customer_id"),
                "role": existing.get("role"), "new": False}

    business_role = body.role if body.role in BUSINESS_ROLES else "exporter"
    customer_id = await allocate_customer_id()
    now = _now()
    user_doc = {
        "uid": uid, "customer_id": customer_id, "email": email,
        "full_name": body.full_name or "", "role": "user", "user_role": business_role,
        "mobile_number": body.mobile_number or "", "provider": provider,
        "auth_methods": [provider], "is_email_verified": bool(claims.get("email_verified")),
        "onboarding_status": "completed", "verification_status": "pending",
        "kyc_status": "pending", "is_deleted": False, "is_suspended": False, "is_active": True,
        "subscription_status": "free", "subscription_expiry": None, "subscription_plan": "free",
        "country": body.country or "", "country_code": body.country_code or "",
        "state": "", "city": "", "created_at": now, "last_activity_at": now,
    }
    await db.users.insert_one(user_doc)
    await _create_profile(uid, customer_id, user_doc, body)
    return {"ok": True, "customer_id": customer_id, "role": business_role, "new": True}


async def _create_profile(uid, customer_id, user_doc, body: RegisterBody):
    await db.profiles.update_one({"uid": uid}, {"$setOnInsert": {
        "uid": uid, "customer_id": customer_id,
        "name": user_doc.get("full_name", ""), "mobile": user_doc.get("mobile_number", ""),
        "email": user_doc.get("email", ""), "role": user_doc.get("user_role", "exporter"),
        "country": body.country or "", "city": "",
        "hsn_codes": [], "products": [],
        "business_media": {"images": [], "videos": []},
        "company_details": {"company_name": body.business_name or "", "description": ""},
        "verification_status": "pending", "created_at": _now(),
    }}, upsert=True)


# ---------------- Login helpers ----------------
@router.post("/auth/resolve-customer-id")
async def resolve_customer_id(body: ResolveBody):
    cid = body.customer_id.strip().zfill(5) if body.customer_id.strip().isdigit() else body.customer_id.strip()
    u = await db.users.find_one({"customer_id": cid, "is_deleted": {"$ne": True}})
    if not u or not u.get("email"):
        raise HTTPException(status_code=404, detail="Customer ID not found")
    return {"email": u["email"], "customer_id": u["customer_id"]}


def _sanitize(doc):
    if not doc:
        return None
    doc.pop("_id", None)
    return doc


@router.get("/auth/me")
async def me(claims: dict = Depends(require_user)):
    uid = claims["uid"]
    u = await db.users.find_one({"uid": uid})
    if not u:
        # signed into Firebase but not onboarded yet
        return {"onboarded": False, "uid": uid, "email": claims.get("email"),
                "email_verified": bool(claims.get("email_verified"))}
    await db.users.update_one({"uid": uid}, {"$set": {"last_activity_at": _now()}})
    profile = await db.profiles.find_one({"uid": uid})
    return {"onboarded": True, "user": _sanitize(u), "profile": _sanitize(profile)}


# ---------------- Email verification (TEST OTP until provider connected) ----------------
class OtpBody(BaseModel):
    otp: str


@router.post("/auth/request-otp")
async def request_otp(claims: dict = Depends(require_user)):
    # OTP provider not yet connected — return the test instruction.
    return {"ok": True, "test_mode": True,
            "message": "Enter the test code 123456 to verify your email (live OTP provider coming soon)."}


@router.post("/auth/verify-otp")
async def verify_otp(body: OtpBody, claims: dict = Depends(require_user)):
    if body.otp.strip() != TEST_OTP:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    uid = claims["uid"]
    set_email_verified(uid)
    await db.users.update_one({"uid": uid}, {"$set": {"is_email_verified": True}})
    return {"ok": True, "verified": True}


# ---------------- Admin (shared) ----------------
async def require_admin_user(claims: dict = Depends(require_user)):
    u = await db.users.find_one({"uid": claims["uid"]})
    if not u or u.get("role") != "admin" or u.get("is_deleted"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return u


@router.get("/admin_v2/users")
async def list_users(limit: int = 100, _: dict = Depends(require_admin_user)):
    docs = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"users": docs, "total": await db.users.count_documents({})}


@router.delete("/admin_v2/users/{customer_id}/hard-delete")
async def hard_delete_user(customer_id: str, admin: dict = Depends(require_admin_user)):
    if customer_id == "00001":
        raise HTTPException(status_code=403, detail="Super-admin 00001 cannot be deleted")
    target = await db.users.find_one({"customer_id": customer_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.get("uid") == admin.get("uid"):
        raise HTTPException(status_code=403, detail="You cannot delete your own account")

    uid = target["uid"]
    # 1) Firebase Auth
    fb_ok = fb_delete_user(uid)
    # 2) Firestore (best-effort)
    try:
        from firebase_admin import firestore
        fs = firestore.client()
        for coll in ("users", "profiles"):
            fs.collection(coll).document(uid).delete()
    except Exception as exc:
        logging.warning("Firestore purge skipped: %s", exc)
    # 3) MongoDB — users, profiles + known per-user collections
    purged = {}
    for coll in ("users", "profiles", "company_profiles", "notifications", "chats",
                 "ai_conversations", "marketplace_listings"):
        try:
            r = await db[coll].delete_many({"$or": [{"uid": uid}, {"customer_id": customer_id}]})
            purged[coll] = r.deleted_count
        except Exception:
            pass
    return {"ok": True, "customer_id": customer_id, "firebase_deleted": fb_ok, "mongo_purged": purged}
