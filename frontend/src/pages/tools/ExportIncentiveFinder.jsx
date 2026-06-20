import React, { useEffect, useState } from "react";
import { ToolShell, CTARow, Card } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api, fetchProducts, fetchCountries } from "@/lib/api";
import { Sparkle, CheckCircle } from "@phosphor-icons/react";

export default function ExportIncentiveFinder() {
  const [products, setProducts] = useState([]);
  const [countries, setCountries] = useState([]);
  const [form, setForm] = useState({ product: "Basmati Rice", destination: "AE" });
  const [data, setData] = useState(null);

  useEffect(() => { fetchProducts().then(setProducts); fetchCountries().then(setCountries); }, []);
  useEffect(() => {
    api.post("/export-incentive", form).then((r) => setData(r.data));
  }, [form]);

  return (
    <>
      <SEO title="Export Incentive Finder · RoDTEP, Duty Drawback, MSME"
        description="Discover RoDTEP, Duty Drawback, MAI, Interest Equalisation and DGFT incentives applicable to your product and destination."
        path="/tools/export-incentive-finder"
        keywords="RoDTEP eligibility, duty drawback India, export incentives India, interest equalisation, EPCG scheme"
      />
      <ToolShell testIdPrefix="inc" label="Export Incentive Finder"
        title="Stack every incentive you're owed."
        sub="RoDTEP, Drawback, EPCG, Advance Authorisation, MSME interest subvention — find what your shipment qualifies for, instantly."
      >
        <div className="grid lg:grid-cols-12 gap-8">
          <form className="lg:col-span-4 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product">
              <select data-testid="inc-product" value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                {products.map((p) => <option key={p} className="bg-[#0a0f24]">{p}</option>)}
              </select>
            </Field>
            <Field label="Destination country">
              <select data-testid="inc-destination" value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                {countries.map((c) => <option key={c.code} value={c.code} className="bg-[#0a0f24]">{c.flag} {c.name}</option>)}
              </select>
            </Field>
            <CTARow testIdPrefix="inc-cta" />
          </form>

          <div className="lg:col-span-8 space-y-4">
            {data && (
              <>
                <div data-testid="inc-result" className="glass-strong rounded-3xl p-7">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
                    <Sparkle size={14} weight="duotone" /> {data.product} → {data.destination}
                  </div>
                  <div className="mt-4 grid sm:grid-cols-2 gap-4">
                    <Highlight title="RoDTEP" body={data.rodtep.eligible ? `Eligible · ${data.rodtep.rate}` : "Not eligible"} sub={data.rodtep.scrip} />
                    <Highlight title="Duty Drawback" body={data.dutyDrawback.eligible ? `Eligible · ${data.dutyDrawback.rate}` : "Not eligible"} sub={data.dutyDrawback.category} />
                  </div>
                </div>
                <Card title="Incentives stack">
                  <ul className="mt-4 space-y-2.5">
                    {data.incentives.map((i, k) => (
                      <li key={k} data-testid={`inc-item-${k}`} className="flex items-start gap-2 text-sm">
                        <CheckCircle size={16} weight="fill" className="text-cyan-300 mt-0.5 shrink-0" />
                        <span><span className="text-white font-semibold">{i.name}</span> — <span className="text-slate-300">{i.benefit}</span></span>
                      </li>
                    ))}
                  </ul>
                </Card>
                <Card title="Government schemes">
                  <ul className="mt-4 space-y-3">
                    {data.govBenefits.map((b, k) => (
                      <li key={k} className="glass rounded-2xl p-4">
                        <div className="font-display font-semibold">{b.name}</div>
                        <div className="text-sm text-slate-400 mt-1">{b.detail}</div>
                      </li>
                    ))}
                  </ul>
                </Card>
                <div className="text-xs text-slate-500">{data.note}</div>
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
function Highlight({ title, body, sub }) {
  return (
    <div className="glass rounded-2xl p-4 border border-cyan-400/15">
      <div className="text-[10px] uppercase tracking-[0.25em] text-cyan-300 font-mono-display">{title}</div>
      <div className="mt-1 font-display font-bold text-lg">{body}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}
