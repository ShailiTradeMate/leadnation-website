"""Knowledge Base — the Single Source of Truth (SSOT) for the LeadNation ecosystem.

Every domain (countries, products, HSN, corridors, industries, services, learning,
compliance, schemes, blogs, FAQs) is normalised into the `knowledge_base` collection.
The Brain consults this BEFORE any external source.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from core import db

KB = db.knowledge_base


def _now():
    return datetime.now(timezone.utc).isoformat()


def _entry(kind: str, slug: str, title: str, content: str, tags: List[str], data: dict, source: str = "leadnation"):
    text = (title + " " + content + " " + " ".join(tags)).lower()
    return {
        "id": f"{kind}:{slug}",
        "kind": kind,
        "slug": slug,
        "title": title,
        "content": content,
        "tags": tags,
        "data": data,
        "source": source,
        "_text": text,
        "updatedAt": _now(),
    }


def _curated_compliance():
    items = [
        ("iec", "IEC (Import Export Code)", "10-digit DGFT code, mandatory & one-time/lifetime for any cross-border trade. Apply via ANF-2A on the DGFT portal.", ["iec", "dgft", "registration", "compliance"]),
        ("gst", "GST Registration", "Mandatory above turnover threshold or for any exporter claiming input GST refund. Exports are zero-rated.", ["gst", "tax", "compliance", "registration"]),
        ("rcmc", "RCMC (Registration-cum-Membership Certificate)", "Issued by an Export Promotion Council; mandatory to claim DGFT export incentives like RoDTEP. Valid 5 years.", ["rcmc", "epc", "rodtep", "compliance"]),
        ("export-docs", "Export Documentation", "Core docs: Commercial Invoice, Packing List, Bill of Lading/AWB, Certificate of Origin, FTA certificate, inspection/health certificates, LC and insurance.", ["documents", "shipping", "customs", "compliance"]),
        ("customs", "Customs Clearance", "Filed via ICEGATE. AEO-certified shipments clear 60% faster. Classification, valuation and origin determine duty.", ["customs", "icegate", "aeo", "clearance"]),
    ]
    return [_entry("compliance", s, t, c, tags, {}) for (s, t, c, tags) in items]


def _curated_schemes():
    items = [
        ("rodtep", "RoDTEP Scheme", "Remission of Duties & Taxes on Exported Products — tradable scrip on ICEGATE, rates vary by HS line.", ["rodtep", "incentive", "scheme"]),
        ("epcg", "EPCG Scheme", "0% duty on capital goods against a 6x export obligation.", ["epcg", "incentive", "scheme"]),
        ("interest-equalisation", "Interest Equalisation Scheme", "2% interest subvention on pre/post-shipment credit (extra 2% for MSMEs).", ["msme", "finance", "scheme"]),
        ("advance-authorisation", "Advance Authorisation", "Duty-free import of inputs used in export production.", ["incentive", "scheme", "inputs"]),
    ]
    return [_entry("scheme", s, t, c, tags, {}) for (s, t, c, tags) in items]


async def seed_knowledge_base(force: bool = False):
    """Populate the KB from all domain sources. Idempotent."""
    if not force and await KB.count_documents({}) > 0:
        return {"seeded": False, "count": await KB.count_documents({})}

    # Lazy imports to avoid circular import at module load
    from reference import COUNTRIES, PRODUCTS  # noqa
    from engines import COUNTRY_PROFILES, ACADEMY
    from trade_tools import HSN_DB
    from content import PRODUCTS_DB, CORRIDOR_DB, INDUSTRY_DB, BLOG_DB
    from services import SERVICES_DB

    entries = []

    for slug, p in COUNTRY_PROFILES.items():
        entries.append(_entry("country", slug, p["name"],
                              p.get("overview", "") + " " + p.get("tagline", ""),
                              p.get("newsKeywords", []) + [p.get("code", "")], p))

    for slug, p in PRODUCTS_DB.items():
        entries.append(_entry("product", slug, p["name"],
                              p.get("overview", "") + " " + p.get("demand", ""),
                              [p.get("hsn", ""), p.get("category", "")], p))

    for code, h in HSN_DB.items():
        entries.append(_entry("hsn", code, f"HSN {code} · {h['title']}",
                              h.get("opportunities", "") + " " + h.get("customsNotes", ""),
                              [h.get("category", ""), "hsn", code], h))

    for slug, c in CORRIDOR_DB.items():
        entries.append(_entry("corridor", slug, f"{c['from']} → {c['to']}",
                              c.get("tagline", "") + " " + c.get("customsInfo", ""),
                              [c.get("fromCode", ""), c.get("toCode", ""), "corridor"], c))

    for slug, i in INDUSTRY_DB.items():
        entries.append(_entry("industry", slug, i["name"], i.get("overview", ""),
                              i.get("exports", []) + ["industry"], i))

    for slug, s in SERVICES_DB.items():
        entries.append(_entry("service", slug, s["name"],
                              s.get("overview", "") + " " + s.get("tagline", ""),
                              [s.get("category", ""), "service"], s))

    for b in BLOG_DB:
        entries.append(_entry("blog", b["slug"], b["title"], b.get("excerpt", ""),
                              [b.get("category", ""), "blog"], b))

    for level, courses in ACADEMY.items():
        for c in courses:
            entries.append(_entry("learning", c["slug"], c["title"], c.get("summary", ""),
                                  [level.lower(), "learning", "academy"], {**c, "level": level}))

    entries += _curated_compliance()
    entries += _curated_schemes()

    # upsert
    for e in entries:
        await KB.replace_one({"id": e["id"]}, e, upsert=True)

    logging.info("Knowledge base seeded with %d entries", len(entries))
    return {"seeded": True, "count": await KB.count_documents({})}


async def kb_search(query: str, kinds: Optional[List[str]] = None, limit: int = 20):
    q = (query or "").lower().strip()
    flt = {}
    if kinds:
        flt["kind"] = {"$in": kinds}
    if q:
        flt["_text"] = {"$regex": q.replace("(", "").replace(")", ""), "$options": "i"}
    cur = KB.find(flt, {"_id": 0, "_text": 0}).limit(limit)
    return await cur.to_list(limit)


async def kb_get(kind: str, slug: str):
    return await KB.find_one({"id": f"{kind}:{slug}"}, {"_id": 0, "_text": 0})


async def kb_by_kind(kind: str, limit: int = 100):
    return await KB.find({"kind": kind}, {"_id": 0, "_text": 0}).limit(limit).to_list(limit)


async def kb_stats():
    total = await KB.count_documents({})
    kinds = await KB.aggregate([{"$group": {"_id": "$kind", "count": {"$sum": 1}}}]).to_list(100)
    return {"total": total, "byKind": {k["_id"]: k["count"] for k in kinds}}
