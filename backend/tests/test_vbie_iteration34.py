"""Iteration 34: Production Readiness Audit + Quarantine + Analytics."""
import os, pathlib, pytest, requests
from dotenv import load_dotenv
load_dotenv("/app/frontend/.env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
TOKEN = "leadnation-admin-2026"
H = {"X-Admin-Token": TOKEN}


# ---------- Production audit ----------
class TestProductionAudit:
    def test_audit_requires_token(self):
        # retry once for transient 502
        for _ in range(2):
            r = requests.post(f"{BASE}/buyers/admin/production-audit?auto_fix=true", timeout=60)
            if r.status_code != 502:
                break
        assert r.status_code == 401

    def test_audit_runs_and_writes_report(self):
        r = requests.post(f"{BASE}/buyers/admin/production-audit?auto_fix=true", headers=H, timeout=180)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("production_ready") is True, data
        assert data.get("active_production_buyers", 0) > 10000
        assert "quarantined_total" in data
        assert "quarantine_reasons" in data
        # compliant_sources allowlist
        compliant = data.get("compliant_sources") or []
        for s in ("eu_ted", "cid_canada", "sam_gov", "uk_companies_house"):
            assert s in compliant, f"missing compliant source {s}: {compliant}"
        # shared_apis note
        blob = str(data).lower()
        assert "shared" in blob or "same" in blob
        # Report file present
        assert pathlib.Path("/app/memory/VBIE_PRODUCTION_AUDIT.md").exists()
        # Save active count for other tests
        pytest.active_count = data["active_production_buyers"]
        pytest.quarantined_total = data["quarantined_total"]


# ---------- Quarantine effect on public endpoints ----------
class TestQuarantineExcluded:
    def test_meta_equals_active(self):
        r = requests.get(f"{BASE}/buyers/meta", timeout=30)
        assert r.status_code == 200
        total = r.json().get("total")
        assert total == getattr(pytest, "active_count", total), (
            f"public meta total {total} != active {getattr(pytest,'active_count',None)}"
        )

    def test_search_has_no_placeholders(self):
        r = requests.get(f"{BASE}/buyers/search", params={"limit": 200}, timeout=30)
        assert r.status_code == 200
        items = r.json().get("buyers", [])
        assert items
        bad = {"n/a", "test_test", ".", "", "null", "none"}
        for it in items:
            name = (it.get("legal_name") or "").strip().lower()
            assert name not in bad, f"junk name leaked: {name!r}"


# ---------- QA audit still passes ----------
class TestQAAudit:
    def test_qa_pass(self):
        r = requests.get(f"{BASE}/buyers/admin/qa", headers=H, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert data.get("overall_pass") is True, data
        # No sample records leaked
        assert "sample_records" not in data or not data.get("sample_records")


# ---------- Buyer detail includes last_verified ----------
class TestLastVerified:
    def test_buyer_detail_fields(self):
        # pick a geid
        r = requests.get(f"{BASE}/buyers/search", params={"limit": 1}, timeout=30)
        geid = r.json()["buyers"][0]["geid"]
        d = requests.get(f"{BASE}/buyers/{geid}", timeout=30)
        assert d.status_code == 200, d.text
        j = d.json()
        # unauth returns locked payload; verify the required keys exist somewhere
        blob = j.get("buyer") or j
        for key in ("last_verified", "primary_source", "source_warning"):
            assert key in blob or key in j, f"missing {key} in {list(blob.keys())} / {list(j.keys())}"


# ---------- Analytics ----------
class TestAnalytics:
    def test_analytics_requires_token(self):
        r = requests.get(f"{BASE}/buyers/admin/analytics", timeout=30)
        assert r.status_code == 401

    def test_analytics_json(self):
        r = requests.get(f"{BASE}/buyers/admin/analytics", headers=H, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        for k in ("today_buyers", "this_week", "this_month", "total_active",
                  "new_countries", "new_industries", "top_products",
                  "top_corridors", "top_sources", "top_sectors", "top_countries"):
            assert k in j, f"missing key {k}"
        assert isinstance(j["new_countries"], list)
        assert isinstance(j["new_industries"], list)
        assert j["total_active"] > 10000
        # top_sources non-empty
        assert j["top_sources"], "top_sources empty"

    def test_analytics_xlsx(self):
        r = requests.get(f"{BASE}/buyers/admin/analytics.xlsx", headers=H, timeout=60)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "spreadsheet" in ct or "excel" in ct, ct
        assert len(r.content) > 2000


# ---------- Exports still work ----------
class TestExports:
    def test_export_xlsx(self):
        r = requests.get(f"{BASE}/buyers/admin/export.xlsx", headers=H, timeout=120)
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("content-type", "")
        assert len(r.content) > 5000

    def test_export_pdf(self):
        r = requests.get(f"{BASE}/buyers/admin/export.pdf", headers=H, timeout=120)
        assert r.status_code == 200
        assert "pdf" in r.headers.get("content-type", "")
        assert len(r.content) > 2000


# ---------- Admin edit/delete persistence ----------
class TestAdminEditDelete:
    def test_patch_sets_admin_edited(self):
        r = requests.get(f"{BASE}/buyers/search", params={"limit": 5}, timeout=30)
        geid = r.json()["buyers"][2]["geid"]
        p = requests.patch(f"{BASE}/buyers/admin/{geid}", headers=H,
                           json={"sector": "TEST_Iter34_Sector"}, timeout=30)
        assert p.status_code == 200, p.text
        g = requests.get(f"{BASE}/buyers/{geid}", timeout=30).json()
        blob = g.get("buyer") or g
        assert blob.get("admin_edited") is True
        assert blob.get("sector") == "TEST_Iter34_Sector"

    def test_delete_soft_deletes(self):
        r = requests.get(f"{BASE}/buyers/search", params={"limit": 10}, timeout=30)
        geid = r.json()["buyers"][7]["geid"]
        d = requests.delete(f"{BASE}/buyers/admin/{geid}", headers=H, timeout=30)
        assert d.status_code in (200, 204)
        g = requests.get(f"{BASE}/buyers/{geid}", timeout=30)
        assert g.status_code == 404
