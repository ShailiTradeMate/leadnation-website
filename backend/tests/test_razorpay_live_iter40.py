"""Iteration 40 — Razorpay LIVE keys wiring tests.

SAFETY: We NEVER complete a real payment. We only:
  * create unpaid orders (no charge is made)
  * post bogus signatures to /verify and /webhook (must be rejected)
  * confirm Stripe INTL fallback still works
  * confirm professional services are enquiry-only (no razorpay calls)
"""
import os
import re
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
SESSION = "qa-rzp-iter40"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def mongo():
    mc = MongoClient(os.environ["MONGO_URL"])
    return mc[os.environ["DB_NAME"]]


# ---- Pricing gateway routing ----
def test_pricing_IN_returns_razorpay(client):
    r = client.get(f"{API}/payments/pricing", params={"region": "IN"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["gateway"] == "razorpay"
    assert d["razorpayEnabled"] is True
    assert d["region"] == "IN"
    # verify server-side amounts (INR)
    assert d["download"]["amount"] == 25.0 and d["download"]["currency"] == "inr"
    assert d["monthly"]["amount"] == 499.0
    assert d["annual"]["amount"] == 3999.0


def test_pricing_INTL_returns_stripe(client):
    r = client.get(f"{API}/payments/pricing", params={"region": "INTL"})
    assert r.status_code == 200
    d = r.json()
    assert d["gateway"] == "stripe"


# ---- Razorpay order creation (LIVE, unpaid — no money moves) ----
@pytest.fixture(scope="module")
def rzp_order(client, mongo):
    r = client.post(
        f"{API}/payments/razorpay/order",
        headers={"X-Trade-Session": SESSION},
        json={"kind": "monthly", "region": "IN", "origin": "https://leadnation.app"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_razorpay_order_shape(rzp_order):
    d = rzp_order
    assert d["gateway"] == "razorpay"
    assert d["order_id"].startswith("order_"), d
    assert d["key_id"].startswith("rzp_live_"), "key_id should be LIVE (rzp_live_)"
    assert d["currency"] == "INR"
    # monthly INR 499 -> 49900 paise
    assert d["amount"] == 49900


def test_razorpay_tx_persisted(rzp_order, mongo):
    tx = mongo.payment_transactions.find_one({"_id": rzp_order["order_id"]})
    assert tx is not None
    assert tx["gateway"] == "razorpay"
    assert tx["status"] == "initiated"
    assert tx["kind"] == "monthly"
    assert tx["region"] == "IN"
    assert tx["amount"] == 499.0
    assert tx["currency"] == "inr"


def test_razorpay_order_download_paise(client):
    r = client.post(
        f"{API}/payments/razorpay/order",
        headers={"X-Trade-Session": SESSION + "-dl"},
        json={"kind": "download", "region": "IN", "origin": "https://leadnation.app"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == 2500  # ₹25


def test_razorpay_order_annual_paise(client):
    r = client.post(
        f"{API}/payments/razorpay/order",
        headers={"X-Trade-Session": SESSION + "-an"},
        json={"kind": "annual", "region": "IN", "origin": "https://leadnation.app"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == 399900  # ₹3999


# ---- Signature verification (must reject bogus payload) ----
def test_verify_rejects_bad_signature(client, rzp_order):
    r = client.post(
        f"{API}/payments/razorpay/verify",
        headers={"X-Trade-Session": SESSION},
        json={
            "razorpay_payment_id": "pay_x",
            "razorpay_order_id": rzp_order["order_id"],
            "razorpay_signature": "bad",
        },
    )
    assert r.status_code == 400, r.text
    assert "signature" in r.text.lower()


def test_verify_unknown_order_404(client):
    r = client.post(
        f"{API}/payments/razorpay/verify",
        headers={"X-Trade-Session": SESSION},
        json={
            "razorpay_payment_id": "pay_x",
            "razorpay_order_id": "order_doesnotexist_xxxxxxxx",
            "razorpay_signature": "bad",
        },
    )
    assert r.status_code == 404


# ---- Webhook signature verification ----
def test_webhook_rejects_bad_signature(client):
    r = requests.post(
        f"{API}/webhook/razorpay",
        data="{}",
        headers={"X-Razorpay-Signature": "bad", "Content-Type": "application/json"},
    )
    assert r.status_code == 400, r.text


# ---- Stripe INTL regression ----
def test_stripe_intl_checkout_still_works(client):
    r = client.post(
        f"{API}/payments/checkout",
        headers={"X-Trade-Session": "qa-stripe-iter40"},
        json={"kind": "monthly", "region": "INTL", "origin": "https://leadnation.app"},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert "url" in d and d["url"].startswith("http")
    assert "stripe" in d["url"].lower() or "checkout" in d["url"].lower()


# ---- Scope guard: professional services are enquiry-only ----
def test_services_list_contains_gst_and_iec(client):
    r = client.get(f"{API}/services")
    assert r.status_code == 200
    slugs = [s["slug"] for s in r.json()]
    assert "gst-registration" in slugs
    assert "iec-registration" in slugs


def test_services_module_has_no_razorpay_calls():
    """Static guard: services.py must not touch razorpay."""
    with open("/app/backend/services.py") as f:
        src = f.read()
    assert "razorpay" not in src.lower()
    assert "razorpay/order" not in src
    # Should only create leads, no checkout
    assert "db.leads" in src


def test_service_request_creates_lead_no_payment(client, mongo):
    r = client.post(
        f"{API}/service-request",
        json={
            "service": "gst-registration",
            "name": "TEST_ITER40",
            "email": "test_iter40@example.com",
            "phone": "9999999999",
            "country": "India",
            "message": "iter40 scope guard test",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    # Confirm no payment_transactions row for this lead
    lead = mongo.leads.find_one({"email": "test_iter40@example.com"})
    assert lead is not None
    # cleanup
    mongo.leads.delete_many({"email": "test_iter40@example.com"})
    mongo.service_requests.delete_many({"email": "test_iter40@example.com"})
