"""Iter 73 — Publish batch 1 + internal link graph tests."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = "leadnation-admin-2026"
TIMEOUT = 180


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    return sess


# ---------------- Guides index ----------------
class TestGuidesIndex:
    def test_guides_index(self, s):
        r = s.get(f"{BASE_URL}/api/seo/guides", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("total") == 392, f"total={d.get('total')}"
        products = d.get("products") or []
        assert len(products) == 8
        for p in products:
            assert "marketCount" in p and "demandUSD" in p and "hub" in p and "markets" in p
            demands = [m.get("demandUSD", 0) for m in p["markets"]]
            assert demands == sorted(demands, reverse=True)
        regions = {r_["slug"]: r_ for r_ in d.get("regions", [])}
        assert set(regions) >= {"europe", "asia-pacific", "middle-east", "americas", "africa"}
        def _c(r_): return r_.get("count") or r_.get("guides")
        assert _c(regions["europe"]) == 152
        assert _c(regions["asia-pacific"]) == 104
        assert _c(regions["middle-east"]) == 64
        assert _c(regions["americas"]) == 40
        assert _c(regions["africa"]) == 32
        for slug in ["europe", "middle-east", "asia-pacific", "americas", "africa"]:
            assert regions[slug].get("url"), f"missing region hub url for {slug}"


# ---------------- Product hubs ----------------
class TestProductHub:
    def test_basmati_rice(self, s):
        r = s.get(f"{BASE_URL}/api/seo/product-hub/basmati-rice", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        stats = d.get("stats") or {}
        assert stats.get("markets") == 49
        assert stats.get("dutyMin") == 0
        assert stats.get("dutyMax") == 513
        assert "zeroDutyMarkets" in stats and "buyerRecords" in stats and "demandUSD" in stats
        markets = d.get("markets") or []
        assert len(markets) == 49
        for m in markets[:5]:
            for k in ("url", "dutyRate", "importsUSD", "dutyToolUrl", "landedCostUrl", "buyersUrl"):
                assert k in m, f"missing {k} in market"
        assert len(d.get("regions") or []) >= 1
        assert len(d.get("relatedProducts") or []) == 7
        tools = d.get("tools") or {}
        for k in ("hsnFinder", "dutyCalculator", "landedCost", "productResearch", "buyers", "brain"):
            assert k in tools
        assert d.get("marketingProduct") == "/products/basmati-rice"

    def test_engineering_machinery_no_marketing(self, s):
        r = s.get(f"{BASE_URL}/api/seo/product-hub/engineering-machinery", timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json().get("marketingProduct") in (None, "", None)

    def test_404(self, s):
        r = s.get(f"{BASE_URL}/api/seo/product-hub/not-a-product", timeout=TIMEOUT)
        assert r.status_code == 404


# ---------------- Guides by country ----------------
class TestGuidesByCountry:
    def test_germany(self, s):
        r = s.get(f"{BASE_URL}/api/seo/guides-by-country/germany", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        guides = d.get("guides") or []
        assert len(guides) == 8
        for g in guides:
            assert g.get("productHub", "").startswith("/export/")
        assert d.get("regionHub") == "/regions/europe"

    def test_uae(self, s):
        r = s.get(f"{BASE_URL}/api/seo/guides-by-country/uae", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert len(d.get("guides") or []) >= 1
        assert d.get("regionHub") == "/regions/middle-east"


# ---------------- page-data related ----------------
class TestPageDataRelated:
    def test_related_block(self, s):
        r = s.get(f"{BASE_URL}/api/seo/page-data/basmati-rice/germany", timeout=TIMEOUT)
        assert r.status_code == 200
        rel = r.json().get("related") or {}
        assert rel.get("productHub") == "/export/basmati-rice"
        assert rel.get("guidesIndex") == "/export"
        assert rel.get("regionHub") == "/regions/europe"
        assert rel.get("marketingProduct") == "/products/basmati-rice"
        spm = rel.get("sameProductMarkets") or []
        assert len(spm) == 8
        for m in spm:
            assert "germany" not in (m.get("country") or m.get("slug") or m.get("url") or "").lower()
        scp = rel.get("sameCountryProducts") or []
        assert len(scp) == 7
        for p in scp:
            u = (p.get("product") or p.get("slug") or p.get("url") or "").lower()
            assert "basmati-rice" not in u


# ---------------- Regions ----------------
class TestRegions:
    def test_americas(self, s):
        r = s.get(f"{BASE_URL}/api/seo/region/americas", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("indexable") is True
        assert len(d.get("facts") or []) == 4
        assert len(d.get("countries") or d.get("cards") or []) >= 1

    def test_africa(self, s):
        r = s.get(f"{BASE_URL}/api/seo/region/africa", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("indexable") is True
        assert len(d.get("facts") or []) == 4

    def test_regions_list(self, s):
        r = s.get(f"{BASE_URL}/api/seo/regions", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        regions = d.get("regions") or d
        slugs = {x.get("slug") for x in regions} if isinstance(regions, list) else set()
        assert slugs >= {"europe", "asia-pacific", "middle-east", "americas", "africa"}


# ---------------- GEO answers ----------------
class TestAnswers:
    def test_answers_index(self, s):
        r = s.get(f"{BASE_URL}/api/answers/index", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("total") == 413, f"total={d.get('total')}"

    def test_md_pharma(self, s):
        r = s.get(f"{BASE_URL}/api/answers/md/export/pharmaceuticals", timeout=TIMEOUT)
        assert r.status_code == 200
        txt = r.text
        # buyer counts formatted with comma
        assert re.search(r"\d{1,3}(,\d{3})+", txt), "expected comma-formatted number"
        # count the market lines - should list 49 markets. Allow flexible but ensure >40 country references
        assert txt.count("/export/pharmaceuticals/to/") >= 40

    def test_html_canonical(self, s):
        r = s.get(f"{BASE_URL}/api/answers/html/export/basmati-rice", timeout=TIMEOUT)
        assert r.status_code == 200
        html = r.text
        canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]*>', html)
        assert len(canonicals) == 1
        assert "https://vametra.com/export/basmati-rice" in canonicals[0]


# ---------------- Sitemap ----------------
class TestSitemap:
    def test_sitemap(self, s):
        r = s.get(f"{BASE_URL}/api/sitemap.xml", timeout=TIMEOUT)
        assert r.status_code == 200
        locs = re.findall(r"<loc>([^<]+)</loc>", r.text)
        assert 950 <= len(locs) <= 1050, f"loc count={len(locs)}"
        assert len(locs) == len(set(locs)), "duplicate <loc> entries"
        assert any(u.endswith("/export") for u in locs)
        for p in ["basmati-rice", "pharmaceuticals"]:
            assert any(u.endswith(f"/export/{p}") for u in locs)
        # regions
        assert any(u.endswith("/regions") for u in locs)
        for rg in ["europe", "asia-pacific", "middle-east", "americas", "africa"]:
            assert any(u.endswith(f"/regions/{rg}") for u in locs)
        # answers URLs
        answer_urls = [u for u in locs if "/api/answers/html/" in u]
        assert len(answer_urls) == 413, f"answer url count={len(answer_urls)}"


# ---------------- Publish batch ----------------
class TestPublishBatch:
    def test_without_token(self, s):
        r = s.post(f"{BASE_URL}/api/seo/publish-batch", timeout=TIMEOUT)
        assert r.status_code == 403

    def test_with_token(self, s):
        r = s.post(
            f"{BASE_URL}/api/seo/publish-batch",
            headers={"x-admin-token": ADMIN_TOKEN},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert d.get("submitted", 0) >= 560
