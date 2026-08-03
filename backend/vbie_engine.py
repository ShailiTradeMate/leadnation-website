"""VBIE Recurring Intelligence Engine — LeadNation's permanent continuous data pipeline.

Turns VBIE from one-time ingestion into a self-maintaining intelligence platform.
Everything runs on the ONE shared MongoDB, ONE GEID, ONE Brain — a single source of
truth consumed identically by the Website and Mobile App.

Cadences (configurable in Mongo `vbie_config._id='vbie_schedule'`):
  • WEEKLY  full refresh   (default Sun 02:00 UTC) — all approved connectors → dedupe →
                                                      brain recompute → change detection →
                                                      alerts → weekly report.
  • DAILY   incremental    (default 03:00 UTC)     — throttled LEI enrich + rolling brain
                                                      recompute + change detection + alerts
                                                      (no full source re-download).
  • MONTHLY bulk refresh   (default 1st 04:00 UTC) — heavy bulk datasets (Companies House
                                                      full register, France SIRENE) when
                                                      `bulk_enabled` is on.

Pipeline stages: legal precheck → incremental fetch → duplicate resolution (multi-key,
audit-preserving) → freshness → brain automation → change detection → alerts → report.
"""
import logging
from datetime import datetime, timezone, timedelta

from core import db
from vbie_core import (compute_trust, compute_confidence, compute_freshness,
                       source_reliability, _now, _iso, is_source_approved, _SOURCE_BY_ID)
import vbie_connectors as C

logger = logging.getLogger(__name__)

SCHEDULE_ID = "vbie_schedule"
DEFAULT_SCHEDULE = {
    "_id": SCHEDULE_ID,
    "enabled": True,
    "weekly": {"day_of_week": "sun", "hour": 2, "minute": 0},
    "daily": {"hour": 3, "minute": 0},
    "monthly": {"day": 1, "hour": 4, "minute": 0},
    "daily_lei_limit": 150,        # throttled GLEIF lookups per daily run
    "daily_brain_batch": 2500,     # rolling brain recompute batch per daily run
    "bulk_enabled": False,         # heavy bulk loaders (CH full file / SIRENE) — enable in prod
    "bulk_max_records": 5000,      # safety cap for bulk parse (raise in production)
    "subscriber_alerts": True,     # email watchers on buyer changes
}


# ─────────────────────────────── config ─────────────────────────────────────
async def get_schedule() -> dict:
    cfg = await db.vbie_config.find_one({"_id": SCHEDULE_ID})
    if not cfg:
        await db.vbie_config.insert_one(dict(DEFAULT_SCHEDULE))
        return dict(DEFAULT_SCHEDULE)
    merged = {**DEFAULT_SCHEDULE, **cfg}
    return merged


async def set_schedule(patch: dict) -> dict:
    allowed = {k: v for k, v in (patch or {}).items() if k in DEFAULT_SCHEDULE and k != "_id"}
    await db.vbie_config.update_one({"_id": SCHEDULE_ID}, {"$set": allowed}, upsert=True)
    return await get_schedule()


# ─────────────────────── legal compliance precheck ──────────────────────────
async def validate_sources_legal() -> dict:
    """Validate every source's licence/terms before sync. Auto-disable any connector
    whose `legal_status` is flagged non-compliant. Returns a per-source matrix."""
    out = {}
    for s in _SOURCE_BY_ID.values():
        sid = s["_id"]
        override = await db.vbie_sources.find_one({"_id": sid}, {"legal_status": 1})
        status = (override or {}).get("legal_status")
        approved = is_source_approved(sid) and status not in ("disabled", "revoked", "pending")
        out[sid] = {
            "source": s.get("name", sid), "tier": s.get("tier"),
            "attribution": s.get("attribution", ""),
            "approved": approved,
            "legal_status": status or ("approved" if is_source_approved(sid) else "pending_legal_approval"),
        }
    return out


async def can_run(source_id: str) -> bool:
    m = await validate_sources_legal()
    return bool(m.get(source_id, {}).get("approved"))


