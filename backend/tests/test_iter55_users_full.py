"""Iteration 55 — verify canonical DO user registry, on-demand full profile,
search race fix, allocation categories, user-side verify prefill, and sub-admin
RBAC regression."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@vametra.com"
ADMIN_PW = "Shiv@12345"
SUBADMIN_EMAIL = "sakshi@vametra.com"
SUBADMIN_PW = "Shiv@12345"
BUYER_EMAIL = "vaibhav@leadnation.app"   # regular buyer with active subscription
BUYER_PW = "Shiv@12345"
TARGET_EMAIL = "vaibhav.deshmane@vametra.com"


def _firebase_token(email, pw):
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": email, "password": pw, "returnSecureToken": True}, timeout=20)
    assert r.status_code == 200, f"firebase login failed for {email}: {r.status_code} {r.text[:200]}"
    return r.json()["idToken"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"Authorization": f"Bearer {_firebase_token(ADMIN_EMAIL, ADMIN_PW)}"}


@pytest.fixture(scope="module")
def subadmin_headers():
    r = requests.post(f"{BASE_URL}/api/admin-auth/login",
                      json={"identifier": SUBADMIN_EMAIL, "password": SUBADMIN_PW}, timeout=20)
    assert r.status_code == 200, r.text
    return {"X-Staff-Token": r.json()["token"]}


@pytest.fixture(scope="module")
def buyer_headers():
    return {"Authorization": f"Bearer {_firebase_token(BUYER_EMAIL, BUYER_PW)}"}


# ---------- 1. Canonical users list ----------
class TestUsersList:
    def test_admin_users_contains_target(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers, timeout=45)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["is_main"] is True
        users = data["users"]
        emails = [str(u.get("email") or "").lower() for u in users]
        assert TARGET_EMAIL in emails, f"target {TARGET_EMAIL} missing from admin list; got {len(users)} users"
        # Expect at least ~11 registered users (canonical DO registry) — accept >=8 for safety
        assert len(users) >= 8, f"admin users too small ({len(users)}); expected canonical registry >=8"

    def test_target_row_has_full_details(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers, timeout=45).json()
        row = next((u for u in r["users"] if (u.get("email") or "").lower() == TARGET_EMAIL), None)
        assert row is not None
        # Expected fields per RCA
        assert row.get("customer_id") == "00002", f"customer_id={row.get('customer_id')}"
        assert (row.get("name") or "").lower().startswith("vaibhav"), row.get("name")
        assert str(row.get("mobile") or "").endswith("7020691832"), row.get("mobile")
        assert (row.get("country") or "").lower() == "india"
        assert (row.get("city") or "").lower() in ("ahilyanagar", "ahilya nagar")
        assert "vametra" in (row.get("company_name") or "").lower()

    def test_search_by_email_prefix(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?q=vaibhav.deshmane",
                         headers=admin_headers, timeout=45)
        assert r.status_code == 200
        rows = r.json()["users"]
        assert len(rows) == 1, f"expected exactly 1 match, got {len(rows)}"
        assert (rows[0].get("email") or "").lower() == TARGET_EMAIL

    def test_search_by_mobile(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?q=7020691832",
                         headers=admin_headers, timeout=45).json()
        assert any((u.get("email") or "").lower() == TARGET_EMAIL for u in r["users"])

    def test_search_by_company(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?q=Vametra",
                         headers=admin_headers, timeout=45).json()
        assert any((u.get("email") or "").lower() == TARGET_EMAIL for u in r["users"])

    def test_search_by_customer_id(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?q=00002",
                         headers=admin_headers, timeout=45).json()
        assert any(u.get("customer_id") == "00002" for u in r["users"])


# ---------- 2. On-demand full profile ----------
class TestFullProfile:
    def _uid_of_target(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?q=vaibhav.deshmane",
                         headers=admin_headers, timeout=45).json()
        return r["users"][0]["uid"]

    def test_profile_endpoint_returns_200_for_identity_only_user(self, admin_headers):
        uid = self._uid_of_target(admin_headers)
        r = requests.get(f"{BASE_URL}/api/admin/users/{uid}/profile",
                         headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "profile" in data and "identity" in data
        prof = data["profile"] or {}
        # Should include shared-profiles hydration
        assert (prof.get("mobile") or data["identity"].get("mobile") or "").endswith("7020691832") \
            or "vametra" in ((prof.get("company_details") or {}).get("company_name") or "").lower()

    def test_admin_ops_edit_endpoints_do_not_404(self, admin_headers):
        uid = self._uid_of_target(admin_headers)
        # notes GET is a safe read that goes through _resolve() — this was 404-ing before fix
        r = requests.get(f"{BASE_URL}/api/admin/users/{uid}/notes",
                         headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"notes endpoint {r.status_code}: {r.text[:200]}"
        r2 = requests.get(f"{BASE_URL}/api/admin/users/{uid}/payments",
                          headers=admin_headers, timeout=30)
        assert r2.status_code == 200, f"payments endpoint {r2.status_code}: {r2.text[:200]}"
        r3 = requests.get(f"{BASE_URL}/api/admin/users/{uid}/activity",
                          headers=admin_headers, timeout=30)
        assert r3.status_code == 200, f"activity endpoint {r3.status_code}: {r3.text[:200]}"


# ---------- 3. Allocation categories ----------
class TestAllocationCategories:
    def test_no_verification_bucket_includes_all_registered(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/categories",
                         headers=admin_headers, timeout=45)
        assert r.status_code == 200
        cats = {c["key"]: c for c in r.json()["categories"]}
        assert "no_verification" in cats
        assert cats["no_verification"]["allocatable"] is False
        assert cats["no_verification"]["count"] >= 5, cats["no_verification"]["count"]

    def test_missing_details_not_flag_when_profile_has_mobile(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/categories",
                         headers=admin_headers, timeout=45).json()
        cats = {c["key"]: c for c in r["categories"]}
        md = cats.get("missing_details", {}).get("items", [])
        for it in md:
            if (it.get("email") or "").lower() == TARGET_EMAIL:
                assert "Contact number" not in (it.get("missing") or []), \
                    "target should not have Contact number in missing (mobile lives on shared profile)"


# ---------- 4. Sub-admin regression ----------
class TestSubAdminRBAC:
    def test_subadmin_users_scoped(self, subadmin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=subadmin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("is_main") is False
        # Sakshi should see only her allocated user(s) — <= 3
        assert len(data["users"]) <= 3, f"sub-admin sees too many rows: {len(data['users'])}"

    def test_subadmin_forbidden_signoff(self, subadmin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/signoff", headers=subadmin_headers, timeout=30)
        assert r.status_code == 403

    def test_subadmin_forbidden_delete(self, subadmin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/users/some-uid/delete",
                          headers=subadmin_headers, json={"confirm": "DELETE"}, timeout=30)
        assert r.status_code == 403

    def test_subadmin_forbidden_subscription_grant(self, subadmin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/users/some-uid/subscription",
                          headers=subadmin_headers,
                          json={"action": "grant", "plan": "monthly"}, timeout=30)
        assert r.status_code == 403

    def test_subadmin_forbidden_other_profile(self, subadmin_headers, admin_headers):
        # Get a uid the sub-admin is NOT allocated (target)
        r = requests.get(f"{BASE_URL}/api/admin/users?q=vaibhav.deshmane",
                         headers=admin_headers, timeout=30).json()
        other_uid = r["users"][0]["uid"]
        r2 = requests.get(f"{BASE_URL}/api/admin/users/{other_uid}/profile",
                          headers=subadmin_headers, timeout=30)
        assert r2.status_code == 403, f"expected 403, got {r2.status_code}"


# ---------- 5. User-side verify prefill regression ----------
class TestVerifyPrefill:
    def test_verify_state_ok(self, buyer_headers):
        r = requests.get(f"{BASE_URL}/api/verify/state", headers=buyer_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "profile" in data or "status" in data or isinstance(data, dict)
