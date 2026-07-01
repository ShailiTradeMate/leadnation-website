"""Centralized Pricing Engine for LeadNation.

Single source of truth for ALL prices (pay-per-report + subscriptions), currencies,
payment gateways and paywall/monetization settings. Prices live in Mongo
(`pricing_config` single doc) and are edited from the Admin CMS. Every consumer —
website pricing page, checkout, Stripe, Razorpay, future mobile app / partner
portals — reads prices dynamically from here. NOTHING is hardcoded downstream.

Also owns conversion tracking (`paywall_events`) and pre-paywall email capture
(`email_captures`) so the funnel is measurable.
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from core import db, require_admin

pricing_router = APIRouter(prefix="/pricing")

CFG = db.pricing_config
EVENTS = db.paywall_events
CAPTURES = db.email_captures

CONFIG_ID = "current"
REGIONS = ("IN", "INTL")
PLAN_KEYS = ("download", "monthly", "annual")


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _region(r: Optional[str]) -> str:
    return "IN" if (r or "").upper() == "IN" else "INTL"


# ---- Defaults (seeded once; the admin owns everything after that) ----
DEFAULT_PRICING: Dict[str, Any] = {
    "_id": CONFIG_ID,
    "currencies": {
        "IN": {"code": "inr", "symbol": "\u20b9"},
        "INTL": {"code": "usd", "symbol": "$"},
    },
    "plans": {
        "download": {"label": "Pay-per-Report", "interval": "one_time",
                     "IN": 25.0, "INTL": 1.0,
                     "tagline": "One branded Trade Report", "active": True},
        "monthly": {"label": "Pro Monthly", "interval": "month",
                    "IN": 499.0, "INTL": 9.0,
                    "tagline": "Unlimited reports, billed monthly", "active": True},
        "annual": {"label": "Pro Annual", "interval": "year",
                   "IN": 3999.0, "INTL": 79.0,
                   "tagline": "Unlimited reports, best value", "active": True},
    },
    "gateways": {
        "stripe": {"label": "Stripe", "enabled": True, "regions": ["INTL", "IN"]},
        "razorpay": {"label": "Razorpay", "enabled": False, "regions": ["IN"]},
    },
    "settings": {
        "freeFirstDownload": True,
        "mostPopular": "annual",
        "emailCaptureBeforePaywall": True,
    },
    "features": [
        {"label": "Branded Trade Reports (PDF)", "download": "1 free, then per report",
         "monthly": "Unlimited", "annual": "Unlimited"},
        {"label": "Full cost & duty waterfall", "download": True, "monthly": True, "annual": True},
        {"label": "Buyer-market comparison", "download": True, "monthly": True, "annual": True},
        {"label": "LeadNation Brain queries", "download": "Limited", "monthly": "Priority", "annual": "Priority"},
        {"label": "Saved projects & version history", "download": True, "monthly": True, "annual": True},
        {"label": "Priority support", "download": False, "monthly": True, "annual": True},
    ],
    "updatedAt": _iso(),
}


async def get_config() -> Dict[str, Any]:
    """Return the live pricing config, seeding defaults on first access."""
    doc = await CFG.find_one({"_id": CONFIG_ID})
    if not doc:
        await CFG.insert_one({**DEFAULT_PRICING, "updatedAt": _iso()})
        doc = await CFG.find_one({"_id": CONFIG_ID})
    return doc


async def resolve(plan: str, region: str) -> Tuple[float, str]:
    """Return (amount, currency_code) for a plan+region. `subscription` == monthly."""
    if plan == "subscription":
        plan = "monthly"
    if plan not in PLAN_KEYS:
        raise HTTPException(400, "Unknown plan")
    r = _region(region)
    cfg = await get_config()
    amount = float(cfg["plans"][plan][r])
    currency = cfg["currencies"][r]["code"]
    return amount, currency


async def gateway_for(region: str) -> str:
    """Pick the enabled gateway serving a region (Stripe is the universal fallback)."""
    r = _region(region)
    cfg = await get_config()
    # Region-specific enabled gateway wins (e.g. Razorpay for IN once keys exist)
    for name, g in cfg.get("gateways", {}).items():
        if g.get("enabled") and r in (g.get("regions") or []) and name != "stripe":
            if name == "razorpay" and os.environ.get("RAZORPAY_KEY_ID"):
                return name
    return "stripe"


def public_view(cfg: Dict[str, Any], region: str) -> Dict[str, Any]:
    """Shape the config for public/website consumption for a given region."""
    r = _region(region)
    cur = cfg["currencies"][r]
    plans = []
    for key in PLAN_KEYS:
        p = cfg["plans"].get(key, {})
        if not p.get("active", True):
            continue
        amount = float(p.get(r, 0))
        plans.append({
            "key": key,
            "label": p.get("label", key),
            "interval": p.get("interval", "one_time"),
            "tagline": p.get("tagline", ""),
            "amount": amount,
            "currency": cur["code"],
            "symbol": cur["symbol"],
        })
    # annual savings vs 12x monthly
    savings_pct = None
    try:
        m = float(cfg["plans"]["monthly"][r]); a = float(cfg["plans"]["annual"][r])
        if m > 0:
            savings_pct = max(0, round((1 - a / (m * 12)) * 100))
    except Exception:
        pass
    return {
        "region": r,
        "currency": cur["code"],
        "symbol": cur["symbol"],
        "plans": plans,
        "settings": cfg.get("settings", {}),
        "features": cfg.get("features", []),
        "annualSavingsPct": savings_pct,
        "gateway": None,  # resolved at checkout
    }


# ---------------- Public endpoints ----------------
@pricing_router.get("/config")
async def pricing_config(region: str = "INTL"):
    cfg = await get_config()
    view = public_view(cfg, region)
    view["gateway"] = await gateway_for(region)
    return view


class TrackIn(BaseModel):
    event: str                       # paywall_view | email_capture | checkout_start | purchase | plan_view
    plan: str = ""
    region: str = "INTL"
    projectId: str = ""
    meta: Dict[str, Any] = {}


@pricing_router.post("/track")
async def track(body: TrackIn, x_trade_session: Optional[str] = Header(default=None)):
    await EVENTS.insert_one({
        "_id": uuid.uuid4().hex, "event": body.event, "plan": body.plan,
        "region": _region(body.region), "projectId": body.projectId,
        "session": x_trade_session or "", "meta": body.meta, "at": _iso()})
    return {"ok": True}


class LeadIn(BaseModel):
    email: str
    region: str = "INTL"
    projectId: str = ""
    source: str = "paywall"


@pricing_router.post("/lead")
async def capture_lead(body: LeadIn, x_trade_session: Optional[str] = Header(default=None)):
    email = (body.email or "").strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(400, "Valid email required")
    await CAPTURES.update_one(
        {"email": email},
        {"$set": {"email": email, "region": _region(body.region), "source": body.source,
                  "projectId": body.projectId, "session": x_trade_session or "",
                  "updatedAt": _iso()},
         "$setOnInsert": {"_id": uuid.uuid4().hex, "createdAt": _iso()}},
        upsert=True)
    await EVENTS.insert_one({
        "_id": uuid.uuid4().hex, "event": "email_capture", "region": _region(body.region),
        "projectId": body.projectId, "session": x_trade_session or "",
        "meta": {"email": email}, "at": _iso()})
    return {"ok": True}


# ---------------- Admin endpoints ----------------
@pricing_router.get("/admin")
async def admin_get(_: dict = Depends(require_admin)):
    cfg = await get_config()
    return {k: v for k, v in cfg.items() if k != "_id"}


class PricingUpdate(BaseModel):
    currencies: Optional[Dict[str, Any]] = None
    plans: Optional[Dict[str, Any]] = None
    gateways: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    features: Optional[List[Dict[str, Any]]] = None


def _validate_plans(plans: Dict[str, Any]):
    for key, p in plans.items():
        for r in REGIONS:
            if r in p:
                try:
                    if float(p[r]) < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    raise HTTPException(400, f"Invalid price for {key}/{r}")


@pricing_router.put("/admin")
async def admin_update(body: PricingUpdate, admin: dict = Depends(require_admin)):
    cfg = await get_config()
    patch = {}
    data = body.model_dump(exclude_none=True)
    if "plans" in data:
        _validate_plans(data["plans"])
        merged = {**cfg.get("plans", {})}
        for k, v in data["plans"].items():
            merged[k] = {**merged.get(k, {}), **v}
        patch["plans"] = merged
    if "gateways" in data:
        merged = {**cfg.get("gateways", {})}
        for k, v in data["gateways"].items():
            merged[k] = {**merged.get(k, {}), **v}
        patch["gateways"] = merged
    if "currencies" in data:
        merged = {**cfg.get("currencies", {})}
        for k, v in data["currencies"].items():
            merged[k] = {**merged.get(k, {}), **v}
        patch["currencies"] = merged
    if "settings" in data:
        patch["settings"] = {**cfg.get("settings", {}), **data["settings"]}
    if "features" in data:
        patch["features"] = data["features"]
    patch["updatedAt"] = _iso()
    patch["updatedBy"] = admin.get("email") or admin.get("customer_id") or admin.get("sub")
    await CFG.update_one({"_id": CONFIG_ID}, {"$set": patch}, upsert=True)
    cfg = await get_config()
    return {"ok": True, "config": {k: v for k, v in cfg.items() if k != "_id"}}


@pricing_router.get("/admin/analytics")
async def admin_analytics(_: dict = Depends(require_admin)):
    pipeline = [{"$group": {"_id": "$event", "n": {"$sum": 1}}}]
    rows = await EVENTS.aggregate(pipeline).to_list(50)
    funnel = {r["_id"]: r["n"] for r in rows}
    captures = await CAPTURES.count_documents({})
    recent = await CAPTURES.find({}).sort("createdAt", -1).to_list(50)
    views = funnel.get("paywall_view", 0)
    purchases = funnel.get("purchase", 0)
    conv = round((purchases / views) * 100, 1) if views else 0.0
    return {"funnel": funnel, "emailCaptures": captures, "conversionPct": conv,
            "recentCaptures": [{k: v for k, v in c.items() if k != "_id"} for c in recent]}
