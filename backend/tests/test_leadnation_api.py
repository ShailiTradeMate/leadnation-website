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



# ---------- PHASE 2 ----------

# Duty Calculator
class TestDutyCalculator:
    def test_duty_calc_in_ae_agri(self, client):
        payload = {"exportCountry": "IN", "importCountry": "AE", "category": "Agriculture & Food", "value": 10000, "currency": "USD"}
        r = client.post(f"{API}/duty-calc", json=payload, timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["estimatedDuty", "estimatedTaxes", "estimatedHandling", "estimatedLandedCost", "ftaApplied", "dutyRate", "vatRate"]:
            assert k in d, f"missing key {k}"
        assert d["ftaApplied"] is True, "IN->AE should be preferential"
        # Agriculture 0.06 + (-0.04) = 0.02 -> 2%
        assert d["dutyRate"] == 2.0
        assert d["vatRate"] == 5.0  # AE VAT
        assert d["estimatedDuty"] == 200.0
        # taxes = (10000 + 200) * 0.05 = 510
        assert d["estimatedTaxes"] == 510.0
        assert d["estimatedHandling"] == 50.0
        assert d["estimatedLandedCost"] == 10760.0

    def test_duty_calc_electronics_rate(self, client):
        r = client.post(f"{API}/duty-calc", json={"exportCountry": "CN", "importCountry": "US", "category": "Electronics", "value": 5000}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["dutyRate"] == 5.0
        assert d["ftaApplied"] is False

    def test_duty_calc_pharma_rate(self, client):
        r = client.post(f"{API}/duty-calc", json={"exportCountry": "IN", "importCountry": "US", "category": "Pharmaceuticals", "value": 1000}, timeout=20)
        assert r.status_code == 200
        assert r.json()["dutyRate"] == 3.0

    def test_duty_calc_autos_rate(self, client):
        r = client.post(f"{API}/duty-calc", json={"exportCountry": "DE", "importCountry": "IN", "category": "Automobiles & Parts", "value": 20000}, timeout=20)
        assert r.status_code == 200
        assert r.json()["dutyRate"] == 15.0


# Country Profiles
class TestCountryProfiles:
    def test_list_country_profiles(self, client):
        r = client.get(f"{API}/country-profiles", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 5
        slugs = sorted(d["slug"] for d in data)
        assert slugs == sorted(["india", "uae", "usa", "australia", "armenia"])
        for d in data:
            assert {"slug", "code", "name", "flag", "tagline"} <= set(d.keys())

    @pytest.mark.parametrize("slug", ["india", "uae", "usa", "australia", "armenia"])
    def test_country_profile_detail(self, client, slug):
        r = client.get(f"{API}/country/{slug}", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["overview", "majorImports", "majorExports", "opportunities", "customs", "compliance", "marketplace"]:
            assert k in d, f"missing {k}"
        assert isinstance(d["majorExports"], list) and len(d["majorExports"]) > 0
        assert isinstance(d["majorImports"], list) and len(d["majorImports"]) > 0
        assert isinstance(d["opportunities"], list) and len(d["opportunities"]) > 0
        assert isinstance(d["marketplace"], list) and len(d["marketplace"]) > 0
        assert isinstance(d["customs"], dict)
        assert d["overview"]

    def test_country_profile_unknown(self, client):
        r = client.get(f"{API}/country/unknown", timeout=20)
        assert r.status_code == 404


# Academy
class TestAcademy:
    def test_academy(self, client):
        r = client.get(f"{API}/academy", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for level in ["Beginner", "Intermediate", "Advanced"]:
            assert level in d
            assert isinstance(d[level], list) and len(d[level]) >= 3
            for c in d[level]:
                assert {"title", "slug", "duration", "lessons", "summary", "image"} <= set(c.keys())


# Intelligence
class TestIntelligence:
    def test_intelligence(self, client):
        r = client.get(f"{API}/intelligence", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "commodities" in d and len(d["commodities"]) == 6
        assert "currencies" in d and len(d["currencies"]) == 8
        assert "trends" in d and len(d["trends"]) == 6
        assert "updatedAt" in d
        for c in d["commodities"]:
            assert {"name", "price", "change"} <= set(c.keys())
        for c in d["currencies"]:
            assert {"pair", "rate", "change"} <= set(c.keys())
        for t in d["trends"]:
            assert {"title", "impact"} <= set(t.keys())
