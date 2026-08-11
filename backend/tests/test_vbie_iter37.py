"""Regression tests for VBIE iteration 37: GLEIF/CH ingestion, intelligence panel, legal gating."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://payments-cms.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = "leadnation-admin-2026"

LEI_BUYER = "LN-buyer-C3FYC9ZJHCKS7VCGKBENZNSDHZ"
CH_BUYER = "LN-buyer-1YF6ABYE21V8F0APNZ396CJDSG"


def test_buyers_meta():
    r = requests.get(f"{BASE_URL}/api/buyers/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("total", 0) >= 11000, f"total={d.get('total')}"
    assert "countries" in d and "sectors" in d
    disclaimer = (d.get("disclaimer") or "") + " " + str(d.get("attribution") or "")
    dl = disclaimer.lower()
    assert "gleif" in dl, f"disclaimer missing GLEIF: {disclaimer}"
    assert "companies house" in dl, f"disclaimer missing Companies House: {disclaimer}"


def test_buyers_search_paginate():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"page": 1, "page_size": 10}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    items = d.get("items") or d.get("results") or d.get("buyers") or []
    assert len(items) > 0
    # trust score present
    first = items[0]
    ts = first.get("trust_score") or (first.get("trust") or {}).get("score") or (first.get("intelligence") or {}).get("trust_score")
    assert ts is not None, f"trust_score missing in card: {first}"
    r2 = requests.get(f"{BASE_URL}/api/buyers/search", params={"page": 2, "page_size": 10}, timeout=30)
    assert r2.status_code == 200


def test_locked_buyer_has_intelligence_and_empty_provenance():
    r = requests.get(f"{BASE_URL}/api/buyers/{LEI_BUYER}", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("locked") is True, f"expected locked True, got {d.get('locked')}"
    intel = d.get("intelligence") or {}
    assert "trust_score" in intel
    for k in ("confidence", "freshness", "source_reliability"):
        assert isinstance(intel.get(k), dict) and "label" in intel[k], f"{k} missing label"
    assert isinstance(d.get("evidence_sources"), list) and len(d["evidence_sources"]) > 0
    # provenance must be empty when locked
    prov = d.get("provenance", [])
    assert prov == [], f"expected empty provenance when locked, got {prov}"


def test_evidence_endpoint_402_unauth():
    r = requests.get(f"{BASE_URL}/api/buyers/{LEI_BUYER}/evidence", timeout=30)
    assert r.status_code == 402, f"expected 402, got {r.status_code}: {r.text[:200]}"


def test_sources_includes_gleif_and_ch():
    r = requests.get(f"{BASE_URL}/api/buyers/sources", timeout=30)
    assert r.status_code == 200
    d = r.json()
    src_list = d if isinstance(d, list) else (d.get("sources") or d.get("items") or [])
    names = " | ".join([str(s.get("name") or s.get("label") or s) for s in src_list]).lower()
    assert "gleif" in names, f"GLEIF missing in sources: {names}"
    assert "companies house" in names, f"UK Companies House missing: {names}"


def test_gb_companies_house_buyer():
    r = requests.get(f"{BASE_URL}/api/buyers/{CH_BUYER}", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    country = (d.get("country") or (d.get("company") or {}).get("country") or "").upper()
    assert country in ("GB", "UK", "UNITED KINGDOM"), f"country={country}"
    ev = " | ".join(d.get("evidence_sources") or []).lower()
    assert "companies house" in ev, f"evidence_sources missing CH: {d.get('evidence_sources')}"


def test_lei_buyer_has_lei():
    r = requests.get(f"{BASE_URL}/api/buyers/{LEI_BUYER}", timeout=30)
    assert r.status_code == 200
    d = r.json()
    intel = d.get("intelligence") or {}
    lei = intel.get("lei")
    assert lei and isinstance(lei, str) and len(lei) >= 18, f"lei={lei}"
    ev = " | ".join(d.get("evidence_sources") or []).lower()
    assert "gleif" in ev, f"evidence_sources missing GLEIF: {d.get('evidence_sources')}"


def test_admin_ingest_status():
    r = requests.get(f"{BASE_URL}/api/buyers/ingest/status", headers={"X-Admin-Token": ADMIN_TOKEN}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("real_buyers") or d.get("real_total") or d.get("total"), f"no real count: {d}"
    runs = d.get("runs") or []
    assert len(runs) > 0
    latest = runs[-1] if isinstance(runs, list) else runs
    # find one run containing the sources we expect
    joined = str(runs).lower()
    assert "eu_ted" in joined
    assert "uk_companies_house" in joined
    assert "sam_gov" in joined  # skipped_pending_legal
