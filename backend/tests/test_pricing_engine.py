"""Iteration 23 — Centralized Pricing Engine + monetization integration tests.

Verifies /api/pricing/* endpoints (public + admin), admin auth via X-Admin-Token,
plan mutation persistence & validation, event/lead tracking, and downstream
monetization (payments.pricing, downloads.check, payments.checkout) reading the
engine dynamically. Resets any mutated values back to defaults at end.
"""
import os
import uuid
import requests
import pytest
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
ADMIN = {"X-Admin-Token": "leadnation-admin-2026"}
SESSION = uuid.uuid4().hex
GUEST = {"X-Trade-Session": SESSION}


# ---- /api/pricing/config ----
def test_config_IN_shape():
    r = requests.get(f"{BASE}/pricing/config", params={"region": "IN"})
    assert r.status_code == 200
    d = r.json()
    assert d["region"] == "IN"
    assert d["symbol"] == "\u20b9"
    assert d["currency"] == "inr"
    keys = {p["key"] for p in d["plans"]}
    assert {"download", "monthly", "annual"}.issubset(keys)
    assert d["settings"].get("mostPopular") == "annual"
    assert d["settings"].get("freeFirstDownload") is True
    assert d["settings"].get("emailCaptureBeforePaywall") is True
    assert isinstance(d["features"], list) and len(d["features"]) > 0
    assert isinstance(d["annualSavingsPct"], int)
    assert d["gateway"] in ("stripe", "razorpay")


def test_config_INTL_shape():
    r = requests.get(f"{BASE}/pricing/config", params={"region": "INTL"})
    assert r.status_code == 200
    d = r.json()
    assert d["region"] == "INTL"
    assert d["symbol"] == "$"
    assert d["currency"] == "usd"


# ---- /api/pricing/admin GET auth ----
def test_admin_get_requires_token():
    r = requests.get(f"{BASE}/pricing/admin")
    assert r.status_code == 401


def test_admin_get_with_token():
    r = requests.get(f"{BASE}/pricing/admin", headers=ADMIN)
    assert r.status_code == 200
    d = r.json()
    assert "plans" in d and "currencies" in d and "settings" in d
    assert d["plans"]["monthly"]["IN"] == 499


# ---- /api/pricing/admin PUT: mutate + persist + reset ----
def test_admin_update_persists_and_validation():
    # Mutate monthly IN to 599
    r = requests.put(f"{BASE}/pricing/admin", headers=ADMIN,
                     json={"plans": {"monthly": {"IN": 599}}})
    assert r.status_code == 200, r.text
    assert r.json()["config"]["plans"]["monthly"]["IN"] == 599

    # Persisted on subsequent GET
    r = requests.get(f"{BASE}/pricing/config", params={"region": "IN"})
    m = next(p for p in r.json()["plans"] if p["key"] == "monthly")
    assert m["amount"] == 599

    # Also flows through to payments.pricing
    r = requests.get(f"{BASE}/payments/pricing", params={"region": "IN"})
    assert r.status_code == 200
    assert r.json()["monthly"]["amount"] == 599

    # Negative price rejected
    r = requests.put(f"{BASE}/pricing/admin", headers=ADMIN,
                     json={"plans": {"monthly": {"IN": -5}}})
    assert r.status_code == 400

    # RESET back to default 499
    r = requests.put(f"{BASE}/pricing/admin", headers=ADMIN,
                     json={"plans": {"monthly": {"IN": 499}}})
    assert r.status_code == 200
    assert r.json()["config"]["plans"]["monthly"]["IN"] == 499


# ---- /api/pricing/track + /lead ----
def test_track_paywall_view():
    r = requests.post(f"{BASE}/pricing/track", headers=GUEST,
                      json={"event": "paywall_view", "plan": "monthly", "region": "IN"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_lead_capture_valid_and_invalid():
    good = f"test_{SESSION[:8]}@example.com"
    r = requests.post(f"{BASE}/pricing/lead", headers=GUEST,
                      json={"email": good, "region": "IN", "source": "paywall"})
    assert r.status_code == 200
    # invalid
    r = requests.post(f"{BASE}/pricing/lead", headers=GUEST,
                      json={"email": "not-an-email", "region": "IN"})
    assert r.status_code == 400


# ---- /api/pricing/admin/analytics ----
def test_admin_analytics():
    r = requests.get(f"{BASE}/pricing/admin/analytics", headers=ADMIN)
    assert r.status_code == 200
    d = r.json()
    assert "funnel" in d
    assert isinstance(d["emailCaptures"], int) and d["emailCaptures"] >= 1
    assert "conversionPct" in d


# ---- Monetization integration ----
def test_payments_pricing_reads_engine():
    r = requests.get(f"{BASE}/payments/pricing", params={"region": "IN"})
    assert r.status_code == 200
    d = r.json()
    assert d["download"]["amount"] == 25 and d["download"]["currency"] == "inr"
    assert d["monthly"]["amount"] == 499
    assert d["annual"]["amount"] == 3999
    assert d["gateway"] == "stripe"

    r = requests.get(f"{BASE}/payments/pricing", params={"region": "INTL"})
    d = r.json()
    assert d["download"]["amount"] == 1 and d["download"]["currency"] == "usd"
    assert d["monthly"]["amount"] == 9
    assert d["annual"]["amount"] == 79


def test_downloads_check_free_first_intl():
    fresh = {"X-Trade-Session": uuid.uuid4().hex}
    r = requests.get(f"{BASE}/downloads/check", params={"region": "INTL"}, headers=fresh)
    assert r.status_code == 200
    d = r.json()
    assert d["freeAvailable"] is True
    assert d["allowed"] is True
    assert d["price"] == 1
    assert d["currency"] == "usd"
    assert d["region"] == "INTL"


def test_checkout_annual_monthly_and_invalid():
    origin = "https://example.com"
    # annual
    r = requests.post(f"{BASE}/payments/checkout", headers=GUEST,
                      json={"kind": "annual", "region": "IN", "origin": origin})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["amount"] == 3999 and d["currency"] == "inr"
    assert d["url"].startswith("https://") and "stripe" in d["url"]

    # monthly
    r = requests.post(f"{BASE}/payments/checkout", headers=GUEST,
                      json={"kind": "monthly", "region": "INTL", "origin": origin})
    assert r.status_code == 200
    d = r.json()
    assert d["amount"] == 9 and d["currency"] == "usd"

    # invalid kind
    r = requests.post(f"{BASE}/payments/checkout", headers=GUEST,
                      json={"kind": "bogus", "region": "IN", "origin": origin})
    assert r.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
