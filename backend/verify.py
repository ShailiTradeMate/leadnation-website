"""Verified Buyer Completion + Verification — REFERENCE implementation.

The website is a CLIENT of the shared DigitalOcean (DO) identity backend, which
OWNS identity, the shared profile, Customer IDs, the GEID entity graph and the
members_bridge. This module is a working blueprint for the capabilities the DO
backend does not yet expose (object-storage upload, selfie/liveness + AI-fake +
duplicate-face checks, document OCR, a submit->review->decision workflow). The
DO team can mirror this logic server-side.

Boundaries kept intact:
  * Profile reads/writes proxy to DO  (GET/PUT /v1/profiles/{uid}).
  * On approval we LINK the user as a Verified Buyer via DO's live endpoints
    (POST /entities + POST /members/bind) — we never write the entity graph here.
  * Verification artefacts (submissions, face index) live in local Mongo only as
    a reference store; production ownership belongs to DO.
"""
import os
import io
import time
import uuid
import base64
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from PIL import Image
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from core import db, require_admin
from firebase_auth import require_user
import storage
import verify_ai

router = APIRouter(prefix="/verify")
log = logging.getLogger("verify")

SUBS = db.verification_submissions
FACE_INDEX = db.verification_face_index

DO_BASE = os.environ.get("AUTH_API_BASE", "").rstrip("/")

# ---- decision thresholds (tunable) ----
AUTO_APPROVE_MIN = 0.75      # overall confidence for instant "verified"
AI_FAKE_MAX = 0.35           # above this selfie is rejected
QUALITY_MIN = 0.40
DOC_CONF_MIN = 0.40
FACE_DUP_MAX_DISTANCE = 8    # Hamming distance <= this ⇒ same face

