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
    {"_id": "gleif", "name": "GLEIF Global LEI Index", "tier": "gov", "category": "identity", "url": "https://www.gleif.org", "attribution": "Global Legal Entity Identifier Foundation (CC0 1.0)"},
    {"_id": "sirene_fr", "name": "INSEE SIRENE (France)", "tier": "gov", "category": "registry", "url": "https://www.insee.fr/fr/information/3591226", "attribution": "Source: INSEE, SIRENE — Licence Ouverte / Etalab 2.0"},
    {"_id": "no_brreg", "name": "Brønnøysund Register Centre (Norway)", "tier": "gov", "category": "registry", "url": "https://data.brreg.no/enhetsregisteret", "attribution": "Brønnøysundregistrene — Norwegian Licence for Open Government Data (NLOD)"},
    {"_id": "cz_ares", "name": "ARES Business Register (Czechia)", "tier": "gov", "category": "registry", "url": "https://ares.gov.cz", "attribution": "Ministry of Finance of the Czech Republic — ARES (open data)"},
    {"_id": "sg_acra", "name": "ACRA Entities (Singapore)", "tier": "gov", "category": "registry", "url": "https://data.gov.sg", "attribution": "Accounting and Corporate Regulatory Authority via data.gov.sg (Singapore Open Data Licence)"},
    {"_id": "fi_prh", "name": "PRH/YTJ Business Information (Finland)", "tier": "gov", "category": "registry", "url": "https://avoindata.prh.fi", "attribution": "Finnish Patent and Registration Office (PRH) — CC BY 4.0"},
    {"_id": "jp_nta", "name": "National Tax Agency Corporate Number (Japan)", "tier": "gov", "category": "registry", "url": "https://www.houjin-bangou.nta.go.jp", "attribution": "Japan National Tax Agency Corporate Number Publication Site"},
    {"_id": "dk_cvr", "name": "CVR Central Business Register (Denmark)", "tier": "gov", "category": "registry", "url": "https://datacvr.virk.dk", "attribution": "Erhvervsstyrelsen — Danish CVR open distribution"},
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
    if signals.get("lei_verified"):
        score += 8; factors.append({"label": "Global LEI verified", "points": 8, "detail": "Matched to GLEIF Global LEI Index (canonical identity)"})

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


# ─────────────────── per-source legal-approval gating ───────────────────────
# Only sources whose licence/ToS have been reviewed + explicitly approved may run
# in ingestion. Everything else stays dormant (pending_legal_approval) until a
# human flips it on. P0 approved set (all verified GREEN in the research report):
# P0 approved (verified GREEN). Norway (NLOD) and Czechia (ARES open data) are
# confirmed GREEN + commercially reusable and enabled here. Key-gated sources
# (France SIRENE, Japan NTA, Australia ABR, Denmark CVR, Singapore ACRA, Finland
# PRH) stay pending_legal_approval until their key/terms are supplied + reviewed.
APPROVED_SOURCES = {"eu_ted", "cid_canada", "uk_companies_house", "trade_gov_csl",
                    "gleif", "no_brreg", "cz_ares"}


def is_source_approved(source_id: str) -> bool:
    return source_id in APPROVED_SOURCES


# ──────────── intelligence layer: confidence · freshness · reliability ───────
# LeadNation exposes INTELLIGENCE, never raw copied datasets. These deterministic
# summaries sit on top of provenance so subscribers see Trust / Confidence /
# Freshness / Source Reliability + cited evidence labels.
_RELIABILITY_LABEL = {"gov": "Government", "official": "Official", "licensed": "Licensed", "directory": "Directory"}


def _distinct_sources(provenance: list) -> list:
    seen, out = set(), []
    for p in provenance or []:
        sid = p.get("source_id")
        if sid and sid not in seen:
            seen.add(sid); out.append(p)
    return out


def compute_confidence(provenance: list, signals: dict) -> dict:
    """How corroborated is this entity — more independent sources + signals = higher."""
    n = len(_distinct_sources(provenance))
    bonus = sum(4 for k in ("registry_listed", "sanctions_clear", "vat_validated", "website_verified", "lei_verified")
                if (signals or {}).get(k))
    score = min(100, (30 if n <= 1 else 55 if n == 2 else 80) + bonus)
    label = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
    return {"score": score, "label": label, "sources": n}


def compute_freshness(provenance: list, last_verified=None) -> dict:
    """How recent is the newest evidence."""
    dates = []
    for c in ([last_verified] + [p.get("captured_at") for p in (provenance or [])]):
        if not c:
            continue
        try:
            d = datetime.fromisoformat(c) if isinstance(c, str) else c
            if getattr(d, "tzinfo", None) is None:
                d = d.replace(tzinfo=timezone.utc)
            dates.append(d)
        except Exception:
            pass
    if not dates:
        return {"score": 50, "label": "Unknown", "age_days": None}
    age = (_now() - max(dates)).days
    if age <= 30:
        score, label = 100, "Fresh"
    elif age <= 180:
        score, label = 80, "Recent"
    elif age <= 365:
        score, label = 55, "Aging"
    else:
        score, label = 30, "Stale"
    return {"score": score, "label": label, "age_days": age}


def source_reliability(provenance: list) -> dict:
    """Best (highest-tier) source backing this entity."""
    order = ["gov", "official", "licensed", "directory"]
    tiers = [_SOURCE_BY_ID.get(p.get("source_id"), {}).get("tier", "directory") for p in (provenance or [])]
    best = min(tiers, key=lambda t: order.index(t) if t in order else 99) if tiers else "directory"
    return {"tier": best, "label": _RELIABILITY_LABEL.get(best, "Directory"), "score": TIER_RELIABILITY.get(best, 55)}


def evidence_source_labels(provenance: list, has_brain: bool = True) -> list:
    """Distinct source LABELS (not raw rows) — e.g. Companies House, Canada CID, EU TED, GLEIF."""
    labels = []
    for p in _distinct_sources(provenance):
        nm = p.get("source_name")
        if nm and nm not in labels:
            labels.append(nm)
    if has_brain and "Brain Analysis" not in labels:
        labels.append("Brain Analysis")
    return labels
