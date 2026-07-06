"""Expo & Global Events Engine — admin-curated + user-submitted + admin-approved.

Permanent, app-shared architecture. Collections:
  * events            — canonical event records (all lifecycle statuses)
  * event_submissions — audit log of user submission actions
  * event_payments    — listing payment records (Stripe INTL / Razorpay IN)

Only APPROVED + PUBLISHED (and unexpired) events are shown publicly on the website
AND the mobile app (same endpoints). Pricing is owned by the Pricing Engine
(pricing.py -> eventPricing), never hardcoded. Emails fire at every lifecycle step.
"""
import os
import uuid
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Header, Query, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core import db, require_admin
from firebase_auth import optional_user
from pricing import get_event_pricing, set_event_pricing, region_of
from emailer import send_event_email, notify_admin
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

router = APIRouter(prefix="/events")

EVENTS = db.expo_listings
SUBS = db.event_submissions
PAY = db.event_payments

STRIPE_KEY = os.environ.get("STRIPE_API_KEY")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

CATEGORIES = ["Import/Export", "Trade Fair", "Business", "Agriculture", "Manufacturing",
              "Logistics", "Customs", "Government", "Technology", "Finance"]
INDUSTRIES = ["Agriculture & Food", "Textiles & Apparel", "Pharmaceuticals", "Engineering Goods",
              "Chemicals", "FMCG", "Handicrafts", "Electronics", "Automotive", "Gems & Jewellery",
              "Logistics", "Multi-sector"]
AUDIENCES = ["Exporters", "Importers", "Manufacturers", "Buyers", "Distributors",
             "Investors", "Government", "Startups", "All"]

PUBLIC_STATUSES = {"published", "approved"}


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _owner(claims, session):
    if claims:
        return claims.get("uid"), "uid"
    return (f"guest-{session}" if session else f"guest-{uuid.uuid4().hex[:8]}"), "guest"


def _clean(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in doc.items() if k != "_id"}
    d["id"] = doc.get("_id") or doc.get("id")
    return d


def _is_expired(doc) -> bool:
    exp = doc.get("expiresAt")
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp) < _now()
    except Exception:
        return False


# ---------------- Filters / config ----------------
@router.get("/filters")
async def event_filters():
    countries = await EVENTS.distinct("country", {"status": {"$in": list(PUBLIC_STATUSES)}})
    return {"categories": CATEGORIES, "industries": INDUSTRIES, "audiences": AUDIENCES,
            "countries": sorted([c for c in countries if c]) or ["India", "UAE", "USA", "Germany", "Singapore"]}


@router.get("/pricing")
async def event_pricing(region: str = Query("INTL"), country: str = Query("")):
    r = region_of(country) if country else ("IN" if region.upper() == "IN" else "INTL")
    cfg = await get_event_pricing()
    amount = float(cfg[r]["amount"])
    currency = cfg[r]["currency"]
    gateway = "razorpay" if (r == "IN" and RAZORPAY_ENABLED) else "stripe"
    return {"region": r, "amount": amount, "currency": currency,
            "durationDays": cfg.get("durationDays", 30), "gateway": gateway,
            "razorpayEnabled": RAZORPAY_ENABLED,
            "symbol": "\u20b9" if currency == "inr" else "$"}


# ---------------- Public list + detail ----------------
@router.get("/list")
async def list_events(category: str = Query(""), country: str = Query(""),
                      industry: str = Query(""), audience: str = Query(""),
                      q: str = Query(""), limit: int = Query(60)):
    query: Dict[str, Any] = {"status": {"$in": list(PUBLIC_STATUSES)}}
    if category:
        query["category"] = category
    if country:
        query["country"] = country
    if industry:
        query["industry"] = industry
    if audience:
        query["audience"] = audience
    if q:
        query["$or"] = [{"name": {"$regex": q, "$options": "i"}},
                        {"description": {"$regex": q, "$options": "i"}},
                        {"city": {"$regex": q, "$options": "i"}}]
    docs = await EVENTS.find(query).sort([("featured", -1), ("startDate", 1)]).to_list(min(limit, 100))
    items = [_clean(d) for d in docs if not _is_expired(d)]
    return {"items": items, "count": len(items)}


