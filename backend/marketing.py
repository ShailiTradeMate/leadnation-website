"""Admin marketing dashboard — Facebook Ads, Instagram and LinkedIn organic metrics pulled
from Windsor.ai (api_key is a query parameter upstream; never logged or returned), plus the
site's own Meta-Pixel-equivalent conversions from db.events. Cached per range for 1h."""
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, Query

from core import db, require_admin

logger = logging.getLogger("marketing")
# httpx logs every request URL at INFO — Windsor carries the key in the query string.
logging.getLogger("httpx").setLevel(logging.WARNING)
router = APIRouter(prefix="/admin/marketing", tags=["admin-marketing"])

WINDSOR = "https://connectors.windsor.ai"
CACHE_TTL = 3600
RANGES = {"last_7d": 7, "last_30d": 30, "last_90d": 90}

FIELDS = {
    "facebook": "date,campaign_name,spend,impressions,reach,clicks,ctr,cpm,actions_lead",
    "instagram_account": "date,followers_count,reach_1d,impressions_1d,profile_views_1d,website_clicks_1d",
    "instagram_profile": "date,account_id,user_name,followers_count",
    "instagram_posts": ("date,media_id,media_type,media_caption,media_permalink,media_like_count,"
                        "media_comments_count,media_reach,media_impressions,media_engagement,media_saved"),
    "linkedin_account": ("date,organization_follower_count,account_analytics_impression_count,"
                         "account_analytics_total_engagements,account_analytics_click_count"),
    "linkedin_profile": "date,organization_id,organization_name,organization_follower_count",
    "linkedin_posts": ("date,post_id,share_text,share_impression_count,share_engagement_rate,"
                       "share_total_engagements,share_like_count"),
}
CONNECTOR = {"facebook": "facebook", "instagram_account": "instagram", "instagram_posts": "instagram",
             "instagram_profile": "instagram", "linkedin_account": "linkedin_organic",
             "linkedin_posts": "linkedin_organic", "linkedin_profile": "linkedin_organic"}


def _key() -> str:
    return os.environ.get("WINDSOR_API_KEY", "")


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


async def _windsor(dataset: str, date_preset: str) -> list:
    params = {"api_key": _key(), "fields": FIELDS[dataset], "date_preset": date_preset, "_max_rows": 2000}
    async with httpx.AsyncClient(timeout=60) as cx:
        r = await cx.get(f"{WINDSOR}/{CONNECTOR[dataset]}", params=params)
    if r.status_code != 200:
        raise RuntimeError(f"Windsor {dataset} HTTP {r.status_code}")  # body may echo the key — never log it
    data = r.json().get("data")
    return data if isinstance(data, list) else []


def _daily(rows, fields):
    """Collapse rows to one point per date (sum of the given fields), sorted ascending."""
    out = {}
    for r in rows:
        d = r.get("date")
        if not d:
            continue
        pt = out.setdefault(d, {"date": d, **{f: 0.0 for f in fields}})
        for f in fields:
            pt[f] += _num(r.get(f))
    return [out[d] for d in sorted(out)]


def _last_nonzero(rows, field):
    vals = [_num(r.get(field)) for r in rows if r.get(field) not in (None, "", 0, 0.0)]
    return vals[-1] if vals else 0.0


def _facebook(rows):
    spend = sum(_num(r.get("spend")) for r in rows)
    impressions = sum(_num(r.get("impressions")) for r in rows)
    clicks = sum(_num(r.get("clicks")) for r in rows)
    leads = sum(_num(r.get("actions_lead")) for r in rows)
    camps = {}
    for r in rows:
        c = camps.setdefault(r.get("campaign_name") or "—", {"campaign": r.get("campaign_name") or "—", "spend": 0.0, "impressions": 0.0, "clicks": 0.0, "leads": 0.0})
        c["spend"] += _num(r.get("spend")); c["impressions"] += _num(r.get("impressions"))
        c["clicks"] += _num(r.get("clicks")); c["leads"] += _num(r.get("actions_lead"))
    return {
        "summary": {"spend": round(spend, 2), "impressions": impressions, "reach": sum(_num(r.get("reach")) for r in rows),
                    "clicks": clicks, "leads": leads,
                    "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
                    "cpm": round(spend / impressions * 1000, 2) if impressions else 0,
                    "costPerLead": round(spend / leads, 2) if leads else 0},
        "daily": _daily(rows, ["spend", "impressions", "clicks", "actions_lead"]),
        "campaigns": sorted(camps.values(), key=lambda c: -c["spend"])[:20],
        "connected": True, "hasData": bool(rows),
    }


