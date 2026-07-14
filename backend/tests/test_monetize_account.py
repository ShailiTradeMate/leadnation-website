"""Backend tests for iteration 22: monetize (payments/downloads) + account (profile/buyers/invoices/admin)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://trade-beyond-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _new_session():
    return str(uuid.uuid4())


def _headers(sid):
    return {"X-Trade-Session": sid, "Content-Type": "application/json"}


# ---------- Pricing ----------
class TestPricing:
    def test_pricing_in(self):
        r = requests.get(f"{API}/payments/pricing", params={"region": "IN"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["region"] == "IN"
        assert d["download"] == {"amount": 25.0, "currency": "inr"}
        assert d["subscription"] == {"amount": 499.0, "currency": "inr"}
        assert d["razorpayEnabled"] is False
        assert d["gateway"] == "stripe"

    def test_pricing_intl(self):
        r = requests.get(f"{API}/payments/pricing", params={"region": "INTL"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["region"] == "INTL"
        assert d["download"] == {"amount": 1.0, "currency": "usd"}
        assert d["subscription"] == {"amount": 9.0, "currency": "usd"}
        assert d["razorpayEnabled"] is False


# ---------- Downloads first-free ----------
class TestDownloadsFirstFree:
    def test_first_free_then_paywalled(self):
        sid = _new_session()
        h = _headers(sid)

        # Initial check - allowed & free
        r = requests.get(f"{API}/downloads/check", params={"region": "IN"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["allowed"] is True
        assert d["freeAvailable"] is True
        assert d["totalDownloads"] == 0
        assert d["region"] == "IN"
        assert d["price"] == 25.0

        # Record the free download
        r = requests.post(f"{API}/downloads/record",
                          json={"projectId": "p1", "projectTitle": "t", "region": "IN"},
                          headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["free"] is True
        assert d["paid"] is False

        # Second check - not free anymore
        r = requests.get(f"{API}/downloads/check", params={"region": "IN"}, headers=h, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["allowed"] is False
        assert d["freeAvailable"] is False
        assert d["totalDownloads"] == 1


# ---------- Stripe checkout ----------
class TestCheckout:
    def test_download_checkout_intl(self):
        sid = _new_session()
        h = _headers(sid)
        # First, consume free download so paid path is meaningful (not required)
        payload = {"kind": "download", "region": "INTL", "projectId": "p1",
                   "origin": "https://trade-beyond-2.preview.emergentagent.com"}
        r = requests.post(f"{API}/payments/checkout", json=payload, headers=h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["amount"] == 1.0
        assert d["currency"] == "usd"
        assert d["sessionId"]
        assert d["url"].startswith("https://checkout.stripe.com/")

        # status
        r = requests.get(f"{API}/payments/status/{d['sessionId']}", timeout=20)
        assert r.status_code == 200
        s = r.json()
        assert s["kind"] == "download"
        assert s["amount"] == 1.0
        assert s["currency"] == "usd"
        assert s["status"] in ("initiated", "expired")  # unpaid

    def test_subscription_checkout_intl(self):
        sid = _new_session()
        payload = {"kind": "subscription", "region": "INTL", "projectId": "",
                   "origin": "https://trade-beyond-2.preview.emergentagent.com"}
        r = requests.post(f"{API}/payments/checkout", json=payload, headers=_headers(sid), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["amount"] == 9.0
        assert d["currency"] == "usd"
        assert d["url"].startswith("https://checkout.stripe.com/")


# ---------- Account ----------
class TestAccount:
    def test_me_guest_and_flow(self):
        sid = _new_session()
        h = _headers(sid)

        # Initial /me
        r = requests.get(f"{API}/account/me", headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["profile"]["guest"] is True
        assert "referral" in d and d["referral"]["code"].startswith("LN")
        assert d["referral"]["link"]
        assert d["stats"]["downloads"] == 0
        assert d["stats"]["projects"] == 0

        # free download
        r = requests.post(f"{API}/downloads/record",
                          json={"projectId": "p1", "projectTitle": "t", "region": "IN"},
                          headers=h, timeout=15)
        assert r.status_code == 200

        # /me now shows 1 download
        r = requests.get(f"{API}/account/me", headers=h, timeout=15)
        d = r.json()
        assert d["stats"]["downloads"] == 1
        assert len(d["downloads"]) == 1
        assert d["stats"]["spend"] == 0  # free download

        # Update profile
        r = requests.put(f"{API}/account/profile",
                         json={"role": "Exporter", "country": "IN", "mobile": "999"},
                         headers=h, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True

        # Verify persistence
        r = requests.get(f"{API}/account/me", headers=h, timeout=15)
        p = r.json()["profile"]
        assert p["role"] == "Exporter"
        assert p["country"] == "IN"
        assert p["mobile"] == "999"

        # Invoices should be empty (free download)
        r = requests.get(f"{API}/account/invoices", headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json()["invoices"] == []

    def test_buyers_crud(self):
        sid = _new_session()
        h = _headers(sid)

        # empty
        r = requests.get(f"{API}/account/buyers", headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json()["buyers"] == []

        # add
        r = requests.post(f"{API}/account/buyers",
                         json={"name": "ACME", "country": "US", "product": "rice"},
                         headers=h, timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b["name"] == "ACME"
        assert b["country"] == "US"
        assert b["product"] == "rice"
        bid = b["id"]
        assert bid

        # list
        r = requests.get(f"{API}/account/buyers", headers=h, timeout=15)
        buyers = r.json()["buyers"]
        assert len(buyers) == 1
        assert buyers[0]["id"] == bid

        # delete
        r = requests.delete(f"{API}/account/buyers/{bid}", headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # verify removed
        r = requests.get(f"{API}/account/buyers", headers=h, timeout=15)
        assert r.json()["buyers"] == []


# ---------- Admin protection ----------
class TestAdminProtected:
    def test_admin_users_requires_auth(self):
        r = requests.get(f"{API}/account/admin/users", timeout=15)
        assert r.status_code in (401, 403, 422), f"Expected 401/403/422, got {r.status_code}"
