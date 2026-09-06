"""Shared core: Mongo connection, config, JWT + admin auth dependency."""
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "leadnation-admin-2026")
MAIN_ADMIN_CUSTOMER_ID = os.environ.get("MAIN_ADMIN_CUSTOMER_ID", "00001")
JWT_SECRET = os.environ.get("JWT_SECRET", "leadnation-jwt-secret-change-me")
JWT_ALG = "HS256"
JWT_TTL_HOURS = 24


def create_access_token(sub: str, role: str = "admin") -> str:
    payload = {"sub": sub, "role": role,
               "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None


async def resolve_admin_identity(claims: dict, authorization: Optional[str]) -> Optional[dict]:
    """Resolve main-admin status for a verified Firebase user.

    The DigitalOcean backend OWNS identity/roles, so the local Mongo `users` doc is
    only a cache: if it says admin we accept, otherwise we ask DO for the canonical
    shared profile (role == 'admin' or the main-admin Customer ID). Without this the
    admin CMS works in one environment and 401s in another.
    """
    uid = claims.get("uid")
    if not uid:
        return None
    u = await db.users.find_one({"uid": uid}) or {}
    if u.get("role") == "admin" and not u.get("is_deleted"):
        return {"uid": uid, "email": u.get("email"), "customer_id": u.get("customer_id"),
                "name": u.get("full_name") or u.get("name") or "Admin",
                "role": "admin", "source": "mongo"}
    try:
        import verify
        p = verify._do_get_profile(uid, authorization) or {}
    except Exception:
        p = {}
    cid = str(p.get("customer_id") or "").strip()
    if not p.get("is_deleted") and (p.get("role") == "admin" or p.get("user_role") == "admin"
                                    or (cid and cid.zfill(5) == MAIN_ADMIN_CUSTOMER_ID)):
        return {"uid": uid, "email": p.get("email") or claims.get("email"),
                "customer_id": p.get("customer_id"),
                "name": p.get("name") or p.get("full_name") or "Admin",
                "role": "admin", "source": "do_profile"}
    return None


async def require_admin(authorization: Optional[str] = Header(default=None),
                        x_admin_token: Optional[str] = Header(default=None)):
    """Admin gate — shared identity: a verified Firebase user who is an admin on the
    canonical DO profile (or the local Mongo cache). Legacy X-Admin-Token is an
    emergency fallback only."""
    from firebase_auth import verify_token
    if authorization and authorization.lower().startswith("bearer "):
        claims = verify_token(authorization.split(" ", 1)[1].strip())
        if claims:
            ident = await resolve_admin_identity(claims, authorization)
            if ident:
                return ident
    if x_admin_token and x_admin_token == ADMIN_TOKEN:
        return {"sub": "legacy", "role": "admin"}
    raise HTTPException(status_code=401, detail="Admin access required")
