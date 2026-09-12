"""Iter 62 — resume fixture 00018 with canonical approval semantics.

# Module: state assertions, bulk approval workflow, rejection workflow, and conditional cleanup.
"""

from __future__ import annotations

import json
import os
import time

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
AUTH_API_BASE = (os.environ.get("REACT_APP_AUTH_API_BASE") or _read_env("/app/frontend/.env", "REACT_APP_AUTH_API_BASE")).rstrip("/")
FIREBASE_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY") or _read_env("/app/frontend/.env", "REACT_APP_FIREBASE_API_KEY")
MONGO_URL = os.environ.get("MONGO_URL") or _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or _read_env("/app/backend/.env", "DB_NAME")

STATE_PATH = "/app/test_reports/iter60_fixture_state.json"
MAIN_EMAIL = "admin@vametra.com"
MAIN_PASSWORD = "Shiv@12345"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PASSWORD = "Shiv@12345"
EXPECTED_MAIN_UID = "gq5pHUPD3LPXNhycRHSdhmkhPiS2"
EXPECTED_GEID = "LN-member_company-01M2BPJ0N1WMK3CK61C3WSBERF"


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    last = None
    for i in range(3):
        last = requests.request(method, url, **kwargs)
        if last.status_code not in (502, 503, 504):
            return last
        time.sleep(0.8 * (i + 1))
    return last


def _fb_signin(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=45,
    )


def _save_state(data: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@pytest.fixture(scope="module")
def session() -> requests.Session:
    if not BASE_URL or not AUTH_API_BASE or not FIREBASE_KEY:
        pytest.skip("Missing required env values")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def state() -> dict:
    if not os.path.exists(STATE_PATH):
        pytest.skip("iter60 fixture state missing")
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if str(data.get("customer_id")) != "00018":
        pytest.skip(f"Unexpected fixture customer_id: {data.get('customer_id')}")
    return data


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
    r = _fb_signin(MAIN_EMAIL, MAIN_PASSWORD)
    if r.status_code != 200:
        pytest.skip(f"Main login failed: {r.status_code} {r.text[:180]}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


@pytest.fixture(scope="module")
def sub_headers(session) -> dict:
    r = session.post(
        f"{BASE_URL}/api/admin-auth/login",
        json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PASSWORD},
        timeout=45,
    )
    if r.status_code != 200:
        pytest.skip(f"Sub-admin login failed: {r.status_code} {r.text[:180]}")
    return {"X-Staff-Token": r.json()["token"]}


@pytest.fixture(scope="module")
def progress() -> dict:
    return {"a_passed": False, "b_passed": False, "c_passed": False}


def _wait_request_by_id(session, main_headers: dict, rid: str, timeout_s: int = 40) -> dict:
    end = time.time() + timeout_s
    while time.time() < end:
        inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
        assert inbox.status_code == 200, inbox.text
        row = next((x for x in (inbox.json().get("requests") or []) if x.get("id") == rid), None)
        if row:
            return row
        time.sleep(2)
    raise AssertionError(f"Request {rid} not present in admin approvals inbox")


def _wait_review_pending_or_failed(session, main_headers: dict, uid: str, timeout_s: int = 60) -> dict:
    end = time.time() + timeout_s
    while time.time() < end:
        inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
        assert inbox.status_code == 200, inbox.text
        row = next(
            (
                x
                for x in (inbox.json().get("requests") or [])
                if x.get("uid") == uid and x.get("kind") == "review" and x.get("status") in ("pending", "failed")
            ),
            None,
        )
        if row:
            return row
        time.sleep(2)
    raise AssertionError(f"No pending/failed review request found for uid={uid}")


def test_01_state_assertions_after_canonical_fix(session, state, main_headers, mongo_db, progress):
    uid = state["uid"]
    cid = str(state["customer_id"])

    if not state.get("approved_geid"):
        state["approved_geid"] = EXPECTED_GEID
        _save_state(state)

    # A) DO canonical approval readback: must be approved or verified
    do_user = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=120)
    assert do_user.status_code == 200, do_user.text
    user = do_user.json().get("user") or do_user.json().get("data") or do_user.json()
    status = (user.get("verification_status") or "").strip().lower()
    assert status in ("approved", "verified"), f"Unexpected DO verification_status={status}"

    # Local submission should be verified after approval path.
    sub = mongo_db.verification_submissions.find_one({"_id": state["submission_id"]}, {"_id": 0}) or {}
    assert sub.get("status") == "verified"
    geid = sub.get("geid")
    assert geid == EXPECTED_GEID

    # members_bridge must map target uid/cid/geid; main baseline unchanged.
    bridge = mongo_db.members_bridge.find_one({"uid": uid, "customer_id": cid, "geid": geid}, {"_id": 0})
    assert bridge is not None
    before_main = state.get("before_main_bridge") or []
    main_after = sorted(list(mongo_db.members_bridge.find({"uid": EXPECTED_MAIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1})))
    assert main_after == before_main

    # Search and CMS should both include same geid
    search = session.get(f"{BASE_URL}/api/buyers/search", params={"q": "TEST Workflow60", "limit": 25}, timeout=90)
    assert search.status_code == 200, search.text
    assert any((b or {}).get("geid") == geid for b in (search.json().get("buyers") or []))

    cms = _request_with_retry(
        "GET",
        f"{BASE_URL}/api/buyers/admin/list",
        headers=main_headers,
        params={"q": geid, "limit": 25},
        timeout=90,
    )
    assert cms.status_code == 200, cms.text
    assert any((b or {}).get("geid") == geid for b in (cms.json().get("buyers") or []))

    progress["a_passed"] = True


