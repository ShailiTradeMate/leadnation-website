# WhatsApp message templates: public GET, admin GET/PUT/reset, auth gates
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FB_KEY = "AIzaSyCHQaCkzlfOdVB1-bzuJ_NnCE7vRFmT5WA"
KEYS = ["general", "service_request", "service_enquiry", "contact", "supplier_connect", "cha_connect", "tool_help"]


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FB_KEY}",
                      json={"email": "admin@vametra.com", "password": "Shiv@12345", "returnSecureToken": True}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"firebase login failed {r.text[:200]}")
    return {"Authorization": f"Bearer {r.json()['idToken']}"}


# Public
def test_public_templates():
    r = requests.get(f"{BASE_URL}/api/whatsapp/templates", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert sorted(d["templates"].keys()) == sorted(KEYS)
    assert "{{name}}" in d["templates"]["general"]
    assert "{{request_id}}" in d["templates"]["service_request"]
    assert "name" in d["placeholders"]


# Admin gates
@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/whatsapp-templates"),
    ("put", "/api/admin/whatsapp-templates/general"),
    ("post", "/api/admin/whatsapp-templates/general/reset"),
])
def test_admin_requires_auth(method, path):
    r = getattr(requests, method)(f"{BASE_URL}{path}", json={"template": "x"}, timeout=20)
    assert r.status_code in (401, 403)


def test_admin_list(admin_headers):
    r = requests.get(f"{BASE_URL}/api/admin/whatsapp-templates", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    items = r.json()["items"]
    assert [i["key"] for i in items] == KEYS
    for i in items:
        assert i["label"] and i["where"] and i["default"] and i["template"]


def test_admin_update_and_reset(admin_headers):
    txt = "TEST_ Hi Vametra, contact page custom.\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}"
    r = requests.put(f"{BASE_URL}/api/admin/whatsapp-templates/contact", json={"template": txt}, headers=admin_headers, timeout=20)
    assert r.status_code == 200 and r.json()["customized"] is True
    pub = requests.get(f"{BASE_URL}/api/whatsapp/templates", timeout=20).json()
    assert pub["templates"]["contact"] == txt
    adm = requests.get(f"{BASE_URL}/api/admin/whatsapp-templates", headers=admin_headers, timeout=20).json()
    c = [i for i in adm["items"] if i["key"] == "contact"][0]
    assert c["customized"] is True and c["updatedAt"]
    r = requests.post(f"{BASE_URL}/api/admin/whatsapp-templates/contact/reset", headers=admin_headers, timeout=20)
    assert r.status_code == 200 and r.json()["customized"] is False
    pub = requests.get(f"{BASE_URL}/api/whatsapp/templates", timeout=20).json()
    assert pub["templates"]["contact"].startswith("Hi Vametra AI, I'm reaching out through your Contact page")


def test_admin_validation(admin_headers):
    r = requests.put(f"{BASE_URL}/api/admin/whatsapp-templates/nope", json={"template": "x"}, headers=admin_headers, timeout=20)
    assert r.status_code == 404
    r = requests.put(f"{BASE_URL}/api/admin/whatsapp-templates/general", json={"template": "   "}, headers=admin_headers, timeout=20)
    assert r.status_code == 400
    r = requests.post(f"{BASE_URL}/api/admin/whatsapp-templates/nope/reset", headers=admin_headers, timeout=20)
    assert r.status_code == 404
