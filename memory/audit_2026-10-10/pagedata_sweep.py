import requests,re,time,csv,json
from concurrent.futures import ThreadPoolExecutor
xml=requests.get("https://vametra.com/api/sitemap.xml",timeout=120).text
combos=sorted(set(re.findall(r"https://vametra\.com/export/([a-z-]+)/to/([a-z-]+)",xml)))
def one(pc):
    p,c=pc; t=time.time()
    try:
        r=requests.get(f"https://vametra.com/api/seo/page-data/{p}/{c}",timeout=120); ms=int((time.time()-t)*1000)
        j=r.json() if r.status_code==200 else {}
        return {"product":p,"country":c,"status":r.status_code,"ms":ms,"cachedAt":j.get("cachedAt",""),"indexable":j.get("indexable",""),"hole":ms>2000}
    except Exception as e:
        return {"product":p,"country":c,"status":0,"ms":int((time.time()-t)*1000),"cachedAt":"","indexable":"","hole":True,"err":type(e).__name__}
with ThreadPoolExecutor(max_workers=2) as ex: rows=list(ex.map(one,combos))
with open("pagedata_sweep.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["product","country","status","ms","cachedAt","indexable","hole","err"],extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("total",len(rows),"holes(>2s):",sum(r["hole"] for r in rows),"non-200:",sum(r["status"]!=200 for r in rows))
print("holes:",[(r["product"],r["country"],r["ms"]) for r in rows if r["hole"]])
print("cachedAt sample:",sorted({r["cachedAt"][:13] for r in rows}))
print("DONE")
