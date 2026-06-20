import React, { useEffect, useState } from "react";
import { ToolShell, CTARow, Card } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api, fetchProducts } from "@/lib/api";
import { ChartLine, TrendUp, ArrowRight } from "@phosphor-icons/react";

export default function ProductResearch() {
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ product: "Basmati Rice", hsnCode: "10063020" });
  const [data, setData] = useState(null);

  useEffect(() => { fetchProducts().then(setProducts); }, []);
  useEffect(() => { api.post("/product-research", form).then((r) => setData(r.data)); }, [form]);

  return (
    <>
      <SEO title="Product Research · Demand, Opportunity & Markets"
        description="Discover demand, top markets, opportunity size and trends for any product. Free product research powered by LeadNation."
        path="/tools/product-research"
        keywords="product market research, export demand by product, top importing countries, top exporting countries, market opportunity"
      />
      <ToolShell testIdPrefix="pr" label="Product Research"
        title="Find your next $1M product."
        sub="Spot global demand, top buyer markets and the size of the opportunity — for any product, in 5 seconds."
      >
        <div className="grid lg:grid-cols-12 gap-8">
          <form className="lg:col-span-4 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product">
              <select data-testid="pr-product" value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                {products.map((p) => <option key={p} className="bg-[#0a0f24]">{p}</option>)}
              </select>
            </Field>
            <Field label="HSN code (optional)">
              <input data-testid="pr-hsn" value={form.hsnCode} onChange={(e) => setForm({ ...form, hsnCode: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" />
            </Field>
            <CTARow testIdPrefix="pr-cta" />
          </form>
          <div className="lg:col-span-8 space-y-4">
            {data && (
              <>
                <div data-testid="pr-result" className="glass-strong rounded-3xl p-7">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2"><ChartLine size={14} weight="duotone" /> {data.product} · {data.hsn}</div>
                  <p className="mt-3 text-slate-300 text-lg leading-relaxed">{data.demandOverview}</p>
                  <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 text-sm">
                    <TrendUp size={14} weight="bold" /> {data.opportunity}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <Card title="Top Importing Countries">
                    <ul className="mt-3 space-y-2">
                      {data.topImporting.map((c, i) => (
                        <li key={c.country} data-testid={`pr-import-${i}`} className="glass rounded-xl px-3 py-2 flex items-center justify-between text-sm">
                          <span>{c.country}</span><span className="text-cyan-300 font-mono-display tracking-widest">{c.share}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                  <Card title="Top Exporting Countries">
                    <ul className="mt-3 space-y-2">
                      {data.topExporting.map((c, i) => (
                        <li key={c.country} data-testid={`pr-export-${i}`} className="glass rounded-xl px-3 py-2 flex items-center justify-between text-sm">
                          <span>{c.country}</span><span className="text-violet-300 font-mono-display tracking-widest">{c.share}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                </div>

                <Card title="Trade trends">
                  <ul className="mt-3 space-y-2">
                    {data.trends.map((t, i) => (
                      <li key={i} data-testid={`pr-trend-${i}`} className="flex items-start gap-2 text-sm text-slate-200">
                        <ArrowRight size={14} className="text-cyan-300 mt-1" />{t}
                      </li>
                    ))}
                  </ul>
                </Card>
              </>
            )}
          </div>
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
function Field({ label, children }) {
  return <label className="block"><div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>{children}</label>;
}
