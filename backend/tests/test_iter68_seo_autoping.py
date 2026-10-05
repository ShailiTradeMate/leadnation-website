"""Iteration 68 — SEO auto-ping (IndexNow) + honest sitemap lastmod regression tests.

Covers:
 - /api/sitemap.xml structure, expected sections, per-URL <lastmod>/<changefreq>/<priority>
 - CMS auto-ping on create/update/delete via /api/admin/collection/{name}
 - Second collection auto-ping (countries) uses correct public prefix
 - Honest lastmod for Google: today's UTC date after a create
 - /api/seo/ping-log + /api/seo/indexnow auth guard (403 w/o or wrong X-Admin-Token)
 - Expo admin create auto-ping + sitemap inclusion
 - Regression: /api/countries, /api/robots.txt, /api/services, /api/events listings, backend logs clean
"""
import os
import re
import time
import uuid
from datetime import datetime, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = "leadnation-admin-2026"
ADMIN_HEADERS = {"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"}


# ---------- helpers ----------

def _get_ping_log(limit=20):
    r = requests.get(f"{BASE_URL}/api/seo/ping-log", params={"limit": limit}, headers=ADMIN_HEADERS, timeout=30)
    assert r.status_code == 200, f"ping-log fetch failed: {r.status_code} {r.text[:200]}"
    return r.json().get("pings", [])


