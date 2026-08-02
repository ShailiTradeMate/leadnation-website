"""VBIE Phase 2 backend tests — scale, QA audit, admin CRUD/export, notifications, buyer warning, Brain gating."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-preview.preview.emergentagent.com").rstrip("/")
ADMIN_HEADERS = {"X-Admin-Token": "leadnation-admin-2026"}


def _items(j):
    return j.get("buyers") or j.get("items") or j.get("results") or []


@pytest.fixture(scope="module")
def sample_geid():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"limit": 5}, timeout=30)
    assert r.status_code == 200
    items = _items(r.json())
    assert items, "no buyers returned"
    return items[0].get("geid") or items[0].get("id")


# ---- SCALE ----
def test_meta_scale():
    r = requests.get(f"{BASE_URL}/api/buyers/meta", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j["total"] >= 10000, f"total={j['total']}"
    assert len(j["countries"]) >= 10
    assert len(j["sectors"]) >= 3


# ---- QA AUDIT ----
def test_qa_audit():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/qa", headers=ADMIN_HEADERS, timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("overall_pass") is True, f"QA failed: {j}"
    checks = j.get("checks", {})
    for key in ["unique_geid", "no_duplicate_entities", "provenance_present",
                "source_registry_compliance", "trust_explainable",
                "country_classified", "sector_classified", "no_demo_data"]:
        c = checks.get(key)
        assert c and c.get("pass") is True, f"check {key} failed: {c}"
    assert os.path.exists("/app/memory/VBIE_QA_REPORT.md"), "QA report file missing"


# ---- ADMIN LIST ----
def test_admin_list_requires_token():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/list", timeout=30)
    assert r.status_code == 401


def test_admin_list_ok():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/list",
                     headers=ADMIN_HEADERS, params={"page": 1, "limit": 25}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j["total"] >= 10000
    buyers = _items(j)
    assert len(buyers) <= 25 and len(buyers) > 0
    b = buyers[0]
    assert "admin_edited" in b
    assert "created_by" in b or "source" in b or "primary_source" in b


# ---- ADMIN EDIT persists ----
def test_admin_edit_persists(sample_geid):
    r = requests.patch(f"{BASE_URL}/api/buyers/admin/{sample_geid}",
                       headers=ADMIN_HEADERS, json={"sector": "QA Sector"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    updated = j.get("updated")
    if isinstance(updated, list):
        assert "admin_edited" in updated
    else:
        assert (updated or {}).get("admin_edited") is True
    # Verify persistence via public GET buyer endpoint
    gr = requests.get(f"{BASE_URL}/api/buyers/{sample_geid}", timeout=15)
    assert gr.status_code == 200, gr.text
    gb = gr.json()
    assert gb.get("sector") == "QA Sector", f"sector not persisted: {gb.get('sector')}"
    # And admin list first page should include the buyer with admin_edited when queried by legal_name
    lname = gb.get("legal_name") or gb.get("display_name") or ""
    if lname:
        r2 = requests.get(f"{BASE_URL}/api/buyers/admin/list",
                          headers=ADMIN_HEADERS, params={"q": lname[:20], "limit": 25}, timeout=30)
        assert r2.status_code == 200
        items = _items(r2.json())
        match = next((x for x in items if x.get("geid") == sample_geid), None)
        if match:
            assert match.get("admin_edited") is True
            assert match.get("sector") == "QA Sector"


# ---- ADMIN DELETE soft ----
def test_admin_delete_soft():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"limit": 20}, timeout=30)
    items = _items(r.json())
    geid = None
    for b in items:
        g = b.get("geid") or b.get("id")
        if g:
            geid = g
            break
    assert geid
    d = requests.delete(f"{BASE_URL}/api/buyers/admin/{geid}", headers=ADMIN_HEADERS, timeout=30)
    assert d.status_code == 200, d.text
    # confirm public 404
    g = requests.get(f"{BASE_URL}/api/buyers/{geid}", timeout=30)
    assert g.status_code == 404, f"expected 404 after delete, got {g.status_code}"


# ---- ADMIN BULK DELETE ----
def test_admin_bulk_delete_source():
    r = requests.post(f"{BASE_URL}/api/buyers/admin/delete-bulk",
                      headers=ADMIN_HEADERS,
                      json={"scope": "source", "source_id": "cid_canada"}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True


# ---- EXPORTS ----
def test_export_xlsx():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/export.xlsx",
                     headers=ADMIN_HEADERS, timeout=120)
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers.get("content-type", "").lower()
    assert len(r.content) > 10_000


def test_export_pdf():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/export.pdf",
                     headers=ADMIN_HEADERS, timeout=120)
    assert r.status_code == 200
    assert "pdf" in r.headers.get("content-type", "").lower()
    assert len(r.content) > 1000


# ---- INGEST ----
def test_ingest_status():
    r = requests.get(f"{BASE_URL}/api/buyers/ingest/status", headers=ADMIN_HEADERS, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j.get("real_buyers", 0) >= 10000
    assert "runs" in j or "history" in j or "last_run" in j


def test_ingest_run_bg():
    r = requests.post(f"{BASE_URL}/api/buyers/ingest/run",
                      headers=ADMIN_HEADERS, params={"background": "true"}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("ok") is True


# ---- NOTIFICATIONS user ----
def test_user_notifications_get():
    r = requests.get(f"{BASE_URL}/api/notifications", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "unread" in j or "unread_count" in j
    items = j.get("items") or j.get("notifications") or []
    text = " ".join(str(x) for x in items).lower()
    assert "new verified buyers" in text or "buyers added" in text, f"broadcast missing; items={items[:3]}"


def test_user_notifications_read_requires_auth():
    r = requests.post(f"{BASE_URL}/api/notifications/read", timeout=30, json={})
    assert r.status_code == 401


# ---- NOTIFICATIONS admin ----
def test_admin_notifications():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/notifications", headers=ADMIN_HEADERS, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "unread" in j or "unread_count" in j

    r2 = requests.post(f"{BASE_URL}/api/buyers/admin/notifications/read",
                       headers=ADMIN_HEADERS, timeout=30, json={})
    assert r2.status_code == 200
    assert r2.json().get("ok") is True


# ---- BUYER WARNING ----
def test_buyer_source_warning():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"limit": 5}, timeout=30)
    items = _items(r.json())
    geid = None
    for b in items:
        g = b.get("geid") or b.get("id")
        if g:
            # ensure not deleted
            gr = requests.get(f"{BASE_URL}/api/buyers/{g}", timeout=15)
            if gr.status_code == 200:
                geid = g
                break
    assert geid
    r = requests.get(f"{BASE_URL}/api/buyers/{geid}", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j.get("locked") is True
    sw = (j.get("source_warning") or "").lower()
    assert "verify" in sw or "your own risk" in sw, f"source_warning={sw}"
    assert j.get("primary_source"), j


# ---- BRAIN gating ----
def test_brain_buyer_gating_unauth():
    r = requests.post(f"{BASE_URL}/api/brain/ask",
                      json={"question": "who are the buyers importing food in Germany?"},
                      timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    ba = j.get("buyerAccess") or {}
    assert ba.get("locked") is True
    assert ba.get("subscribed") is False
    assert ba.get("count", 0) > 0
    answer = (j.get("answer") or j.get("text") or "").lower()
    # should NOT contain contact emails or phones
    import re
    assert not re.search(r"[\w\.]+@[\w\.]+", answer), "answer leaks email"
    ctas = j.get("ctas") or []
    actions = [str(c.get("action", c)).lower() for c in ctas] if isinstance(ctas, list) else []
    assert any("subscribe" in a for a in actions), f"no subscribe cta; ctas={ctas}"
