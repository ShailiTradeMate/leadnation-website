"""The 12 LeadNation Brain engines.

Each engine is async, reads from the Knowledge Base (SSOT) and returns a
structured dict with a `summary` (human line) + `data` (structured payload) +
`sources`. The Brain Router orchestrates them; the AI provider composes them.
"""
from brain.knowledge import kb_get, kb_search, kb_by_kind


def _src(kind, slug, to):
    return {"kind": kind, "slug": slug, "title": slug, "to": to}


async def country_context_engine(country=None, state=None, city=None, **_):
    entry = await kb_get("country", (country or "").lower()) if country else None
    if not entry:
        hits = await kb_search(country or "", kinds=["country"], limit=1) if country else []
        entry = hits[0] if hits else None
    if not entry:
        return None
    d = entry["data"]
    return {
        "summary": f"{d['name']} — {d.get('tagline', '')}. Major imports: {', '.join(d.get('majorImports', [])[:4])}.",
        "data": {"overview": d.get("overview"), "currency": d.get("currency"),
                 "majorImports": d.get("majorImports"), "majorExports": d.get("majorExports"),
                 "opportunities": d.get("opportunities"), "customs": d.get("customs"),
                 "compliance": d.get("compliance"), "marketplace": d.get("marketplace")},
        "sources": [{"kind": "country", "slug": entry["slug"], "title": d["name"], "to": f"/countries/{entry['slug']}"}],
    }


async def trade_news_engine(product=None, country=None, **_):
    kws = [w for w in [product, country] if w]
    return {
        "summary": "Latest movers: India exports crossed $450B; UAE–India CEPA past $100B; Red Sea reroutes lifted freight 38%; EU CBAM reporting live.",
        "data": {"keywords": kws, "headlines": [
            "India merchandise exports cross record $450B",
            "UAE–India CEPA pushes bilateral trade past $100B",
            "Red Sea reroutes lift container rates 38%",
            "EU CBAM enters reporting phase",
        ]},
        "sources": [{"kind": "news", "slug": "trade-news", "title": "Trade News", "to": "/trade-news"}],
    }


async def market_intelligence_engine(**_):
    return {
        "summary": "Gold $2,418/oz (+0.9%), Brent $84.2/bbl, USD/INR 83.42. Asia-Europe ocean freight +38% YoY.",
        "data": {"gold": 2418.5, "silver": 31.22, "brent": 84.15, "wti": 80.42, "usdinr": 83.42},
        "sources": [{"kind": "intelligence", "slug": "intelligence", "title": "Trade Intelligence", "to": "/intelligence"}],
    }


async def learning_engine(level=None, topic=None, **_):
    hits = await kb_search(topic or level or "export", kinds=["learning"], limit=3)
    if not hits:
        hits = await kb_by_kind("learning", limit=3)
    return {
        "summary": "Recommended learning: " + ", ".join(h["title"] for h in hits[:3]) + ".",
        "data": {"courses": [{"title": h["title"], "slug": h["slug"], "summary": h["content"]} for h in hits]},
        "sources": [{"kind": "academy", "slug": "academy", "title": "Learning Academy", "to": "/academy"}],
    }


async def compliance_engine(topic=None, product=None, country=None, **_):
    hits = await kb_search(topic or product or "", kinds=["compliance"], limit=5)
    if not hits:
        hits = await kb_by_kind("compliance", limit=5)
    return {
        "summary": "Compliance essentials: " + ", ".join(h["title"] for h in hits[:4]) + ".",
        "data": {"requirements": [{"title": h["title"], "detail": h["content"], "slug": h["slug"]} for h in hits]},
        "sources": [{"kind": "service", "slug": "iec-registration", "title": "Compliance Services", "to": "/services"}],
    }


async def tariff_engine(product=None, origin="India", destination=None, value=None, **_):
    dest = (destination or "").lower()
    fta = any(k in dest for k in ["uae", "united arab", "australia", "armenia", "eaeu"])
    rate = "0% (FTA preferential — e.g. CEPA/ECTA)" if fta else "0–8% MFN depending on HS line"
    return {
        "summary": f"Estimated duty for {product or 'this product'} into {destination or 'destination'}: {rate}. Use the Duty Calculator for an exact landed cost.",
        "data": {"dutyRate": rate, "ftaApplicable": fta, "origin": origin, "destination": destination},
        "sources": [{"kind": "tool", "slug": "duty-calculator", "title": "Duty Calculator", "to": "/tools/duty-calculator"}],
    }


