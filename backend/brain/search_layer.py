"""Universal Search + Google Search Integration Layer (architecture only).

Search priority (per product spec):
  1. LeadNation Knowledge Base (SSOT)
  2. LeadNation Database (CMS collections)
  3. LeadNation Trade Engines
  4. Approved external APIs   (stub — disabled)
  5. Public web search        (stub — disabled, NO scraping)
"""
from core import db
from brain.knowledge import kb_search

KIND_TO_PATH = {
    "country": "/countries/{slug}", "product": "/products/{slug}",
    "hsn": "/hsn/{slug}", "corridor": "/corridors/{slug}",
    "industry": "/industries/{slug}", "service": "/services/{slug}",
    "blog": "/blog/{slug}", "learning": "/academy", "compliance": "/services",
    "scheme": "/tools/export-incentive-finder",
}


async def universal_search(query: str, limit: int = 25):
    query = (query or "").strip()
    results, layers = [], []

    # Priority 1 — Knowledge Base
    kb_hits = await kb_search(query, limit=limit)
    for h in kb_hits:
        path = KIND_TO_PATH.get(h["kind"], "/search").format(slug=h["slug"])
        results.append({"type": h["kind"], "label": h["title"], "to": path,
                        "sub": (h.get("content") or "")[:120], "source": "knowledge_base"})
    layers.append({"layer": 1, "name": "Knowledge Base", "hits": len(kb_hits), "used": True})

    # Priority 2 — Database (CMS collections, e.g. admin-authored content)
    db_hits = 0
    if query:
        try:
            cur = db.cms_blog.find({"title": {"$regex": query, "$options": "i"}}, {"_id": 0, "slug": 1, "title": 1}).limit(5)
            async for d in cur:
                results.append({"type": "blog", "label": d.get("title", ""),
                                "to": f"/blog/{d.get('slug', '')}", "source": "database"})
                db_hits += 1
        except Exception:
            pass
    layers.append({"layer": 2, "name": "Database (CMS)", "hits": db_hits, "used": db_hits > 0})

    # Priority 3 — Trade Engines (tools registry)
    tools = [("HSN Finder", "/tools/hsn-finder"), ("Duty Calculator", "/tools/duty-calculator"),
             ("Find Buyers", "/tools/find-buyers"), ("Export Readiness", "/tools/export-readiness")]
    eng_hits = 0
    for label, to in tools:
        if not query or query.lower() in label.lower():
            results.append({"type": "tool", "label": label, "to": to, "source": "engines"})
            eng_hits += 1
    layers.append({"layer": 3, "name": "Trade Engines", "hits": eng_hits, "used": eng_hits > 0})

    # Priority 4 & 5 — external APIs + public web (architecture only)
    layers.append({"layer": 4, "name": "Approved External APIs", "hits": 0, "used": False, "enabled": False})
    layers.append({"layer": 5, "name": "Public Web Search", "hits": 0, "used": False, "enabled": False,
                   "note": "Future architecture only — no scraping."})

    # de-dup
    seen, deduped = set(), []
    for r in results:
        k = (r["type"], r["to"])
        if k not in seen:
            seen.add(k)
            deduped.append(r)

    return {"query": query, "total": len(deduped), "results": deduped[:limit],
            "searchLayers": layers}
