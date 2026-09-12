"""Shared buyer membership: presentation on the existing GEID, never a new identity."""
import asyncio
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from core import db
from firebase_auth import require_user

router = APIRouter(prefix="/buyer-membership")
BUYER_Q = {"$or": [{"entity_type": "buyer"}, {"verified_buyer": True}]}
PUBLIC_Q = {"$and": [BUYER_Q], "status": "active", "merged_into": None,
            "admin_deleted": {"$ne": True}, "has_contact": True}


def now():
    return datetime.now(timezone.utc).isoformat()


def entity_query(geid):
    return {"$and": [BUYER_Q, {"$or": [{"geid": geid}, {"_id": geid}]}]}


def validate_profile_patch(patch):
    allowed = {"name", "mobile", "mobile_number", "country", "state", "city", "address",
               "products", "hsn_codes", "role", "company_details"}
    if set(patch) - allowed:
        raise HTTPException(400, "Identity, verification and permission fields cannot be edited here.")
    if "role" in patch and str(patch["role"]).lower() not in {
        "importer", "exporter", "both", "both (import & export)", "wholesaler", "distributor", "manufacturer", "trader", "buyer"}:
        raise HTTPException(400, "Select a valid business category.")
    cd = patch.get("company_details", {})
    if not isinstance(cd, dict) or set(cd) - {"company_name", "company_email", "company_phone", "address", "description", "gst", "tax_id", "name"}:
        raise HTTPException(400, "Invalid company fields.")
    return patch


def norm_name(value):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", str(value or "")).casefold())


def norm_phone(value, country):
    import phonenumbers
    import pycountry
    try:
        region = pycountry.countries.lookup(country).alpha_2
        number = phonenumbers.parse(str(value), region)
        if not phonenumbers.is_possible_number(number):
            return None
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None


