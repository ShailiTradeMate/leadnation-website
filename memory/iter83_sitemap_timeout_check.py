import asyncio, sys, time, logging
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

records = []
class H(logging.Handler):
    def emit(self, rec):
        records.append(rec.getMessage())

logging.getLogger().addHandler(H())
logging.getLogger().setLevel(logging.WARNING)
import seo


async def slow():
    await asyncio.sleep(60)
    return [("/should-not-appear", "weekly", "0.1")]


async def main():
    seo._region_routes = slow
    t = time.time()
    resp = await seo.sitemap_xml()
    dt = time.time() - t
    body = resp.body.decode()
    ok = (dt < 25 and "<urlset" in body and "/export/" in body and "/api/answers/html/" in body
          and "/should-not-appear" not in body and any("sitemap section regions skipped" in m for m in records))
    print(f"seconds={dt:.1f} locs={body.count('<loc>')} regions_in={'/regions/' in body} warn={[m for m in records if 'sitemap' in m]}")
    print("PASS" if ok else "FAIL")

asyncio.run(main())
