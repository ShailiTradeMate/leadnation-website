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
                       compute_trust, _prov, TIER_RELIABILITY, TRUST_BANDS, _band)

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
    }


SOURCE_WARNING = ("Buyer records are aggregated from public, official sources and are provided for "
                  "discovery only. LeadNation has no consent or contact arrangement with these "
                  "organisations. Independently verify all details and reach out to the buyer directly — "
                  "any business you conduct is entirely at your own risk.")


def _primary_source(e: dict) -> str:
    prov = e.get("provenance") or []
    return prov[0].get("source_name") if prov else ""


def _full(e: dict) -> dict:
    return {
        **_card(e),
        "website": e.get("website", ""), "signals": e.get("signals", {}),
        "trust": e.get("trust", {}), "provenance": e.get("provenance", []),
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
        "disclaimer": "Buyer records are ingested daily from official government sources "
                      "(EU TED procurement, Canadian Importers Database, UN Comtrade, "
                      "trade.gov sanctions screening) with cited provenance. Full buyer "
                      "profiles require sign-in and an active plan.",
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
    """Public transparency: the official sources VBIE ingests, with attribution."""
    srcs = await db.vbie_sources.find({}).to_list(100)
    meta = await db.vbie_sanctions_meta.find_one({"_id": "csl"})
    last = await db.vbie_ingest_runs.find_one(sort=[("started_at", -1)])
    return {
        "sources": [{"id": s["_id"], "name": s.get("name"), "tier": s.get("tier"),
                     "category": s.get("category"), "url": s.get("url"),
                     "attribution": s.get("attribution")} for s in srcs],
        "sanctions_screening": {"provider": "trade.gov Consolidated Screening List",
                                "denied_parties": (meta or {}).get("count"),
                                "refreshed_at": (meta or {}).get("refreshed_at")},
        "last_ingestion": {"finished_at": (last or {}).get("finished_at"),
                           "upserted": (last or {}).get("upserted"),
                           "screened_out": (last or {}).get("screened_out"),
                           "by_source": (last or {}).get("sources")} if last else None,
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
    # Locked teaser: identity + trust band only. Contact/website/evidence gated behind a plan.
    return {**_card(e), "locked": True, "lock_reason": ent["reason"],
            "trust": e.get("trust", {}), "website": "", "provenance": [], "signals": {},
            "status": e.get("status", "active"),
            "last_verified": e.get("last_verified") or _iso(e.get("updated_at")),
            "admin_edited": bool(e.get("admin_edited")),
            "primary_source": _primary_source(e), "source_warning": SOURCE_WARNING}


@router.get("/{geid}/evidence")
async def get_buyer_evidence(geid: str, authorization: Optional[str] = Header(default=None)):
    e = await db.entities.find_one({"_id": geid, "entity_type": "buyer"})
    if not e:
        raise HTTPException(status_code=404, detail="Buyer not found")
    ent = await _entitlement(authorization)
    if not ent["entitled"]:
        raise HTTPException(status_code=402, detail=f"locked:{ent['reason']}")
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
