"""Iteration 19 — LeadNation Trade Command Center (Volume 1 completion).

Tests:
  * /api/projects — full CRUD, pin, duplicate, version, ownership isolation
  * /api/command-center/quote — FOB/CIF math, comparison, currency, incentives
  * /api/command-center/explain — formula + brain explanation
  * /api/command-center/compliance — documents + duty + narrative
  * /api/command-center/markets — sorted country list
"""
import os
import uuid

import pytest
import requests

def _read_frontend_env():
    try:
        with open('/app/frontend/.env') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return os.environ.get('REACT_APP_BACKEND_URL', '')

BASE = _read_frontend_env().rstrip('/') + '/api'
assert BASE.startswith('http'), "REACT_APP_BACKEND_URL not configured"

# Single fixed session UUID across all project tests (per review request)
SESSION_A = "test-iter19-" + uuid.uuid4().hex[:12]
SESSION_B = "test-iter19-other-" + uuid.uuid4().hex[:12]


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def created_id(s):
    """Create a single project that other project tests reuse."""
    r = s.post(f"{BASE}/projects",
               json={"title": "TEST_iter19_main", "product": "Rice", "hs": "100630",
                     "exporter": "356", "importer": "842", "marginPct": 15},
               headers={"X-Trade-Session": SESSION_A}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    pid = body["id"]
    yield pid
    # teardown
    try:
        s.delete(f"{BASE}/projects/{pid}", headers={"X-Trade-Session": SESSION_A}, timeout=15)
    except Exception:
        pass


# ==================== /api/projects ====================

def test_project_create_returns_health_summary_stage_timeline(s, created_id):
    r = s.get(f"{BASE}/projects/{created_id}",
              headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["id"] == created_id
    assert p["stage"] == "Created"
    assert isinstance(p.get("health"), dict)
    for k in ("overall", "profitability", "risk", "compliance", "documentation", "timeline", "cashFlow"):
        assert k in p["health"], f"missing health.{k}"
        assert "value" in p["health"][k] and "color" in p["health"][k]
    assert isinstance(p.get("summary"), dict)
    assert p["summary"]["stage"] == "Created"
    assert p["summary"]["nextAction"]  # non-empty
    assert isinstance(p.get("timeline"), list) and len(p["timeline"]) >= 1
    assert p["timeline"][0]["type"] == "created"


def test_project_list_owner_scoped(s, created_id):
    r = s.get(f"{BASE}/projects", headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["projects"]]
    assert created_id in ids


def test_project_ownership_isolation(s, created_id):
    """A different X-Trade-Session must NOT see another session's projects."""
    r = s.get(f"{BASE}/projects", headers={"X-Trade-Session": SESSION_B}, timeout=15)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()["projects"]]
    assert created_id not in ids
    # And direct GET must 404
    r2 = s.get(f"{BASE}/projects/{created_id}",
               headers={"X-Trade-Session": SESSION_B}, timeout=15)
    assert r2.status_code == 404


def test_project_update_appends_timeline(s, created_id):
    r = s.put(f"{BASE}/projects/{created_id}",
              json={"patch": {"marginPct": 20}, "activity": "Bumped margin to 20%"},
              headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["marginPct"] == 20
    assert any(t["text"] == "Bumped margin to 20%" for t in p["timeline"])


def test_project_pin_toggle(s, created_id):
    r1 = s.post(f"{BASE}/projects/{created_id}/pin",
                headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r1.status_code == 200
    assert r1.json()["pinned"] is True
    r2 = s.post(f"{BASE}/projects/{created_id}/pin",
                headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r2.json()["pinned"] is False


def test_project_duplicate(s, created_id):
    r = s.post(f"{BASE}/projects/{created_id}/duplicate",
               headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r.status_code == 200, r.text
    dup = r.json()
    assert dup["id"] != created_id
    assert "(copy)" in dup["title"]
    # cleanup
    s.delete(f"{BASE}/projects/{dup['id']}", headers={"X-Trade-Session": SESSION_A}, timeout=15)


def test_project_version(s, created_id):
    r = s.post(f"{BASE}/projects/{created_id}/version",
               json={"kind": "quote", "label": "v1", "snapshot": {"foo": "bar"}},
               headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["version"]["label"] == "v1"
    # Verify persisted
    g = s.get(f"{BASE}/projects/{created_id}", headers={"X-Trade-Session": SESSION_A}, timeout=15)
    versions = g.json().get("versions", [])
    assert any(v["label"] == "v1" for v in versions)


def test_project_delete_and_404(s):
    r = s.post(f"{BASE}/projects",
               json={"title": "TEST_iter19_to_delete", "product": "Rice", "hs": "100630"},
               headers={"X-Trade-Session": SESSION_A}, timeout=15)
    pid = r.json()["id"]
    d = s.delete(f"{BASE}/projects/{pid}",
                 headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert d.status_code == 200 and d.json()["ok"] is True
    g = s.get(f"{BASE}/projects/{pid}",
              headers={"X-Trade-Session": SESSION_A}, timeout=15)
    assert g.status_code == 404


# ==================== /api/command-center/quote ====================

@pytest.fixture(scope="module")
def quote_body():
    return {
        "hs": "100630", "product": "", "exporter": "356", "importer": "842",
        "quantity": 100, "unit": "unit",
        "costs": {"exw": 75, "packing": 1, "inland": 1.5, "thc": 2,
                  "customsDocs": 1, "freight": 5, "insurance": 0.1},
        "marginPct": 15, "transactionCurrency": "USD", "globalCurrency": "EUR",
        "incoterm": "FOB", "shipmentMode": "Sea FCL",
    }


@pytest.fixture(scope="module")
def quote_response(s, quote_body):
    r = s.post(f"{BASE}/command-center/quote", json=quote_body, timeout=90)
    assert r.status_code == 200, r.text
    return r.json()


def test_quote_ok_and_fob_cif_math(quote_response):
    q = quote_response
    assert q.get("ok") is True, q
    # Costs sum per-unit: 75+1+1.5+2+1=80.5 → FOB total = 80.5 * 100 = 8050
    assert abs(q["fob"]["total"] - 8050) < 1, f"fob.total={q['fob']['total']}"
    # CIF = FOB + freight + insurance per unit: (80.5 + 5 + 0.1) * 100 = 8560
    assert abs(q["cif"]["total"] - 8560) < 1, f"cif.total={q['cif']['total']}"


def test_quote_waterfall_has_9_rows(quote_response):
    wf = quote_response.get("waterfall", [])
    assert len(wf) == 9, f"waterfall len={len(wf)}"


def test_quote_destination_block(quote_response):
    d = quote_response.get("destination") or {}
    # dutyRate may be None if WITS returns nothing; vatRate and landed must be present
    assert "dutyRate" in d
    assert "vatRate" in d
    assert "landed" in d


def test_quote_comparison_sorted_ascending(quote_response):
    comp = quote_response.get("comparison", [])
    assert len(comp) >= 6, f"comparison has {len(comp)} markets"
    totals = [c["buyerTotal"] for c in comp]
    assert totals == sorted(totals), "comparison must be sorted ascending"


def test_quote_currency_converted(quote_response):
    c = quote_response.get("currency", {})
    assert c.get("transaction") == "USD"
    conv = c.get("converted", {})
    # converted is keyed by field (fob/cif/landed/selling), each carrying global + exporterLocal
    assert "fob" in conv and "cif" in conv
    assert "global" in conv["fob"] and "exporterLocal" in conv["fob"]
    assert "global" in conv["cif"] and "exporterLocal" in conv["cif"]


def test_quote_incentives_for_india_origin(quote_response):
    inc = quote_response.get("incentives", [])
    assert isinstance(inc, list) and len(inc) >= 1, f"incentives={inc}"


def test_quote_routes_present(quote_response):
    routes = quote_response.get("routes", [])
    assert isinstance(routes, list) and len(routes) >= 1


# ==================== /api/command-center/explain ====================

def test_explain_cif(s, quote_response):
    r = s.post(f"{BASE}/command-center/explain",
               json={"field": "cif", "quote": quote_response}, timeout=90)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert body.get("formula"), "missing formula"
    assert body.get("source"), "missing source"
    # Brain may be slow; allow empty explanation but field must exist
    assert "explanation" in body


# ==================== /api/command-center/compliance ====================

def test_compliance_documents_and_duty(s):
    r = s.post(f"{BASE}/command-center/compliance",
               json={"hs": "100630", "exporter": "356", "importer": "842", "incoterm": "FOB"},
               timeout=90)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    docs = body.get("documents", [])
    assert isinstance(docs, list) and len(docs) >= 5
    assert "Commercial Invoice" in docs
    # India exporter docs
    assert any("Shipping Bill" in d for d in docs)
    # narrative key exists (may be empty if brain timed out)
    assert "narrative" in body
    # duty block (may be None if WITS empty)
    assert "duty" in body


# ==================== /api/command-center/markets ====================

def test_markets_sorted(s):
    r = s.get(f"{BASE}/command-center/markets", timeout=30)
    assert r.status_code == 200
    cs = r.json().get("countries", [])
    assert len(cs) > 50
    names = [c["name"] for c in cs]
    assert names == sorted(names), "markets must be alphabetically sorted"
