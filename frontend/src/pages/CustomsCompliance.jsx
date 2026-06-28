import React, { useState } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import {
  ShieldCheck, CurrencyCircleDollar, Cube, Calculator, Path, Gift, Users,
  FileText, ArrowSquareOut, Brain, MagnifyingGlass, CircleNotch,
} from "@phosphor-icons/react";

const COUNTRIES = [
  ["AE", "United Arab Emirates"], ["US", "United States"], ["GB", "United Kingdom"],
  ["AU", "Australia"], ["SA", "Saudi Arabia"], ["SG", "Singapore"], ["CN", "China"],
  ["DE", "Germany"], ["JP", "Japan"], ["KR", "South Korea"],
];

const TABS = [
  ["report", "Compliance Report", ShieldCheck],
  ["fx", "Currency Exchange", CurrencyCircleDollar],
  ["cbm", "CBM Calculator", Cube],
  ["cha", "CHA Charges", Calculator],
  ["price", "Price Calculator", Calculator],
  ["freight", "Freight Routes", Path],
  ["benefits", "Govt. Benefits", Gift],
  ["chas", "CHA Directory", Users],
];

const Field = ({ label, children }) => (
  <label className="block">
    <span className="text-[11px] font-mono-display tracking-widest uppercase text-slate-400">{label}</span>
    <div className="mt-1.5">{children}</div>
  </label>
);
const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none text-white focus:border-cyan-400/40";

