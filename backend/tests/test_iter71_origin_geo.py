"""Iteration 71 — Origin-aware tools, country incentive registry, GEO answer layer."""
import os
import re
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    return (url or "").rstrip("/")

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"


# --- Country incentive registry ---

class TestIncentiveCountries:
    def test_countries_list(self):
        r = requests.get(f"{API}/incentives/countries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        countries = data.get("countries") or data if isinstance(data, list) else data.get("countries")
        assert isinstance(countries, list)
        assert len(countries) >= 40, f"expected ~52 countries, got {len(countries)}"
        india = next((c for c in countries if str(c.get("code")) == "356"), None)
        assert india is not None
        # India should have hasRateSchedule True
        assert india.get("hasRateSchedule") is True
        for c in countries[:5]:
            assert "code" in c and "name" in c
            # schemeCount & kinds should exist
            assert "schemeCount" in c or "count" in c or "schemes" in c

    @pytest.mark.parametrize("code,expected_name", [
        ("842", "United States"),
        ("356", "India"),
        ("276", "Germany"),
        ("784", "United Arab Emirates"),
    ])
    def test_country_detail_covered(self, code, expected_name):
        r = requests.get(f"{API}/incentives/{code}", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("covered") is True, f"{code} should be covered"
        schemes = data.get("schemes") or []
        assert len(schemes) >= 1
        for s in schemes:
            assert s.get("name")
            assert s.get("authority")
            url = s.get("official") or s.get("url") or s.get("link")
            assert url and url.startswith("https://"), f"scheme missing https url: {s}"
            assert s.get("gives"), f"scheme missing gives text: {s}"

    def test_country_not_covered(self):
        r = requests.get(f"{API}/incentives/204", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("covered") is False
        # no fabricated schemes
        schemes = data.get("schemes") or []
        assert len(schemes) == 0
        assert data.get("note") or data.get("message")


# --- Duty lookup origin awareness ---

class TestDutyLookupOrigin:
    def test_us_origin_no_rodtep(self):
        r = requests.get(f"{API}/duty/lookup", params={"hs": "847130", "origin": "842", "destination": "124"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        es = data.get("exportSupport")
        assert es is not None, "exportSupport missing for US origin"
        schemes = es.get("schemes") if isinstance(es, dict) else es
        assert isinstance(schemes, list) and len(schemes) >= 3
        assert data.get("exportBenefit") in (None, {}, []), "exportBenefit should be null for non-India origin"

    def test_india_origin_rodtep(self):
        r = requests.get(f"{API}/duty/lookup", params={"hs": "100630", "origin": "356", "destination": "276"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("exportBenefit"), "India origin should return RoDTEP exportBenefit"
        assert data.get("exportSupport"), "India origin should also have exportSupport"


# --- HSN finder ---

class TestHsnFinder:
    def test_hsn_us_origin(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "laptop", "origin": "842", "destination": "124"}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        # find first result item
        items = data.get("results") or data.get("matches") or data.get("items") or []
        if items:
            first = items[0]
            assert first.get("exportSupport") or data.get("exportSupport")
        sources_str = (str(data.get("sources") or "") + str(data)).lower()
        assert "dgft" not in sources_str or "rodtep" not in sources_str, "US origin must not include DGFT RoDTEP sources"

    def test_hsn_india_origin(self):
        r = requests.post(f"{API}/hsn-finder", json={"productName": "laptop", "origin": "356", "destination": "276"}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        s = str(data).lower()
        assert ("dgft" in s and "rodtep" in s) or "appendix 4r" in s, "India origin should include DGFT RoDTEP Appendix 4R"


# --- Next steps origin awareness ---

class TestNextSteps:
    def _call(self, tool, origin, dest, hs="847130"):
        payload = {
            "tool": tool,
            "inputs": {"hs": hs, "origin": origin, "destination": dest},
            "result": {},
            "ai": False,
        }
        return requests.post(f"{API}/tools/next-steps", json=payload, timeout=30)

    def test_duty_us_origin(self):
        r = self._call("duty", "842", "124")
        assert r.status_code == 200, r.text
        text = str(r.json()).lower()
        assert "united states" in text
        assert "from=842" in text and "to=124" in text
        # no India-only wording
        assert "rodtep" not in text, f"should not mention RoDTEP for US origin: {text[:500]}"
        assert "dgft" not in text

    def test_incentives_non_india(self):
        r = self._call("incentives", "276", "124")
        assert r.status_code == 200
        text = str(r.json()).lower()
        assert "rodtep" not in text
        assert "dgft" not in text

    def test_buyers_non_india(self):
        r = self._call("buyers", "842", "124")
        assert r.status_code == 200
        text = str(r.json()).lower()
        assert "rodtep" not in text
        assert "dgft" not in text


# --- GEO answer layer ---

class TestAnswers:
    def test_answers_index(self):
        r = requests.get(f"{API}/answers/index", timeout=30)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items") or data
        assert isinstance(items, list)
        assert len(items) >= 100, f"expected 100+ items, got {len(items)}"
        for it in items[:5]:
            assert it.get("page") or it.get("pageUrl") or it.get("path")
            assert it.get("html") or it.get("htmlUrl")
            assert it.get("markdown") or it.get("md") or it.get("markdownUrl")

    def test_md_tool(self):
        r = requests.get(f"{API}/answers/md/tools/duty-calculator", timeout=30)
        assert r.status_code == 200
        body = r.text
        assert len(body) > 200
        assert "source" in body.lower() or "http" in body.lower()

    def test_md_export_guide(self):
        r = requests.get(f"{API}/answers/md/export/basmati-rice/to/germany", timeout=30)
        assert r.status_code == 200
        body = r.text
        assert len(body) > 200
        assert "basmati" in body.lower()

    def test_html_canonical(self):
        r = requests.get(f"{API}/answers/html/export/basmati-rice/to/germany", timeout=30)
        assert r.status_code == 200
        html = r.text
        canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]*>', html, flags=re.I)
        assert len(canonicals) == 1, f"expected exactly 1 canonical, got {len(canonicals)}"
        assert "https://vametra.com/export/basmati-rice/to/germany" in canonicals[0]

    def test_unknown_md_404(self):
        r = requests.get(f"{API}/answers/md/export/nope/to/nowhere", timeout=30)
        assert r.status_code == 404


# --- Sitemap ---

class TestSitemap:
    def test_sitemap_contains_answers(self):
        r = requests.get(f"{API}/sitemap.xml", timeout=30)
        assert r.status_code == 200
        body = r.text
        assert body.strip().startswith("<?xml")
        assert "/api/answers/html/" in body
