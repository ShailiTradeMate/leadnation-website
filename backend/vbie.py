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
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel

from core import db, require_admin
from firebase_auth import _bearer, verify_token
from vbie_core import (SOURCES_SEED, _SOURCE_BY_ID, _now, _iso, _stable_geid,
                       compute_trust, _prov, TIER_RELIABILITY, TRUST_BANDS, _band,
                       compute_confidence, compute_freshness, source_reliability,
                       evidence_source_labels, public_source_labels, public_evidence)

router = APIRouter(prefix="/buyers")
logger = logging.getLogger(__name__)


async def seed_vbie():
    """Idempotent seed of the SOURCE REGISTRY only. Buyer/entity records come EXCLUSIVELY
    from the live connector ingestion (vbie_connectors) — no fabricated demo buyers are
    written. Only touches VBIE-owned docs; never modifies member/company identity."""
    for s in SOURCES_SEED:
        await db.vbie_sources.update_one({"_id": s["_id"]}, {"$set": s}, upsert=True)
    logger.info("VBIE source registry seeded: %d sources", len(SOURCES_SEED))


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
        "has_contact": bool(e.get("has_contact")),
    }


SOURCE_WARNING = ("Buyer records are aggregated from public, official government sources and are provided "
                  "for discovery only. LeadNation independently verifies each record; we have no consent or "
                  "contact arrangement with these organisations. Any business you conduct is entirely at your "
                  "own risk.")


def _primary_source(e: dict) -> str:
    """GENERIC provenance category only — never the exact registry / source site."""
    labels = public_source_labels(e.get("provenance") or [], has_brain=False)
    return labels[0] if labels else "official government sources"


def _intelligence(e: dict) -> dict:
    """The INTELLIGENCE users see — not raw copied datasets. Deterministic summary
    on top of provenance: Trust · Confidence · Freshness · Source Reliability."""
    prov = e.get("provenance", []); sig = e.get("signals", {})
    lv = e.get("last_verified") or _iso(e.get("updated_at"))
    t = e.get("trust") or {}
    return {
        "trust_score": t.get("score"), "trust_band": t.get("band"), "trust_color": t.get("color"),
        "confidence": compute_confidence(prov, sig),
        "freshness": compute_freshness(prov, lv),
        "source_reliability": source_reliability(prov),
        "lei_verified": bool(e.get("lei")),
    }


def _full(e: dict) -> dict:
    """Full profile for entitled subscribers. NEVER includes the exact source name,
    source URL, or the raw provenance notes (which carry notice ids). Only generic,
    category-level evidence labels — so users cannot bypass LeadNation to the source.
    Contact details are NOT included here; they come from the gated reveal endpoint."""
    return {
        **_card(e),
        "signals": e.get("signals", {}),
        "trust": e.get("trust", {}),
        "evidence": public_evidence(e.get("provenance", [])),
        "intelligence": _intelligence(e),
        "evidence_sources": public_source_labels(e.get("provenance", [])),
        "created_at": _iso(e.get("created_at")), "updated_at": _iso(e.get("updated_at")),
        "last_verified": e.get("last_verified") or _iso(e.get("updated_at")),
        "admin_edited": bool(e.get("admin_edited")),
        "status": e.get("status", "active"),
        "primary_source": _primary_source(e), "source_warning": SOURCE_WARNING,
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
        "disclaimer": "Buyer records are ingested from official, licence-cleared government "
                      "sources and independently verified by LeadNation, with sanctions screening "
                      "and contact resolution. LeadNation shows verified intelligence, never raw "
                      "datasets or source links. Full buyer profiles and contact details require "
                      "sign-in and an active plan.",
    }


async def _has_active_sub(uid: str) -> bool:
    s = await db.subscriptions.find_one({"owner": uid, "status": "active"})
    if not s:
        return False
    try:
        return datetime.fromisoformat(s["until"]) > _now()
    except Exception:
        return False


async def _entitlement(authorization: Optional[str]) -> dict:
    """Full buyer intelligence requires a signed-in user with an active plan (admins bypass)."""
    token = _bearer(authorization)
    claims = verify_token(token) if token else None
    if not claims:
        return {"authed": False, "entitled": False, "reason": "login"}
    uid = claims.get("uid")
    u = await db.users.find_one({"uid": uid})
    if u and u.get("role") == "admin":
        return {"authed": True, "entitled": True, "reason": "admin"}
    if await _has_active_sub(uid):
        return {"authed": True, "entitled": True, "reason": "plan"}
    return {"authed": True, "entitled": False, "reason": "plan"}


