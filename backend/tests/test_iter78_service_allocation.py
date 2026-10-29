# Iter78: Service-request allocation (ca-options, PUT update rules, email-ca dryRun + one real send)
import os
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FB_KEY = os.environ.get("REACT_APP_FIREBASE_API_KEY")
CUST = "vaibhav.deshmane@vametra.com"
STATUSES = ["new", "assigned", "in-progress", "Partial payment received", "Full payment received", "completed", "cancelled"]
REAL_SEND = os.environ.get("ITER78_REAL_SEND") == "1"


@pytest.fixture(scope="module")
def s():
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
                      json={"email": "admin@vametra.com", "password": "Shiv@12345", "returnSecureToken": True}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Firebase login failed {r.text[:200]}")
    ses = requests.Session()
    ses.headers.update({"Authorization": f"Bearer {r.json()['idToken']}", "Content-Type": "application/json"})
    return ses


@pytest.fixture(scope="module")
def created():
    ids = []
    yield ids
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    if ids:
        db.service_requests.delete_many({"id": {"$in": ids}})
        db.leads.delete_many({"name": {"$regex": "^TEST_iter78"}})


def _new_req(created, name="TEST_iter78 Req"):
    r = requests.post(f"{BASE_URL}/api/service-request", json={"service": "gst-registration", "name": name, "email": CUST,
                      "phone": "9999999999", "entity": "Proprietorship", "message": "TEST_iter78 automated"}, timeout=30)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    created.append(rid)
    return rid


def _get(s, rid):
    items = s.get(f"{BASE_URL}/api/admin/service-requests", timeout=30).json()
    return next(i for i in items if i["id"] == rid)


class TestCaOptions:
    def test_unauth(self):
        assert requests.get(f"{BASE_URL}/api/admin/service-requests/ca-options", timeout=20).status_code == 401

    def test_options(self, s):
        r = s.get(f"{BASE_URL}/api/admin/service-requests/ca-options", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["statuses"] == STATUSES
        names = {c["name"] for c in d["cas"]}
        print("CAs:", d["cas"])
        for n in ("PatniCA", "Sakshi", "QA UI Phase B"):
            assert n in names
        for c in d["cas"]:
            assert c["id"] and "email" in c


class TestUpdate:
    def test_submission_stores_meta(self, s, created):
        rid = _new_req(created)
        it = _get(s, rid)
        assert it["status"] == "new"
        assert it["serviceLabel"] == "GST Registration"
        assert it["entity"] == "Proprietorship"
        assert it["profileRows"] == [["Account", "Submitted as guest (not logged in)"]]

    def test_assign_subadmin_auto_status(self, s, created):
        rid = created[0]
        ca = next(c for c in s.get(f"{BASE_URL}/api/admin/service-requests/ca-options").json()["cas"] if c["name"] == "PatniCA")
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"assignedCaId": ca["id"]})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "assigned"
        assert d["assignedCa"] == "PatniCA" and d["assignedCaId"] == ca["id"]
        assert d["assignedCaEmail"] == (ca["email"] or "").lower()
        assert len(d["history"]) >= 1 and any("auto" in c for c in d["history"][-1]["changes"])
        assert _get(s, rid)["status"] == "assigned"

    def test_invalid_status(self, s, created):
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{created[0]}", json={"status": "bogus"})
        assert r.status_code == 400

    def test_unknown_subadmin_404(self, s, created):
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{created[0]}", json={"assignedCaId": "nope-xyz"})
        assert r.status_code == 404

    def test_email_free_text_lower_and_note(self, s, created):
        rid = created[0]
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"assignedCaEmail": "  Some.CA@Firm.COM ", "internalNote": "TEST note"})
        assert r.status_code == 200
        d = r.json()
        assert d["assignedCaEmail"] == "some.ca@firm.com"
        assert d["notes"][-1]["text"] == "TEST note"
        assert _get(s, rid)["assignedCaEmail"] == "some.ca@firm.com"

    def test_clear_ca(self, s, created):
        rid = created[0]
        d = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"clearCa": True}).json()
        assert d["assignedCa"] is None and d["assignedCaId"] is None and d["assignedCaEmail"] is None
        assert "CA unassigned" in d["history"][-1]["changes"]

    def test_external_ca(self, s, created):
        rid = created[0]
        d = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"assignedCaId": None, "assignedCa": "Ext CA", "assignedCaEmail": "EXT@x.com"}).json()
        assert d["assignedCa"] == "Ext CA" and d["assignedCaEmail"] == "ext@x.com" and d["assignedCaId"] is None

    def test_completed_blocks_ca(self, s, created):
        rid = _new_req(created, "TEST_iter78 Closed")
        assert s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"status": "completed"}).json()["status"] == "completed"
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"assignedCaEmail": "a@b.com"})
        assert r.status_code == 400 and "Completed or cancelled" in r.json()["detail"]
        r = s.put(f"{BASE_URL}/api/admin/service-requests/{rid}", json={"clearCa": True})
        assert r.status_code == 400
        r = s.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-ca", json={"to": "admin@vametra.com", "dryRun": True})
        assert r.status_code == 400

    def test_404(self, s):
        assert s.put(f"{BASE_URL}/api/admin/service-requests/nope", json={"status": "new"}).status_code == 404


class TestEmailCa:
    def test_dry_run(self, s, created):
        rid = created[0]
        r = s.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-ca",
                   json={"to": "CA.Person@Firm.com", "extraCc": ["extra@firm.com"], "note": "Call after 6", "dryRun": True})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["subject"] == "Vametra Service Request · GST Registration · Allocated to Vametra CA"
        assert d["to"] == "ca.person@firm.com"
        assert CUST in d["cc"] and "admin@vametra.com" in d["cc"] and "extra@firm.com" in d["cc"]
        assert d["lockedCc"] == [CUST, "admin@vametra.com"]
        assert "Call after 6" in d["html"] and "Allocated to Vametra CA" in d["html"]
        # dryRun must not mutate
        assert not _get(s, rid).get("caNotifiedAt")

    def test_invalid_to(self, s, created):
        r = s.post(f"{BASE_URL}/api/admin/service-requests/{created[0]}/email-ca", json={"to": "not-an-email", "dryRun": True})
        assert r.status_code == 400

    def test_invalid_extra_cc(self, s, created):
        r = s.post(f"{BASE_URL}/api/admin/service-requests/{created[0]}/email-ca", json={"to": "a@b.com", "extraCc": ["bad@"], "dryRun": True})
        assert r.status_code == 400 and "Invalid CC" in r.json()["detail"]

    @pytest.mark.skipif(not REAL_SEND, reason="real send only when ITER78_REAL_SEND=1")
    def test_real_send_once(self, s, created):
        rid = _new_req(created, "TEST_iter78 RealSend")
        r = s.post(f"{BASE_URL}/api/admin/service-requests/{rid}/email-ca", json={"to": "admin@vametra.com"})
        print(r.status_code, r.text[:400])
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] and CUST in d["cc"]
        it = d["item"]
        assert it["caNotifiedAt"] and it["status"] == "assigned" and it["emailActivity"][-1]["providerId"]