def _wait_for_ping(source, path_contains=None, timeout=15):
    """Poll the audit log until a ping with the given source (and optional path) appears."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for row in _get_ping_log(limit=50):
            if row.get("source") == source:
                if path_contains is None or any(path_contains in p for p in row.get("paths", [])):
                    return row
        time.sleep(1)
    return None


# ---------- SITEMAP ----------

class TestSitemap:
    def test_sitemap_structure_and_sections(self):
        r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=30)
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "").lower()
        xml = r.text
        locs = re.findall(r"<loc>([^<]+)</loc>", xml)
        assert len(locs) >= 100, f"too few <loc> entries: {len(locs)}"
        # must include key pages
        joined = "\n".join(locs)
        for must in ["/marketplace", "/network", "/legal/privacy", "/legal/terms",
                     "/legal/cookies", "/legal/disclaimer", "/legal/refund"]:
            assert any(l.endswith(must) for l in locs), f"missing {must}"
        # 11 services
        services = [l for l in locs if "/services/" in l]
        assert len(services) >= 11, f"expected >=11 /services/*, got {len(services)}"
        # every <url> block has all 4 children
        url_blocks = re.findall(r"<url>.*?</url>", xml, re.S)
        assert len(url_blocks) == len(locs)
        for block in url_blocks[:5] + url_blocks[-5:]:
            for tag in ("<loc>", "<lastmod>", "<changefreq>", "<priority>"):
                assert tag in block, f"missing {tag} in {block[:120]}"

    def test_sitemap_includes_published_expos(self):
        xml = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=30).text
        # at least zero or more /expo/{id} entries; this must not error
        expo_entries = re.findall(r"<loc>[^<]*/expo/([^<]+)</loc>", xml)
        # /expo hub always present
        assert "/expo</loc>" in xml or any(e.endswith("/expo") for e in re.findall(r"<loc>([^<]+)</loc>", xml))
        print(f"sitemap expo detail entries: {len(expo_entries)}")


# ---------- AUTH GUARDS ----------

class TestSeoAuthGuards:
    def test_ping_log_requires_admin_token(self):
        r = requests.get(f"{BASE_URL}/api/seo/ping-log", timeout=15)
        assert r.status_code == 403, f"expected 403 w/o token, got {r.status_code}"
        r2 = requests.get(f"{BASE_URL}/api/seo/ping-log",
                          headers={"X-Admin-Token": "WRONG"}, timeout=15)
        assert r2.status_code == 403
        # should not leak pings
        assert "pings" not in r2.text.lower() or r2.json().get("pings") is None

    def test_indexnow_requires_admin_token(self):
        r = requests.post(f"{BASE_URL}/api/seo/indexnow",
                          json={"urls": ["/pricing"]},
                          headers={"X-Admin-Token": "WRONG", "Content-Type": "application/json"}, timeout=15)
        assert r.status_code == 403

    def test_indexnow_valid_token_ok(self):
        r = requests.post(f"{BASE_URL}/api/seo/indexnow",
                          json={"urls": ["/pricing"]},
                          headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True, f"indexnow result not ok: {data}"


# ---------- CMS AUTO-PING (blog + countries) ----------

@pytest.fixture(scope="module")
def blog_item():
    slug = f"test-autoping-{uuid.uuid4().hex[:8]}"
    payload = {"slug": slug, "title": "TEST_autoping", "published": False, "body": "TEST"}
    r = requests.post(f"{BASE_URL}/api/admin/collection/blog",
                      json=payload, headers=ADMIN_HEADERS, timeout=30)
    assert r.status_code == 200, f"blog create failed: {r.status_code} {r.text[:200]}"
    item = r.json()
    assert item.get("slug") == slug
    yield item
    # best-effort cleanup
    try:
        requests.delete(f"{BASE_URL}/api/admin/collection/blog/{item['id']}",
                        headers=ADMIN_HEADERS, timeout=15)
    except Exception:
        pass


class TestCmsAutoPing:
    def test_blog_create_pings(self, blog_item):
        row = _wait_for_ping("cms:blog:create", path_contains=blog_item["slug"], timeout=20)
        assert row is not None, "no cms:blog:create ping-log row found"
        paths = row.get("paths", [])
        assert "/blog" in paths, f"missing /blog in {paths}"
        assert any(p == f"/blog/{blog_item['slug']}" for p in paths), f"missing /blog/<slug> in {paths}"
        result = row.get("result", {})
        assert result.get("ok") is True, f"indexnow result not ok: {result}"
        assert result.get("status") in (200, 202), f"unexpected status: {result}"

    def test_blog_update_pings(self, blog_item):
        r = requests.put(f"{BASE_URL}/api/admin/collection/blog/{blog_item['id']}",
                         json={"title": "TEST_autoping_updated"},
                         headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200, r.text[:200]
        row = _wait_for_ping("cms:blog:update", path_contains=blog_item["slug"], timeout=20)
        assert row is not None, "no cms:blog:update ping-log row"
        assert "/blog" in row["paths"]

    def test_sitemap_lastmod_blog_today(self):
        """Google-side: /blog <lastmod> equals today's UTC date after creation."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        xml = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=30).text
        m = re.search(r"<url><loc>[^<]*/blog</loc><lastmod>([^<]+)</lastmod>", xml)
        assert m is not None, "/blog entry not found in sitemap"
        assert m.group(1) == today, f"/blog lastmod {m.group(1)} != today {today}"

    def test_blog_delete_pings(self, blog_item):
        r = requests.delete(f"{BASE_URL}/api/admin/collection/blog/{blog_item['id']}",
                            headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200
        row = _wait_for_ping("cms:blog:delete", timeout=20)
        assert row is not None, "no cms:blog:delete ping-log row"
        assert row["paths"] == ["/blog"], f"expected ['/blog'], got {row['paths']}"

    def test_countries_collection_autoping(self):
        """Second CMS collection: /countries/ prefix + /countries hub."""
        slug = f"test-ctry-{uuid.uuid4().hex[:6]}"
        payload = {"slug": slug, "name": "TEST_Countryland", "published": False}
        r = requests.post(f"{BASE_URL}/api/admin/collection/countries",
                          json=payload, headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200, r.text[:200]
        item = r.json()
        try:
            row = _wait_for_ping("cms:countries:create", path_contains=slug, timeout=20)
            assert row is not None, "no cms:countries:create ping-log row"
            paths = row.get("paths", [])
            assert "/countries" in paths
            assert f"/countries/{slug}" in paths, f"missing /countries/<slug> in {paths}"
        finally:
            requests.delete(f"{BASE_URL}/api/admin/collection/countries/{item['id']}",
                            headers=ADMIN_HEADERS, timeout=15)


# ---------- EXPO AUTO-PING ----------

class TestExpoAutoPing:
    def test_expo_admin_create_pings_and_in_sitemap(self):
        payload = {
            "name": f"TEST_autoping_expo_{uuid.uuid4().hex[:6]}",
            "country": "India",
            "city": "Mumbai",
            "contactEmail": "test-autoping@vametra.test",
            "startDate": "2026-06-01",
            "endDate": "2026-06-03",
            "description": "TEST ping event",
        }
        r = requests.post(f"{BASE_URL}/api/events/admin/create",
                          json=payload, headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200, f"expo admin create failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        eid = data.get("eventId")
        assert eid, data
        try:
            row = _wait_for_ping("expo:admin-create", path_contains=eid, timeout=20)
            assert row is not None, "no expo:admin-create ping-log row"
            paths = row.get("paths", [])
            assert "/expo" in paths and f"/expo/{eid}" in paths, paths
            # sitemap now contains /expo/{eid}
            xml = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=30).text
            assert f"/expo/{eid}</loc>" in xml, f"/expo/{eid} not in sitemap"
        finally:
            requests.delete(f"{BASE_URL}/api/events/admin/{eid}",
                            headers=ADMIN_HEADERS, timeout=15)


# ---------- REGRESSION ----------

class TestRegression:
    def test_countries_still_returns_all(self):
        r = requests.get(f"{BASE_URL}/api/countries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("countries") or data.get("items") or []
        assert len(items) >= 240, f"expected ~250 countries, got {len(items)}"

    def test_services_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/services", timeout=30)
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("services") or data.get("items") or []
        assert len(items) >= 11, f"expected >=11 services, got {len(items)}"

    def test_expo_listings_endpoint(self):
        # try common listings endpoints
        for path in ("/api/events/list", "/api/events", "/api/events/listings"):
            r = requests.get(f"{BASE_URL}{path}", timeout=20)
            if r.status_code == 200:
                return
        pytest.fail("no working expo listings endpoint among tried paths")

    def test_robots_txt(self):
        # /api/robots.txt or frontend root — must respond
        r = requests.get(f"{BASE_URL}/api/robots.txt", timeout=15)
        if r.status_code != 200:
            r = requests.get(f"{BASE_URL}/robots.txt", timeout=15)
        assert r.status_code == 200, f"robots.txt not reachable: {r.status_code}"

    def test_backend_log_clean_of_seo_tracebacks(self):
        """Scan last 400 lines of backend supervisor log for ImportError / auto-ping failures."""
        import glob
        import subprocess
        logs = sorted(glob.glob("/var/log/supervisor/backend.*.log"))
        if not logs:
            pytest.skip("no supervisor backend log found")
        tail = subprocess.run(["tail", "-n", "400"] + logs, capture_output=True, text=True).stdout
        bad = []
        for line in tail.splitlines():
            low = line.lower()
            if ("importerror" in low and "seo" in low) or ("auto-ping failed" in low) or \
               ("traceback" in low and "seo.py" in low):
                bad.append(line)
        assert not bad, "SEO-related errors in backend log:\n" + "\n".join(bad[:10])
