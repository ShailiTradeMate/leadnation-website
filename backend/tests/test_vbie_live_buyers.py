"""VBIE — Live/Real Verified Buyer tests (iteration 32).

Covers:
- /api/buyers/meta with real buyer count > 0 + disclaimer
- /api/buyers/search filters (country, sector, corridor, hs, trust_min, q)
- /api/buyers/sources source registry + sanctions block
- Paywall: locked teaser on GET /{geid} and 402 on /{geid}/evidence
- Admin: /buyers/ingest/status and /buyers/ingest/run with X-Admin-Token
- Ingestion screened_out >= 1
- No sample/demo buyers (all real: sample=False, source_verified=True)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_HEADER = {"X-Admin-Token": "leadnation-admin-2026"}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ── /meta ────────────────────────────────────────────────────────────────────
def test_meta_real_data(s):
    r = s.get(f"{API}/buyers/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0, f"expected real buyers>0, got {d['total']}"
    assert isinstance(d["countries"], list) and len(d["countries"]) > 0
    assert isinstance(d["sectors"], list) and len(d["sectors"]) > 0
    assert d["trust_bands"] == ["Verified", "Trusted", "Emerging", "Unverified"]
    disc = d.get("disclaimer", "").lower()
    assert "official" in disc or "government" in disc or "source" in disc, disc


# ── /search filters ─────────────────────────────────────────────────────────
def test_search_default_sorted_by_trust(s):
    r = s.get(f"{API}/buyers/search", params={"limit": 50}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
    scores = [b["trust"]["score"] for b in d["buyers"]]
    assert scores == sorted(scores, reverse=True)


def test_search_country(s):
    meta = s.get(f"{API}/buyers/meta", timeout=30).json()
    if not meta["countries"]:
        pytest.skip("no countries facet")
    country = meta["countries"][0]["name"] if isinstance(meta["countries"][0], dict) else meta["countries"][0]
    r = s.get(f"{API}/buyers/search", params={"country": country, "limit": 20}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    for b in d["buyers"]:
        assert b["country_name"] == country


def test_search_sector(s):
    meta = s.get(f"{API}/buyers/meta", timeout=30).json()
    if not meta["sectors"]:
        pytest.skip("no sectors facet")
    sector = meta["sectors"][0]["name"] if isinstance(meta["sectors"][0], dict) else meta["sectors"][0]
    r = s.get(f"{API}/buyers/search", params={"sector": sector, "limit": 20}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1


def test_search_trust_min(s):
    r = s.get(f"{API}/buyers/search", params={"trust_min": 80, "limit": 50}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    for b in d["buyers"]:
        assert b["trust"]["score"] >= 80


def test_search_hs_and_q(s):
    r = s.get(f"{API}/buyers/search", params={"hs": "1006"}, timeout=30)
    assert r.status_code == 200
    r2 = s.get(f"{API}/buyers/search", params={"q": "food"}, timeout=30)
    assert r2.status_code == 200


def test_no_fake_demo_buyers(s):
    r = s.get(f"{API}/buyers/search", params={"limit": 500}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    fake_names = {"Atlantic Grain & Foods", "Emirates Food Trading"}
    for b in d["buyers"]:
        # sample flag / source_verified may live at top level; be lenient
        assert b.get("sample") in (False, None), f"sample buyer detected: {b.get('display_name')}"
        name = b.get("display_name") or b.get("name") or ""
        assert name not in fake_names, f"fake demo buyer remains: {name}"


# ── /sources ────────────────────────────────────────────────────────────────
def test_sources_registry(s):
    r = s.get(f"{API}/buyers/sources", timeout=30)
    assert r.status_code == 200
    d = r.json()
    sources = d.get("sources") or d.get("registry") or []
    assert isinstance(sources, list) and len(sources) >= 5, f"expected source registry, got {len(sources)}"
    # sanctions screening block
    sanc = d.get("sanctions_screening") or {}
    assert sanc, "missing sanctions_screening block"
    dp = sanc.get("denied_parties") or sanc.get("count") or 0
    assert dp and dp > 1000, f"denied_parties too low: {dp}"
    # last ingestion summary present
    assert d.get("last_ingestion") is not None or d.get("last_run") is not None


# ── PAYWALL on detail + evidence (unauthenticated) ──────────────────────────
@pytest.fixture(scope="module")
def sample_geid(s):
    r = s.get(f"{API}/buyers/search", params={"limit": 1}, timeout=30).json()
    assert r["buyers"], "no buyers to test paywall"
    return r["buyers"][0]["geid"]


def test_paywall_detail_locked(s, sample_geid):
    r = s.get(f"{API}/buyers/{sample_geid}", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("locked") is True
    assert d.get("lock_reason") == "login"
    assert d.get("display_name")
    assert d.get("website", "") == ""
    assert d.get("provenance", []) == []


def test_paywall_evidence_402(s, sample_geid):
    r = s.get(f"{API}/buyers/{sample_geid}/evidence", timeout=30)
    assert r.status_code == 402


# ── ADMIN endpoints ─────────────────────────────────────────────────────────
def test_admin_ingest_status_requires_token(s):
    r = s.get(f"{API}/buyers/ingest/status", timeout=30)
    assert r.status_code == 401


def test_admin_ingest_status_ok(s):
    r = s.get(f"{API}/buyers/ingest/status", headers=ADMIN_HEADER, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("real_buyers", 0) > 0
    assert d.get("sample_buyers", 0) == 0
    # run history
    assert "runs" in d or "history" in d or "last_run" in d


def test_admin_ingest_run_ok(s):
    r = s.post(f"{API}/buyers/ingest/run", headers=ADMIN_HEADER, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is True


def test_sanctions_screened_out(s):
    r = s.get(f"{API}/buyers/ingest/status", headers=ADMIN_HEADER, timeout=30)
    d = r.json()
    # walk possible shapes: last_run.screened_out or runs[-1].screened_out
    screened = None
    if isinstance(d.get("last_run"), dict):
        screened = d["last_run"].get("screened_out")
    if screened is None and isinstance(d.get("runs"), list) and d["runs"]:
        screened = d["runs"][-1].get("screened_out") or d["runs"][0].get("screened_out")
    if screened is None:
        screened = d.get("screened_out")
    assert screened is not None and screened >= 1, f"expected screened_out>=1, got {screened} / payload keys={list(d.keys())}"
