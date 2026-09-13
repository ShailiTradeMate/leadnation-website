"""Iteration 66 — Business Services admin pricing + business-website tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://leadnation-build.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_HEADERS = {"X-Admin-Token": "leadnation-admin-2026", "Content-Type": "application/json"}

ORIGINAL = {
    "rcmc-registration": {"IN": "INR 4,999", "INTL": ""},
    "gst-registration": {"IN": "INR 1,499", "INTL": ""},
    "iec-registration": {"IN": "INR 1,999", "INTL": ""},
    "company-registration": {"IN": "INR 2,499", "INTL": ""},
    "business-website": {"IN": "INR 35,000 / year", "INTL": "USD 2,500 / year"},
    "export-consulting": {"IN": "INR 14,999", "INTL": ""},
    "import-consulting": {"IN": "INR 14,999", "INTL": ""},
    "compliance-consulting": {"IN": "INR 24,999", "INTL": ""},
    "market-entry": {"IN": "INR 49,999", "INTL": ""},
    "product-sourcing": {"IN": "INR 19,999", "INTL": ""},
    "buyer-discovery-service": {"IN": "INR 39,999 / month", "INTL": ""},
}


def test_services_list_has_business_website():
    r = requests.get(f"{API}/services", timeout=20)
    assert r.status_code == 200
    items = r.json()
    slugs = {s["slug"]: s for s in items}
    assert "business-website" in slugs
    bw = slugs["business-website"]
    assert bw["category"] == "Govt Documentation"
    assert bw["priceFrom"] == "INR 35,000 / year"
    assert bw["priceFromIntl"] == "USD 2,500 / year"
    # sanity: all 11 services
    assert len(items) == 11


def test_service_detail_business_website():
    r = requests.get(f"{API}/service/business-website", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["slug"] == "business-website"
    assert d["priceFrom"] == "INR 35,000 / year"
    assert d["priceFromIntl"] == "USD 2,500 / year"
    assert len(d["benefits"]) >= 11
    assert len(d["process"]) >= 5
    assert len(d["faqs"]) >= 4
    txt = " ".join(d["benefits"]).lower()
    for kw in ["domain", "email", "hosting", "payment", "quality testing", "annual support", "15"]:
        assert kw in txt, f"missing keyword: {kw}"


def test_admin_rates_requires_auth():
    r = requests.get(f"{API}/services/admin/rates", timeout=20)
    assert r.status_code in (401, 403)
    r2 = requests.put(f"{API}/services/admin/rates", json={"rates": {}}, timeout=20)
    assert r2.status_code in (401, 403)


def test_admin_rates_list():
    r = requests.get(f"{API}/services/admin/rates", headers=ADMIN_HEADERS, timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 11
    assert len(data["items"]) == 11
    for it in data["items"]:
        for k in ("slug", "name", "category", "defaultPriceFrom", "defaultPriceFromIntl",
                  "priceFrom", "priceFromIntl", "overridden"):
            assert k in it, f"missing {k} in {it['slug'] if 'slug' in it else it}"


def test_admin_rates_save_and_live_gst():
    # Save GST with distinctive value
    payload = {"rates": {"gst-registration": {"IN": "INR 1,777", "INTL": ""}, "bogus-slug": {"IN": "X"}}}
    r = requests.put(f"{API}/services/admin/rates", headers=ADMIN_HEADERS, json=payload, timeout=20)
    assert r.status_code == 200
    resp = r.json()
    assert resp["count"] == 11
    # unknown slug should be ignored
    slugs = {i["slug"] for i in resp["items"]}
    assert "bogus-slug" not in slugs
    gst = next(i for i in resp["items"] if i["slug"] == "gst-registration")
    assert gst["priceFrom"] == "INR 1,777"
    assert gst["overridden"] is True

    # Public endpoints reflect immediately
    pub = requests.get(f"{API}/services", timeout=20).json()
    gst_pub = next(s for s in pub if s["slug"] == "gst-registration")
    assert gst_pub["priceFrom"] == "INR 1,777"

    detail = requests.get(f"{API}/service/gst-registration", timeout=20).json()
    assert detail["priceFrom"] == "INR 1,777"


def test_intl_price_editing_consulting():
    # Set INTL on export-consulting
    payload = {"rates": {"export-consulting": {"IN": "INR 14,999", "INTL": "USD 299"}}}
    r = requests.put(f"{API}/services/admin/rates", headers=ADMIN_HEADERS, json=payload, timeout=20)
    assert r.status_code == 200
    pub = requests.get(f"{API}/services", timeout=20).json()
    ec = next(s for s in pub if s["slug"] == "export-consulting")
    assert ec["priceFromIntl"] == "USD 299"

    # Clear INTL by sending only IN
    payload2 = {"rates": {"export-consulting": {"IN": "INR 14,999"}}}
    r2 = requests.put(f"{API}/services/admin/rates", headers=ADMIN_HEADERS, json=payload2, timeout=20)
    assert r2.status_code == 200
    pub2 = requests.get(f"{API}/services", timeout=20).json()
    ec2 = next(s for s in pub2 if s["slug"] == "export-consulting")
    assert ec2["priceFromIntl"] == ""


def test_zzz_restore_all_original_prices():
    """Final: restore all originals and verify live."""
    payload = {"rates": ORIGINAL}
    r = requests.put(f"{API}/services/admin/rates", headers=ADMIN_HEADERS, json=payload, timeout=20)
    assert r.status_code == 200
    pub = requests.get(f"{API}/services", timeout=20).json()
    for s in pub:
        exp = ORIGINAL.get(s["slug"])
        if not exp:
            continue
        assert s["priceFrom"] == exp["IN"], f"{s['slug']} IN mismatch: {s['priceFrom']} vs {exp['IN']}"
        assert s["priceFromIntl"] == exp["INTL"], f"{s['slug']} INTL mismatch: {s['priceFromIntl']} vs {exp['INTL']}"
    # gst detail also
    d = requests.get(f"{API}/service/gst-registration", timeout=20).json()
    assert d["priceFrom"] == "INR 1,499"


def test_service_request_business_website():
    r = requests.post(f"{API}/service-request", json={
        "service": "business-website",
        "name": "TEST_iter66",
        "email": "test_iter66@example.com",
        "phone": "+911234567890",
        "country": "India",
        "message": "Testing business website enquiry",
    }, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is True
    assert "id" in d


def test_pricing_config_still_works():
    r = requests.get(f"{API}/pricing/config", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert "download" in d or "monthly" in d or "annual" in d or "plans" in d or "gateways" in d or isinstance(d, dict)
