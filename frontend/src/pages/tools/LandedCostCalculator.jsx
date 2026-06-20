import React, { useEffect, useState } from "react";
import { ToolShell, CTARow } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api } from "@/lib/api";
import { Coins, ArrowRight } from "@phosphor-icons/react";

const CURRENCIES = ["USD", "EUR", "INR", "AED", "GBP", "AUD"];

export default function LandedCostCalculator() {
  const [form, setForm] = useState({ productCost: 10000, freight: 800, insurance: 120, duty: 600, localCharges: 350, currency: "USD" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/landed-cost", form);
      setResult(data);
    } finally { setLoading(false); }
  };
  useEffect(() => { submit(); }, []); // eslint-disable-line

  return (
    <>
      <SEO title="Landed Cost Calculator · Free Import Cost Estimator"
        description="Calculate your true landed cost — product, freight, insurance, duty and local charges. Free breakdown for any shipment."
        path="/tools/landed-cost-calculator"
        keywords="landed cost calculator, import cost calculator, CIF DDP, freight calculator, true landed cost"
      />
      <ToolShell testIdPrefix="lcc" label="Landed Cost Calculator"
        title="See your true landed cost."
        sub="Add every component — product, freight, insurance, duty, local charges — and get the real cost of doing business at destination."
      >
        <div className="grid lg:grid-cols-12 gap-8">
          <form onSubmit={submit} className="lg:col-span-5 glass-strong rounded-3xl p-6 sm:p-7 space-y-3">
            {[
              ["productCost", "Product cost"],
              ["freight", "Freight"],
              ["insurance", "Insurance"],
              ["duty", "Customs duty"],
              ["localCharges", "Local charges (THC, drayage, CHA)"],
            ].map(([k, l]) => (
              <Field key={k} label={l}>
                <input data-testid={`lcc-${k}`} type="number" min="0" value={form[k]}
                  onChange={(e) => setForm({ ...form, [k]: Number(e.target.value) || 0 })}
                  className="w-full glass rounded-xl px-4 py-3 outline-none" />
              </Field>
            ))}
            <Field label="Currency">
              <select data-testid="lcc-currency" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none">
                {CURRENCIES.map((c) => <option key={c} className="bg-[#0a0f24]">{c}</option>)}
              </select>
            </Field>
            <button data-testid="lcc-submit" className="btn-primary w-full justify-center mt-2" disabled={loading}>
              {loading ? "Calculating…" : <>Calculate landed cost <ArrowRight size={14} weight="bold" /></>}
            </button>
            <CTARow testIdPrefix="lcc-cta" />
          </form>

          <div className="lg:col-span-7">
            {result && (
              <div data-testid="lcc-result" className="glass-strong rounded-3xl p-7">
                <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
                  <Coins size={14} weight="duotone" /> Total landed cost
                </div>
                <div className="mt-2 text-5xl sm:text-6xl font-display font-extrabold gradient-text">
                  {result.currency} {result.total.toLocaleString()}
                </div>
                <div className="mt-7 space-y-2">
                  {result.breakdown.map((b, i) => (
                    <div key={b.label} data-testid={`lcc-row-${i}`} className="glass rounded-2xl px-4 py-3 flex items-center gap-4">
                      <div className="text-sm flex-1">{b.label}</div>
                      <div className="text-[10px] font-mono-display tracking-widest text-slate-400">{b.share}%</div>
                      <div className="font-display font-bold">{result.currency} {b.amount.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>
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
