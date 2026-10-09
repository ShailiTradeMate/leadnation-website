import requests, re, time
UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
urls = ["https://vametra.com/export/pharmaceuticals/to/switzerland",
        "https://vametra.com/export/engineering-machinery/to/germany",
        "https://vametra.com/export/fresh-fruits/to/uae"]

def probe(u):
    t = time.time()
    r = requests.get(u, headers=UA, timeout=120)
    txt = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)
    w = len(re.sub(r"<[^>]+>", " ", txt).split())
    return r.status_code, w, ("<h1" in r.text), int((time.time() - t) * 1000)

print("PASS A (cold, 30s apart, single-threaded)", flush=True)
for u in urls:
    print("  ", probe(u), u.replace("https://vametra.com", ""), flush=True)
    time.sleep(30)
print("waiting 8 minutes with zero traffic from us...", flush=True)
time.sleep(480)
print("PASS B (8 min later, single-threaded)", flush=True)
for u in urls:
    print("  ", probe(u), u.replace("https://vametra.com", ""), flush=True)
    time.sleep(20)
print("DONE", flush=True)
