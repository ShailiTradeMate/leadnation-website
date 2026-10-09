import json, re, time, threading
from concurrent.futures import ThreadPoolExecutor
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
xml = requests.get("https://vametra.com/api/sitemap.xml", timeout=120).text
urls = list(dict.fromkeys(re.findall(r"<loc>(.*?)</loc>", xml)))
guides = [u for u in urls if "/to/" in u and "/api/answers/" not in u]
hubs = [u for u in urls if re.match(r"https://vametra\.com/(export(/[a-z-]+)?|regions(/[a-z-]+)?)$", u)]
print(f"guides={len(guides)} hubs={len(hubs)}", flush=True)

lock, done = threading.Lock(), [0]

def probe(u):
    for a in (1, 2):
        try:
            t = time.time()
            r = requests.get(u, headers=UA, timeout=90)
            txt = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)
            words = len(re.sub(r"<[^>]+>", " ", txt).split())
            h1 = re.findall(r"(?s)<h1[^>]*>(.*?)</h1>", r.text)
            return {"url": u, "status": r.status_code, "ms": int((time.time() - t) * 1000),
                    "words": words, "h1": re.sub(r"<[^>]+>", "", h1[0]).strip()[:90] if h1 else "",
                    "canonicals": len(re.findall(r'rel="canonical"', r.text)),
                    "robots": len(re.findall(r'name="robots"', r.text)),
                    "noindex": "noindex" in r.text}
        except Exception as e:
            if a == 2:
                return {"url": u, "status": 0, "ms": 0, "words": 0, "h1": "", "canonicals": 0,
                        "robots": 0, "noindex": False, "err": type(e).__name__}
            time.sleep(2)

def work(u):
    r = probe(u)
    with lock:
        done[0] += 1
        if done[0] % 50 == 0:
            print(f"  ...{done[0]}", flush=True)
    return r

with ThreadPoolExecutor(max_workers=8) as ex:
    rows = list(ex.map(work, guides + hubs))
json.dump(rows, open("/app/memory/reaudit.json", "w"))
print("DONE", flush=True)
