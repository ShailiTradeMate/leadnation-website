import json, re, random, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
xml = requests.get("https://vametra.com/api/sitemap.xml", timeout=120).text
urls = list(dict.fromkeys(re.findall(r"<loc>(.*?)</loc>", xml)))
guides = [u for u in urls if "/to/" in u and "/api/answers/" not in u]
random.seed(7)
pick = random.sample(guides, min(N, len(guides)))


def probe(u):
    try:
        t = time.time()
        r = requests.get(u, headers=UA, timeout=90)
        txt = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)
        words = len(re.sub(r"<[^>]+>", " ", txt).split())
        h1 = re.findall(r"(?s)<h1[^>]*>(.*?)</h1>", r.text)
        return {"url": u, "status": r.status_code, "ms": int((time.time() - t) * 1000),
                "words": words, "h1": bool(h1), "rendered": bool(h1) and words > 400}
    except Exception as e:
        return {"url": u, "status": 0, "ms": 0, "words": 0, "h1": False, "rendered": False,
                "err": type(e).__name__}


with ThreadPoolExecutor(max_workers=4) as ex:
    rows = list(ex.map(probe, pick))

ren = [r for r in rows if r["rendered"]]
shell = [r for r in rows if not r["rendered"]]
print(f"sampled={len(rows)} rendered={len(ren)} shell={len(shell)}")
print("status:", {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r['status'] for r in rows})})
if ren:
    print("rendered median words:", sorted(r["words"] for r in ren)[len(ren) // 2],
          "median ms:", sorted(r["ms"] for r in ren)[len(ren) // 2])
if shell:
    print("shell median words:", sorted(r["words"] for r in shell)[len(shell) // 2],
          "median ms:", sorted(r["ms"] for r in shell)[len(shell) // 2])
    for r in shell[:5]:
        print("  SHELL", r["words"], "w", r["ms"], "ms", r["url"])
json.dump(rows, open("/app/memory/sample_audit.json", "w"))