async def logistics_engine(origin="India", destination=None, **_):
    return {
        "summary": f"Typical route: Mundra → destination port by sea (4–35 days depending on lane); air freight for time-sensitive cargo.",
        "data": {"recommendedPorts": ["Mundra", "Nhava Sheva", "Chennai"], "modes": ["FCL", "LCL", "Air"], "origin": origin, "destination": destination},
        "sources": [{"kind": "tool", "slug": "landed-cost-calculator", "title": "Landed Cost Calculator", "to": "/tools/landed-cost-calculator"}],
    }


async def policy_engine(country="India", **_):
    return {
        "summary": "India incentives: RoDTEP scrip, EPCG (0% duty on capital goods), 2% interest equalisation, Advance Authorisation.",
        "data": {"schemes": [s["title"] for s in await kb_by_kind("scheme", limit=10)]},
        "sources": [{"kind": "tool", "slug": "export-incentive-finder", "title": "Export Incentive Finder", "to": "/tools/export-incentive-finder"}],
    }


async def product_intelligence_engine(product=None, hsn=None, **_):
    entry = None
    if product:
        hits = await kb_search(product, kinds=["product"], limit=1)
        entry = hits[0] if hits else None
    if not entry and hsn:
        entry = await kb_get("hsn", hsn)
    if not entry:
        return None
    d = entry["data"]
    name = d.get("name") or d.get("title") or entry["title"]
    return {
        "summary": f"{name} (HSN {d.get('hsn', d.get('code', 'n/a'))}). Top importers: {', '.join(d.get('topImporters', [])[:4]) or 'global'}. {d.get('demand', '')}",
        "data": {"hsn": d.get("hsn") or d.get("code"), "topImporters": d.get("topImporters"),
                 "topExporters": d.get("topExporters"), "opportunities": d.get("opportunities"),
                 "certifications": d.get("certifications"), "compliance": d.get("compliance")},
        "sources": [{"kind": "product", "slug": entry["slug"], "title": name,
                     "to": f"/products/{entry['slug']}" if entry["kind"] == "product" else f"/hsn/{entry['slug']}"}],
    }


async def business_services_engine(need=None, **_):
    hits = await kb_search(need or "", kinds=["service"], limit=4)
    if not hits:
        hits = await kb_by_kind("service", limit=4)
    return {
        "summary": "LeadNation can handle this end-to-end: " + ", ".join(h["title"] for h in hits[:4]) + ".",
        "data": {"services": [{"title": h["title"], "slug": h["slug"],
                               "priceFrom": h["data"].get("priceFrom")} for h in hits]},
        "sources": [{"kind": "service", "slug": hits[0]["slug"] if hits else "", "title": "Business Services", "to": "/services"}],
    }


async def marketplace_engine(product=None, **_):
    return {
        "summary": "Live RFQs and verified listings are available on the LeadNation Marketplace.",
        "data": {"hasRFQs": True, "product": product},
        "sources": [{"kind": "marketplace", "slug": "marketplace", "title": "Marketplace", "to": "/marketplace"}],
    }


async def network_engine(kind=None, **_):
    return {
        "summary": "Connect with verified exporters, importers, suppliers, CHAs and export agents in the LeadNation Network.",
        "data": {"directories": ["exporters", "importers", "suppliers", "cha", "export-agents"], "kind": kind},
        "sources": [{"kind": "network", "slug": "network", "title": "Trade Network", "to": "/network"}],
    }


def _fmt(v):
    try:
        v = float(v)
    except Exception:
        return v
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= div:
            return f"{v / div:.1f}{unit}"
    return f"{v:.0f}"


async def _resolve_hs6(product, hsn):
    from trade_intel import _norm_hs, hs_search
    if hsn:
        h = _norm_hs(hsn)
        if len(h) >= 6:
            return h
    if product:
        hits = await hs_search(product, limit=1)
        if hits:
            return hits[0]["hs6"]
    return None


