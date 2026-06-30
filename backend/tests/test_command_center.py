"""Tests for LeadNation Trade Command Center — quote, markets, insights."""
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-brain-ai.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

QUOTE_BODY = {
    "hs": "100630",
    "exporter": "356",
    "importer": "276",
    "quantity": 1000,
    "costs": {"exw": 75, "packing": 1, "inland": 1.5, "thc": 2, "customsDocs": 1, "freight": 5, "insurance": 0.1},
    "marginPct": 15,
    "transactionCurrency": "INR",
    "globalCurrency": "USD",
}


@pytest.fixture(scope="module")
def quote_response():
    r = requests.post(f"{API}/command-center/quote", json=QUOTE_BODY, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True, data
    return data


# /command-center/quote main happy path
def test_quote_ok_and_fob_cif(quote_response):
    q = quote_response
    assert q["hsCode"] == "100630"
    # FOB = (75+1+1.5+2+1)*1000 = 80500
    assert q["fob"]["total"] == 80500, q["fob"]
    # CIF = (80.5+5+0.1)*1000 = 85600
    assert q["cif"]["total"] == 85600, q["cif"]
    assert q["fob"]["perUnit"] == 80.5
    assert q["cif"]["perUnit"] == 85.6


def test_waterfall_has_9_rows_with_milestones(quote_response):
    wf = quote_response["waterfall"]
    assert len(wf) == 9, [w["stage"] for w in wf]
    milestones = [w for w in wf if w.get("milestone")]
    stages = [m["stage"] for m in milestones]
    assert "FOB Value" in stages and "CIF Value" in stages


def test_destination_duty_vat_landed(quote_response):
    d = quote_response["destination"]
    assert "dutyRate" in d and "vatRate" in d
    assert isinstance(d["landed"], (int, float))
    # Germany VAT = 19%
    assert d["vatRate"] == 19


def test_comparison_sorted_ascending(quote_response):
    comp = quote_response["comparison"]
    assert isinstance(comp, list) and len(comp) >= 1
    totals = [c["buyerTotal"] for c in comp]
    assert totals == sorted(totals)
    for c in comp:
        assert "code" in c and "country" in c and "cif" in c


def test_currency_conversion_global_and_local(quote_response):
    cur = quote_response["currency"]
    assert cur["transaction"] == "INR"
    assert cur["global"] == "USD"
    assert cur["exporterLocal"] == "INR"
    conv = cur["converted"]
    for key in ("fob", "cif", "landed", "selling"):
        assert key in conv
        # global is USD — must be present
        assert conv[key]["global"] is not None, f"{key}.global is None"


def test_incentives_india_origin(quote_response):
    inc = quote_response["incentives"]
    assert isinstance(inc, list) and len(inc) >= 2
    schemes = [i["scheme"] for i in inc]
    assert any("GST" in s for s in schemes)


def test_routes_present(quote_response):
    routes = quote_response["routes"]
    assert isinstance(routes, list) and len(routes) >= 3
    modes = [r["mode"] for r in routes]
    assert any("Sea" in m for m in modes) and any("Air" in m for m in modes)


# Validation: missing hs AND product
def test_quote_missing_hs_and_product_returns_error():
    body = {**QUOTE_BODY, "hs": "", "product": ""}
    r = requests.post(f"{API}/command-center/quote", json=body, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is False
    assert "error" in data


# Resolution via product name
def test_quote_resolves_via_product_name():
    body = {**QUOTE_BODY, "hs": "", "product": "rice"}
    r = requests.post(f"{API}/command-center/quote", json=body, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True, data
    assert data.get("hsCode") and len(data["hsCode"]) >= 6


# /command-center/markets
def test_markets_sorted_list():
    r = requests.get(f"{API}/command-center/markets", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "countries" in data
    countries = data["countries"]
    assert isinstance(countries, list) and len(countries) >= 50
    names = [c["name"] for c in countries]
    assert names == sorted(names)
    for c in countries[:5]:
        assert "code" in c and "name" in c


# /command-center/insights — Brain wired
def test_insights_live_grounded(quote_response):
    r = requests.post(f"{API}/command-center/insights", json={"quote": quote_response}, timeout=90)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True, data
    advisor = data.get("advisor", "")
    assert isinstance(advisor, str) and len(advisor) > 100, f"advisor too short: {advisor!r}"
    assert data.get("live") is True, f"expected live brain: {data}"
    # Grounded — should reference Germany or HS or numbers from quote
    t = advisor.lower()
    grounded = ("germany" in t) or ("100630" in advisor) or ("85600" in advisor) or ("80500" in advisor) or ("cif" in t)
    assert grounded, f"advisor not grounded: {advisor[:400]}"
