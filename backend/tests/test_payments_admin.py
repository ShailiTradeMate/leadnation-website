"""Payments admin transactions API + regression tests for payment routing."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://buyer-intel-10.preview.emergentagent.com").rstrip("/")
ADMIN_HEADERS = {"X-Admin-Token": "leadnation-admin-2026"}


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Admin transactions endpoint ---
class TestAdminTransactions:
    def test_list_returns_schema(self, api):
        r = api.get(f"{BASE_URL}/api/payments/admin/transactions", headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("transactions", "count", "paidCount", "revenueINR", "revenueUSD"):
            assert k in data, f"missing key: {k}"
        assert isinstance(data["transactions"], list)
        # Per-row schema check (skip if empty)
        if data["transactions"]:
            row = data["transactions"][0]
            expected = {"txnId", "gateway", "status", "plan", "amount", "currency", "userId", "createdAt"}
            missing = expected - set(row.keys())
            assert not missing, f"row missing keys: {missing}; got {list(row.keys())}"

    def test_filter_status_paid(self, api):
        r = api.get(f"{BASE_URL}/api/payments/admin/transactions?status=paid", headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for t in data.get("transactions", []):
            assert t.get("status") == "paid", f"expected paid; got {t.get('status')}"

    def test_filter_gateway_razorpay(self, api):
        r = api.get(f"{BASE_URL}/api/payments/admin/transactions?gateway=razorpay", headers=ADMIN_HEADERS, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for t in data.get("transactions", []):
            assert t.get("gateway") == "razorpay"

    def test_requires_admin(self, api):
        r = api.get(f"{BASE_URL}/api/payments/admin/transactions", timeout=30)
        assert r.status_code in (401, 403), f"expected auth block; got {r.status_code}"


# --- Payment routing regression ---
class TestPricingRouting:
    def test_pricing_in_razorpay(self, api):
        r = api.get(f"{BASE_URL}/api/payments/pricing?region=IN", timeout=30)
        assert r.status_code == 200
        assert r.json().get("gateway") == "razorpay"

    def test_pricing_intl_stripe(self, api):
        r = api.get(f"{BASE_URL}/api/payments/pricing?region=INTL", timeout=30)
        assert r.status_code == 200
        assert r.json().get("gateway") == "stripe"


class TestOrderCreation:
    def test_razorpay_order(self, api):
        r = api.post(
            f"{BASE_URL}/api/payments/razorpay/order",
            headers={"X-Trade-Session": "qa-pay-1", "Content-Type": "application/json"},
            json={"kind": "monthly", "region": "IN", "origin": "https://leadnation.app"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("order_id"), d
        assert d.get("key_id"), d
        assert d.get("amount") == 49900, d
        assert (d.get("currency") or "").upper() == "INR"

    def test_stripe_checkout(self, api):
        r = api.post(
            f"{BASE_URL}/api/payments/checkout",
            headers={"X-Trade-Session": "qa-pay-2", "Content-Type": "application/json"},
            json={"kind": "monthly", "region": "INTL", "origin": "https://leadnation.app"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        url = d.get("url") or d.get("checkout_url") or ""
        assert "stripe.com" in url, f"expected stripe url; got {d}"