def _instagram(account, posts, profile):
    daily = _daily(account, ["reach_1d", "impressions_1d", "profile_views_1d", "website_clicks_1d"])
    followers = _last_nonzero(sorted(profile, key=lambda r: r.get("date") or ""), "followers_count")
    top = sorted(posts, key=lambda p: -_num(p.get("media_engagement")))[:10]
    return {
        "summary": {"followers": followers, "reach": sum(p["reach_1d"] for p in daily),
                    "impressions": sum(p["impressions_1d"] for p in daily),
                    "profileViews": sum(p["profile_views_1d"] for p in daily),
                    "websiteClicks": sum(p["website_clicks_1d"] for p in daily),
                    "posts": len(posts), "engagement": sum(_num(p.get("media_engagement")) for p in posts)},
        "daily": daily,
        "posts": [{"id": p.get("media_id"), "date": p.get("date"), "type": p.get("media_type"),
                   "caption": (p.get("media_caption") or "")[:140], "url": p.get("media_permalink"),
                   "likes": _num(p.get("media_like_count")), "comments": _num(p.get("media_comments_count")),
                   "saved": _num(p.get("media_saved")), "reach": _num(p.get("media_reach")),
                   "engagement": _num(p.get("media_engagement"))} for p in top],
        "connected": True, "hasData": bool(account or posts),
    }


def _linkedin(account, posts, profile):
    daily = _daily(account, ["account_analytics_impression_count", "account_analytics_total_engagements", "account_analytics_click_count"])
    followers = _last_nonzero(sorted(profile + account, key=lambda r: r.get("date") or ""), "organization_follower_count")
    top = sorted(posts, key=lambda p: -_num(p.get("share_total_engagements")))[:10]
    impressions = sum(p["account_analytics_impression_count"] for p in daily)
    engagements = sum(p["account_analytics_total_engagements"] for p in daily)
    return {
        "summary": {"followers": followers, "impressions": impressions, "engagements": engagements,
                    "clicks": sum(p["account_analytics_click_count"] for p in daily),
                    "engagementRate": round(engagements / impressions * 100, 2) if impressions else 0,
                    "posts": len(posts)},
        "daily": [{"date": p["date"], "impressions": p["account_analytics_impression_count"],
                   "engagements": p["account_analytics_total_engagements"], "clicks": p["account_analytics_click_count"]} for p in daily],
        "posts": [{"id": p.get("post_id"), "date": p.get("date"), "text": (p.get("share_text") or "")[:140],
                   "impressions": _num(p.get("share_impression_count")), "likes": _num(p.get("share_like_count")),
                   "engagements": _num(p.get("share_total_engagements")),
                   "engagementRate": round(_num(p.get("share_engagement_rate")) * 100, 2)} for p in top],
        "connected": True, "hasData": bool(account or posts),
    }


async def _site_conversions(days: int):
    """What the Meta Pixel sees, counted first-party from db.events (same triggers)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    names = {"page_view": "pageViews", "user_registered": "registrations", "contact_form_submitted": "contactLeads",
             "service_request_submitted": "serviceLeads", "whatsapp_click": "whatsappLeads", "payment_success": "purchases"}
    pipeline = [{"$match": {"createdAt": {"$gte": since}, "name": {"$in": list(names)}}},
                {"$group": {"_id": "$name", "n": {"$sum": 1}}}]
    out = {v: 0 for v in names.values()}
    async for row in db.events.aggregate(pipeline):
        out[names[row["_id"]]] = row["n"]
    out["leads"] = out["contactLeads"] + out["serviceLeads"] + out["whatsappLeads"]
    return out


async def build_overview(date_preset: str) -> dict:
    channels, errors = {}, {}
    if not _key():
        for ch in ("facebook", "instagram", "linkedin"):
            channels[ch] = {"connected": False, "hasData": False, "summary": {}, "daily": [], "posts": [], "campaigns": []}
    else:
        async def fetch(ds):
            try:  # follower counts are a current-state field — only recent days carry a value
                return await _windsor(ds, "last_7d" if ds.endswith("_profile") else date_preset)
            except Exception as exc:
                errors[ds] = str(exc)[:120]
                return []
        fb, ig_a, ig_p, ig_f, li_a, li_p, li_f = [await fetch(ds) for ds in
                                                  ("facebook", "instagram_account", "instagram_posts", "instagram_profile",
                                                   "linkedin_account", "linkedin_posts", "linkedin_profile")]
        channels["facebook"] = _facebook(fb)
        channels["instagram"] = _instagram(ig_a, ig_p, ig_f)
        channels["linkedin"] = _linkedin(li_a, li_p, li_f)
    return {"range": date_preset, "windsorConfigured": bool(_key()), "channels": channels, "errors": errors,
            "site": await _site_conversions(RANGES[date_preset]),
            "generatedAt": datetime.now(timezone.utc).isoformat()}


@router.get("/overview")
async def overview(range: str = Query("last_30d"), refresh: bool = False, _=Depends(require_admin)):
    date_preset = range if range in RANGES else "last_30d"
    cache_id = f"overview:{date_preset}"
    if not refresh:
        cached = await db.marketing_cache.find_one({"_id": cache_id})
        if cached and (datetime.now(timezone.utc) - datetime.fromisoformat(cached["at"])).total_seconds() < CACHE_TTL:
            return {**cached["data"], "cached": True}
    data = await build_overview(date_preset)
    if not data["errors"] or any(c.get("hasData") for c in data["channels"].values()):
        await db.marketing_cache.replace_one(
            {"_id": cache_id}, {"_id": cache_id, "data": data, "at": datetime.now(timezone.utc).isoformat()}, upsert=True)
    return {**data, "cached": False}
