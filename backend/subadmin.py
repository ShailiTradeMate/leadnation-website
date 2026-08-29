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

    subs_by_uid, subs_by_email = {}, {}
    async for s in SUBS.find({}).sort("created_at", 1):  # asc → last wins = latest
        if s.get("uid"):
            subs_by_uid[s["uid"]] = s
        if s.get("email"):
            subs_by_email[str(s["email"]).lower()] = s

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
    for u in users:
        uid = u.get("uid")
        email = (u.get("email") or "").lower()
        sub = subs_by_uid.get(uid) or subs_by_email.get(email) or {}
        ov = overlays.get(uid) or {}
        cd_ov = (ov.get("company_details") or {})
        cid = u.get("customer_id")
        sc = subscriptions.get(str(uid)) or subscriptions.get(str(cid)) or {}

        docs = []
        if sub.get("selfie_file_id"):
            docs.append({"kind": "selfie", "label": "Selfie", "file_id": sub["selfie_file_id"],
                         "url": _file_url(sub["selfie_file_id"])})
        if sub.get("document_file_id"):
            docs.append({"kind": "document", "label": sub.get("doc_type") or "Business document",
                         "file_id": sub["document_file_id"], "url": _file_url(sub["document_file_id"])})

        applied = bool(sub)
        rows.append({
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
        })

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
