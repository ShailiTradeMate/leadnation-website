"""VBIE contact-resolution service.

Owner-mandated business rule: LeadNation is the intermediary. Subscribers must
NEVER be handed a link to the free government source (that lets them bypass us).
Instead we resolve the buyer's official contact point (email / phone / address)
SERVER-SIDE, store it in our own database, and reveal ONLY the contact fields to
an active subscriber — the source URL is never exposed.

Two jobs live here:
  1. `resolve_ted_contacts()` — batch-fetch buyer contact for TED-sourced buyers
     straight from the TED API (by publication-number), keyed off the source_url
     we already stored.
  2. `enrich_and_prune()` — one-off/maintenance backfill: enrich every existing
     buyer with contact, then HARD-DELETE buyers that still have no email/phone
     (they must not be shown), respecting admin sovereignty.
"""
import logging

import httpx

from core import db
from vbie_core import _now, _iso
from vbie_connectors import (TED_URL, UA, TED_CONTACT_FIELDS, ted_extract_contact,
                             has_contact)

logger = logging.getLogger(__name__)


def _pub_from_url(url: str) -> str:
    if not url:
        return ""
    return url.rstrip("/").split("/")[-1].split("?")[0]


async def resolve_ted_contacts(pubs: list) -> dict:
    """Return {publication-number: contact} for a batch of TED notices."""
    pubs = [p for p in pubs if p]
    if not pubs:
        return {}
    out = {}
    fields = ["publication-number"] + TED_CONTACT_FIELDS
    async with httpx.AsyncClient(timeout=45, headers=UA) as cx:
        for i in range(0, len(pubs), 25):
            chunk = pubs[i:i + 25]
            query = " OR ".join(f"publication-number={p}" for p in chunk)
            try:
                r = await cx.post(TED_URL, json={"query": query, "fields": fields,
                                                 "limit": 50, "scope": "ALL"})
                if r.status_code != 200:
                    logger.warning("TED contact batch %d: status %s", i, r.status_code)
                    continue
                for n in (r.json() or {}).get("notices", []):
                    pub = n.get("publication-number")
                    if pub:
                        out[str(pub)] = ted_extract_contact(n)
            except Exception as exc:
                logger.warning("TED contact batch %d failed: %s", i, exc)
    return out


async def resolve_buyer_contact(e: dict) -> dict:
    """Resolve a single buyer's contact on-demand (used by the reveal endpoint
    as a fallback when nothing is cached). Returns {} if unresolvable."""
    existing = e.get("contact") or {}
    if has_contact(existing):
        return existing
    # Try the TED provenance URL.
    for p in e.get("provenance", []):
        if p.get("source_id") == "eu_ted":
            pub = _pub_from_url(p.get("source_url", ""))
            if pub:
                got = await resolve_ted_contacts([pub])
                c = got.get(pub)
                if c and has_contact(c):
                    await db.entities.update_one(
                        {"_id": e["_id"]},
                        {"$set": {"contact": c, "has_contact": True,
                                  "website": c.get("website", "") or e.get("website", ""),
                                  "city": c.get("city", "") or e.get("city", "")}})
                    return c
    return existing


async def enrich_and_prune(delete_uncontactable: bool = True) -> dict:
    """Backfill contact for every buyer, then hard-delete those still without
    email/phone (owner rule). Admin-edited buyers are never deleted."""
    stats = {"scanned": 0, "enriched": 0, "already": 0, "deleted": 0,
             "kept_no_contact_admin": 0, "started_at": _iso(_now())}

    # 1) Collect TED buyers that still need contact, grouped by publication-number.
    pending = {}  # pub -> geid
    cursor = db.entities.find(
        {"entity_type": "buyer", "provenance.source_id": "eu_ted"},
        {"provenance": 1, "contact": 1})
    async for e in cursor:
        stats["scanned"] += 1
        if has_contact(e.get("contact")):
            stats["already"] += 1
            continue
        for p in e.get("provenance", []):
            if p.get("source_id") == "eu_ted":
                pub = _pub_from_url(p.get("source_url", ""))
                if pub:
                    pending[pub] = e["_id"]
                break

    logger.info("enrich_and_prune: %d TED buyers need contact", len(pending))

    # 2) Batch-resolve from TED and write contact back.
    pubs = list(pending.keys())
    for i in range(0, len(pubs), 25):
        got = await resolve_ted_contacts(pubs[i:i + 25])
        ops = []
        from pymongo import UpdateOne
        for pub, contact in got.items():
            if not has_contact(contact):
                continue
            geid = pending.get(pub)
            if not geid:
                continue
            ops.append(UpdateOne(
                {"_id": geid},
                {"$set": {"contact": contact, "has_contact": True,
                          "website": contact.get("website", ""),
                          "city": contact.get("city", ""),
                          "updated_at": _now()}}))
        if ops:
            res = await db.entities.bulk_write(ops, ordered=False)
            stats["enriched"] += (res.modified_count or 0) + (res.upserted_count or 0)

    # 3) Prune buyers that STILL have no contact — VERIFIED against the actual
    #    contact object (email/phone), never just a flag. Admin-managed buyers and
    #    any buyer that genuinely has contact are ALWAYS kept.
    if delete_uncontactable:
        # 3a) SAFETY: protect every buyer that actually has an email/phone by
        #     ensuring its has_contact flag is set (covers legacy/admin-added contact).
        protect = await db.entities.update_many(
            {"entity_type": "buyer", "has_contact": {"$ne": True},
             "$or": [{"contact.email": {"$nin": ["", None]}},
                     {"contact.phone": {"$nin": ["", None]}}]},
            {"$set": {"has_contact": True}})
        stats["protected_flag_fixed"] = protect.modified_count
        # 3b) Delete ONLY buyers verified to have NO email AND NO phone.
        no_email = {"$or": [{"contact.email": {"$in": ["", None]}}, {"contact.email": {"$exists": False}}]}
        no_phone = {"$or": [{"contact.phone": {"$in": ["", None]}}, {"contact.phone": {"$exists": False}}]}
        prune_q = {"entity_type": "buyer",
                   "admin_edited": {"$ne": True}, "admin_deleted": {"$ne": True},
                   "$and": [no_email, no_phone]}
        stats["kept_no_contact_admin"] = await db.entities.count_documents(
            {"entity_type": "buyer", "admin_edited": True, "$and": [no_email, no_phone]})
        res = await db.entities.delete_many(prune_q)
        stats["deleted"] = res.deleted_count

    stats["finished_at"] = _iso(_now())
    stats["remaining_buyers"] = await db.entities.count_documents(
        {"entity_type": "buyer", "status": "active", "merged_into": None})
    await db.vbie_contact_runs.insert_one(dict(stats))
    logger.info("enrich_and_prune done: %s", stats)
    return stats
