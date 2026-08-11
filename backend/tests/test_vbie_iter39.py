"""VBIE Iteration 39 - Persistent recurring engine + new sources (Norway/Czechia) + CH bulk phases + auto-updating filters."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://payments-cms.preview.emergentagent.com').rstrip('/')
ADMIN_HEADERS = {"X-Admin-Token": "leadnation-admin-2026"}
TIMEOUT = 60


# ---------- Engine health / history / checkpoints ----------
def test_engine_health():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/engine/health", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    print("HEALTH:", {k: d.get(k) for k in ("status","jobs_total","jobs_enabled","jobs_failing")})
    assert d.get("status") == "healthy", f"Expected healthy, got {d.get('status')}"
    assert d.get("jobs_total") == 8, f"jobs_total={d.get('jobs_total')}"
    assert d.get("jobs_enabled") == 8, f"jobs_enabled={d.get('jobs_enabled')}"
    failing = d.get("jobs_failing") or []
    assert failing == [] or len(failing) == 0, f"jobs_failing not empty: {failing}"


def test_engine_history():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/engine/history", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    hist = d.get("history") if isinstance(d, dict) else d
    assert isinstance(hist, list), f"history is not a list: {type(hist)}"
    print(f"HISTORY: {len(hist)} entries; sample={hist[:2] if hist else 'empty'}")
    if hist:
        statuses = {h.get("status") for h in hist}
        print(f"statuses seen: {statuses}")


def test_engine_checkpoints():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/engine/checkpoints", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    cps = d.get("checkpoints") if isinstance(d, dict) else d
    # accept list or dict-of-src
    keys = set()
    if isinstance(cps, dict):
        keys = set(cps.keys())
    elif isinstance(cps, list):
        keys = {c.get("source") or c.get("_id") or c.get("id") for c in cps}
    print("CHECKPOINT KEYS:", keys)
    expected = {"eu_ted", "uk_companies_house", "no_brreg", "cz_ares", "cid_canada"}
    missing = expected - keys
    assert not missing, f"missing checkpoints: {missing}"


# ---------- Jobs run/toggle ----------
def test_job_run_no_brreg():
    r = requests.post(f"{BASE_URL}/api/buyers/admin/engine/jobs/src:no_brreg/run", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    print("RUN no_brreg:", d)
    assert d.get("ok") is True
    assert d.get("queued") is True


def test_job_toggle_no_brreg_enable():
    # ensure enabled=true (do not disable persistently)
    r = requests.post(
        f"{BASE_URL}/api/buyers/admin/engine/jobs/src:no_brreg/toggle",
        headers=ADMIN_HEADERS, json={"enabled": True}, timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    print("TOGGLE no_brreg enable:", d)
    assert d.get("ok") is True


# ---------- CH bulk phases ----------
def test_bulk_phases_shape():
    r = requests.get(f"{BASE_URL}/api/buyers/admin/bulk/phases", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    print("PHASES:", d)
    assert d.get("phase_targets") == [100000, 500000, 1000000, 5000000]
    assert isinstance(d.get("phases"), list)


def test_bulk_run_phase_invalid_target():
    # target is a query param on this endpoint
    r = requests.post(
        f"{BASE_URL}/api/buyers/admin/bulk/run-phase",
        headers=ADMIN_HEADERS, params={"target": 12345}, timeout=TIMEOUT,
    )
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"


# ---------- Public meta / search ----------
def test_meta_includes_norway_czechia():
    r = requests.get(f"{BASE_URL}/api/buyers/meta", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    countries = d.get("countries") or []
    print(f"COUNTRIES ({len(countries)}): sample={countries[:15]}")
    assert "Norway" in countries, "Norway missing from countries"
    assert "Czechia" in countries, "Czechia missing from countries"
    sectors = d.get("sectors") or []
    corridors = d.get("corridors") or []
    trust = d.get("trust_bands") or []
    print(f"sectors={len(sectors)}, corridors={len(corridors)}, trust_bands={len(trust)}")
    assert len(sectors) > 0
    assert len(corridors) >= 30, f"expected >=30 corridors, got {len(corridors)}"
    assert len(trust) > 0


def test_search_norway():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"country": "Norway"}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    items = d.get("buyers") or d.get("items") or []
    print(f"Norway buyers: {len(items)}; total={d.get('total')}")
    assert len(items) > 0 or (d.get("total") or 0) > 0, "no Norway buyers returned"


def test_search_czechia():
    r = requests.get(f"{BASE_URL}/api/buyers/search", params={"country": "Czechia"}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    d = r.json()
    items = d.get("buyers") or d.get("items") or []
    print(f"Czechia buyers: {len(items)}; total={d.get('total')}")
    assert len(items) > 0 or (d.get("total") or 0) > 0, "no Czechia buyers returned"


# ---------- Production audit ----------
def test_production_audit():
    r = requests.post(
        f"{BASE_URL}/api/buyers/admin/production-audit",
        headers=ADMIN_HEADERS, params={"auto_fix": "true"}, timeout=120,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    print("AUDIT:", {k: d.get(k) for k in ("active_production_buyers","quarantined_total","total","summary")})
    active = d.get("active_production_buyers") or d.get("active") or 0
    quar = d.get("quarantined_total") or d.get("quarantined") or 0
    assert active > 13000, f"active_production_buyers={active}"
    # allow small quarantines but Norway/Czech must not be quarantined
    quar_sources = d.get("quarantined_by_source") or {}
    print("quarantined_by_source:", quar_sources)
    for bad in ("no_brreg", "cz_ares"):
        assert quar_sources.get(bad, 0) == 0, f"{bad} quarantined!"
