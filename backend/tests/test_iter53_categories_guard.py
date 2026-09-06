"""Iter 53 — Allocation CATEGORIES + approved-user guard tests.

Focus:
  - GET /api/admin/allocate/categories shape + counts
  - POST /api/admin/allocate returns 400 when submission_ids include a
    non-needs_review row (verified/approved/rejected)
  - POST /api/admin/allocate with category='missing_details' allocates only
    pending submissions that have missing details
  - RBAC: sub-admin gets 403 on both endpoints
Seeds a couple of verification_submissions directly in Mongo and cleans them
up afterwards.
"""
import os
import time
import uuid
import asyncio
import requests
import pytest
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

MONGO_URL = os.environ.get("MONGO_URL") or open("/app/backend/.env").read().split('MONGO_URL="')[1].split('"')[0]
DB_NAME = os.environ.get("DB_NAME") or "leadnation"

FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@vametra.com"
ADMIN_PASS = "Shiv@12345"
SAKSHI_EMAIL = "sakshi@vametra.com"
STAFF_PASS = "Shiv@12345"

TAG = f"TEST_iter53_{uuid.uuid4().hex[:6]}"

# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def admin_bearer():
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS, "returnSecureToken": True},
        timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["idToken"]


@pytest.fixture(scope="module")
def sakshi_token():
    for _ in range(3):
        r = requests.post(f"{BASE_URL}/api/admin-auth/login",
                          json={"identifier": SAKSHI_EMAIL, "password": STAFF_PASS}, timeout=30)
        if r.status_code == 200:
            return r.json()["token"]
        time.sleep(2)
    pytest.skip("staff login failed")


@pytest.fixture(scope="module")
def seeded_ids():
    """Seed 3 test verification submissions: needs_review, verified, rejected.
    Also seed a pending-with-missing-details.
    """
    async def _seed():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        now = datetime.now(timezone.utc).isoformat()
        docs = {
            "needs_review": {
                "_id": f"{TAG}_needs",
                "id": f"{TAG}_needs",
                "status": "needs_review",
                "email": f"{TAG.lower()}_needs@example.com",
                "name": f"{TAG} Needs",
                "mobile": "9990000001",
                "company_name": f"{TAG} Co",
                "company_phone": "9990000011",
                "country": "IN",
                "document_file_id": "fake-doc-id",
                "selfie_file_id": "fake-selfie-id",
                "created_at": now,
            },
            "verified": {
                "_id": f"{TAG}_verified",
                "id": f"{TAG}_verified",
                "status": "verified",
                "email": f"{TAG.lower()}_verified@example.com",
                "name": f"{TAG} Verified",
                "mobile": "9990000002",
                "company_name": f"{TAG} Co V",
                "created_at": now,
            },
            "rejected": {
                "_id": f"{TAG}_rejected",
                "id": f"{TAG}_rejected",
                "status": "rejected",
                "email": f"{TAG.lower()}_rejected@example.com",
                "name": f"{TAG} Rejected",
                "created_at": now,
            },
            "missing": {
                "_id": f"{TAG}_missing",
                "id": f"{TAG}_missing",
                "status": "needs_review",
                "email": f"{TAG.lower()}_missing@example.com",
                "name": f"{TAG} Missing",
                # No mobile, no company_name, no docs -> missing details
                "created_at": now,
            },
        }
        for d in docs.values():
            await db.verification_submissions.insert_one(d)
        client.close()
        return {k: v["_id"] for k, v in docs.items()}

    ids = asyncio.get_event_loop().run_until_complete(_seed()) if False else asyncio.new_event_loop().run_until_complete(_seed())
    yield ids
    # Cleanup
    async def _cleanup():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.verification_submissions.delete_many({"_id": {"$in": list(ids.values())}})
        client.close()
    asyncio.new_event_loop().run_until_complete(_cleanup())


def admin_headers(t): return {"Authorization": f"Bearer {t}"}
def staff_headers(t): return {"X-Staff-Token": t}


