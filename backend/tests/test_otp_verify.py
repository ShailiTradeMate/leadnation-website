"""Backend tests for OTP email verification flow (iteration 17).

Creates a throwaway Firebase user, registers it, exercises:
  - POST /api/auth/request-otp (test_mode true, mentions 123456)
  - POST /api/auth/verify-otp with wrong code → 400
  - POST /api/auth/verify-otp with 123456 → ok/verified
  - GET /api/auth/me → user.is_email_verified == True
Hard-deletes the throwaway at the end. Reports customer_id for cleanup.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@leadnation.app"
ADMIN_PASSWORD = "Shiv@12345"


def fb_signup(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    assert r.status_code == 200, f"Firebase signUp failed: {r.status_code} {r.text}"
    return r.json()


def fb_signin(email, password):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    assert r.status_code == 200, f"Firebase signIn failed: {r.status_code} {r.text}"
    return r.json()


def fb_lookup(id_token):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_KEY}",
        json={"idToken": id_token},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def throwaway_user():
    ts = int(time.time())
    email = f"otpqa_{ts}@leadnation.test"
    password = "Test@12345"
    signup = fb_signup(email, password)
    token = signup["idToken"]
    uid = signup["localId"]

    # Register with backend to allocate customer_id
    r = requests.post(
        f"{BASE_URL}/api/onboarding/register",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"role": "exporter", "provider": "password", "full_name": "OTP QA"},
        timeout=20,
    )
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    reg = r.json()
    customer_id = reg.get("customer_id") or reg.get("user", {}).get("customer_id")
    print(f"\n[seed] Created throwaway: email={email} uid={uid} customer_id={customer_id}")

    yield {"email": email, "password": password, "token": token, "uid": uid, "customer_id": customer_id}

    # Teardown: hard delete via admin
    try:
        admin = fb_signin(ADMIN_EMAIL, ADMIN_PASSWORD)
        atoken = admin["idToken"]
        d = requests.delete(
            f"{BASE_URL}/api/admin_v2/users/{customer_id}/hard-delete",
            headers={"Authorization": f"Bearer {atoken}"},
            timeout=30,
        )
        print(f"[teardown] hard-delete {customer_id} → {d.status_code} {d.text[:200]}")
    except Exception as e:
        print(f"[teardown] FAILED to delete {customer_id}: {e}")


# -------- request-otp --------
def test_request_otp_returns_test_mode(throwaway_user):
    r = requests.post(
        f"{BASE_URL}/api/auth/request-otp",
        headers={"Authorization": f"Bearer {throwaway_user['token']}"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert data.get("test_mode") is True
    assert "123456" in (data.get("message") or "")


# -------- verify-otp wrong code --------
def test_verify_otp_wrong_code_returns_400(throwaway_user):
    r = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        headers={"Authorization": f"Bearer {throwaway_user['token']}", "Content-Type": "application/json"},
        json={"otp": "000000"},
        timeout=15,
    )
    assert r.status_code == 400, f"expected 400 got {r.status_code} {r.text}"
    data = r.json()
    assert "detail" in data or "message" in data


# -------- verify-otp correct code --------
def test_verify_otp_correct_code_marks_verified(throwaway_user):
    r = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        headers={"Authorization": f"Bearer {throwaway_user['token']}", "Content-Type": "application/json"},
        json={"otp": "123456"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert data.get("verified") is True

    # Backend Mongo flag check via /auth/me
    me = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {throwaway_user['token']}"},
        timeout=15,
    )
    assert me.status_code == 200, me.text
    user = me.json().get("user", {})
    assert user.get("is_email_verified") is True, f"is_email_verified not true: {user}"

    # Firebase should also reflect email_verified=true
    fresh = fb_signin(throwaway_user["email"], throwaway_user["password"])
    lk = fb_lookup(fresh["idToken"])
    users = lk.get("users", [])
    assert users and users[0].get("emailVerified") is True, f"Firebase emailVerified not true: {users}"
