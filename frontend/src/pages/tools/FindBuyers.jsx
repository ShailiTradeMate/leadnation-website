import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ToolShell, CTARow, Card } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api, fetchProducts, fetchCountries } from "@/lib/api";
import { Users, Lock, ArrowRight } from "@phosphor-icons/react";

export default function FindBuyers() {
  const [products, setProducts] = useState([]);
  const [countries, setCountries] = useState([]);
  const [form, setForm] = useState({ product: "Basmati Rice", country: "" });
  const [data, setData] = useState(null);

  useEffect(() => { fetchProducts().then(setProducts); fetchCountries().then(setCountries); }, []);
  useEffect(() => { api.post("/find-buyers", form).then((r) => setData(r.data)); }, [form]);

  return (
    <>
      <SEO title="Buyer Discovery · Find Verified Importers Worldwide"
        description="Find verified global buyers for your product — by country, demand and market potential. Free preview. Unlock full database in the LeadNation app."
        path="/tools/find-buyers"
        keywords="find buyers for export, verified importers, buyer discovery India, export leads, B2B buyer database"
      />
      <ToolShell testIdPrefix="fb" label="Buyer Discovery"
        title="Find your next buyer. Today."
        sub="Search verified buyers by product and market. See demand, fit and volume — full profiles unlock when you create an account."
      >
        <div className="grid lg:grid-cols-12 gap-8">
          <form className="lg:col-span-4 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product">
              <select data-testid="fb-product" value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                {products.map((p) => <option key={p} className="bg-[#0a0f24]">{p}</option>)}
              </select>
            </Field>
            <Field label="Country (optional)">
              <select data-testid="fb-country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                <option value="" className="bg-[#0a0f24]">All markets</option>
                {countries.map((c) => <option key={c.code} value={c.code} className="bg-[#0a0f24]">{c.flag} {c.name}</option>)}
              </select>
            </Field>
            <CTARow testIdPrefix="fb-cta" />
          </form>

          <div className="lg:col-span-8 space-y-4">
            {data && (
              <>
                <div data-testid="fb-result" className="glass-strong rounded-3xl p-7">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
                    <Users size={14} weight="duotone" /> {data.buyers.length} buyers · {data.marketPotential}
                  </div>
                  <div className="mt-2 text-sm text-slate-400">Suggested regions: {data.suggestedRegions.join(" · ")}</div>
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  {data.buyers.map((b, i) => (
                    <div key={i} data-testid={`fb-card-${i}`} className="glass rounded-3xl p-5">
                      <div className="flex items-center justify-between">
                        <div className="font-display font-bold">{b.company}</div>
                        <div className={`text-[10px] px-2 py-1 rounded-full font-mono-display tracking-widest uppercase ${b.fit === "High" ? "bg-emerald-500/15 text-emerald-300" : "bg-amber-500/15 text-amber-300"}`}>{b.fit} fit</div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{b.city} · {b.country}</div>
                      <div className="mt-3 text-sm">Demand: <span className="font-bold">{b.volume} {b.demand}</span></div>
                    </div>
                  ))}
                </div>
                {data.lockedExtras && (
                  <div className="glass-strong rounded-3xl p-6 flex items-center gap-4 border border-cyan-400/20">
                    <Lock size={26} className="text-cyan-300" weight="duotone" />
                    <div className="flex-1">
                      <div className="font-display font-bold">12+ more verified buyers locked.</div>
                      <div className="text-sm text-slate-400">Full contact details, decision-makers and 3-year demand history are inside the LeadNation app.</div>
                    </div>
                    <Link to="/contact" className="btn-primary">Create free account <ArrowRight size={14} weight="bold" /></Link>
                  </div>
                )}
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
