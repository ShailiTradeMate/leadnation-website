"""Profile Brain — the Brain's watcher over USER PROFILES.

Every admin/sub-admin action on a user funnels through here so the Brain:
  1. sees the profile (memory snapshot in `user_context.profile` → available to
     every Brain answer via brain.context.build_context),
  2. diffs what actually changed (`profile_changes` = audit + change feed),
  3. informs the user itself — branded email + in-app notification.

No admin code sends user emails directly; the Brain owns user communication so
a change can never happen silently.
"""
import logging
from datetime import datetime, timezone

from core import db

CHANGES = db.profile_changes
CTX = db.user_context
NOTIF = db.notifications
log = logging.getLogger("profile_brain")

# Fields the Brain watches on a buyer profile.
WATCHED = [
    ("name", "Full name"),
    ("mobile", "Mobile number"),
    ("mobile_number", "Mobile number"),
    ("email", "Email address"),
    ("country", "Country"),
    ("state", "State / Province"),
    ("city", "City"),
    ("address", "Address"),
    ("role", "User category"),
    ("products", "Products traded"),
    ("company_details.company_name", "Company name"),
    ("company_details.company_email", "Company email"),
    ("company_details.company_phone", "Company contact number"),
    ("company_details.gst", "GST / Tax ID"),
    ("verification_status", "Verification status"),
]

# Event kind -> (title, short summary) for the in-app feed.
EVENT_TITLES = {
    "verify_approved": "You're a Verified Buyer",
    "verify_rejected": "Verification could not be approved",
    "verify_correction": "We need a correction on your application",
    "profile_changed": "Your profile was updated",
    "document_updated": "A document on your account was updated",
    "account_removed": "Your Vametra AI records were removed",
    "subscription_granted": "A subscription was added to your account",
    "subscription_revoked": "A subscription on your account was removed",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(obj: dict, path: str):
    cur = obj or {}
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _norm(v):
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v)
    return "" if v is None else str(v)


def diff(before: dict, after: dict) -> list:
    """Human-readable field-level diff of a buyer profile."""
    out, seen = [], set()
    for path, label in WATCHED:
        if label in seen:
            continue
        a, b = _norm(_get(before, path)), _norm(_get(after, path))
        if a.strip() == b.strip():
            continue
        seen.add(label)
        out.append({"field": path, "label": label, "from": a or "—", "to": b or "—"})
    return out


async def sync_profile_memory(uid: str, profile: dict):
    """Give the Brain read access to the user's live profile (memory snapshot)."""
    if not uid or not profile:
        return
    cd = profile.get("company_details") or {}
    snap = {
        "name": profile.get("name"), "email": profile.get("email"),
        "mobile": profile.get("mobile") or profile.get("mobile_number"),
        "country": profile.get("country"), "state": profile.get("state"),
        "city": profile.get("city"), "role": profile.get("role"),
        "products": profile.get("products") or [],
        "company_name": cd.get("company_name"), "company_email": cd.get("company_email"),
        "company_phone": cd.get("company_phone"),
        "customer_id": profile.get("customer_id"), "geid": profile.get("geid"),
        "verification_status": profile.get("verification_status"),
        "synced_at": _now(),
    }
    await CTX.update_one({"user_id": uid},
                         {"$set": {"profile": snap, "preferredCountry": snap.get("country"),
                                   "role": snap.get("role"), "updatedAt": _now()},
                          "$setOnInsert": {"user_id": uid, "createdAt": _now()}},
                         upsert=True)


async def profile_snapshot(uid: str) -> dict:
    doc = await CTX.find_one({"user_id": uid}, {"_id": 0, "profile": 1}) or {}
    return doc.get("profile") or {}


async def _log(uid: str, kind: str, actor: dict, summary: str, changes: list = None,
               detail: dict = None):
    doc = {"uid": uid, "kind": kind, "summary": summary,
           "changes": changes or [], "detail": detail or {},
           "actor": {"role": (actor or {}).get("role"), "name": (actor or {}).get("name"),
                     "email": (actor or {}).get("email")},
           "at": _now()}
    await CHANGES.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def _notify_inapp(uid: str, kind: str, summary: str):
    if not uid:
        return
    await NOTIF.insert_one({
        "audience": "user", "uid": uid, "scope": "account", "kind": kind,
        "title": EVENT_TITLES.get(kind, "Account update"), "message": summary,
        "created_at": _now()})


async def announce(uid: str, kind: str, *, email: str = None, name: str = None,
                   actor: dict = None, summary: str = "", ctx: dict = None,
                   changes: list = None):
    """Brain-owned user communication: log the event, notify in-app, send the email."""
    import emailer
    summary = summary or EVENT_TITLES.get(kind, "Your account was updated")
    entry = await _log(uid, kind, actor, summary, changes, ctx)
    await _notify_inapp(uid, kind, summary)
    sent = {"sent": False, "reason": "no recipient"}
    if email:
        payload = dict(ctx or {})
        payload.setdefault("name", name or "there")
        payload.setdefault("changes", changes or [])
        payload.setdefault("actor", (actor or {}).get("name") or "The Vametra AI team")
        sent = await emailer.send(kind, email, payload)
    log.info("[brain] %s for %s (email sent=%s)", kind, uid, sent.get("sent"))
    return {"event": entry, "email": sent}


async def observe(uid: str, before: dict, after: dict, *, actor: dict = None,
                  source: str = "admin", email: str = None, name: str = None):
    """Diff a profile change, refresh Brain memory and inform the user if anything moved."""
    changes = diff(before or {}, after or {})
    await sync_profile_memory(uid, after or {})
    if not changes:
        return {"changes": [], "email": {"sent": False, "reason": "no change detected"}}
    summary = ", ".join(f"{c['label']} → {c['to']}" for c in changes[:4])
    res = await announce(uid, "profile_changed", email=email, name=name, actor=actor,
                         summary=summary, ctx={"source": source}, changes=changes)
    return {"changes": changes, "email": res["email"]}


async def feed(uid: str, limit: int = 30) -> list:
    rows = await CHANGES.find({"uid": uid}).sort("at", -1).limit(int(limit)).to_list(limit)
    return [{k: v for k, v in r.items() if k != "_id"} for r in rows]
