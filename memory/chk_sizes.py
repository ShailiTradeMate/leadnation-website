import os,asyncio,json
from dotenv import load_dotenv; load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient
async def m():
    db=AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    d=await db.seo_matrix_cache.find_one({"_id":"matrix:all:all"}); print("matrix bytes", len(json.dumps(d)))
    n=0;b=0
    async for p in db.seo_page_cache.find({}): n+=1;b+=len(json.dumps(p,default=str))
    print("page cache", n, b)
    for c in ["duty_cache","trade_cache"]:
        print(c, await db[c].count_documents({}))
asyncio.run(m())
