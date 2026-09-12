"""Iter 58 — live mutation workflow tests for identity-bound approvals and hard delete.

Covers REAL workflow mutations (no mocks):
- Disposable Firebase signup + onboarding register
- Main-admin allocation + test-account flagging
- Sub-admin request -> main-admin approval for subscription/profile mutations
- Duplicate decision/idempotency checks for grants
- Review recommendation approve/decline cycle
- Hard-delete request flow with Firebase login removal verification
"""

from __future__ import annotations

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
FIREBASE_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY") or _read_env("/app/frontend/.env", "REACT_APP_FIREBASE_API_KEY")
AUTH_API_BASE = (os.environ.get("REACT_APP_AUTH_API_BASE") or _read_env("/app/frontend/.env", "REACT_APP_AUTH_API_BASE")).rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL") or _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or _read_env("/app/backend/.env", "DB_NAME")

MAIN_ADMIN_EMAIL = "admin@vametra.com"
MAIN_ADMIN_PW = "Shiv@12345"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PW = "Shiv@12345"
MAIN_ADMIN_UID = "gq5pHUPD3LPXNhycRHSdhmkhPiS2"


def _fb_signup(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=30,
    )


def _fb_signin(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=30,
    )


@pytest.fixture(scope="module")
def session() -> requests.Session:
    if not BASE_URL or not FIREBASE_KEY:
        pytest.skip("Missing REACT_APP_BACKEND_URL or REACT_APP_FIREBASE_API_KEY")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def mongo_db():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Missing MONGO_URL/DB_NAME for workflow fixture checks")
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


@pytest.fixture(scope="module")
def main_headers(session):
    r = _fb_signin(MAIN_ADMIN_EMAIL, MAIN_ADMIN_PW)
    if r.status_code != 200:
        pytest.skip(f"Main-admin Firebase login failed: {r.status_code} {r.text[:200]}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


@pytest.fixture(scope="module")
def sub_headers(session):
    r = session.post(
        f"{BASE_URL}/api/admin-auth/login",
        json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PW},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Sub-admin login failed: {r.status_code} {r.text[:200]}")
    return {"X-Staff-Token": r.json()["token"]}


@pytest.fixture(scope="module")
def disposable_user(session, main_headers):
    email = f"iter58_{int(time.time())}_{uuid.uuid4().hex[:6]}@leadnation.test"
    password = "Iter58@Test123"

    su = _fb_signup(email, password)
    assert su.status_code == 200, su.text
    signup = su.json()
    id_token = signup["idToken"]
    uid = signup["localId"]

    reg = session.post(
        f"{AUTH_API_BASE}/onboarding/register",
        headers={"Authorization": f"Bearer {id_token}"},
        json={"full_name": "TEST Iter58 User", "role": "importer", "provider": "password"},
        timeout=30,
    )
    assert reg.status_code == 200, reg.text
    regd = reg.json()
    assert regd.get("customer_id")

    # Persist credentials context for test continuity (explicitly flagged TEST account).
    with open("/app/memory/test_credentials.md", "a", encoding="utf-8") as f:
        f.write(
            f"\n- Iter58 disposable (DELETED at end): {email} / {password} / uid {uid} / customer_id {regd.get('customer_id')}\n"
        )

    return {
        "email": email,
        "password": password,
        "uid": uid,
        "id_token": id_token,
        "customer_id": regd["customer_id"],
    }


@pytest.fixture(scope="module")
def prepared_submission(session, disposable_user, main_headers, mongo_db):
    uid = disposable_user["uid"]

    # Upload real test bytes via verify upload API for THIS disposable account only.
    s1 = requests.post(
        f"{BASE_URL}/api/verify/upload",
        headers={"Authorization": f"Bearer {disposable_user['id_token']}"},
        data={"kind": "selfie"},
        files={"file": ("iter58_selfie.jpg", b"iter58-selfie-bytes", "image/jpeg")},
        timeout=60,
    )
    assert s1.status_code == 200, s1.text
    selfie_id = s1.json()["id"]

    d1 = requests.post(
        f"{BASE_URL}/api/verify/upload",
        headers={"Authorization": f"Bearer {disposable_user['id_token']}"},
        data={"kind": "document"},
        files={"file": ("iter58_doc.pdf", b"iter58-doc-bytes", "application/pdf")},
        timeout=60,
    )
    assert d1.status_code == 200, d1.text
    document_id = d1.json()["id"]

    sid = f"ITER58_SUB_{uid}"
    now = datetime.utcnow().isoformat() + "Z"
    mongo_db.verification_submissions.update_one(
        {"_id": sid},
        {
            "$set": {
                "id": sid,
                "uid": uid,
                "status": "needs_review",
                "review_stage": None,
                "name": "TEST Iter58 User",
                "email": disposable_user["email"],
                "customer_id": disposable_user["customer_id"],
                "company_name": "TEST Iter58 Company",
                "company_email": disposable_user["email"],
                "company_phone": "+919876543210",
                "country": "India",
                "city": "Pune",
                "role": "importer",
                "entity_type": "member_company",
                "consent": True,
                "selfie_file_id": selfie_id,
                "document_file_id": document_id,
                "updated_at": now,
                "created_at": now,
            }
        },
        upsert=True,
    )

    # Flag as TEST and allocate only this submission to Sakshi.
    fr = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/test-flag",
        headers=main_headers,
        json={"is_test": True, "reason": "Iter58 workflow mutation testing"},
        timeout=30,
    )
    assert fr.status_code == 200, fr.text

    subs = session.get(f"{BASE_URL}/api/admin/subadmins", headers=main_headers, timeout=30)
    assert subs.status_code == 200, subs.text
    sakshi = next((x for x in (subs.json().get("subadmins") or []) if x.get("email") == SUBADMIN_EMAIL), None)
    assert sakshi, "Sakshi sub-admin not found"

    alloc = session.post(
        f"{BASE_URL}/api/admin/allocate",
        headers=main_headers,
        json={"subadmin_ids": [sakshi["id"]], "submission_ids": [sid]},
        timeout=30,
    )
    assert alloc.status_code == 200, alloc.text

    return {
        "uid": uid,
        "submission_id": sid,
        "selfie": selfie_id,
        "document": document_id,
        "customer_id": disposable_user["customer_id"],
    }


