"""Backend tests for Vametra AI Verify admin endpoints + admin login prerequisites."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-verify.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = "leadnation-admin-2026"

HEADERS = {"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"}


def test_admin_queue_needs_review():
    r = requests.get(f"{BASE_URL}/api/verify/admin/queue", params={"status": "needs_review"}, headers=HEADERS, timeout=30)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert "items" in data and isinstance(data["items"], list)
    assert "counts" in data and isinstance(data["counts"], dict)
    for k in ("needs_review", "verified", "rejected"):
        assert k in data["counts"], f"Missing count key {k}"


def test_admin_queue_verified():
    r = requests.get(f"{BASE_URL}/api/verify/admin/queue", params={"status": "verified"}, headers=HEADERS, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "counts" in data


def test_admin_queue_rejected():
    r = requests.get(f"{BASE_URL}/api/verify/admin/queue", params={"status": "rejected"}, headers=HEADERS, timeout=30)
    assert r.status_code == 200


def test_admin_queue_requires_admin_token():
    r = requests.get(f"{BASE_URL}/api/verify/admin/queue", timeout=30)
    assert r.status_code in (401, 403), f"Expected auth error, got {r.status_code}"


def test_admin_decide_missing_submission():
    """Only test decide with a fake sid to verify 404 handling (avoid mutating real data)."""
    r = requests.post(
        f"{BASE_URL}/api/verify/admin/does-not-exist/decide",
        json={"decision": "approve", "note": "test"},
        headers=HEADERS, timeout=30,
    )
    assert r.status_code == 404


def test_resolve_admin_customer_id():
    """Confirm admin ID 00001 resolves to the vametra admin email (login-by-ID path)."""
    r = requests.post(f"{BASE_URL}/api/auth/resolve-customer-id", json={"customer_id": "00001"}, timeout=30)
    # Route may live on DO backend or local backend; if 404 skip.
    if r.status_code == 404:
        pytest.skip("resolve-customer-id not exposed by this backend")
    assert r.status_code == 200
    data = r.json()
    email = (data.get("email") or "").lower()
    assert "admin" in email, f"unexpected admin email: {email}"


def test_verify_documents_public_or_authed():
    """Documents route requires auth; expect 401/403 without a token."""
    r = requests.get(f"{BASE_URL}/api/verify/documents", timeout=30)
    assert r.status_code in (401, 403), f"Unexpected: {r.status_code}"
