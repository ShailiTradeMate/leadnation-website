"""VBIE iteration 38 - Recurring Continuous Intelligence Engine (P1) regression."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vbie-preview.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = "leadnation-admin-2026"
ADMIN_HDR = {"X-Admin-Token": ADMIN_TOKEN}
LEI_BUYER = "LN-buyer-C3FYC9ZJHCKS7VCGKBENZNSDHZ"


# ---------- REGRESSION ----------
def test_meta_total_buyers():
    r = requests.get(f"{BASE_URL}/api/buyers/meta", timeout=30)
    assert r.status_code == 200
    assert (r.json().get("total") or 0) >= 11000


def test_search_returns_cards():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"page": 1, "page_size": 5}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    items = j.get("buyers") or j.get("items") or j.get("results") or []
    assert len(items) > 0


def test_locked_buyer_intelligence_provenance_empty():
    r = requests.get(f"{BASE_URL}/api/buyers/{LEI_BUYER}", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("locked") is True
    assert d.get("intelligence")
    assert isinstance(d.get("evidence_sources"), list) and len(d["evidence_sources"]) > 0
    assert d.get("provenance", []) == []


def test_evidence_unauth_402():
    r = requests.get(f"{BASE_URL}/api/buyers/{LEI_BUYER}/evidence", timeout=30)
    assert r.status_code == 402


# ---------- ENGINE SCHEDULE ----------
def test_get_schedule_defaults():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/schedule", headers=ADMIN_HDR, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    # Might wrap in {"schedule": {...}} or return flat
    cfg = d.get("schedule") if isinstance(d.get("schedule"), dict) else d
    assert cfg.get("enabled") is True
    assert isinstance(cfg.get("weekly"), dict)
    assert isinstance(cfg.get("daily"), dict)
    assert isinstance(cfg.get("monthly"), dict)
    # bulk_enabled may live at either root or under monthly
    bulk = cfg.get("bulk_enabled")
    if bulk is None:
        bulk = (cfg.get("monthly") or {}).get("bulk_enabled")
    assert bulk is False


def test_put_schedule_updates_and_reverts():
    # PUT hour 5
    r = requests.put(
        f"{BASE_URL}/api/buyers/admin/schedule",
        headers=ADMIN_HDR,
        json={"daily": {"hour": 5, "minute": 30}},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True

    r2 = requests.get(f"{BASE_URL}/api/buyers/admin/schedule", headers=ADMIN_HDR, timeout=30).json()
    cfg = r2.get("schedule") if isinstance(r2.get("schedule"), dict) else r2
    assert cfg.get("daily", {}).get("hour") == 5
    assert cfg.get("daily", {}).get("minute") == 30

    # Revert
    r3 = requests.put(
        f"{BASE_URL}/api/buyers/admin/schedule",
        headers=ADMIN_HDR,
        json={"daily": {"hour": 3, "minute": 0}},
        timeout=30,
    )
    assert r3.status_code == 200


# ---------- LEGAL MATRIX ----------
def test_legal_matrix():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/legal", headers=ADMIN_HDR, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    srcs = d.get("sources") if isinstance(d.get("sources"), dict) else d
    approved_expected = ["eu_ted", "cid_canada", "uk_companies_house", "trade_gov_csl", "gleif"]
    pending_expected = ["sam_gov", "sirene_fr"]
    for s in approved_expected:
        row = srcs.get(s) or {}
        assert row.get("approved") is True, f"{s} not approved: {row}"
        assert row.get("legal_status") == "approved", f"{s} legal_status={row.get('legal_status')}"
    for s in pending_expected:
        row = srcs.get(s) or {}
        assert row.get("approved") is False, f"{s} approved should be false: {row}"
        assert row.get("legal_status") == "pending_legal_approval", f"{s} legal_status={row.get('legal_status')}"


# ---------- ENGINE STATUS ----------
def test_engine_status():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/engine/status", headers=ADMIN_HDR, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "schedule" in d or "cycles" in d
    assert isinstance(d.get("cycles", []), list)


# ---------- RUN CYCLE ----------
def test_run_cycle_incremental():
    r = requests.post(
        f"{BASE_URL}/api/buyers/admin/engine/run-cycle",
        headers=ADMIN_HDR,
        params={"kind": "incremental"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("ok") is True
    assert d.get("started") == "incremental"


# ---------- WEEKLY REPORT ----------
def test_generate_and_list_report_and_xlsx():
    r = requests.post(f"{BASE_URL}/api/buyers/admin/reports/generate", headers=ADMIN_HDR, timeout=60)
    assert r.status_code == 200, r.text
    rep = r.json()
    # unwrap if {"report": {...}}
    if isinstance(rep, dict) and "report" in rep and isinstance(rep["report"], dict):
        rep = rep["report"]
    rid = rep.get("_id") or rep.get("id")
    assert rid, f"no id in report: {rep}"
    # metrics (may be nested under 'metrics')
    metrics_bag = rep.get("metrics") if isinstance(rep.get("metrics"), dict) else rep
    for k in ("new_buyers", "buyers_updated", "duplicates_merged", "total_buyers", "lei_coverage_pct"):
        assert k in metrics_bag, f"metric missing: {k} in {list(metrics_bag.keys())}"

    # list
    r2 = requests.get(f"{BASE_URL}/api/buyers/admin/reports", headers=ADMIN_HDR, timeout=30)
    assert r2.status_code == 200
    lst = r2.json()
    items = lst if isinstance(lst, list) else (lst.get("items") or lst.get("reports") or [])
    assert len(items) >= 1

    # xlsx download
    r3 = requests.get(f"{BASE_URL}/api/buyers/admin/reports/{rid}/xlsx", headers=ADMIN_HDR, timeout=30)
    assert r3.status_code == 200, r3.text[:200]
    ct = r3.headers.get("content-type", "").lower()
    assert "spreadsheet" in ct or "officedocument" in ct or "excel" in ct, f"unexpected ct={ct}"


# ---------- WATCHLIST GATING ----------
def test_watch_post_unauth_401():
    r = requests.post(f"{BASE_URL}/api/buyers/{LEI_BUYER}/watch", timeout=30)
    assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"


def test_watchlist_get_unauth_401():
    r = requests.get(f"{BASE_URL}/api/buyers/watchlist", timeout=30)
    assert r.status_code == 401


def test_watch_delete_unauth_401():
    r = requests.delete(f"{BASE_URL}/api/buyers/{LEI_BUYER}/watch", timeout=30)
    assert r.status_code == 401


# ---------- NETWORKING MATCH ----------
def test_match_with_name_country():
    r = requests.get(f"{BASE_URL}/api/buyers/match", params={"name": "ROSSO GROUP", "country": "GB"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    cands = d.get("candidates") if isinstance(d, dict) else d
    assert isinstance(cands, list)
    assert len(cands) > 0, "expected at least one ROSSO GROUP candidate"
    hit = None
    for c in cands:
        name = (c.get("display_name") or c.get("name") or "").upper()
        if "ROSSO GROUP" in name:
            hit = c
            break
    assert hit, f"no ROSSO GROUP in candidates: {cands[:3]}"
    assert hit.get("geid")
    assert hit.get("claim_url")


def test_match_empty_no_params():
    r = requests.get(f"{BASE_URL}/api/buyers/match", timeout=30)
    assert r.status_code == 200
    d = r.json()
    cands = d.get("candidates") if isinstance(d, dict) else d
    assert cands == [] or cands is None or len(cands) == 0
