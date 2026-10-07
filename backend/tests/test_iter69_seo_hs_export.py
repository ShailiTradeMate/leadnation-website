"""Iteration 69 backend tests: HS directory, Product x Country SEO pages, sitemap integrity, regression."""
import os
import re
import pytest
import requests
import xml.etree.ElementTree as ET

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
ADMIN_HEADER = {"X-Admin-Token": "leadnation-admin-2026"}
TIMEOUT = 60


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------- HS directory ----------
class TestHsDirectory:
    def test_total_count(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"limit": 1}, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("total") == 5606, f"expected 5606, got {data.get('total')}"

    def test_no_duplicate_hs6_full(self, s):
        # page through all
        seen = set()
        offset = 0
        while True:
            r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"limit": 500, "offset": offset}, timeout=TIMEOUT)
            assert r.status_code == 200
            items = r.json().get("items") or r.json().get("results") or []
            if not items:
                break
            for it in items:
                hs6 = it.get("hs6") or it.get("code")
                assert hs6 not in seen, f"duplicate hs6 {hs6}"
                seen.add(hs6)
            offset += len(items)
            if len(items) < 500:
                break
        assert len(seen) == 5606

    def test_search_turmeric(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"q": "turmeric"}, timeout=TIMEOUT)
        assert r.status_code == 200
        items = r.json().get("items") or r.json().get("results") or []
        codes = [it.get("hs6") or it.get("code") for it in items]
        assert "091030" in codes

    def test_search_code_prefix(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"q": "0910"}, timeout=TIMEOUT)
        assert r.status_code == 200
        items = r.json().get("items") or r.json().get("results") or []
        codes = [it.get("hs6") or it.get("code") for it in items]
        assert all(c.startswith("0910") for c in codes), codes
        assert len(codes) > 0

    def test_chapter_filter(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"chapter": "09", "limit": 500}, timeout=TIMEOUT)
        assert r.status_code == 200
        items = r.json().get("items") or r.json().get("results") or []
        for it in items:
            code = it.get("hs6") or it.get("code")
            assert code.startswith("09"), code

    def test_limit_capped(self, s):
        # Either server caps at 500 silently, or rejects values > 500 with 422
        r = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"limit": 9999}, timeout=TIMEOUT)
        assert r.status_code in (200, 422)
        if r.status_code == 200:
            items = r.json().get("items") or r.json().get("results") or []
            assert len(items) <= 500
        # verify 500 works
        r2 = s.get(f"{BASE}/api/trade-intel/hs-directory", params={"limit": 500}, timeout=TIMEOUT)
        assert r2.status_code == 200
        items2 = r2.json().get("items") or r2.json().get("results") or []
        assert len(items2) <= 500


class TestHsChapters:
    def test_chapters(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-chapters", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else (data.get("items") or data.get("chapters") or [])
        assert 90 <= len(items) <= 100, f"got {len(items)}"
        sample = items[0]
        for k in ("chapter", "section"):
            assert k in sample, f"missing {k} in {sample}"
        # sectionName and codes count
        has_counts = any(("codes" in i) or ("count" in i) for i in items)
        has_sname = any("sectionName" in i for i in items)
        assert has_counts and has_sname


class TestHsSearch:
    def test_hs_search(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-search", params={"q": "turmeric"}, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else (data.get("items") or data.get("results") or [])
        assert len(items) > 0

    def test_hs_search_code(self, s):
        r = s.get(f"{BASE}/api/trade-intel/hs-search", params={"q": "100630"}, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else (data.get("items") or data.get("results") or [])
        assert len(items) > 0


# ---------- Product x Country ----------
class TestSeoPageData:
    def test_basmati_germany(self, s):
        r = s.get(f"{BASE}/api/seo/page-data/basmati-rice/germany", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("indexable") is True
        # product/duty content
        assert d.get("product", {}).get("primaryHs") == "100630"
        assert d.get("duty", {}).get("hsCode") == "100630"
        duty_rate = d["duty"]["importDuty"]
        assert "rate" in duty_rate and "year" in duty_rate and "source" in duty_rate
        # demand data present
        dem = d.get("demand") or {}
        assert dem.get("worldImportsUSD", 0) > 0
        assert dem.get("countryImportsUSD", 0) > 0
        assert dem.get("countryRank")
        assert len(dem.get("topImporters") or []) >= 5

    def test_agarbatti_bahrain_thin(self, s):
        r = s.get(f"{BASE}/api/seo/page-data/agarbatti/bahrain", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("indexable") is False, d.get("score")

    def test_agarbatti_uae_waitlist(self, s):
        r = s.get(f"{BASE}/api/seo/page-data/agarbatti/uae", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        buyers = d.get("buyers") or {}
        # should have waitlist=true or coverage flag
        is_wait = buyers.get("waitlist") or buyers.get("mode") == "waitlist" or buyers.get("coverage") == "waitlist"
        assert is_wait or (buyers.get("count", 0) == 0), f"UAE buyers panel: {buyers}"

    def test_agarbatti_germany_real(self, s):
        r = s.get(f"{BASE}/api/seo/page-data/agarbatti/germany", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        buyers = d.get("buyers") or {}
        # Europe should NOT be waitlist
        assert not (buyers.get("waitlist") or buyers.get("mode") == "waitlist"), buyers

    def test_unknown_slugs(self, s):
        r = s.get(f"{BASE}/api/seo/page-data/not-a-product/germany", timeout=TIMEOUT)
        # Could 404 or return error payload
        if r.status_code == 200:
            d = r.json()
            assert d.get("error") or d.get("indexable") is False
        else:
            assert r.status_code in (404, 400)


# ---------- Sitemap ----------
class TestSitemap:
    def test_sitemap_valid_and_no_noindex(self, s):
        r = s.get(f"{BASE}/api/sitemap.xml", timeout=TIMEOUT)
        assert r.status_code == 200
        root = ET.fromstring(r.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [u.text for u in root.findall(".//sm:url/sm:loc", ns)]
        export_urls = [u for u in urls if "/export/" in u]
        assert len(export_urls) > 0
        # Bahrain / agarbatti must be absent
        for u in export_urls:
            assert "agarbatti/to/bahrain" not in u, f"noindex page in sitemap: {u}"


# ---------- Part 1 regression ----------
class TestPart1Regression:
    def test_catalogue(self, s):
        r = s.get(f"{BASE}/api/seo/catalogue", timeout=TIMEOUT)
        assert r.status_code == 200

    def test_matrix_filtered(self, s):
        r = s.get(f"{BASE}/api/seo/matrix", params={"product": "agarbatti", "region": "middle-east"}, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_ping_log_requires_admin(self, s):
        r = s.get(f"{BASE}/api/seo/ping-log", timeout=TIMEOUT)
        assert r.status_code in (401, 403)


# ---------- General regression ----------
class TestGeneralRegression:
    def test_countries(self, s):
        r = s.get(f"{BASE}/api/countries", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        items = d if isinstance(d, list) else (d.get("countries") or d.get("items") or [])
        assert len(items) == 250, f"got {len(items)}"

    def test_duty_lookup(self, s):
        r = s.get(f"{BASE}/api/duty/lookup", params={"hs": "100630", "origin": "356", "destination": "784"}, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_buyers_meta(self, s):
        r = s.get(f"{BASE}/api/buyers/meta", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("total") == 27388, f"got {d.get('total')}"
