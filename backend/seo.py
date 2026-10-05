"""SEO/GEO surface: dynamic sitemap (auto-includes current + future programmatic
pages) and IndexNow instant-indexing (Bing / Yandex).

The sitemap is generated from the SAME in-code data the pages render from, so any
new country / product / corridor / industry / HSN / blog / academy page is picked
up automatically on the next crawl — no manual sitemap edits."""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response, PlainTextResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["seo"])

SITE = "https://vametra.com"

# IndexNow key (must match the file served at /{key}.txt on the frontend).
INDEXNOW_KEY = "a3f5c9e21b7d4680b2f1c8e4d9a70f36"

# CMS collection -> public URL prefix + hub page, used by the auto-ping.
CMS_URL_MAP = {
    "countries": ("/countries/", "/countries"),
    "products": ("/products/", "/products"),
    "corridors": ("/corridors/", "/corridors"),
    "industries": ("/industries/", "/industries"),
    "hsn_codes": ("/hsn/", "/tools/hsn-finder"),
    "blog": ("/blog/", "/blog"),
}


def _static_routes():
    return [
        ("/", "daily", "1.0"),
        ("/customs-compliance", "weekly", "0.9"),
        ("/expo", "daily", "0.8"),
        ("/trade-news", "daily", "0.8"),
        ("/contact", "monthly", "0.6"),
        ("/tools", "weekly", "1.0"),
        ("/tools/duty-calculator", "weekly", "1.0"),
        ("/tools/hsn-finder", "weekly", "1.0"),
        ("/tools/landed-cost-calculator", "weekly", "0.9"),
        ("/tools/export-incentive-finder", "weekly", "0.9"),
        ("/tools/product-research", "weekly", "0.9"),
        ("/tools/find-buyers", "weekly", "1.0"),
        ("/tools/export-readiness", "weekly", "0.9"),
        ("/ai-assistant", "weekly", "0.95"),
        ("/brain", "weekly", "0.95"),
        ("/intelligence", "daily", "0.9"),
        ("/academy", "weekly", "0.9"),
        ("/countries", "weekly", "0.9"),
        ("/products", "weekly", "0.9"),
        ("/corridors", "weekly", "0.9"),
        ("/industries", "weekly", "0.8"),
        ("/buyers", "daily", "0.9"),
        ("/blog", "daily", "0.8"),
        ("/pricing", "monthly", "0.7"),
        ("/services", "weekly", "0.7"),
        ("/marketplace", "weekly", "0.7"),
        ("/network", "weekly", "0.7"),
        ("/legal/privacy", "yearly", "0.3"),
        ("/legal/terms", "yearly", "0.3"),
        ("/legal/cookies", "yearly", "0.3"),
        ("/legal/disclaimer", "yearly", "0.3"),
        ("/legal/refund", "yearly", "0.3"),
    ]


def _dynamic_routes():
    """All data-driven programmatic pages, pulled live from the app's data."""
    routes = []
    try:
        import engines
        for slug in getattr(engines, "COUNTRY_PROFILES", {}).keys():
            routes.append((f"/countries/{slug}", "weekly", "0.95"))
        ac = getattr(engines, "ACADEMY", {})
        for _lvl, items in (ac.items() if isinstance(ac, dict) else []):
            for it in (items or []):
                s = it.get("slug") if isinstance(it, dict) else it
                if s:
                    routes.append((f"/academy/{s}", "weekly", "0.85"))
    except Exception as exc:
        logger.warning("sitemap engines source: %s", exc)
    try:
        import content
        for slug in getattr(content, "PRODUCTS_DB", {}).keys():
            routes.append((f"/products/{slug}", "weekly", "0.95"))
        for slug in getattr(content, "CORRIDOR_DB", {}).keys():
            routes.append((f"/corridors/{slug}", "weekly", "0.95"))
        for slug in getattr(content, "INDUSTRY_DB", {}).keys():
            routes.append((f"/industries/{slug}", "weekly", "0.85"))
        for b in getattr(content, "BLOG_DB", []):
            s = b.get("slug") if isinstance(b, dict) else b
            if s:
                routes.append((f"/blog/{s}", "weekly", "0.85"))
    except Exception as exc:
        logger.warning("sitemap content source: %s", exc)
    try:
        import trade_tools
        for code in getattr(trade_tools, "HSN_DB", {}).keys():
            routes.append((f"/hsn/{code}", "weekly", "0.9"))
    except Exception as exc:
        logger.warning("sitemap trade_tools source: %s", exc)
    try:
        import services as services_mod
        for slug in getattr(services_mod, "SERVICES_DB", {}).keys():
            routes.append((f"/services/{slug}", "monthly", "0.8"))
    except Exception as exc:
        logger.warning("sitemap services source: %s", exc)
    return routes


async def _event_routes():
    """Live expo listings — each published event has a public /expo/{id} page."""
    try:
        from event_listings import EVENTS
        rows = await EVENTS.find({"status": "published"}, {"_id": 1}).to_list(2000)
        return [(f"/expo/{r['_id']}", "weekly", "0.7") for r in rows]
    except Exception as exc:
        logger.warning("sitemap expo source: %s", exc)
        return []


def all_public_urls():
    seen, out = set(), []
    for loc, freq, pri in _static_routes() + _dynamic_routes():
        if loc in seen:
            continue
        seen.add(loc)
        out.append((loc, freq, pri))
    return out


