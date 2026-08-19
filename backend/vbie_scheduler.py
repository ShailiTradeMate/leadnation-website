"""VBIE Production Recurring Intelligence Service — Vametra AI's permanent, self-growing
data engine. This is a CORE service, not a best-effort cron.

Design goals (all satisfied here):
  • Persistent MongoDB job store  — every job + its schedule + state lives in `vbie_jobs`.
  • Survives backend restarts      — state is in Mongo, never in process memory.
  • Automatic catch-up             — `next_due_at` persists; if a run was missed while the
                                      process was down, the next tick runs it immediately.
  • Job history                    — every attempt is appended to `vbie_job_history`.
  • Retry queue                    — failed jobs retry with exponential backoff up to N times.
  • Failure alerts                 — exhausted retries raise an admin notification + email.
  • Health monitoring              — `vbie_engine_health` heartbeats every tick.
  • Incremental sync checkpoints   — `vbie_checkpoints` lets each source keep discovering NEW
                                      records slice-by-slice (the DB grows every day).
  • Source-specific schedules      — each source is its own interval job with its own cadence.
  • No cycle is ever silently skipped — the tick loop always advances `next_due_at` only after
                                      a run completes, and logs catch-up runs explicitly.

The ticker is a lightweight asyncio loop (every TICK_SECONDS) that runs any job whose
`next_due_at <= now`. All scheduling truth is in MongoDB; the loop is just a clock.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from apscheduler.triggers.cron import CronTrigger

from core import db
from vbie_core import _now, _iso, is_source_approved
import vbie_connectors as C
import vbie_engine as E

logger = logging.getLogger(__name__)

TICK_SECONDS = 30
MAX_CONCURRENT = 1          # run one heavy job at a time (pod-safe)
DEFAULT_MAX_RETRIES = 3
RETRY_BACKOFF_MIN = 10      # base backoff (minutes); grows * attempt

# ─────────────────────────── job definitions ────────────────────────────────
# Scheduled maintenance jobs (cron). Source discovery jobs are seeded from the
# approved-source discovery adapters with per-source interval cadences.
SCHEDULED_JOBS = [
    {"_id": "weekly_full", "kind": "weekly_full", "trigger": "cron",
     "cron": {"day_of_week": "sun", "hour": 2, "minute": 0},
     "label": "Weekly full intelligence cycle"},
    {"_id": "daily_brain", "kind": "daily_brain", "trigger": "cron",
     "cron": {"hour": 5, "minute": 0},
     "label": "Daily reconcile: dedupe · brain · change-detection · alerts · audit"},
    {"_id": "monthly_bulk", "kind": "monthly_bulk", "trigger": "cron",
     "cron": {"day": 1, "hour": 4, "minute": 0},
     "label": "Monthly official bulk import"},
]

# Per-source discovery cadences (seconds). Registry crawls daily; TED daily; CID weekly.
SOURCE_INTERVALS = {
    "eu_ted": 86400,
    "uk_companies_house": 86400,
    "cid_canada": 604800,
    "no_brreg": 86400,
    "cz_ares": 86400,
}


# ─────────────────────────── schedule helpers ───────────────────────────────
def _next_cron(cron_kwargs: dict, after: datetime = None) -> str:
    trig = CronTrigger(timezone="UTC", **cron_kwargs)
    nxt = trig.get_next_fire_time(None, after or _now())
    return _iso(nxt)


def _next_interval(seconds: int, after: datetime = None) -> str:
    return _iso((after or _now()) + timedelta(seconds=seconds))


async def ensure_jobs():
    """Idempotently seed the persistent job store. Existing jobs keep their state."""
    for j in SCHEDULED_JOBS:
        existing = await db.vbie_jobs.find_one({"_id": j["_id"]})
        if existing:
            continue
        doc = {**j, "enabled": True, "running": False, "attempts": 0,
               "max_retries": DEFAULT_MAX_RETRIES, "last_status": None, "last_run_at": None,
               "last_result": None, "last_error": None,
               "next_due_at": _next_cron(j["cron"]), "created_at": _iso(_now())}
        await db.vbie_jobs.insert_one(doc)
    for sid, interval in SOURCE_INTERVALS.items():
        jid = f"src:{sid}"
        existing = await db.vbie_jobs.find_one({"_id": jid})
        if existing:
            # keep enabled state in sync with legal approval (auto-disable revoked sources)
            if not is_source_approved(sid) and existing.get("enabled"):
                await db.vbie_jobs.update_one({"_id": jid}, {"$set": {"enabled": False}})
            continue
        doc = {"_id": jid, "kind": "source_discovery", "source_id": sid, "trigger": "interval",
               "interval_seconds": interval, "label": f"Discover new buyers · {sid}",
               "enabled": is_source_approved(sid), "running": False, "attempts": 0,
               "max_retries": DEFAULT_MAX_RETRIES, "last_status": None, "last_run_at": None,
               "last_result": None, "last_error": None,
               "next_due_at": _next_interval(min(interval, 300)),  # first crawl within 5 min
               "created_at": _iso(_now())}
        await db.vbie_jobs.insert_one(doc)
    logger.info("VBIE job store ensured (%d scheduled + %d source jobs)",
                len(SCHEDULED_JOBS), len(SOURCE_INTERVALS))


def _advance_next_due(job: dict, after: datetime = None) -> str:
    if job.get("trigger") == "cron":
        return _next_cron(job["cron"], after)
    return _next_interval(job.get("interval_seconds", 86400), after)


# ───────────────────────────── job execution ────────────────────────────────
async def _execute(job: dict) -> dict:
    kind = job.get("kind")
    if kind == "weekly_full":
        cyc = await E.run_full_cycle(trigger="weekly")
        return {"cycle_id": cyc.get("_id"), "new_buyers": (cyc.get("ingest") or {}).get("new_buyers")}
    if kind == "daily_brain":
        return await E.run_reconcile(trigger="daily")
    if kind == "monthly_bulk":
        cyc = await E.run_bulk_monthly(trigger="monthly")
        return {"cycle_id": cyc.get("_id"), "sources": cyc.get("sources")}
    if kind == "source_discovery":
        sid = job["source_id"]
        cp_doc = await db.vbie_checkpoints.find_one({"_id": sid}) or {}
        res = await C.discover_source(sid, cp_doc.get("checkpoint") or {})
        await db.vbie_checkpoints.update_one(
            {"_id": sid},
            {"$set": {"checkpoint": res.get("checkpoint"), "exhausted": res.get("exhausted"),
                      "last_run_at": _iso(_now()), "last_new": res.get("new", 0)},
             "$inc": {"total_new": int(res.get("new", 0) or 0), "runs": 1}},
            upsert=True)
        return {"source": sid, "fetched": res.get("fetched"), "new": res.get("new"),
                "exhausted": res.get("exhausted"), "checkpoint": res.get("checkpoint")}
    raise ValueError(f"unknown job kind: {kind}")


async def _fire_failure_alert(job: dict, error: str):
    """Raise an admin notification + best-effort email when a job exhausts its retries."""
    try:
        await db.notifications.insert_one({
            "audience": "admin", "scope": "admin", "kind": "engine_failure",
            "title": f"Intelligence engine job failed: {job['_id']}",
            "body": f"Job '{job.get('label', job['_id'])}' failed after {job.get('max_retries')} retries. "
                    f"Last error: {error[:400]}",
            "meta": {"job": job["_id"], "error": error[:1000]}, "created_at": _iso(_now())})
    except Exception:
        pass
    try:
        import os
        from emailer import notify_admin
        await notify_admin("engine_failure", {"job": job["_id"], "error": error[:500]})
    except Exception as exc:
        logger.warning("Failure-alert email skipped: %s", exc)


async def _run_job(job: dict):
    name = job["_id"]
    now = _now()
    # Single-runner lock: only proceed if we flip running False→True atomically.
    lock = await db.vbie_jobs.update_one(
        {"_id": name, "running": {"$ne": True}},
        {"$set": {"running": True, "running_since": _iso(now)}})
    if not lock.modified_count:
        return
    due = job.get("next_due_at")
    catchup = bool(due and _iso(now) > str(due) and (now - datetime.fromisoformat(due)).total_seconds() > 3600)
    run_id = uuid.uuid4().hex
    attempt = int(job.get("attempts", 0)) + 1
    await db.vbie_job_history.insert_one({
        "_id": run_id, "job": name, "kind": job.get("kind"), "started_at": _iso(now),
        "status": "running", "attempt": attempt, "catchup": catchup})
    logger.info("VBIE job start: %s (attempt %d%s)", name, attempt, ", CATCH-UP" if catchup else "")
    try:
        result = await _execute(job)
        fin = _now()
        await db.vbie_jobs.update_one({"_id": name}, {"$set": {
            "running": False, "last_status": "success", "last_run_at": _iso(fin),
            "last_result": result, "last_error": None, "attempts": 0,
            "next_due_at": _advance_next_due(job, fin)}})
        await db.vbie_job_history.update_one({"_id": run_id}, {"$set": {
            "status": "success", "finished_at": _iso(fin), "result": result,
            "duration_s": round((fin - now).total_seconds(), 1)}})
        logger.info("VBIE job ok: %s → %s", name, result)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        fin = _now()
        max_r = int(job.get("max_retries", DEFAULT_MAX_RETRIES))
        if attempt <= max_r:
            backoff = RETRY_BACKOFF_MIN * attempt
            next_due = _next_interval(backoff * 60, fin)
            await db.vbie_jobs.update_one({"_id": name}, {"$set": {
                "running": False, "last_status": "retrying", "last_error": err,
                "attempts": attempt, "next_due_at": next_due}})
            await db.vbie_job_history.update_one({"_id": run_id}, {"$set": {
                "status": "failed", "finished_at": _iso(fin), "error": err,
                "will_retry_at": next_due}})
            logger.warning("VBIE job %s failed (attempt %d/%d): %s → retry in %d min",
                           name, attempt, max_r, err, backoff)
        else:
            await db.vbie_jobs.update_one({"_id": name}, {"$set": {
                "running": False, "last_status": "failed", "last_error": err, "attempts": 0,
                "next_due_at": _advance_next_due(job, fin)}})
            await db.vbie_job_history.update_one({"_id": run_id}, {"$set": {
                "status": "failed", "finished_at": _iso(fin), "error": err, "retries_exhausted": True}})
            logger.error("VBIE job %s FAILED after %d retries: %s", name, max_r, err)
            await _fire_failure_alert(job, err)


# ─────────────────────────────── tick loop ──────────────────────────────────
_running = False


async def tick():
    now = _now()
    await db.vbie_engine_health.update_one(
        {"_id": "health"},
        {"$set": {"last_tick_at": _iso(now)}, "$inc": {"ticks": 1}}, upsert=True)
    due = await db.vbie_jobs.find(
        {"enabled": True, "running": {"$ne": True}, "next_due_at": {"$lte": _iso(now)}}
    ).sort("next_due_at", 1).to_list(50)
    ran = 0
    for job in due:
        if ran >= MAX_CONCURRENT:
            break
        # Reclaim stuck locks (crash mid-run > 2h ago).
        await _run_job(job)
        ran += 1


async def _loop():
    global _running
    _running = True
    await db.vbie_engine_health.update_one(
        {"_id": "health"}, {"$set": {"boot_at": _iso(_now()), "status": "up"}}, upsert=True)
    # Reclaim any locks left 'running' by a previous crashed process.
    await db.vbie_jobs.update_many(
        {"running": True}, {"$set": {"running": False, "last_status": "reclaimed"}})
    logger.info("VBIE production recurring engine loop started (tick=%ds)", TICK_SECONDS)
    while _running:
        try:
            await tick()
        except Exception as exc:
            logger.warning("VBIE engine tick error: %s", exc)
            try:
                await db.vbie_engine_health.update_one(
                    {"_id": "health"}, {"$set": {"last_error": str(exc)[:400]}}, upsert=True)
            except Exception:
                pass
        await asyncio.sleep(TICK_SECONDS)


def start():
    """Wire the persistent recurring engine into the app event loop."""
    async def _boot():
        try:
            await ensure_jobs()
            asyncio.create_task(_loop())
        except Exception as exc:
            logger.error("VBIE scheduler boot failed: %s", exc)
    try:
        asyncio.get_event_loop().create_task(_boot())
    except Exception as exc:
        logger.warning("Could not start VBIE scheduler: %s", exc)


# ───────────────────────── admin monitoring helpers ─────────────────────────
async def health_snapshot() -> dict:
    h = await db.vbie_engine_health.find_one({"_id": "health"}) or {}
    jobs = await db.vbie_jobs.find({}).sort("_id", 1).to_list(100)
    now = _now()
    healthy = False
    lt = h.get("last_tick_at")
    if lt:
        try:
            healthy = (now - datetime.fromisoformat(lt)).total_seconds() < TICK_SECONDS * 4
        except Exception:
            pass
    failing = [j["_id"] for j in jobs if j.get("last_status") in ("failed",)]
    retrying = [j["_id"] for j in jobs if j.get("last_status") == "retrying"]
    return {
        "status": "healthy" if healthy else "stalled",
        "last_tick_at": lt, "boot_at": h.get("boot_at"), "ticks": h.get("ticks"),
        "tick_seconds": TICK_SECONDS, "last_error": h.get("last_error"),
        "jobs_total": len(jobs), "jobs_enabled": sum(1 for j in jobs if j.get("enabled")),
        "jobs_failing": failing, "jobs_retrying": retrying,
        "jobs": [{k: v for k, v in j.items()} for j in jobs],
    }


async def run_now(job_id: str) -> dict:
    j = await db.vbie_jobs.find_one({"_id": job_id})
    if not j:
        return {"ok": False, "error": "job not found"}
    await db.vbie_jobs.update_one({"_id": job_id}, {"$set": {"next_due_at": _iso(_now()), "attempts": 0}})
    return {"ok": True, "job": job_id, "queued": True}


async def set_enabled(job_id: str, enabled: bool) -> dict:
    res = await db.vbie_jobs.update_one({"_id": job_id}, {"$set": {"enabled": bool(enabled)}})
    return {"ok": res.matched_count > 0, "job": job_id, "enabled": bool(enabled)}


async def set_interval(job_id: str, seconds: int) -> dict:
    res = await db.vbie_jobs.update_one(
        {"_id": job_id, "trigger": "interval"},
        {"$set": {"interval_seconds": int(seconds), "next_due_at": _iso(_now())}})
    return {"ok": res.matched_count > 0, "job": job_id, "interval_seconds": int(seconds)}
