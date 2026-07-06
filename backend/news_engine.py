"""Trade News Engine — live + AI + admin, personalized by user profile.

Architecture:  Live News API (NewsData.io, env-based adapter)  +  LeadNation Brain
(impact analysis)  +  User Profile Context (country / role / products)  =  personalized
trade intelligence. Logged-in users get country/role-tailored news; guests get global
trade news. Admins can add / edit / feature / remove news. Shared by website + app.
"""
import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import httpx
from fastapi import APIRouter, Header, Query, Depends, HTTPException
from pydantic import BaseModel

from core import db, require_admin
from firebase_auth import optional_user, _bearer, verify_token
import llm_util

router = APIRouter(prefix="/news")

ADMIN_NEWS = db.trade_news_admin      # admin-authored / curated
NEWS_ITEMS = db.news_items            # resolved cache for detail lookups (admin + live)
NEWS_CACHE = db.news_feed_cache       # live feed cache by scope key

NEWSDATA_KEY = os.environ.get("NEWSDATA_API_KEY", "").strip()
NEWSDATA_URL = "https://newsdata.io/api/1/latest"
CACHE_TTL_MIN = 30

FALLBACK_IMG = [
    "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1517292987719-0369a794ec0f?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
]

CATEGORIES = ["All", "Tariffs & Duties", "FTAs & Trade Deals", "Logistics & Shipping",
              "Policy & Compliance", "Commodities", "Business", "India"]


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _img_for(seed: str) -> str:
    return FALLBACK_IMG[abs(hash(seed)) % len(FALLBACK_IMG)]


def _mk_id(prefix: str, seed: str) -> str:
    return f"{prefix}-{hashlib.sha1(seed.encode()).hexdigest()[:16]}"


# ---------------- Curated fallback (used when live API unavailable) ----------------
CURATED: List[Dict[str, Any]] = [
    {"title": "Global merchandise trade rebounds as tariff tensions ease",
     "category": "Business", "country": "Global",
     "excerpt": "WTO data points to a broad recovery in goods trade led by electronics and machinery.",
     "source": "LeadNation Intelligence"},
    {"title": "Red Sea reroutes keep Asia–Europe container rates elevated",
     "category": "Logistics & Shipping", "country": "Global",
     "excerpt": "Carriers continue routing via the Cape of Good Hope, extending transit times 10–14 days.",
     "source": "Global Freight"},
    {"title": "EU CBAM reporting tightens for steel, cement and aluminium exporters",
     "category": "Policy & Compliance", "country": "Global",
     "excerpt": "Exporters to the EU must now track and report embedded carbon each quarter.",
     "source": "Regulatory Watch"},
    {"title": "India–UAE CEPA pushes bilateral trade past record highs",
     "category": "FTAs & Trade Deals", "country": "India",
     "excerpt": "Preferential tariffs open new lanes for SME exporters across food, textiles and pharma.",
     "source": "Trade Wire"},
    {"title": "New duty exemptions announced on key raw-material imports",
     "category": "Tariffs & Duties", "country": "India",
     "excerpt": "The move aims to lower input costs for manufacturers and boost export competitiveness.",
     "source": "MoCI"},
    {"title": "Commodity outlook: agri and metals firm on tight supply",
     "category": "Commodities", "country": "Global",
     "excerpt": "Analysts flag continued strength in food grains and base metals into next quarter.",
     "source": "Market Desk"},
]


def _normalise_curated() -> List[Dict[str, Any]]:
    out = []
    for c in CURATED:
        cid = _mk_id("ai", c["title"])
        out.append({**c, "id": cid, "image": _img_for(c["title"]),
                    "date": "Today", "badge": "ai", "url": ""})
    return out


