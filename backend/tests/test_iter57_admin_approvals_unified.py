"""Iter 57 — approval inbox + RBAC + unified verified-buyer surfaces (non-destructive)."""
import os
import pytest
import requests


def _read_env(path: str, key: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.startswith(f"{key}="):
                    return ln.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
FIREBASE_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY") or _read_env("/app/frontend/.env", "REACT_APP_FIREBASE_API_KEY")

MAIN_ADMIN_EMAIL = "admin@vametra.com"
MAIN_ADMIN_PW = "Shiv@12345"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PW = "Shiv@12345"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def main_headers(session):
    if not BASE_URL or not FIREBASE_KEY:
        pytest.skip("Missing REACT_APP_BACKEND_URL or REACT_APP_FIREBASE_API_KEY")
    r = session.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": MAIN_ADMIN_EMAIL, "password": MAIN_ADMIN_PW, "returnSecureToken": True},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Main admin Firebase sign-in failed: {r.status_code}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


@pytest.fixture(scope="module")
def sub_headers(session):
    if not BASE_URL:
        pytest.skip("Missing REACT_APP_BACKEND_URL")
    r = session.post(
        f"{BASE_URL}/api/admin-auth/login",
        json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PW},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Sub-admin sign-in failed: {r.status_code}")
    return {"X-Staff-Token": r.json()["token"]}


# Approval inbox + decision RBAC
def test_main_admin_can_read_approval_inbox(session, main_headers):
    r = session.get(f"{BASE_URL}/api/admin/approvals", headers=main_headers, timeout=45)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("is_main") is True
    assert isinstance(data.get("requests"), list)
    for row in data.get("requests", [])[:5]:
        assert "id" in row and "uid" in row and "kind" in row and "status" in row


def test_subadmin_can_read_only_scoped_approval_requests(session, sub_headers):
    r = session.get(f"{BASE_URL}/api/admin/approvals", headers=sub_headers, timeout=45)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("is_main") is False
    assert isinstance(data.get("requests"), list)


def test_subadmin_cannot_decide_approvals(session, sub_headers):
    r = session.post(
        f"{BASE_URL}/api/admin/approvals/decide",
        headers=sub_headers,
        json={"request_ids": ["nonexistent-approval-id"], "action": "approve"},
        timeout=30,
    )
    assert r.status_code == 403, r.text


# Input validation guardrails for subscription/free-access requests
def test_negative_subscription_days_rejected_by_validation(session, main_headers):
    r = session.post(
        f"{BASE_URL}/api/admin/users/nonexistent-iter57/subscription",
        headers=main_headers,
        json={"action": "grant", "plan": "monthly", "days": -1, "note": "invalid test"},
        timeout=30,
    )
    assert r.status_code == 422, r.text


def test_invalid_subscription_plan_rejected_by_validation(session, main_headers):
    r = session.post(
        f"{BASE_URL}/api/admin/users/nonexistent-iter57/subscription",
        headers=main_headers,
        json={"action": "grant", "plan": "weekly", "note": "invalid plan"},
        timeout=30,
    )
    assert r.status_code == 422, r.text


# Unified verified-buyer surfaces and privacy checks
def test_buyers_meta_and_search_available(session):
    m = session.get(f"{BASE_URL}/api/buyers/meta", timeout=30)
    assert m.status_code == 200, m.text
    md = m.json()
    assert "total" in md and isinstance(md.get("total"), int)

    s = session.get(f"{BASE_URL}/api/buyers/search", params={"limit": 12}, timeout=30)
    assert s.status_code == 200, s.text
    sd = s.json()
    assert "buyers" in sd and isinstance(sd.get("buyers"), list)


def test_public_buyer_detail_does_not_leak_contact_without_entitlement(session):
    s = session.get(f"{BASE_URL}/api/buyers/search", params={"limit": 1}, timeout=30)
    assert s.status_code == 200, s.text
    buyers = s.json().get("buyers") or []
    if not buyers:
        pytest.skip("No active buyers available in public search")
    geid = buyers[0]["geid"]

    d = session.get(f"{BASE_URL}/api/buyers/{geid}", timeout=30)
    assert d.status_code == 200, d.text
    body = d.json()
    if body.get("locked"):
        assert "contact" not in body
        assert "source_warning" in body


def test_cms_and_public_use_overlapping_geids(session, main_headers):
    pub = session.get(f"{BASE_URL}/api/buyers/search", params={"limit": 30}, timeout=30)
    assert pub.status_code == 200, pub.text
    pub_geids = {b.get("geid") for b in (pub.json().get("buyers") or []) if b.get("geid")}
    if not pub_geids:
        pytest.skip("No public buyers to compare")

    cms = session.get(f"{BASE_URL}/api/buyers/admin/list", headers=main_headers,
                      params={"limit": 50}, timeout=45)
    assert cms.status_code == 200, cms.text
    cms_buyers = cms.json().get("buyers") or []
    cms_geids = {b.get("geid") for b in cms_buyers if b.get("geid")}
    assert len(pub_geids.intersection(cms_geids)) > 0


def test_cms_buyer_directory_has_required_contact_fields(session, main_headers):
    cms = session.get(f"{BASE_URL}/api/buyers/admin/list", headers=main_headers,
                      params={"limit": 25}, timeout=45)
    assert cms.status_code == 200, cms.text
    buyers = cms.json().get("buyers") or []
    if not buyers:
        pytest.skip("No buyers available in CMS list")
    b = buyers[0]
    for key in ("display_name", "geid", "country_name", "contact"):
        assert key in b
    assert isinstance(b.get("contact") or {}, dict)
