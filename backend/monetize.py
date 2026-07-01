"""Monetization + Account for the LeadNation website.

Paywall: building quotes is free; the FIRST PDF download is free, after that each
download costs ₹25 (India) / $1 (international) — or an active monthly pass gives
unlimited downloads. Payments via Stripe now (Razorpay slot ready for later).

Account: Instagram-style profile page data — profile (uid/name/email/mobile/role/
country from the shared DO backend, overridable locally), downloads history, saved
buyers, GST-style invoices, referral link, subscription. Admin can view any user.

Owner = Firebase UID (signed-in) or anonymous Trade-Session UUID (guest) — same
model as projects.py, so it is testable in preview without login.
"""
import os
import uuid
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from core import db, require_admin
from fastapi import Depends
from projects import _owner
from firebase_auth import _bearer, verify_token
from pricing import resolve as pricing_resolve, gateway_for, get_config as pricing_config_doc
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

pay_router = APIRouter(prefix="/payments")
dl_router = APIRouter(prefix="/downloads")
acc_router = APIRouter(prefix="/account")
hook_router = APIRouter()

TX = db.payment_transactions
DL = db.downloads
SUB = db.subscriptions
BUYERS = db.saved_buyers
PREFS = db.user_prefs

STRIPE_KEY = os.environ.get("STRIPE_API_KEY")
DO_API_BASE = os.environ.get("DO_API_BASE", "https://leadnation-lfrhs.ondigitalocean.app/api")

# All prices are owned by the centralized Pricing Engine (pricing.py) — never hardcoded here.
RAZORPAY_ENABLED = bool(os.environ.get("RAZORPAY_KEY_ID"))

SUB_DAYS = {"monthly": 30, "subscription": 30, "annual": 365}


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _region(r: Optional[str]) -> str:
    return "IN" if (r or "").upper() == "IN" else "INTL"


# ---------------- Payments (Stripe) ----------------
class CheckoutIn(BaseModel):
    kind: str = "download"      # download | monthly | annual | subscription(=monthly)
    region: str = "INTL"        # IN | INTL (selects a FIXED package, not the price)
    projectId: str = ""
    origin: str


@pay_router.post("/checkout")
async def create_checkout(body: CheckoutIn, request: Request,
                          authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    if body.kind not in ("download", "monthly", "annual", "subscription"):
        raise HTTPException(400, "Invalid package")
    owner, otype = _owner(authorization, x_trade_session)
    region = _region(body.region)
    amount, currency = await pricing_resolve(body.kind, region)  # server-side price from engine
    is_sub = body.kind in ("monthly", "annual", "subscription")

    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=webhook_url)
    origin = body.origin.rstrip("/")
    pid = body.projectId or ""
    success_url = f"{origin}/account?tab={'billing' if is_sub else 'downloads'}&session_id={{CHECKOUT_SESSION_ID}}&pid={pid}"
    cancel_url = f"{origin}/command-center"
    meta = {"owner": owner, "kind": body.kind, "region": region, "projectId": body.projectId or ""}
    session = await stripe.create_checkout_session(CheckoutSessionRequest(
        amount=float(amount), currency=currency, success_url=success_url, cancel_url=cancel_url, metadata=meta))

    await TX.insert_one({
        "_id": session.session_id, "sessionId": session.session_id, "owner": owner, "ownerType": otype,
        "kind": body.kind, "amount": amount, "currency": currency, "region": region,
        "projectId": body.projectId or "", "status": "initiated", "paymentStatus": "pending",
        "consumed": False, "createdAt": _iso(_now()), "updatedAt": _iso(_now())})
    return {"url": session.url, "sessionId": session.session_id, "amount": amount, "currency": currency}