# ---------------- Live adapter (NewsData.io) ----------------
async def _fetch_live(country: Optional[str], query: str) -> List[Dict[str, Any]]:
    if not NEWSDATA_KEY:
        return []
    params = {"apikey": NEWSDATA_KEY, "language": "en", "q": query or "trade OR export OR import OR tariff"}
    if country:
        params["country"] = country.lower()
    try:
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(NEWSDATA_URL, params=params)
            if r.status_code != 200:
                logging.info("NewsData %s: %s", r.status_code, r.text[:180])
                return []
            data = r.json()
        items = []
        for a in (data.get("results") or [])[:24]:
            title = a.get("title") or ""
            if not title:
                continue
            nid = _mk_id("live", a.get("link") or title)
            items.append({
                "id": nid, "title": title,
                "excerpt": (a.get("description") or "")[:220],
                "image": a.get("image_url") or _img_for(title),
                "category": "Business",
                "country": (a.get("country") or ["Global"])[0].title() if a.get("country") else "Global",
                "date": (a.get("pubDate") or "")[:16] or "Recently",
                "source": a.get("source_id") or "Newswire",
                "url": a.get("link") or "", "badge": "live",
                "body": a.get("content") or a.get("description") or "",
            })
        return items
    except Exception as exc:
        logging.warning("Live news fetch failed: %s", exc)
        return []


async def _admin_news(country: Optional[str]) -> List[Dict[str, Any]]:
    q = {"active": {"$ne": False}}
    docs = await ADMIN_NEWS.find(q).sort([("featured", -1), ("createdAt", -1)]).to_list(50)
    out = []
    for d in docs:
        out.append({"id": d["_id"], "title": d.get("title", ""), "excerpt": d.get("excerpt", ""),
                    "image": d.get("image") or _img_for(d.get("title", "")),
                    "category": d.get("category", "Business"), "country": d.get("country", "Global"),
                    "date": d.get("date") or (d.get("createdAt", "") or "")[:10] or "Today",
                    "source": d.get("source", "LeadNation"), "url": d.get("url", ""),
                    "badge": "admin", "featured": bool(d.get("featured")),
                    "body": d.get("body", "")})
    return out


async def _persist(items: List[Dict[str, Any]]):
    for it in items:
        try:
            await NEWS_ITEMS.update_one({"_id": it["id"]}, {"$set": {**it, "_id": it["id"], "cachedAt": _iso()}}, upsert=True)
        except Exception:
            pass


def _role_query(role: str, products: List[str]) -> str:
    base = "trade OR export OR import OR tariff OR customs OR logistics"
    role = (role or "").lower()
    extra = {
        "exporter": "export incentives OR shipping",
        "importer": "import duty OR customs clearance",
        "manufacturer": "manufacturing OR supply chain",
        "farmer": "agriculture export OR commodity",
        "cha": "customs OR clearance OR freight",
        "export_agent": "export OR buyers OR trade fair",
        "consultant": "trade policy OR FTA",
    }.get(role, "")
    prod = " OR ".join([p for p in (products or [])][:3])
    return " OR ".join([x for x in [base, extra, prod] if x])


# ---------------- Public endpoints ----------------
@router.get("/categories")
async def news_categories():
    return {"categories": CATEGORIES}


@router.get("/feed")
async def news_feed(country: str = Query(""), category: str = Query("All"),
                    limit: int = Query(24), authorization: Optional[str] = Header(default=None)):
    claims = await optional_user(authorization)
    personalized = False
    role = ""
    products: List[str] = []
    user_country = country

    if claims:
        personalized = True
        owner = claims.get("uid")
        pref = await db.user_prefs.find_one({"owner": owner})
        if pref:
            user_country = user_country or pref.get("country", "")
            role = pref.get("role", "")
        # profile products memory (brain)
        mem = await db.brain_user_memory.find_one({"owner": owner}) if "brain_user_memory" in await db.list_collection_names() else None
        if mem:
            products = mem.get("preferredProducts", []) or []

    query = _role_query(role, products) if personalized else "global trade OR export OR import OR tariff OR logistics OR business"
    cc = (user_country or "").strip()
    # 2-letter code guess for common inputs
    code_map = {"india": "in", "united states": "us", "usa": "us", "uae": "ae",
                "united arab emirates": "ae", "united kingdom": "gb", "uk": "gb",
                "singapore": "sg", "china": "cn", "germany": "de", "australia": "au"}
    cc_code = code_map.get(cc.lower(), cc.lower() if len(cc) == 2 else "")

    live = await _fetch_live(cc_code or None, query)
    admin = await _admin_news(cc or None)
    fallback = _normalise_curated() if len(live) + len(admin) < 4 else []

    # merge: featured admin first, then live, then remaining admin + fallback
    featured = [a for a in admin if a.get("featured")]
    rest_admin = [a for a in admin if not a.get("featured")]
    merged = featured + live + rest_admin + fallback

    if category and category != "All":
        merged = [m for m in merged if m.get("category") == category] or merged

    # de-dupe by id
    seen = set(); items = []
    for m in merged:
        if m["id"] in seen:
            continue
        seen.add(m["id"]); items.append(m)
    items = items[:max(1, min(limit, 40))]

    await _persist(items)
    return {"items": items, "personalized": personalized,
            "context": {"country": cc or "Global", "role": role or None},
            "live": bool(NEWSDATA_KEY), "categories": CATEGORIES}