async def registry_candidate(profile):
    """All three exact normalized values must match; missing/ambiguous => manual path."""
    cd = profile.get("company_details") or {}
    name = norm_name(cd.get("company_name"))
    email = str(profile.get("email") or "").strip().casefold()
    phone = norm_phone(profile.get("mobile") or profile.get("mobile_number"), profile.get("country"))
    if not all((name, email, phone)):
        return None
    # Match email first using an anchored escaped predicate, then normalized company/phone.
    q = {**PUBLIC_Q, "entity_type": "buyer", "source_verified": True,
         "sample": {"$ne": True}, "contact.email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}
    matches = []
    async for e in db.entities.find(q, {"_id": 0}).limit(100):
        if norm_name(e.get("legal_name") or e.get("display_name")) != name:
            continue
        if norm_phone((e.get("contact") or {}).get("phone"), e.get("country") or e.get("country_name")) != phone:
            continue
        if not e.get("provenance"):
            continue
        matches.append(e)
    return matches[0] if len(matches) == 1 else None


@router.post("/check")
async def check_match(user: dict = Depends(require_user), authorization: Optional[str] = Header(default=None)):
    import verify
    uid = user["uid"]
    latest = await db.verification_submissions.find_one({"uid": uid}, {"_id": 0}, sort=[("created_at", -1)])
    if latest and latest.get("status") == "verified":
        return {"match": None, "status": "approved"}
    profile = await verify._profile(uid, authorization)
    # Account email comes from the authenticated Firebase identity, not editable profile input.
    profile["email"] = user.get("email") or profile.get("email")
    e = await registry_candidate(profile)
    if not e:
        await db.registry_matches.update_one({"uid": uid, "status": {"$in": ["candidate", "accepted"]}},
                                            {"$set": {"status": "stale"}})
        return {"match": None, "status": "manual_verification"}
    old = await db.registry_matches.find_one({"uid": uid}, {"_id": 0}) or {}
    status = old.get("status") if old.get("geid") == e["geid"] and old.get("status") in ("accepted", "needs_review", "approved") else "candidate"
    await db.registry_matches.update_one({"uid": uid}, {"$set": {"uid": uid, "geid": e["geid"],
        "status": status, "matched_fields": ["company_name", "email", "mobile"], "checked_at": now()}}, upsert=True)
    return {"match": {"company_name": e.get("legal_name"), "country": e.get("country_name"),
                       "address": (e.get("contact") or {}).get("address")}, "status": status}


@router.post("/accept")
async def accept_match(user: dict = Depends(require_user), authorization: Optional[str] = Header(default=None)):
    result = await check_match(user, authorization)
    if not result.get("match"):
        raise HTTPException(409, "No unique registry match. Continue with standard verification.")
    if result["status"] not in ("candidate", "accepted"):
        raise HTTPException(409, "This application is already under review.")
    await db.registry_matches.update_one({"uid": user["uid"]}, {"$set": {"status": "accepted", "accepted_at": now()}})
    return {"ok": True, "status": "accepted", "next": "/verify"}


async def sync_approved_member(uid, profile=None, submission=None):
    """Update buyer presentation on the existing entity, keeping private PII out of public fields."""
    import verify
    s = submission or await db.verification_submissions.find_one({"uid": uid}, {"_id": 0}, sort=[("updated_at", -1), ("created_at", -1)]) or {}
    if s.get("status") != "verified" or not s.get("geid") or not s.get("consent"):
        return
    p = profile or await verify._profile(uid, None)
    geid = s["geid"]
    e = await db.entities.find_one({"geid": geid}, {"_id": 0})
    if not e:
        raise HTTPException(502, "The shared GEID is not available yet. Please retry approval.")
    cd = p.get("company_details") or {}
    update = {"verified_buyer": True, "member_verified_at": now(), "updated_at": datetime.now(timezone.utc)}
    # Registry provenance/contact stay untouched; a registered member is additional evidence.
    if e.get("entity_type") != "buyer":
        country = p.get("country") or s.get("country") or ""
        import pycountry
        try:
            c = pycountry.countries.lookup(country)
            code, country_name = c.alpha_2, c.name
        except LookupError:
            code, country_name = country, country
        contact = {"email": cd.get("company_email") or s.get("company_email") or "",
                   "phone": cd.get("company_phone") or s.get("company_phone") or "",
                   "address": cd.get("address") or "", "city": p.get("city") or s.get("city") or ""}
        company = cd.get("company_name") or s.get("company_name")
        update.update({"legal_name": company, "display_name": company,
            "country": code, "country_name": country_name, "city": contact["city"],
            "products": p.get("products") or [], "sector": e.get("sector") or "Member businesses",
            "contact": contact, "has_contact": bool(contact["email"] or contact["phone"]),
            "status": "active" if not e.get("admin_deleted") else "deleted", "sample": False,
            "last_verified": now(), "listing_origin": "member_kyc",
            "trust": {"band": "Verified", "score": None, "color": "#34d399",
                "factors": [{"label": "Member KYC", "detail": "Identity and company documents reviewed"}]}})
    await db.entities.update_one({"geid": geid}, {"$set": update, "$addToSet": {"verified_member_uids": uid}})


async def remove_member_listing(uid):
    async for e in db.entities.find({"verified_member_uids": uid}, {"_id": 0}):
        remaining = [u for u in e.get("verified_member_uids", []) if u != uid]
        update = {"verified_member_uids": remaining, "verified_buyer": bool(remaining)}
        if not remaining and e.get("listing_origin") == "member_kyc":
            update["status"] = "unverified"
        await db.entities.update_one({"geid": e["geid"]}, {"$set": update})


async def set_shared_verification(customer_id, status, admin_authorization):
    import verify
    import requests
    if not admin_authorization:
        raise HTTPException(403, "A main-admin session is required for shared verification.")
    headers = {"Authorization": admin_authorization}
    url = f"{verify.DO_BASE}/admin_v2/users/{customer_id}"
    try:
        if status == "verified":
            r = await asyncio.to_thread(requests.post, f"{url}/approve", headers=headers, timeout=25)
        else:
            r = await asyncio.to_thread(requests.put, url, headers=headers,
                json={"verification_status": status}, timeout=25)
        if not r.ok:
            raise HTTPException(502, "Shared verification update was not confirmed.")
        check = await asyncio.to_thread(requests.get, url, headers=headers, timeout=25)
        data = check.json() if check.ok else {}
        data = data.get("user") or data.get("data") or data
        expected = {"approved", "verified"} if status == "verified" else {status}
        if data.get("verification_status") not in expected:
            raise HTTPException(502, "Shared identity service did not persist the verification status.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Shared identity service is unavailable; retry sign-off.")


async def approve_membership(uid, sub, profile, authorization, admin_authorization=None):
    import verify
    profile = verify._merge_supplement(sub, profile)
    cd = dict(profile.get("company_details") or {})
    for k in ("company_name", "company_email", "company_phone"):
        if not cd.get(k):
            cd[k] = sub.get(k)
    profile["company_details"] = cd
    if not sub.get("selfie_file_id") or not sub.get("document_file_id"):
        raise HTTPException(400, "A selfie and company KYC document are required for approval.")
    if not profile.get("customer_id"):
        from admin_ops import _user_doc
        profile["customer_id"] = (await _user_doc(uid)).get("customer_id")
    if not profile.get("customer_id"):
        raise HTTPException(409, "Customer ID is not available from the shared identity service. Complete account onboarding first.")
    bridge = await db.members_bridge.find_one({"uid": uid}, {"_id": 0}) or {}
    match = await db.registry_matches.find_one({"uid": uid, "status": {"$in": ["accepted", "needs_review"]}}, {"_id": 0})
    target = sub.get("geid") or bridge.get("geid")
    if match:
        e = await registry_candidate(profile)
        if not e or e.get("geid") != match["geid"]:
            raise HTTPException(409, "Registry details changed. Re-check company, email and mobile before approval.")
        if not sub.get("selfie_file_id") or not sub.get("document_file_id"):
            raise HTTPException(400, "Selfie and company KYC document are required.")
        if target and target != match["geid"]:
            raise HTTPException(409, "Existing company binding differs. Resolve the GEID conflict on the identity service first.")
        target = match["geid"]
    if target:
        profile["_existing_geid"] = target
    link = await asyncio.to_thread(verify._do_link_buyer, uid, profile.get("customer_id"), profile,
                                  sub.get("entity_type") or "member_company", authorization)
    if not link.get("linked") or not link.get("geid"):
        raise HTTPException(502, "Shared identity binding was not confirmed. Approval has not completed.")
    # Mirror ONLY the authoritative DO readback, under its existing identifiers. In production
    # these are already present in the shared DB; preview uses an isolated snapshot/cache.
    if not link.get("entity") or not link.get("bridge"):
        raise HTTPException(502, "Shared membership readback is incomplete.")
    await db.entities.update_one({"geid": link["geid"]}, {"$setOnInsert": {
        **link["entity"], "_id": link["geid"], "canonical_source": "do_identity"}}, upsert=True)
    await db.members_bridge.update_one({"uid": uid}, {"$set": link["bridge"]}, upsert=True)
    await set_shared_verification(profile["customer_id"], "verified", admin_authorization)
    await sync_approved_member(uid, profile, {**sub, "status": "verified", "geid": link["geid"]})
    if match:
        await db.registry_matches.update_one({"uid": uid}, {"$set": {"status": "approved", "approved_at": now()}})
    return link