"""Iteration 35: retest of last_verified / admin_edited / GEID search fixes + regressions."""
import os, pytest, requests
from dotenv import load_dotenv
load_dotenv("/app/frontend/.env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
H = {"X-Admin-Token": "leadnation-admin-2026"}
FIXED_GEID = "LN-buyer-JTX4PXKNH69XHYAS7Y3FFPNTY2"


# ---- FIX 1: buyer detail unauth payload keys ----
class TestBuyerDetailLockedFields:
    def test_fixed_geid_has_new_keys(self):
        r = requests.get(f"{BASE}/buyers/{FIXED_GEID}", timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        blob = j.get("buyer") or j
        for k in ("last_verified", "admin_edited", "primary_source", "source_warning"):
            assert k in blob, f"missing {k}; got keys={list(blob.keys())}"
        # last_verified must look like an ISO date
        lv = blob["last_verified"]
        assert lv and isinstance(lv, str) and len(lv) >= 10, lv

    def test_searched_geid_has_new_keys(self):
        s = requests.get(f"{BASE}/buyers/search", params={"limit": 1}, timeout=30)
        geid = s.json()["buyers"][0]["geid"]
        r = requests.get(f"{BASE}/buyers/{geid}", timeout=30)
        assert r.status_code == 200
        blob = r.json().get("buyer") or r.json()
        for k in ("last_verified", "admin_edited", "primary_source", "source_warning"):
            assert k in blob, f"missing {k}"


# ---- FIX 2: admin list matches on GEID ----
class TestAdminListGeidSearch:
    def test_admin_list_q_by_geid(self):
        r = requests.get(f"{BASE}/buyers/admin/list", params={"q": FIXED_GEID}, headers=H, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("total", 0) >= 1, j
        rows = j.get("buyers") or j.get("rows") or j.get("items") or []
        assert any((row.get("geid") == FIXED_GEID) for row in rows), rows[:2]
        # admin_edited flag should be present in row shape
        assert "admin_edited" in rows[0], list(rows[0].keys())


# ---- Regressions ----
class TestRegressions:
    def test_production_audit(self):
        r = requests.post(f"{BASE}/buyers/admin/production-audit?auto_fix=true", headers=H, timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("production_ready") is True
        assert d.get("active_production_buyers") == 10719, d.get("active_production_buyers")
        assert d.get("quarantined_total") == 3, d.get("quarantined_total")

    def test_meta_total(self):
        r = requests.get(f"{BASE}/buyers/meta", timeout=30)
        assert r.status_code == 200
        assert r.json().get("total") == 10719

    def test_analytics_json(self):
        r = requests.get(f"{BASE}/buyers/admin/analytics", headers=H, timeout=60)
        assert r.status_code == 200
        j = r.json()
        for k in ("today_buyers", "this_week", "this_month", "total_active",
                  "new_countries", "new_industries", "top_products",
                  "top_corridors", "top_sources", "top_sectors", "top_countries"):
            assert k in j, f"missing {k}"

    def test_analytics_xlsx(self):
        r = requests.get(f"{BASE}/buyers/admin/analytics.xlsx", headers=H, timeout=60)
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("content-type", "")

    def test_export_xlsx(self):
        r = requests.get(f"{BASE}/buyers/admin/export.xlsx", headers=H, timeout=120)
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("content-type", "")

    def test_export_pdf(self):
        r = requests.get(f"{BASE}/buyers/admin/export.pdf", headers=H, timeout=120)
        assert r.status_code == 200
        assert "pdf" in r.headers.get("content-type", "")
