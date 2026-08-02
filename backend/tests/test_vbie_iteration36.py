"""Iteration 36 regression tests — verify vbie_core extraction (circular import fix)
did NOT change any observable behavior. Covers full VBIE surface + brain buyer path."""
import os
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-preview.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"
ADMIN = {"X-Admin-Token": "leadnation-admin-2026"}


# --- Public buyers endpoints ---
def test_buyers_meta_total_10719():
    r = requests.get(f"{API}/buyers/meta", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("total") == 10719, d
    assert "country" in (d.get("facets") or {}) or "countries" in d
    assert "sector" in (d.get("facets") or {}) or "sectors" in d


def test_buyers_search_filters_and_pagination():
    r = requests.get(f"{API}/buyers/search", params={"country": "DE", "sector": "food", "page": 1, "page_size": 5}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    items = d.get("items") or d.get("buyers")
    assert isinstance(items, list)
    assert d.get("page") == 1
    # trust_min + q
    r2 = requests.get(f"{API}/buyers/search", params={"trust_min": 50, "q": "gmbh", "page_size": 3}, timeout=30)
    assert r2.status_code == 200


def test_buyer_detail_unauth_locked_teaser():
    s = requests.get(f"{API}/buyers/search", params={"page_size": 1}, timeout=30).json()
    items = s.get("items") or s.get("buyers")
    geid = items[0]["geid"]
    r = requests.get(f"{API}/buyers/{geid}", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("locked") is True or d.get("access", {}).get("locked") is True
    assert "last_verified" in d
    assert "primary_source" in d
    assert "source_warning" in d
    # evidence 402 for unauth
    ev = requests.get(f"{API}/buyers/{geid}/evidence", timeout=30)
    assert ev.status_code == 402, ev.text


def test_buyers_sources_registry():
    r = requests.get(f"{API}/buyers/sources", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "sources" in d
    assert "sanctions_screening" in d or "sanctions" in d
    assert "last_ingestion" in d


# --- Admin endpoints require token ---
def test_admin_endpoints_401_without_token():
    # GET endpoints
    for path in ["/buyers/admin/qa", "/buyers/admin/list", "/buyers/admin/analytics"]:
        r = requests.get(f"{API}{path}", timeout=30)
        assert r.status_code in (401, 403), f"{path} => {r.status_code}"
    # POST production-audit without token
    r = requests.post(f"{API}/buyers/admin/production-audit", timeout=30)
    assert r.status_code in (401, 403), f"production-audit => {r.status_code}"


def test_admin_qa_pass():
    r = requests.get(f"{API}/buyers/admin/qa", headers=ADMIN, timeout=60)
    assert r.status_code == 200, r.text
    assert r.json().get("overall_pass") is True


def test_admin_production_audit():
    r = requests.post(f"{API}/buyers/admin/production-audit", params={"auto_fix": "true"}, headers=ADMIN, timeout=120)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("production_ready") is True, d
    active = d.get("active_production_buyers")
    quar = d.get("quarantined_total")
    assert active == 10719, f"active={active}"
    assert quar == 3, f"quarantined={quar}"


def test_admin_list_and_analytics():
    r = requests.get(f"{API}/buyers/admin/list", headers=ADMIN, params={"page_size": 5}, timeout=30)
    assert r.status_code == 200
    r2 = requests.get(f"{API}/buyers/admin/analytics", headers=ADMIN, timeout=30)
    assert r2.status_code == 200
    d = r2.json()
    assert d and isinstance(d, dict) and len(d) > 0


def test_admin_exports():
    for path in ["/buyers/admin/export.xlsx", "/buyers/admin/export.pdf", "/buyers/admin/analytics.xlsx"]:
        r = requests.get(f"{API}{path}", headers=ADMIN, timeout=60)
        assert r.status_code == 200, f"{path} => {r.status_code}"
        assert len(r.content) > 100


def test_ingest_status():
    # ingest/status is public (mounted at /api/buyers/ingest/status)
    r = requests.get(f"{API}/buyers/ingest/status", headers=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    # look for any count field >= 10719
    def _find_num(obj):
        found = []
        if isinstance(obj, dict):
            for v in obj.values():
                found += _find_num(v)
        elif isinstance(obj, list):
            for v in obj: found += _find_num(v)
        elif isinstance(obj, (int, float)):
            found.append(obj)
        return found
    nums = _find_num(d)
    assert any(n >= 10719 for n in nums), d


# --- Brain buyer path (unauth) ---
def test_brain_ask_buyers_locked_teaser():
    r = requests.post(f"{API}/brain/ask",
                      json={"question": "who are the buyers importing food in Germany?"},
                      timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    ba = d.get("buyerAccess") or {}
    assert ba.get("locked") is True, d
    # teaser answer + some subscribe/cta indicator
    txt = str(d).lower()
    assert "subscribe" in txt or "cta" in txt or "upgrade" in txt or "plan" in txt
