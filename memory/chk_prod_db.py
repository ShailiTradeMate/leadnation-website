import os,asyncio
from dotenv import load_dotenv; load_dotenv("/app/backend/.env")
from motor.motor_asyncio import AsyncIOMotorClient
async def m():
    db=AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    for col in await db.list_collection_names():
        if "trade" in col or "cache" in col: print(col)
    d=await db.trade_cache.find_one({"_id":"stats:090411"},{"result":0})
    print(d)
asyncio.run(m())