# ---------- Categories endpoint ----------
class TestAllocateCategories:
    def test_categories_shape(self, admin_bearer, seeded_ids):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/categories",
                         headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 200, r.text
        cats = r.json()["categories"]
        keys = {c["key"] for c in cats}
        expected = {"pending_unassigned", "pending_assigned", "missing_details",
                    "no_verification", "approved", "rejected"}
        assert expected.issubset(keys), f"missing keys, got {keys}"
        for c in cats:
            assert "count" in c and "items" in c and "allocatable" in c and "hint" in c
            assert c["count"] == len(c["items"])
        # allocatable flags
        by_key = {c["key"]: c for c in cats}
        assert by_key["pending_unassigned"]["allocatable"] is True
        assert by_key["missing_details"]["allocatable"] is True
        assert by_key["no_verification"]["allocatable"] is False
        assert by_key["approved"]["allocatable"] is False
        assert by_key["rejected"]["allocatable"] is False

    def test_seeded_rows_appear_in_expected_categories(self, admin_bearer, seeded_ids):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/categories",
                         headers=admin_headers(admin_bearer), timeout=30)
        cats = {c["key"]: c for c in r.json()["categories"]}

        def has(cat_key, sid):
            return any((it.get("submission_id") == sid) for it in cats[cat_key]["items"])

        assert has("approved", seeded_ids["verified"]), "verified sub should be in approved"
        assert has("rejected", seeded_ids["rejected"]), "rejected sub should be in rejected"
        # pending w/ complete details -> pending_unassigned but NOT missing_details
        assert has("pending_unassigned", seeded_ids["needs_review"])
        # pending w/ missing details -> both pending_unassigned AND missing_details
        assert has("pending_unassigned", seeded_ids["missing"])
        assert has("missing_details", seeded_ids["missing"])
        # verify missing labels present on the missing one
        miss_item = next(it for it in cats["missing_details"]["items"]
                         if it.get("submission_id") == seeded_ids["missing"])
        assert isinstance(miss_item["missing"], list) and len(miss_item["missing"]) >= 1

    def test_subadmin_cannot_read_categories(self, sakshi_token):
        r = requests.get(f"{BASE_URL}/api/admin/allocate/categories",
                         headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403


# ---------- Guard: cannot allocate approved / rejected ----------
class TestAllocateGuard:
    def _sakshi_id(self, admin_bearer):
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=admin_headers(admin_bearer), timeout=30)
        return next(s for s in r.json()["subadmins"] if s["email"] == SAKSHI_EMAIL)["id"]

    def test_allocate_with_verified_id_returns_400(self, admin_bearer, seeded_ids):
        sid = self._sakshi_id(admin_bearer)
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": [sid],
                                "submission_ids": [seeded_ids["verified"]]},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        assert "not awaiting review" in detail.lower() or "cannot be allocated" in detail.lower()

    def test_allocate_with_rejected_id_returns_400(self, admin_bearer, seeded_ids):
        sid = self._sakshi_id(admin_bearer)
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": [sid],
                                "submission_ids": [seeded_ids["rejected"]]},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 400

    def test_allocate_mixed_ids_all_or_nothing(self, admin_bearer, seeded_ids):
        """If one of the submission_ids is not needs_review, the whole call is
        rejected and NO submission gets assigned."""
        sid = self._sakshi_id(admin_bearer)
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": [sid],
                                "submission_ids": [seeded_ids["needs_review"],
                                                   seeded_ids["verified"]]},
                          headers=admin_headers(admin_bearer), timeout=30)
        assert r.status_code == 400
        # Verify the needs_review one was NOT assigned
        async def _check():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            doc = await db.verification_submissions.find_one({"_id": seeded_ids["needs_review"]})
            client.close()
            return doc
        doc = asyncio.new_event_loop().run_until_complete(_check())
        assert doc is not None
        assert not doc.get("assigned_to"), f"needs_review sub should not be assigned, got {doc.get('assigned_to')}"

    def test_subadmin_cannot_allocate(self, sakshi_token, seeded_ids):
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": ["x"],
                                "submission_ids": [seeded_ids["needs_review"]]},
                          headers=staff_headers(sakshi_token), timeout=30)
        assert r.status_code == 403


# ---------- Missing-details category allocation ----------
class TestAllocateMissingCategory:
    def test_allocate_missing_details_only(self, admin_bearer, seeded_ids):
        # Grab sakshi id
        r = requests.get(f"{BASE_URL}/api/admin/subadmins",
                         headers=admin_headers(admin_bearer), timeout=30)
        sid = next(s for s in r.json()["subadmins"] if s["email"] == SAKSHI_EMAIL)["id"]

        # Allocate by category=missing_details (no submission_ids -> filters on server)
        r = requests.post(f"{BASE_URL}/api/admin/allocate",
                          json={"subadmin_ids": [sid], "category": "missing_details",
                                "include_assigned": True},
                          headers=admin_headers(admin_bearer), timeout=60)
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True

        # Verify our seeded 'missing' doc got assigned, but the 'needs_review'
        # (complete) doc did NOT (through this category call at least).
        async def _check():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            m = await db.verification_submissions.find_one({"_id": seeded_ids["missing"]})
            client.close()
            return m
        m = asyncio.new_event_loop().run_until_complete(_check())
        assert m and m.get("assigned_to") == sid, f"missing-details sub should be allocated to sakshi, got {m}"

        # And the 'verified' should still be untouched
        async def _check2():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            v = await db.verification_submissions.find_one({"_id": seeded_ids["verified"]})
            client.close()
            return v
        v = asyncio.new_event_loop().run_until_complete(_check2())
        assert v and not v.get("assigned_to")