# ─────────────────────────── brain automation ───────────────────────────────
async def brain_recompute(rolling: int = None) -> dict:
    """Automatically recompute Trust · Confidence · Freshness · Source Reliability for
    buyers, re-screen sanctions, and detect dissolved/inactive companies. `rolling`
    limits how many (oldest-scored first) to process so the full corpus is covered over
    several runs without reprocessing everything nightly (enterprise-scale friendly)."""
    screener = await C.load_sanctions()
    q = {"entity_type": "buyer", "admin_deleted": {"$ne": True}}
    cur = db.entities.find(q, {"legal_name": 1, "provenance": 1, "signals": 1, "trust": 1,
                               "last_verified": 1, "updated_at": 1, "status": 1, "brain_scored_at": 1})
    if rolling:
        cur = cur.sort("brain_scored_at", 1).limit(rolling)
    updated = stale = dissolved = sanctioned = 0
    ops = []
    from pymongo import UpdateOne
    async for e in cur:
        prov = e.get("provenance", []); sig = dict(e.get("signals", {}))
        lv = e.get("last_verified") or _iso(e.get("updated_at"))
        fresh = compute_freshness(prov, lv)
        conf = compute_confidence(prov, sig)
        rel = source_reliability(prov)
        set_doc = {}
        # Sanctions re-screen (sources/rules change over time).
        if C.is_sanctioned(e.get("legal_name", ""), screener):
            sig["sanctions_clear"] = False; set_doc["status"] = "flagged"; sanctioned += 1
        # Dissolved / inactive detection from status signals.
        if sig.get("dissolved") or sig.get("inactive"):
            set_doc["status"] = "inactive"; dissolved += 1
        # Freshness-driven confidence decay: stale records lose trust.
        trust = compute_trust(prov, sig)
        if fresh["score"] < 55:
            trust["score"] = max(1, int(trust["score"]) - (55 - fresh["score"]) // 5)
            trust["band"] = "Emerging" if trust["score"] < 45 else trust.get("band")
            stale += 1
        set_doc.update({
            "signals": sig, "trust": trust,
            "freshness_score": fresh["score"], "freshness_label": fresh["label"],
            "confidence_score": conf["score"], "confidence_label": conf["label"],
            "reliability_label": rel["label"], "reliability_tier": rel["tier"],
            "last_source_sync": _iso(_now()), "brain_scored_at": _iso(_now()),
        })
        ops.append(UpdateOne({"_id": e["_id"]}, {"$set": set_doc}))
        updated += 1
        if len(ops) >= 500:
            await db.entities.bulk_write(ops, ordered=False); ops = []
    if ops:
        await db.entities.bulk_write(ops, ordered=False)
    logger.info("Brain recompute: updated=%d stale=%d dissolved=%d sanctioned=%d", updated, stale, dissolved, sanctioned)
    return {"updated": updated, "stale": stale, "dissolved": dissolved, "sanctioned": sanctioned}


# ─────────────────────────── change detection ───────────────────────────────
_SNAP_FIELDS = ["status", "city", "legal_name", "lei", "sector"]


async def detect_changes(rolling: int = None) -> list:
    """Compare each buyer against its last snapshot; record status/address/name/legal/
    identity changes into `vbie_changes`. First pass sets a baseline (no changes)."""
    q = {"entity_type": "buyer", "admin_deleted": {"$ne": True}}
    proj = {f: 1 for f in _SNAP_FIELDS}; proj["_snap"] = 1; proj["products"] = 1; proj["corridors"] = 1
    cur = db.entities.find(q, proj)
    if rolling:
        cur = cur.sort("brain_scored_at", 1).limit(rolling)
    changes = []
    from pymongo import UpdateOne
    ops = []
    async for e in cur:
        prev = e.get("_snap") or {}
        cur_snap = {f: e.get(f) for f in _SNAP_FIELDS}
        cur_snap["products_n"] = len(e.get("products", []))
        cur_snap["corridors_n"] = len(e.get("corridors", []))
        if prev:
            diffs = {}
            label_map = {"status": "legal_status", "city": "address", "legal_name": "name",
                         "lei": "identity", "sector": "industry",
                         "products_n": "trade_activity", "corridors_n": "trade_corridor"}
            for k, cv in cur_snap.items():
                pv = prev.get(k)
                if pv is not None and pv != cv:
                    diffs[label_map.get(k, k)] = {"from": pv, "to": cv}
            if diffs:
                change = {"geid": e["_id"], "diffs": diffs, "at": _iso(_now())}
                changes.append(change)
                await db.vbie_changes.insert_one(dict(change))
        ops.append(UpdateOne({"_id": e["_id"]}, {"$set": {"_snap": cur_snap}}))
        if len(ops) >= 500:
            await db.entities.bulk_write(ops, ordered=False); ops = []
    if ops:
        await db.entities.bulk_write(ops, ordered=False)
    logger.info("Change detection: %d buyer changes recorded", len(changes))
    return changes


# ───────────────────── buyer change alerts (watchlist) ──────────────────────
async def fire_change_alerts(changes: list) -> dict:
    """Notify subscribers who watch a buyer when its status/address/trade activity
    changes (in-app notification + best-effort Resend email)."""
    cfg = await get_schedule()
    notified = emailed = 0
    for ch in changes:
        geid = ch["geid"]
        e = await db.entities.find_one({"_id": geid}, {"legal_name": 1})
        name = (e or {}).get("legal_name", "A watched buyer")
        summary = ", ".join(f"{k} changed" for k in ch["diffs"].keys())
        async for w in db.buyer_watchlist.find({"geid": geid}):
            uid = w.get("uid")
            await db.notifications.insert_one({
                "audience": "user", "uid": uid, "scope": "watch", "kind": "buyer_changed",
                "title": f"Update on {name}", "body": f"{name}: {summary}.",
                "meta": {"geid": geid, "diffs": ch["diffs"]}, "created_at": _iso(_now())})
            notified += 1
            if cfg.get("subscriber_alerts") and w.get("email"):
                try:
                    from emailer import send
                    await send("buyer_changed", w["email"],
                               {"buyer": name, "summary": summary, "geid": geid})
                    emailed += 1
                except Exception as exc:
                    logger.warning("Change-alert email failed: %s", exc)
    return {"notified": notified, "emailed": emailed}


# ─────────────────────── weekly intelligence report ─────────────────────────
async def build_weekly_report(period_days: int = 7) -> dict:
    since = _now() - timedelta(days=period_days)
    since_iso = _iso(since)
    buyer_q = {"entity_type": "buyer", "admin_deleted": {"$ne": True}}

    new_buyers = await db.entities.count_documents({**buyer_q, "created_at": {"$gte": since}})
    updated = await db.entities.count_documents({**buyer_q, "updated_at": {"$gte": since}})
    dissolved = await db.entities.count_documents({**buyer_q, "status": "inactive"})
    flagged = await db.entities.count_documents({**buyer_q, "status": "flagged"})
    changes_n = await db.vbie_changes.count_documents({"at": {"$gte": since_iso}})

    # Duplicates merged/removed from recent ingest runs.
    merged = removed = 0
    failed_connectors = []
    runs = await db.vbie_ingest_runs.find({"started_at": {"$gte": since_iso}}).sort("started_at", -1).to_list(20)
    for r in runs:
        d = r.get("dedupe") or {}
        merged += int(d.get("merged", 0)); removed += int(d.get("hard_deleted", 0))
        for sid, n in (r.get("sources") or {}).items():
            if n == 0 and sid not in failed_connectors:
                failed_connectors.append(sid)

    # New countries / industries among buyers added this period.
    new_country_names = await db.entities.distinct("country_name", {**buyer_q, "created_at": {"$gte": since}})
    new_industries = await db.entities.distinct("sector", {**buyer_q, "created_at": {"$gte": since}})

    # Data-quality score via production audit (read-only summary).
    dq = None
    try:
        import vbie_admin
        audit = await vbie_admin.production_audit(auto_fix=False)
        dq = audit.get("data_quality_score") or audit.get("score")
    except Exception:
        pass

    total = await db.entities.count_documents(buyer_q)
    lei_cov = await db.entities.count_documents({**buyer_q, "lei": {"$nin": ["", None]}})

    report = {
        "_id": f"wk-{_now().strftime('%Y%m%d-%H%M')}",
        "generated_at": _iso(_now()), "period_days": period_days, "period_start": since_iso,
        "metrics": {
            "new_buyers": new_buyers, "buyers_updated": updated,
            "duplicates_merged": merged, "duplicate_records_removed": removed,
            "companies_dissolved_or_inactive": dissolved, "companies_flagged_sanctions": flagged,
            "changes_detected": changes_n,
            "new_countries": sorted([c for c in new_country_names if c]),
            "new_industries": sorted([s for s in new_industries if s]),
            "failed_connectors": failed_connectors,
            "data_quality_score": dq,
            "total_buyers": total, "lei_coverage": lei_cov,
            "lei_coverage_pct": round(100 * lei_cov / total, 1) if total else 0,
        },
        "sync_summary": [{"trigger": r.get("trigger"), "at": r.get("started_at"),
                          "sources": r.get("sources"), "new": r.get("new_buyers")} for r in runs[:5]],
    }
    await db.vbie_reports.insert_one(dict(report))

    # Email the report to admin (best-effort).
    try:
        from emailer import notify_admin
        m = report["metrics"]
        await notify_admin("weekly_report", {
            "new_buyers": m["new_buyers"], "updated": m["buyers_updated"],
            "merged": m["duplicates_merged"], "removed": m["duplicate_records_removed"],
            "dissolved": m["companies_dissolved_or_inactive"], "total": m["total_buyers"],
            "lei_pct": m["lei_coverage_pct"]})
    except Exception as exc:
        logger.warning("Weekly report admin email failed: %s", exc)
    return report


# ─────────────────────────── recurring cycles ───────────────────────────────
async def run_full_cycle(trigger: str = "weekly") -> dict:
    logger.info("VBIE FULL cycle start (trigger=%s)", trigger)
    ingest = await C.run_ingestion(trigger=trigger)          # connectors → dedupe → audit
    brain = await brain_recompute(rolling=None)               # full recompute after full refresh
    changes = await detect_changes()
    alerts = await fire_change_alerts(changes)
    report = await build_weekly_report()
    cycle = {"_id": f"cycle-{_now().strftime('%Y%m%d-%H%M%S')}", "type": "full", "trigger": trigger,
             "at": _iso(_now()), "ingest": {k: ingest.get(k) for k in ("sources", "new_buyers", "dedupe", "real_total")},
             "brain": brain, "changes": len(changes), "alerts": alerts, "report_id": report["_id"]}
    await db.vbie_cycles.insert_one(dict(cycle))
    logger.info("VBIE FULL cycle done")
    return cycle


async def run_incremental(trigger: str = "daily") -> dict:
    logger.info("VBIE INCREMENTAL cycle start (trigger=%s)", trigger)
    cfg = await get_schedule()
    lei = await C.connector_gleif_enrich(limit=cfg.get("daily_lei_limit", 150))
    brain = await brain_recompute(rolling=cfg.get("daily_brain_batch", 2500))
    changes = await detect_changes(rolling=cfg.get("daily_brain_batch", 2500))
    alerts = await fire_change_alerts(changes)
    cycle = {"_id": f"cycle-{_now().strftime('%Y%m%d-%H%M%S')}", "type": "incremental", "trigger": trigger,
             "at": _iso(_now()), "lei_matched": lei, "brain": brain,
             "changes": len(changes), "alerts": alerts}
    await db.vbie_cycles.insert_one(dict(cycle))
    logger.info("VBIE INCREMENTAL cycle done")
    return cycle


async def run_bulk_monthly(trigger: str = "monthly") -> dict:
    logger.info("VBIE MONTHLY bulk cycle start (trigger=%s)", trigger)
    cfg = await get_schedule()
    out = {"bulk_enabled": cfg.get("bulk_enabled", False), "sources": {}}
    if cfg.get("bulk_enabled"):
        cap = cfg.get("bulk_max_records", 5000)
        for sid, fn in (("uk_companies_house_bulk", C.connector_companies_house_bulk),
                        ("sirene_fr", C.connector_sirene)):
            try:
                rows = await fn(max_records=cap)
                out["sources"][sid] = len(rows)
                await C.upsert_candidates(rows, source_label=sid)
            except Exception as exc:
                logger.warning("Bulk connector %s failed: %s", sid, exc)
                out["sources"][sid] = 0
        await C.dedupe_and_prune()
        out["brain"] = await brain_recompute(rolling=None)
    cycle = {"_id": f"cycle-{_now().strftime('%Y%m%d-%H%M%S')}", "type": "bulk", "trigger": trigger,
             "at": _iso(_now()), **out}
    await db.vbie_cycles.insert_one(dict(cycle))
    logger.info("VBIE MONTHLY bulk cycle done")
    return cycle


# ─────────────────────────────── scheduler ──────────────────────────────────
_scheduler = None


async def _boot_schedule():
    global _scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    cfg = await get_schedule()
    if _scheduler:
        _scheduler.shutdown(wait=False)
    _scheduler = AsyncIOScheduler(timezone="UTC")
    if cfg.get("enabled", True):
        w, d, m = cfg["weekly"], cfg["daily"], cfg["monthly"]
        _scheduler.add_job(run_full_cycle, CronTrigger(day_of_week=w["day_of_week"], hour=w["hour"], minute=w["minute"]),
                           args=["weekly"], id="vbie_weekly_full", replace_existing=True, max_instances=1)
        _scheduler.add_job(run_incremental, CronTrigger(hour=d["hour"], minute=d["minute"]),
                           args=["daily"], id="vbie_daily_incremental", replace_existing=True, max_instances=1)
        _scheduler.add_job(run_bulk_monthly, CronTrigger(day=m["day"], hour=m["hour"], minute=m["minute"]),
                           args=["monthly"], id="vbie_monthly_bulk", replace_existing=True, max_instances=1)
    _scheduler.start()
    logger.info("VBIE recurring intelligence scheduler started (weekly/daily/monthly, enabled=%s)", cfg.get("enabled", True))


def start_scheduler():
    try:
        import asyncio
        asyncio.get_event_loop().create_task(_boot_schedule())
    except Exception as exc:
        logger.warning("Could not start VBIE engine scheduler: %s", exc)


async def reload_scheduler():
    await _boot_schedule()
