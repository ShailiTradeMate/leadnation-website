"""Iter 56 — GEID hard-delete & test-flag workflow tests.

Covers Owner directive:
- Sub-admin delete-request flow (business_case validation + RBAC lockout)
- Main-admin delete-request queue + decline
- Test-account flagging (POST /test-flag) + auto-flag for automation emails
- One-click export endpoint schema
- Regression: 7 real users present in main-admin Users list; vaibhav 00002 has full data
- Hard-delete endpoint DELETE-confirm gate (no destructive call against real users)
"""
import os
import time
import pytest
import requests

def _read_env(path, key):
    try:
        for ln in open(path):
            if ln.startswith(key + "="):
                return ln.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
FIREBASE_KEY = (os.environ.get("REACT_APP_FIREBASE_API_KEY")
                or _read_env("/app/frontend/.env", "REACT_APP_FIREBASE_API_KEY")
                or "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

MAIN_ADMIN_EMAIL = "admin@vametra.com"
MAIN_ADMIN_PW = "Shiv@12345"
SUB_ADMIN_EMAIL = "sakshi@vametra.com"
SUB_ADMIN_PW = "Shiv@12345"

REAL_CUSTOMER_IDS = {"00001", "00002", "00003", "00004", "00009", "00010", "00011"}
VAIBHAV_CID = "00002"


@pytest.fixture(scope="module")
def s():
    ses = requests.Session()
    ses.headers.update({"Content-Type": "application/json"})
    return ses


@pytest.fixture(scope="module")
def main_token(s):
    r = s.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": MAIN_ADMIN_EMAIL, "password": MAIN_ADMIN_PW, "returnSecureToken": True},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Firebase main-admin sign-in failed: {r.status_code} {r.text[:200]}")
    return r.json()["idToken"]


