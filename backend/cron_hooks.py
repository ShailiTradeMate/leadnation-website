"""Platform cron webhooks (.emergent/crons.yml). Bearer = WEBHOOK_CRON_SECRET; ack fast, work in background."""
import asyncio
import hmac
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request

from core import db

logger = logging.getLogger("cron")
router = APIRouter(prefix="/cron", tags=["cron"])


def _authorized(authorization: str | None) -> bool:
    secret = os.environ.get("WEBHOOK_CRON_SECRET", "")
    if not secret or not authorization or not authorization.startswith("Bearer "):
        return False
    return hmac.compare_digest(authorization[7:].strip(), secret)


async def _accept(request: Request, authorization: str | None, x_webhook_id: str | None, job: str, coro_factory):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    if not _authorized(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        body = await request.json() if await request.body() else {}
    except Exception:
        raise HTTPException(status_code=400, detail="invalid body")
    run_id = x_webhook_id or (body or {}).get("run_id") or f"{job}:{datetime.now(timezone.utc).isoformat()}"
    try:
        await db.cron_runs.insert_one({"_id": f"{job}:{run_id}", "job": job, "runId": run_id,
                                       "acceptedAt": datetime.now(timezone.utc).isoformat(), "status": "accepted"})
    except Exception:  # duplicate delivery → ack without re-running
        return {"ok": True, "duplicate": True, "runId": run_id}

    async def runner():
        try:
            result = await coro_factory(run_id)
            await db.cron_runs.update_one({"_id": f"{job}:{run_id}"}, {"$set": {"status": "done", "result": result,
                                                                               "finishedAt": datetime.now(timezone.utc).isoformat()}})
        except Exception as exc:
            logger.warning("cron %s failed: %s", job, exc)
            await db.cron_runs.update_one({"_id": f"{job}:{run_id}"}, {"$set": {"status": "failed", "error": str(exc)[:300]}})

    asyncio.create_task(runner())
    return {"ok": True, "accepted": True, "runId": run_id}


@router.post("/meta-token-check")
async def meta_token_check(request: Request, authorization: str | None = Header(default=None),
                           x_webhook_id: str | None = Header(default=None)):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    import meta_ads
    return await _accept(request, authorization, x_webhook_id, "meta-token-check", meta_ads.check_token_expiry)
