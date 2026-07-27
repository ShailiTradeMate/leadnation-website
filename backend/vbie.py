"""VBIE — Verified Buyer Intelligence Engine.

This module is the FIRST production slice of the LeadNation Global Trade
Intelligence Server. Per the locked architecture, the Website/Command Center
backend is the SINGLE owner of the buyer/supplier entity graph — the mobile app
and any future client consume these same `/api/*` endpoints. The DigitalOcean
backend remains identity-only (users, customer_id, onboarding, company_profiles,
members_bridge) and MUST NOT write into this buyer graph.

Design principles (from the approved VBIE research program):
  • Entity-centric: every company is a canonical `entity` keyed by an immutable
    GEID (`LN-<type>-<ULID>`), shared with the identity spine.
  • Evidence-first: every buyer carries `provenance[]` citing the source of each
    fact; nothing is shown without a source.
  • Explainable trust: a deterministic Trust v0 score (0-100 + band) computed
    from source reliability + verification signals + freshness. No black box.

Collections (all ADDITIVE on the shared `leadnation` DB):
  • `entities`      — canonical company graph (VBIE writes entity_type=buyer here)
  • `vbie_sources`  — the source registry (reliability tiers)
  • `buyer_claims`  — "claim this company" requests (lead capture)

The seed set is clearly labelled illustrative directory data (`sample: True`) with
honest, source-typed provenance — it demonstrates the full engine while real
official/free connectors are built. It NEVER fabricates specific shipment
figures against named real firms.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from core import db

router = APIRouter(prefix="/buyers")
logger = logging.getLogger(__name__)

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Source reliability by tier (0-100). gov > official > licensed > directory.
TIER_RELIABILITY = {"gov": 100, "official": 85, "licensed": 75, "directory": 55}

TRUST_BANDS = [
    (80, "Verified", "emerald"),
    (65, "Trusted", "cyan"),
    (45, "Emerging", "amber"),
    (0, "Unverified", "slate"),
]


# ─────────────────────────── source registry ────────────────────────────────
SOURCES_SEED = [
    {"_id": "un_comtrade", "name": "UN Comtrade", "tier": "official", "category": "trade_stats", "url": "https://comtrade.un.org", "attribution": "United Nations Comtrade Database"},
    {"_id": "trade_gov_csl", "name": "US Trade.gov Consolidated Screening List", "tier": "gov", "category": "sanctions", "url": "https://www.trade.gov/consolidated-screening-list", "attribution": "US Department of Commerce"},
    {"_id": "uk_companies_house", "name": "UK Companies House", "tier": "gov", "category": "registry", "url": "https://find-and-update.company-information.service.gov.uk", "attribution": "UK Companies House (Open Government Licence)"},
    {"_id": "sam_gov", "name": "SAM.gov", "tier": "gov", "category": "registry", "url": "https://sam.gov", "attribution": "US General Services Administration"},
    {"_id": "eu_ted", "name": "EU Tenders Electronic Daily (TED)", "tier": "gov", "category": "tenders", "url": "https://ted.europa.eu", "attribution": "Publications Office of the European Union"},
    {"_id": "vies", "name": "EU VIES VAT Validation", "tier": "gov", "category": "tax_id", "url": "https://ec.europa.eu/taxation_customs/vies", "attribution": "European Commission"},
    {"_id": "abr_australia", "name": "Australian Business Register", "tier": "gov", "category": "registry", "url": "https://abr.business.gov.au", "attribution": "Australian Government"},
    {"_id": "company_website", "name": "Company Website", "tier": "directory", "category": "website", "url": "", "attribution": "Company-published information"},
    {"_id": "trade_fair_exhibitor", "name": "Trade Fair Exhibitor Directory", "tier": "directory", "category": "exhibitor", "url": "", "attribution": "Published exhibitor list"},
    {"_id": "epc_directory", "name": "Export Promotion Council Directory", "tier": "official", "category": "association", "url": "", "attribution": "Export Promotion Council member directory"},
]
_SOURCE_BY_ID = {s["_id"]: s for s in SOURCES_SEED}


def _now():
    return datetime.now(timezone.utc)


def _iso(v):
    return v.isoformat() if isinstance(v, datetime) else v


def _stable_geid(slug: str) -> str:
    """Deterministic GEID from a slug so reseeds upsert instead of duplicating.
    Keeps the frozen `LN-<type>-<ULID-shaped>` format (26 Crockford chars)."""
    h = hashlib.sha1(slug.encode()).digest()
    num = int.from_bytes(h, "big")
    chars = ""
    for _ in range(26):
        chars = _CROCKFORD[num % 32] + chars
        num //= 32
    return f"LN-buyer-{chars}"


def _band(score: int):
    for threshold, label, color in TRUST_BANDS:
        if score >= threshold:
            return label, color
    return "Unverified", "slate"


def compute_trust(provenance: list, signals: dict) -> dict:
    """Deterministic, explainable Trust v0. Returns score + band + factor breakdown."""
    factors = []
    reliabilities = [TIER_RELIABILITY.get(_SOURCE_BY_ID.get(p.get("source_id"), {}).get("tier", "directory"), 55)
                     for p in provenance] or [40]
    base = max(reliabilities)
    best_src = max(provenance, key=lambda p: TIER_RELIABILITY.get(_SOURCE_BY_ID.get(p.get("source_id"), {}).get("tier", "directory"), 55), default=None) if provenance else None
    factors.append({"label": "Source reliability", "points": base,
                    "detail": f"Best source: {_SOURCE_BY_ID.get(best_src.get('source_id'), {}).get('name', 'directory') if best_src else 'directory'}"})

    score = base * 0.7  # source reliability is 70% of the base
    if signals.get("website_verified"):
        score += 6; factors.append({"label": "Website verified", "points": 6, "detail": "Public company website resolves"})
    if signals.get("vat_validated"):
        score += 8; factors.append({"label": "Tax/VAT ID validated", "points": 8, "detail": "Government tax-ID registry match"})
    if signals.get("registry_listed"):
        score += 6; factors.append({"label": "Company registry listed", "points": 6, "detail": "Found in official company registry"})
    if signals.get("sanctions_clear"):
        score += 10; factors.append({"label": "Sanctions screened", "points": 10, "detail": "Cleared against trade.gov CSL"})

    # freshness: penalise stale provenance
    caps = [p.get("captured_at") for p in provenance if p.get("captured_at")]
    if caps:
        try:
            oldest = min(datetime.fromisoformat(c) if isinstance(c, str) else c for c in caps)
            if oldest.tzinfo is None:
                oldest = oldest.replace(tzinfo=timezone.utc)
            age_days = (_now() - oldest).days
            if age_days > 365:
                score -= 8; factors.append({"label": "Freshness", "points": -8, "detail": "Some evidence older than 12 months"})
            else:
                factors.append({"label": "Freshness", "points": 0, "detail": "Evidence within 12 months"})
        except Exception:
            pass

    score = max(0, min(100, round(score)))
    label, color = _band(score)
    return {"score": score, "band": label, "color": color, "factors": factors, "updated_at": _iso(_now())}


# ───────────────────────────── seed dataset ─────────────────────────────────
def _prov(source_id: str, field: str, note: str = "", url: str = ""):
    s = _SOURCE_BY_ID.get(source_id, {})
    return {"field": field, "source_id": source_id, "source_name": s.get("name", source_id),
            "source_tier": s.get("tier", "directory"), "source_url": url or s.get("url", ""),
            "attribution": s.get("attribution", ""), "captured_at": _iso(_now()), "note": note}


# Illustrative directory seed. `sample: True` + honest source-typed provenance.
# Companies are representative importers/distributors by sector & market — NOT an
# assertion of confidential shipment activity against any specific named firm.
_BUYERS_SEED = [
    {"slug": "atlantic-grain-foods-usa", "legal_name": "Atlantic Grain & Foods LLC", "country": "US", "country_name": "United States", "city": "Newark, NJ",
     "sector": "Agri & Foods", "products": ["Basmati Rice", "Pulses", "Spices"], "hs_families": ["1006", "0713", "0904"], "corridors": ["IN-US"], "size": "Mid-market distributor",
     "website": "https://example-atlanticgrain.com", "signals": {"website_verified": True, "sanctions_clear": True, "registry_listed": True},
     "prov": [("company_website", "profile"), ("sam_gov", "registry_listed"), ("trade_gov_csl", "sanctions_clear")]},
    {"slug": "emirates-food-trading-uae", "legal_name": "Emirates Food Trading FZE", "country": "AE", "country_name": "United Arab Emirates", "city": "Dubai",
     "sector": "Agri & Foods", "products": ["Basmati Rice", "Tea", "Sugar"], "hs_families": ["1006", "0902", "1701"], "corridors": ["IN-AE"], "size": "Regional wholesaler",
     "website": "https://example-emiratesfood.ae", "signals": {"website_verified": True, "registry_listed": True},
     "prov": [("company_website", "profile"), ("trade_fair_exhibitor", "products")]},
    {"slug": "britannia-textiles-uk", "legal_name": "Britannia Textiles Ltd", "country": "GB", "country_name": "United Kingdom", "city": "Manchester",
     "sector": "Textiles & Apparel", "products": ["Cotton Fabric", "Home Textiles"], "hs_families": ["5208", "6302"], "corridors": ["IN-GB"], "size": "Importer & retailer",
     "website": "https://example-britannia-textiles.co.uk", "signals": {"website_verified": True, "vat_validated": True, "registry_listed": True, "sanctions_clear": True},
     "prov": [("uk_companies_house", "registry_listed"), ("vies", "vat_validated"), ("company_website", "profile"), ("trade_gov_csl", "sanctions_clear")]},
    {"slug": "rhein-pharma-import-de", "legal_name": "Rhein Pharma Import GmbH", "country": "DE", "country_name": "Germany", "city": "Frankfurt",
     "sector": "Pharma & Chemicals", "products": ["Generic APIs", "Excipients"], "hs_families": ["2941", "3003"], "corridors": ["IN-DE"], "size": "Pharma distributor",
     "website": "https://example-rheinpharma.de", "signals": {"website_verified": True, "vat_validated": True, "sanctions_clear": True},
     "prov": [("vies", "vat_validated"), ("company_website", "profile"), ("eu_ted", "tenders"), ("trade_gov_csl", "sanctions_clear")]},
    {"slug": "southern-cross-spices-au", "legal_name": "Southern Cross Spices Pty Ltd", "country": "AU", "country_name": "Australia", "city": "Melbourne",
     "sector": "Agri & Foods", "products": ["Spices", "Turmeric", "Chilli"], "hs_families": ["0904", "0910"], "corridors": ["IN-AU"], "size": "Specialty importer",
     "website": "https://example-southerncross.au", "signals": {"website_verified": True, "registry_listed": True},
     "prov": [("abr_australia", "registry_listed"), ("company_website", "profile")]},
    {"slug": "liberty-home-goods-usa", "legal_name": "Liberty Home Goods Inc", "country": "US", "country_name": "United States", "city": "Los Angeles, CA",
     "sector": "Home & Handicrafts", "products": ["Home Décor", "Brassware", "Rugs"], "hs_families": ["6913", "8306", "5701"], "corridors": ["IN-US"], "size": "E-commerce importer",
     "website": "https://example-libertyhome.com", "signals": {"website_verified": True, "sanctions_clear": True},
     "prov": [("company_website", "profile"), ("trade_gov_csl", "sanctions_clear"), ("trade_fair_exhibitor", "products")]},
    {"slug": "gulf-steel-metals-uae", "legal_name": "Gulf Steel & Metals LLC", "country": "AE", "country_name": "United Arab Emirates", "city": "Sharjah",
     "sector": "Metals & Engineering", "products": ["Steel Fasteners", "Pipe Fittings"], "hs_families": ["7318", "7307"], "corridors": ["IN-AE"], "size": "Industrial buyer",
     "website": "https://example-gulfsteel.ae", "signals": {"registry_listed": True},
     "prov": [("epc_directory", "profile"), ("trade_fair_exhibitor", "products")]},
    {"slug": "nordic-organics-de", "legal_name": "Nordic Organics Handels GmbH", "country": "DE", "country_name": "Germany", "city": "Hamburg",
     "sector": "Agri & Foods", "products": ["Organic Rice", "Millets", "Superfoods"], "hs_families": ["1006", "1008"], "corridors": ["IN-DE"], "size": "Organic distributor",
     "website": "https://example-nordicorganics.de", "signals": {"website_verified": True, "vat_validated": True},
     "prov": [("vies", "vat_validated"), ("company_website", "profile")]},
    {"slug": "thames-pharma-uk", "legal_name": "Thames Pharma Distribution Ltd", "country": "GB", "country_name": "United Kingdom", "city": "London",
     "sector": "Pharma & Chemicals", "products": ["Generics", "Nutraceuticals"], "hs_families": ["3004", "2106"], "corridors": ["IN-GB"], "size": "Distributor",
     "website": "https://example-thamespharma.co.uk", "signals": {"registry_listed": True, "sanctions_clear": True},
     "prov": [("uk_companies_house", "registry_listed"), ("trade_gov_csl", "sanctions_clear")]},
    {"slug": "pacific-leather-au", "legal_name": "Pacific Leather Imports Pty Ltd", "country": "AU", "country_name": "Australia", "city": "Sydney",
     "sector": "Leather & Footwear", "products": ["Leather Goods", "Footwear"], "hs_families": ["4202", "6403"], "corridors": ["IN-AU"], "size": "Retail importer",
     "website": "https://example-pacificleather.au", "signals": {"website_verified": True},
     "prov": [("company_website", "profile"), ("abr_australia", "registry_listed")]},
    {"slug": "midwest-agro-usa", "legal_name": "Midwest Agro Commodities Corp", "country": "US", "country_name": "United States", "city": "Chicago, IL",
     "sector": "Agri & Foods", "products": ["Guar Gum", "Sesame Seeds", "Castor Oil"], "hs_families": ["1301", "1207", "1515"], "corridors": ["IN-US"], "size": "Commodity trader",
     "website": "https://example-midwestagro.com", "signals": {"registry_listed": True, "sanctions_clear": True},
     "prov": [("sam_gov", "registry_listed"), ("un_comtrade", "trade_stats"), ("trade_gov_csl", "sanctions_clear")]},
    {"slug": "alpen-engineering-de", "legal_name": "Alpen Engineering Components GmbH", "country": "DE", "country_name": "Germany", "city": "Stuttgart",
     "sector": "Metals & Engineering", "products": ["Auto Components", "Precision Castings"], "hs_families": ["8708", "7325"], "corridors": ["IN-DE"], "size": "OEM buyer",
     "website": "https://example-alpen-eng.de", "signals": {"website_verified": True, "vat_validated": True, "sanctions_clear": True},
     "prov": [("vies", "vat_validated"), ("company_website", "profile"), ("eu_ted", "tenders"), ("trade_gov_csl", "sanctions_clear")]},
]


async def seed_vbie():
    """Idempotent seed of the source registry + illustrative buyer entities.
    Only touches VBIE-owned docs; never modifies member/company identity."""
    for s in SOURCES_SEED:
        await db.vbie_sources.update_one({"_id": s["_id"]}, {"$set": s}, upsert=True)

    for b in _BUYERS_SEED:
        geid = _stable_geid(b["slug"])
        provenance = [_prov(sid, field, url=b.get("website", "") if field == "profile" else "")
                      for (sid, field) in b["prov"]]
        signals = b.get("signals", {})
        trust = compute_trust(provenance, signals)
        doc = {
            "_id": geid, "geid": geid, "entity_type": "buyer", "status": "active",
            "legal_name": b["legal_name"], "display_name": b["legal_name"],
            "country": b["country"], "country_name": b["country_name"], "city": b["city"],
            "sector": b["sector"], "products": b["products"], "hs_families": b["hs_families"],
            "corridors": b["corridors"], "size": b.get("size", ""), "website": b.get("website", ""),
            "role": "importer", "signals": signals, "provenance": provenance, "trust": trust,
            "sample": True, "created_by": "vbie-seed", "merged_into": None,
            "updated_at": _now(),
        }
        await db.entities.update_one(
            {"_id": geid},
            {"$set": doc, "$setOnInsert": {"created_at": _now()}},
            upsert=True,
        )
    logger.info("VBIE seed complete: %d sources, %d illustrative buyers", len(SOURCES_SEED), len(_BUYERS_SEED))


# ───────────────────────────── serialization ────────────────────────────────
def _card(e: dict) -> dict:
    t = e.get("trust") or {}
    return {
        "geid": e.get("geid"), "legal_name": e.get("legal_name"), "display_name": e.get("display_name"),
        "country": e.get("country"), "country_name": e.get("country_name"), "city": e.get("city"),
        "sector": e.get("sector"), "products": e.get("products", []), "hs_families": e.get("hs_families", []),
        "corridors": e.get("corridors", []), "size": e.get("size", ""), "role": e.get("role", "importer"),
        "trust": {"score": t.get("score"), "band": t.get("band"), "color": t.get("color")},
        "evidence_count": len(e.get("provenance", [])), "sample": bool(e.get("sample")),
    }


def _full(e: dict) -> dict:
    return {
        **_card(e),
        "website": e.get("website", ""), "signals": e.get("signals", {}),
        "trust": e.get("trust", {}), "provenance": e.get("provenance", []),
        "created_at": _iso(e.get("created_at")), "updated_at": _iso(e.get("updated_at")),
        "status": e.get("status", "active"),
    }


# ──────────────────────────────── endpoints ─────────────────────────────────
@router.get("/meta")
async def buyers_meta():
    """Facets for the buyer-search filters + totals."""
    q = {"entity_type": "buyer", "status": "active", "merged_into": None}
    total = await db.entities.count_documents(q)
    countries = await db.entities.distinct("country_name", q)
    sectors = await db.entities.distinct("sector", q)
    corridors = await db.entities.distinct("corridors", q)
    return {
        "total": total,
        "countries": sorted([c for c in countries if c]),
        "sectors": sorted([s for s in sectors if s]),
        "corridors": sorted([c for c in corridors if c]),
        "trust_bands": ["Verified", "Trusted", "Emerging", "Unverified"],
        "disclaimer": "Buyer records shown are illustrative directory data with cited sources. "
                      "Live, connector-verified intelligence is being onboarded from official trade sources.",
    }


@router.get("/search")
async def search_buyers(
    q: Optional[str] = None,
    country: Optional[str] = None,
    sector: Optional[str] = None,
    corridor: Optional[str] = None,
    hs: Optional[str] = None,
    trust_min: int = 0,
    page: int = 1,
    limit: int = 24,
):
    query: dict = {"entity_type": "buyer", "status": "active", "merged_into": None}
    if country:
        query["$or"] = [{"country": country}, {"country_name": country}]
    if sector:
        query["sector"] = sector
    if corridor:
        query["corridors"] = corridor
    if hs:
        query["hs_families"] = {"$in": [hs, hs[:4], hs[:2]]}
    if trust_min:
        query["trust.score"] = {"$gte": int(trust_min)}
    if q:
        rx = {"$regex": q.strip(), "$options": "i"}
        query["$and"] = [{"$or": [{"legal_name": rx}, {"display_name": rx},
                                  {"products": rx}, {"sector": rx}, {"city": rx}, {"country_name": rx}]}]

    page = max(1, int(page)); limit = max(1, min(int(limit), 60))
    total = await db.entities.count_documents(query)
    cursor = db.entities.find(query).sort("trust.score", -1).skip((page - 1) * limit).limit(limit)
    rows = await cursor.to_list(limit)
    return {"buyers": [_card(r) for r in rows], "total": total, "page": page, "limit": limit}


@router.get("/{geid}")
async def get_buyer(geid: str):
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    # follow merges
    hops = 0
    while e.get("merged_into") and hops < 10:
        nxt = await db.entities.find_one({"_id": e["merged_into"]})
        if not nxt:
            break
        e, hops = nxt, hops + 1
    return _full(e)


@router.get("/{geid}/evidence")
async def get_buyer_evidence(geid: str):
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return {"geid": geid, "evidence": e.get("provenance", []), "trust": e.get("trust", {})}


class BuyerClaim(BaseModel):
    name: str
    email: str
    company: Optional[str] = ""
    role: Optional[str] = ""
    message: Optional[str] = ""


@router.post("/{geid}/claim")
async def claim_buyer(geid: str, body: BuyerClaim, request: Request):
    """Claim-this-company / request introduction. Captured as a lead."""
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    doc = {
        "geid": geid, "buyer_name": e.get("legal_name"),
        "name": body.name.strip(), "email": body.email.strip().lower(),
        "company": (body.company or "").strip(), "role": (body.role or "").strip(),
        "message": (body.message or "").strip(), "status": "new", "created_at": _now(),
    }
    res = await db.buyer_claims.insert_one(doc)
    # mirror into the shared leads CMS so the team sees it
    try:
        await db.leads.insert_one({
            "name": body.name.strip(), "email": body.email.strip().lower(),
            "company": (body.company or "").strip(), "phone": "",
            "message": f"[Buyer claim/intro] {e.get('legal_name')} ({geid}). {body.message or ''}",
            "source": "vbie-buyer-claim", "createdAt": _now().isoformat(),
        })
    except Exception:
        pass
    return {"ok": True, "claim_id": str(res.inserted_id)}