@pytest.fixture(scope="module")
def sub_token(s):
    r = s.post(f"{BASE_URL}/api/admin-auth/login",
               json={"identifier": SUB_ADMIN_EMAIL, "password": SUB_ADMIN_PW}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _main_h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _sub_h(tok):
    return {"X-Staff-Token": tok}


# ---------------------------------------------------------------- Users list regression
def test_main_admin_users_list_has_7_real_users(s, main_token):
    last = None
    for _ in range(3):
        r = s.get(f"{BASE_URL}/api/admin/users", headers=_main_h(main_token), timeout=60)
        last = r
        if r.status_code == 200:
            break
        time.sleep(2)
    assert last.status_code == 200, last.text[:400]
    data = last.json()
    rows = data.get("users") or []
    cids = {str(r.get("customer_id")) for r in rows if r.get("customer_id")}
    missing = REAL_CUSTOMER_IDS - cids
    assert not missing, f"Missing real users: {missing}. Got cids={sorted(cids)}"


def test_vaibhav_00002_row_complete(s, main_token):
    r = s.get(f"{BASE_URL}/api/admin/users?q=vaibhav.deshmane",
              headers=_main_h(main_token), timeout=30)
    assert r.status_code == 200, r.text
    rows = r.json().get("users") or []
    match = [x for x in rows if str(x.get("customer_id")) == VAIBHAV_CID]
    assert match, f"vaibhav 00002 missing. rows={rows}"
    row = match[0]
    assert row.get("email"), "email missing"
    assert row.get("mobile"), "mobile missing"
    assert row.get("company_name"), "company missing"
    assert row.get("name"), "name missing"


# ---------------------------------------------------------------- Test-flag
def _find_test_target(rows):
    """Prefer an already-test-flagged automation account (never a real customer)."""
    for r in rows:
        cid = str(r.get("customer_id") or "")
        if cid in REAL_CUSTOMER_IDS:
            continue
        if r.get("is_test_account") or (r.get("email") and "@example.com" in r["email"].lower()):
            return r
    # else pick any non-real row
    for r in rows:
        if str(r.get("customer_id") or "") not in REAL_CUSTOMER_IDS and r.get("uid"):
            return r
    return None


def test_test_flag_toggle_and_auto_flag(s, main_token):
    r = s.get(f"{BASE_URL}/api/admin/users", headers=_main_h(main_token), timeout=60)
    rows = r.json().get("users") or []
    # auto-flag check: any @example.com / probe emails MUST be flagged
    auto = [x for x in rows if x.get("email") and any(
        h in x["email"].lower() for h in ("@example.com", "dsa-probe", "dsa-loop", "dsa-login", "dsa-diagnostic"))]
    for a in auto:
        assert a.get("is_test_account") is True, f"auto-flag missing: {a.get('email')}"

    # Toggle endpoint end-to-end against vaibhav 00002 (identity_registry row), with strict cleanup.
    target = next((x for x in rows if str(x.get("customer_id")) == VAIBHAV_CID), None)
    if not target:
        pytest.skip("vaibhav 00002 not present for flag toggle test")
    uid = target["uid"]
    was_flagged = bool(target.get("is_test_account"))
    try:
        r1 = s.post(f"{BASE_URL}/api/admin/users/{uid}/test-flag",
                    headers=_main_h(main_token), json={"is_test": True, "reason": "iter56 toggle probe"}, timeout=30)
        assert r1.status_code == 200, r1.text
        assert r1.json().get("is_test_account") is True

        r2 = s.get(f"{BASE_URL}/api/admin/users?q={uid}", headers=_main_h(main_token), timeout=30)
        assert any(x.get("uid") == uid and x.get("is_test_account") for x in r2.json().get("users") or []), \
            "flag not reflected in list"

        r3 = s.post(f"{BASE_URL}/api/admin/users/{uid}/test-flag",
                    headers=_main_h(main_token), json={"is_test": False}, timeout=30)
        assert r3.status_code == 200, r3.text
    finally:
        # ensure cleanup regardless
        s.post(f"{BASE_URL}/api/admin/users/{uid}/test-flag",
               headers=_main_h(main_token),
               json={"is_test": was_flagged}, timeout=30)


# ---------------------------------------------------------------- Export
def test_export_endpoint_full_record(s, main_token):
    r = s.get(f"{BASE_URL}/api/admin/users", headers=_main_h(main_token), timeout=30)
    rows = r.json().get("users") or []
    target = next((x for x in rows if str(x.get("customer_id")) == VAIBHAV_CID), rows[0])
    uid = target["uid"]
    r2 = s.get(f"{BASE_URL}/api/admin/users/{uid}/export", headers=_main_h(main_token), timeout=30)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    for key in ("identity_registry", "shared_profile", "website_overlay",
                "verification_submissions", "documents", "subscription",
                "payments", "contact_notes", "brain_events", "admin_audit",
                "is_test_account", "uid", "customer_id"):
        assert key in body, f"export missing key {key}"
    # documents entries must expose /api/storage/file URL
    for d in body.get("documents") or []:
        assert (d.get("url") or "").startswith("/api/storage/file/"), d


# ---------------------------------------------------------------- Sub-admin delete-request path
def test_subadmin_delete_request_short_case_400(s, sub_token):
    # find any user allocated to sakshi
    r = s.get(f"{BASE_URL}/api/admin/users", headers=_sub_h(sub_token), timeout=30)
    assert r.status_code == 200, r.text
    rows = r.json().get("users") or []
    if not rows:
        pytest.skip("Sakshi has no allocated user to raise request against")
    uid = rows[0]["uid"]
    r2 = s.post(f"{BASE_URL}/api/admin/users/{uid}/delete-request",
                headers=_sub_h(sub_token), json={"business_case": "short"}, timeout=30)
    assert r2.status_code == 400, r2.text


def test_subadmin_cannot_hit_hard_delete_or_queue(s, sub_token):
    r = s.get(f"{BASE_URL}/api/admin/users", headers=_sub_h(sub_token), timeout=30)
    rows = r.json().get("users") or []
    if not rows:
        pytest.skip("Sakshi has no allocated user")
    uid = rows[0]["uid"]
    r1 = s.post(f"{BASE_URL}/api/admin/users/{uid}/hard-delete",
                headers=_sub_h(sub_token), json={"confirm": "DELETE"}, timeout=30)
    assert r1.status_code == 403, r1.text
    r2 = s.get(f"{BASE_URL}/api/admin/delete-requests", headers=_sub_h(sub_token), timeout=30)
    assert r2.status_code == 403, r2.text


def test_subadmin_delete_request_valid_then_main_admin_decline(s, sub_token, main_token):
    r = s.get(f"{BASE_URL}/api/admin/users", headers=_sub_h(sub_token), timeout=30)
    rows = r.json().get("users") or []
    if not rows:
        pytest.skip("Sakshi has no allocated user")
    uid = rows[0]["uid"]
    biz = "TEST_iter56 — validating end-to-end delete-request queue behaviour."
    r1 = s.post(f"{BASE_URL}/api/admin/users/{uid}/delete-request",
                headers=_sub_h(sub_token), json={"business_case": biz}, timeout=30)
    assert r1.status_code == 200, r1.text
    body = r1.json()
    assert body.get("stage") == "awaiting_admin_approval"
    req_id = body.get("request_id")
    assert req_id

    # main admin lists it
    r2 = s.get(f"{BASE_URL}/api/admin/delete-requests", headers=_main_h(main_token), timeout=30)
    assert r2.status_code == 200, r2.text
    queue = r2.json().get("queue") or []
    match = [q for q in queue if q.get("id") == req_id]
    assert match, f"delete request {req_id} not in queue"
    q = match[0]
    assert q.get("business_case") == biz
    assert q.get("requested_by")
    assert q.get("uid") == uid

    # main admin declines
    r3 = s.post(f"{BASE_URL}/api/admin/delete-requests/{req_id}/decline",
                headers=_main_h(main_token), timeout=30)
    assert r3.status_code == 200, r3.text

    # gone from queue
    r4 = s.get(f"{BASE_URL}/api/admin/delete-requests", headers=_main_h(main_token), timeout=30)
    assert not any(q.get("id") == req_id for q in r4.json().get("queue") or [])


# ---------------------------------------------------------------- Hard-delete gate (non-destructive)
def test_hard_delete_requires_typed_DELETE(s, main_token):
    # use a bogus UID so we never touch a real user; endpoint validates confirm BEFORE lookup.
    r = s.post(f"{BASE_URL}/api/admin/users/nonexistent-uid-iter56/hard-delete",
               headers=_main_h(main_token), json={"confirm": ""}, timeout=30)
    assert r.status_code == 400, r.text
    assert "DELETE" in r.text
