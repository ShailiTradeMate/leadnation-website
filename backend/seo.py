"""SEO/GEO surface: dynamic sitemap (auto-includes current + future programmatic
pages) and IndexNow instant-indexing (Bing / Yandex).

The sitemap is generated from the SAME in-code data the pages render from, so any
new country / product / corridor / industry / HSN / blog / academy page is picked
up automatically on the next crawl — no manual sitemap edits."""
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response, PlainTextResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["seo"])

SITE = "https://leadnation.app"

# IndexNow key (must match the file served at /{key}.txt on the frontend).
INDEXNOW_KEY = "a3f5c9e21b7d4680b2f1c8e4d9a70f36"


def _static_routes():
    return [
        ("/", "daily", "1.0"),
        ("/customs-compliance", "weekly", "0.9"),
        ("/product-info", "weekly", "0.9"),
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
    return routes


def all_public_urls():
    seen, out = set(), []
    for loc, freq, pri in _static_routes() + _dynamic_routes():
        if loc in seen:
            continue
        seen.add(loc)
        out.append((loc, freq, pri))
    return out


@router.get("/sitemap.xml")
async def sitemap_xml():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = "".join(
        f"<url><loc>{SITE}{loc}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>"
        for loc, freq, pri in all_public_urls())
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f"{rows}</urlset>")
    return Response(content=xml, media_type="application/xml")


async def indexnow_submit(urls: list) -> dict:
    """Notify Bing / Yandex (and IndexNow-participating engines) of new/changed URLs."""
    urls = [u if u.startswith("http") else f"{SITE}{u}" for u in (urls or []) if u]
    if not urls:
        return {"ok": False, "reason": "no urls"}
    payload = {"host": "leadnation.app", "key": INDEXNOW_KEY,
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
