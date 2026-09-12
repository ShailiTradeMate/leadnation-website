"""Iter 58 (MOCKED) — registry-matching unit coverage with isolated fake DB fixtures.

MOCKED scope only: no real government-buyer inserts and no live remote dependencies.
"""

import types
import sys
import anyio

sys.path.insert(0, "/app/backend")

import pytest

import buyer_membership as bm


class _AsyncCursor:
    def __init__(self, rows):
        self.rows = rows

    def limit(self, _n):
        return self

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self.rows):
            raise StopAsyncIteration
        row = self.rows[self._i]
        self._i += 1
        return row


class _Entities:
    def __init__(self, rows):
        self.rows = rows

    def find(self, *_args, **_kwargs):
        return _AsyncCursor(self.rows)


def test_mocked_registry_candidate_missing_fields_returns_none(monkeypatch):
    fake_db = types.SimpleNamespace(entities=_Entities([]))
    monkeypatch.setattr(bm, "db", fake_db)

    profile = {
        "email": "u@example.com",
        "mobile": None,
        "country": "India",
        "company_details": {"company_name": "Acme Pvt Ltd"},
    }
    out = anyio.run(bm.registry_candidate, profile)
    assert out is None


def test_mocked_registry_candidate_ambiguous_returns_none(monkeypatch):
    rows = [
        {
            "geid": "LN-prospect-A",
            "legal_name": "Acme Pvt. Ltd.",
            "country": "IN",
            "country_name": "India",
            "contact": {"email": "owner@acme.com", "phone": "+919876543210"},
            "provenance": [{"source_id": "x"}],
        },
        {
            "geid": "LN-prospect-B",
            "legal_name": "Acme Pvt. Ltd.",
            "country": "IN",
            "country_name": "India",
            "contact": {"email": "owner@acme.com", "phone": "+91 98765 43210"},
            "provenance": [{"source_id": "y"}],
        },
    ]
    fake_db = types.SimpleNamespace(entities=_Entities(rows))
    monkeypatch.setattr(bm, "db", fake_db)

    profile = {
        "email": "owner@acme.com",
        "mobile": "09876543210",
        "country": "India",
        "company_details": {"company_name": "Acme Pvt Ltd"},
    }
    out = anyio.run(bm.registry_candidate, profile)
    assert out is None


def test_mocked_registry_candidate_unicode_name_and_phone_normalization(monkeypatch):
    rows = [
        {
            "geid": "LN-prospect-UNICODE",
            "legal_name": "ＡＣＭＥ Pvt. Ltd",
            "country": "IN",
            "country_name": "India",
            "contact": {"email": "unicode@acme.com", "phone": "+91-98765-43210"},
            "provenance": [{"source_id": "gov"}],
        }
    ]
    fake_db = types.SimpleNamespace(entities=_Entities(rows))
    monkeypatch.setattr(bm, "db", fake_db)

    profile = {
        "email": "unicode@acme.com",
        "mobile": "9876543210",
        "country": "India",
        "company_details": {"company_name": "acme pvt ltd"},
    }
    out = anyio.run(bm.registry_candidate, profile)
    assert out is not None
    assert out["geid"] == "LN-prospect-UNICODE"


def test_mocked_accept_match_requires_unique_candidate(monkeypatch):
    async def _fake_check(_user, _authorization=None):
        return {"match": None, "status": "manual_verification"}

    monkeypatch.setattr(bm, "check_match", _fake_check)
    with pytest.raises(Exception) as exc:
        anyio.run(bm.accept_match, {"uid": "U1"}, None)
    assert "No unique registry match" in str(exc.value)
