"""Seed a cold deployment's SEO caches from this (warm) preview DB.
usage: python3 seed_prod_caches.py https://vametra.com <admin-token> [collection ...]"""
import asyncio, json, os, sys
import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
TARGET, TOKEN = sys.argv[1].rstrip("/"), sys.argv[2]
COLLS = sys.argv[3:] or ["seo_matrix_cache", "duty_cache", "trade_cache", "seo_page_cache"]


async def main():
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    async with httpx.AsyncClient(timeout=120) as cx:
        for coll in COLLS:
            q = {"_id": "matrix:all:all"} if coll == "seo_matrix_cache" else {}
            docs = [d async for d in db[coll].find(q)]
            if coll == "seo_matrix_cache" and any(d.get("partial") for d in docs):
                print("matrix snapshot is partial — refusing to seed it")
                continue
            sent, chunk, size = 0, [], 0
            for d in docs:
                d["_id"] = str(d["_id"])
                s = json.dumps(d, default=str)
                if chunk and size + len(s) > 400_000:
                    sent += await push(cx, coll, chunk); chunk, size = [], 0
                chunk.append(json.loads(s)); size += len(s)
            if chunk:
                sent += await push(cx, coll, chunk)
            print(f"{coll}: {sent}/{len(docs)} docs written")


async def push(cx, coll, chunk):
    r = await cx.post(f"{TARGET}/api/seo/cache-import", headers={"X-Admin-Token": TOKEN},
                      json={"collection": coll, "docs": chunk})
    r.raise_for_status()
    return r.json()["written"]


asyncio.run(main())
