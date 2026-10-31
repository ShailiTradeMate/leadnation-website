# Iter80: WhatsApp click logging + CA -> customer WhatsApp hand-off (share links, whatsapp-shared)
import os
import re
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
ADMIN = {"X-Admin-Token": "leadnation-admin-2026"}
STATE = {}
STATE_FILE = "/tmp/iter80_state.json"


def _save():
    json.dump(STATE, open(STATE_FILE, "w"))


@pytest.fixture(scope="module")
def main_admin():
    r = requests.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA",
                      json={"email": "admin@vametra.com", "password": "Shiv@12345", "returnSecureToken": True}, timeout=30)
    if r.status_code != 200:
        pytest.skip("firebase admin token mint failed")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


@pytest.fixture(scope="module")
def sakshi():
    r = requests.post(f"{API}/admin-auth/login", json={"identifier": "sakshi@vametra.com", "password": "Shiv@12345"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"sakshi login failed {r.status_code} {r.text[:200]}")
    return {"X-Staff-Token": r.json()["token"]}


# --- templates
def test_templates_include_ca_message():
    r = requests.get(f"{API}/whatsapp/templates", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert len(d["templates"]) == 8
    assert "ca_message" in d["templates"]
    for p in ("ca_name", "message", "documents"):
        assert p in d["placeholders"]


# --- create service request
def test_create_service_request():
    r = requests.post(f"{API}/service-request", json={"service": "rcmc-registration", "name": "QA Customer",
                      "email": "delivered@resend.dev", "phone": "+91 98765 43210", "country": "IN",
                      "entity": "Proprietorship", "message": "test"}, timeout=60)
    assert r.status_code in (200, 201), r.text
    d = r.json()
    rid = d.get("id") or d.get("requestId") or (d.get("item") or {}).get("id")
    assert rid, d
    STATE["rid"] = rid
    _save()


# --- public click logging
def test_log_click_guest_and_admin_list():
    rid = STATE["rid"]
    r = requests.post(f"{API}/whatsapp/clicks", json={"key": "service_request", "page": "/services/x", "message": "Hi QA",
                      "requestId": rid, "phone": "98765 43210", "name": "QA Guest", "email": "qa@example.com"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True and isinstance(d["id"], str)
    STATE["c1"] = d["id"]
    r = requests.get(f"{API}/admin/whatsapp-clicks", headers=ADMIN, timeout=30)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["id"] == d["id"], "newest-first"
    c = items[0]
    assert c["label"] == "After a service request is submitted"
    assert c["phoneKey"] == "9876543210"
    assert c["signedIn"] is False
    assert c["key"] == "service_request"
    _save()


def test_unknown_key_falls_back_direct():
    r = requests.post(f"{API}/whatsapp/clicks", json={"key": "bogus", "page": "/x", "name": "QA Guest", "email": "qa@example.com"}, timeout=30)
    assert r.status_code == 200
    cid = r.json()["id"]
    items = requests.get(f"{API}/admin/whatsapp-clicks", headers=ADMIN, timeout=30).json()["items"]
    row = next(i for i in items if i["id"] == cid)
    assert row["key"] == "direct"
    assert row["label"] == "WhatsApp link"


def test_admin_clicks_requires_auth():
    r = requests.get(f"{API}/admin/whatsapp-clicks", timeout=30)
    assert r.status_code in (401, 403)


def test_staff_endpoint_with_legacy_admin_token():
    # E1 claims X-Admin-Token is accepted by require_staff; verify
    r = requests.get(f"{API}/staff/service-requests/{STATE['rid']}/whatsapp-clicks", headers=ADMIN, timeout=30)
    assert r.status_code == 200, f"X-Admin-Token not accepted by require_staff: {r.status_code}"


def test_phone_and_email_matching(main_admin):
    rid = STATE["rid"]
    r1 = requests.post(f"{API}/whatsapp/clicks", json={"key": "general", "page": "/", "phone": "9876543210",
                       "name": "QA Guest", "email": "qa.other@example.com"}, timeout=30)
    r2 = requests.post(f"{API}/whatsapp/clicks", json={"key": "contact", "page": "/contact", "name": "QA Guest",
                       "email": "delivered@resend.dev"}, timeout=30)
    assert r1.status_code == 200 and r2.status_code == 200
    r = requests.get(f"{API}/staff/service-requests/{rid}/whatsapp-clicks", headers=main_admin, timeout=30)
    assert r.status_code == 200, r.text
    ids = [i["id"] for i in r.json()["items"]]
    assert STATE["c1"] in ids, "requestId match"
    assert r1.json()["id"] in ids, "phoneKey match"
    assert r2.json()["id"] in ids, "email match"
    reqs = requests.get(f"{API}/admin/service-requests", headers=ADMIN, timeout=30).json()
    sr = next(i for i in reqs if i["id"] == rid)
    assert sr.get("lastWhatsAppAt")


# --- sub-admin scoping
def test_subadmin_scoping(sakshi):
    rid = STATE["rid"]
    r = requests.get(f"{API}/staff/service-requests/{rid}/whatsapp-clicks", headers=sakshi, timeout=30)
    assert r.status_code == 403
    cas = requests.get(f"{API}/admin/service-requests/ca-options", headers=ADMIN, timeout=30).json()["cas"]
    sid = next(c["id"] for c in cas if (c.get("email") or "").lower() == "sakshi@vametra.com")
    r = requests.post(f"{API}/admin/service-requests/{rid}/allocate", headers=ADMIN, json={"assignedCaId": sid, "sendEmail": False}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json()["item"]["assignedCaId"] == sid
    r = requests.get(f"{API}/staff/service-requests/{rid}/whatsapp-clicks", headers=sakshi, timeout=30)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 3


# --- email with files + share link
def test_email_files_and_share_link(sakshi):
    rid = STATE["rid"]
    content = b"QA RCMC draft content iter80"
    r = requests.post(f"{API}/staff/service-requests/{rid}/email-customer-files", headers=sakshi,
                      data={"message": "Your RCMC draft is ready"}, files=[("files", ("qa_rcmc_draft.txt", content, "text/plain"))], timeout=90)
    if r.status_code == 400 and "Email could not be sent" in r.text:
        pytest.skip(f"ENV: Resend failed: {r.text[:200]}")
    assert r.status_code == 200, r.text
    acts = r.json()["item"]["emailActivity"]
    last = acts[-1]
    tok = last["attachments"][0]["shareToken"]
    assert re.fullmatch(r"[0-9a-f]{64}", tok)
    STATE["idx"] = len(acts) - 1
    STATE["token"] = tok
    _save()
    g = requests.get(f"{API}/files/shared/{tok}", timeout=30)
    assert g.status_code == 200
    assert g.content == content
    assert "attachment" in g.headers.get("content-disposition", "")
    assert requests.get(f"{API}/files/shared/invalidtoken", timeout=30).status_code == 404
    assert requests.get(f"{API}/files/shared/{'0' * 64}", timeout=30).status_code == 404


def test_whatsapp_shared(sakshi):
    rid = STATE["rid"]
    if "idx" not in STATE:
        pytest.skip("no message")
    idx = STATE["idx"]
    r = requests.post(f"{API}/staff/service-requests/{rid}/whatsapp-shared", headers=sakshi, json={"activityIndex": idx}, timeout=30)
    assert r.status_code == 200, r.text
    item = r.json()["item"]
    assert item["emailActivity"][idx].get("whatsappSharedAt")
    assert any("sent to customer on WhatsApp" in c for h in item["history"] for c in h.get("changes", []))
    r = requests.post(f"{API}/staff/service-requests/{rid}/whatsapp-shared", headers=sakshi, json={"activityIndex": 999}, timeout=30)
    assert r.status_code == 404
    r = requests.post(f"{API}/staff/service-requests/{rid}/whatsapp-shared", headers=sakshi, json={"activityIndex": -1}, timeout=30)
    assert r.status_code == 404
