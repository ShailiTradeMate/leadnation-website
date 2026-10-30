# Iter79: Phase 4 — /allocate endpoint, staff (sub-admin) service-request endpoints, email-customer dryRun
import os
import uuid
from datetime import datetime, timezone
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FB_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY")
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
PATNI = DB.sub_admins.find_one({"email": "patnica@vametra.com"})["id"]
SAKSHI = DB.sub_admins.find_one({"email": "sakshi@vametra.com"})["id"]


@pytest.fixture(scope="module")
def admin():
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
                      json={"email": "admin@vametra.com", "password": "Shiv@12345", "returnSecureToken": True}, timeout=20)
    if r.status_code != 200:
        pytest.skip("Firebase login failed")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {r.json()['idToken']}"})
    return s


def _staff(email):
    r = requests.post(f"{BASE_URL}/api/admin-auth/login", json={"identifier": email, "password": "Shiv@12345"}, timeout=20)
    assert r.status_code == 200, r.text
    s = requests.Session()
    s.headers.update({"X-Staff-Token": r.json()["token"]})
    return s


@pytest.fixture(scope="module")
def patni():
    return _staff("patnica@vametra.com")


@pytest.fixture(scope="module")
def sakshi():
    return _staff("sakshi@vametra.com")


@pytest.fixture(scope="module")
def ids():
    out = []
    yield out
    DB.service_requests.delete_many({"id": {"$in": out}})


def _seed(ids, status="new", **extra):
    rid = f"TEST_iter79_{uuid.uuid4().hex[:8]}"
    doc = {"id": rid, "service": "gst-registration", "serviceLabel": "GST Registration", "name": "TEST_iter79 Cust",
           "email": "test_iter79@example.com", "phone": "9999999999", "status": status,
           "createdAt": datetime.now(timezone.utc).isoformat(), "history": [], "notes": []}
    doc.update(extra)
    DB.service_requests.insert_one(doc)
    ids.append(rid)
    return rid


def _doc(rid):
    return DB.service_requests.find_one({"id": rid}, {"_id": 0})


# ---- Allocate (main admin) ----
class TestAllocate:
    def test_allocate_patni_no_email(self, admin, ids):
        rid = _seed(ids, openedBy=["x"])
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate", json={"assignedCaId": PATNI, "sendEmail": False}, timeout=20)
        assert r.status_code == 200, r.text
        it = r.json()["item"]
        assert it["assignedCa"] == "PatniCA" and it["assignedCaEmail"] == "patnica@vametra.com"
        assert it["status"] == "assigned" and it["openedBy"] == []
        assert any("allocated to PatniCA" in c for h in it["history"] for c in h["changes"])
        assert _doc(rid)["assignedCaId"] == PATNI

    def test_allocate_external(self, admin, ids):
        rid = _seed(ids)
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate",
                       json={"assignedCa": "External Firm", "assignedCaEmail": "ext@firm.com", "sendEmail": False}, timeout=20)
        assert r.status_code == 200, r.text
        d = _doc(rid)
        assert d["assignedCa"] == "External Firm" and d["assignedCaEmail"] == "ext@firm.com" and d["assignedCaId"] is None

    def test_send_email_invalid(self, admin, ids):
        rid = _seed(ids)
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate",
                       json={"assignedCa": "X", "assignedCaEmail": "bad", "sendEmail": True}, timeout=20)
        assert r.status_code == 400
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate", json={"assignedCa": "X", "sendEmail": True}, timeout=20)
        assert r.status_code == 400
        assert _doc(rid).get("assignedCa") is None

    def test_completed_rejected(self, admin, ids):
        rid = _seed(ids, status="completed")
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate", json={"assignedCaId": PATNI, "sendEmail": False}, timeout=20)
        assert r.status_code == 400

    def test_external_no_name(self, admin, ids):
        rid = _seed(ids)
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate", json={"assignedCaEmail": "a@b.com", "sendEmail": False}, timeout=20)
        assert r.status_code == 400

    def test_subadmin_cannot_allocate(self, patni, ids):
        rid = _seed(ids)
        r = patni.post(f"{BASE_URL}/api/admin/service-requests/{rid}/allocate", json={"assignedCaId": PATNI, "sendEmail": False}, timeout=20)
        assert r.status_code in (401, 403)