async def _sync_status(session_id: str):
    tx = await TX.find_one({"_id": session_id})
    if not tx:
        raise HTTPException(404, "Transaction not found")
    if tx["status"] == "paid":
        return tx
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url="")
    st = await stripe.get_checkout_status(session_id)
    new_status = "paid" if st.payment_status == "paid" else ("expired" if st.status == "expired" else "initiated")
    if new_status != tx["status"]:
        await TX.update_one({"_id": session_id}, {"$set": {"status": new_status, "paymentStatus": st.payment_status, "updatedAt": _iso(_now())}})
        if new_status == "paid" and tx["kind"] in SUB_DAYS:
            until = _now() + timedelta(days=SUB_DAYS[tx["kind"]])
            await SUB.update_one({"owner": tx["owner"]}, {"$set": {"owner": tx["owner"], "status": "active", "plan": tx["kind"], "until": _iso(until), "updatedAt": _iso(_now())}}, upsert=True)
        tx = await TX.find_one({"_id": session_id})
    return tx


@pay_router.get("/status/{session_id}")
async def checkout_status(session_id: str):
    tx = await _sync_status(session_id)
    return {"status": tx["status"], "paymentStatus": tx.get("paymentStatus"), "kind": tx["kind"],
            "amount": tx["amount"], "currency": tx["currency"], "projectId": tx.get("projectId")}


@pay_router.get("/pricing")
async def pricing(region: str = "INTL"):
    r = _region(region)
    d_amt, d_cur = await pricing_resolve("download", r)
    s_amt, s_cur = await pricing_resolve("monthly", r)
    a_amt, a_cur = await pricing_resolve("annual", r)
    return {"region": r, "download": {"amount": d_amt, "currency": d_cur},
            "subscription": {"amount": s_amt, "currency": s_cur},
            "monthly": {"amount": s_amt, "currency": s_cur},
            "annual": {"amount": a_amt, "currency": a_cur},
            "razorpayEnabled": RAZORPAY_ENABLED, "gateway": await gateway_for(r)}


@hook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    try:
        body = await request.body()
        stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url="")
        res = await stripe.handle_webhook(body, request.headers.get("Stripe-Signature"))
        if res.session_id:
            await _sync_status(res.session_id)
    except Exception as exc:
        logging.warning("Stripe webhook: %s", exc)
    return {"ok": True}


# ---------------- Downloads / entitlements ----------------
async def _has_subscription(owner: str) -> bool:
    s = await SUB.find_one({"owner": owner, "status": "active"})
    if not s:
        return False
    try:
        return datetime.fromisoformat(s["until"]) > _now()
    except Exception:
        return False


