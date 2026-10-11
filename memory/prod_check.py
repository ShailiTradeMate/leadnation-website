import re, sys, csv, concurrent.futures as cf, urllib.request, time

UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
SITE = "https://vametra.com"

def fetch(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.getcode(), r.read().decode("utf-8", "ignore"), time.time() - t0
    except Exception as e:
        code = getattr(e, "code", 0)
        return code, "", time.time() - t0

def analyse(u):
    code, t, el = fetch(u)
    if not t:
        return dict(url=u, http=code, titles=0, descs=0, canons=0, canonical="", h1s=0, words=0, robots="", jsonld="", sec=round(el, 2))
    body = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", t)
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    canon = re.findall(r'<link rel="canonical" href="([^"]+)"', t)
    types = re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', t)
    return dict(
        url=u, http=code,
        titles=len(re.findall(r"<title[ >]", t)),
        descs=len(re.findall(r'<meta name="description"', t)),
        canons=len(canon), canonical=canon[0] if canon else "",
        h1s=len(re.findall(r"<h1[ >]", t)),
        words=words,
        robots=(re.findall(r'<meta name="robots" content="([^"]+)"', t) or [""])[0],
        jsonld="|".join(sorted(set(types))),
        sec=round(el, 2),
    )

urls = [l.strip() for l in open(sys.argv[1]) if l.strip()]
rows = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(analyse, urls):
        rows.append(r)
        print(r["http"], r["titles"], r["words"], r["sec"], r["url"], flush=True)

out = sys.argv[2]
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

bad = [r for r in rows if r["http"] != 200 or r["titles"] != 1 or r["canons"] != 1 or r["h1s"] < 1 or r["words"] < 350]
print("\nTOTAL", len(rows), "PROBLEM", len(bad))
for r in bad:
    print("  ", r["http"], "titles", r["titles"], "canons", r["canons"], "h1", r["h1s"], "words", r["words"], r["url"])
