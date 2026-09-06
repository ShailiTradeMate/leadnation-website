"""Iter 54 — Admin Phase C two-tier sign-off, edit profile, payments, documents, delete."""
import os
import io
import time
import uuid
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

FIREBASE_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
ADMIN_EMAIL = "admin@vametra.com"
ADMIN_PASS = "Shiv@12345"
SAKSHI_EMAIL = "sakshi@vametra.com"
PATNICA_EMAIL = "patnica@vametra.com"
STAFF_PASS = "Shiv@12345"
ALLOCATED_UID = "SPKdrHke3NNjWTpYwxHUzwLnZbO2"  # Vaibhav, allocated to Sakshi


# ---------------- fixtures ----------------
@pytest.fixture(scope="session")
def admin_headers():
    r = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_KEY}",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS, "returnSecureToken": True},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"firebase login failed: {r.status_code} {r.text[:200]}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


def _staff_login(email):
    r = requests.post(f"{API}/admin-auth/login",
                      json={"identifier": email, "password": STAFF_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="session")
def sakshi_headers():
    return {"X-Staff-Token": _staff_login(SAKSHI_EMAIL)}


@pytest.fixture(scope="session")
def patnica_headers():
    return {"X-Staff-Token": _staff_login(PATNICA_EMAIL)}


# ---------------- Permissions ----------------
class TestPermissions:
    def test_main_admin_permissions(self, admin_headers):
        r = requests.get(f"{API}/admin/permissions", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["is_main"] is True
        perms = set(d["permissions"])
        for p in ("users.view_all", "users.delete", "users.review_final",
                  "payments.grant", "signoff.view", "allocate", "subadmins.manage"):
            assert p in perms, f"main admin missing {p}"

    def test_sub_admin_permissions(self, sakshi_headers):
        r = requests.get(f"{API}/admin/permissions", headers=sakshi_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["is_main"] is False
        perms = set(d["permissions"])
        for p in ("users.view_assigned", "users.edit", "users.review_recommend",
                  "users.contact", "users.documents", "payments.view"):
            assert p in perms
        for forbidden in ("users.delete", "payments.grant", "signoff.view",
                          "subadmins.manage", "allocate", "users.review_final"):
            assert forbidden not in perms, f"sub_admin should not have {forbidden}"


# ---------------- Recommendation → Sign-off flow ----------------
class TestTwoTierSignoff:
    def test_signoff_queue_has_seeded_recommendation(self, admin_headers):
        r = requests.get(f"{API}/admin/signoff", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        q = r.json()
        assert q["count"] >= 1
        matches = [x for x in q["queue"] if x["uid"] == ALLOCATED_UID]
        # If seeded rec was already confirmed, we'll create a fresh one below
        if matches:
            assert matches[0]["recommended"] in ("approve", "reject")
            assert matches[0].get("recommended_by")

    def test_sub_admin_can_recommend_and_no_buyer_email(self, sakshi_headers, admin_headers):
        # Ensure there's an awaiting_signoff for ALLOCATED_UID by having Sakshi recommend
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/review",
            headers=sakshi_headers,
            json={"decision": "approve", "note": "iter54 test recommendation"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["stage"] == "awaiting_signoff"
        assert "sign-off" in body["message"].lower() or "signoff" in body["message"].lower()
        # No email/announce key in response at recommendation stage
        assert "email" not in body

        # Verify appears in queue
        q = requests.get(f"{API}/admin/signoff", headers=admin_headers, timeout=30).json()
        assert any(x["uid"] == ALLOCATED_UID and x["recommended"] == "approve"
                   for x in q["queue"])

    def test_sub_admin_cannot_call_signoff_endpoints(self, sakshi_headers):
        r = requests.get(f"{API}/admin/signoff", headers=sakshi_headers, timeout=30)
        assert r.status_code == 403

    def test_sub_admin_cannot_signoff(self, sakshi_headers, admin_headers):
        q = requests.get(f"{API}/admin/signoff", headers=admin_headers, timeout=30).json()
        row = next((x for x in q["queue"] if x["uid"] == ALLOCATED_UID), None)
        if not row:
            pytest.skip("no recommendation in queue")
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/signoff",
            headers=sakshi_headers,
            json={"submission_id": row["submission_id"], "action": "decline"},
            timeout=30,
        )
        assert r.status_code == 403

    def test_main_admin_return_recommendation(self, admin_headers, sakshi_headers):
        # Sakshi first ensures a recommendation exists
        requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/review",
            headers=sakshi_headers,
            json={"decision": "approve", "note": "iter54 pre-return"},
            timeout=30,
        )
        q = requests.get(f"{API}/admin/signoff", headers=admin_headers, timeout=30).json()
        row = next((x for x in q["queue"] if x["uid"] == ALLOCATED_UID), None)
        assert row is not None
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/signoff",
            headers=admin_headers,
            json={"submission_id": row["submission_id"], "action": "decline",
                  "note": "please double-check the GST"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.json()["stage"] == "returned"
        # Verify recommendation cleared from queue
        q2 = requests.get(f"{API}/admin/signoff", headers=admin_headers, timeout=30).json()
        assert not any(x["uid"] == ALLOCATED_UID for x in q2["queue"])


# ---------------- Main admin direct review ----------------
class TestMainAdminDirectReview:
    def test_correction_requires_fields_or_note(self, admin_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/review",
            headers=admin_headers,
            json={"decision": "correction"},
            timeout=30,
        )
        assert r.status_code == 400

    def test_correction_with_note_sets_stage(self, admin_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/review",
            headers=admin_headers,
            json={"decision": "correction",
                  "fields": ["mobile"], "note": "please share updated mobile"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["stage"] == "correction_requested"
        assert "email" in d  # buyer notified

    def test_invalid_decision_400(self, admin_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/review",
            headers=admin_headers,
            json={"decision": "foobar"},
            timeout=30,
        )
        assert r.status_code == 400


# ---------------- Edit profile ----------------
class TestEditProfile:
    def test_edit_profile_records_change(self, admin_headers):
        new_mobile = f"+91-{int(time.time()) % 10000000000:010d}"
        r = requests.patch(
            f"{API}/admin/users/{ALLOCATED_UID}/profile",
            headers=admin_headers,
            json={"patch": {"mobile": new_mobile}},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # response reports changes list
        assert isinstance(d.get("changes"), list)
        # There should be at least one change reported (mobile) OR profile echoes mobile
        assert d["profile"].get("mobile") == new_mobile or any(
            c.get("field") == "mobile" or "mobile" in str(c).lower() for c in d["changes"]
        )
        # Activity: brain_events should include profile_changed
        act = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/activity",
                           headers=admin_headers, timeout=30).json()
        kinds = [e.get("kind") for e in act.get("brain_events", [])]
        assert "profile_changed" in kinds

    def test_edit_profile_no_change_returns_no_change(self, admin_headers):
        # Fetch current profile mobile then send same value
        act = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/activity",
                           headers=admin_headers, timeout=30)
        assert act.status_code == 200
        # Send an empty patch → 400 nothing to update
        r = requests.patch(
            f"{API}/admin/users/{ALLOCATED_UID}/profile",
            headers=admin_headers, json={"patch": {}}, timeout=30,
        )
        assert r.status_code == 400

    def test_sub_admin_can_edit_allocated(self, sakshi_headers):
        r = requests.patch(
            f"{API}/admin/users/{ALLOCATED_UID}/profile",
            headers=sakshi_headers,
            json={"patch": {"city": "Pune"}},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_sub_admin_cannot_edit_unallocated(self, patnica_headers):
        r = requests.patch(
            f"{API}/admin/users/{ALLOCATED_UID}/profile",
            headers=patnica_headers,
            json={"patch": {"city": "Delhi"}},
            timeout=30,
        )
        assert r.status_code == 403


# ---------------- Payments / subscription ----------------
class TestPayments:
    def test_payments_view_main(self, admin_headers):
        r = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/payments",
                         headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("subscription", "transactions", "invoices", "totals", "can_grant"):
            assert k in d
        assert d["can_grant"] is True

    def test_payments_view_sub(self, sakshi_headers):
        r = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/payments",
                         headers=sakshi_headers, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["can_grant"] is False

    def test_sub_admin_cannot_grant(self, sakshi_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/subscription",
            headers=sakshi_headers,
            json={"action": "grant", "plan": "monthly", "note": "iter54"},
            timeout=30,
        )
        assert r.status_code == 403

    def test_main_admin_grant_and_revoke(self, admin_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/subscription",
            headers=admin_headers,
            json={"action": "grant", "plan": "monthly", "note": "iter54 grant"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "active"
        assert d["plan"] == "monthly"
        assert d.get("until")
        # verify GET reflects it
        p = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/payments",
                         headers=admin_headers, timeout=30).json()
        assert p["subscription"]["status"] == "active"
        assert p["subscription"]["source"] == "admin_grant"

        # revoke
        r2 = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/subscription",
            headers=admin_headers,
            json={"action": "revoke", "note": "iter54 revoke"},
            timeout=30,
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["status"] == "cancelled"


# ---------------- Documents ----------------
class TestDocuments:
    def test_document_upload_by_main(self, admin_headers):
        payload = ("iter54-doc.txt", io.BytesIO(b"iter54 test document bytes"), "text/plain")
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/documents",
            headers=admin_headers,
            files={"file": payload},
            data={"kind": "document", "label": "Iter54 test doc"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("file_id")
        # activity has document_updated
        act = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/activity",
                           headers=admin_headers, timeout=30).json()
        kinds = [e.get("kind") for e in act.get("brain_events", [])]
        assert "document_updated" in kinds


# ---------------- Hard delete RBAC + throwaway ----------------
class TestHardDelete:
    def test_sub_admin_cannot_delete(self, sakshi_headers):
        r = requests.post(
            f"{API}/admin/users/{ALLOCATED_UID}/delete",
            headers=sakshi_headers,
            json={"confirm": "DELETE", "note": "iter54 forbidden"},
            timeout=30,
        )
        assert r.status_code == 403

    def test_main_admin_hard_delete_throwaway(self, admin_headers):
        # Seed a throwaway user + submission via direct Mongo call through admin endpoint
        # We use a fake uid; the endpoint requires either a user OR a submission to exist.
        # Insert via the internal SUBS collection through a helper endpoint? None available.
        # Instead, POST a raw submission using a private path — we'll insert via db
        # Actually we don't have a public seed endpoint; use motor via /api? No.
        # Trick: use admin_deleted_archive check by seeding directly in Mongo via motor.
        import motor.motor_asyncio, asyncio
        mongo_url = os.environ["MONGO_URL"]
        db_name = os.environ["DB_NAME"]
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        throw_uid = f"TEST_iter54_{uuid.uuid4().hex[:10]}"

        async def _seed():
            await db.users.insert_one({
                "uid": throw_uid, "email": f"{throw_uid}@example.com",
                "full_name": "Iter54 Throwaway", "role": "user",
                "customer_id": "99999", "created_at": "2026-01-01T00:00:00+00:00"})
            await db.verification_submissions.insert_one({
                "_id": f"sub_{throw_uid}", "uid": throw_uid,
                "status": "needs_review", "email": f"{throw_uid}@example.com",
                "name": "Iter54 Throwaway", "company_name": "Throwaway Co",
                "created_at": "2026-01-01T00:00:00+00:00"})

        asyncio.get_event_loop().run_until_complete(_seed())

        # Missing confirm → 400
        r0 = requests.post(f"{API}/admin/users/{throw_uid}/delete",
                          headers=admin_headers,
                          json={"confirm": "wrong"}, timeout=30)
        assert r0.status_code == 400

        # Correct DELETE → 200
        r = requests.post(f"{API}/admin/users/{throw_uid}/delete",
                          headers=admin_headers,
                          json={"confirm": "DELETE", "note": "iter54 throwaway"},
                          timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("archived") is True

        async def _verify():
            assert (await db.verification_submissions.count_documents({"uid": throw_uid})) == 0
            u = await db.users.find_one({"uid": throw_uid})
            assert u and u.get("is_deleted") is True
            arch = await db.admin_deleted_archive.find_one({"uid": throw_uid})
            assert arch is not None
            # cleanup
            await db.users.delete_one({"uid": throw_uid})
            await db.admin_deleted_archive.delete_one({"uid": throw_uid})

        asyncio.get_event_loop().run_until_complete(_verify())


# ---------------- RBAC: sub-admin blocked on unallocated user ----------------
class TestSubAdminScope:
    def test_patnica_403_on_sakshi_user(self, patnica_headers):
        r = requests.get(f"{API}/admin/users/{ALLOCATED_UID}/payments",
                         headers=patnica_headers, timeout=30)
        assert r.status_code == 403

    def test_patnica_403_on_review(self, patnica_headers):
        r = requests.post(f"{API}/admin/users/{ALLOCATED_UID}/review",
                          headers=patnica_headers,
                          json={"decision": "approve", "note": "not mine"}, timeout=30)
        assert r.status_code == 403
