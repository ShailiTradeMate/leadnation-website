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


async def require_admin(authorization: Optional[str] = Header(default=None),
                        x_admin_token: Optional[str] = Header(default=None)):
    """Admin gate — shared identity: a verified Firebase user whose Mongo users.role == 'admin'.
    Legacy X-Admin-Token kept only as an emergency fallback."""
    from firebase_auth import verify_token
    if authorization and authorization.lower().startswith("bearer "):
        claims = verify_token(authorization.split(" ", 1)[1].strip())
        if claims:
            u = await db.users.find_one({"uid": claims.get("uid")})
            if u and u.get("role") == "admin" and not u.get("is_deleted"):
                return {"uid": claims["uid"], "email": u.get("email"),
                        "customer_id": u.get("customer_id"), "role": "admin"}
    if x_admin_token and x_admin_token == ADMIN_TOKEN:
        return {"sub": "legacy", "role": "admin"}
    raise HTTPException(status_code=401, detail="Admin access required")