def _main_get_payments(session, headers, uid: str) -> dict:
    r = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _find_pending_request(session, headers, request_id: str) -> dict | None:
    ib = session.get(f"{BASE_URL}/api/admin/approvals", headers=headers, timeout=45)
    assert ib.status_code == 200, ib.text
    for row in ib.json().get("requests", []):
        if row.get("id") == request_id:
            return row
    return None


# Admin approvals + subscription grant mutation and idempotency
def test_subscription_request_main_approval_idempotent(session, sub_headers, main_headers, prepared_submission):
    uid = prepared_submission["uid"]
    before = _main_get_payments(session, main_headers, uid)
    assert before.get("subscription", {}).get("status") != "active"

    req = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "TEST iter58 free-month request business case"},
        timeout=30,
    )
    assert req.status_code == 200, req.text
    rid = req.json().get("request_id")
    assert rid
    assert _find_pending_request(session, main_headers, rid)

    dec = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=60,
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["results"][0]["status"] == "approved"

    after = _main_get_payments(session, main_headers, uid)
    assert after.get("subscription", {}).get("status") == "active"
    until_1 = after.get("subscription", {}).get("until")
    assert until_1

    dup = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=60,
    )
    assert dup.status_code == 200, dup.text
    assert dup.json()["results"][0]["status"] in ("skipped", "approved")

    after_dup = _main_get_payments(session, main_headers, uid)
    assert after_dup.get("subscription", {}).get("until") == until_1


# Existing expiry extends on a new approved request
def test_second_subscription_request_extends_expiry(session, sub_headers, main_headers, prepared_submission):
    uid = prepared_submission["uid"]
    before = _main_get_payments(session, main_headers, uid)
    old_until = before.get("subscription", {}).get("until")
    assert old_until

    req = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "TEST iter58 extension request business case"},
        timeout=30,
    )
    assert req.status_code == 200, req.text
    rid = req.json().get("request_id")

    dec = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=60,
    )
    assert dec.status_code == 200, dec.text

    after = _main_get_payments(session, main_headers, uid)
    new_until = after.get("subscription", {}).get("until")
    assert new_until and new_until > old_until


# Profile change request should apply only after main approval
def test_profile_change_deferred_until_approval(session, sub_headers, main_headers, prepared_submission):
    uid = prepared_submission["uid"]
    city = f"Iter58City{int(time.time()) % 10000}"

    before = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=30)
    assert before.status_code == 200, before.text

    req = session.patch(
        f"{BASE_URL}/api/admin/users/{uid}/profile",
        headers=sub_headers,
        json={"patch": {"city": city}, "note": "TEST iter58 demographic update request"},
        timeout=30,
    )
    assert req.status_code == 200, req.text
    rid = req.json().get("request_id")
    assert rid

    mid = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=30)
    assert mid.status_code == 200, mid.text
    assert (mid.json().get("profile") or {}).get("city") != city

    dec = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=60,
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["results"][0]["status"] == "approved"

    after = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=30)
    assert after.status_code == 200, after.text
    assert (after.json().get("profile") or {}).get("city") == city