@router.get("/sources")
async def buyers_sources():
    """Public transparency: the CATEGORIES of official sources VBIE ingests. We
    deliberately do NOT publish exact registry names or links — LeadNation is the
    verified intermediary, and every record is independently verified by us."""
    from vbie_core import SOURCE_PUBLIC_LABEL, DEFAULT_PUBLIC_LABEL
    srcs = await db.vbie_sources.find({}).to_list(100)
    meta = await db.vbie_sanctions_meta.find_one({"_id": "csl"})
    last = await db.vbie_ingest_runs.find_one(sort=[("started_at", -1)])
    seen, cats = set(), []
    for s in srcs:
        lbl = SOURCE_PUBLIC_LABEL.get(s["_id"], DEFAULT_PUBLIC_LABEL)
        if lbl in seen or s.get("category") in ("sanctions",):
            continue
        seen.add(lbl)
        cats.append({"name": lbl, "tier": s.get("tier"), "category": s.get("category")})
    return {
        "sources": cats,
        "sanctions_screening": {"provider": "Government sanctions & denied-party screening",
                                "denied_parties": (meta or {}).get("count"),
                                "refreshed_at": (meta or {}).get("refreshed_at")},
        "last_ingestion": {"finished_at": (last or {}).get("finished_at"),
                           "upserted": (last or {}).get("upserted")} if last else None,
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
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$and"] = [{"$or": [{"legal_name": rx}, {"display_name": rx},
                                  {"products": rx}, {"sector": rx}, {"city": rx}, {"country_name": rx}]}]

    page = max(1, int(page)); limit = max(1, min(int(limit), 60))
    total = await db.entities.count_documents(query)
    cursor = db.entities.find(query).sort("trust.score", -1).skip((page - 1) * limit).limit(limit)
    rows = await cursor.to_list(limit)
    return {"buyers": [_card(r) for r in rows], "total": total, "page": page, "limit": limit}


@router.get("/watchlist")
async def get_watchlist(authorization: Optional[str] = Header(default=None)):
    """Buyers the signed-in user is watching (for change alerts)."""
    claims = verify_token(_bearer(authorization)) if authorization else None
    if not claims:
        raise HTTPException(status_code=401, detail="Authentication required")
    rows = await db.buyer_watchlist.find({"uid": claims["uid"]}).sort("created_at", -1).to_list(200)
    geids = [r["geid"] for r in rows]
    ents = await db.entities.find({"_id": {"$in": geids}}).to_list(len(geids))
    by_id = {e["_id"]: e for e in ents}
    return {"watchlist": [_card(by_id[g]) for g in geids if g in by_id]}


@router.get("/match")
async def match_company(name: str = Query(""), country: str = Query(""),
                        number: str = Query("")):
    """Networking hook: given a company (name / country / registration number), return
    candidate VBIE buyers (by GEID) the member can CLAIM — so a verified buyer joining
    LeadNation is auto-linked to their existing intelligence record."""
    import re as _re
    q = {"entity_type": "buyer", "admin_deleted": {"$ne": True}, "status": {"$ne": "deleted"}}
    ors = []
    if number.strip():
        ors.append({"identifiers.company_number": number.strip()})
    if name.strip():
        rx = _re.compile(_re.escape(name.strip()), _re.IGNORECASE)
        clause = {"legal_name": rx}
        if country.strip():
            clause["country"] = country.strip().upper()
        ors.append(clause)
    if not ors:
        return {"candidates": []}
    q["$or"] = ors
    rows = await db.entities.find(q).limit(10).to_list(10)
    return {"candidates": [{**_card(e), "lei": e.get("lei", ""),
                            "claim_url": f"/buyers/{e['_id']}",
                            "identifiers": e.get("identifiers", {})} for e in rows]}


@router.get("/{geid}")
async def get_buyer(geid: str, authorization: Optional[str] = Header(default=None)):
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e or e.get("admin_deleted") or e.get("status") == "deleted":
        raise HTTPException(status_code=404, detail="Buyer not found")
    # follow merges
    hops = 0
    while e.get("merged_into") and hops < 10:
        nxt = await db.entities.find_one({"_id": e["merged_into"]})
        if not nxt:
            break
        e, hops = nxt, hops + 1
    ent = await _entitlement(authorization)
    if ent["entitled"]:
        return {**_full(e), "locked": False}
    # Locked teaser: identity + INTELLIGENCE summary + GENERIC source labels only.
    # Detailed evidence and contact stay gated behind an active plan.
    return {**_card(e), "locked": True, "lock_reason": ent["reason"],
            "trust": e.get("trust", {}), "signals": {},
            "intelligence": _intelligence(e),
            "evidence_sources": public_source_labels(e.get("provenance", [])),
            "status": e.get("status", "active"),
            "last_verified": e.get("last_verified") or _iso(e.get("updated_at")),
            "admin_edited": bool(e.get("admin_edited")),
            "primary_source": _primary_source(e), "source_warning": SOURCE_WARNING}


