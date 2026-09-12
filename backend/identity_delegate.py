"""Short-lived, server-only delegation for explicitly authorized main-admin actions.

DO binds the token subject. Never send the administrator's token to /members/bind.
No session tokens are returned to a route caller, cached, logged, or persisted.
"""
import asyncio
import os
import requests
from fastapi import HTTPException
from firebase_admin import auth
from firebase_auth import init_firebase


def _delegate(uid):
    init_firebase()
    try:
        user = auth.get_user(uid)
        if user.disabled:
            raise HTTPException(409, "This user is disabled.")
        custom = auth.create_custom_token(uid).decode("utf-8")
        base = os.environ["FIREBASE_IDENTITY_TOOLKIT_URL"].rstrip("/")
        params = {"key": os.environ["FIREBASE_WEB_API_KEY"]}
        exchange = requests.post(f"{base}/accounts:signInWithCustomToken", params=params,
                                 json={"token": custom, "returnSecureToken": True}, timeout=25)
        if not exchange.ok:
            raise HTTPException(502, "Server identity delegation failed.")
        data = exchange.json()
        if data.get("isNewUser") or not data.get("idToken"):
            raise HTTPException(409, "Existing identity could not be confirmed.")
        token = data["idToken"]
        lookup = requests.post(f"{base}/accounts:lookup", params=params, json={"idToken": token}, timeout=25)
        if not lookup.ok or {u.get("localId") for u in lookup.json().get("users", [])} != {uid}:
            raise HTTPException(502, "Delegated identity did not match the target user.")
        return f"Bearer {token}"
    except auth.UserNotFoundError:
        raise HTTPException(404, "Target Firebase user no longer exists.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Identity delegation is unavailable; approval was not applied.")


async def for_approved_action(uid, actor):
    if not actor.get("is_main"):
        raise HTTPException(403, "Main-admin approval is required.")
    return await asyncio.to_thread(_delegate, uid)