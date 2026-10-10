"""Production Googlebot-UA render audit of every sitemap guide + hub. Writes per-URL and per-product CSVs."""
import csv, json, re, time, threading, collections
from concurrent.futures import ThreadPoolExecutor
import requests

OUT = "/app/memory/audit_2026-10-10/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
xml = requests.get("https://vametra.com/api/sitemap.xml", timeout=120).text
urls = list(dict.fromkeys(re.findall(r"<loc>(.*?)</loc>", xml)))
guides = [u for u in urls if "/to/" in u and "/api/answers/" not in u]
hubs = [u for u in urls if re.match(r"https://vametra\.com/(export(/[a-z-]+)?|regions(/[a-z-]+)?)$", u)]
print(f"sitemap={len(urls)} guides={len(guides)} hubs={len(hubs)}", flush=True)

lock, done = threading.Lock(), [0]


def classify(r, words, h1, has_answer):
    if r.status_code == 0:
        return "failure"
    if r.status_code >= 400:
        return f"http_{r.status_code}"
    if 300 <= r.status_code < 400:
        return "redirect"
    if h1 and has_answer and words >= 600:
        return "rendered"
    if words < 320 and not h1:
        return "shell"
    return "partial"


def probe(u):
    for a in (1, 2):
        try:
            t = time.time()
            r = requests.get(u, headers=UA, timeout=120, allow_redirects=False)
            txt = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)
            words = len(re.sub(r"<[^>]+>", " ", txt).split())
            h1 = re.findall(r"(?s)<h1[^>]*>(.*?)</h1>", r.text)
            h1t = re.sub(r"<[^>]+>", "", h1[0]).strip()[:90] if h1 else ""
            canon = re.findall(r'rel="canonical" href="([^"]+)"', r.text)
            has_answer = 'data-testid="epc-answer"' in r.text or 'data-testid="eph-' in r.text or 'data-testid="region-' in r.text or 'data-testid="egi-' in r.text or words >= 600
            return {"url": u, "status": r.status_code, "ms": int((time.time() - t) * 1000), "words": words,
                    "h1": h1t, "canonical": canon[0] if canon else "", "canonical_count": len(canon),
                    "canonical_ok": (canon[0] == u) if canon else False,
                    "titles": len(re.findall(r"<title[ >]", r.text)),
                    "descriptions": len(re.findall(r'name="description"', r.text)),
                    "robots": len(re.findall(r'name="robots"', r.text)), "noindex": "noindex" in r.text,
                    "product_schema": '"@type":"Product"' in r.text,
                    "verdict": classify(r, words, h1t, has_answer)}
        except Exception as e:
            if a == 2:
                return {"url": u, "status": 0, "ms": 0, "words": 0, "h1": "", "canonical": "", "canonical_count": 0,
                        "canonical_ok": False, "titles": 0, "descriptions": 0, "robots": 0, "noindex": False,
                        "product_schema": False, "verdict": "failure", "err": type(e).__name__}
            time.sleep(3)


def work(u):
    r = probe(u)
    with lock:
        done[0] += 1
        if done[0] % 40 == 0:
            print(f"  ...{done[0]}/{len(guides) + len(hubs)}", flush=True)
    return r


with ThreadPoolExecutor(max_workers=6) as ex:
    rows = list(ex.map(work, guides + hubs))

fields = ["url", "verdict", "status", "ms", "words", "h1", "canonical_ok", "canonical_count", "titles",
          "descriptions", "robots", "noindex", "product_schema", "err"]
with open(OUT + "guides_per_url.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

by = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    m = re.match(r"https://vametra\.com/export/([a-z-]+)/to/", r["url"])
    key = m.group(1) if m else "hubs"
    by[key][r["verdict"]] += 1
    by[key]["total"] += 1
verdicts = ["rendered", "partial", "shell", "redirect", "failure"]
with open(OUT + "guides_by_product.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["product", "total"] + verdicts + ["http_4xx_5xx"])
    tot = collections.Counter()
    for k in sorted(by):
        c = by[k]
        http = sum(v for kk, v in c.items() if kk.startswith("http_"))
        w.writerow([k, c["total"]] + [c[v] for v in verdicts] + [http])
        tot.update(c)
    http = sum(v for kk, v in tot.items() if kk.startswith("http_"))
    w.writerow(["ALL", tot["total"]] + [tot[v] for v in verdicts] + [http])
json.dump(rows, open(OUT + "guides_rows.json", "w"))
print(open(OUT + "guides_by_product.csv").read())
rend = [r["ms"] for r in rows if r["verdict"] == "rendered"]
shell = [r["ms"] for r in rows if r["verdict"] == "shell"]
med = lambda a: sorted(a)[len(a) // 2] if a else 0
print(f"median ms rendered={med(rend)} shell={med(shell)}")
print("DONE", flush=True)
