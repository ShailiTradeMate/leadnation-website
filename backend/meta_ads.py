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


# ---------------- Marketing-panel summary + expiry reminder ----------------
PRESETS = {"last_7d": "last_7d", "last_30d": "last_30d", "last_90d": "last_90d"}


async def panel(date_preset: str = "last_30d") -> dict:
    """Everything the Admin → Marketing Meta panel needs in one call (fails soft per section)."""
    if not all(os.environ.get(k) for k in ("META_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET")):
        return {"configured": False}
    out = {"configured": True, "errors": {}}
    tok = await _token()
    try:
        out["token"] = await token_info(tok)
        exp = out["token"]["expiresAt"]
        out["token"]["daysLeft"] = (round((datetime.fromisoformat(exp) - datetime.now(timezone.utc)).total_seconds() / 86400, 1)
                                    if exp != "never" else None)
        stored = await db.secrets_store.find_one({"_id": TOKEN_DOC}, {"token": 0})
        out["usingLongLived"] = bool(stored and datetime.fromisoformat(stored["expiresAt"]) > datetime.now(timezone.utc))
    except HTTPException as exc:
        out["errors"]["token"] = exc.detail
        return out
    try:
        accts = (await graph_get("me/adaccounts", {"fields": "id,account_id,name,account_status,currency,business", "limit": 50}, token=tok)).get("data", [])
        biz = [a for a in accts if (a.get("business") or {}).get("id")] or accts
        out["adAccounts"] = [{**a, "statusLabel": STATUS.get(a.get("account_status"), str(a.get("account_status")))} for a in accts]
        primary = biz[0] if biz else None
        out["primary"] = primary
        if primary:
            aid = primary["account_id"]
            det = await graph_get(f"act_{aid}", {"fields": "amount_spent,balance,spend_cap,currency"}, token=tok)
            out["primary"] = {**out["primary"], **det, "statusLabel": STATUS.get(primary.get("account_status"), "")}
            out["campaigns"] = (await graph_get(f"act_{aid}/campaigns", {"fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget", "limit": 50}, token=tok)).get("data", [])
            out["insights"] = (await graph_get(f"act_{aid}/insights", {
                "fields": "campaign_name,impressions,reach,clicks,spend,ctr,cpm,actions",
                "date_preset": PRESETS.get(date_preset, "last_30d"), "level": "campaign", "limit": 100}, token=tok)).get("data", [])
    except HTTPException as exc:
        out["errors"]["account"] = exc.detail
    return out


@router.get("/panel")
async def panel_route(range: str = "last_30d", _=Depends(require_admin)):
    return await panel(range)


REMIND_DAYS = (7, 3, 1)


async def check_token_expiry(run_id: str = "") -> dict:
    """Daily cron body: email ADMIN_EMAIL once per threshold (7 / 3 / 1 days) before expiry, and when expired."""
    import emailer
    if not all(os.environ.get(k) for k in ("META_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET")):
        return {"ok": False, "skipped": "meta not configured"}
    tok = await _token()
    try:
        info = await token_info(tok)
    except HTTPException as exc:
        info = {"valid": False, "expiresAt": "unknown", "error": exc.detail}
    now = datetime.now(timezone.utc)
    if info.get("valid") and info.get("expiresAt") not in ("never", "unknown"):
        days_left = (datetime.fromisoformat(info["expiresAt"]) - now).total_seconds() / 86400
        due = next((d for d in REMIND_DAYS if days_left <= d), None)
        stage = f"d{due}" if due is not None else None
    else:
        days_left, stage = 0, "expired"
    rec = {"checkedAt": now.isoformat(), "daysLeft": round(days_left, 1), "expiresAt": info.get("expiresAt"),
           "valid": info.get("valid"), "stage": stage, "runId": run_id}
    if stage is None:
        await db.meta_token_checks.replace_one({"_id": "latest"}, {"_id": "latest", **rec, "sent": False}, upsert=True)
        return {"ok": True, **rec, "sent": False}
    already = await db.meta_token_checks.find_one({"_id": f"sent:{info.get('expiresAt')}:{stage}"})
    if already:
        await db.meta_token_checks.replace_one({"_id": "latest"}, {"_id": "latest", **rec, "sent": False, "dedup": True}, upsert=True)
        return {"ok": True, **rec, "sent": False, "dedup": True}
    accts = []
    try:
        accts = (await graph_get("me/adaccounts", {"fields": "name,business", "limit": 10}, token=tok)).get("data", [])
    except HTTPException:
        pass
    biz = [a["name"] for a in accts if (a.get("business") or {}).get("id")]
    ctx = {"daysLeft": max(0, int(days_left)) if stage != "expired" else 0,
           "expiresAt": (info.get("expiresAt") or "")[:16].replace("T", " ") + " UTC" if stage != "expired" else "already expired",
           "type": info.get("type", "USER"), "dataAccessExpiresAt": (info.get("dataAccessExpiresAt") or "")[:10],
           "adAccount": ", ".join(biz) or "Vametra AI Advertising"}
    res = await emailer.notify_admin("meta_token_expiry", ctx)
    await db.meta_token_checks.insert_one({"_id": f"sent:{info.get('expiresAt')}:{stage}", **rec, "email": res})
    await db.meta_token_checks.replace_one({"_id": "latest"}, {"_id": "latest", **rec, "sent": bool(res.get("sent")), "email": res}, upsert=True)
    return {"ok": True, **rec, "sent": bool(res.get("sent")), "email": res}


@router.get("/token-check")
async def token_check_status(_=Depends(require_admin)):
    latest = await db.meta_token_checks.find_one({"_id": "latest"})
    return latest or {"checkedAt": None}


@router.post("/token-check/run")
async def token_check_run(_=Depends(require_admin)):
    return await check_token_expiry("manual")
