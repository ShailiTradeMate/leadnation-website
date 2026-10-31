# Iter80 cleanup: remove QA service requests, files, wa_clicks, leads, templates override
import asyncio, os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    reqs = await db.service_requests.find({"name": "QA Customer"}, {"_id": 0, "id": 1}).to_list(100)
    ids = [r["id"] for r in reqs]
    print("service_requests", ids)
    print("files", (await db.service_files.delete_many({"requestId": {"$in": ids}})).deleted_count)
    print("srs", (await db.service_requests.delete_many({"id": {"$in": ids}})).deleted_count)
    q = {"$or": [{"name": "QA Guest"}, {"email": {"$regex": "^qa"}}, {"email": "delivered@resend.dev"}, {"requestId": {"$in": ids}},
                 {"at": {"$gte": "2026-10-31T12:45"}, "name": None, "email": None}]}
    print("wa_clicks", (await db.wa_clicks.delete_many(q)).deleted_count)
    for coll in ("leads", "service_leads"):
        if coll in await db.list_collection_names():
            print(coll, (await db[coll].delete_many({"$or": [{"name": "QA Customer"}, {"email": "delivered@resend.dev"}, {"email": {"$regex": "^qa\\.customer"}}]})).deleted_count)
    print("wa_templates ca override", await db.wa_templates.count_documents({"key": "ca_message"}))


asyncio.run(main())