async def _lastmod_map():
    """Real per-URL change dates recorded by the auto-ping (Google trusts honest lastmod)."""
    try:
        from core import db
        rows = await db.seo_lastmod.find({}, {"_id": 0}).to_list(5000)
        return {r["path"]: r["lastmod"] for r in rows if r.get("path") and r.get("lastmod")}
    except Exception as exc:
        logger.warning("lastmod lookup: %s", exc)
        return {}


@router.get("/sitemap.xml")
async def sitemap_xml():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lastmods = await _lastmod_map()
    urls = all_public_urls() + await _event_routes()
    rows = "".join(
        f"<url><loc>{SITE}{loc}</loc><lastmod>{lastmods.get(loc, today)}</lastmod>"
        f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>"
        for loc, freq, pri in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f"{rows}</urlset>")
    return Response(content=xml, media_type="application/xml")


async def indexnow_submit(urls: list) -> dict:
    """Notify Bing / Yandex (and IndexNow-participating engines) of new/changed URLs."""
    urls = [u if u.startswith("http") else f"{SITE}{u}" for u in (urls or []) if u]
    if not urls:
        return {"ok": False, "reason": "no urls"}
    payload = {"host": "vametra.com", "key": INDEXNOW_KEY,
               "keyLocation": f"{SITE}/{INDEXNOW_KEY}.txt", "urlList": urls[:10000]}
    try:
        async with httpx.AsyncClient(timeout=20) as cx:
            r = await cx.post("https://api.indexnow.org/indexnow", json=payload,
                              headers={"Content-Type": "application/json"})
        return {"ok": r.status_code in (200, 202), "status": r.status_code, "count": len(urls)}
    except Exception as exc:
        logger.warning("IndexNow submit failed: %s", exc)
        return {"ok": False, "reason": str(exc)}


@router.post("/seo/indexnow")
async def seo_indexnow(body: dict = None, x_admin_token: str = Header(default=None)):
    """Admin: push URLs to IndexNow. Body {"urls": [...]}; empty => key marketing pages."""
    import os
    if x_admin_token != os.environ.get("ADMIN_TOKEN", "leadnation-admin-2026"):
        raise HTTPException(status_code=403, detail="admin only")
    urls = (body or {}).get("urls") or [loc for loc, _f, _p in _static_routes()]
    return await indexnow_submit(urls)


async def _ping_and_log(paths: list, source: str):
    """Record the change date, submit to IndexNow, keep an audit row."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        from core import db
        for p in paths:
            await db.seo_lastmod.update_one({"path": p}, {"$set": {"path": p, "lastmod": today}}, upsert=True)
        result = await indexnow_submit(paths)
        await db.seo_pings.insert_one({"source": source, "paths": paths, "result": result,
                                       "at": datetime.now(timezone.utc).isoformat()})
        logger.info("IndexNow auto-ping [%s] %s -> %s", source, len(paths), result)
    except Exception as exc:
        logger.warning("auto-ping failed [%s]: %s", source, exc)


def notify_content_change(paths, source: str = "cms"):
    """Fire-and-forget: tell Bing/Yandex instantly and stamp lastmod for Google's next crawl.

    Never blocks or breaks the caller — scheduled on the running loop."""
    paths = sorted({p for p in (paths or []) if p and p.startswith("/")})
    if not paths:
        return
    try:
        asyncio.get_running_loop().create_task(_ping_and_log(paths, source))
    except RuntimeError:
        logger.warning("auto-ping skipped (no running loop): %s", source)


def cms_paths(collection: str, slug: str) -> list:
    """Detail page + its hub page for a CMS collection item."""
    prefix, hub = CMS_URL_MAP.get(collection, (None, None))
    if not prefix:
        return []
    return ([f"{prefix}{slug}"] if slug else []) + [hub]


@router.get("/seo/ping-log")
async def seo_ping_log(limit: int = 50, x_admin_token: str = Header(default=None)):
    """Admin: recent auto-ping activity (what was pushed, when, and the engine response)."""
    import os
    if x_admin_token != os.environ.get("ADMIN_TOKEN", "leadnation-admin-2026"):
        raise HTTPException(status_code=403, detail="admin only")
    from core import db
    rows = await db.seo_pings.find({}, {"_id": 0}).sort("at", -1).to_list(min(limit, 200))
    return {"count": len(rows), "pings": rows}


async def weekly_full_sweep():
    """Safety net: re-announce every public URL weekly so nothing is ever missed."""
    paths = [loc for loc, _f, _p in all_public_urls()] + [loc for loc, _f, _p in await _event_routes()]
    result = await indexnow_submit(paths)
    try:
        from core import db
        await db.seo_pings.insert_one({"source": "weekly-sweep", "paths": [f"{len(paths)} urls"],
                                       "result": result, "at": datetime.now(timezone.utc).isoformat()})
    except Exception:
        pass
    logger.info("IndexNow weekly sweep: %s urls -> %s", len(paths), result)
    return result


_seo_sched = None


def start_seo_scheduler():
    """Weekly IndexNow sweep (Mondays 01:10 UTC) + one sweep 3 min after boot."""
    global _seo_sched
    if _seo_sched:
        return
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from datetime import timedelta
    _seo_sched = AsyncIOScheduler(timezone="UTC")
    _seo_sched.add_job(weekly_full_sweep, CronTrigger(day_of_week="mon", hour=1, minute=10),
                       id="indexnow-weekly", replace_existing=True)
    _seo_sched.add_job(weekly_full_sweep,
                       DateTrigger(run_date=datetime.now(timezone.utc) + timedelta(minutes=3)),
                       id="indexnow-boot", replace_existing=True)
    _seo_sched.start()
    logger.info("IndexNow sweep scheduler started (weekly + boot warm-up)")
