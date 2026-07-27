"""VBIE — Verified Buyer Intelligence Engine API tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-beyond-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ── /meta ────────────────────────────────────────────────────────────────────
def test_meta(s):
    r = s.get(f"{API}/buyers/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 12
    assert isinstance(d["countries"], list) and len(d["countries"]) > 0
    assert isinstance(d["sectors"], list) and len(d["sectors"]) > 0
    assert isinstance(d["corridors"], list) and len(d["corridors"]) > 0
    assert d["trust_bands"] == ["Verified", "Trusted", "Emerging", "Unverified"]
    assert isinstance(d["disclaimer"], str) and len(d["disclaimer"]) > 10


# ── /search ─────────────────────────────────────────────────────────────────
def test_search_default_returns_12(s):
    r = s.get(f"{API}/buyers/search", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 12
    assert len(d["buyers"]) == 12
    scores = [b["trust"]["score"] for b in d["buyers"]]
    assert scores == sorted(scores, reverse=True)


def test_search_country_uk(s):
    r = s.get(f"{API}/buyers/search", params={"country": "United Kingdom"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    for b in d["buyers"]:
        assert b["country_name"] == "United Kingdom"


def test_search_sector(s):
    r = s.get(f"{API}/buyers/search", params={"sector": "Textiles & Apparel"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    for b in d["buyers"]:
        assert b["sector"] == "Textiles & Apparel"


def test_search_corridor(s):
    r = s.get(f"{API}/buyers/search", params={"corridor": "IN-US"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    for b in d["buyers"]:
        assert "IN-US" in b["corridors"]


def test_search_trust_min(s):
    r_all = s.get(f"{API}/buyers/search", timeout=30).json()
    r = s.get(f"{API}/buyers/search", params={"trust_min": 80}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] <= r_all["total"]
    for b in d["buyers"]:
        assert b["trust"]["score"] >= 80


def test_search_q_textiles(s):
    r = s.get(f"{API}/buyers/search", params={"q": "textiles"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1


# ── /{geid} + evidence + claim ──────────────────────────────────────────────
@pytest.fixture(scope="module")
def sample_geid(s):
    r = s.get(f"{API}/buyers/search", timeout=30).json()
    return r["buyers"][0]["geid"]


def test_get_buyer_detail(s, sample_geid):
    r = s.get(f"{API}/buyers/{sample_geid}", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["geid"] == sample_geid
    assert "trust" in d
    assert isinstance(d["trust"]["score"], int)
    assert d["trust"]["band"] in ["Verified", "Trusted", "Emerging", "Unverified"]
    assert isinstance(d["trust"]["factors"], list) and len(d["trust"]["factors"]) >= 1
    assert isinstance(d["provenance"], list) and len(d["provenance"]) >= 1


def test_get_buyer_evidence(s, sample_geid):
    r = s.get(f"{API}/buyers/{sample_geid}/evidence", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["geid"] == sample_geid
    assert isinstance(d["evidence"], list) and len(d["evidence"]) >= 1
    for e in d["evidence"]:
        assert "source_name" in e
        assert "source_tier" in e


def test_get_buyer_404(s):
    r = s.get(f"{API}/buyers/LN-buyer-DOESNOTEXIST0000000000", timeout=30)
    assert r.status_code == 404


def test_claim_buyer(s, sample_geid):
    payload = {
        "name": "TEST_Claimer",
        "email": "TEST_claim@example.com",
        "company": "TEST Co",
        "message": "Interested in supply",
    }
    r = s.post(f"{API}/buyers/{sample_geid}/claim", json=payload, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["claim_id"]
