"""Iteration 70 - Tools rewire: duty countries, hsn-finder, hsn detail, next-steps, removed mocks."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://leadnation-build.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


# --- Duty Countries ---
class TestDutyCountries:
    def test_countries_list(self):
        r = requests.get(f"{API}/duty/countries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        countries = data.get('countries') or data if isinstance(data, list) else data.get('countries', [])
        assert isinstance(countries, list)
        assert len(countries) == 56, f"expected 56, got {len(countries)}"
        by_code = {c['code']: c for c in countries}
        assert '356' in by_code and by_code['356']['iso2'].upper() == 'IN'
        assert '276' in by_code and by_code['276']['iso2'].upper() == 'DE'
        assert '784' in by_code and by_code['784']['iso2'].upper() == 'AE'
        # Required fields
        for c in countries[:5]:
            for k in ('code', 'iso2', 'name', 'flag', 'currency'):
                assert k in c, f"missing {k} in {c}"


# --- HSN Finder ---
class TestHsnFinder:
    def test_agarbatti(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "agarbatti"}, timeout=45)
        assert r.status_code == 200
        results = r.json().get('results', [])
        assert len(results) >= 1
        assert results[0]['code'] == '330741'
        top = results[0]
        assert 'rodtep' in top and 'rate' in top['rodtep']
        assert 'igstSlab' in top or 'gst' in top
        assert 'sectionName' in top or 'section' in top

    def test_basmati_rice(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "basmati rice"}, timeout=45)
        assert r.status_code == 200
        results = r.json().get('results', [])
        assert len(results) >= 1
        assert results[0]['code'] == '100630'

    def test_turmeric_with_destination(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "turmeric", "destination": "784"}, timeout=60)
        assert r.status_code == 200
        results = r.json().get('results', [])
        assert len(results) >= 1
        top = results[0]
        imp = top.get('importDuty') or {}
        assert isinstance(imp.get('rate'), (int, float)), f"importDuty.rate missing: {imp}"
        assert imp.get('year')
        assert imp.get('destination') == 'United Arab Emirates'

    def test_hs6_direct(self):
        r = requests.post(f"{API}/hsn-finder", json={"hs6": "091030"}, timeout=30)
        assert r.status_code == 200
        results = r.json().get('results', [])
        assert len(results) >= 1
        assert results[0]['code'] == '091030'

    def test_nonsense(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "zzzqqq"}, timeout=20)
        assert r.status_code == 200
        assert r.json().get('results', []) == []


# --- HSN Detail ---
class TestHsnDetail:
    def test_non_curated(self):
        r = requests.get(f"{API}/hsn/091030", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get('title')
        assert 'gst' in data
        assert 'rodtep' in data
        assert isinstance(data.get('documents'), list)
        assert isinstance(data.get('exportBenefits'), list)
        assert data.get('category')

    def test_curated_basmati(self):
        r = requests.get(f"{API}/hsn/10063020", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert 'Basmati' in data.get('title', '')
        rodtep = data.get('rodtep', '')
        if isinstance(rodtep, dict):
            rodtep = str(rodtep)
        assert '1.0%' in rodtep or '1%' in rodtep

    def test_unknown_404(self):
        r = requests.get(f"{API}/hsn/000000", timeout=20)
        assert r.status_code == 404


# --- Tools Next Steps ---
class TestNextSteps:
    @pytest.mark.parametrize("tool", ["duty", "trade-stats", "command-center", "hsn", "readiness", "buyers", "incentives"])
    def test_deterministic(self, tool):
        r = requests.post(f"{API}/tools/next-steps", json={"tool": tool, "ai": False, "inputs": {}}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get('ok') is True
        assert isinstance(data.get('insight'), str) and len(data['insight']) > 0
        steps = data.get('nextSteps', [])
        assert 1 <= len(steps) <= 5
        for s in steps:
            assert 'label' in s and 'to' in s
        assert data.get('upgrade', {}).get('to') == '/pricing'

    def test_duty_specific_links(self):
        r = requests.post(f"{API}/tools/next-steps", json={
            "tool": "duty", "ai": False,
            "inputs": {"hs": "100630", "origin": "356", "destination": "276"}
        }, timeout=20)
        assert r.status_code == 200
        steps = r.json().get('nextSteps', [])
        tos = [s['to'] for s in steps]
        assert any('/export/basmati-rice/to/germany' in t for t in tos), f"missing export page link: {tos}"
        assert any('/buyers?hs=100630' in t and 'Germany' in t for t in tos), f"missing buyers link: {tos}"

    def test_ai_insight(self):
        r = requests.post(f"{API}/tools/next-steps", json={
            "tool": "duty", "ai": True,
            "inputs": {"hs": "100630", "origin": "356", "destination": "276"},
            "result": {"importDuty": {"rate": 50, "year": 2023}, "exportBenefit": {"rate": 1.0}}
        }, timeout=35)
        assert r.status_code == 200
        data = r.json()
        # soft check
        assert data.get('insight')
        # aiGenerated may be true, soft
        print(f"AI flag: {data.get('aiGenerated')}")


# --- Removed mock endpoints should 404 ---
class TestRemovedMocks:
    @pytest.mark.parametrize("ep", ["/duty-calc", "/landed-cost", "/export-incentive", "/product-research", "/find-buyers"])
    def test_404(self, ep):
        r = requests.post(f"{API}{ep}", json={}, timeout=15)
        assert r.status_code == 404, f"{ep} returned {r.status_code}"

    def test_export_readiness_still_works(self):
        r = requests.post(f"{API}/export-readiness", json={
            "answers": {"iec": True, "gst": True},
            "name": "Test User", "email": "test+tools@vametra.com", "phone": "+919999999999"
        }, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert 'score' in data
        assert 'band' in data


# --- Duty Lookup ---
class TestDutyLookup:
    def test_lookup_rice_in_de(self):
        r = requests.get(f"{API}/duty/lookup", params={"hs": "100630", "origin": "356", "destination": "276"}, timeout=45)
        assert r.status_code == 200
        data = r.json()
        assert data.get('ok') is True
        assert 'importDuty' in data
        assert 'exportBenefit' in data
        imp = data['importDuty']
        if isinstance(imp.get('rate'), (int, float)) and imp['rate'] == 0:
            notes = data.get('notes') or imp.get('notes') or []
            assert any('specific' in str(n).lower() for n in notes), f"missing specific-duty note: {data}"
