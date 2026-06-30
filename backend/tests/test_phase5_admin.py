"""Phase 5 backend tests: Admin auth, CMS CRUD, leads CSV, services, service-requests,
directories, global-search, track/events."""
import os
import io
import csv as csv_mod
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_TOKEN = "leadnation-admin-2026"
HDR = {"X-Admin-Token": ADMIN_TOKEN}


# ---------- Admin Login ----------
class TestAdminLogin:
    def test_login_success(self):
        r = requests.post(f"{API}/admin/login", json={"token": ADMIN_TOKEN}, timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body.get("ok") is True

    def test_login_wrong_token(self):
        r = requests.post(f"{API}/admin/login", json={"token": "wrong"}, timeout=20)
        assert r.status_code == 401


# ---------- Admin Collections ----------
class TestAdminCollections:
    def test_list_collections_requires_auth(self):
        r = requests.get(f"{API}/admin/collections", timeout=20)
        assert r.status_code == 401

    def test_list_collections_with_token(self):
        r = requests.get(f"{API}/admin/collections", headers=HDR, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        names = {x["name"]: x["count"] for x in data}
        # Required collections
        for needed in ["countries", "products", "corridors", "hsn_codes", "industries", "blog", "leads", "service_requests"]:
            assert needed in names, f"missing collection {needed}"
        # Expected mock counts (from review_request)
        assert names["countries"] == 5
        assert names["products"] == 5
        assert names["corridors"] == 4
        assert names["hsn_codes"] == 5
        assert names["industries"] == 8
        assert names["blog"] == 6


# ---------- CMS CRUD ----------
class TestCmsCrud:
    created_id = None

    def test_get_products(self):
        r = requests.get(f"{API}/admin/collection/products", headers=HDR, timeout=20)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 5

    def test_unknown_collection_404(self):
        r = requests.get(f"{API}/admin/collection/unknown_xyz", headers=HDR, timeout=20)
        assert r.status_code == 404

    def test_crud_lifecycle(self):
        # CREATE
        payload = {"name": "TEST_Phase5_Product", "slug": "test-phase5-product", "category": "Test", "hsn": "99999999"}
        r = requests.post(f"{API}/admin/collection/products", json=payload, headers=HDR, timeout=20)
        assert r.status_code == 200, r.text
        created = r.json()
        assert "id" in created
        item_id = created["id"]
        assert created["name"] == payload["name"]

        # READ via list
        r = requests.get(f"{API}/admin/collection/products", headers=HDR, timeout=20)
        assert any(i.get("id") == item_id for i in r.json())

        # UPDATE
        r = requests.put(f"{API}/admin/collection/products/{item_id}", json={"name": "TEST_Phase5_Product_Updated"},
                         headers=HDR, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("name") == "TEST_Phase5_Product_Updated"

        # DELETE
        r = requests.delete(f"{API}/admin/collection/products/{item_id}", headers=HDR, timeout=20)
        assert r.status_code == 200, r.text

        # Verify gone
        r = requests.get(f"{API}/admin/collection/products", headers=HDR, timeout=20)
        assert not any(i.get("id") == item_id for i in r.json())


# ---------- Leads ----------
class TestLeads:
    def test_leads_list_requires_auth(self):
        r = requests.get(f"{API}/admin/leads", timeout=20)
        assert r.status_code == 401

    def test_leads_list(self):
        r = requests.get(f"{API}/admin/leads", headers=HDR, timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_leads_csv(self):
        r = requests.get(f"{API}/admin/leads.csv", params={"token": ADMIN_TOKEN}, timeout=20)
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert "leads.csv" in cd
        # Confirm CSV parseable
        reader = csv_mod.reader(io.StringIO(r.text))
        rows = list(reader)
        assert len(rows) >= 1  # at least header

    def test_leads_csv_wrong_token(self):
        r = requests.get(f"{API}/admin/leads.csv", params={"token": "bad"}, timeout=20)
        assert r.status_code in (401, 403)


# ---------- Services ----------
class TestServices:
    def test_list_services(self):
        r = requests.get(f"{API}/services", timeout=20)
        assert r.status_code == 200
        services = r.json()
        assert isinstance(services, list)
        assert len(services) == 10, f"expected 10 services, got {len(services)}"
        cats = {s.get("category") for s in services}
        assert "Govt Documentation" in cats
        assert "Consulting" in cats

    def test_service_detail(self):
        r = requests.get(f"{API}/service/iec-registration", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data.get("slug") == "iec-registration"

    def test_service_unknown(self):
        r = requests.get(f"{API}/service/unknown-xyz", timeout=20)
        assert r.status_code == 404


# ---------- Service Requests ----------
class TestServiceRequests:
    def test_create_service_request_creates_lead(self):
        # baseline lead count
        r0 = requests.get(f"{API}/admin/leads", headers=HDR, timeout=20)
        before = len(r0.json())

        payload = {"service": "iec-registration", "name": "TEST_Phase5_SR", "email": "test_phase5_sr@example.com",
                   "phone": "9999999999", "message": "Need IEC", "company": "Acme", "country": "India"}
        r = requests.post(f"{API}/service-request", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        req_id = body.get("id")
        assert req_id

        # Visible in admin/service-requests
        r = requests.get(f"{API}/admin/service-requests", headers=HDR, timeout=20)
        assert r.status_code == 200
        srs = r.json()
        assert any(s.get("id") == req_id for s in srs)
        match = next(s for s in srs if s.get("id") == req_id)
        assert match.get("service") == "iec-registration"
        assert match.get("status") == "new"

        # Lead also created with source service:iec-registration
        r = requests.get(f"{API}/admin/leads", headers=HDR, timeout=20)
        assert any(l.get("source") == "service:iec-registration" and l.get("email") == "test_phase5_sr@example.com"
                   for l in r.json())
        assert len(r.json()) >= before + 1

        # Update status / assign CA
        r = requests.put(f"{API}/admin/service-requests/{req_id}",
                         json={"status": "assigned", "assignedCa": "CA Sharma"}, headers=HDR, timeout=20)
        assert r.status_code == 200, r.text
        updated = r.json()
        assert updated.get("status") == "assigned"
        assert updated.get("assignedCa") == "CA Sharma"

    def test_admin_service_requests_requires_auth(self):
        r = requests.get(f"{API}/admin/service-requests", timeout=20)
        assert r.status_code == 401


# ---------- Directories ----------
class TestDirectory:
    @pytest.mark.parametrize("kind", ["exporters", "importers", "suppliers", "cha", "export-agents"])
    def test_directory_returns_items(self, kind):
        r = requests.get(f"{API}/directory/{kind}", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data.get("items"), list) and len(data["items"]) > 0
        assert data.get("lockedExtras") is True

    def test_exporters_count(self):
        r = requests.get(f"{API}/directory/exporters", timeout=20)
        assert len(r.json()["items"]) == 6

    def test_directory_unknown(self):
        r = requests.get(f"{API}/directory/unknown-kind", timeout=20)
        assert r.status_code == 404

    def test_directory_filter_country(self):
        r = requests.get(f"{API}/directory/importers", params={"country": "AE"}, timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        assert all(i["country"] == "AE" for i in items)

    def test_directory_search_q(self):
        r = requests.get(f"{API}/directory/exporters", params={"q": "rice"}, timeout=20)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1


# ---------- Global Search ----------
class TestGlobalSearch:
    def test_rice(self):
        r = requests.get(f"{API}/global-search", params={"q": "rice"}, timeout=20)
        assert r.status_code == 200
        results = r.json().get("results", [])
        assert len(results) > 0
        types = {x["type"] for x in results}
        # Should include at least product/blog/hsn related to rice
        assert types & {"product", "hsn", "blog"}

    def test_iec(self):
        r = requests.get(f"{API}/global-search", params={"q": "iec"}, timeout=20)
        assert r.status_code == 200
        results = r.json().get("results", [])
        assert any(x["type"] == "service" for x in results)

    def test_india(self):
        r = requests.get(f"{API}/global-search", params={"q": "india"}, timeout=20)
        assert r.status_code == 200
        results = r.json().get("results", [])
        assert any(x["type"] == "country" for x in results)


# ---------- Track / Events ----------
class TestTrack:
    def test_track_and_admin_events(self):
        r0 = requests.get(f"{API}/admin/events", headers=HDR, timeout=20)
        assert r0.status_code == 200
        before = len(r0.json())

        r = requests.post(f"{API}/track", json={"name": "test_event_phase5", "path": "/x", "meta": {"x": 1}}, timeout=20)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        r = requests.get(f"{API}/admin/events", headers=HDR, timeout=20)
        assert r.status_code == 200
        events = r.json()
        assert len(events) >= before + 1
        assert any(e.get("name") == "test_event_phase5" for e in events)

    def test_admin_events_requires_auth(self):
        r = requests.get(f"{API}/admin/events", timeout=20)
        assert r.status_code == 401