def test_02_bulk_approve_profile_subscription_document(session, state, main_headers, sub_headers, mongo_db, progress):
    assert progress["a_passed"], "Step A must pass before Step B"
    uid = state["uid"]
    sid = state["submission_id"]
    geid = state.get("approved_geid") or EXPECTED_GEID

    prof_before = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=90)
    assert prof_before.status_code == 200, prof_before.text
    city_before = (prof_before.json().get("profile") or {}).get("city")

    pay_before = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=90)
    assert pay_before.status_code == 200, pay_before.text
    until_before = (pay_before.json().get("subscription") or {}).get("until")
    assert until_before

    sub_before = mongo_db.verification_submissions.find_one({"_id": sid}, {"_id": 0}) or {}
    doc_before = sub_before.get("document_file_id")
    assert doc_before

    new_city = f"Iter62City{int(time.time()) % 100000}"
    rp = session.patch(
        f"{BASE_URL}/api/admin/users/{uid}/profile",
        headers=sub_headers,
        json={"patch": {"city": new_city}, "note": "Iter62 staged profile city update."},
        timeout=90,
    )
    assert rp.status_code == 200, rp.text
    profile_rid = rp.json().get("request_id")
    assert profile_rid

    rs = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "Iter62 staged free-month extension."},
        timeout=90,
    )
    assert rs.status_code == 200, rs.text
    sub_rid = rs.json().get("request_id")
    assert sub_rid

    rd = requests.post(
        f"{BASE_URL}/api/admin/users/{uid}/documents",
        headers=sub_headers,
        data={"kind": "document", "label": "ITER62 replacement", "note": "Iter62 staged doc update."},
        files={"file": ("iter62_replacement.pdf", b"iter62-replacement-doc", "application/pdf")},
        timeout=120,
    )
    assert rd.status_code == 200, rd.text
    doc_rid = rd.json().get("request_id")
    assert doc_rid

    # Verify staged changes are not applied before main decision.
    prof_mid = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=90)
    assert prof_mid.status_code == 200, prof_mid.text
    assert (prof_mid.json().get("profile") or {}).get("city") == city_before

    sub_mid = mongo_db.verification_submissions.find_one({"_id": sid}, {"_id": 0}) or {}
    assert sub_mid.get("document_file_id") == doc_before

    doc_row = _wait_request_by_id(session, main_headers, doc_rid)
    uploaded_file_id = (doc_row.get("payload") or {}).get("file_id")
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
    statuses = {r.get("id"): r.get("status") for r in (dec.json().get("results") or [])}
    assert statuses.get(profile_rid) == "approved"
    assert statuses.get(sub_rid) == "approved"
    assert statuses.get(doc_rid) == "approved"

    prof_after = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=90)
    assert prof_after.status_code == 200, prof_after.text
    assert (prof_after.json().get("profile") or {}).get("city") == new_city

    sub_after = mongo_db.verification_submissions.find_one({"_id": sid}, {"_id": 0}) or {}
    assert sub_after.get("document_file_id") == uploaded_file_id

    pay_after = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=90)
    assert pay_after.status_code == 200, pay_after.text
    until_after = (pay_after.json().get("subscription") or {}).get("until")
    assert until_after and until_after > until_before

    # Re-decide should not double-grant subscription extension.
    dup = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": bulk_ids, "action": "approve"},
        timeout=180,
    )
    assert dup.status_code == 200, dup.text
    pay_dup = session.get(f"{BASE_URL}/api/admin/users/{uid}/payments", headers=main_headers, timeout=90)
    assert pay_dup.status_code == 200, pay_dup.text
    assert (pay_dup.json().get("subscription") or {}).get("until") == until_after

    # Newly granted user must reveal contact.
    fixture_login = _fb_signin(state["email"], state["password"])
    assert fixture_login.status_code == 200, fixture_login.text
    target_headers = {"Authorization": f"Bearer {fixture_login.json()['idToken']}"}
    reveal = _request_with_retry("POST", f"{BASE_URL}/api/buyers/{geid}/contact", headers=target_headers, timeout=90)
    assert reveal.status_code == 200, reveal.text

    progress["b_passed"] = True