export default function CustomsCompliance() {
  const [tab, setTab] = useState("report");
  return (
    <>
      <SEO title="Customs & Compliance + CHA Hub · India Import-Export"
        description="India-first customs & compliance engine — duty, HSN, documents, RoDTEP & government benefits, CHA charges, CBM, live currency exchange and freight routes. Powered by the LeadNation Brain."
        path="/customs-compliance"
        keywords="India customs duty calculator, ICEGATE DGFT, HSN compliance, CHA charges, CBM calculator, RoDTEP benefits, freight routes, currency exchange" />

      <PageHero testIdPrefix="customs" label="Customs · Compliance · CHA"
        title="Clear any product. Any border."
        sub="A product-based India customs engine: duty, documents, HSN, RoDTEP & government benefits, plus CHA charges, CBM, live currency and freight routes — closed loop, all in one place." />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
          {TABS.map(([k, label, I]) => (
            <button key={k} data-testid={`customs-tab-${k}`} onClick={() => setTab(k)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm whitespace-nowrap transition-all ${tab === k ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              <I size={15} weight="duotone" />{label}
            </button>
          ))}
        </div>

        {tab === "report" && <ReportTool />}
        {tab === "fx" && <FxTool />}
        {tab === "cbm" && <CbmTool />}
        {tab === "cha" && <ChaTool />}
        {tab === "price" && <PriceTool />}
        {tab === "freight" && <FreightTool />}
        {tab === "benefits" && <BenefitsTool />}
        {tab === "chas" && <ChaDirectory />}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}

/* ---------------- Compliance Report ---------------- */
function ReportTool() {
  const [f, setF] = useState({ product: "", country: "AE", direction: "Export", hsn: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { const { data } = await api.post("/customs/profile", f); setData(data); }
    finally { setLoading(false); }
  };
  return (
    <div className="grid lg:grid-cols-12 gap-6">
      <div className="lg:col-span-4 glass-strong rounded-3xl p-6 h-fit space-y-4">
        <Field label="Product"><input data-testid="report-product" className={inputCls} placeholder="e.g. Agarbatti, Basmati Rice" value={f.product} onChange={(e) => setF({ ...f, product: e.target.value })} /></Field>
        <Field label="Direction">
          <div className="flex gap-2">
            {["Export", "Import"].map((d) => (
              <button key={d} data-testid={`report-dir-${d.toLowerCase()}`} onClick={() => setF({ ...f, direction: d })}
                className={`flex-1 py-2.5 rounded-xl text-sm ${f.direction === d ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>{d}</button>
            ))}
          </div>
        </Field>
        <Field label="Country">
          <select data-testid="report-country" className={inputCls} value={f.country} onChange={(e) => setF({ ...f, country: e.target.value })}>
            {COUNTRIES.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
          </select>
        </Field>
        <Field label="HSN (optional)"><input data-testid="report-hsn" className={inputCls} placeholder="e.g. 33074100" value={f.hsn} onChange={(e) => setF({ ...f, hsn: e.target.value })} /></Field>
        <button data-testid="report-submit" onClick={run} disabled={loading} className="btn-primary w-full justify-center disabled:opacity-50">
          {loading ? <CircleNotch size={16} className="animate-spin" /> : <MagnifyingGlass size={16} weight="bold" />} Get compliance report
        </button>
      </div>

      <div className="lg:col-span-8" data-testid="report-result">
        {!data && <div className="glass rounded-3xl p-10 text-center text-slate-400">Enter a product and country, then run the report.</div>}
        {data && (
          <div className="space-y-4">
            <div className="glass-strong rounded-3xl p-6">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-display font-bold text-xl">{data.product || "Product"} · {data.direction} → {data.country}</h3>
                {data.hsn && <span className="text-xs font-mono-display text-cyan-300">HSN {data.hsn}</span>}
              </div>
              {data.hsnTitle && <p className="text-sm text-slate-400 mt-1">{data.hsnTitle} · {data.category}</p>}
              <div className="grid sm:grid-cols-3 gap-3 mt-4">
                <Stat label="Basic Customs Duty" value={data.duty.basicCustomsDuty} />
                <Stat label="IGST" value={data.duty.igst} />
                <Stat label="Social Welfare Surcharge" value={data.duty.socialWelfareSurcharge} />
              </div>
              {data.duty.ftaApplicable && <div className="mt-3 text-sm text-emerald-300">✓ FTA preferential ({data.duty.ftaName}) — {data.duty.note}</div>}
              <div className="mt-3 text-xs text-amber-300/80">{data.note}</div>
            </div>

            <Panel title="Required Documents" icon={FileText}>
              <div className="flex flex-wrap gap-2">{data.documents.map((d, i) => <span key={i} className="glass rounded-full px-3 py-1.5 text-xs">{d}</span>)}</div>
            </Panel>
            <Panel title="CHA Clearance Steps" icon={Users}>
              <ol className="space-y-2">{data.chaSteps.map((s, i) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-cyan-300 font-bold">{i + 1}.</span>{s}</li>)}</ol>
            </Panel>
            {data.benefits.length > 0 && (
              <Panel title="Government Benefits" icon={Gift}>
                <div className="space-y-2">{data.benefits.map((b, i) => (
                  <a key={i} href={b.link} target="_blank" rel="noopener noreferrer" className="block glass rounded-xl px-4 py-2.5 hover:border-cyan-400/30">
                    <span className="text-cyan-300 font-medium text-sm">{b.scheme}</span> <span className="text-xs text-slate-400">— {b.detail}</span>
                    <ArrowSquareOut size={12} className="inline ml-1 text-cyan-300" />
                  </a>))}</div>
              </Panel>
            )}
            <div className="glass-strong rounded-3xl p-5 flex items-center gap-4 flex-wrap">
              <Brain size={28} weight="duotone" className="text-cyan-300" />
              <div className="flex-1 min-w-[200px] text-sm text-slate-300">Get a deeper, AI-written breakdown from the LeadNation Brain.</div>
              <Link to={`/brain?q=${encodeURIComponent(data.brainPrompt)}`} className="btn-primary" data-testid="report-ask-brain">Ask the Brain</Link>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(data.officialLinks).map(([k, v]) => (
                <a key={k} href={v} target="_blank" rel="noopener noreferrer" className="glass rounded-full px-3 py-1.5 text-slate-300 hover:text-cyan-300 capitalize">{k} <ArrowSquareOut size={11} className="inline" /></a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- Currency Exchange (LIVE) ---------------- */
function FxTool() {
  const [f, setF] = useState({ base: "USD", target: "INR", amount: 1000 });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const CUR = ["USD", "INR", "EUR", "GBP", "AED", "CNY", "JPY", "AUD", "SGD", "SAR"];
  const run = async () => {
    setLoading(true);
    try { const { data } = await api.get("/customs/fx", { params: f }); setData(data); }
    finally { setLoading(false); }
  };
  return (
    <ToolCard title="Live Currency Exchange" desc="Real-time mid-market rates (updated hourly).">
      <div className="grid sm:grid-cols-4 gap-3 items-end">
        <Field label="Amount"><input data-testid="fx-amount" type="number" className={inputCls} value={f.amount} onChange={(e) => setF({ ...f, amount: parseFloat(e.target.value) || 0 })} /></Field>
        <Field label="From"><select data-testid="fx-base" className={inputCls} value={f.base} onChange={(e) => setF({ ...f, base: e.target.value })}>{CUR.map((c) => <option key={c}>{c}</option>)}</select></Field>
        <Field label="To"><select data-testid="fx-target" className={inputCls} value={f.target} onChange={(e) => setF({ ...f, target: e.target.value })}>{CUR.map((c) => <option key={c}>{c}</option>)}</select></Field>
        <button data-testid="fx-submit" onClick={run} disabled={loading} className="btn-primary justify-center disabled:opacity-50">{loading ? <CircleNotch size={16} className="animate-spin" /> : "Convert"}</button>
      </div>
      {data?.ok && (
        <div className="mt-5 glass-strong rounded-2xl p-6" data-testid="fx-result">
          <div className="font-display font-extrabold text-3xl text-gradient">{data.amount} {data.base} = {data.converted.toLocaleString()} {data.target}</div>
          <div className="text-sm text-slate-400 mt-1">1 {data.base} = {data.rate} {data.target} · <span className="text-emerald-300">{data.live ? "live" : "cached"}</span> · {data.source}</div>
        </div>
      )}
      {data && !data.ok && <div className="mt-4 text-amber-300 text-sm">Rate unavailable. Try another pair.</div>}
    </ToolCard>
  );
}

/* ---------------- CBM Calculator ---------------- */
function CbmTool() {
  const [f, setF] = useState({ length_cm: 100, width_cm: 80, height_cm: 60, quantity: 10, weight_kg: 25 });
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.post("/customs/cbm", f); setData(data); };
  return (
    <ToolCard title="CBM & Volumetric Weight Calculator" desc="Calculate shipment volume, chargeable weight and container fit.">
      <div className="grid sm:grid-cols-5 gap-3">
        {[["length_cm", "Length (cm)"], ["width_cm", "Width (cm)"], ["height_cm", "Height (cm)"], ["quantity", "Quantity"], ["weight_kg", "Unit wt (kg)"]].map(([k, l]) => (
          <Field key={k} label={l}><input data-testid={`cbm-${k}`} type="number" className={inputCls} value={f[k]} onChange={(e) => setF({ ...f, [k]: parseFloat(e.target.value) || 0 })} /></Field>
        ))}
      </div>
      <button data-testid="cbm-submit" onClick={run} className="btn-primary mt-4">Calculate CBM</button>
      {data && (
        <div className="mt-5 grid sm:grid-cols-3 gap-3" data-testid="cbm-result">
          <Stat label="Total CBM" value={`${data.totalCBM} m³`} />
          <Stat label="Air chargeable wt" value={`${data.airChargeableWeightKg} kg`} />
          <Stat label="Sea chargeable" value={`${data.seaChargeableTons} t`} />
          <Stat label="20ft fill" value={data.container20ft} />
          <Stat label="40ft fill" value={data.container40ft} />
          <Stat label="Recommendation" value={data.recommendation} />
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- CHA Charges ---------------- */
function ChaTool() {
  const [f, setF] = useState({ shipmentValue: 500000, mode: "sea", direction: "Export", containers: 1 });
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.post("/customs/cha-charges", f); setData(data); };
  return (
    <ToolCard title="CHA Charges Estimator" desc="Indicative customs broker & clearance charges for your shipment.">
      <div className="grid sm:grid-cols-4 gap-3">
        <Field label="Shipment value (₹)"><input data-testid="cha-value" type="number" className={inputCls} value={f.shipmentValue} onChange={(e) => setF({ ...f, shipmentValue: parseFloat(e.target.value) || 0 })} /></Field>
        <Field label="Mode"><select data-testid="cha-mode" className={inputCls} value={f.mode} onChange={(e) => setF({ ...f, mode: e.target.value })}><option value="sea">Sea</option><option value="air">Air</option></select></Field>
        <Field label="Direction"><select data-testid="cha-dir" className={inputCls} value={f.direction} onChange={(e) => setF({ ...f, direction: e.target.value })}><option>Export</option><option>Import</option></select></Field>
        <Field label="Containers"><input data-testid="cha-containers" type="number" className={inputCls} value={f.containers} onChange={(e) => setF({ ...f, containers: parseInt(e.target.value) || 1 })} /></Field>
      </div>
      <button data-testid="cha-submit" onClick={run} className="btn-primary mt-4">Estimate charges</button>
      {data && (
        <div className="mt-5 glass-strong rounded-2xl p-5" data-testid="cha-result">
          {data.items.map((i, k) => <div key={k} className="flex justify-between py-1.5 text-sm border-b border-white/5"><span className="text-slate-300">{i.label}</span><span>₹{i.amount.toLocaleString()}</span></div>)}
          <div className="flex justify-between pt-3 font-display font-bold text-lg"><span>Total</span><span className="text-cyan-300">₹{data.total.toLocaleString()}</span></div>
          <div className="text-xs text-slate-500 mt-2">{data.note}</div>
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- Price Calculator ---------------- */
function PriceTool() {
  const [f, setF] = useState({ productCost: 1000, quantity: 100, freight: 15000, insurance: 2000, dutyPct: 5, marginPct: 20 });
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.post("/customs/price", f); setData(data); };
  return (
    <ToolCard title="Landed & Selling Price Calculator" desc="Compute CIF, duty, landed cost and your quote with margin.">
      <div className="grid sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[["productCost", "Unit cost"], ["quantity", "Qty"], ["freight", "Freight"], ["insurance", "Insurance"], ["dutyPct", "Duty %"], ["marginPct", "Margin %"]].map(([k, l]) => (
          <Field key={k} label={l}><input data-testid={`price-${k}`} type="number" className={inputCls} value={f[k]} onChange={(e) => setF({ ...f, [k]: parseFloat(e.target.value) || 0 })} /></Field>
        ))}
      </div>
      <button data-testid="price-submit" onClick={run} className="btn-primary mt-4">Calculate price</button>
      {data && (
        <div className="mt-5 grid sm:grid-cols-3 gap-3" data-testid="price-result">
          <Stat label="CIF value" value={data.cif.toLocaleString()} />
          <Stat label="Duty" value={data.duty.toLocaleString()} />
          <Stat label="Landed cost" value={data.landedCost.toLocaleString()} />
          <Stat label="Landed / unit" value={data.landedPerUnit.toLocaleString()} />
          <Stat label="Selling price" value={data.sellingPrice.toLocaleString()} />
          <Stat label="Profit" value={data.profit.toLocaleString()} />
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- Freight Routes ---------------- */
function FreightTool() {
  const [to, setTo] = useState("AE");
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.get("/customs/freight-routes", { params: { to } }); setData(data); };
  return (
    <ToolCard title="Freight Routes (from India)" desc="Indicative sea & air lanes and transit times.">
      <div className="flex gap-3 items-end">
        <Field label="Destination"><select data-testid="freight-to" className={inputCls} value={to} onChange={(e) => setTo(e.target.value)}>{COUNTRIES.map(([c, n]) => <option key={c} value={c}>{n}</option>)}</select></Field>
        <button data-testid="freight-submit" onClick={run} className="btn-primary">Show routes</button>
      </div>
      {data && (
        <div className="mt-5 space-y-3" data-testid="freight-result">
          {data.routes.map((r, i) => (
            <div key={i} className="glass rounded-2xl p-4 flex items-center gap-4">
              <span className="text-xs font-mono-display uppercase px-2 py-1 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-300">{r.mode}</span>
              <div className="flex-1"><div className="font-medium">{r.lane}</div><div className="text-xs text-slate-400">{r.type}</div></div>
              <div className="text-sm text-cyan-300">{r.transit}</div>
            </div>
          ))}
          <div className="text-xs text-amber-300/80">{data.tip}</div>
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- Govt Benefits ---------------- */
function BenefitsTool() {
  const [direction, setDirection] = useState("Export");
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.get("/customs/benefits", { params: { direction } }); setData(data); };
  return (
    <ToolCard title="Government Benefits Finder" desc="Schemes and incentives you can claim.">
      <div className="flex gap-3 items-end">
        <Field label="Direction"><select data-testid="benefits-dir" className={inputCls} value={direction} onChange={(e) => setDirection(e.target.value)}><option>Export</option><option>Import</option></select></Field>
        <button data-testid="benefits-submit" onClick={run} className="btn-primary">Find benefits</button>
      </div>
      {data && (
        <div className="mt-5 space-y-2" data-testid="benefits-result">
          {data.benefits.map((b, i) => (
            <a key={i} href={b.link} target="_blank" rel="noopener noreferrer" className="block glass rounded-xl px-4 py-3 hover:border-cyan-400/30">
              <span className="text-cyan-300 font-medium">{b.scheme}</span> <span className="text-sm text-slate-400">— {b.detail}</span>
              <ArrowSquareOut size={12} className="inline ml-1 text-cyan-300" />
            </a>
          ))}
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- CHA Directory ---------------- */
function ChaDirectory() {
  const [port, setPort] = useState("");
  const [data, setData] = useState(null);
  const run = async () => { const { data } = await api.get("/customs/cha-directory", { params: { port } }); setData(data); };
  React.useEffect(() => { run(); /* eslint-disable-next-line */ }, []);
  return (
    <ToolCard title="Customs House Agents (CHA) Directory" desc="Verified customs brokers by port.">
      <div className="flex gap-3 items-end">
        <Field label="Port / City"><input data-testid="chas-port" className={inputCls} placeholder="e.g. Nhava Sheva, Mundra" value={port} onChange={(e) => setPort(e.target.value)} /></Field>
        <button data-testid="chas-submit" onClick={run} className="btn-primary">Search</button>
      </div>
      {data && (
        <div className="mt-5 grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="chas-result">
          {data.chas.map((c, i) => (
            <div key={i} className="glass rounded-2xl p-5">
              <div className="flex items-center justify-between"><div className="font-display font-bold">{c.name}</div>{c.verified && <ShieldCheck size={18} weight="fill" className="text-cyan-300" />}</div>
              <div className="text-xs text-slate-400 mt-1">{c.port} · {c.city}</div>
              <div className="text-sm mt-2">{c.services}</div>
              <a href={`https://wa.me/918237161088?text=${encodeURIComponent(`Hi LeadNation, connect me with CHA: ${c.name} (${c.port}).`)}`} target="_blank" rel="noopener noreferrer" className="btn-ghost !py-2 text-xs mt-3 inline-flex justify-center">Connect via WhatsApp</a>
            </div>
          ))}
        </div>
      )}
    </ToolCard>
  );
}

/* ---------------- shared ---------------- */
const Stat = ({ label, value }) => (
  <div className="glass rounded-xl px-4 py-3">
    <div className="font-display font-bold text-white">{value}</div>
    <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">{label}</div>
  </div>
);
const Panel = ({ title, icon: I, children }) => (
  <div className="glass rounded-3xl p-6">
    <div className="text-xs font-mono-display tracking-[0.25em] uppercase text-cyan-300 flex items-center gap-2 mb-3">{I && <I size={14} weight="duotone" />}{title}</div>
    {children}
  </div>
);
const ToolCard = ({ title, desc, children }) => (
  <div className="glass-strong rounded-3xl p-6 sm:p-8">
    <h3 className="font-display font-bold text-2xl">{title}</h3>
    <p className="text-sm text-slate-400 mt-1 mb-5">{desc}</p>
    {children}
  </div>
);
