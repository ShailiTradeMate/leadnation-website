"""Meta Marketing API — READ-ONLY. Verifies the user token, exchanges it for a long-lived one
(kept server-side in Mongo, never returned), and reads ad accounts / campaigns / insights.
No POST/DELETE to Graph is ever issued from here."""
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from core import db, require_admin

logger = logging.getLogger("meta_ads")
logging.getLogger("httpx").setLevel(logging.WARNING)  # Graph URLs carry the token
router = APIRouter(prefix="/admin/meta", tags=["admin-meta-ads"])

GRAPH = "https://graph.facebook.com/v27.0"
TOKEN_DOC = "meta_long_lived_user_token"
STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW", 8: "PENDING_SETTLEMENT",
          9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE", 101: "CLOSED", 201: "ANY_ACTIVE", 202: "ANY_CLOSED"}


def _app_token() -> str:
    return f"{os.environ.get('META_APP_ID', '')}|{os.environ.get('META_APP_SECRET', '')}"


async def _token() -> str:
    """Prefer the stored long-lived token while valid, else the env (short-lived) one."""
    doc = await db.secrets_store.find_one({"_id": TOKEN_DOC})
    if doc and datetime.fromisoformat(doc["expiresAt"]) > datetime.now(timezone.utc):
        return doc["token"]
    return os.environ.get("META_ACCESS_TOKEN", "")


def _sanitize(exc_text: str) -> str:
    for secret in (os.environ.get("META_APP_SECRET", ""), os.environ.get("META_ACCESS_TOKEN", "")):
        if secret:
            exc_text = exc_text.replace(secret, "***")
    return exc_text[:300]


async def graph_get(path: str, params: dict | None = None, token: str | None = None) -> dict:
    p = {"access_token": token or await _token(), **(params or {})}
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.get(f"{GRAPH}/{path.lstrip('/')}", params=p)
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200:
        err = (body.get("error") or {})
        raise HTTPException(status_code=502, detail={
            "graphStatus": r.status_code, "code": err.get("code"), "subcode": err.get("error_subcode"),
            "message": _sanitize(err.get("message") or "Meta request failed")})
    return body


async def token_info(token: str) -> dict:
    d = (await graph_get("debug_token", {"input_token": token}, token=_app_token())).get("data", {})
    exp = d.get("expires_at")
    return {"valid": d.get("is_valid"), "appId": d.get("app_id"), "userId": d.get("user_id"),
            "type": d.get("type"), "scopes": d.get("scopes", []),
            "expiresAt": datetime.fromtimestamp(exp, timezone.utc).isoformat() if exp else "never",
            "dataAccessExpiresAt": (datetime.fromtimestamp(d["data_access_expires_at"], timezone.utc).isoformat()
                                    if d.get("data_access_expires_at") else None)}


@router.get("/status")
async def status(_=Depends(require_admin)):
    configured = {"token": bool(os.environ.get("META_ACCESS_TOKEN")), "appId": bool(os.environ.get("META_APP_ID")),
                  "appSecret": bool(os.environ.get("META_APP_SECRET"))}
    if not all(configured.values()):
        return {"ok": False, "configured": configured}
    tok = await _token()
    stored = await db.secrets_store.find_one({"_id": TOKEN_DOC}, {"token": 0})
    info = await token_info(tok)
    me = await graph_get("me", {"fields": "id,name"}, token=tok)
    accts = (await graph_get("me/adaccounts", {"fields": "id,account_id,name,account_status,currency,timezone_name,business",
                                               "limit": 50}, token=tok)).get("data", [])
    return {"ok": True, "configured": configured, "token": info,
            "usingLongLived": bool(stored and datetime.fromisoformat(stored["expiresAt"]) > datetime.now(timezone.utc)),
            "longLived": {"expiresAt": stored["expiresAt"], "exchangedAt": stored["exchangedAt"]} if stored else None,
            "user": me,
            "adAccounts": [{**a, "statusLabel": STATUS.get(a.get("account_status"), str(a.get("account_status")))} for a in accts]}


@router.post("/exchange-token")
async def exchange_token(_=Depends(require_admin)):
    """Short-lived user token → ~60-day token. Stored server-side only; the response carries expiry, never the token."""
    short = os.environ.get("META_ACCESS_TOKEN", "")
    if not short:
        raise HTTPException(400, "META_ACCESS_TOKEN not configured")
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.get(f"{GRAPH}/oauth/access_token", params={
            "grant_type": "fb_exchange_token", "client_id": os.environ.get("META_APP_ID", ""),
            "client_secret": os.environ.get("META_APP_SECRET", ""), "fb_exchange_token": short})
    body = r.json()
    if r.status_code != 200 or "access_token" not in body:
        raise HTTPException(502, {"message": _sanitize((body.get("error") or {}).get("message") or "exchange failed")})
    long_tok = body["access_token"]
    info = await token_info(long_tok)
    expires_at = info["expiresAt"] if info["expiresAt"] != "never" else (
        datetime.now(timezone.utc) + timedelta(seconds=int(body.get("expires_in", 5184000)))).isoformat()
    await db.secrets_store.replace_one({"_id": TOKEN_DOC}, {
        "_id": TOKEN_DOC, "token": long_tok, "expiresAt": expires_at,
        "exchangedAt": datetime.now(timezone.utc).isoformat(), "scopes": info["scopes"]}, upsert=True)
    return {"ok": True, "expiresAt": expires_at, "scopes": info["scopes"], "valid": info["valid"],
            "daysLeft": round((datetime.fromisoformat(expires_at) - datetime.now(timezone.utc)).total_seconds() / 86400, 1)}


@router.get("/account/{account_id}")
async def account(account_id: str, _=Depends(require_admin)):
    aid = account_id.removeprefix("act_")
    if not aid.isdigit():
        raise HTTPException(400, "account_id must be numeric")
    a = await graph_get(f"act_{aid}", {"fields": "name,account_status,currency,timezone_name,amount_spent,balance,spend_cap"})
    return {**a, "statusLabel": STATUS.get(a.get("account_status"), str(a.get("account_status")))}


@router.get("/account/{account_id}/campaigns")
async def campaigns(account_id: str, _=Depends(require_admin)):
    aid = account_id.removeprefix("act_")
    if not aid.isdigit():
        raise HTTPException(400, "account_id must be numeric")
    return await graph_get(f"act_{aid}/campaigns", {"fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,created_time", "limit": 100})


@router.get("/account/{account_id}/insights")
async def insights(account_id: str, date_preset: str = "last_30d", _=Depends(require_admin)):
    aid = account_id.removeprefix("act_")
    if not aid.isdigit() or date_preset not in {"today", "yesterday", "last_7d", "last_30d", "last_90d"}:
        raise HTTPException(400, "invalid account_id or date_preset")
    return await graph_get(f"act_{aid}/insights", {
        "fields": "campaign_id,campaign_name,impressions,reach,clicks,spend,ctr,cpm,actions,date_start,date_stop",
        "date_preset": date_preset, "level": "campaign", "limit": 100})
