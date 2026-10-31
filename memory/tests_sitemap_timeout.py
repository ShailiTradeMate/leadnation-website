"""The sitemap must stay fast and valid even when a data source hangs."""
import asyncio, re, sys, time
sys.path.insert(0, "/app/backend")
import seo


async def main():
    r = await seo.sitemap_xml()
    base = len(re.findall(r"<loc>", r.body.decode()))
    print("healthy sitemap locs:", base)
    assert base > 900

    async def hang():
        await asyncio.sleep(120)
        return []

    seo._region_routes = hang
    seo._answer_routes = hang
    t0 = time.time()
    r = await seo.sitemap_xml()
    took = time.time() - t0
    xml = r.body.decode()
    locs = len(re.findall(r"<loc>", xml))
    print(f"two sections hanging -> {locs} locs in {took:.1f}s")
    assert xml.startswith("<?xml") and "<urlset" in xml
    assert "/export/" in xml, "the good sections must survive"
    assert took < 25, f"sitemap took {took:.1f}s — gateway would time out"
    print("PASS: hanging sections are skipped concurrently, sitemap still served")


asyncio.run(main())
