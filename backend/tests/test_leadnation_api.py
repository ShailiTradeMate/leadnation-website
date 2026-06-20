"""LeadNation backend API tests"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://nation-deploy.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# Reference data
class TestReference:
    def test_countries(self, client):
        r = client.get(f"{API}/countries", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 10
        assert all({"code", "name", "flag"} <= set(d.keys()) for d in data)
        codes = [d["code"] for d in data]
        assert "IN" in codes

    def test_business_types(self, client):
        r = client.get(f"{API}/business-types", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and "Manufacturer" in data

    def test_trade_directions(self, client):
        r = client.get(f"{API}/trade-directions", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "Import" in data and "Export" in data

    def test_products(self, client):
        r = client.get(f"{API}/products", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 10
        assert "Basmati Rice" in data


# Trade news
class TestTradeNews:
    def test_trade_news(self, client):
        r = client.get(f"{API}/trade-news", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 6
        for item in data:
            assert {"id", "title", "image", "date", "source"} <= set(item.keys())


# Expos
class TestExpos:
    def test_expos(self, client):
        r = client.get(f"{API}/expos", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 8
        for item in data:
            assert {"name", "city", "date", "category", "attendees", "image"} <= set(item.keys())


# Customs Compliance
class TestCustoms:
    def test_customs_compliance(self, client):
        r = client.get(f"{API}/customs-compliance", params={"country": "IN", "direction": "Import"}, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["country"] == "IN"
        assert data["direction"] == "Import"
        assert "dutyRate" in data
        assert isinstance(data["documents"], list) and len(data["documents"]) > 0
        assert isinstance(data["incoterms"], list) and len(data["incoterms"]) > 0
        assert "tip" in data

    def test_customs_export_uae(self, client):
        r = client.get(f"{API}/customs-compliance", params={"country": "AE", "direction": "Export"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["direction"] == "Export"
        assert "0%" in d["dutyRate"]


# Product Info
class TestProductInfo:
    def test_product_info(self, client):
        payload = {"country": "India", "businessType": "Manufacturer", "direction": "Export", "product": "Basmati Rice"}
        r = client.post(f"{API}/product-info", json=payload, timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["marketSize", "yoyGrowth", "topMarkets", "topSuppliers", "certifications", "insights"]:
            assert k in d
        assert isinstance(d["topMarkets"], list)
        assert d["product"] == "Basmati Rice"


# Search
class TestSearch:
    def test_search_ind(self, client):
        r = client.get(f"{API}/search", params={"q": "ind"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "results" in d
        assert isinstance(d["results"], list)
        labels = [x["label"].lower() for x in d["results"]]
        assert any("india" in lbl for lbl in labels)

    def test_search_basm(self, client):
        r = client.get(f"{API}/search", params={"q": "basm"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert any("basmati" in x["label"].lower() for x in d["results"])

    def test_search_empty(self, client):
        r = client.get(f"{API}/search", params={"q": ""}, timeout=20)
        assert r.status_code == 200


# Leads
class TestLeads:
    def test_create_lead(self, client):
        payload = {
            "name": "TEST_LeadNation User",
            "email": "test_leadnation@example.com",
            "phone": "+919999999999",
            "country": "India",
            "message": "Interested in export consultation",
        }
        r = client.post(f"{API}/leads", json=payload, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert isinstance(d.get("id"), str) and len(d["id"]) > 0

    def test_create_lead_invalid_email(self, client):
        r = client.post(f"{API}/leads", json={"name": "X", "email": "not-an-email"}, timeout=20)
        assert r.status_code in (400, 422)


# India features
class TestIndiaFeatures:
    def test_india_features(self, client):
        r = client.get(f"{API}/india-features", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list) and len(d) == 6
        for item in d:
            assert {"title", "description", "icon"} <= set(item.keys())