# Role escalation guard (sub-admin cannot set invalid role)
def test_role_escalation_rejected(session, sub_headers, prepared_submission):
    uid = prepared_submission["uid"]
    r = session.patch(
        f"{BASE_URL}/api/admin/users/{uid}/profile",
        headers=sub_headers,
        json={"patch": {"role": "admin"}, "note": "TEST iter58 escalation attempt"},
        timeout=30,
    )
    assert r.status_code == 400, r.text


# Recommendation approve + decline path and identity-bridge invariant check
def test_review_recommendation_paths_and_bridge_guard(session, sub_headers, main_headers, prepared_submission, mongo_db):
    uid = prepared_submission["uid"]
    main_baseline = sorted(
        list(mongo_db.members_bridge.find({"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "geid": 1, "customer_id": 1}))
    )

    rec1 = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "reject", "note": "TEST iter58 reject recommendation reason"},
        timeout=30,
    )
    assert rec1.status_code == 200, rec1.text

    inbox = session.get(f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=45)
    assert inbox.status_code == 200, inbox.text
    req = next((r for r in inbox.json().get("requests", []) if r.get("uid") == uid and r.get("kind") == "review" and r.get("status") in ("pending", "failed")), None)
    assert req, "Pending review approval request not found"

    dec1 = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "decline"},
        timeout=60,
    )
    assert dec1.status_code == 200, dec1.text
    assert dec1.json()["results"][0]["status"] == "declined"

    rec2 = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "approve", "note": "TEST iter58 approve recommendation reason"},
        timeout=30,
    )
    assert rec2.status_code == 200, rec2.text
    inbox2 = session.get(f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=45)
    assert inbox2.status_code == 200, inbox2.text
    req2 = next((r for r in inbox2.json().get("requests", []) if r.get("uid") == uid and r.get("kind") == "review" and r.get("status") in ("pending", "failed")), None)
    assert req2

    dec2 = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req2["id"]], "action": "approve"},
        timeout=90,
    )
    assert dec2.status_code == 200, dec2.text
    assert dec2.json()["results"][0]["status"] in ("approved", "failed")

    main_after = sorted(
        list(mongo_db.members_bridge.find({"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "geid": 1, "customer_id": 1}))
    )
    assert main_after == main_baseline

    user_bridge = list(mongo_db.members_bridge.find({"uid": uid}, {"_id": 0, "uid": 1, "geid": 1, "customer_id": 1}))
    if dec2.json()["results"][0]["status"] == "approved":
        assert user_bridge, "Approved review did not create/confirm target bridge"
        assert any(b.get("customer_id") == prepared_submission.get("customer_id") for b in user_bridge)


# Hard-delete request path + delete confirmation + Firebase login removal verification
def test_hard_delete_full_request_cycle(session, sub_headers, main_headers, prepared_submission, disposable_user, mongo_db):
    uid = prepared_submission["uid"]

    dr = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/delete-request",
        headers=sub_headers,
        json={"business_case": "TEST iter58 account cleanup after full mutation cycle"},
        timeout=30,
    )
    assert dr.status_code == 200, dr.text

    pending = session.get(f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=45)
    assert pending.status_code == 200, pending.text
    dreq = next((r for r in pending.json().get("requests", []) if r.get("uid") == uid and r.get("kind") == "hard_delete" and r.get("status") in ("pending", "failed")), None)
    assert dreq

    bad = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [dreq["id"]], "action": "approve", "confirm_delete": "NOPE"},
        timeout=60,
    )
    assert bad.status_code == 400, bad.text

    ok = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [dreq["id"]], "action": "approve", "confirm_delete": "DELETE"},
        timeout=120,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["results"][0]["status"] in ("approved", "failed")

    # Verify Firebase account removal by login failure.
    fb = _fb_signin(disposable_user["email"], disposable_user["password"])
    assert fb.status_code != 200, "Disposable user can still log in after hard-delete"

    # Verify user no longer listed by admin users search and core records cleaned.
    users = session.get(f"{BASE_URL}/api/admin/users?q={disposable_user['email']}", headers=main_headers, timeout=45)
    assert users.status_code == 200, users.text
    assert not any((u.get("uid") == uid) for u in (users.json().get("users") or []))

    assert mongo_db.users.count_documents({"uid": uid}) == 0
    assert mongo_db.verification_submissions.count_documents({"uid": uid}) == 0
    assert mongo_db.members_bridge.count_documents({"uid": uid}) == 0
