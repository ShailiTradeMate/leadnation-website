"""Iter 59 — focused live verification + disposable-account cleanup.

Scope only (no broad repeat):
- Main inbox review approve MUST return approved (not failed) with canonical readback checks
- Shared identity bridge + DO verification_status + public/CMS visibility checks
- Main approving a reject recommendation must produce rejected outcome
- Document request must apply only after main approval
- Subscriber contact reveal entitlement
- Hard-delete disposable test accounts via /admin_v2/users/{cid}/hard-delete + cleanup verification
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

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

MAIN_ADMIN_EMAIL = "admin@vametra.com"
MAIN_ADMIN_PW = "Shiv@12345"
MAIN_ADMIN_UID = "gq5pHUPD3LPXNhycRHSdhmkhPiS2"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PW = "Shiv@12345"
SUBSCRIBER_EMAIL = "vaibhav@leadnation.app"
SUBSCRIBER_PW = "Shiv@12345"

DISPOSABLE = [
    {"uid": "ehBZU1XTBhVUIdHICQdcnEWKJqC3", "cid": "00014", "email": "iter58_1789244554_bfe0b1@leadnation.test", "pw": "Iter58@Test123"},
    {"uid": "197GxUSrFZUAGm8pYG0zVnREW2j1", "cid": "00015", "email": "iter58_1789244609_78e821@leadnation.test", "pw": "Iter58@Test123"},
    {"uid": "fGALnKTwZoPEwnHsYlSu9zreRKB3", "cid": "00016", "email": "iter58_1789244734_f7dc40@leadnation.test", "pw": "Iter58@Test123"},
    {"uid": "VEYOrZmCJme5rQetUOChlGuGkMm1", "cid": "00017", "email": "iter58_1789245208_ef9245@leadnation.test", "pw": "Iter58@Test123"},
]


@dataclass
class Context:
    review_uid: str
    review_cid: str
    review_geid_after_approve: str | None
    main_bridge_baseline: list[dict]
    pre_doc_file_id: str | None
    doc_request_id: str | None
    uploaded_doc_file_id: str | None


def _fb_signin(email: str, password: str) -> requests.Response:
    return requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=30,
    )


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    last = None
    for i in range(3):
        last = requests.request(method, url, **kwargs)
        if last.status_code not in (502, 503, 504):
            return last
        time.sleep(0.8 * (i + 1))
    return last


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def session() -> requests.Session:
    if not BASE_URL or not AUTH_API_BASE or not FIREBASE_KEY:
        pytest.skip("Missing REACT_APP_BACKEND_URL / REACT_APP_AUTH_API_BASE / REACT_APP_FIREBASE_API_KEY")
    return _session()


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
def main_authz() -> str:
    r = _fb_signin(MAIN_ADMIN_EMAIL, MAIN_ADMIN_PW)
    if r.status_code != 200:
        pytest.skip(f"Main admin Firebase login failed: {r.status_code} {r.text[:180]}")
    return f"Bearer {r.json()['idToken']}"


@pytest.fixture(scope="module")
def main_headers(main_authz) -> dict:
    return {"Authorization": main_authz}


@pytest.fixture(scope="module")
def sub_headers(session) -> dict:
    r = session.post(
        f"{BASE_URL}/api/admin-auth/login",
        json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PW},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Sub-admin login failed: {r.status_code} {r.text[:180]}")
    return {"X-Staff-Token": r.json()["token"]}


def _latest_submission(db, uid: str) -> dict | None:
    return db.verification_submissions.find_one(
        {"uid": uid},
        {"_id": 0},
        sort=[("updated_at", -1), ("created_at", -1)],
    )


def _ensure_allocated_to_sakshi(session, main_headers, submission_id: str):
    subs = session.get(f"{BASE_URL}/api/admin/subadmins", headers=main_headers, timeout=30)
    assert subs.status_code == 200, subs.text
    sakshi = next((x for x in (subs.json().get("subadmins") or []) if x.get("email") == SUBADMIN_EMAIL), None)
    assert sakshi, "Sakshi sub-admin not found"
    alloc = session.post(
        f"{BASE_URL}/api/admin/allocate",
        headers=main_headers,
        json={"subadmin_ids": [sakshi["id"]], "submission_ids": [submission_id]},
        timeout=45,
    )
    assert alloc.status_code in (200, 409), alloc.text


def _fetch_inbox(session, headers: dict) -> list[dict]:
    r = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=headers, timeout=60)
    assert r.status_code == 200, r.text
    return r.json().get("requests", [])


def _wait_for_request(session, headers, uid: str, kind: str, timeout_s: int = 40) -> dict:
    end = time.time() + timeout_s
    latest = None
    while time.time() < end:
        rows = _fetch_inbox(session, headers)
        latest = next((x for x in rows if x.get("uid") == uid and x.get("kind") == kind and x.get("status") in ("pending", "failed")), None)
        if latest:
            return latest
        time.sleep(2)
    raise AssertionError(f"No pending {kind} request found for uid={uid}. latest={latest}")


@pytest.fixture(scope="module")
def review_context(session, main_headers, sub_headers, mongo_db) -> Context:
    # preserve main admin bridge invariant baseline
    baseline = sorted(list(mongo_db.members_bridge.find({"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1})))

    candidate = None
    for row in DISPOSABLE:
        sub = _latest_submission(mongo_db, row["uid"])
        if not sub:
            continue
        if sub.get("selfie_file_id") and sub.get("document_file_id"):
            candidate = (row, sub)
            break
    if not candidate:
        pytest.skip("No disposable account with selfie+document submission available")

    row, sub = candidate
    sid = sub.get("id") or sub.get("_id")
    assert sid, "Disposable submission id missing"
    _ensure_allocated_to_sakshi(session, main_headers, sid)

    return Context(
        review_uid=row["uid"],
        review_cid=row["cid"],
        review_geid_after_approve=None,
        main_bridge_baseline=baseline,
        pre_doc_file_id=sub.get("document_file_id"),
        doc_request_id=None,
        uploaded_doc_file_id=None,
    )


# Review approve path: status MUST be approved, then canonical readback checks.
def test_review_approve_strict_and_canonical_readback(session, main_headers, sub_headers, mongo_db, review_context):
    uid = review_context.review_uid
    cid = review_context.review_cid

    req = None
    existing = _fetch_inbox(session, main_headers)
    req = next((x for x in existing if x.get("uid") == uid and x.get("kind") == "review" and x.get("status") in ("pending", "failed")), None)
    if not req:
        rec = session.post(
            f"{BASE_URL}/api/admin/users/{uid}/review",
            headers=sub_headers,
            json={"decision": "approve", "note": "ITER59 strict approve verification through main inbox sign-off."},
            timeout=45,
        )
        assert rec.status_code == 200, rec.text
        req = _wait_for_request(session, main_headers, uid, "review")
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=120,
    )
    assert dec.status_code == 200, dec.text
    result = dec.json()["results"][0]
    assert result["status"] == "approved", f"Expected APPROVED only, got: {result}"

    sub = _latest_submission(mongo_db, uid)
    assert sub and sub.get("status") == "verified"
    assert sub.get("geid")
    review_context.review_geid_after_approve = sub.get("geid")

    # DO canonical readback (verification_status must be verified)
    do_get = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=45)
    assert do_get.status_code == 200, do_get.text
    payload = do_get.json()
    user = payload.get("user") or payload.get("data") or payload
    assert str(user.get("customer_id")) == cid
    assert user.get("verification_status") == "verified"

    bridge = mongo_db.members_bridge.find_one({"uid": uid, "customer_id": cid, "geid": review_context.review_geid_after_approve}, {"_id": 0})
    assert bridge is not None

    # same GEID visible in public + CMS list
    pub = session.get(f"{BASE_URL}/api/buyers/{review_context.review_geid_after_approve}", timeout=45)
    assert pub.status_code == 200, pub.text
    cms = _request_with_retry("GET", f"{BASE_URL}/api/buyers/admin/list", headers=main_headers,
                              params={"q": review_context.review_geid_after_approve, "limit": 25}, timeout=60)
    assert cms.status_code == 200, cms.text
    assert any(b.get("geid") == review_context.review_geid_after_approve for b in (cms.json().get("buyers") or []))

    # main admin bridge must remain unchanged
    after = sorted(list(mongo_db.members_bridge.find({"uid": MAIN_ADMIN_UID}, {"_id": 0, "uid": 1, "customer_id": 1, "geid": 1})))
    assert after == review_context.main_bridge_baseline


# Document request: should apply only after main approval.
def test_document_request_deferred_until_main_approval(session, main_headers, sub_headers, mongo_db, review_context):
    uid = review_context.review_uid
    before = _latest_submission(mongo_db, uid) or {}
    before_doc = before.get("document_file_id")

    files = {"file": ("iter59_admin_doc.pdf", b"iter59-doc-change", "application/pdf")}
    form = {"kind": "document", "label": "ITER59 document", "note": "ITER59 document request for staged approval"}
    r = requests.post(f"{BASE_URL}/api/admin/users/{uid}/documents", headers=sub_headers, data=form, files=files, timeout=90)
    assert r.status_code == 200, r.text
    rid = r.json().get("request_id")
    assert rid
    review_context.doc_request_id = rid

    # Not applied before sign-off
    mid = _latest_submission(mongo_db, uid) or {}
    assert mid.get("document_file_id") == before_doc

    req = _wait_for_request(session, main_headers, uid, "document")
    assert req.get("id") == rid
    review_context.uploaded_doc_file_id = (req.get("payload") or {}).get("file_id")
    assert review_context.uploaded_doc_file_id

    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [rid], "action": "approve"},
        timeout=120,
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["results"][0]["status"] == "approved"

    after = _latest_submission(mongo_db, uid) or {}
    assert after.get("document_file_id") == review_context.uploaded_doc_file_id


# Main approving REJECT recommendation should produce rejected outcome (not declined).
def test_main_approve_reject_recommendation(session, main_headers, sub_headers, mongo_db, review_context):
    uid = review_context.review_uid
    geid = review_context.review_geid_after_approve
    if not geid:
        pytest.skip("approve path failed earlier; reject-recommendation verification blocked")

    rec = session.post(
        f"{BASE_URL}/api/admin/users/{uid}/review",
        headers=sub_headers,
        json={"decision": "reject", "note": "ITER59 reject recommendation should be main-approved as rejected."},
        timeout=45,
    )
    assert rec.status_code == 200, rec.text

    req = _wait_for_request(session, main_headers, uid, "review")
    dec = _request_with_retry(
        "POST",
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=main_headers,
        json={"request_ids": [req["id"]], "action": "approve"},
        timeout=120,
    )
    assert dec.status_code == 200, dec.text
    assert dec.json()["results"][0]["status"] == "approved"

    sub = _latest_submission(mongo_db, uid)
    assert sub and sub.get("status") == "rejected"

    do_get = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{review_context.review_cid}", headers=main_headers, timeout=45)
    assert do_get.status_code == 200, do_get.text
    u = (do_get.json().get("user") or do_get.json().get("data") or do_get.json())
    assert u.get("verification_status") == "rejected"

    # member listing removal check
    public_after = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=45)
    assert public_after.status_code in (404, 200), public_after.text
    if public_after.status_code == 200:
        body = public_after.json()
        # if still present, it should no longer carry this member uid
        e = mongo_db.entities.find_one({"geid": geid}, {"_id": 0, "verified_member_uids": 1}) or {}
        assert uid not in (e.get("verified_member_uids") or [])


# Subscriber entitlement: /buyers/{geid}/contact should unlock without checkout for active subscriber.
def test_subscriber_contact_reveal_unlocked(session):
    s = _fb_signin(SUBSCRIBER_EMAIL, SUBSCRIBER_PW)
    if s.status_code != 200:
        pytest.skip(f"Subscriber login failed: {s.status_code}")
    token = s.json()["idToken"]

    search = session.get(f"{BASE_URL}/api/buyers/search", params={"limit": 1}, timeout=30)
    assert search.status_code == 200, search.text
    buyers = search.json().get("buyers") or []
    if not buyers:
        pytest.skip("No public buyers available")
    geid = buyers[0]["geid"]

    reveal = _request_with_retry("POST", f"{BASE_URL}/api/buyers/{geid}/contact",
                                 headers={"Authorization": f"Bearer {token}"}, timeout=45)
    assert reveal.status_code == 200, reveal.text
    contact = (reveal.json().get("contact") or {})
    assert isinstance(contact, dict)
    assert any(contact.get(k) for k in ("email", "phone", "website", "address"))


# Disposable hard-delete cleanup through shared identity hard-delete contract.
def test_hard_delete_disposable_accounts_and_verify_cleanup(session, main_headers, mongo_db):
    # remove old artifact requested by owner (safe TEST artifact only)
    mongo_db.trade_projects.delete_many({"name": "TEST Iter57 Project"})

    for row in DISPOSABLE:
        cid, uid = row["cid"], row["uid"]
        # Preferred cleanup path: local hard-delete (purges local + calls upstream /hard-delete).
        local = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/admin/users/{uid}/hard-delete",
            headers=main_headers,
            json={"confirm": "DELETE", "note": "ITER59 disposable cleanup"},
            timeout=180,
        )
        assert local.status_code in (200, 404, 409), local.text

        get_before = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=45)
        if get_before.status_code == 404:
            # already gone in shared identity; verify local cleanup state anyway
            pass
        else:
            assert get_before.status_code == 200, get_before.text
            u = (get_before.json().get("user") or get_before.json().get("data") or get_before.json())
            # safety guard: never delete non-disposable users
            assert str(u.get("customer_id")) == cid
            assert u.get("uid") == uid
            if row.get("email"):
                assert str(u.get("email", "")).lower() == row["email"].lower()

            d = _request_with_retry("DELETE", f"{AUTH_API_BASE}/admin_v2/users/{cid}/hard-delete", headers=main_headers, timeout=120)
            assert d.status_code in (200, 404), d.text

        get_after = _request_with_retry("GET", f"{AUTH_API_BASE}/admin_v2/users/{cid}", headers=main_headers, timeout=45)
        assert get_after.status_code == 404, get_after.text

        fb = _fb_signin(row["email"], row["pw"])
        assert fb.status_code != 200

        assert mongo_db.users.count_documents({"uid": uid}) == 0
        assert mongo_db.profiles.count_documents({"uid": uid}) == 0
        assert mongo_db.verification_submissions.count_documents({"uid": uid}) == 0
        assert mongo_db.members_bridge.count_documents({"uid": uid}) == 0
        assert mongo_db.registry_matches.count_documents({"uid": uid}) == 0


# Post-cleanup regression guard.
def test_inbox_and_users_load_after_cleanup(session, main_headers):
    inbox = _request_with_retry("GET", f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=60)
    assert inbox.status_code == 200, inbox.text
    users = _request_with_retry("GET", f"{BASE_URL}/api/admin/users", headers=main_headers, timeout=60)
    assert users.status_code == 200, users.text


def test_no_leftover_disposable_requests_or_artifacts(mongo_db):
    uids = [x["uid"] for x in DISPOSABLE]
    assert mongo_db.trade_projects.count_documents({"name": "TEST Iter57 Project"}) == 0
    assert mongo_db.admin_approval_requests.count_documents({"uid": {"$in": uids}, "status": {"$in": ["pending", "failed", "processing"]}}) == 0
    assert mongo_db.delete_requests.count_documents({"uid": {"$in": uids}, "status": "pending"}) == 0
    assert mongo_db.test_accounts.count_documents({"uid": {"$in": uids}}) == 0
