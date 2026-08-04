import asyncio, os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

async def main():
    c = AsyncIOMotorClient(MONGO_URL)
    db = c[DB_NAME]
    now = datetime.now(timezone.utc)
    today0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week0 = now - timedelta(days=7)
    buyer_q = {"entity_type": "buyer", "admin_deleted": {"$ne": True}}

    total = await db.entities.count_documents(buyer_q)
    print("TOTAL buyers:", total)

    # created_at may be datetime or iso string; test both
    for label, dt in [("TODAY", today0), ("7-DAYS", week0)]:
        n_dt = await db.entities.count_documents({**buyer_q, "created_at": {"$gte": dt}})
        iso = dt.isoformat()
        n_iso = await db.entities.count_documents({**buyer_q, "created_at": {"$gte": iso}})
        u_dt = await db.entities.count_documents({**buyer_q, "updated_at": {"$gte": dt}})
        u_iso = await db.entities.count_documents({**buyer_q, "updated_at": {"$gte": iso}})
        print(f"{label}: new(dt)={n_dt} new(iso)={n_iso} updated(dt)={u_dt} updated(iso)={u_iso}")

    # sample created_at type
    s = await db.entities.find_one(buyer_q, {"created_at": 1, "updated_at": 1})
    print("sample created_at:", type(s.get("created_at")) if s else None, s.get("created_at") if s else None)

    print("\n--- INGEST RUNS (last 10) ---")
    runs = await db.vbie_ingest_runs.find().sort("started_at", -1).to_list(10)
    if not runs:
        print("NONE — no ingest runs ever recorded")
    for r in runs:
        print(r.get("started_at"), "| trigger:", r.get("trigger"), "| new_buyers:", r.get("new_buyers"), "| sources:", r.get("sources"))

    print("\n--- CYCLES (last 10) ---")
    cyc = await db.vbie_cycles.find().sort("at", -1).to_list(10)
    if not cyc:
        print("NONE — no engine cycles ever run")
    for r in cyc:
        print(r.get("at"), "| type:", r.get("type"), "| trigger:", r.get("trigger"))

    print("\n--- CONFIG / SCHEDULE ---")
    cfg = await db.vbie_config.find_one({"_id": "vbie_schedule"})
    print(cfg)

    print("\n--- SOURCE LEGAL STATUS ---")
    async for src in db.vbie_sources.find():
        print(src.get("_id"), "->", src.get("legal_status"))

    print("\n--- REPORTS (last 3) ---")
    reps = await db.vbie_reports.find().sort("generated_at", -1).to_list(3)
    for r in reps:
        print(r.get("generated_at"), r.get("metrics", {}).get("new_buyers"), "new buyers")

    c.close()

asyncio.run(main())
