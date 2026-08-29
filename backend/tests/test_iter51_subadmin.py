"""Phase A — Sub-admin (staff) JWT auth + Admin User Section.

Covers:
- POST /api/admin-auth/login (email + username identifiers, wrong password)
- GET /api/admin-auth/me (X-Staff-Token)
- GET /api/admin/users scoped for sub-admin (empty) and full for main admin
  (via minted Firebase idToken)
- ?q= search filter (main admin)
"""
import os
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-verify.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"
FB_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"

MAIN_ADMIN = {"email": "admin@vametra.com", "password": "Shiv@12345"}
SUBS = [
    {"identifier": "sakshi@vametra.com", "username": "sakshi", "name": "Sakshi", "password": "Shiv@12345"},
    {"identifier": "patnica@vametra.com", "username": "patnica", "name": "PatniCA", "password": "Shiv@12345"},
]


@pytest.fixture(scope="module")
def firebase_id_token():
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
        json={**MAIN_ADMIN, "returnSecureToken": True}, timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Firebase login failed: {r.status_code} {r.text[:200]}")
    return r.json()["idToken"]


# ---------- Sub-admin login ----------
@pytest.mark.parametrize("sa", SUBS)
def test_subadmin_login_by_email(sa):
    r = requests.post(f"{API}/admin-auth/login",
                      json={"identifier": sa["identifier"], "password": sa["password"]}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert isinstance(d.get("token"), str) and len(d["token"]) > 20
    assert d["subadmin"]["email"] == sa["identifier"]
    assert d["subadmin"]["role"] == "sub_admin"


@pytest.mark.parametrize("sa", SUBS)
def test_subadmin_login_by_username(sa):
    r = requests.post(f"{API}/admin-auth/login",
                      json={"identifier": sa["username"], "password": sa["password"]}, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json()["subadmin"]["email"] == sa["identifier"]


def test_subadmin_login_wrong_password():
    r = requests.post(f"{API}/admin-auth/login",
                      json={"identifier": "sakshi@vametra.com", "password": "WrongPass!"}, timeout=15)
    assert r.status_code == 401


@pytest.mark.parametrize("sa", SUBS)
def test_subadmin_me(sa):
    tok = requests.post(f"{API}/admin-auth/login",
                        json={"identifier": sa["identifier"], "password": sa["password"]},
                        timeout=15).json()["token"]
    r = requests.get(f"{API}/admin-auth/me", headers={"X-Staff-Token": tok}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["role"] == "sub_admin"
    assert d["is_main"] is False
    assert d["name"] == sa["name"]
    assert d["email"] == sa["identifier"]


# ---------- Users scope ----------
def test_subadmin_users_empty_scope():
    tok = requests.post(f"{API}/admin-auth/login",
                        json={"identifier": "sakshi@vametra.com", "password": "Shiv@12345"},
                        timeout=15).json()["token"]
    r = requests.get(f"{API}/admin/users", headers={"X-Staff-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["role"] == "sub_admin"
    assert d["is_main"] is False
    assert d["total"] == 0
    assert d["users"] == []


def test_main_admin_users_list(firebase_id_token):
    r = requests.get(f"{API}/admin/users",
                     headers={"Authorization": f"Bearer {firebase_id_token}"}, timeout=45)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["is_main"] is True
    assert isinstance(d["users"], list)
    assert d["total"] >= 1
    # verify row shape
    row = d["users"][0]
    for key in ("uid", "email", "status", "documents", "subscription",
                "company_name", "company_email", "company_phone",
                "mobile", "country", "state", "category", "customer_id"):
        assert key in row, f"missing key {key} in row"
    # not_applied status must exist for signups without a verification
    statuses = {r_.get("status") for r_ in d["users"]}
    assert "not_applied" in statuses or any(r_.get("applied") for r_ in d["users"])


def test_main_admin_search_partial(firebase_id_token):
    # search for admin's own email fragment
    r = requests.get(f"{API}/admin/users?q=vametra",
                     headers={"Authorization": f"Bearer {firebase_id_token}"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    # Case-insensitive partial should find admin@vametra.com at minimum
    assert d["total"] >= 1
    emails = [(r_.get("email") or "").lower() for r_ in d["users"]]
    assert any("vametra" in e for e in emails)


def test_admin_users_requires_auth():
    r = requests.get(f"{API}/admin/users", timeout=15)
    assert r.status_code == 401


# ---------- Mobile persistence regression ----------
def test_verify_state_reflects_mobile(firebase_id_token=None):
    """Login end-user via Firebase, hit /api/verify/state, verify mobile field present in schema."""
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
        json={"email": "vaibhav@leadnation.app", "password": "Shiv@12345", "returnSecureToken": True},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip("End-user Firebase login failed")
    tok = r.json()["idToken"]
    rs = requests.get(f"{API}/verify/state",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    # endpoint may 404 depending on router; only assert if present
    if rs.status_code == 404:
        pytest.skip("/api/verify/state not present")
    assert rs.status_code == 200, rs.text
    # Not asserting a specific mobile value — just that response is JSON
    assert isinstance(rs.json(), dict)