@router.get("/mine")
async def my_events(authorization: Optional[str] = Header(default=None),
                    x_trade_session: Optional[str] = Header(default=None)):
    claims = await optional_user(authorization)
    owner, _t = _owner(claims, x_trade_session)
    docs = await EVENTS.find({"owner": owner}).sort("createdAt", -1).to_list(100)
    return {"items": [_clean(d) for d in docs]}


@router.get("/{event_id}")
async def get_event(event_id: str, authorization: Optional[str] = Header(default=None),
                    x_trade_session: Optional[str] = Header(default=None)):
    doc = await EVENTS.find_one({"_id": event_id})
    if not doc:
        raise HTTPException(404, "Event not found")
    if doc.get("status") not in PUBLIC_STATUSES:
        claims = await optional_user(authorization)
        owner, _t = _owner(claims, x_trade_session)
        is_admin = False
        if claims:
            u = await db.users.find_one({"uid": claims.get("uid")})
            is_admin = bool(u and u.get("role") == "admin")
        if doc.get("owner") != owner and not is_admin:
            raise HTTPException(403, "Not authorised to view this event")
    return _clean(doc)


# ---------------- Submission ----------------
class EventIn(BaseModel):
    name: str
    category: str = "Trade Fair"
    country: str
    city: str = ""
    venueName: str = ""
    venueAddress: str = ""
    startDate: str = ""
    endDate: str = ""
    organizer: str = ""
    description: str = ""
    audience: str = "All"
    industry: str = "Multi-sector"
    products: str = ""
    contactName: str = ""
    contactEmail: str
    contactPhone: str = ""
    website: str = ""
    images: List[str] = Field(default_factory=list)     # storage file URLs
    posters: List[str] = Field(default_factory=list)
    flyers: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)


@router.post("/submit")
async def submit_event(body: EventIn, authorization: Optional[str] = Header(default=None),
                       x_trade_session: Optional[str] = Header(default=None)):
    claims = await optional_user(authorization)
    owner, otype = _owner(claims, x_trade_session)
    r = region_of(body.country)
    eid = uuid.uuid4().hex
    doc = {"_id": eid, "id": eid, "owner": owner, "ownerType": otype,
           **body.model_dump(), "region": r, "status": "payment_pending",
           "paid": False, "featured": False, "image": (body.images or [None])[0],
           "createdAt": _iso(), "updatedAt": _iso(), "expiresAt": None}
    await EVENTS.insert_one(doc)
    await SUBS.insert_one({"_id": uuid.uuid4().hex, "eventId": eid, "owner": owner,
                           "action": "submitted", "at": _iso()})
    await send_event_email("submitted", body.contactEmail,
                           {"name": body.contactName, "eventName": body.name, "eventId": eid})
    await notify_admin("admin_new_submission", {
        "eventName": body.name, "country": body.country, "category": body.category,
        "contactName": body.contactName, "contactEmail": body.contactEmail})
    return {"ok": True, "eventId": eid, "region": r, "status": doc["status"]}