# ---- Staff endpoints ----
class TestStaff:
    def test_list_only_mine(self, patni, ids):
        mine = _seed(ids, status="assigned", assignedCaId=PATNI, assignedCa="PatniCA", assignedCaEmail="patnica@vametra.com", openedBy=[])
        other = _seed(ids, status="assigned", assignedCaId=SAKSHI, assignedCa="Sakshi")
        r = patni.get(f"{BASE_URL}/api/staff/service-requests", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert all(i["assignedCaId"] == PATNI for i in d["items"])
        got = {i["id"]: i for i in d["items"]}
        assert mine in got and other not in got and got[mine]["isNew"] is True
        assert d["me"]["sid"] == PATNI and d["me"]["isMain"] is False and "statuses" in d
        # forbidden on someone else's
        assert patni.put(f"{BASE_URL}/api/staff/service-requests/{other}", json={"status": "in-progress"}, timeout=20).status_code == 403
        assert patni.post(f"{BASE_URL}/api/staff/service-requests/{other}/open", timeout=20).status_code == 403
        assert patni.post(f"{BASE_URL}/api/staff/service-requests/{other}/email-customer", json={"message": "hi", "dryRun": True}, timeout=20).status_code == 403

    def test_open_clears_new(self, patni, ids):
        rid = _seed(ids, status="assigned", assignedCaId=PATNI, assignedCa="PatniCA", assignedCaEmail="patnica@vametra.com", openedBy=[])
        before = patni.get(f"{BASE_URL}/api/staff/service-requests/summary", timeout=20).json()
        assert set(before) >= {"open", "new", "unassigned"}
        assert patni.post(f"{BASE_URL}/api/staff/service-requests/{rid}/open", timeout=20).status_code == 200
        after = patni.get(f"{BASE_URL}/api/staff/service-requests/summary", timeout=20).json()
        assert after["new"] == before["new"] - 1
        it = next(i for i in patni.get(f"{BASE_URL}/api/staff/service-requests", timeout=20).json()["items"] if i["id"] == rid)
        assert it["isNew"] is False

    def test_update_and_completed_final(self, admin, patni, ids):
        rid = _seed(ids, status="assigned", assignedCaId=PATNI, assignedCa="PatniCA", assignedCaEmail="patnica@vametra.com")
        r = patni.put(f"{BASE_URL}/api/staff/service-requests/{rid}", json={"status": "in-progress", "internalNote": "x", "assignedCa": "Hacker", "assignedCaId": SAKSHI}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "in-progress" and d["history"][-1]["by"] == "patnica@vametra.com"
        assert d["notes"][-1]["text"] == "x" and d["assignedCa"] == "PatniCA" and d["assignedCaId"] == PATNI
        assert patni.put(f"{BASE_URL}/api/staff/service-requests/{rid}", json={"status": "completed"}, timeout=20).status_code == 200
        r = patni.put(f"{BASE_URL}/api/staff/service-requests/{rid}", json={"status": "in-progress"}, timeout=20)
        assert r.status_code == 400 and "Completed requests are final" in r.json()["detail"]
        r = admin.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"status": "in-progress"}, timeout=20)
        assert r.status_code == 200 and r.json()["status"] == "in-progress"

    def test_staff_email_customer_dry(self, patni, ids):
        rid = _seed(ids, status="assigned", assignedCaId=PATNI, assignedCa="PatniCA", assignedCaEmail="patnica@vametra.com")
        r = patni.post(f"{BASE_URL}/api/staff/service-requests/{rid}/email-customer", json={"message": "Hello <b>x</b>", "dryRun": True}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["to"] == "test_iter79@example.com"
        assert "admin@vametra.com" in d["cc"] and "patnica@vametra.com" in d["cc"]
        assert "PatniCA" in d["html"] and "(your Vametra CA)" in d["html"]
        assert "&lt;b&gt;x&lt;/b&gt;" in d["html"]

    def test_main_admin_sees_all(self, admin):
        r = admin.get(f"{BASE_URL}/api/staff/service-requests", timeout=20)
        assert r.status_code == 200
        assert len(r.json()["items"]) == DB.service_requests.count_documents({})
        assert r.json()["me"]["isMain"] is True

    def test_staff_unauth(self):
        assert requests.get(f"{BASE_URL}/api/staff/service-requests", timeout=20).status_code == 401


# ---- Admin email-customer dryRun ----
class TestAdminEmailCustomer:
    def test_dry(self, admin, ids):
        rid = _seed(ids, status="assigned", assignedCaId=PATNI, assignedCa="PatniCA", assignedCaEmail="patnica@vametra.com")
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-customer", json={"message": "Hi <script>x</script>", "dryRun": True}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["subject"] == "Vametra Service Request · GST Registration · Allocated to Vametra CA"
        assert set(d["cc"]) == {"admin@vametra.com", "patnica@vametra.com"}
        assert "<script>x</script>" not in d["html"] and "&lt;script&gt;" in d["html"]

    def test_blank(self, admin, ids):
        rid = _seed(ids)
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-customer", json={"message": "  ", "dryRun": True}, timeout=20)
        assert r.status_code == 400 and r.json()["detail"] == "Write a message first"

    def test_bad_cc(self, admin, ids):
        rid = _seed(ids)
        r = admin.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-customer", json={"message": "hi", "extraCc": ["nope"], "dryRun": True}, timeout=20)
        assert r.status_code == 400
