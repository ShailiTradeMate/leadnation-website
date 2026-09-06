"""Website-local sub-admin auth + RBAC + admin User Section (Phase A).

Self-contained STAFF auth (bcrypt + JWT) that COEXISTS with the Firebase main
admin (customer_id 00001). It does NOT touch the DO/Firebase buyer identity
system or Customer-ID allocation — sub-admins are internal staff only.

Reusable by design: `require_staff` returns a role dict ({role, is_main, ...})
so future CMS sections can gate features per role without a rewrite.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel

from core import db, JWT_SECRET, JWT_ALG

router = APIRouter()
log = logging.getLogger("subadmin")

SUBADMINS = db.sub_admins
SUBS = db.verification_submissions
OVERLAY = db.profile_overlay
STAFF_TTL_HOURS = 12


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify(pw: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), (h or "").encode("utf-8"))
    except Exception:
        return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _staff_token(sa: dict) -> str:
    payload = {
        "kind": "staff", "sid": sa["id"], "email": sa.get("email"),
        "name": sa.get("name"), "role": "sub_admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=STAFF_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


# ---------------- identity resolver ----------------
async def staff_identity(authorization: Optional[str], x_staff_token: Optional[str]) -> dict:
    """Resolve EITHER a sub-admin JWT OR a Firebase main-admin token."""
    tok = x_staff_token
    if not tok and authorization and authorization.lower().startswith("bearer "):
        cand = authorization.split(" ", 1)[1].strip()
        try:
            p = jwt.decode(cand, JWT_SECRET, algorithms=[JWT_ALG])
            if p.get("kind") == "staff":
                tok = cand
        except Exception:
            pass
    if tok:
        try:
            p = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALG])
            if p.get("kind") == "staff":
                sa = await SUBADMINS.find_one({"id": p["sid"]})
                if sa and sa.get("active", True):
                    return {"role": "sub_admin", "is_main": False, "sid": sa["id"],
                            "name": sa.get("name"), "email": sa.get("email")}
                raise HTTPException(403, "This sub-admin account is deactivated.")
        except HTTPException:
            raise
        except Exception:
            pass
    # Firebase main admin
    if authorization and authorization.lower().startswith("bearer "):
        from firebase_auth import verify_token
        claims = verify_token(authorization.split(" ", 1)[1].strip())
        if claims:
            u = await db.users.find_one({"uid": claims.get("uid")})
            if u and u.get("role") == "admin" and not u.get("is_deleted"):
                return {"role": "main_admin", "is_main": True, "uid": claims["uid"],
                        "name": u.get("full_name") or u.get("name") or "Admin",
                        "email": u.get("email"), "customer_id": u.get("customer_id")}
    raise HTTPException(401, "Admin or sub-admin access required")


async def require_staff(authorization: Optional[str] = Header(default=None),
                        x_staff_token: Optional[str] = Header(default=None)):
    return await staff_identity(authorization, x_staff_token)


async def require_main_admin(authorization: Optional[str] = Header(default=None),
                             x_staff_token: Optional[str] = Header(default=None)):
    ident = await staff_identity(authorization, x_staff_token)
    if not ident.get("is_main"):
        raise HTTPException(403, "Main admin only.")
    return ident


# ---------------- Reusable permission model (future CMS sections just add a key) ----
PERMISSIONS = {
    "main_admin": {
        "users.view_all", "users.edit", "users.delete", "users.review_final",
        "users.review_recommend", "users.correction", "users.contact", "users.documents",
        "payments.view", "payments.grant", "allocate", "subadmins.manage", "signoff.view",
    },
    "sub_admin": {
        "users.view_assigned", "users.edit", "users.review_recommend", "users.correction",
        "users.contact", "users.documents", "payments.view",
    },
}


def perms_for(ident: dict) -> set:
    return PERMISSIONS["main_admin" if ident.get("is_main") else "sub_admin"]


def has_perm(ident: dict, perm: str) -> bool:
    return perm in perms_for(ident)


def require_perm(perm: str):
    """Dependency factory — gate any admin endpoint on a single permission key."""
    async def _dep(ident: dict = Depends(require_staff)):
        if not has_perm(ident, perm):
            raise HTTPException(403, f"Your role does not allow this action ({perm}).")
        return ident
    return _dep


@router.get("/admin/permissions")
async def my_permissions(staff: dict = Depends(require_staff)):
    return {"role": staff.get("role"), "is_main": staff.get("is_main"),
            "name": staff.get("name"), "email": staff.get("email"),
            "permissions": sorted(perms_for(staff))}


# ---------------- auth endpoints ----------------
class StaffLogin(BaseModel):
    identifier: str
    password: str


@router.post("/admin-auth/login")
async def staff_login(body: StaffLogin):
    ident = (body.identifier or "").strip().lower()
    sa = await SUBADMINS.find_one({"$or": [{"email": ident}, {"username": ident}]})
    if not sa or not _verify(body.password, sa.get("password_hash", "")):
        raise HTTPException(401, "Invalid credentials")
    if not sa.get("active", True):
        raise HTTPException(403, "This sub-admin account is deactivated.")
    return {"token": _staff_token(sa),
            "subadmin": {"id": sa["id"], "name": sa.get("name"),
                         "email": sa.get("email"), "role": "sub_admin"}}


@router.get("/admin-auth/me")
async def staff_me(staff: dict = Depends(require_staff)):
    return staff


# ---------------- User Section (all registered users) ----------------
def _pick(*vals):
    for v in vals:
        if v not in (None, "", []):
            return v
    return None


def _file_url(fid):
    return f"/api/storage/file/{fid}" if fid else None


@router.get("/admin/users")
async def admin_users(q: Optional[str] = None, status: Optional[str] = None,
                      staff: dict = Depends(require_staff)):
    """Full visibility of everyone on the platform (shared Mongo `users`),
    enriched with their latest Verified-Buyer submission + overlay + subscription.
    Sub-admins only see users allocated to them."""
    users = await db.users.find({}).to_list(8000)

    def _sub_rank(s):
        st = s.get("status")
        return (
            1 if s.get("assigned_to") else 0,
            1 if st == "needs_review" else 0,
            1 if st == "verified" else 0,
            str(s.get("created_at") or ""),
        )

    subs_by_uid, subs_by_email = {}, {}
    async for s in SUBS.find({}):
        uid = s.get("uid")
        em = str(s.get("email") or "").lower()
        if uid and (uid not in subs_by_uid or _sub_rank(s) > _sub_rank(subs_by_uid[uid])):
            subs_by_uid[uid] = s
        if em and (em not in subs_by_email or _sub_rank(s) > _sub_rank(subs_by_email[em])):
            subs_by_email[em] = s

    overlays = {}
    async for o in OVERLAY.find({}):
        overlays[o.get("uid")] = o

    subscriptions = {}
    try:
        async for sub in db.subscriptions.find({}):
            key = sub.get("uid") or sub.get("owner") or sub.get("customer_id")
            if key:
                subscriptions[str(key)] = sub
    except Exception:
        pass

    rows = []
    covered_uids, covered_emails = set(), set()

    def _row_from(u, sub, ov):
        cd_ov = (ov.get("company_details") or {})
        cid = u.get("customer_id") or sub.get("customer_id")
        uid = u.get("uid") or sub.get("uid")
        sc = subscriptions.get(str(uid)) or subscriptions.get(str(cid)) or {}
        docs = []
        if sub.get("selfie_file_id"):
            docs.append({"kind": "selfie", "label": "Selfie", "file_id": sub["selfie_file_id"],
                         "url": _file_url(sub["selfie_file_id"])})
        if sub.get("document_file_id"):
            docs.append({"kind": "document", "label": sub.get("doc_type") or "Business document",
                         "file_id": sub["document_file_id"], "url": _file_url(sub["document_file_id"])})
        applied = bool(sub)
        return {
            "uid": uid,
            "customer_id": cid,
            "name": _pick(u.get("full_name"), u.get("name"), sub.get("name")),
            "email": _pick(u.get("email"), sub.get("email")),
            "mobile": _pick(u.get("mobile"), u.get("mobile_number"), sub.get("mobile"), ov.get("mobile")),
            "country": _pick(u.get("country"), sub.get("country"), ov.get("country")),
            "state": _pick(sub.get("state"), ov.get("state"), u.get("state")),
            "category": _pick(sub.get("role"), ov.get("role"), u.get("business_role")),
            "company_name": _pick(sub.get("company_name"), cd_ov.get("company_name"), cd_ov.get("name")),
            "company_email": _pick(sub.get("company_email"), cd_ov.get("company_email")),
            "company_phone": _pick(sub.get("company_phone"), cd_ov.get("company_phone")),
            "documents": docs,
            "status": sub.get("status") if applied else "not_applied",
            "applied": applied,
            "submission_id": sub.get("id") or sub.get("_id"),
            "assigned_to": sub.get("assigned_to"),
            "assigned_to_name": sub.get("assigned_to_name"),
            "review_stage": sub.get("review_stage"),
            "recommendation": sub.get("recommendation"),
            "correction_requested": sub.get("correction_requested"),
            "reasons": sub.get("reasons") or [],
            "geid": sub.get("geid"),
            "created_at": _pick(u.get("created_at"), u.get("createdAt"), sub.get("created_at")),
            "subscription": {
                "status": sc.get("status") or ("active" if sc else None),
                "plan": sc.get("plan") or sc.get("kind"),
                "until": sc.get("until") or sc.get("expires_at"),
                "source": sc.get("source"),
            } if sc else {"status": None},
            "platform_role": u.get("role") or "user",
        }

    for u in users:
        uid = u.get("uid")
        email = (u.get("email") or "").lower()
        sub = subs_by_uid.get(uid) or subs_by_email.get(email) or {}
        ov = overlays.get(uid) or {}
        if uid:
            covered_uids.add(uid)
        if email:
            covered_emails.add(email)
        rows.append(_row_from(u, sub, ov))

    # Include verification submissions that have NO matching registered user
    # (so allocated/pending applicants always surface — critical for sub-admin scope).
    for sub in subs_by_uid.values():
        suid = sub.get("uid")
        semail = (sub.get("email") or "").lower()
        if (suid and suid in covered_uids) or (semail and semail in covered_emails):
            continue
        rows.append(_row_from({}, sub, overlays.get(suid) or {}))

    if not staff.get("is_main"):
        sid = staff.get("sid")
        rows = [r for r in rows if r.get("assigned_to") == sid]

    if status:
        rows = [r for r in rows if r.get("status") == status]

    if q:
        ql = q.strip().lower()
        keys = ("email", "mobile", "customer_id", "company_name", "name", "country", "company_email", "state")
        rows = [r for r in rows if any(ql in str(r.get(k) or "").lower() for k in keys)]

    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    counts = {"total": len(rows)}
    return {"users": rows, "total": len(rows), "role": staff.get("role"),
            "is_main": staff.get("is_main"), "counts": counts}


# ---------------- Sub-admin management (main admin only) ----------------
@router.get("/admin/subadmins")
async def list_subadmins(admin: dict = Depends(require_main_admin)):
    out = []
    async for sa in SUBADMINS.find({}):
        pending = await SUBS.count_documents({"assigned_to": sa["id"], "status": "needs_review"})
        out.append({"id": sa["id"], "name": sa.get("name"), "email": sa.get("email"),
                    "username": sa.get("username"), "active": sa.get("active", True),
                    "created_at": sa.get("created_at"), "assigned_pending": pending})
    out.sort(key=lambda x: str(x.get("created_at") or ""))
    return {"subadmins": out}


class CreateSub(BaseModel):
    name: str
    email: str
    password: str


@router.post("/admin/subadmins")
async def create_subadmin(body: CreateSub, admin: dict = Depends(require_main_admin)):
    email = (body.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "A valid email is required.")
    if len((body.password or "")) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    if await SUBADMINS.find_one({"email": email}):
        raise HTTPException(409, "A sub-admin with this email already exists.")
    sid = uuid.uuid4().hex
    username = email.split("@")[0]
    await SUBADMINS.insert_one({
        "_id": sid, "id": sid, "name": (body.name or "").strip() or username,
        "username": username, "email": email, "password_hash": _hash(body.password),
        "role": "sub_admin", "active": True, "created_at": _now(),
        "created_by": admin.get("email") or "main_admin",
    })
    return {"ok": True, "id": sid, "email": email}


class SubPatch(BaseModel):
    active: Optional[bool] = None
    name: Optional[str] = None
    password: Optional[str] = None


@router.patch("/admin/subadmins/{sid}")
async def update_subadmin(sid: str, body: SubPatch, admin: dict = Depends(require_main_admin)):
    upd = {}
    if body.active is not None:
        upd["active"] = body.active
    if body.name:
        upd["name"] = body.name.strip()
    if body.password:
        if len(body.password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters.")
        upd["password_hash"] = _hash(body.password)
    if not upd:
        raise HTTPException(400, "Nothing to update.")
    res = await SUBADMINS.update_one({"id": sid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "Sub-admin not found.")
    return {"ok": True}


# ---------------- Allocation ----------------
class AllocateReq(BaseModel):
    subadmin_ids: list[str]
    submission_ids: Optional[list[str]] = None
    include_assigned: bool = False
    category: Optional[str] = None


@router.get("/admin/allocate/pending")
async def allocation_pending(admin: dict = Depends(require_main_admin)):
    unassigned_q = {"status": "needs_review",
                    "$or": [{"assigned_to": {"$in": [None, ""]}}, {"assigned_to": {"$exists": False}}]}
    return {
        "pending": await SUBS.count_documents({"status": "needs_review"}),
        "unassigned": await SUBS.count_documents(unassigned_q),
    }


# Only submissions in these states may ever be allocated to a sub-admin.
ALLOCATABLE_STATUSES = ("needs_review",)


def _missing_details(sub: dict, user: dict, ov: dict) -> list[str]:
    miss = []
    if not _pick(sub.get("mobile"), sub.get("mobile_number"), user.get("mobile"),
                 user.get("mobile_number"), ov.get("mobile")):
        miss.append("Contact number")
    if not _pick(sub.get("company_name"), (ov.get("company_details") or {}).get("company_name")):
        miss.append("Company name")
    if not _pick(sub.get("company_phone"), (ov.get("company_details") or {}).get("company_phone")):
        miss.append("Company contact")
    if not _pick(sub.get("country"), user.get("country"), ov.get("country")):
        miss.append("Country")
    if not (sub.get("document_file_id") or sub.get("selfie_file_id")):
        miss.append("Documents")
    return miss


@router.get("/admin/allocate/categories")
async def allocation_categories(admin: dict = Depends(require_main_admin)):
    """Categorised allocation candidates. Only verification-SUBMITTED users that are
    still pending review are allocatable — approved/rejected/never-applied users are
    surfaced for visibility only and can never be allocated."""
    users = await db.users.find({}).to_list(8000)
    overlays = {}
    async for o in OVERLAY.find({}):
        overlays[o.get("uid")] = o

    users_by_uid = {u.get("uid"): u for u in users if u.get("uid")}
    users_by_email = {str(u.get("email") or "").lower(): u for u in users if u.get("email")}

    submitted_uids, submitted_emails = set(), set()
    pending_unassigned, pending_assigned = [], []
    missing_details, approved, rejected = [], [], []

    async for s in SUBS.find({}):
        uid = s.get("uid")
        em = str(s.get("email") or "").lower()
        if uid:
            submitted_uids.add(uid)
        if em:
            submitted_emails.add(em)
        u = users_by_uid.get(uid) or users_by_email.get(em) or {}
        ov = overlays.get(uid) or {}
        miss = _missing_details(s, u, ov)
        item = {
            "submission_id": s.get("_id") or s.get("id"),
            "uid": uid,
            "customer_id": _pick(s.get("customer_id"), u.get("customer_id")),
            "name": _pick(s.get("name"), u.get("full_name"), u.get("name")),
            "email": _pick(s.get("email"), u.get("email")),
            "mobile": _pick(s.get("mobile"), u.get("mobile"), u.get("mobile_number"), ov.get("mobile")),
            "company_name": s.get("company_name"),
            "status": s.get("status"),
            "assigned_to": s.get("assigned_to"),
            "assigned_to_name": s.get("assigned_to_name"),
            "missing": miss,
            "created_at": s.get("created_at"),
        }
        st = s.get("status")
        if st in ALLOCATABLE_STATUSES:
            if s.get("assigned_to"):
                pending_assigned.append(item)
            else:
                pending_unassigned.append(item)
            if miss:
                missing_details.append(item)
        elif st == "verified":
            approved.append(item)
        else:
            rejected.append(item)

    no_verification = []
    for u in users:
        uid = u.get("uid")
        em = str(u.get("email") or "").lower()
        if (uid and uid in submitted_uids) or (em and em in submitted_emails):
            continue
        if u.get("is_deleted"):
            continue
        ov = overlays.get(uid) or {}
        mob = _pick(u.get("mobile"), u.get("mobile_number"), ov.get("mobile"))
        no_verification.append({
            "submission_id": None, "uid": uid, "customer_id": u.get("customer_id"),
            "name": _pick(u.get("full_name"), u.get("name")), "email": u.get("email"),
            "mobile": mob, "company_name": None, "status": "not_applied",
            "assigned_to": None, "assigned_to_name": None,
            "missing": [] if mob else ["Contact number"],
            "created_at": _pick(u.get("created_at"), u.get("createdAt")),
        })

    def _sorted(x):
        return sorted(x, key=lambda i: str(i.get("created_at") or ""))

    cats = [
        {"key": "pending_unassigned", "label": "Pending review — unassigned",
         "hint": "Verification submitted, awaiting review, not yet allocated.",
         "allocatable": True, "items": _sorted(pending_unassigned)},
        {"key": "pending_assigned", "label": "Pending review — already allocated",
         "hint": "Already with a sub-admin. Allocating again reassigns them.",
         "allocatable": True, "items": _sorted(pending_assigned)},
        {"key": "missing_details", "label": "Submitted with missing details",
         "hint": "Pending submissions missing contact number, company info or documents.",
         "allocatable": True, "items": _sorted(missing_details)},
        {"key": "no_verification", "label": "Users without verification",
         "hint": "Registered but never applied — cannot be allocated for review.",
         "allocatable": False, "items": _sorted(no_verification)},
        {"key": "approved", "label": "Approved / verified buyers",
         "hint": "Already approved — excluded from allocation.",
         "allocatable": False, "items": _sorted(approved)},
        {"key": "rejected", "label": "Rejected / closed",
         "hint": "Review already completed — excluded from allocation.",
         "allocatable": False, "items": _sorted(rejected)},
    ]
    for c in cats:
        c["count"] = len(c["items"])
    return {"categories": cats}


@router.post("/admin/allocate")
async def allocate(body: AllocateReq, admin: dict = Depends(require_main_admin)):
    sas = []
    for sid in (body.subadmin_ids or []):
        sa = await SUBADMINS.find_one({"id": sid, "active": True})
        if sa:
            sas.append(sa)
    if not sas:
        raise HTTPException(400, "Select at least one active sub-admin.")

    query = {"status": {"$in": list(ALLOCATABLE_STATUSES)}}
    if body.submission_ids:
        query["_id"] = {"$in": body.submission_ids}
        requested = len(set(body.submission_ids))
        eligible = await SUBS.count_documents(query)
        if eligible < requested:
            raise HTTPException(400, "Some selected users are not awaiting review "
                                     "(approved, rejected or never applied) and cannot be allocated.")
    elif body.category == "missing_details":
        pass  # filtered in Python below
    elif not body.include_assigned:
        query["$or"] = [{"assigned_to": {"$in": [None, ""]}}, {"assigned_to": {"$exists": False}}]
    subs = await SUBS.find(query).sort("created_at", 1).to_list(2000)
    if body.category == "missing_details" and not body.submission_ids:
        keep = []
        for s in subs:
            u = await db.users.find_one({"uid": s.get("uid")}) or {}
            ov = await OVERLAY.find_one({"uid": s.get("uid")}) or {}
            if _missing_details(s, u, ov):
                keep.append(s)
        subs = keep
    if not subs:
        return {"ok": True, "allocated": 0, "message": "No pending requests to allocate.",
                "distribution": {}}

    buckets = {sa["id"]: [] for sa in sas}
    for i, s in enumerate(subs):
        sa = sas[i % len(sas)]
        buckets[sa["id"]].append(s)
        await SUBS.update_one({"_id": s["_id"]}, {"$set": {
            "assigned_to": sa["id"], "assigned_to_name": sa.get("name"), "assigned_at": _now()}})

    import emailer
    for sa in sas:
        items = buckets[sa["id"]]
        if not items:
            continue
        try:
            await emailer.send("subadmin_allocation", sa["email"], {
                "name": sa.get("name") or "there", "count": len(items),
                "users": [{"name": it.get("name") or it.get("email") or "—",
                           "email": it.get("email") or "—",
                           "company": it.get("company_name") or "—",
                           "customerId": it.get("customer_id") or "—"} for it in items],
            })
        except Exception as exc:
            log.warning("allocation email failed for %s: %s", sa.get("email"), exc)

    return {"ok": True, "allocated": len(subs),
            "distribution": {sa.get("name"): len(buckets[sa["id"]]) for sa in sas}}


# ---------------- Nightly pending-approvals digest (01:00 IST) ----------------
async def send_pending_digest():
    """Single nightly digest to admin@vametra.com — the COUNT of pending approvals.
    No per-user emails, no emails to sub-admins (admin allocates manually)."""
    try:
        pending = await SUBS.count_documents({"status": "needs_review"})
        unassigned = await SUBS.count_documents({"status": "needs_review",
            "$or": [{"assigned_to": {"$in": [None, ""]}}, {"assigned_to": {"$exists": False}}]})
        import emailer
        await emailer.notify_admin("admin_pending_digest",
                                   {"pending": pending, "unassigned": unassigned})
        log.info("[subadmin] pending digest sent (pending=%s unassigned=%s)", pending, unassigned)
    except Exception as exc:
        log.warning("pending digest failed: %s", exc)


_pending_scheduler = None


def start_pending_digest():
    global _pending_scheduler
    if _pending_scheduler is not None:
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        _pending_scheduler = AsyncIOScheduler(timezone="UTC")
        # 01:00 IST == 19:30 UTC (IST = UTC+5:30)
        _pending_scheduler.add_job(send_pending_digest, CronTrigger(hour=19, minute=30),
                                   id="admin_pending_digest", replace_existing=True)
        _pending_scheduler.start()
        log.info("[subadmin] nightly pending-approvals digest scheduled (01:00 IST / 19:30 UTC)")
    except Exception as exc:
        log.warning("pending digest scheduler start failed: %s", exc)


# ---------------- startup seed ----------------
DEFAULT_SUBADMINS = [
    {"name": "Sakshi", "username": "sakshi", "email": "sakshi@vametra.com", "password": "Shiv@12345"},
    {"name": "PatniCA", "username": "patnica", "email": "patnica@vametra.com", "password": "Shiv@12345"},
]


async def seed_subadmins():
    try:
        await SUBADMINS.create_index("email", unique=True)
    except Exception:
        pass
    for d in DEFAULT_SUBADMINS:
        ex = await SUBADMINS.find_one({"email": d["email"]})
        if not ex:
            sid = uuid.uuid4().hex
            await SUBADMINS.insert_one({
                "_id": sid, "id": sid, "name": d["name"], "username": d["username"],
                "email": d["email"], "password_hash": _hash(d["password"]),
                "role": "sub_admin", "active": True, "created_at": _now(), "created_by": "seed",
            })
            log.info("[subadmin] seeded sub-admin %s", d["email"])