REQUIRED_FIELDS = [
    ("name", "Full name"),
    ("mobile", "Mobile number"),
    ("email", "Email address"),
    ("country", "Country"),
    ("city", "City"),
    ("products", "Products you trade"),
    ("company_details.company_name", "Company name"),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_nested(obj: dict, path: str):
    cur = obj or {}
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _is_filled(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


# ---------------- DO backend proxy ----------------
def _do_headers(authorization: Optional[str], uid: str) -> dict:
    h = {"x-user-uid": uid}
    if authorization:
        h["Authorization"] = authorization
    return h


def _do_get_profile(uid: str, authorization: Optional[str]) -> dict:
    if not DO_BASE:
        return {}
    try:
        r = requests.get(f"{DO_BASE}/v1/profiles/{uid}", headers=_do_headers(authorization, uid), timeout=20)
        if r.ok:
            return r.json() or {}
    except Exception as exc:
        log.warning("DO get_profile failed: %s", exc)
    return {}


def _do_put_profile(uid: str, patch: dict, authorization: Optional[str]) -> dict:
    if not DO_BASE:
        return {"ok": False, "error": "DO backend not configured"}
    last = None
    for attempt in range(3):  # DO occasionally 502s — retry transient 5xx with small backoff
        try:
            r = requests.put(f"{DO_BASE}/v1/profiles/{uid}", json=patch,
                             headers=_do_headers(authorization, uid), timeout=30)
            if r.ok:
                return {"ok": True, "status": r.status_code, "data": (r.json() if r.content else {})}
            if r.status_code < 500:
                return {"ok": False, "status": r.status_code}
            last = r.status_code
        except Exception as exc:
            last = str(exc)
            log.warning("DO put_profile attempt %s failed: %s", attempt + 1, exc)
        time.sleep(0.6 * (attempt + 1))
    return {"ok": False, "status": last, "error": f"Shared profile service unavailable ({last})"}


def _do_link_buyer(uid: str, customer_id, profile: dict, entity_type: str,
                   authorization: Optional[str]) -> dict:
    """Create the Verified Buyer entity (GEID) + members_bridge via DO's live endpoints.
    Resilient: returns {geid, linked} and never raises."""
    if not DO_BASE:
        return {"linked": False, "error": "DO backend not configured"}
    cd = profile.get("company_details") or {}
    name = cd.get("company_name") or cd.get("name") or profile.get("name") or "Member"
    payload = {
        "type": entity_type,
        "name": name,
        "country": profile.get("country") or profile.get("country_code"),
        "city": profile.get("city"),
        "customer_id": customer_id,
        "uid": uid,
        "products": profile.get("products") or [],
        "hsn_codes": profile.get("hsn_codes") or [],
    }
    geid = None
    try:
        r = requests.post(f"{DO_BASE}/entities", json=payload,
                          headers=_do_headers(authorization, uid), timeout=25)
        if r.ok and r.content:
            d = r.json() or {}
            geid = d.get("geid") or (d.get("entity") or {}).get("geid") or d.get("id") or d.get("_id")
    except Exception as exc:
        log.warning("DO create entity failed: %s", exc)
    if geid:
        try:
            requests.post(f"{DO_BASE}/members/bind",
                          json={"uid": uid, "customer_id": customer_id, "geid": geid},
                          headers=_do_headers(authorization, uid), timeout=25)
        except Exception as exc:
            log.warning("DO members/bind failed: %s", exc)
    return {"linked": bool(geid), "geid": geid}


# ---------------- image helpers ----------------
def _ahash(image_bytes: bytes) -> Optional[str]:
    """Dependency-free 64-bit average hash (perceptual) → 16-char hex."""
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("L").resize((8, 8), Image.LANCZOS)
        px = list(im.getdata())
        avg = sum(px) / len(px)
        bits = 0
        for i, p in enumerate(px):
            if p >= avg:
                bits |= (1 << i)
        return f"{bits:016x}"
    except Exception:
        return None


def _hamming(a: str, b: str) -> int:
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except Exception:
        return 999


async def _load_image_b64(file_id: str, owner: str):
    rec = await db.uploaded_files.find_one({"_id": file_id, "is_deleted": False})
    if not rec:
        raise HTTPException(404, "Uploaded file not found")
    data, ctype = storage.get_provider().get(rec["storage_path"])
    return base64.b64encode(data).decode("ascii"), data, ctype


# ---------------- completion state ----------------
def _completion(profile: dict) -> dict:
    missing = []
    for path, label in REQUIRED_FIELDS:
        if not _is_filled(_get_nested(profile, path)):
            missing.append({"field": path, "label": label})
    total = len(REQUIRED_FIELDS)
    filled = total - len(missing)
    return {"percent": round(100 * filled / total), "filled": filled, "total": total, "missing": missing}


def _clean_submission(doc: dict) -> dict:
    if not doc:
        return None
    doc = dict(doc)
    doc.pop("_id", None)
    return doc


# ================= ENDPOINTS =================
@router.get("/state")
async def verify_state(user: dict = Depends(require_user),
                       authorization: Optional[str] = Header(default=None)):
    uid = user["uid"]
    profile = _do_get_profile(uid, authorization)
    sub = await SUBS.find_one({"uid": uid}, sort=[("created_at", -1)])
    return {
        "uid": uid,
        "profile": profile,
        "completion": _completion(profile),
        "verification_status": (sub or {}).get("status") or profile.get("verification_status") or "unverified",
        "submission": _clean_submission(sub),
        "geid": (sub or {}).get("geid") or profile.get("geid"),
    }


@router.get("/documents")
async def verify_documents(country: Optional[str] = None,
                           user: dict = Depends(require_user),
                           authorization: Optional[str] = Header(default=None)):
    """Proxy the DO country-specific document catalog."""
    if not DO_BASE:
        return {"documents": []}
    try:
        params = {"country": country} if country else {}
        r = requests.get(f"{DO_BASE}/v1/documents", params=params,
                         headers=_do_headers(authorization, user["uid"]), timeout=20)
        if r.ok:
            return r.json()
    except Exception as exc:
        log.warning("DO documents failed: %s", exc)
    return {"documents": []}


class ProfilePatch(BaseModel):
    patch: dict


@router.put("/profile")
async def update_profile(body: ProfilePatch, user: dict = Depends(require_user),
                         authorization: Optional[str] = Header(default=None)):
    """Fill in missing shared-profile fields (proxied to DO — DO owns the write)."""
    uid = user["uid"]
    res = _do_put_profile(uid, body.patch, authorization)
    if not res.get("ok"):
        raise HTTPException(502, f"Could not update shared profile: {res.get('error') or res.get('status')}")
    profile = _do_get_profile(uid, authorization)
    return {"ok": True, "profile": profile, "completion": _completion(profile)}


@router.post("/upload")
async def verify_upload(file: UploadFile = File(...), kind: str = Form("document"),
                        user: dict = Depends(require_user)):
    """Store a selfie or business document in object storage (never base64-in-DB)."""
    uid = user["uid"]
    ext = (file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 10 MB).")
    ctype = file.content_type or storage.MIME_TYPES.get(ext, "application/octet-stream")
    path = f"{storage.APP_NAME}/verify/{uid}/{kind}/{uuid.uuid4().hex}.{ext}"
    try:
        result = storage.get_provider().put(path, data, ctype)
    except Exception as exc:
        log.error("verify upload failed: %s", exc)
        raise HTTPException(502, "Upload failed. Please retry.")
    fid = uuid.uuid4().hex
    await db.uploaded_files.insert_one({
        "_id": fid, "id": fid, "storage_path": result.get("path", path),
        "original_filename": file.filename, "content_type": ctype,
        "size": result.get("size", len(data)), "owner": uid, "kind": f"verify:{kind}",
        "provider": storage.get_provider().name, "is_deleted": False, "created_at": _now()})
    return {"id": fid, "url": f"/api/storage/file/{fid}", "kind": kind,
            "filename": file.filename, "size": result.get("size", len(data))}


class SelfieReq(BaseModel):
    file_id: str


@router.post("/analyze-selfie")
async def analyze_selfie_ep(body: SelfieReq, user: dict = Depends(require_user)):
    uid = user["uid"]
    b64, raw, _ = await _load_image_b64(body.file_id, uid)
    result = await verify_ai.analyze_selfie(b64, session=f"selfie-{uid}")

    # Duplicate-face check (perceptual hash vs OTHER users' verified selfies).
    ah = _ahash(raw)
    duplicate, dup_uid = False, None
    if ah:
        async for rec in FACE_INDEX.find({"uid": {"$ne": uid}}):
            if _hamming(ah, rec.get("hash", "")) <= FACE_DUP_MAX_DISTANCE:
                duplicate, dup_uid = True, rec.get("uid")
                break
    result["duplicate_face"] = duplicate
    result["face_hash"] = ah
    passed = (result.get("is_human_face") and not duplicate
              and float(result.get("ai_generated_likelihood") or 1) <= AI_FAKE_MAX
              and float(result.get("quality_score") or 0) >= QUALITY_MIN)
    result["passed"] = bool(passed)
    return result


class DocReq(BaseModel):
    file_id: str
    doc_type: Optional[str] = None


@router.post("/analyze-document")
async def analyze_document_ep(body: DocReq, user: dict = Depends(require_user),
                              authorization: Optional[str] = Header(default=None)):
    uid = user["uid"]
    profile = _do_get_profile(uid, authorization)
    cd = profile.get("company_details") or {}
    b64, _, _ = await _load_image_b64(body.file_id, uid)
    result = await verify_ai.analyze_document(
        b64, expected_name=cd.get("company_name") or cd.get("name") or profile.get("name") or "",
        expected_country=profile.get("country") or "", session=f"doc-{uid}")
    passed = (result.get("is_business_document")
              and float(result.get("confidence") or 0) >= DOC_CONF_MIN
              and not result.get("tamper_signs"))
    result["passed"] = bool(passed)
    return result


class SubmitReq(BaseModel):
    role: str
    consent: bool
    selfie_file_id: str
    document_file_id: Optional[str] = None
    doc_type: Optional[str] = None
    profile_patch: Optional[dict] = None


def _entity_type_for(role: str) -> str:
    r = (role or "").lower()
    if any(k in r for k in ("import", "buyer", "wholesal", "distribut", "both")):
        return "member_company"
    return "prospect"


def _decide(selfie: dict, doc: dict) -> tuple:
    """Return (status, overall_confidence, reasons)."""
    reasons = []
    if selfie.get("duplicate_face"):
        return "rejected", 0.0, ["This face is already registered to another account."]
    if not selfie.get("is_human_face"):
        return "rejected", 0.0, ["No genuine human face detected in the selfie."]
    if float(selfie.get("ai_generated_likelihood") or 0) > AI_FAKE_MAX:
        return "rejected", float(selfie.get("confidence_real_person") or 0), \
            ["Selfie appears AI-generated / manipulated."]
    selfie_conf = float(selfie.get("confidence_real_person") or 0)
    doc_conf = float(doc.get("confidence") or 0) if doc else 0.0
    has_doc = bool(doc and doc.get("available") is not False and doc.get("is_business_document"))
    overall = round(selfie_conf * 0.6 + (doc_conf if has_doc else 0.0) * 0.4, 3)
    if not selfie.get("available", True) or (doc and doc.get("available") is False):
        reasons.append("Automated analysis unavailable for one or more items.")
        return "needs_review", overall, reasons
    if overall >= AUTO_APPROVE_MIN and float(selfie.get("quality_score") or 0) >= QUALITY_MIN and has_doc:
        return "verified", overall, ["Automated identity + document checks passed."]
    reasons.append("Confidence below auto-approval threshold — queued for human review.")
    return "needs_review", overall, reasons


@router.post("/submit")
async def submit_verification(body: SubmitReq, user: dict = Depends(require_user),
                              authorization: Optional[str] = Header(default=None)):
    uid = user["uid"]
    if not body.consent:
        raise HTTPException(400, "Consent to be listed as a Verified Buyer is required.")

    # 1) Persist any missing profile fields + role to the SHARED profile (DO owns it).
    profile0 = _do_get_profile(uid, authorization)
    patch = dict(body.profile_patch or {})
    if (profile0.get("role") or "") != "admin":  # never demote a platform admin
        patch["role"] = body.role
    patch["contact_visibility_flag"] = True
    _do_put_profile(uid, patch, authorization)
    profile = _do_get_profile(uid, authorization)

    # 2) Re-run the automated checks server-side (never trust the client's verdict).
    selfie_b64, selfie_raw, _ = await _load_image_b64(body.selfie_file_id, uid)
    selfie = await verify_ai.analyze_selfie(selfie_b64, session=f"selfie-{uid}")
    ah = _ahash(selfie_raw)
    selfie["face_hash"] = ah
    selfie["duplicate_face"] = False
    if ah:
        async for rec in FACE_INDEX.find({"uid": {"$ne": uid}}):
            if _hamming(ah, rec.get("hash", "")) <= FACE_DUP_MAX_DISTANCE:
                selfie["duplicate_face"] = True
                break

    doc = None
    if body.document_file_id:
        cd = profile.get("company_details") or {}
        doc_b64, _, _ = await _load_image_b64(body.document_file_id, uid)
        doc = await verify_ai.analyze_document(
            doc_b64, expected_name=cd.get("company_name") or cd.get("name") or profile.get("name") or "",
            expected_country=profile.get("country") or "", session=f"doc-{uid}")

    status, overall, reasons = _decide(selfie, doc)

    # 3) On auto-approval, LINK the Verified Buyer via DO (GEID + members_bridge).
    link = {"linked": False}
    if status == "verified":
        link = _do_link_buyer(uid, profile.get("customer_id"), profile,
                              _entity_type_for(body.role), authorization)
        _do_put_profile(uid, {"verification_status": "verified"}, authorization)
        if ah:
            await FACE_INDEX.update_one(
                {"uid": uid}, {"$set": {"uid": uid, "hash": ah, "updated_at": _now()}}, upsert=True)

    sid = uuid.uuid4().hex
    submission = {
        "_id": sid, "id": sid, "uid": uid, "customer_id": profile.get("customer_id"),
        "role": body.role, "entity_type": _entity_type_for(body.role),
        "status": status, "confidence": overall, "reasons": reasons,
        "checks": {"selfie": selfie, "document": doc},
        "selfie_file_id": body.selfie_file_id, "document_file_id": body.document_file_id,
        "consent": True, "geid": link.get("geid"), "linked": link.get("linked"),
        "created_at": _now(), "updated_at": _now(),
    }
    await SUBS.insert_one(submission)
    return {"status": status, "confidence": overall, "reasons": reasons,
            "geid": link.get("geid"), "linked": link.get("linked"),
            "submission": _clean_submission(submission),
            "verification_status": status,
            "completion": _completion(profile)}


# ---------------- Admin human-review ----------------
@router.get("/admin/queue")
async def admin_queue(status: str = "needs_review", _: dict = Depends(require_admin)):
    cur = SUBS.find({"status": status}).sort("created_at", -1).limit(200)
    items = [_clean_submission(d) async for d in cur]
    counts = {}
    for s in ("needs_review", "verified", "rejected"):
        counts[s] = await SUBS.count_documents({"status": s})
    return {"items": items, "counts": counts}


class DecideReq(BaseModel):
    decision: str  # "approve" | "reject"
    note: Optional[str] = None


@router.post("/admin/{sid}/decide")
async def admin_decide(sid: str, body: DecideReq, admin: dict = Depends(require_admin),
                       authorization: Optional[str] = Header(default=None)):
    sub = await SUBS.find_one({"_id": sid})
    if not sub:
        raise HTTPException(404, "Submission not found")
    uid = sub["uid"]
    profile = _do_get_profile(uid, authorization)
    if body.decision == "approve":
        link = _do_link_buyer(uid, profile.get("customer_id"), profile,
                              sub.get("entity_type") or "prospect", authorization)
        _do_put_profile(uid, {"verification_status": "verified"}, authorization)
        fh = (sub.get("checks") or {}).get("selfie", {}).get("face_hash")
        if fh:
            await FACE_INDEX.update_one({"uid": uid},
                {"$set": {"uid": uid, "hash": fh, "updated_at": _now()}}, upsert=True)
        await SUBS.update_one({"_id": sid}, {"$set": {
            "status": "verified", "geid": link.get("geid"), "linked": link.get("linked"),
            "reviewer": admin.get("email") or admin.get("uid"), "review_note": body.note,
            "updated_at": _now()}})
        return {"ok": True, "status": "verified", "geid": link.get("geid")}
    else:
        _do_put_profile(uid, {"verification_status": "rejected"}, authorization)
        await SUBS.update_one({"_id": sid}, {"$set": {
            "status": "rejected", "reviewer": admin.get("email") or admin.get("uid"),
            "review_note": body.note, "updated_at": _now()}})
        return {"ok": True, "status": "rejected"}
