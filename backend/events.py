"""Universal Audit Trail — every important activity becomes a timestamped event.

Permanent architecture: events live in their own collection (`trade_project_events`),
keyed by projectId + owner. Any module can call `log_event(...)`. The Trade Command
Center, Brain and PDF all read from here for the activity timeline / audit appendix.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import APIRouter, Header

from core import db
from projects import _owner

router = APIRouter(prefix="/events")
EVT = db.trade_project_events

# Canonical event types (open set — new types may be added freely).
EVENT_TYPES = [
    "project_created", "scenario_created", "scenario_updated", "scenario_compared",
    "scenario_merged", "scenario_archived", "simulation_executed", "brain_recommendation",
    "recommendation_accepted", "recommendation_ignored", "risk_changed", "quote_generated",
    "pdf_generated", "document_uploaded", "route_changed", "buyer_changed", "supplier_changed",
    "currency_changed", "decision_computed", "admin_action", "subscription_change",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_event(project_id: str, owner: str, etype: str,
                    text: str = "", meta: Optional[Dict[str, Any]] = None) -> dict:
    doc = {"_id": uuid.uuid4().hex, "id": uuid.uuid4().hex, "projectId": project_id,
           "owner": owner, "type": etype, "text": text, "meta": meta or {}, "at": _now()}
    try:
        await EVT.insert_one(doc)
    except Exception:
        pass
    return {k: v for k, v in doc.items() if k != "_id"}


@router.get("")
async def list_events(projectId: str = "", limit: int = 200,
                      authorization: Optional[str] = Header(default=None),
                      x_trade_session: Optional[str] = Header(default=None)):
    owner, _t = _owner(authorization, x_trade_session)
    query = {"owner": owner}
    if projectId:
        query["projectId"] = projectId
    docs = await EVT.find(query).sort("at", -1).to_list(min(limit, 500))
    return {"events": [{k: v for k, v in d.items() if k != "_id"} for d in docs]}
