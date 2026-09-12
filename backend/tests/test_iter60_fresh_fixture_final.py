"""Iter 60 — FINAL fresh-fixture verification after auth precedence fix.

Flow scope (live, strict):
1) NEW disposable signup + onboarding + seeded KYC fixture allocation
2) Sub-admin subscription grant -> main approval -> new user contact reveal 200
3) Sub-admin review approve -> main approval -> shared identity/GEID consistency
4) Bulk approvals (profile + subscription + document) with deferred-apply checks
5) Sub-admin reject recommendation -> main approve => rejected + listing removal

NOTE: hard-delete is intentionally separated to run ONLY after UI step passes.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime

import pytest
import requests
from pymongo import MongoClient


def _read_env(path: str, key: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.startswith(f"{key}="):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return ""
    return ""


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
AUTH_API_BASE = (os.environ.get("AUTH_API_BASE") or os.environ.get("REACT_APP_AUTH_API_BASE") or _read_env("/app/frontend/.env", "REACT_APP_AUTH_API_BASE")).rstrip("/")
FIREBASE_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY") or _read_env("/app/frontend/.env", "REACT_APP_FIREBASE_API_KEY")
MONGO_URL = os.environ.get("MONGO_URL") or _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or _read_env("/app/backend/.env", "DB_NAME")

MAIN_ADMIN_EMAIL = "admin@vametra.com"
MAIN_ADMIN_PW = "Shiv@12345"
MAIN_ADMIN_UID = "gq5pHUPD3LPXNhycRHSdhmkhPiS2"
MAIN_ADMIN_BASELINE_GEID = "LN-prospect-01M0BHNNNRZ54328SK9JDRMDPJ"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PW = "Shiv@12345"
REAL_BUYER_GEID = "LN-prospect-01M0BHNNNRZ54328SK9JDRMDPJ"

ITER60_STATE = "/app/test_reports/iter60_fixture_state.json"


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    last = None
    for i in range(3):
        last = requests.request(method, url, **kwargs)
        if last.status_code not in (502, 503, 504):
            return last
        time.sleep(0.8 * (i + 1))
    return last


def _fb_signup(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=40,
    )


def _fb_signin(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=40,
    )


def _append_test_credential_line(email: str, password: str, uid: str, customer_id: str):
    line = (
        f"\n- Iter60 disposable (KEEP until final delete): {email} / {password} / uid {uid} / customer_id {customer_id}"
        " / SEEDED KYC fixture (document-analysis bytes, not live OCR)\n"
    )
    with open("/app/memory/test_credentials.md", "a", encoding="utf-8") as f:
        f.write(line)


def _save_state(payload: dict):
    with open(ITER60_STATE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


@pytest.fixture(scope="module")
def session() -> requests.Session:
    if not BASE_URL or not AUTH_API_BASE or not FIREBASE_KEY:
        pytest.skip("Missing BASE/AUTH_API_BASE/FIREBASE key env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def mongo_db():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Missing MONGO_URL/DB_NAME")
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


@pytest.fixture(scope="module")
def main_headers() -> dict:
    r = _fb_signin(MAIN_ADMIN_EMAIL, MAIN_ADMIN_PW)
    if r.status_code != 200:
        pytest.skip(f"Main admin Firebase login failed: {r.status_code} {r.text[:160]}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


@pytest.fixture(scope="module")
def sub_headers(session) -> dict:
    r = session.post(
        f"{BASE_URL}/api/admin-auth/login",
        json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PW},
        timeout=40,
    )
    if r.status_code != 200:
        pytest.skip(f"Sub-admin login failed: {r.status_code} {r.text[:160]}")
    return {"X-Staff-Token": r.json()["token"]}


@pytest.fixture(scope="module")
def fixture_ctx(session, main_headers, sub_headers, mongo_db) -> dict:
    # Module-wide mutable state (single disposable fixture only).
    ctx = {
        "email": "",
        "password": "",
        "uid": "",
        "customer_id": "",
        "id_token": "",
        "submission_id": "",
        "selfie_file_id": "",
        "document_file_id": "",
        "approved_geid": "",
        "before_main_bridge": sorted(list(mongo_db.members_bridge.find(
            {"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1}
        ))),
        "staff_token": sub_headers["X-Staff-Token"],
        "main_authz": main_headers["Authorization"],
    }
    return ctx


# auth precedence verification: mixed header must resolve main admin over stale staff token
def test_00_mixed_header_precedence_main_wins(session, main_headers, sub_headers):
    mixed = session.get(
        f"{BASE_URL}/api/admin/approvals",
        headers={"Authorization": main_headers["Authorization"], "X-Staff-Token": sub_headers["X-Staff-Token"]},
        timeout=60,
    )
    assert mixed.status_code == 200, mixed.text
    assert mixed.json().get("is_main") is True

    pure_staff = session.get(
        f"{BASE_URL}/api/admin/approvals",
        headers={"X-Staff-Token": sub_headers["X-Staff-Token"]},
        timeout=60,
    )
    assert pure_staff.status_code == 200, pure_staff.text
    assert pure_staff.json().get("is_main") is False


# fixture setup: NEW disposable signup + onboarding + seeded KYC docs + allocation
def test_01_create_new_disposable_fixture_and_allocate(session, mongo_db, main_headers, fixture_ctx):
    # Reuse existing iter60 fixture on reruns to avoid creating extra disposable users.
    if os.path.exists(ITER60_STATE):
        try:
            with open(ITER60_STATE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("email") and existing.get("password") and existing.get("uid"):
                probe = _fb_signin(existing["email"], existing["password"])
                if probe.status_code == 200:
                    fixture_ctx.update(existing)
                    return
        except Exception:
            pass

    email = f"test_iter60_{int(time.time())}_{uuid.uuid4().hex[:5]}@example.com"
    password = "Iter60@Test123"

    su = _fb_signup(email, password)
    assert su.status_code == 200, su.text
    sign = su.json()
    uid = sign["localId"]
    id_token = sign["idToken"]

    reg = session.post(
        f"{AUTH_API_BASE}/onboarding/register",
        headers={"Authorization": f"Bearer {id_token}"},
        json={"full_name": "TEST Workflow60 User", "role": "importer", "provider": "password"},
        timeout=45,
    )
    assert reg.status_code == 200, reg.text
    customer_id = str(reg.json().get("customer_id") or "")
    assert customer_id

    _append_test_credential_line(email, password, uid, customer_id)

    # Seed fixture files (document-analysis bytes only; not live OCR).
    up_selfie = requests.post(
        f"{BASE_URL}/api/verify/upload",
        headers={"Authorization": f"Bearer {id_token}"},
        data={"kind": "selfie"},
        files={"file": ("iter60_selfie.jpg", b"iter60-seeded-selfie", "image/jpeg")},
        timeout=90,
    )
    assert up_selfie.status_code == 200, up_selfie.text
    selfie_file_id = up_selfie.json()["id"]

    up_doc = requests.post(
        f"{BASE_URL}/api/verify/upload",
        headers={"Authorization": f"Bearer {id_token}"},
        data={"kind": "document"},
        files={"file": ("iter60_doc.pdf", b"iter60-seeded-document", "application/pdf")},
        timeout=90,
    )
    assert up_doc.status_code == 200, up_doc.text
    document_file_id = up_doc.json()["id"]

    submission_id = f"ITER60_SUB_{uid}"
    mongo_db.verification_submissions.update_one(
        {"_id": submission_id},
        {
            "$set": {
                "id": submission_id,
                "uid": uid,
                "status": "needs_review",
                "review_stage": None,
                "name": "TEST Workflow60 User",
                "email": email,
                "customer_id": customer_id,
                "company_name": "TEST Workflow60",
                "company_email": email,
                "company_phone": "+919876543210",
                "country": "India",
                "city": "Pune",
                "role": "importer",
                "entity_type": "member_company",
                "consent": True,
                "selfie_file_id": selfie_file_id,
                "document_file_id": document_file_id,
                "checks": {
                    "selfie": {"is_human_face": True, "quality_score": 0.93, "ai_generated_likelihood": 0.02, "confidence_real_person": 0.96},
                    "document": {"available": True, "is_business_document": True, "confidence": 0.91},
                },
                "reasons": ["SEEDED fixture for iter60 verification workflow"],
                "updated_at": _now(),
                "created_at": _now(),
            }
        },
        upsert=True,
    )

    flag = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/test-flag",
        headers=main_headers,
        json={"is_test": True, "reason": "Iter60 FINAL workflow fixture"},
        timeout=45,
    )
    assert flag.status_code == 200, flag.text

    subs = session.get(f"{BASE_URL}/api/admin/subadmins", headers=main_headers, timeout=45)
    assert subs.status_code == 200, subs.text
    sakshi = next((x for x in (subs.json().get("subadmins") or []) if x.get("email") == SUBADMIN_EMAIL), None)
    assert sakshi, "Sakshi sub-admin not found"

    alloc = session.post(
        f"{BASE_URL}/api/admin/allocate",
        headers=main_headers,
        json={"subadmin_ids": [sakshi["id"]], "submission_ids": [submission_id]},
        timeout=60,
    )
    assert alloc.status_code in (200, 409), alloc.text

    fixture_ctx.update({
        "email": email,
        "password": password,
        "uid": uid,
        "customer_id": customer_id,
        "id_token": id_token,
        "submission_id": submission_id,
        "selfie_file_id": selfie_file_id,
        "document_file_id": document_file_id,
    })
    _save_state(fixture_ctx)


# step-1: subadmin free-month request -> main approve -> fixture user unlocks buyer contact
def test_02_subscription_grant_then_contact_unlock(session, main_headers, sub_headers, fixture_ctx):
    uid = fixture_ctx["uid"]

    pay_before = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=45)
    assert pay_before.status_code == 200, pay_before.text
    before_sub = (pay_before.json().get("subscription") or {})
    assert before_sub.get("status") != "active"

    req = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "Iter60 free-month request for final verification path."},
        timeout=60,
    )
    assert req.status_code == 200, req.text
    rid = req.json().get("request_id")
    assert rid

    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    res = dec.json()["results"][0]
    assert res["status"] == "approved", f"strict expected APPROVED, got {res}"

    fresh = _fb_signin(fixture_ctx["email"], fixture_ctx["password"])
    assert fresh.status_code == 200, fresh.text
    new_token = fresh.json()["idToken"]
    fixture_ctx["id_token"] = new_token
    _save_state(fixture_ctx)

    # Use an actually available public buyer GEID for contact unlock assertion.
    search = session.get(f"{BASE_URL}/api/buyers/search", params={"q": "", "limit": 5}, timeout=60)
    assert search.status_code == 200, search.text
    buyers = search.json().get("buyers") or []
    assert buyers, "No public buyers available for contact unlock test"
    available_geids = [b.get("geid") for b in buyers if b.get("geid")]
    geid_to_reveal = REAL_BUYER_GEID if REAL_BUYER_GEID in available_geids else available_geids[0]

    reveal = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/buyers/{geid_to_reveal}/contact",
        headers={"Authorization": f"Bearer {new_token}"},
        timeout=60,
    )
    assert reveal.status_code == 200, reveal.text
    contact = reveal.json().get("contact") or {}
    assert any(contact.get(k) for k in ("email", "phone", "website", "address"))


# step-2: review approve path -> strict approved + DO verified + shared GEID consistency
def test_03_review_approve_and_shared_identity_consistency(session, main_headers, sub_headers, mongo_db, fixture_ctx):
    uid = fixture_ctx["uid"]
    cid = fixture_ctx["customer_id"]

    rec = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "approve", "note": "Iter60 final recommendation approve for main sign-off verification."},
        timeout=60,
    )
    assert rec.status_code == 200, rec.text

    inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
    assert inbox.status_code == 200, inbox.text
    req = next((x for x in inbox.json().get("requests", [])
                if x.get("uid") == uid and x.get("kind") == "review" and x.get("status") in ("pending", "failed")), None)
    assert req, "Pending review request not found for new fixture"

    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    out = dec.json()["results"][0]
    assert out["status"] == "approved", f"strict expected APPROVED, got {out}"

    sub = mongo_db.verification_submissions.find_one({"_id": fixture_ctx["submission_id"]}, {"_id": 0})
    assert sub and sub.get("status") == "verified"
    geid = sub.get("geid")
    assert geid
    fixture_ctx["approved_geid"] = geid
    _save_state(fixture_ctx)

    do_get = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=90)
    assert do_get.status_code == 200, do_get.text
    user = do_get.json().get("user") or do_get.json().get("data") or do_get.json()
    assert str(user.get("customer_id")) == str(cid)
    assert user.get("verification_status") == "verified"

    bridge = mongo_db.members_bridge.find_one({"uid": uid, "customer_id": str(cid), "geid": geid}, {"_id": 0})
    assert bridge is not None

    main_after = sorted(list(mongo_db.members_bridge.find(
        {"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1}
    )))
    assert main_after == fixture_ctx["before_main_bridge"]
    assert any(x.get("geid") == MAIN_ADMIN_BASELINE_GEID for x in main_after)

    pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=60)
    assert pub.status_code == 200, pub.text

    by_name = session.get(f"{BASE_URL}/api/buyers/search", params={"q": "TEST Workflow60", "limit": 25}, timeout=60)
    assert by_name.status_code == 200, by_name.text
    assert any((b or {}).get("geid") == geid for b in (by_name.json().get("buyers") or []))

    cms = _request_with_retry(
        "GET",
        f"{BASE_URL}/api/buyers/admin/list",
        headers=main_headers,
        params={"q": geid, "limit": 25},
        timeout=90,
    )
    assert cms.status_code == 200, cms.text
    assert any((b or {}).get("geid") == geid for b in (cms.json().get("buyers") or []))


# step-3: bulk approval (profile+subscription+document) + deferred apply and no double grant
def test_04_bulk_requests_apply_only_after_signoff_and_no_double_grant(session, main_headers, sub_headers, mongo_db, fixture_ctx):
    uid = fixture_ctx["uid"]

    prof_before = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=60)
    assert prof_before.status_code == 200, prof_before.text
    city_before = (prof_before.json().get("profile") or {}).get("city")

    pay_before = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=60)
    assert pay_before.status_code == 200, pay_before.text
    until_before = (pay_before.json().get("subscription") or {}).get("until")
    assert until_before

    sub_before = mongo_db.verification_submissions.find_one({"_id": fixture_ctx["submission_id"]}, {"_id": 0}) or {}
    doc_before = sub_before.get("document_file_id")
    assert doc_before

    new_city = f"Workflow60City{int(time.time()) % 100000}"
    rq_profile = session.patch(
        f"{BASE_URL}/api/admin/users/{uid}/profile",
        headers=sub_headers,
        json={"patch": {"city": new_city}, "note": "Iter60 city update pending approval."},
        timeout=60,
    )
    assert rq_profile.status_code == 200, rq_profile.text
    profile_rid = rq_profile.json().get("request_id")
    assert profile_rid

    rq_sub = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "Iter60 extension request for bulk signoff."},
        timeout=60,
    )
    assert rq_sub.status_code == 200, rq_sub.text
    sub_rid = rq_sub.json().get("request_id")
    assert sub_rid

    rq_doc = requests.post(
        f"{BASE_URL}/api/admin/users/{uid}/documents",
        headers=sub_headers,
        data={"kind": "document", "label": "ITER60 replacement", "note": "Iter60 doc replacement pending approval."},
        files={"file": ("iter60_replacement.pdf", b"iter60-replacement-doc", "application/pdf")},
        timeout=120,
    )
    assert rq_doc.status_code == 200, rq_doc.text
    doc_rid = rq_doc.json().get("request_id")
    assert doc_rid

    mid_prof = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=60)
    assert mid_prof.status_code == 200, mid_prof.text
    assert (mid_prof.json().get("profile") or {}).get("city") == city_before

    mid_sub = mongo_db.verification_submissions.find_one({"_id": fixture_ctx["submission_id"]}, {"_id": 0}) or {}
    assert mid_sub.get("document_file_id") == doc_before

    inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
    assert inbox.status_code == 200, inbox.text
    rows = inbox.json().get("requests") or []
    doc_req = next((r for r in rows if r.get("id") == doc_rid), None)
    assert doc_req is not None
    uploaded_file_id = (doc_req.get("payload") or {}).get("file_id")
    assert uploaded_file_id

    bulk_ids = [profile_rid, sub_rid, doc_rid]
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": bulk_ids, "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    statuses = {r["id"]: r["status"] for r in dec.json().get("results", [])}
    assert statuses.get(profile_rid) == "approved"
    assert statuses.get(sub_rid) == "approved"
    assert statuses.get(doc_rid) == "approved"

    prof_after = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=60)
    assert prof_after.status_code == 200, prof_after.text
    assert (prof_after.json().get("profile") or {}).get("city") == new_city

    sub_after = mongo_db.verification_submissions.find_one({"_id": fixture_ctx["submission_id"]}, {"_id": 0}) or {}
    assert sub_after.get("document_file_id") == uploaded_file_id

    pay_after = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=60)
    assert pay_after.status_code == 200, pay_after.text
    until_after = (pay_after.json().get("subscription") or {}).get("until")
    assert until_after and until_after > until_before

    dup = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": bulk_ids, "action": "approve"},
        timeout=180,
    )
    assert dup.status_code == 200, dup.text
    pay_dup = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=60)
    assert pay_dup.status_code == 200, pay_dup.text
    until_dup = (pay_dup.json().get("subscription") or {}).get("until")
    assert until_dup == until_after


# step-4: reject recommendation approved by main => verification rejected + listing removed
def test_05_reject_recommendation_then_main_approve_marks_rejected(session, main_headers, sub_headers, mongo_db, fixture_ctx):
    uid = fixture_ctx["uid"]
    cid = fixture_ctx["customer_id"]
    geid = fixture_ctx["approved_geid"]

    rec = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "reject", "note": "Iter60 rejection recommendation for final strict path."},
        timeout=60,
    )
    assert rec.status_code == 200, rec.text

    inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
    assert inbox.status_code == 200, inbox.text
    req = next((x for x in inbox.json().get("requests", [])
                if x.get("uid") == uid and x.get("kind") == "review" and x.get("status") in ("pending", "failed")), None)
    assert req is not None

    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["results"][0]["status"] == "approved"

    sub = mongo_db.verification_submissions.find_one({"_id": fixture_ctx["submission_id"]}, {"_id": 0})
    assert sub and sub.get("status") == "rejected"

    do_get = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=90)
    assert do_get.status_code == 200, do_get.text
    user = do_get.json().get("user") or do_get.json().get("data") or do_get.json()
    assert user.get("verification_status") == "rejected"

    pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=60)
    assert pub.status_code in (200, 404), pub.text
    if pub.status_code == 200:
        e = mongo_db.entities.find_one({"geid": geid}, {"_id": 0, "verified_member_uids": 1}) or {}
        assert uid not in (e.get("verified_member_uids") or [])
