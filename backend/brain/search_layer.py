"""Universal Search — Brain Search.

Searches across all LeadNation domains and ranks by relevance.
Search priority (per product spec):
  1. LeadNation Knowledge Base (SSOT)  — countries, products, HSN, corridors,
     industries, services, blog, learning, compliance, schemes, FAQs
  2. LeadNation Database (CMS collections)
  3. LeadNation Trade Engines + Network (suppliers / buyers / tools)
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
    "scheme": "/tools/export-incentive-finder", "faq": "/services/{service}",
}

KIND_WEIGHT = {
    "product": 6, "country": 6, "hsn": 6, "service": 5, "corridor": 5,
    "industry": 4, "compliance": 4, "scheme": 3, "blog": 3, "learning": 3,
    "faq": 3, "supplier": 4, "buyer": 4, "tool": 2,
}


def _score(query, label, kind):
    q = (query or "").lower().strip()
    lab = (label or "").lower()
    base = KIND_WEIGHT.get(kind, 1)
    if not q:
        return base
    if lab == q:
        return base + 10
    if lab.startswith(q):
        return base + 6
    if q in lab:
        return base + 3
    # token overlap
    overlap = len(set(q.split()) & set(lab.split()))
    return base + overlap


async def universal_search(query: str, limit: int = 30):
    query = (query or "").strip()
    results, layers = [], []

    # Priority 1 — Knowledge Base
    kb_hits = await kb_search(query, limit=60)
    for h in kb_hits:
        path_tpl = KIND_TO_PATH.get(h["kind"], "/search")
        path = path_tpl.format(slug=h["slug"], service=(h.get("data") or {}).get("service", ""))
        results.append({"type": h["kind"], "label": h["title"], "to": path,
                        "sub": (h.get("content") or "")[:120], "source": "knowledge_base"})
    layers.append({"layer": 1, "name": "Knowledge Base", "hits": len(kb_hits), "used": True})

    # Priority 2 — Database (CMS, admin-authored)
    db_hits = 0
    if query:
        try:
            cur = db.cms_blog.find({"title": {"$regex": query, "$options": "i"}},
                                   {"_id": 0, "slug": 1, "title": 1}).limit(5)
            async for d in cur:
                results.append({"type": "blog", "label": d.get("title", ""),
                                "to": f"/blog/{d.get('slug', '')}", "source": "database"})
                db_hits += 1
        except Exception:
            pass
    layers.append({"layer": 2, "name": "Database (CMS)", "hits": db_hits, "used": db_hits > 0})

    # Priority 3 — Engines + Network (suppliers / buyers / tools)
    eng_hits = 0
    from trade_tools import SAMPLE_SUPPLIERS, SAMPLE_BUYERS
    ql = query.lower()
    for s in SAMPLE_SUPPLIERS:
        if not query or ql in s["company"].lower() or ql in s.get("products", "").lower() or ql in s.get("category", "").lower():
            results.append({"type": "supplier", "label": s["company"], "to": "/suppliers",
                            "sub": f"{s.get('category','')} · {s.get('city','')}", "source": "engines"})
            eng_hits += 1
    for b in SAMPLE_BUYERS:
        if query and ql in b["company"].lower():
            results.append({"type": "buyer", "label": b["company"], "to": "/network",
                            "sub": f"Buyer · {b.get('city','')}", "source": "engines"})
            eng_hits += 1
    tools = [("HSN Finder", "/tools/hsn-finder"), ("Duty Calculator", "/tools/duty-calculator"),
             ("Find Buyers", "/tools/find-buyers"), ("Export Readiness", "/tools/export-readiness"),
             ("LeadNation Brain", "/brain")]
    for label, to in tools:
        if not query or ql in label.lower():
            results.append({"type": "tool", "label": label, "to": to, "source": "engines"})
            eng_hits += 1
    layers.append({"layer": 3, "name": "Trade Engines & Network", "hits": eng_hits, "used": eng_hits > 0})

    # Priority 4 & 5 — external (architecture only)
    layers.append({"layer": 4, "name": "Approved External APIs", "hits": 0, "used": False, "enabled": False})
    layers.append({"layer": 5, "name": "Public Web Search", "hits": 0, "used": False, "enabled": False,
                   "note": "Future architecture only — no scraping."})

    # de-dup + rank
    seen, deduped = set(), []
    for r in results:
        k = (r["type"], r["to"], r["label"])
        if k in seen:
            continue
        seen.add(k)
        r["_score"] = _score(query, r["label"], r["type"])
        deduped.append(r)
    deduped.sort(key=lambda r: -r["_score"])
    for r in deduped:
        r.pop("_score", None)

    return {"query": query, "total": len(deduped), "results": deduped[:limit],
            "searchLayers": layers}
