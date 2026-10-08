"""Iter72 region hubs & GEO answer docs regression."""
import os
import re
import pytest
import requests

def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        return None
    return None

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env() or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not configured"
TIMEOUT = 150  # cold matrix cache

# ---------- /api/seo/regions index ----------
class TestRegionIndex:
    def test_regions_index_returns_three(self):
        r = requests.get(f"{BASE_URL}/api/seo/regions", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        regions = data.get("regions") if isinstance(data, dict) else data
        assert isinstance(regions, list)
        slugs = {x["slug"] for x in regions}
        assert slugs == {"europe", "middle-east", "asia-pacific"}
        for row in regions:
            for k in ("slug", "name", "url", "countries", "guides", "buyers", "dataAsOf"):
                assert k in row, f"missing {k} in {row}"

    def test_europe_buyers_deduped(self):
        r = requests.get(f"{BASE_URL}/api/seo/regions", timeout=TIMEOUT)
        regions = r.json().get("regions") if isinstance(r.json(), dict) else r.json()
        europe = next(x for x in regions if x["slug"] == "europe")
        # Must be country-deduped (roughly 20-30k) not inflated ~190k
        assert europe["buyers"] < 100000, f"europe buyers appear not deduped: {europe['buyers']}"


# ---------- /api/seo/region/{slug} ----------
class TestRegionEurope:
    @pytest.fixture(scope="class")
    def eu(self):
        r = requests.get(f"{BASE_URL}/api/seo/region/europe", timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        return r.json()

    def test_structure(self, eu):
        for k in ("stats", "intro", "facts", "countries", "products", "sources", "disclaimer"):
            assert k in eu, f"missing {k}"
        s = eu["stats"]
        assert s["countries"] == 20
        assert s["guides"] > 0
        assert s["importsUSD"] > 0
        assert "buyerRecords" in s and "buyerCoveredCountries" in s
        assert len(eu["facts"]) == 4
        assert eu.get("indexable") is True

    def test_countries_entries(self, eu):
        assert len(eu["countries"]) == 20
        for c in eu["countries"]:
            for k in ("dutyToolUrl", "landedCostUrl", "buyersUrl"):
                assert c.get(k), f"{c.get('slug')} missing {k}"
        uae = next((c for c in eu["countries"] if c.get("slug") == "uae"), None)
        # UAE not in Europe — expected absent. Check Germany/France exist instead.
        slugs = {c["slug"] for c in eu["countries"]}
        assert "germany" in slugs

    def test_products(self, eu):
        assert isinstance(eu["products"], list) and len(eu["products"]) > 0
        for p in eu["products"]:
            assert p.get("importsUSD", 0) >= 0
            assert isinstance(p.get("markets", []), list)
            assert len(p["markets"]) <= 5

    def test_sources(self, eu):
        assert isinstance(eu["sources"], list) and len(eu["sources"]) > 0
        for s in eu["sources"]:
            for k in ("name", "field", "asOf"):
                assert k in s


class TestRegionMiddleEast:
    def test_middle_east(self):
        r = requests.get(f"{BASE_URL}/api/seo/region/middle-east", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert len(data["countries"]) == 9
        # UAE should have profile + corridor; Oman should have null for both
        uae = next((c for c in data["countries"] if c["slug"] == "uae"), None)
        oman = next((c for c in data["countries"] if c["slug"] == "oman"), None)
        assert uae is not None and oman is not None
        assert uae.get("profileUrl") == "/countries/uae"
        assert uae.get("corridorUrl") == "/corridors/india-to-uae"
        assert oman.get("profileUrl") in (None, "")
        assert oman.get("corridorUrl") in (None, "")
        # buyerCoverage false, buyers 0, still real importsUSD
        for c in data["countries"]:
            assert c.get("buyerCoverage") is False
            assert c.get("buyers", 0) == 0
        total_imports = sum(c.get("topImportsUSD", 0) or 0 for c in data["countries"])
        assert total_imports > 0


class TestRegionAsiaPacific:
    def test_ap(self):
        r = requests.get(f"{BASE_URL}/api/seo/region/asia-pacific", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert len(data["countries"]) == 14


class TestRegion404:
    def test_antarctica(self):
        r = requests.get(f"{BASE_URL}/api/seo/region/antarctica", timeout=TIMEOUT)
        assert r.status_code == 404


# ---------- GEO answers ----------
class TestGeoAnswers:
    def test_europe_markdown(self):
        r = requests.get(f"{BASE_URL}/api/answers/md/regions/europe", timeout=TIMEOUT)
        assert r.status_code == 200
        md = r.text
        # Money formatting: must be 'US$' uppercase and 'M' uppercase
        assert "US$" in md
        assert re.search(r"US\$[0-9][0-9.,]*[MBK]", md), "money not formatted US$NN.NM"
        assert not re.search(r"us\$[0-9]", md), "found lowercased money string"
        # Core sections
        assert "Sources" in md or "source" in md.lower()
        assert "disclaim" in md.lower()

    def test_middle_east_markdown(self):
        r = requests.get(f"{BASE_URL}/api/answers/md/regions/middle-east", timeout=TIMEOUT)
        assert r.status_code == 200
        assert "US$" in r.text

    def test_ap_html_canonical(self):
        r = requests.get(f"{BASE_URL}/api/answers/html/regions/asia-pacific", timeout=TIMEOUT)
        assert r.status_code == 200
        html = r.text
        canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]*>', html)
        assert len(canonicals) == 1, f"expected 1 canonical, got {len(canonicals)}"
        assert "https://vametra.com/regions/asia-pacific" in canonicals[0]

    def test_answer_index_contains_regions_and_tools(self):
        r = requests.get(f"{BASE_URL}/api/answers/index", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        paths_blob = str(data)
        for p in ("/regions/europe", "/regions/middle-east", "/regions/asia-pacific"):
            assert p in paths_blob, f"missing {p} in answer index"


# ---------- sitemap ----------
class TestSitemap:
    def test_sitemap_contains_regions(self):
        r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=TIMEOUT)
        assert r.status_code == 200
        xml = r.text
        assert xml.lstrip().startswith("<?xml")
        assert "https://vametra.com/regions" in xml
        for slug in ("europe", "middle-east", "asia-pacific"):
            assert f"https://vametra.com/regions/{slug}" in xml
        assert "/api/answers/html/regions/" in xml
