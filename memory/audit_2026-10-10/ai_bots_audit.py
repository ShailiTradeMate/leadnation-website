"""Can AI crawlers reach the 975 sitemap URLs on production? robots.txt rules + UA matrix + full GPTBot sweep."""
import csv, json, re, time, collections
from concurrent.futures import ThreadPoolExecutor
from urllib import robotparser
import requests

OUT = "/app/memory/audit_2026-10-10/"
UAS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
    "ChatGPT-User": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot",
    "OAI-SearchBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "Perplexity-User": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "Claude-User": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)",
    "bingbot(Copilot)": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/116.0.1938.76 Safari/537.36",
    "Google-Extended": "Mozilla/5.0 (compatible; Google-Extended/1.0)",
    "Applebot": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
    "Bytespider": "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)",
    "DuckAssistBot": "Mozilla/5.0 (compatible; DuckAssistBot/1.0; +http://duckduckgo.com/duckassistbot)",
    "cohere-ai": "cohere-ai",
    "Meta-ExternalAgent": "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)",
}
xml = requests.get("https://vametra.com/api/sitemap.xml", timeout=120).text
urls = list(dict.fromkeys(re.findall(r"<loc>(.*?)</loc>", xml)))
rp = robotparser.RobotFileParser()
rp.set_url("https://vametra.com/robots.txt"); rp.read()
robots = {ua: sum(rp.can_fetch(ua.split("(")[0], u) for u in urls) for ua in UAS}
robots["*"] = sum(rp.can_fetch("*", u) for u in urls)
print("robots allowed of", len(urls), json.dumps(robots), flush=True)

SAMPLE = ["https://vametra.com/", "https://vametra.com/export", "https://vametra.com/export/indian-spices",
          "https://vametra.com/regions/europe", "https://vametra.com/export/indian-spices/to/chile",
          "https://vametra.com/export/pharmaceuticals/to/germany", "https://vametra.com/export/engineering-machinery/to/italy",
          "https://vametra.com/tools/duty-calculator", "https://vametra.com/countries/chile",
          "https://vametra.com/api/answers/html/export/indian-spices/to/chile",
          "https://vametra.com/api/answers/md/export/pharmaceuticals/to/germany", "https://vametra.com/llms.txt"]


def fetch(ua_name, u):
    try:
        t = time.time()
        r = requests.get(u, headers={"User-Agent": UAS[ua_name]}, timeout=120, allow_redirects=False)
        txt = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", r.text)
        words = len(re.sub(r"<[^>]+>", " ", txt).split())
        h1 = bool(re.search(r"<h1", r.text))
        kind = "non-html" if "text/html" not in r.headers.get("content-type", "") else ("rendered" if h1 and words > 300 else "shell")
        return {"ua": ua_name, "url": u, "status": r.status_code, "ms": int((time.time() - t) * 1000), "words": words,
                "h1": h1, "kind": kind, "server": r.headers.get("server", ""), "cf_mitigated": r.headers.get("cf-mitigated", "")}
    except Exception as e:
        return {"ua": ua_name, "url": u, "status": 0, "ms": 0, "words": 0, "h1": False, "kind": "failure", "err": type(e).__name__}


matrix = []
with ThreadPoolExecutor(max_workers=4) as ex:
    matrix = list(ex.map(lambda p: fetch(*p), [(ua, u) for ua in UAS for u in SAMPLE]))
with open(OUT + "ai_ua_matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ua", "url", "status", "kind", "words", "ms", "cf_mitigated", "err"], extrasaction="ignore")
    w.writeheader(); w.writerows(matrix)
pivot = collections.defaultdict(dict)
for m in matrix:
    pivot[m["ua"]][m["url"].replace("https://vametra.com", "") or "/"] = f'{m["status"]}:{m["kind"][0]}'
print(json.dumps(pivot, indent=1), flush=True)

# full sweep: every sitemap URL as GPTBot (status + rendered/shell), concurrency 4
done = [0]
def sweep(u):
    r = fetch("GPTBot", u)
    done[0] += 1
    if done[0] % 100 == 0:
        print(f"  sweep ...{done[0]}/{len(urls)}", flush=True)
    return r
with ThreadPoolExecutor(max_workers=4) as ex:
    rows = list(ex.map(sweep, urls))
with open(OUT + "gptbot_all_urls.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["url", "status", "kind", "words", "ms", "cf_mitigated", "err"], extrasaction="ignore")
    w.writeheader(); w.writerows(rows)
grp = lambda u: "answers-doc" if "/api/answers/" in u else "export-guide" if "/to/" in u else "other-page"
summ = collections.defaultdict(collections.Counter)
for r in rows:
    summ[grp(r["url"])][f'{r["status"]}:{r["kind"]}'] += 1
print(json.dumps({k: dict(v) for k, v in summ.items()}, indent=1))
print("DONE", flush=True)