class _ContactReveal(BaseModel):
    pass


@router.post("/{geid}/contact")
async def reveal_buyer_contact(geid: str, authorization: Optional[str] = Header(default=None)):
    """Reveal the buyer's official contact point (email / phone / address) to an
    ACTIVE SUBSCRIBER only. Resolves + caches contact server-side and returns ONLY
    the contact fields — the source URL is never exposed."""
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e or e.get("admin_deleted") or e.get("status") == "deleted":
        raise HTTPException(status_code=404, detail="Buyer not found")
    hops = 0
    while e.get("merged_into") and hops < 10:
        nxt = await db.entities.find_one({"_id": e["merged_into"]})
        if not nxt:
            break
        e, hops = nxt, hops + 1
    ent = await _entitlement(authorization)
    if not ent["entitled"]:
        raise HTTPException(status_code=402, detail=f"locked:{ent['reason']}")

    import vbie_contacts
    contact = await vbie_contacts.resolve_buyer_contact(e)
    if not (contact and (contact.get("email") or contact.get("phone"))):
        raise HTTPException(status_code=404, detail="No published contact for this buyer")

    # Analytics: log the reveal (who saw which buyer's contact).
    try:
        uid = (verify_token(_bearer(authorization)) or {}).get("uid") if authorization else None
        await db.buyer_contact_reveals.insert_one(
            {"geid": geid, "uid": uid, "at": _iso(_now())})
    except Exception:
        pass

    return {"geid": geid, "display_name": e.get("display_name"),
            "contact": {"email": contact.get("email", ""), "phone": contact.get("phone", ""),
                        "website": contact.get("website", ""), "address": contact.get("address", ""),
                        "city": contact.get("city", ""), "contact_name": contact.get("contact_name", "")},
            "source_note": "Sourced and verified by LeadNation from official government records."}


@router.get("/{geid}/evidence")
async def get_buyer_evidence(geid: str, authorization: Optional[str] = Header(default=None)):
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    ent = await _entitlement(authorization)
    if not ent["entitled"]:
        raise HTTPException(status_code=402, detail=f"locked:{ent['reason']}")
    return {"geid": geid, "evidence": public_evidence(e.get("provenance", [])),
            "trust": e.get("trust", {})}


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


@router.post("/{geid}/watch")
async def watch_buyer(geid: str, authorization: Optional[str] = Header(default=None)):
    """Add a buyer to the user's watchlist to receive change alerts."""
    claims = verify_token(_bearer(authorization)) if authorization else None
    if not claims:
        raise HTTPException(status_code=401, detail="Authentication required")
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"}, {"_id": 1})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    email = claims.get("email", "")
    await db.buyer_watchlist.update_one(
        {"uid": claims["uid"], "geid": geid},
        {"$set": {"uid": claims["uid"], "geid": geid, "email": email, "created_at": _now()}}, upsert=True)
    return {"ok": True, "watching": True}


@router.delete("/{geid}/watch")
async def unwatch_buyer(geid: str, authorization: Optional[str] = Header(default=None)):
    claims = verify_token(_bearer(authorization)) if authorization else None
    if not claims:
        raise HTTPException(status_code=401, detail="Authentication required")
    await db.buyer_watchlist.delete_one({"uid": claims["uid"], "geid": geid})
    return {"ok": True, "watching": False}


# ─────────────────────── admin: connector ingestion ─────────────────────────
@router.post("/ingest/run")
async def trigger_ingestion(background: bool = True, _: dict = Depends(require_admin)):
    """Manually trigger a daily-style ingestion of real buyers from official sources."""
    import asyncio
    import vbie_connectors
    if background:
        asyncio.create_task(vbie_connectors.run_ingestion(trigger="admin-manual"))
        return {"ok": True, "started": True, "mode": "background"}
    summary = await vbie_connectors.run_ingestion(trigger="admin-sync")
    return {"ok": True, "summary": summary}


@router.get("/ingest/status")
async def ingestion_status(_: dict = Depends(require_admin)):
    runs = await db.vbie_ingest_runs.find({}).sort("started_at", -1).to_list(10)
    real = await db.entities.count_documents({"entity_type": "buyer", "sample": {"$ne": True}})
    samples = await db.entities.count_documents({"entity_type": "buyer", "sample": True})
    return {"real_buyers": real, "sample_buyers": samples,
            "runs": [{k: v for k, v in r.items() if k != "_id"} for r in runs]}
