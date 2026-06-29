"""Shared Firebase identity — verifies the SAME Firebase project as the mobile app.

Passwords live ONLY in Firebase. We verify the Firebase ID token on every protected
route and join to MongoDB via the Firebase uid. Service account comes from the
base64-encoded env var FIREBASE_SERVICE_ACCOUNT_B64 (never committed).
"""
import os
import json
import base64
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, auth as fb_auth
from fastapi import Header, HTTPException

_initialised = False


def init_firebase():
    global _initialised
    if _initialised or firebase_admin._apps:
        _initialised = True
        return
    b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_B64", "").strip()
    if not b64:
        logging.warning("FIREBASE_SERVICE_ACCOUNT_B64 not set — Firebase auth disabled.")
        return
    try:
        info = json.loads(base64.b64decode(b64).decode("utf-8"))
        cred = credentials.Certificate(info)
        firebase_admin.initialize_app(cred)
        _initialised = True
        logging.info("Firebase Admin initialised for project %s", info.get("project_id"))
    except Exception as exc:
        logging.error("Firebase init failed: %s", exc)


def verify_token(id_token: str) -> Optional[dict]:
    if not _initialised:
        init_firebase()
    try:
        return fb_auth.verify_id_token(id_token)
    except Exception as exc:
        logging.warning("Token verify failed: %s", exc)
        return None


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


async def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency → decoded Firebase token (uid, email, ...)."""
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    if not claims:
        raise HTTPException(status_code=401, detail="Authentication required")
    return claims


async def optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[dict]:
    token = _bearer(authorization)
    return verify_token(token) if token else None


# ---- Admin helpers (Firebase user management) ----
def get_user_by_email(email: str):
    try:
        return fb_auth.get_user_by_email(email)
    except Exception:
        return None


def create_user(email: str, password: str, display_name: str = "", email_verified: bool = False):
    return fb_auth.create_user(email=email, password=password,
                               display_name=display_name or None, email_verified=email_verified)


def delete_user(uid: str) -> bool:
    try:
        fb_auth.delete_user(uid)
        return True
    except Exception as exc:
        logging.warning("Firebase delete_user failed for %s: %s", uid, exc)
        return False


def set_email_verified(uid: str) -> bool:
    try:
        fb_auth.update_user(uid, email_verified=True)
        return True
    except Exception as exc:
        logging.warning("Firebase set_email_verified failed for %s: %s", uid, exc)
        return False