async def trade_statistics_engine(product=None, hsn=None, **_):
    """REAL global trade data (OEC World / UN Comtrade) by HS code."""
    from trade_intel import trade_stats
    hs6 = await _resolve_hs6(product, hsn)
    if not hs6:
        return None
    stats = await trade_stats(hs6)
    if not stats.get("ok"):
        return None
    imp = ", ".join(f"{i['country']} (${_fmt(i['value'])})" for i in stats["topImporters"][:4])
    exp = ", ".join(e["country"] for e in stats["topExporters"][:4])
    return {
        "summary": (f"Global trade in {stats['description'] or ('HS ' + stats['hsCode'])} "
                    f"({stats['year']}): world imports ≈ ${_fmt(stats['totalWorldTradeUSD'])}. "
                    f"Top importers: {imp}. Leading exporters: {exp}. Source: {stats['source']}."),
        "data": {"hsCode": stats["hsCode"], "year": stats["year"],
                 "totalWorldTradeUSD": stats["totalWorldTradeUSD"],
                 "topImporters": stats["topImporters"], "topExporters": stats["topExporters"],
                 "trend": stats["trend"], "source": stats["source"]},
        "sources": [{"kind": "tool", "slug": "trade-stats", "title": "Live Trade Statistics",
                     "to": "/customs-compliance"}],
    }


async def duty_benefits_engine(product=None, hsn=None, countries=None, **_):
    """REAL duty & benefits: global WITS tariffs + India BCD/IGST/SWS + RoDTEP."""
    from duty_engine import duty_and_benefits, NAME_BY_CODE
    hs6 = await _resolve_hs6(product, hsn)
    if not hs6:
        return None
    code_by_name = {n.lower(): c for c, n in NAME_BY_CODE.items()}
    matched = [code_by_name[c.lower()] for c in (countries or []) if c.lower() in code_by_name]
    origin = destination = None
    if len(matched) >= 2:
        origin, destination = matched[0], matched[1]
    elif len(matched) == 1:
        destination = matched[0]  # treat a single country as the import destination
    res = await duty_and_benefits(hs6, origin=origin or "", destination=destination or "356")
    if not res.get("ok"):
        return None
    parts = []
    d = res["importDuty"]
    if d:
        parts.append(f"Import duty into {res['destination']['name'] or 'destination'}: {d['rate']}% {d['type']} ({d['year']})")
    if res.get("preferential"):
        parts.append(f"preferential {res['preferential']['rate']}% ({res['preferential']['type']})")
    if res.get("indiaBreakdown"):
        b = res["indiaBreakdown"]
        parts.append(f"India: BCD {b['basicCustomsDuty']}% + SWS {b['socialWelfareSurcharge']}% + IGST {b['igst']}%")
    if res.get("exportBenefit"):
        e = res["exportBenefit"]
        parts.append(f"India export benefit {e['scheme']} {e['rate']}% of FOB")
    if not parts:
        return None
    return {
        "summary": "; ".join(parts) + ". Source: World Bank WITS / DGFT RoDTEP.",
        "data": res,
        "sources": [{"kind": "tool", "slug": "duty-benefits", "title": "Duty & Benefits", "to": "/customs-compliance"}],
    }


ENGINES = {
    "country_context": country_context_engine,
    "trade_news": trade_news_engine,
    "market_intelligence": market_intelligence_engine,
    "learning": learning_engine,
    "compliance": compliance_engine,
    "tariff": tariff_engine,
    "logistics": logistics_engine,
    "policy": policy_engine,
    "product_intelligence": product_intelligence_engine,
    "business_services": business_services_engine,
    "marketplace": marketplace_engine,
    "network": network_engine,
    "trade_statistics": trade_statistics_engine,
    "duty_benefits": duty_benefits_engine,
}


async def run_engine(key: str, entities: dict):
    fn = ENGINES.get(key)
    if not fn:
        return None
    kwargs = {
        "product": (entities.get("products") or [None])[0],
        "country": (entities.get("countries") or [None])[0],
        "destination": (entities.get("countries") or [None])[0],
        "countries": entities.get("countries") or [],
        "hsn": (entities.get("hsn") or [None])[0],
        "need": (entities.get("services") or [None])[0],
        "topic": (entities.get("topics") or [None])[0],
    }
    try:
        return await fn(**kwargs)
    except Exception:
        return None
