"""Part 6 SEO backend tests."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
# Fallback to local for backend-only verification
LOCAL = "http://localhost:8001"
ADMIN_TOKEN = "leadnation-admin-2026"


def _get(path, **kw):
    """Try preview URL first, fall back to local."""
    for base in (BASE_URL, LOCAL):
        try:
            r = requests.get(f"{base}{path}", timeout=15, **kw)
            return r
        except Exception:
            continue
    raise RuntimeError("all backends unreachable")


class TestSeoFacts:
    def test_facts_shape_and_cache(self):
        r1 = _get("/api/seo/facts")
        assert r1.status_code == 200, r1.text
        d = r1.json()
        assert d["hsCodes"] == 5606, d
        assert d["tariffCountries"] == 56
        assert d["buyerRecords"] > 0
        assert d["buyerCountries"] > 0
        assert "buyerSectors" in d
        assert d["guides"] == 392
        assert isinstance(d["asOf"], str) and len(d["asOf"]) > 3
        assert isinstance(d["sources"], dict)
        # Second call cache
        r2 = _get("/api/seo/facts")
        assert r2.status_code == 200
        assert r2.json() == d


class TestAnswers:
    def test_answers_index(self):
        r = _get("/api/answers/index")
        assert r.status_code == 200
        d = r.json()
        assert d.get("total") == 414, f"total={d.get('total')}"
        items = d.get("items") or d.get("answers") or []
        first = items[0]
        # path can be in 'path' or embedded in 'page' url
        p = first.get("path") or first.get("page", "")
        assert p.endswith("/about"), first

    def test_answers_md_about(self):
        r = _get("/api/answers/md/about")
        assert r.status_code == 200
        assert r.text.lstrip().startswith("# About Vametra AI"), r.text[:200]

    def test_answers_html_about(self):
        r = _get("/api/answers/html/about")
        assert r.status_code == 200
        assert "<" in r.text


class TestWarmStatus:
    def test_warm_status_without_token(self):
        r = _get("/api/seo/warm-status")
        assert r.status_code == 403, r.status_code

    def test_warm_status_with_token(self):
        r = _get("/api/seo/warm-status", headers={"x-admin-token": ADMIN_TOKEN})
        assert r.status_code == 200
        d = r.json()
        pc = d.get("pageCache", {})
        assert pc.get("entries") == 392, d
        keys = pc.get("keys") or d.get("keys") or []
        # keys may be an object listing categories
        if isinstance(keys, list):
            key_str = " ".join(keys)
        else:
            key_str = str(d)
        assert "page-data" in key_str or "prerender" in key_str, d
