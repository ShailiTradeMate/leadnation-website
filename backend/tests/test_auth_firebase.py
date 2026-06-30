"""Iteration 16 — Shared Firebase login phase tests against shared Atlas DB + Firebase.

Covers:
 * /api/auth/resolve-customer-id (public)
 * /api/auth/me (Bearer Firebase token)
 * /api/admin_v2/users (admin gate)
 * onboarding/register idempotency + lifecycle
 * /api/admin_v2/users/{cid}/hard-delete (super-admin protected, purges Mongo/FB)
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
FB_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@leadnation.app"
ADMIN_PASSWORD = "Shiv@12345"


def fb_signin(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    return r


def fb_signup(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FB_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    return r


@pytest.fixture(scope="module")
def admin_token():
    r = fb_signin(ADMIN_EMAIL, ADMIN_PASSWORD)
    assert r.status_code == 200, f"Admin signin failed: {r.text}"
    return r.json()["idToken"]


@pytest.fixture(scope="module")
def throwaway():
    ts = int(time.time())
    email = f"webqa_{ts}@leadnation.test"
    password = "Test@12345"
    r = fb_signup(email, password)
    assert r.status_code == 200, f"Signup failed: {r.text}"
    j = r.json()
    return {"email": email, "password": password, "idToken": j["idToken"], "localId": j["localId"], "customer_id": None}


# ---------- 1) resolve-customer-id ----------
def test_resolve_admin_returns_email():
    r = requests.post(f"{BASE_URL}/api/auth/resolve-customer-id", json={"customer_id": "00001"}, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == ADMIN_EMAIL
    assert data["customer_id"] == "00001"


def test_resolve_bogus_returns_404():
    r = requests.post(f"{BASE_URL}/api/auth/resolve-customer-id", json={"customer_id": "99999"}, timeout=15)
    assert r.status_code == 404


# ---------- 2) /auth/me ----------
def test_me_requires_token():
    r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 401


def test_me_admin(admin_token):
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["onboarded"] is True
    assert data["user"]["customer_id"] == "00001"
    assert data["user"]["role"] == "admin"
    assert "_id" not in data["user"]


# ---------- 3) admin gate ----------
def test_admin_users_list(admin_token):
    r = requests.get(f"{BASE_URL}/api/admin_v2/users",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "users" in data and "total" in data
    assert data["total"] >= 1
    assert any(u.get("customer_id") == "00001" for u in data["users"])


def test_admin_users_requires_admin():
    r = requests.get(f"{BASE_URL}/api/admin_v2/users", timeout=15)
    assert r.status_code in (401, 403)


# ---------- 4) lifecycle: register idempotency ----------
def test_register_allocates_and_is_idempotent(throwaway):
    headers = {"Authorization": f"Bearer {throwaway['idToken']}"}
    r1 = requests.post(f"{BASE_URL}/api/onboarding/register",
                       json={"full_name": "WebQA Throwaway", "role": "exporter", "provider": "password"},
                       headers=headers, timeout=20)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["ok"] is True
    assert d1["new"] is True
    assert d1["customer_id"]
    throwaway["customer_id"] = d1["customer_id"]
    print(f"\nALLOCATED throwaway customer_id={d1['customer_id']} email={throwaway['email']}")

    r2 = requests.post(f"{BASE_URL}/api/onboarding/register",
                       json={"full_name": "WebQA Throwaway", "role": "exporter", "provider": "password"},
                       headers=headers, timeout=20)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["new"] is False
    assert d2["customer_id"] == d1["customer_id"]

    me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15)
    assert me.status_code == 200
    j = me.json()
    assert j["onboarded"] is True
    assert j["user"]["customer_id"] == d1["customer_id"]
    assert j["profile"] is not None


# ---------- 5) hard-delete: protection + purge ----------
def test_hard_delete_protects_00001(admin_token):
    r = requests.delete(f"{BASE_URL}/api/admin_v2/users/00001/hard-delete",
                        headers={"Authorization": f"Bearer {admin_token}"}, timeout=20)
    assert r.status_code == 403, r.text


def test_hard_delete_throwaway_and_verify_purge(admin_token, throwaway):
    cid = throwaway["customer_id"]
    assert cid, "throwaway customer_id missing — register test must run first"
    r = requests.delete(f"{BASE_URL}/api/admin_v2/users/{cid}/hard-delete",
                        headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["customer_id"] == cid
    print(f"\nPURGED throwaway customer_id={cid} firebase_deleted={j.get('firebase_deleted')} mongo={j.get('mongo_purged')}")

    # After delete, the original idToken is still valid until expiry, but the DB row is gone
    me = requests.get(f"{BASE_URL}/api/auth/me",
                      headers={"Authorization": f"Bearer {throwaway['idToken']}"}, timeout=15)
    # token may or may not be revoked; if accepted, must show onboarded:false
    if me.status_code == 200:
        assert me.json().get("onboarded") is False
    else:
        assert me.status_code == 401
