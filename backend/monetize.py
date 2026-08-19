"""Monetization + Account for the Vametra AI website.

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
    email: str = ""             # optional: enables payment/receipt emails
    name: str = ""


@pay_router.post("/checkout")
async def create_checkout(body: CheckoutIn, request: Request,
                          authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    if body.kind not in ("download", "monthly", "annual", "subscription"):
        raise HTTPException(400, "Invalid package")
    owner, otype = _owner(authorization, x_trade_session)
    region = _region(body.region)
    amount, currency = await pricing_resolve(body.kind, region)  # server-side price from engine
    _prof = await _profile(owner, otype, _bearer_token(authorization))
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
        "gateway": "stripe", "uid": _prof.get("uid"), "customerId": _prof.get("customerId", ""),
        "mobile": _prof.get("mobile", ""), "country": _prof.get("country") or ("International" if region == "INTL" else region),
        "kind": body.kind, "amount": amount, "currency": currency, "region": region,
        "projectId": body.projectId or "", "status": "initiated", "paymentStatus": "pending",
        "email": (body.email or _prof.get("email") or "").strip(), "name": body.name or _prof.get("name", ""),
        "consumed": False, "granted": False, "createdAt": _iso(_now()), "updatedAt": _iso(_now())})
    return {"url": session.url, "sessionId": session.session_id, "amount": amount, "currency": currency}


async def _sync_status(session_id: str):
    tx = await TX.find_one({"_id": session_id})
    if not tx:
        raise HTTPException(404, "Transaction not found")
    if tx["status"] == "paid":
        return tx
    if tx.get("gateway") == "razorpay":
        # Razorpay status is maintained by /razorpay/verify + the webhook, not Stripe.
        return tx
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url="")
    st = await stripe.get_checkout_status(session_id)
    new_status = "paid" if st.payment_status == "paid" else ("expired" if st.status == "expired" else "initiated")
    if new_status != tx["status"]:
        await TX.update_one({"_id": session_id}, {"$set": {"status": new_status, "paymentStatus": st.payment_status, "updatedAt": _iso(_now())}})
        if new_status == "paid":
            await _finalize_paid(session_id, {"method": "card"})
        elif new_status == "expired" and tx.get("email"):
            from emailer import send
            await send("payment_failed", tx["email"], {"name": tx.get("name"), "item": tx.get("kind", "purchase")})
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


# ---------------- Payments (Razorpay — IN region) ----------------
# Razorpay is used ONLY for subscription/report/download/event checkout (never for
# professional services like GST/IEC — those are enquiry-based and have separate keys).
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip()
_rzp_client = None


def _razorpay():
    """Lazily build the Razorpay client. Raises 503 until keys are configured."""
    global _rzp_client
    if not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
        raise HTTPException(503, "Razorpay is not configured yet")
    if _rzp_client is None:
        import razorpay
        _rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    return _rzp_client


_PLAN_LABEL = {"monthly": "Monthly Pro", "annual": "Annual Pro",
               "subscription": "Pro Subscription", "download": "Report Download"}
_PERIOD = {"monthly": "1 month (30 days)", "annual": "12 months (365 days)",
           "subscription": "30 days", "download": "One-time"}
_COUNTRY = {"IN": "India", "INTL": "International"}
_BENEFITS = [
    "Unlimited Trade Command Center report downloads (PDF)",
    "Full access to Verified Buyer Intelligence (VBIE) — verified importers & buyers",
    "Landed-cost, HS-code and trade-corridor calculators",
    "Live trade news, expo & events intelligence",
    "Priority updates as new verified buyers are added",
]


def _bearer_token(authorization):
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


async def _finalize_paid(tx_id: str, pay_meta: dict = None):
    """Single idempotent finalizer for BOTH gateways (Razorpay=IN, Stripe=INTL). Atomically
    claims the TX, activates a time-boxed subscription (sub kinds), records the payment for
    the admin CMS, and sends TWO emails: a detailed receipt to the user + an alert to admin."""
    pay_meta = pay_meta or {}
    claim = await TX.update_one(
        {"_id": tx_id, "granted": {"$ne": True}},
        {"$set": {"status": "paid", "paymentStatus": "captured", "granted": True,
                  "paidAt": _iso(_now()), "updatedAt": _iso(_now())}})
    if claim.modified_count != 1:
        return  # already finalized by a prior /verify or webhook delivery — no double action
    tx = await TX.find_one({"_id": tx_id})
    from emailer import send, notify_admin, _amount_label

    gateway = tx.get("gateway", "stripe")
    email = (tx.get("email") or pay_meta.get("email") or "").strip()
    mobile = tx.get("mobile") or pay_meta.get("contact") or ""
    country = tx.get("country") or _COUNTRY.get(tx.get("region"), tx.get("region", ""))
    method = (pay_meta.get("method") or tx.get("method") or ("card" if gateway == "stripe" else "")).strip()
    txn_id = pay_meta.get("payment_id") or tx.get("razorpay_payment_id") or tx.get("_id")
    plan_label = _PLAN_LABEL.get(tx["kind"], tx["kind"])
    amount_label = _amount_label(tx["amount"], tx["currency"])
    until_iso = ""
    if tx["kind"] in SUB_DAYS:
        until = _now() + timedelta(days=SUB_DAYS[tx["kind"]])
        until_iso = _iso(until)
        await SUB.update_one({"owner": tx["owner"]},
                             {"$set": {"owner": tx["owner"], "status": "active", "plan": tx["kind"],
                                       "until": until_iso, "gateway": gateway, "updatedAt": _iso(_now())}},
                             upsert=True)
    inv = await _make_invoice(tx["owner"], tx["amount"], tx["currency"], plan_label)

    # Persist enriched payment record for the admin CMS payments table.
    await TX.update_one({"_id": tx_id}, {"$set": {
        "txnId": txn_id, "method": method, "mobile": mobile, "country": country,
        "email": email, "invoice": inv.get("number", ""), "planLabel": plan_label,
        "subUntil": until_iso}})

    # 1) User receipt (subscription kinds).
    if tx["kind"] in SUB_DAYS and email:
        await send("subscription_success", email, {
            "name": tx.get("name") or "there", "plan": plan_label, "period": _PERIOD.get(tx["kind"], ""),
            "until": until_iso, "amountLabel": amount_label, "method": method, "txnId": txn_id,
            "invoice": inv.get("number", ""), "userId": tx.get("uid") or tx["owner"],
            "customerId": tx.get("customerId", ""), "email": email, "benefits": _BENEFITS})
    # 2) Admin alert (all paid transactions).
    await notify_admin("admin_payment_alert", {
        "plan": plan_label, "amountLabel": amount_label, "gateway": gateway, "method": method,
        "name": tx.get("name") or "", "email": email, "mobile": mobile, "country": country,
        "region": tx.get("region", ""), "userId": tx.get("uid") or tx["owner"],
        "customerId": tx.get("customerId", ""), "txnId": txn_id, "invoice": inv.get("number", ""),
        "until": until_iso, "kind": tx["kind"]})


@pay_router.post("/razorpay/order")
async def razorpay_create_order(body: CheckoutIn, request: Request,
                                authorization: Optional[str] = Header(default=None),
                                x_trade_session: Optional[str] = Header(default=None)):
    if body.kind not in ("download", "monthly", "annual", "subscription"):
        raise HTTPException(400, "Invalid package")
    client = _razorpay()
    owner, otype = _owner(authorization, x_trade_session)
    region = _region(body.region)
    amount, currency = await pricing_resolve(body.kind, region)   # server-side price (never trust client)
    paise = int(round(float(amount) * 100))
    if paise <= 0:
        raise HTTPException(400, "Invalid price")
    receipt = f"ln_{uuid.uuid4().hex[:28]}"
    order = client.order.create(data={
        "amount": paise, "currency": currency.upper(), "receipt": receipt,
        "notes": {"owner": owner, "kind": body.kind, "region": region,
                  "projectId": body.projectId or ""}})
    prof = await _profile(owner, otype, _bearer_token(authorization))
    email = (body.email or prof.get("email") or "").strip()
    await TX.insert_one({
        "_id": order["id"], "sessionId": order["id"], "gateway": "razorpay",
        "razorpay_order_id": order["id"], "owner": owner, "ownerType": otype,
        "uid": prof.get("uid"), "customerId": prof.get("customerId", ""),
        "mobile": prof.get("mobile", ""), "country": prof.get("country") or _COUNTRY.get(region, region),
        "kind": body.kind, "amount": amount, "currency": currency, "region": region,
        "projectId": body.projectId or "", "status": "initiated", "paymentStatus": "created",
        "email": email, "name": body.name or prof.get("name", ""),
        "consumed": False, "granted": False, "createdAt": _iso(_now()), "updatedAt": _iso(_now())})
    return {"gateway": "razorpay", "key_id": RAZORPAY_KEY_ID, "order_id": order["id"],
            "amount": paise, "currency": currency.upper(), "sessionId": order["id"],
            "name": "Vametra AI", "description": f"{body.kind} — Vametra AI",
            "prefill": {"name": body.name or prof.get("name", ""), "email": email,
                        "contact": prof.get("mobile", "")}}


class RazorpayVerifyIn(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


@pay_router.post("/razorpay/verify")
async def razorpay_verify(body: RazorpayVerifyIn,
                          authorization: Optional[str] = Header(default=None),
                          x_trade_session: Optional[str] = Header(default=None)):
    client = _razorpay()
    tx = await TX.find_one({"_id": body.razorpay_order_id, "gateway": "razorpay"})
    if not tx:
        raise HTTPException(404, "Unknown order")
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": tx["razorpay_order_id"],   # from DB, never the browser
            "razorpay_payment_id": body.razorpay_payment_id,
            "razorpay_signature": body.razorpay_signature})
    except Exception:
        raise HTTPException(400, "Invalid payment signature")
    # Signature proves authenticity; confirm the payment is actually captured.
    try:
        pay = client.payment.fetch(body.razorpay_payment_id)
    except Exception:
        pay = {}
    if pay.get("order_id") and pay.get("order_id") != tx["razorpay_order_id"]:
        raise HTTPException(400, "Payment/order mismatch")
    await TX.update_one({"_id": tx["_id"]}, {"$set": {"razorpay_payment_id": body.razorpay_payment_id,
                                                       "updatedAt": _iso(_now())}})
    if pay.get("status") == "captured":
        await _finalize_paid(tx["_id"], {"payment_id": body.razorpay_payment_id,
                                         "method": pay.get("method"), "email": pay.get("email"),
                                         "contact": pay.get("contact")})
        return {"ok": True, "status": "paid", "kind": tx["kind"], "sessionId": tx["_id"]}
    return {"ok": True, "status": pay.get("status", "pending"), "kind": tx["kind"], "sessionId": tx["_id"]}


@hook_router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not (RAZORPAY_KEY_ID and RAZORPAY_WEBHOOK_SECRET):
        return {"ok": True}
    try:
        _razorpay().utility.verify_webhook_signature(raw.decode("utf-8"), signature, RAZORPAY_WEBHOOK_SECRET)
    except HTTPException:
        raise
    except Exception as exc:
        logging.warning("Razorpay webhook signature invalid: %s", exc)
        raise HTTPException(400, "invalid webhook signature")
    try:
        import json as _json
        event = _json.loads(raw)
        etype = event.get("event")
        if etype in ("order.paid", "payment.captured"):
            ent = (event.get("payload", {}).get("payment", {}) or {}).get("entity", {}) or {}
            order_id = ent.get("order_id")
            if order_id and ent.get("status") == "captured":
                tx = await TX.find_one({"_id": order_id, "gateway": "razorpay"})
                if tx:
                    await _finalize_paid(order_id, {"payment_id": ent.get("id"),
                                                    "method": ent.get("method"),
                                                    "email": ent.get("email"),
                                                    "contact": ent.get("contact")})
    except Exception as exc:
        logging.warning("Razorpay webhook processing: %s", exc)
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
    email: str = ""
    name: str = ""


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
    if body.email:
        from emailer import send
        await send("report_generated", body.email, {
            "name": body.name, "reportTitle": body.projectTitle or body.projectId,
            "invoice": (invoice or {}).get("number", "")})
    return {"ok": True, "downloadId": did, "paid": paid, "free": free_available and not paid,
            "invoice": invoice}


async def _make_invoice(owner, amount, currency, item):
    seq = await DL.count_documents({"owner": owner, "paid": True}) + 1
    num = f"LN-{datetime.now().strftime('%Y%m')}-{owner[:6].upper()}-{seq:04d}"
    gst = round(amount - amount / 1.18, 2) if currency == "inr" else 0.0
    return {"id": uuid.uuid4().hex, "number": num, "date": _iso(_now()),
            "amount": amount, "currency": currency, "gst": gst,
            "item": f"Trade Intelligence Report — {item}", "seller": "Vametra AI"}


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
    return {"code": code, "link": f"https://vametra.com/?ref={code}"}


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



@pay_router.get("/admin/transactions")
async def admin_transactions(_: dict = Depends(require_admin), limit: int = 200,
                             status: Optional[str] = None, gateway: Optional[str] = None):
    """Admin CMS payments log — every payment with full user + payment detail + transaction id."""
    q = {}
    if status:
        q["status"] = status
    if gateway:
        q["gateway"] = gateway
    rows = await TX.find(q).sort("createdAt", -1).limit(min(int(limit), 500)).to_list(500)
    out = []
    for t in rows:
        out.append({
            "id": t["_id"], "txnId": t.get("txnId") or t.get("razorpay_payment_id") or t["_id"],
            "gateway": t.get("gateway", "stripe"), "method": t.get("method", ""),
            "status": t.get("status"), "kind": t.get("kind"), "plan": t.get("planLabel") or t.get("kind"),
            "amount": t.get("amount"), "currency": t.get("currency"),
            "name": t.get("name", ""), "email": t.get("email", ""), "mobile": t.get("mobile", ""),
            "country": t.get("country", ""), "region": t.get("region", ""),
            "userId": t.get("uid") or t.get("owner"), "customerId": t.get("customerId", ""),
            "invoice": t.get("invoice", ""), "subUntil": t.get("subUntil", ""),
            "createdAt": t.get("createdAt"), "paidAt": t.get("paidAt", "")})
    paid = [t for t in out if t["status"] == "paid"]
    rev_inr = round(sum(t["amount"] or 0 for t in paid if str(t["currency"]).lower() == "inr"), 2)
    rev_usd = round(sum(t["amount"] or 0 for t in paid if str(t["currency"]).lower() != "inr"), 2)
    return {"transactions": out, "count": len(out), "paidCount": len(paid),
            "revenueINR": rev_inr, "revenueUSD": rev_usd}
