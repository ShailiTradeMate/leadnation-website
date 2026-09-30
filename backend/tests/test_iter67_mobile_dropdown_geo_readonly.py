"""
Iteration 67 — Read-only API regression checks for mobile dropdown geo rollout.
Modules: countries/geo coverage, news country filters, expo filters/list, trade-news, brain ask.
"""

import os
import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="REACT_APP_BACKEND_URL is required")
API = f"{BASE_URL.rstrip('/')}/api"


def _get(path: str, **kwargs):
    return requests.get(f"{API}{path}", timeout=60, **kwargs)


def _post(path: str, **kwargs):
    return requests.post(f"{API}{path}", timeout=90, **kwargs)


def test_countries_has_250_and_required_records():
    r = _get("/countries")
    assert r.status_code == 200
    data = r.json()
    countries = data if isinstance(data, list) else data.get("countries", [])
    assert isinstance(countries, list)
    assert len(countries) >= 250

    by_code = {c.get("code"): c for c in countries if isinstance(c, dict)}
    for code in ["PS", "VA", "AM", "ZW", "CA", "US", "IN", "FR"]:
        assert code in by_code
        assert by_code[code].get("name")


def test_news_countries_endpoint_shape():
    r = _get("/news/countries")
    assert r.status_code == 200
    data = r.json()
    rows = data.get("countries") if isinstance(data, dict) else data
    assert isinstance(rows, list)
    assert len(rows) >= 200
    assert "code" in rows[0] and "name" in rows[0]


@pytest.mark.parametrize("cc", ["am", "fr", "in", "us"])
def test_news_feed_accepts_lowercase_iso_country(cc):
    r = _get("/news/feed", params={"country": cc, "topic": "all"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "items" in data


def test_trade_news_endpoint_works():
    r = _get("/trade-news")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


def test_expo_filters_endpoint_has_countries():
    r = _get("/events/filters")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert isinstance(data.get("countries"), list)
    assert len(data.get("countries")) > 0


@pytest.mark.parametrize("country", ["India", "IN", "United Arab Emirates", "UAE", "Armenia", "France"])
def test_expo_list_accepts_country_values_and_aliases(country):
    r = _get("/events/list", params={"country": country})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert ("items" in data) or ("events" in data)


def test_brain_ask_accepts_origin_destination_country_names():
    payload = {
        "question": "Compare export basics for spices from India to France",
        "mode": "product",
        "session_id": "iter67-dropdown-geo-readonly",
        "product": "Spices",
        "origin": "India",
        "destination": "France",
    }
    r = _post("/brain/ask", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert bool(data.get("answer"))
