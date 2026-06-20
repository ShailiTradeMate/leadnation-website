import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO, { baseOrgSchema } from "@/components/SEO";
import { api, fetchCountries } from "@/lib/api";
import { Calculator, ArrowRight, TrendDown } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";

const CATEGORIES = [
  "Agriculture & Food",
  "Textiles & Apparel",
  "Electronics",
  "Pharmaceuticals",
  "Machinery",
  "Chemicals",
  "Automobiles & Parts",
  "Gems & Jewellery",
  "Furniture & Handicrafts",
  "Energy & Petrochemicals",
];
const CURRENCIES = ["USD", "EUR", "INR", "AED", "GBP", "AUD", "SGD", "JPY"];

export default function DutyCalculator() {
  const [countries, setCountries] = useState([]);
  const [form, setForm] = useState({
    exportCountry: "IN",
    importCountry: "AE",
    category: "Agriculture & Food",
    value: 10000,
    currency: "USD",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCountries().then(setCountries);
  }, []);

  const calc = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/duty-calc", form);
      setResult(r.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { calc(); /* initial */ }, []); // eslint-disable-line

  return (
    <>
      <SEO
        title="Customs Duty Calculator · Free Import & Export Tariff Tool"
        description="Estimate customs duty, taxes and landed cost for any product between any two countries — free, instant, and powered by LeadNation's trade engine."
        path="/tools/duty-calculator"
        keywords="customs duty calculator, import duty calculator, export duty India UAE, landed cost calculator, free tariff tool"
        schema={{
          "@context": "https://schema.org",
          "@type": "WebApplication",
          name: "LeadNation Customs Duty Calculator",
          applicationCategory: "BusinessApplication",
          operatingSystem: "Web",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        }}
      />

      <PageHero
        testIdPrefix="duty"
        label="SEO Tool · 100% Free"
        title="Customs Duty Calculator"
        sub="Estimate duty, taxes and landed cost in any corridor on earth. Powered by the LeadNation trade engine — no signup, no card, instant result."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-8">
        <form onSubmit={calc} className="lg:col-span-5 glass-strong rounded-3xl p-7 sm:p-8 space-y-4">
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
            <Calculator size={16} weight="duotone" /> Configure shipment
          </div>

          <Field label="Country of Export">
            <select
              data-testid="duty-export-country"
              value={form.exportCountry}
              onChange={(e) => setForm({ ...form, exportCountry: e.target.value })}
              className="w-full glass rounded-xl px-4 py-3 outline-none"
            >
              {countries.map((c) => (
                <option key={c.code} value={c.code} className="bg-[#0a0f24]">{c.flag} {c.name}</option>
              ))}
            </select>
          </Field>

          <Field label="Country of Import">
            <select
              data-testid="duty-import-country"
              value={form.importCountry}
              onChange={(e) => setForm({ ...form, importCountry: e.target.value })}
              className="w-full glass rounded-xl px-4 py-3 outline-none"
            >
              {countries.map((c) => (
                <option key={c.code} value={c.code} className="bg-[#0a0f24]">{c.flag} {c.name}</option>
              ))}
            </select>
          </Field>

          <Field label="Product Category">
            <select
              data-testid="duty-category"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full glass rounded-xl px-4 py-3 outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c} className="bg-[#0a0f24]">{c}</option>
              ))}
            </select>
          </Field>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <Field label="Product Value">
                <input
                  data-testid="duty-value"
                  type="number"
                  min="1"
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: Number(e.target.value) || 0 })}
                  className="w-full glass rounded-xl px-4 py-3 outline-none"
                />
              </Field>
            </div>
            <Field label="Currency">
              <select
                data-testid="duty-currency"
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
                className="w-full glass rounded-xl px-4 py-3 outline-none"
              >
                {CURRENCIES.map((c) => (<option key={c} value={c} className="bg-[#0a0f24]">{c}</option>))}
              </select>
            </Field>
          </div>

          <button data-testid="duty-submit" className="btn-primary w-full justify-center" disabled={loading}>
            {loading ? "Calculating…" : <>Calculate landed cost <ArrowRight size={16} weight="bold" /></>}
          </button>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Indicative figures only. Real duties depend on HS code, certificate of origin and live tariff schedules — for exact figures, use the LeadNation app.
          </p>
        </form>

        <div className="lg:col-span-7">
          {result && (
            <div data-testid="duty-result" className="glass-strong rounded-3xl p-7 sm:p-9">
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
                {result.exportCountry} → {result.importCountry} · {result.category}
              </div>
              <div className="mt-3 flex items-end gap-3 flex-wrap">
                <div className="text-5xl sm:text-6xl font-display font-extrabold gradient-text">
                  {result.currency} {result.estimatedLandedCost.toLocaleString()}
                </div>
                {result.ftaApplied && (
                  <span className="px-3 py-1.5 rounded-full text-[11px] font-mono-display tracking-widest uppercase bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 flex items-center gap-1">
                    <TrendDown size={12} weight="bold" /> FTA applied
                  </span>
                )}
              </div>
              <div className="text-sm text-slate-400 mt-1">Estimated landed cost</div>

              <div className="mt-7 grid sm:grid-cols-2 gap-4">
                <Row label="Shipment value" value={`${result.currency} ${result.shipmentValue.toLocaleString()}`} />
                <Row label={`Customs duty (${result.dutyRate}%)`} value={`+ ${result.currency} ${result.estimatedDuty.toLocaleString()}`} />
                <Row label={`VAT / GST (${result.vatRate}%)`} value={`+ ${result.currency} ${result.estimatedTaxes.toLocaleString()}`} />
                <Row label="Customs handling (~0.5%)" value={`+ ${result.currency} ${result.estimatedHandling.toLocaleString()}`} />
              </div>

              <div className="mt-6 p-4 rounded-2xl bg-cyan-500/5 border border-cyan-400/15 text-sm text-slate-300">
                {result.note}
              </div>

              <div className="mt-7 grid sm:grid-cols-2 gap-3">
                <button
                  data-testid="duty-cta-create-account"
                  onClick={() => navigate("/contact")}
                  className="btn-primary justify-center w-full"
                >
                  Create free account
                </button>
                <a
                  href="#download"
                  data-testid="duty-cta-download"
                  className="btn-ghost justify-center w-full"
                >
                  Download LeadNation app
                </a>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA id="download" />
      </section>
    </>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>
      {children}
    </label>
  );
}
function Row({ label, value }) {
  return (
    <div className="glass rounded-2xl p-4 flex items-center justify-between">
      <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 font-mono-display">{label}</div>
      <div className="font-display font-bold">{value}</div>
    </div>
  );
}
