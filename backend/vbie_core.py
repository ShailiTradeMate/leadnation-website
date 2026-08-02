"""VBIE shared core — pure helpers + source registry + Trust v0.

Extracted from vbie.py to break the vbie ↔ vbie_connectors import cycle: both the
router (vbie.py) and the connectors/admin modules import from here, and this module
imports nothing from them (single dependency direction).
"""
import hashlib
from datetime import datetime, timezone

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
    {"_id": "cid_canada", "name": "Canadian Importers Database", "tier": "official", "category": "customs_bol", "url": "https://ised-isde.canada.ca/site/canadian-importers-database/en", "attribution": "Innovation, Science and Economic Development Canada (Open Government Licence)"},
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


def _prov(source_id: str, field: str, note: str = "", url: str = ""):
    s = _SOURCE_BY_ID.get(source_id, {})
    return {"field": field, "source_id": source_id, "source_name": s.get("name", source_id),
            "source_tier": s.get("tier", "directory"), "source_url": url or s.get("url", ""),
            "attribution": s.get("attribution", ""), "captured_at": _iso(_now()), "note": note}