# ---------------- Payments ----------------
async def _mark_paid(event_id: str, amount: float, currency: str, gateway: str, ref: str):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        return
    if ev.get("paid"):
        return
    cfg = await get_event_pricing()
    duration = int(cfg.get("durationDays", 30))
    invoice = f"LN-EV-{datetime.now().strftime('%Y%m')}-{event_id[:6].upper()}"
    await EVENTS.update_one({"_id": event_id}, {"$set": {
        "paid": True, "status": "under_review", "paidAt": _iso(),
        "paymentGateway": gateway, "paymentRef": ref, "invoice": invoice,
        "durationDays": duration, "updatedAt": _iso()}})
    await PAY.update_one({"eventId": event_id, "ref": ref}, {"$set": {
        "eventId": event_id, "owner": ev.get("owner"), "amount": amount, "currency": currency,
        "gateway": gateway, "ref": ref, "status": "paid", "invoice": invoice, "at": _iso()}}, upsert=True)
    amount_label = (f"\u20b9{amount:,.0f}" if currency == "inr" else f"${amount:,.2f}")
    await send_event_email("payment_success", ev.get("contactEmail"),
                           {"name": ev.get("contactName"), "eventName": ev.get("name"),
                            "amountLabel": amount_label, "invoice": invoice, "durationDays": duration})
    await send_event_email("under_review", ev.get("contactEmail"),
                           {"name": ev.get("contactName"), "eventName": ev.get("name")})


# --- Stripe (INTL) ---
class StripePayIn(BaseModel):
    origin: str


@router.post("/{event_id}/pay/stripe")
async def pay_stripe(event_id: str, body: StripePayIn, request: Request):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    if ev.get("paid"):
        raise HTTPException(400, "Already paid")
    cfg = await get_event_pricing()
    r = ev.get("region", "INTL")
    amount = float(cfg[r]["amount"]); currency = cfg[r]["currency"]
    host_url = str(request.base_url)
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=f"{host_url}api/webhook/stripe")
    origin = body.origin.rstrip("/")
    success_url = f"{origin}/expo/submit?event_paid={event_id}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/expo/submit?cancelled=1"
    meta = {"kind": "event_listing", "eventId": event_id, "region": r}
    session = await stripe.create_checkout_session(CheckoutSessionRequest(
        amount=amount, currency=currency, success_url=success_url, cancel_url=cancel_url, metadata=meta))
    await PAY.insert_one({"_id": session.session_id, "eventId": event_id, "owner": ev.get("owner"),
                          "amount": amount, "currency": currency, "gateway": "stripe",
                          "ref": session.session_id, "status": "initiated", "at": _iso()})
    return {"url": session.url, "sessionId": session.session_id, "amount": amount, "currency": currency}


@router.get("/pay/stripe/status/{session_id}")
async def pay_stripe_status(session_id: str):
    rec = await PAY.find_one({"_id": session_id})
    if not rec:
        raise HTTPException(404, "Payment not found")
    if rec["status"] == "paid":
        return {"status": "paid", "eventId": rec["eventId"]}
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url="")
    st = await stripe.get_checkout_status(session_id)
    if st.payment_status == "paid":
        await PAY.update_one({"_id": session_id}, {"$set": {"status": "paid", "at": _iso()}})
        await _mark_paid(rec["eventId"], rec["amount"], rec["currency"], "stripe", session_id)
        return {"status": "paid", "eventId": rec["eventId"]}
    return {"status": st.status, "paymentStatus": st.payment_status, "eventId": rec["eventId"]}


# --- Razorpay (IN) ---
@router.post("/{event_id}/pay/razorpay/order")
async def pay_razorpay_order(event_id: str):
    if not RAZORPAY_ENABLED:
        raise HTTPException(503, "Razorpay not configured — use Stripe or add Razorpay keys.")
    import razorpay
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    if ev.get("paid"):
        raise HTTPException(400, "Already paid")
    cfg = await get_event_pricing()
    amount = float(cfg["IN"]["amount"]); currency = "INR"
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    order = client.order.create({"amount": int(round(amount * 100)), "currency": currency,
                                 "payment_capture": 1, "receipt": f"ev_{event_id[:20]}"})
    await PAY.insert_one({"_id": order["id"], "eventId": event_id, "owner": ev.get("owner"),
                          "amount": amount, "currency": "inr", "gateway": "razorpay",
                          "ref": order["id"], "status": "initiated", "at": _iso()})
    return {"orderId": order["id"], "amount": order["amount"], "currency": currency,
            "keyId": RAZORPAY_KEY_ID, "eventName": ev.get("name"),
            "contact": {"name": ev.get("contactName"), "email": ev.get("contactEmail"),
                        "phone": ev.get("contactPhone")}}


class RazorpayVerifyIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/pay/razorpay/verify")
async def pay_razorpay_verify(body: RazorpayVerifyIn):
    if not RAZORPAY_ENABLED:
        raise HTTPException(503, "Razorpay not configured")
    expected = hmac.new(RAZORPAY_KEY_SECRET.encode(),
                        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(400, "Invalid payment signature")
    rec = await PAY.find_one({"_id": body.razorpay_order_id})
    if not rec:
        raise HTTPException(404, "Order not found")
    await PAY.update_one({"_id": body.razorpay_order_id},
                         {"$set": {"status": "paid", "paymentId": body.razorpay_payment_id, "at": _iso()}})
    await _mark_paid(rec["eventId"], rec["amount"], "inr", "razorpay", body.razorpay_payment_id)
    return {"ok": True, "eventId": rec["eventId"]}


# ---------------- Admin ----------------
@router.get("/admin/all")
async def admin_all(status: str = Query(""), _: dict = Depends(require_admin)):
    q = {"status": status} if status else {}
    docs = await EVENTS.find(q).sort("createdAt", -1).to_list(400)
    return {"items": [_clean(d) for d in docs]}


@router.get("/admin/pricing")
async def admin_get_pricing(_: dict = Depends(require_admin)):
    return await get_event_pricing()


class EventPricingIn(BaseModel):
    inAmount: Optional[float] = None
    intlAmount: Optional[float] = None
    durationDays: Optional[int] = None
    discountPct: Optional[float] = None


@router.put("/admin/pricing")
async def admin_set_pricing(body: EventPricingIn, _: dict = Depends(require_admin)):
    cfg = await set_event_pricing(body.model_dump(exclude_none=True))
    return {"ok": True, "config": cfg}


@router.post("/admin/create")
async def admin_create(body: EventIn, _: dict = Depends(require_admin)):
    r = region_of(body.country)
    cfg = await get_event_pricing()
    eid = uuid.uuid4().hex
    doc = {"_id": eid, "id": eid, "owner": "admin", "ownerType": "admin",
           **body.model_dump(), "region": r, "status": "published", "paid": True,
           "featured": False, "image": (body.images or [None])[0],
           "durationDays": int(cfg.get("durationDays", 30)),
           "expiresAt": _iso(_now() + timedelta(days=int(cfg.get("durationDays", 30)) * 6)),
           "createdAt": _iso(), "updatedAt": _iso()}
    await EVENTS.insert_one(doc)
    return {"ok": True, "eventId": eid}


@router.put("/admin/{event_id}")
async def admin_edit(event_id: str, body: EventIn, _: dict = Depends(require_admin)):
    res = await EVENTS.update_one({"_id": event_id}, {"$set": {**body.model_dump(),
                                  "image": (body.images or [None])[0], "updatedAt": _iso()}})
    if not res.matched_count:
        raise HTTPException(404, "Event not found")
    return {"ok": True}


@router.post("/admin/{event_id}/approve")
async def admin_approve(event_id: str, _: dict = Depends(require_admin)):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    cfg = await get_event_pricing()
    duration = int(ev.get("durationDays") or cfg.get("durationDays", 30))
    expires = _iso(_now() + timedelta(days=duration))
    await EVENTS.update_one({"_id": event_id}, {"$set": {
        "status": "published", "approvedAt": _iso(), "publishedAt": _iso(),
        "expiresAt": expires, "updatedAt": _iso()}})
    await send_event_email("approved", ev.get("contactEmail"),
                           {"name": ev.get("contactName"), "eventName": ev.get("name")})
    await send_event_email("published", ev.get("contactEmail"),
                           {"name": ev.get("contactName"), "eventName": ev.get("name"), "expiresAt": expires})
    return {"ok": True, "expiresAt": expires}


class RejectIn(BaseModel):
    reason: str = ""


@router.post("/admin/{event_id}/reject")
async def admin_reject(event_id: str, body: RejectIn, _: dict = Depends(require_admin)):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    await EVENTS.update_one({"_id": event_id}, {"$set": {"status": "rejected",
                            "rejectReason": body.reason, "updatedAt": _iso()}})
    await send_event_email("rejected", ev.get("contactEmail"),
                           {"name": ev.get("contactName"), "eventName": ev.get("name"), "reason": body.reason})
    return {"ok": True}


@router.post("/admin/{event_id}/feature")
async def admin_feature(event_id: str, _: dict = Depends(require_admin)):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    await EVENTS.update_one({"_id": event_id}, {"$set": {"featured": not ev.get("featured"), "updatedAt": _iso()}})
    return {"ok": True, "featured": not ev.get("featured")}


class ExtendIn(BaseModel):
    days: int = 30


@router.post("/admin/{event_id}/extend")
async def admin_extend(event_id: str, body: ExtendIn, _: dict = Depends(require_admin)):
    ev = await EVENTS.find_one({"_id": event_id})
    if not ev:
        raise HTTPException(404, "Event not found")
    base = _now()
    if ev.get("expiresAt"):
        try:
            cur = datetime.fromisoformat(ev["expiresAt"])
            base = cur if cur > base else base
        except Exception:
            pass
    expires = _iso(base + timedelta(days=body.days))
    await EVENTS.update_one({"_id": event_id}, {"$set": {"expiresAt": expires, "updatedAt": _iso()}})
    return {"ok": True, "expiresAt": expires}


@router.delete("/admin/{event_id}")
async def admin_delete(event_id: str, _: dict = Depends(require_admin)):
    await EVENTS.delete_one({"_id": event_id})
    return {"ok": True}


class EmailTestIn(BaseModel):
    to: str
    kind: str = "submitted"


@router.post("/admin/email-test")
async def admin_email_test(body: EmailTestIn, _: dict = Depends(require_admin)):
    """Send a sample of any template to verify Resend delivery + rendering."""
    from emailer import send, RESEND_API_KEY
    sample = {
        "name": "Test User", "eventName": "India Global Export Summit 2026",
        "eventId": "test1234", "amountLabel": "\u20b910,000", "invoice": "LN-EV-202607-TEST01",
        "durationDays": 30, "expiresAt": "2026-08-05T00:00:00+00:00",
        "reason": "Sample rejection reason.", "reportTitle": "HSN 090411 · India→UAE",
        "plan": "annual", "until": "2027-07-06T00:00:00+00:00", "item": "annual subscription",
        "country": "India", "category": "Business", "contactName": "Test User",
        "contactEmail": body.to, "email": body.to, "phone": "+91 90000 00000",
        "service": "Export Documentation", "source": "email-test",
    }
    res = await send(body.kind, body.to, sample)
    return {"resendConfigured": bool(RESEND_API_KEY), "result": res}


# ---------------- Seed (starter published expos) ----------------
_SEED = [
    {"name": "India International Trade Fair (IITF)", "category": "Trade Fair", "country": "India",
     "city": "New Delhi", "venueName": "Pragati Maidan", "startDate": "2026-11-14", "endDate": "2026-11-27",
     "industry": "Multi-sector", "audience": "All", "organizer": "ITPO",
     "description": "India's largest multi-sector trade fair drawing 1.5M+ visitors across every industry.",
     "image": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80"},
    {"name": "Gulfood Dubai", "category": "Trade Fair", "country": "UAE", "city": "Dubai",
     "venueName": "Dubai World Trade Centre", "startDate": "2026-02-16", "endDate": "2026-02-20",
     "industry": "Agriculture & Food", "audience": "Importers", "organizer": "DWTC",
     "description": "The world's largest annual food & beverage sourcing event.",
     "image": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80"},
    {"name": "Canton Fair", "category": "Import/Export", "country": "China", "city": "Guangzhou",
     "venueName": "Canton Fair Complex", "startDate": "2026-04-15", "endDate": "2026-05-05",
     "industry": "Multi-sector", "audience": "Importers", "organizer": "China Foreign Trade Centre",
     "description": "China's flagship import & export fair spanning electronics, machinery and consumer goods.",
     "image": "https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&w=1200&q=80"},
    {"name": "Hannover Messe", "category": "Manufacturing", "country": "Germany", "city": "Hannover",
     "venueName": "Deutsche Messe", "startDate": "2026-04-20", "endDate": "2026-04-24",
     "industry": "Engineering Goods", "audience": "Manufacturers", "organizer": "Deutsche Messe AG",
     "description": "The world's leading industrial technology and manufacturing trade fair.",
     "image": "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80"},
    {"name": "Vibrant Gujarat Global Summit", "category": "Government", "country": "India", "city": "Gandhinagar",
     "venueName": "Mahatma Mandir", "startDate": "2026-01-10", "endDate": "2026-01-12",
     "industry": "Multi-sector", "audience": "Investors", "organizer": "Government of Gujarat",
     "description": "Flagship investment summit connecting global investors with Indian opportunities.",
     "image": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1200&q=80"},
    {"name": "Singapore FinTech Festival", "category": "Finance", "country": "Singapore", "city": "Singapore",
     "venueName": "Singapore EXPO", "startDate": "2026-11-11", "endDate": "2026-11-13",
     "industry": "Logistics", "audience": "Startups", "organizer": "MAS",
     "description": "The world's largest fintech gathering with a strong trade-finance track.",
     "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"},
]


async def seed_events():
    if await EVENTS.count_documents({}) > 0:
        return
    cfg = await get_event_pricing()
    for s in _SEED:
        eid = uuid.uuid4().hex
        await EVENTS.insert_one({"_id": eid, "id": eid, "owner": "admin", "ownerType": "admin",
                                 "region": region_of(s["country"]), "status": "published", "paid": True,
                                 "featured": s["name"].startswith("Gulfood"), "products": "",
                                 "contactEmail": "", "contactName": s.get("organizer", ""),
                                 "durationDays": cfg["durationDays"],
                                 "expiresAt": _iso(_now() + timedelta(days=365)),
                                 "createdAt": _iso(), "updatedAt": _iso(), **s})
    logging.info("Seeded %d starter events", len(_SEED))


async def event_expiry_sweep():
    """Daily: email 'expiring soon' (~3 days out) and mark/notify expired listings."""
    now = _now()
    soon = _iso(now + timedelta(days=3))
    now_iso = _iso(now)
    # expiring soon (published, not yet reminded, expiring within 3 days)
    async for ev in EVENTS.find({"status": "published", "expiringNotified": {"$ne": True},
                                 "expiresAt": {"$lte": soon, "$gt": now_iso}}):
        await send_event_email("expiring", ev.get("contactEmail"),
                               {"name": ev.get("contactName"), "eventName": ev.get("name"),
                                "expiresAt": ev.get("expiresAt")})
        await EVENTS.update_one({"_id": ev["_id"]}, {"$set": {"expiringNotified": True}})
    # expired
    async for ev in EVENTS.find({"status": "published", "expiresAt": {"$lte": now_iso}}):
        await EVENTS.update_one({"_id": ev["_id"]}, {"$set": {"status": "expired", "updatedAt": now_iso}})
        await send_event_email("expired", ev.get("contactEmail"),
                               {"name": ev.get("contactName"), "eventName": ev.get("name")})