@router.get("/{news_id}")
async def news_detail(news_id: str, authorization: Optional[str] = Header(default=None)):
    doc = await NEWS_ITEMS.find_one({"_id": news_id}) or await ADMIN_NEWS.find_one({"_id": news_id})
    if not doc:
        raise HTTPException(404, "News item not found")
    item = {k: v for k, v in doc.items() if k not in ("_id", "cachedAt")}
    item["id"] = news_id
    # personalized impact
    claims = await optional_user(authorization)
    ctx = ""
    if claims:
        pref = await db.user_prefs.find_one({"owner": claims.get("uid")})
        if pref:
            ctx = f"The reader is a {pref.get('role','trader')} based in {pref.get('country','their country')}."
    system = ("You are LeadNation Brain, a global trade analyst. In 90-130 words explain, in plain "
              "language, what a trade news item MEANS for an importer/exporter — concrete actions, "
              "risks and opportunities. Use markdown bullets. Do not invent specific figures.")
    prompt = (f"NEWS: {item.get('title','')}\n{item.get('excerpt','')}\n{item.get('body','')[:600]}\n\n"
              f"{ctx}\nExplain: 'What does this mean for my trade?'")
    impact = await llm_util.generate(system, prompt, session=f"news-{news_id}")
    item["impact"] = impact or ("- Monitor how this affects your lane's costs and timelines.\n"
                                "- Review duties, FTAs and freight for affected products.\n"
                                "- Ask the LeadNation Brain for a tailored action plan.")
    return item


# ---------------- Admin CRUD ----------------
class NewsIn(BaseModel):
    title: str
    excerpt: str = ""
    body: str = ""
    category: str = "Business"
    country: str = "Global"
    source: str = "LeadNation"
    image: str = ""
    url: str = ""
    date: str = ""
    featured: bool = False
    active: bool = True


@router.get("/admin/all")
async def admin_list(_: dict = Depends(require_admin)):
    docs = await ADMIN_NEWS.find({}).sort([("featured", -1), ("createdAt", -1)]).to_list(300)
    return {"items": [{**{k: v for k, v in d.items() if k != "_id"}, "id": d["_id"]} for d in docs]}


@router.post("/admin")
async def admin_create(body: NewsIn, _: dict = Depends(require_admin)):
    nid = _mk_id("admin", body.title + uuid.uuid4().hex)
    doc = {"_id": nid, **body.model_dump(), "createdAt": _iso(), "updatedAt": _iso()}
    await ADMIN_NEWS.insert_one(doc)
    return {"ok": True, "id": nid}


@router.put("/admin/{nid}")
async def admin_update(nid: str, body: NewsIn, _: dict = Depends(require_admin)):
    res = await ADMIN_NEWS.update_one({"_id": nid}, {"$set": {**body.model_dump(), "updatedAt": _iso()}})
    if not res.matched_count:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@router.delete("/admin/{nid}")
async def admin_delete(nid: str, _: dict = Depends(require_admin)):
    await ADMIN_NEWS.delete_one({"_id": nid})
    return {"ok": True}
