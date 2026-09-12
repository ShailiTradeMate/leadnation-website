"""Iter 61 — resume preserved fixture00018 only (no new user creation).

# Module: approvals + shared identity consistency + buyer visibility + hard-delete cleanup.
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
EXPECTED_MEMBER_GEID = "LN-member_company-01M2BPJ0N1WMK3CK61C3WSBERF"
EXPECTED_MAIN_UID = "gq5pHUPD3LPXNhycRHSdhmkhPiS2"


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


@pytest.fixture(scope="module")
def session() -> requests.Session:
    if not BASE_URL or not AUTH_API_BASE or not FIREBASE_KEY:
        pytest.skip("Missing env required for iter61 resume test")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def state() -> dict:
    if not os.path.exists(STATE_PATH):
        pytest.skip("iter60 fixture state not found")
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


def _save_state(data: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _wait_approval_row(session, main_headers: dict, uid: str, kind: str, timeout_s: int = 50) -> dict:
    end = time.time() + timeout_s
    while time.time() < end:
        inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
        assert inbox.status_code == 200, inbox.text
        row = next((x for x in (inbox.json().get("requests") or [])
                    if x.get("uid") == uid and x.get("kind") == kind and x.get("status") in ("pending", "failed")), None)
        if row:
            return row
        time.sleep(2)
    raise AssertionError(f"No {kind} pending/failed request found for uid={uid}")


def test_01_retry_existing_review_then_verify_canonical_reads(session, main_headers, state, mongo_db):
    uid = state["uid"]
    cid = str(state["customer_id"])

    # retry existing failed/pending review request only; do NOT post new recommendation
    req = _wait_approval_row(session, main_headers, uid, "review")
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    out = dec.json().get("results", [{}])[0]
    assert out.get("status") == "approved", f"Expected APPROVED, got: {out}"

    do_user = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=120)
    assert do_user.status_code == 200, do_user.text
    user = do_user.json().get("user") or do_user.json().get("data") or do_user.json()
    assert str(user.get("customer_id")) == cid
    assert user.get("verification_status") == "verified"

    # target token checks for /members/company readback
    fixture_login = _fb_signin(state["email"], state["password"])
    assert fixture_login.status_code == 200, fixture_login.text
    target_headers = {"Authorization": f"Bearer {fixture_login.json()['idToken']}"}
    company = _request_with_retry("GET", f"{AUTH_API_BASE}/members/company", headers=target_headers, timeout=90)
    assert company.status_code == 200, company.text
    cbody = company.json()
    assert cbody.get("linked") is True
    assert str(cbody.get("customer_id")) == cid
    geid = cbody.get("geid")
    assert geid == EXPECTED_MEMBER_GEID
    ent = cbody.get("entity") or {}
    assert ent.get("geid") == geid

    # local mirror must match same uid/cid/geid
    bridge = mongo_db.members_bridge.find_one({"uid": uid, "customer_id": cid, "geid": geid}, {"_id": 0})
    assert bridge is not None

    # main baseline bridge should remain unchanged
    before = state.get("before_main_bridge") or []
    main_after = sorted(list(mongo_db.members_bridge.find(
        {"uid": EXPECTED_MAIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1}
    )))
    assert main_after == before

    # public + search + CMS visibility
    pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=90)
    assert pub.status_code == 200, pub.text

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

    state["approved_geid"] = geid
    _save_state(state)


def test_02_bulk_decide_three_requests_and_no_double_grant(session, main_headers, state, sub_headers, mongo_db):
    uid = state["uid"]
    sid = state["submission_id"]
    geid = state.get("approved_geid")
    assert geid, "approved_geid missing from step-1"

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

    new_city = f"Iter61City{int(time.time()) % 100000}"
    rp = session.patch(
        f"{BASE_URL}/api/admin/users/{uid}/profile",
        headers=sub_headers,
        json={"patch": {"city": new_city}, "note": "Iter61 staged profile city update."},
        timeout=90,
    )
    assert rp.status_code == 200, rp.text
    profile_rid = rp.json().get("request_id")
    assert profile_rid

    rs = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/subscription",
        headers=sub_headers,
        json={"action": "grant", "plan": "monthly", "note": "Iter61 staged free-month extension."},
        timeout=90,
    )
    assert rs.status_code == 200, rs.text
    sub_rid = rs.json().get("request_id")
    assert sub_rid

    rd = requests.post(
        f"{BASE_URL}/api/admin/users/{uid}/documents",
        headers=sub_headers,
        data={"kind": "document", "label": "ITER61 replacement", "note": "Iter61 staged doc update."},
        files={"file": ("iter61_replacement.pdf", b"iter61-replacement-doc", "application/pdf")},
        timeout=120,
    )
    assert rd.status_code == 200, rd.text
    doc_rid = rd.json().get("request_id")
    assert doc_rid

    # staged means not yet applied
    prof_mid = session.get(f"{BASE_URL}/api/admin/users/{uid}/profile", headers=main_headers, timeout=90)
    assert prof_mid.status_code == 200, prof_mid.text
    assert (prof_mid.json().get("profile") or {}).get("city") == city_before

    sub_mid = mongo_db.verification_submissions.find_one({"_id": sid}, {"_id": 0}) or {}
    assert sub_mid.get("document_file_id") == doc_before

    inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=90)
    assert inbox.status_code == 200, inbox.text
    rows = inbox.json().get("requests") or []
    doc_req = next((x for x in rows if x.get("id") == doc_rid), None)
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

    # idempotency retry should not grant twice
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

    # ensure contact reveal still works for existing approved geid
    fixture_login = _fb_signin(state["email"], state["password"])
    assert fixture_login.status_code == 200, fixture_login.text
    target_headers = {"Authorization": f"Bearer {fixture_login.json()['idToken']}"}
    reveal = _request_with_retry("POST", f"{BASE_URL}/api/buyers/{geid}/contact", headers=target_headers, timeout=90)
    assert reveal.status_code == 200, reveal.text


def test_03_reject_recommendation_main_approve_rejected(session, main_headers, sub_headers, state, mongo_db):
    uid = state["uid"]
    cid = str(state["customer_id"])
    geid = state.get("approved_geid")
    assert geid

    rec = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "reject", "note": "Iter61 reject recommendation strict main approval."},
        timeout=90,
    )
    assert rec.status_code == 200, rec.text

    req = _wait_approval_row(session, main_headers, uid, "review")
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=180,
    )
    assert dec.status_code == 200, dec.text
    out = dec.json().get("results", [{}])[0]
    assert out.get("status") == "approved"

    sub = mongo_db.verification_submissions.find_one({"_id": state["submission_id"]}, {"_id": 0}) or {}
    assert sub.get("status") == "rejected"

    do_user = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=90)
    assert do_user.status_code == 200, do_user.text
    user = do_user.json().get("user") or do_user.json().get("data") or do_user.json()
    assert user.get("verification_status") == "rejected"

    pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=90)
    assert pub.status_code in (200, 404), pub.text
    if pub.status_code == 200:
        entity = mongo_db.entities.find_one({"geid": geid}, {"_id": 0, "verified_member_uids": 1}) or {}
        assert uid not in (entity.get("verified_member_uids") or [])


def test_04_hard_delete_fixture00018_after_all_success(session, main_headers, state, mongo_db):
    uid = state["uid"]
    cid = str(state["customer_id"])

    # execute shared hard-delete contract
    d = _request_with_retry("DELETE", f"{AUTH_API_BASE}/admin_v2/users/{cid}/hard-delete", headers=main_headers, timeout=180)
    assert d.status_code in (200, 404), d.text

    # verify DO removed
    do_after = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=90)
    assert do_after.status_code == 404, do_after.text

    # verify Firebase sign-in blocked
    fb = _fb_signin(state["email"], state["password"])
    assert fb.status_code != 200

    # verify local removal
    assert mongo_db.users.count_documents({"uid": uid}) == 0
    assert mongo_db.profiles.count_documents({"uid": uid}) == 0
    assert mongo_db.verification_submissions.count_documents({"uid": uid}) == 0
    assert mongo_db.members_bridge.count_documents({"uid": uid}) == 0

    geid = state.get("approved_geid")
    if geid:
        pub = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=90)
        assert pub.status_code == 404, pub.text