def test_03_reject_recommendation_and_verify_removal(session, state, main_headers, sub_headers, mongo_db, progress):
    assert progress["b_passed"], "Step B must pass before Step C"
    uid = state["uid"]
    cid = str(state["customer_id"])
    geid = state.get("approved_geid") or EXPECTED_GEID

    rec = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "reject", "note": "Iter62 reject recommendation strict main approval."},
        timeout=90,
    )
    assert rec.status_code == 200, rec.text

    req = _wait_review_pending_or_failed(session, main_headers, uid)
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    out = dec.json().get("results", [{}])[0]
    assert out.get("status") == "approved", out

    sub = mongo_db.verification_submissions.find_one({"_id": state["submission_id"]}, {"_id": 0}) or {}
    assert sub.get("status") == "rejected"

    do_user = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=120)
    assert do_user.status_code == 200, do_user.text
    user = do_user.json().get("user") or do_user.json().get("data") or do_user.json()
    assert (user.get("verification_status") or "").strip().lower() == "rejected"

    # Member should become unavailable publicly and in search.
    end = time.time() + 45
    pub_code = None
    while time.time() < end:
        pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=90)
        pub_code = pub.status_code
        if pub_code == 404:
            break
        time.sleep(2)
    assert pub_code == 404

    sr = session.get(f"{BASE_URL}/api/buyers/search", params={"q": geid, "limit": 25}, timeout=90)
    assert sr.status_code == 200, sr.text
    assert not any((b or {}).get("geid") == geid for b in (sr.json().get("buyers") or []))

    progress["c_passed"] = True


def test_04_hard_delete_only_after_a_b_c_pass(session, state, main_headers, mongo_db, progress):
    if not (progress["a_passed"] and progress["b_passed"] and progress["c_passed"]):
        pytest.skip("Skipping hard-delete because A/B/C did not all pass")

    uid = state["uid"]
    cid = str(state["customer_id"])
    geid = state.get("approved_geid") or EXPECTED_GEID

    d = _request_with_retry("DELETE", f"{AUTH_API_BASE}/admin_v2/users/{cid}/hard-delete", headers=main_headers, timeout=180)
    assert d.status_code in (200, 404), d.text

    do_after = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=90)
    assert do_after.status_code == 404, do_after.text

    fb = _fb_signin(state["email"], state["password"])
    assert fb.status_code != 200

    assert mongo_db.users.count_documents({"uid": uid}) == 0
    assert mongo_db.profiles.count_documents({"uid": uid}) == 0
    assert mongo_db.verification_submissions.count_documents({"uid": uid}) == 0
    assert mongo_db.members_bridge.count_documents({"uid": uid}) == 0

    if geid:
        pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=90)
        assert pub.status_code == 404, pub.text
