"""Backend tests for POST /api/brain/explore (Vametra AI Brain — Explore)."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vametra-whatsapp--5yd7gle9.preview.emergentagent.com").rstrip("/")
EP = f"{BASE_URL}/api/brain/explore"
TIMEOUT = 120


def _post(payload):
    return requests.post(EP, json=payload, timeout=TIMEOUT)


# Corridor: India → Germany, Basmati rice
def test_corridor_india_germany_basmati():
    r = _post({"kind": "corridor", "origin": "India", "destination": "Germany", "product": "Basmati Rice"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("hs6") == "100630", f"hs6={d.get('hs6')}"
    assert isinstance(d.get("duty", {}).get("importDuty", {}).get("rate"), (int, float))
    assert (d.get("demand") or {}).get("countryImportsUSD", 0) > 0
    assert (d.get("buyers") or {}).get("covered") is True
    n = d.get("narrative") or {}
    for k in ("exportProcess", "importProcess", "customsInfo"):
        assert n.get(k), f"missing narrative.{k}"
    assert 6 <= len(n.get("documents") or []) <= 8
    assert len(d.get("faqs") or []) == 4
    links = [l["to"] for l in d.get("closestPublished") or []]
    assert "/export/basmati-rice/to/germany" in links
    assert "/regions/europe" in links
    assert d.get("aiGenerated") is True
    assert d.get("disclaimer")


# Caching: 2nd identical call fast + cached
def test_corridor_cache():
    payload = {"kind": "corridor", "origin": "India", "destination": "Germany", "product": "Basmati Rice"}
    _post(payload)  # ensure cached
    t = time.time()
    r = _post(payload)
    elapsed = time.time() - t
    assert r.status_code == 200
    assert r.json().get("cached") is True
    assert elapsed < 5, f"cached call took {elapsed:.2f}s"


# Country Japan
def test_country_japan():
    r = _post({"kind": "country", "destination": "Japan"})
    assert r.status_code == 200
    assert r.json().get("title") == "Japan trade profile"


# Region Middle East
def test_region_middle_east():
    r = _post({"kind": "region", "region": "Middle East", "product": "spices"})
    assert r.status_code == 200
    rc = r.json().get("regionCountries") or []
    assert len(rc) == 8, f"regionCountries len={len(rc)}: {rc}"


# Product turmeric → Nigeria
def test_product_turmeric_nigeria():
    r = _post({"kind": "product", "product": "turmeric", "destination": "Nigeria"})
    assert r.status_code == 200
    d = r.json()
    assert d.get("hs6") == "091030", f"hs6={d.get('hs6')}"
    assert (d.get("duty") or {}).get("importDuty", {}).get("rate") == 20


# Industry Pharmaceuticals → UAE
def test_industry_pharma_uae():
    r = _post({"kind": "industry", "industry": "Pharmaceuticals", "destination": "UAE"})
    assert r.status_code == 200


# Validation: corridor without destination
def test_corridor_missing_destination():
    r = _post({"kind": "corridor"})
    assert r.status_code == 400
    assert "detail" in r.json()


def test_bogus_kind():
    r = _post({"kind": "bogus"})
    assert r.status_code == 400


# Nonsense product → 200 with notes
def test_nonsense_product_notes():
    r = _post({"kind": "product", "product": "zzqq nonsense"})
    assert r.status_code == 200
    notes = r.json().get("notes") or []
    assert any("hs code" in n.lower() for n in notes), notes