@dl_router.get("/check")
async def download_check(projectId: str = "", region: str = "INTL",
                         authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    total = await DL.count_documents({"owner": owner})
    cfg = await pricing_config_doc()
    free_enabled = cfg.get("settings", {}).get("freeFirstDownload", True)
    free_available = free_enabled and total == 0
    sub = await _has_subscription(owner)
    r = _region(region)
    amount, currency = await pricing_resolve("download", r)
    return {"allowed": bool(free_available or sub), "freeAvailable": free_available,
            "hasSubscription": sub, "totalDownloads": total,
            "price": amount, "currency": currency, "region": r}


class RecordIn(BaseModel):
    projectId: str
    projectTitle: str = ""
    sessionId: str = ""
    region: str = "INTL"


@dl_router.post("/record")
async def download_record(body: RecordIn, authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    total = await DL.count_documents({"owner": owner})
    cfg = await pricing_config_doc()
    free_enabled = cfg.get("settings", {}).get("freeFirstDownload", True)
    free_available = free_enabled and total == 0
    sub = await _has_subscription(owner)
    paid = False
    amount = 0.0
    currency = _region(body.region).lower()
    invoice = None

    if not (free_available or sub):
        # must present a paid, unconsumed download transaction
        if not body.sessionId:
            raise HTTPException(402, "Payment required")
        tx = await _sync_status(body.sessionId)
        if tx["owner"] != owner or tx["kind"] != "download" or tx["status"] != "paid" or tx.get("consumed"):
            raise HTTPException(402, "Payment not valid for this download")
        await TX.update_one({"_id": body.sessionId}, {"$set": {"consumed": True, "updatedAt": _iso(_now())}})
        paid = True; amount = tx["amount"]; currency = tx["currency"]

    did = uuid.uuid4().hex
    if paid:
        invoice = await _make_invoice(owner, amount, currency, body.projectTitle or body.projectId)
    await DL.insert_one({
        "_id": did, "id": did, "owner": owner, "projectId": body.projectId,
        "projectTitle": body.projectTitle, "paid": paid, "free": free_available and not paid,
        "amount": amount, "currency": currency, "invoiceId": (invoice or {}).get("id"),
        "at": _iso(_now())})
    return {"ok": True, "downloadId": did, "paid": paid, "free": free_available and not paid,
            "invoice": invoice}


async def _make_invoice(owner, amount, currency, item):
    seq = await DL.count_documents({"owner": owner, "paid": True}) + 1
    num = f"LN-{datetime.now().strftime('%Y%m')}-{owner[:6].upper()}-{seq:04d}"
    gst = round(amount - amount / 1.18, 2) if currency == "inr" else 0.0
    return {"id": uuid.uuid4().hex, "number": num, "date": _iso(_now()),
            "amount": amount, "currency": currency, "gst": gst,
            "item": f"Trade Intelligence Report — {item}", "seller": "LeadNation"}


# ---------------- Account ----------------
async def _profile(owner: str, otype: str, token: Optional[str]):
    prof = {"uid": owner if otype == "uid" else None, "name": "", "email": "", "mobile": "",
            "role": "", "country": "", "guest": otype != "uid"}
    claims = verify_token(token) if token else None
    if claims:
        prof["uid"] = claims.get("uid", owner)
        prof["email"] = claims.get("email", "")
        prof["name"] = claims.get("name", "")
        prof["mobile"] = claims.get("phone_number", "")
        # best-effort DO profile enrichment
        try:
            async with httpx.AsyncClient(timeout=6) as c:
                r = await c.get(f"{DO_API_BASE}/v1/profiles/{prof['uid']}", headers={"Authorization": f"Bearer {token}"})
                if r.status_code == 200:
                    d = r.json() or {}
                    prof["role"] = d.get("role") or d.get("user_type") or prof["role"]
                    prof["country"] = d.get("country") or prof["country"]
                    prof["mobile"] = d.get("phone") or d.get("mobile") or prof["mobile"]
                    prof["name"] = d.get("name") or d.get("display_name") or prof["name"]
                    prof["customerId"] = d.get("customer_id") or d.get("customerId")
        except Exception as exc:
            logging.info("DO profile fetch skipped: %s", exc)
    # local overrides
    ov = await PREFS.find_one({"owner": owner})
    if ov:
        for k in ("role", "country", "mobile", "name"):
            if ov.get(k):
                prof[k] = ov[k]
    return prof


def _referral(owner: str):
    code = "LN" + hashlib.sha1(owner.encode()).hexdigest()[:7].upper()
    return {"code": code, "link": f"https://leadnation.app/?ref={code}"}


@acc_router.get("/me")
async def account_me(request: Request, authorization: Optional[str] = Header(default=None),
                     x_trade_session: Optional[str] = Header(default=None)):
    owner, otype = _owner(authorization, x_trade_session)
    token = _bearer(authorization)
    prof = await _profile(owner, otype, token)
    projects_n = await db.trade_projects.count_documents({"owner": owner})
    dls = await DL.find({"owner": owner}).sort("at", -1).to_list(100)
    spend = round(sum(d.get("amount", 0) for d in dls if d.get("paid")), 2)
    sub = await SUB.find_one({"owner": owner, "status": "active"})
    return {
        "profile": prof,
        "stats": {"projects": projects_n, "downloads": len(dls), "spend": spend},
        "downloads": [{k: v for k, v in d.items() if k != "_id"} for d in dls],
        "subscription": {"active": await _has_subscription(owner), "until": (sub or {}).get("until")},
        "referral": _referral(owner),
    }


class ProfilePatch(BaseModel):
    role: Optional[str] = None
    country: Optional[str] = None
    mobile: Optional[str] = None
    name: Optional[str] = None


@acc_router.put("/profile")
async def update_profile(body: ProfilePatch, authorization: Optional[str] = Header(default=None),
                         x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if patch:
        patch["owner"] = owner; patch["updatedAt"] = _iso(_now())
        await PREFS.update_one({"owner": owner}, {"$set": patch}, upsert=True)
    return {"ok": True, "profile": await _profile(owner, "uid" if _bearer(authorization) else "guest", _bearer(authorization))}


@acc_router.get("/invoices")
async def invoices(authorization: Optional[str] = Header(default=None),
                   x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    dls = await DL.find({"owner": owner, "paid": True}).sort("at", -1).to_list(100)
    inv = []
    for d in dls:
        inv.append({"number": d.get("invoiceId"), "date": d.get("at"), "amount": d.get("amount"),
                    "currency": d.get("currency"), "item": f"Trade Intelligence Report — {d.get('projectTitle') or d.get('projectId')}"})
    return {"invoices": inv}


class BuyerIn(BaseModel):
    name: str
    country: str = ""
    product: str = ""
    contact: str = ""
    notes: str = ""


@acc_router.get("/buyers")
async def list_buyers(authorization: Optional[str] = Header(default=None),
                      x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    docs = await BUYERS.find({"owner": owner}).sort("createdAt", -1).to_list(200)
    return {"buyers": [{k: v for k, v in d.items() if k != "_id"} for d in docs]}


@acc_router.post("/buyers")
async def add_buyer(body: BuyerIn, authorization: Optional[str] = Header(default=None),
                    x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    bid = uuid.uuid4().hex
    doc = {"_id": bid, "id": bid, "owner": owner, **body.model_dump(), "createdAt": _iso(_now())}
    await BUYERS.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@acc_router.delete("/buyers/{bid}")
async def del_buyer(bid: str, authorization: Optional[str] = Header(default=None),
                    x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    res = await BUYERS.delete_one({"_id": bid, "owner": owner})
    return {"ok": res.deleted_count > 0}


# ---------------- Admin ----------------
@acc_router.get("/admin/users")
async def admin_users(_: dict = Depends(require_admin)):
    pipeline = [{"$group": {"_id": "$owner", "downloads": {"$sum": 1},
                            "spend": {"$sum": {"$cond": ["$paid", "$amount", 0]}}}},
                {"$sort": {"downloads": -1}}, {"$limit": 200}]
    rows = await DL.aggregate(pipeline).to_list(200)
    out = []
    for r in rows:
        proj = await db.trade_projects.count_documents({"owner": r["_id"]})
        pref = await PREFS.find_one({"owner": r["_id"]})
        out.append({"owner": r["_id"], "downloads": r["downloads"], "spend": round(r["spend"], 2),
                    "projects": proj, "role": (pref or {}).get("role"), "country": (pref or {}).get("country")})
    total_rev = round(sum(o["spend"] for o in out), 2)
    return {"users": out, "totalRevenue": total_rev, "totalUsers": len(out)}


@acc_router.get("/admin/{owner}")
async def admin_user(owner: str, _: dict = Depends(require_admin)):
    dls = await DL.find({"owner": owner}).sort("at", -1).to_list(100)
    proj = await db.trade_projects.find({"owner": owner}).sort("updatedAt", -1).to_list(100)
    pref = await PREFS.find_one({"owner": owner})
    return {"owner": owner, "prefs": {k: v for k, v in (pref or {}).items() if k != "_id"},
            "downloads": [{k: v for k, v in d.items() if k != "_id"} for d in dls],
            "projects": [{"id": p["id"], "title": p.get("title"), "stage": p.get("stage")} for p in proj],
            "spend": round(sum(d.get("amount", 0) for d in dls if d.get("paid")), 2)}
