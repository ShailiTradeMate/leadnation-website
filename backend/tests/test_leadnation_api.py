"""LeadNation backend API tests"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
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


# ---------- PHASE 3 & 4 ----------

class TestHsnFinder:
    def test_hsn_finder_rice(self, client):
        r = client.post(f"{API}/hsn-finder", json={"productName": "rice", "description": "long grain", "category": "Agriculture & Food"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["results"], list) and len(d["results"]) >= 1
        assert all("code" in x and "matchScore" in x for x in d["results"])
        # rice should match basmati
        assert any("Basmati" in x["title"] for x in d["results"])

    def test_hsn_finder_fallback(self, client):
        r = client.post(f"{API}/hsn-finder", json={"productName": "zzzunmatchable123"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d["results"]) >= 1


class TestLandedCost:
    def test_landed_cost(self, client):
        payload = {"productCost": 1000, "freight": 200, "insurance": 50, "duty": 100, "localCharges": 50, "currency": "USD"}
        r = client.post(f"{API}/landed-cost", json=payload, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 1400.0
        assert len(d["breakdown"]) == 5
        # shares should sum to ~100
        s = sum(b["share"] for b in d["breakdown"])
        assert 99 <= s <= 101


class TestExportIncentive:
    def test_export_incentive(self, client):
        r = client.post(f"{API}/export-incentive", json={"product": "Basmati Rice", "destination": "AE"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["rodtep"]["eligible"] is True
        assert d["dutyDrawback"]["eligible"] is True
        assert isinstance(d["incentives"], list) and len(d["incentives"]) >= 1
        assert isinstance(d["govBenefits"], list) and len(d["govBenefits"]) >= 1


class TestProductResearch:
    def test_product_research(self, client):
        r = client.post(f"{API}/product-research", json={"product": "Basmati Rice", "hsnCode": "10063020"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "demandOverview" in d
        assert len(d["topImporting"]) == 5
        assert len(d["topExporting"]) == 5
        assert len(d["trends"]) == 3
        assert "opportunity" in d


class TestFindBuyers:
    def test_find_buyers_all(self, client):
        r = client.post(f"{API}/find-buyers", json={"product": "Basmati Rice"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["buyers"], list) and len(d["buyers"]) >= 1
        assert d["lockedExtras"] is True
        for b in d["buyers"]:
            assert {"company", "country", "city", "volume", "fit"} <= set(b.keys())
        assert "marketPotential" in d

    def test_find_buyers_filter(self, client):
        r = client.post(f"{API}/find-buyers", json={"product": "Rice", "country": "AE"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        # all returned should be AE
        assert all(b["country"] == "AE" for b in d["buyers"])


class TestExportReadiness:
    def test_all_true_100(self, client):
        r = client.post(f"{API}/export-readiness", json={"iec": True, "gst": True, "website": True, "packagingReady": True, "certifications": True, "experience": True}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 100
        assert d["band"] == "Export-ready"

    def test_all_false_0(self, client):
        r = client.post(f"{API}/export-readiness", json={}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 0
        assert isinstance(d["recommendations"], list) and len(d["recommendations"]) >= 1

    def test_lead_captured(self, client):
        r = client.post(f"{API}/export-readiness", json={"iec": True, "name": "TEST_Readiness", "email": "test_readiness@example.com", "phone": "+919999999999"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["leadCaptured"] is True


class TestAiAsk:
    def test_ai_documents(self, client):
        r = client.post(f"{API}/ai-ask", json={"question": "What documents do I need?"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["isMock"] is True
        assert "Commercial Invoice" in d["answer"] or "Packing List" in d["answer"]
        assert isinstance(d["suggestedTools"], list) and len(d["suggestedTools"]) >= 1

    def test_ai_fallback(self, client):
        r = client.post(f"{API}/ai-ask", json={"question": "tell me a joke"}, timeout=20)
        assert r.status_code == 200
        assert r.json()["isMock"] is True


class TestProductsCatalog:
    def test_list(self, client):
        r = client.get(f"{API}/products-catalog", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list) and len(d) == 5
        for p in d:
            assert {"slug", "name", "hsn", "image", "category"} <= set(p.keys())

    def test_detail_basmati(self, client):
        r = client.get(f"{API}/product/basmati-rice", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["overview", "topExporters", "topImporters", "demand", "opportunities", "compliance", "certifications", "logistics", "relatedCorridors"]:
            assert k in d

    def test_unknown(self, client):
        r = client.get(f"{API}/product/unknown-xyz", timeout=20)
        assert r.status_code == 404


class TestCorridors:
    def test_list(self, client):
        r = client.get(f"{API}/corridors", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list) and len(d) == 4

    def test_detail_uae(self, client):
        r = client.get(f"{API}/corridor/india-to-uae", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["exportProcess", "importProcess", "customsInfo", "documents", "dutiesTaxes", "opportunities", "popularProducts", "logistics"]:
            assert k in d

    def test_unknown(self, client):
        r = client.get(f"{API}/corridor/unknown-xyz", timeout=20)
        assert r.status_code == 404


class TestHsn:
    def test_list(self, client):
        r = client.get(f"{API}/hsn", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list) and len(d) == 5

    def test_detail(self, client):
        r = client.get(f"{API}/hsn/10063020", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["code"] == "10063020"
        assert "Basmati" in d["title"]

    def test_unknown(self, client):
        r = client.get(f"{API}/hsn/00000000", timeout=20)
        assert r.status_code == 404


class TestIndustries:
    def test_list(self, client):
        r = client.get(f"{API}/industries", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d) == 8

    def test_detail(self, client):
        r = client.get(f"{API}/industry/agriculture", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ["overview", "exports", "topMarkets", "compliance"]:
            assert k in d

    def test_unknown(self, client):
        r = client.get(f"{API}/industry/unknown-xyz", timeout=20)
        assert r.status_code == 404


class TestBlog:
    def test_list(self, client):
        r = client.get(f"{API}/blog", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d) == 6

    def test_detail(self, client):
        r = client.get(f"{API}/blog/complete-guide-to-iec-code-india", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "body" in d and isinstance(d["body"], list) and len(d["body"]) > 0


class TestSuppliers:
    def test_list(self, client):
        r = client.get(f"{API}/suppliers", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "suppliers" in d and d["lockedExtras"] is True
        assert isinstance(d["suppliers"], list) and len(d["suppliers"]) >= 1

    def test_filter_country(self, client):
        r = client.get(f"{API}/suppliers", params={"country": "IN"}, timeout=20)
        assert r.status_code == 200

    def test_filter_q(self, client):
        r = client.get(f"{API}/suppliers", params={"q": "KRBL"}, timeout=20)
        assert r.status_code == 200
        assert any("KRBL" in s["company"] for s in r.json()["suppliers"])


class TestMarketplace:
    def test_marketplace(self, client):
        r = client.get(f"{API}/marketplace", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d["listings"]) == 6
        assert len(d["reels"]) == 4
        assert len(d["buyerRequests"]) == 3


class TestNetwork:
    def test_network(self, client):
        r = client.get(f"{API}/network", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert len(d["members"]) == 6
        assert len(d["stats"]) == 4


class TestSitemap:
    def test_sitemap(self, client):
        r = client.get(f"{BASE_URL}/sitemap.xml", timeout=20)
        assert r.status_code == 200
        text = r.text
        # check key new paths
        for path in ["/tools", "/ai-assistant", "/products", "/corridors", "/hsn/", "/industries", "/blog", "/suppliers", "/marketplace", "/network"]:
            assert path in text, f"sitemap missing {path}"
