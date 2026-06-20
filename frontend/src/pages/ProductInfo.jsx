import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import {
  fetchCountries,
  fetchBusinessTypes,
  fetchTradeDirections,
  fetchProducts,
  postProductInfo,
} from "@/lib/api";
import { Package, TrendUp, Buildings, CheckCircle, MagnifyingGlass } from "@phosphor-icons/react";

export default function ProductInfo() {
  const [countries, setCountries] = useState([]);
  const [bts, setBts] = useState([]);
  const [dirs, setDirs] = useState([]);
  const [products, setProducts] = useState([]);

  const [form, setForm] = useState({
    country: "IN",
    businessType: "Manufacturer",
    direction: "Export",
    product: "Basmati Rice",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCountries().then(setCountries);
    fetchBusinessTypes().then(setBts);
    fetchTradeDirections().then(setDirs);
    fetchProducts().then(setProducts);
  }, []);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const data = await postProductInfo(form);
      setResult(data);
      setTimeout(() => {
        document.getElementById("pi-result")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    } finally {
      setLoading(false);
    }
  };

  // Initial result on mount
  useEffect(() => {
    handleSubmit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <SEO
        title="Product Trade Intelligence · Market Size, Buyers, Tariffs"
        description="Pick a country, business type and product. Get market size, top buyers, certifications and tariffs — instantly."
        path="/product-info"
        keywords="product market size, top buyers, HS code, certifications, FOB price, MOQ, export market intelligence"
      />
      <PageHero
        testIdPrefix="pi"
        label="Product Info Engine"
        title="Pick a product. Win a market."
        sub="Select a country, your business type, trade direction and product. We'll surface market size, top buyers, tariffs and certifications — instantly."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <form
          onSubmit={handleSubmit}
          className="glass-strong rounded-3xl p-6 sm:p-8 grid grid-cols-1 md:grid-cols-5 gap-4"
        >
          <Field label="Country">
            <select
              data-testid="pi-country"
              value={form.country}
              onChange={(e) => setForm({ ...form, country: e.target.value })}
              className="w-full glass rounded-xl px-3 py-3 outline-none"
            >
              {countries.map((c) => (
                <option key={c.code} value={c.code} className="bg-[#0a0f24]">
                  {c.flag} {c.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Business Type">
            <select
              data-testid="pi-business-type"
              value={form.businessType}
              onChange={(e) => setForm({ ...form, businessType: e.target.value })}
              className="w-full glass rounded-xl px-3 py-3 outline-none"
            >
              {bts.map((b) => (
                <option key={b} value={b} className="bg-[#0a0f24]">{b}</option>
              ))}
            </select>
          </Field>
          <Field label="Direction">
            <select
              data-testid="pi-direction"
              value={form.direction}
              onChange={(e) => setForm({ ...form, direction: e.target.value })}
              className="w-full glass rounded-xl px-3 py-3 outline-none"
            >
              {dirs.map((d) => (
                <option key={d} value={d} className="bg-[#0a0f24]">{d}</option>
              ))}
            </select>
          </Field>
          <Field label="Product">
            <select
              data-testid="pi-product"
              value={form.product}
              onChange={(e) => setForm({ ...form, product: e.target.value })}
              className="w-full glass rounded-xl px-3 py-3 outline-none"
            >
              {products.map((p) => (
                <option key={p} value={p} className="bg-[#0a0f24]">{p}</option>
              ))}
            </select>
          </Field>
          <div className="flex items-end">
            <button data-testid="pi-submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading ? "Loading…" : <><MagnifyingGlass size={16} weight="bold" /> Analyze</>}
            </button>
          </div>
        </form>

        {result && (
          <div id="pi-result" data-testid="pi-result" className="mt-10 space-y-5">
            <div className="glass-strong rounded-3xl p-7">
              <div className="flex items-center gap-3">
                <Package size={22} weight="duotone" className="text-cyan-300" />
                <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
                  {result.direction} · {result.businessType} · {result.country}
                </div>
              </div>
              <h2 className="font-display font-extrabold text-3xl sm:text-4xl mt-2">
                {result.product}{" "}
                <span className="text-slate-500 text-xl font-mono-display">HS {result.hsCode}</span>
              </h2>
              <div className="mt-6 grid sm:grid-cols-4 gap-4">
                <Stat label="Market Size" value={result.marketSize} />
                <Stat label="YoY Growth" value={result.yoyGrowth} accent />
                <Stat label="Avg Price" value={result.averagePrice} small />
                <Stat label="Lead Time" value={result.leadTime} small />
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-5">
              <Card title="Top Markets" Icon={TrendUp}>
                <ul className="mt-4 grid grid-cols-2 gap-2.5">
                  {result.topMarkets.map((m) => (
                    <li key={m} className="glass rounded-lg px-3 py-2 text-sm">{m}</li>
                  ))}
                </ul>
              </Card>
              <Card title="Top Suppliers" Icon={Buildings}>
                <ul className="mt-4 space-y-2">
                  {result.topSuppliers.map((m) => (
                    <li key={m} className="text-sm text-slate-300">· {m}</li>
                  ))}
                </ul>
              </Card>
              <Card title="Certifications">
                <div className="mt-4 flex flex-wrap gap-2">
                  {result.certifications.map((c) => (
                    <span key={c} className="px-3 py-1.5 rounded-full text-xs font-mono-display tracking-widest bg-white/5 border border-white/10">
                      {c}
                    </span>
                  ))}
                </div>
              </Card>
              <Card title="Incoterms">
                <div className="mt-4 flex flex-wrap gap-2">
                  {result.incoterms.map((c) => (
                    <span key={c} className="px-3 py-1.5 rounded-full text-xs font-mono-display tracking-widest bg-white/5 border border-white/10">
                      {c}
                    </span>
                  ))}
                </div>
                <div className="mt-5 text-xs text-slate-400">Tariff: <span className="text-white">{result.tariff}</span></div>
                <div className="mt-1 text-xs text-slate-400">MOQ: <span className="text-white">{result.minOrderQty}</span></div>
              </Card>
            </div>

            <Card title="Market Insights">
              <ul className="mt-4 space-y-2.5">
                {result.insights.map((i, k) => (
                  <li key={k} className="flex items-start gap-2 text-sm text-slate-200">
                    <CheckCircle size={16} weight="fill" className="text-cyan-300 mt-0.5 shrink-0" />
                    {i}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">
        {label}
      </div>
      {children}
    </div>
  );
}
function Stat({ label, value, accent = false, small = false }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div>
      <div className={`mt-2 font-display font-bold ${accent ? "text-cyan-300" : ""} ${small ? "text-sm sm:text-base" : "text-xl sm:text-2xl"}`}>
        {value}
      </div>
    </div>
  );
}
function Card({ title, Icon, children }) {
  return (
    <div className="glass rounded-3xl p-6">
      <div className="flex items-center gap-2">
        {Icon && <Icon size={18} className="text-cyan-300" weight="duotone" />}
        <div className="font-display font-bold">{title}</div>
      </div>
      {children}
    </div>
  );
}
