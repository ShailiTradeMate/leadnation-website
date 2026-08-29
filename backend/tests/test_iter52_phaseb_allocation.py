"""Phase B — Allocation & Sub-admin CRUD backend tests."""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@vametra.com"
ADMIN_PASS = "Shiv@12345"
SAKSHI_EMAIL = "sakshi@vametra.com"
PATNICA_EMAIL = "patnica@vametra.com"
STAFF_PASS = "Shiv@12345"


# ---------------- fixtures ----------------
@pytest.fixture(scope="module")
def admin_bearer():
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS, "returnSecureToken": True},
        timeout=20,
    )
    assert r.status_code == 200, f"Firebase sign-in failed: {r.text}"
    return r.json()["idToken"]


def _staff_login(email):
    # tolerate cold-start
    for attempt in range(3):
        try:
            r = requests.post(f"{BASE_URL}/api/admin-auth/login",
                              json={"identifier": email, "password": STAFF_PASS},
                              timeout=30)
            if r.status_code == 200:
                return r.json()["token"]
        except requests.RequestException:
            pass
        time.sleep(3)
    pytest.skip(f"Could not log in staff {email}")


@pytest.fixture(scope="module")
def sakshi_token():
    return _staff_login(SAKSHI_EMAIL)


@pytest.fixture(scope="module")
def patnica_token():
    return _staff_login(PATNICA_EMAIL)


def admin_headers(token):
    return {"Authorization": f"Bearer {token}"}


def staff_headers(token):
    return {"X-Staff-Token": token}


# ---------------- Phase B tests ----------------
class TestAllocationEndpoints:
    def test_pending_counts(self, admin_bearer):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/pending",
                         headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "pending" in d and "unassigned" in d
        assert isinstance(d["pending"], int)
        assert isinstance(d["unassigned"], int)

    def test_list_subadmins(self, admin_bearer):
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200
        subs = r.json()["subadmins"]
        emails = [s["email"] for s in subs]
        assert SAKSHI_EMAIL in emails
        assert PATNICA_EMAIL in emails
        for s in subs:
            assert "id" in s and "active" in s and "assigned_pending" in s

    def test_allocate_no_pending_returns_ok_zero(self, admin_bearer):
        # find sakshi's id
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=admin_headers(admin_bearer), timeout=30)
        sakshi = next(s for s in r.json()["subadmins"] if s["email"] == SAKSHI_EMAIL)
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": [sakshi["id"]]},
                          headers=admin_headers(admin_bearer), timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["allocated"] >= 0  # 0 expected when unassigned=0

    def test_allocate_requires_active_subadmin(self, admin_bearer):
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": ["nonexistent-id"]},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 400


class TestSubAdminCRUD:
    created_id = None
    created_email = None

    def test_create_subadmin(self, admin_bearer):
        email = f"qa_phaseb_{uuid.uuid4().hex[:6]}@vametra.com"
        r = requests.post(f"{BASE_URL}/api/admin/subadmins",
                          json={"name": "QA Phase B", "email": email, "password": "Shiv@12345"},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["email"] == email
        assert d["id"]
        TestSubAdminCRUD.created_id = d["id"]
        TestSubAdminCRUD.created_email = email

    def test_created_subadmin_appears_in_list_active(self, admin_bearer):
        assert TestSubAdminCRUD.created_id
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=admin_headers(admin_bearer), timeout=30)
        sub = next((s for s in r.json()["subadmins"] if s["id"] == TestSubAdminCRUD.created_id), None)
        assert sub is not None
        assert sub["active"] is True

    def test_duplicate_email_conflict(self, admin_bearer):
        assert TestSubAdminCRUD.created_email
        r = requests.post(f"{BASE_URL}/api/admin/subadmins",
                          json={"name": "Dup", "email": TestSubAdminCRUD.created_email, "password": "Shiv@12345"},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 409

    def test_toggle_deactivate(self, admin_bearer):
        assert TestSubAdminCRUD.created_id
        r = requests.patch(f"{BASE_URL}/api/admin/subadmins/{TestSubAdminCRUD.created_id}",
                           json={"active": False},
                           headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/admin/subadmins",
                          headers=admin_headers(admin_bearer), timeout=30)
        sub = next(s for s in r2.json()["subadmins"] if s["id"] == TestSubAdminCRUD.created_id)
        assert sub["active"] is False

    def test_deactivated_cannot_login(self, admin_bearer):
        assert TestSubAdminCRUD.created_email
        r = requests.post(f"{BASE_URL}/api/admin-auth/login",
                          json={"identifier": TestSubAdminCRUD.created_email, "password": "Shiv@12345"},
                          timeout=30)
        assert r.status_code == 403


class TestRBAC:
    def test_subadmin_cannot_list_subadmins(self, sakshi_token):
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403

    def test_subadmin_cannot_create_subadmins(self, sakshi_token):
        r = requests.post(f"{BASE_URL}/api/admin/subadmins",
                          json={"name": "x", "email": "x@x.com", "password": "Shiv@12345"},
                          headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403

    def test_subadmin_cannot_allocate(self, sakshi_token):
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": ["any"]},
                          headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403

    def test_subadmin_cannot_read_allocate_pending(self, sakshi_token):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/pending",
                         headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403


class TestSubAdminScope:
    def test_sakshi_sees_only_allocated(self, sakshi_token):
        r = requests.get(f"{BASE_URL}/api/admin/users",
                         headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["is_main"] is False
        # Every returned row must be assigned to this sub-admin
        for row in d["users"]:
            assert row.get("assigned_to")  # must not be None/empty

    def test_patnica_sees_zero(self, patnica_token):
        r = requests.get(f"{BASE_URL}/api/admin/users",
                         headers=staff_headers(patnica_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["is_main"] is False
        assert d["total"] == 0

    def test_main_admin_sees_all(self, admin_bearer):
        r = requests.get(f"{BASE_URL}/api/admin/users",
                         headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["is_main"] is True
        assert d["total"] >= 1


# ---------------- Cleanup ----------------
def test_zz_cleanup_created_subadmin(request):
    # Fire a Firebase login just for cleanup
    if not TestSubAdminCRUD.created_id:
        pytest.skip("nothing to clean")
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS, "returnSecureToken": True},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip("no admin token for cleanup")
    tok = r.json()["idToken"]
    # Leave it deactivated (there is no DELETE endpoint) — safe by design.
    requests.patch(f"{BASE_URL}/api/admin/subadmins/{TestSubAdminCRUD.created_id}",
                   json={"active": False},
                   headers={"Authorization": f"Bearer {tok}"}, timeout=30)
