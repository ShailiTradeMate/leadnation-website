import React, { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ReportButton } from "@/components/TradeIntelReport";
import {
  ShieldCheck, CurrencyCircleDollar, Cube, Calculator, Path, Gift, Users,
  FileText, ArrowSquareOut, Brain, MagnifyingGlass, CircleNotch, Handshake,
  ChartLineUp, TrendUp, TrendDown, Globe, Scales, ArrowRight, Sparkle,
  Truck, Coins, Lightning, Stack, Printer, ChartBar, Strategy,
} from "@phosphor-icons/react";

const CUR = ["USD", "EUR", "GBP", "INR", "AED", "CNY", "JPY", "AUD", "SGD", "SAR", "CAD", "CHF"];
const fmtCur = (v, cur) => {
  if (v === null || v === undefined || isNaN(v)) return "—";
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(v); }
  catch (_) { return `${Number(v).toLocaleString()} ${cur}`; }
};
const num = (v) => (v === "" || v === null || v === undefined ? 0 : parseFloat(v) || 0);

const COUNTRIES = [
  ["AE", "United Arab Emirates"], ["US", "United States"], ["GB", "United Kingdom"],
  ["AU", "Australia"], ["SA", "Saudi Arabia"], ["SG", "Singapore"], ["CN", "China"],
  ["DE", "Germany"], ["JP", "Japan"], ["KR", "South Korea"],
];

const TABS = [
  ["compile", "Trade Command Center", Lightning],
  ["report", "Compliance Report", ShieldCheck],
  ["trade", "Trade Statistics", ChartLineUp],
  ["duty", "Duty & Benefits", Scales],
  ["terms", "Trade Terms", Handshake],
  ["fx", "Currency Exchange", CurrencyCircleDollar],
  ["cbm", "CBM Calculator", Cube],
  ["freight", "Freight Routes", Path],
  ["benefits", "Govt. Benefits", Gift],
];

const Field = ({ label, children }) => (
  <label className="block">
    <span className="text-[11px] font-mono-display tracking-widest uppercase text-slate-400">{label}</span>
    <div className="mt-1.5">{children}</div>
  </label>
);
const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none text-white focus:border-cyan-400/40";

export default function CustomsCompliance() {
  const [tab, setTab] = useState("compile");
  return (
    <>
      <SEO title="LeadNation Trade Command Center™ — AI Global Trade Operating System"
        description="The world's first AI-powered global trade operating system. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across 195 markets, quote in your currency and any global currency, check duty, FTA benefits, incentives and routes — analysed by the LeadNation Brain."
        path="/customs-compliance"
        keywords="FOB CIF calculator, landed cost calculator, export costing tool, buyer landed cost comparison, customs duty calculator, FTA checker, RoDTEP incentives, global trade operating system, export quotation tool, dual currency trade quote" />

      <PageHero testIdPrefix="customs" label="LeadNation Trade Command Center™"
        title="The World's First AI-Powered Global Trade Operating System."
        sub="Plan, cost, comply, price and ship from one screen. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across markets, quote in your currency and any global currency, and let the LeadNation Brain analyse every number — for any product across 195 countries." />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
          {TABS.map(([k, label, I]) => (
            <button key={k} data-testid={`customs-tab-${k}`} onClick={() => setTab(k)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm whitespace-nowrap transition-all ${tab === k ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              <I size={15} weight="duotone" />{label}
            </button>
          ))}
        </div>

        {tab === "compile" && <CommandCenterTool />}
        {tab === "report" && <ReportTool />}
        {tab === "trade" && <TradeStatsTool />}
        {tab === "duty" && <DutyBenefitsTool />}
        {tab === "terms" && <TradeTermsTool />}
        {tab === "fx" && <FxTool />}
        {tab === "cbm" && <CbmTool />}
        {tab === "freight" && <FreightTool />}
        {tab === "benefits" && <BenefitsTool />}
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

const fmtUSD = (v) => {
  v = Number(v) || 0;
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

/* ---------------- lightweight markdown for Brain narrative ---------------- */
function MarkdownLite({ text }) {
  const lines = (text || "").split("\n");
  const out = []; let bullets = [];
  const inline = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith("**") && p.endsWith("**")
    ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span> : <span key={j}>{p}</span>);
  const flush = (k) => { if (bullets.length) { out.push(<ul key={"u" + k} className="list-disc pl-5 space-y-1 text-sm text-slate-300">{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>); bullets = []; } };
  lines.forEach((raw, k) => {
    const l = raw.trim();
    if (!l || l === "---") { flush(k); return; }
    if (l.startsWith("### ")) { flush(k); out.push(<div key={k} className="font-display font-bold text-base mt-3 text-white">{inline(l.slice(4))}</div>); }
    else if (l.startsWith("## ")) { flush(k); out.push(<div key={k} className="font-display font-bold text-lg mt-4 text-cyan-200">{inline(l.slice(3))}</div>); }
    else if (l.startsWith("- ") || l.startsWith("* ")) { bullets.push(l.replace(/^[-*]\s/, "")); }
    else { flush(k); out.push(<p key={k} className="text-sm leading-relaxed text-slate-200">{inline(l)}</p>); }
  });
  flush("end");
  return <div className="space-y-1.5">{out}</div>;
}

/* ---------------- Trade Command Center — flagship costing & quotation ---------------- */
function CommandCenterTool() {
  const [q, setQ] = useState("");
  const [sugg, setSugg] = useState([]);
  const [openSugg, setOpenSugg] = useState(false);
  const [hs, setHs] = useState("");
  const [exporter, setExporter] = useState("356");
  const [importer, setImporter] = useState("842");
  const [countries, setCountries] = useState([]);
  const [qty, setQty] = useState(1);
  const [unit, setUnit] = useState("unit");
  const [txnCur, setTxnCur] = useState("USD");
  const [globalCur, setGlobalCur] = useState("EUR");
  const [margin, setMargin] = useState("");
  const [costs, setCosts] = useState({ exw: "", packing: "", inland: "", thc: "", customsDocs: "", freight: "", insurance: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [advisor, setAdvisor] = useState("");
  const [advLoading, setAdvLoading] = useState(false);
  const lastPick = useRef("");

  React.useEffect(() => { api.get("/command-center/markets").then(({ data }) => setCountries(data.countries || [])); }, []);
  React.useEffect(() => {
    const text = q.trim();
    if (text === lastPick.current) return;
    if (text.length < 2 || /^\d+$/.test(text)) { setSugg([]); return; }
    const t = setTimeout(async () => {
      try { const { data } = await api.get("/trade-intel/hs-search", { params: { q: text, limit: 8 } }); setSugg(data.results || []); setOpenSugg(true); } catch (_) {}
    }, 300);
    return () => clearTimeout(t);
  }, [q]);
  const pick = (s) => { const label = `${s.hs6} · ${s.description}`; lastPick.current = label; setQ(label); setHs(s.hs6); setSugg([]); setOpenSugg(false); };

  const COST_FIELDS = [
    ["exw", "Ex-Works (EXW) price", "Factory gate price"],
    ["packing", "Export packing & labelling", "Cartons, marks, palletising"],
    ["inland", "Inland / local transport", "Factory → origin port"],
    ["thc", "Port handling (THC)", "Stuffing, loading, port charges"],
    ["customsDocs", "Customs & documentation", "CHA, shipping bill, certs"],
    ["freight", "Ocean / air freight", "Main-leg freight to destination"],
    ["insurance", "Marine / cargo insurance", "≈0.1%–0.5% of CIF"],
  ];
  // live client-side preview as the user types
  const fobUnit = num(costs.exw) + num(costs.packing) + num(costs.inland) + num(costs.thc) + num(costs.customsDocs);
  const cifUnit = fobUnit + num(costs.freight) + num(costs.insurance);

  const run = async () => {
    if (!hs && !q.trim()) { setErr("Search and pick a product, or enter an HS code."); return; }
    if (fobUnit <= 0) { setErr("Enter at least the Ex-Works price to build your cost waterfall."); return; }
    setLoading(true); setErr(""); setData(null); setAdvisor(""); setOpenSugg(false);
    try {
      const { data } = await api.post("/command-center/quote", {
        hs, product: hs ? "" : q.trim(), exporter, importer,
        quantity: num(qty) || 1, unit,
        costs: { exw: num(costs.exw), packing: num(costs.packing), inland: num(costs.inland), thc: num(costs.thc), customsDocs: num(costs.customsDocs), freight: num(costs.freight), insurance: num(costs.insurance) },
        marginPct: num(margin), transactionCurrency: txnCur, globalCurrency: globalCur,
      }, { timeout: 90000 });
      if (data.ok) {
        setData(data);
        setAdvLoading(true);
        api.post("/command-center/insights", { quote: data })
          .then(({ data: ins }) => { if (ins.ok) setAdvisor(ins.advisor || ""); })
          .catch(() => {}).finally(() => setAdvLoading(false));
      } else setErr(data.error || "Could not build your quote.");
    } catch (_) { setErr("Quote failed — please try again."); }
    finally { setLoading(false); }
  };

  const tc = txnCur;
  const d = data;

  return (
    <div className="space-y-5">
      {/* INTRO */}
      <div className="glass-strong rounded-3xl p-6 sm:p-8 border border-cyan-400/20">
        <div className="flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
          <Lightning size={14} weight="duotone" /> LeadNation Trade Command Center™
        </div>
        <h3 className="font-display font-extrabold text-2xl sm:text-3xl mt-2">Your entire deal, costed and analysed in one screen.</h3>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl">Build the full Ex-Works → FOB → CIF → landed-cost waterfall, compare what your buyer pays across markets, quote in your own currency <span className="text-cyan-300">and</span> any globally-traded currency, and let the LeadNation Brain flag savings, risks and the best market — for any product across 195 countries.</p>
        <Link to="/command-center" data-testid="cc-tab-open-workspace" className="btn-primary mt-4 inline-flex"><Lightning size={15} weight="bold" /> Open the full workspace (Trade Projects, Brain, PDF) <ArrowRight size={15} weight="bold" /></Link>
      </div>

      {/* SETUP */}
      <ToolCard title="1 · Define your trade lane" desc="Pick the product, the route, quantity and the two currencies you want to quote in.">
        <div className="grid lg:grid-cols-6 gap-3 items-end">
          <div className="lg:col-span-2 relative">
            <Field label="Product or HS code">
              <input data-testid="cc-search" className={inputCls} value={q}
                onChange={(e) => { setQ(e.target.value); setHs(""); }} onFocus={() => sugg.length && setOpenSugg(true)}
                placeholder="e.g. Basmati Rice, Turmeric, or 100630" />
            </Field>
            {openSugg && sugg.length > 0 && (
              <div data-testid="cc-suggestions" className="absolute z-30 mt-1 w-full glass-strong rounded-2xl border border-white/10 max-h-72 overflow-auto shadow-2xl">
                {sugg.map((s) => (
                  <button key={s.hs6} type="button" data-testid={`cc-sugg-${s.hs6}`} onClick={() => pick(s)}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/5 flex items-center gap-3 border-b border-white/5 last:border-0">
                    <span className="font-mono-display text-xs text-cyan-300 shrink-0">{s.hs6}</span>
                    <span className="text-sm text-slate-200 truncate">{s.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <Field label="Export from">
            <select data-testid="cc-exporter" className={inputCls} value={exporter} onChange={(e) => setExporter(e.target.value)}>
              {countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Import to">
            <select data-testid="cc-importer" className={inputCls} value={importer} onChange={(e) => setImporter(e.target.value)}>
              {countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Quantity">
            <div className="flex gap-2">
              <input data-testid="cc-qty" type="number" className={inputCls} value={qty} onChange={(e) => setQty(e.target.value)} />
              <input data-testid="cc-unit" className={`${inputCls} w-24`} value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="unit" />
            </div>
          </Field>
        </div>
        <div className="grid sm:grid-cols-3 gap-3 mt-3">
          <Field label="Your currency (transaction)">
            <select data-testid="cc-txn-currency" className={inputCls} value={txnCur} onChange={(e) => setTxnCur(e.target.value)}>{CUR.map((c) => <option key={c}>{c}</option>)}</select>
          </Field>
          <Field label="Quote also in (global currency)">
            <select data-testid="cc-global-currency" className={inputCls} value={globalCur} onChange={(e) => setGlobalCur(e.target.value)}>{CUR.map((c) => <option key={c}>{c}</option>)}</select>
          </Field>
          <Field label="Your margin %">
            <input data-testid="cc-margin" type="number" className={inputCls} value={margin} onChange={(e) => setMargin(e.target.value)} placeholder="e.g. 15" />
          </Field>
        </div>
      </ToolCard>

      {/* COST BUILD-UP */}
      <ToolCard title="2 · Cost build-up — Ex-Works → FOB → CIF" desc="Enter your costs per unit (in your transaction currency). FOB and CIF update live as you type.">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {COST_FIELDS.map(([k, label, note]) => (
            <div key={k}>
              <Field label={`${label} (per ${unit})`}>
                <input data-testid={`cc-cost-${k}`} type="number" className={inputCls} value={costs[k]}
                  onChange={(e) => setCosts({ ...costs, [k]: e.target.value })} placeholder="0" />
              </Field>
              <div className="text-[10px] text-slate-500 mt-1">{note}</div>
            </div>
          ))}
        </div>
        <div className="grid sm:grid-cols-2 gap-3 mt-4">
          <div className="glass rounded-2xl px-5 py-4 flex items-center justify-between" data-testid="cc-fob-preview">
            <div><div className="text-[10px] text-slate-400 uppercase tracking-wider">FOB / {unit}</div><div className="text-[10px] text-slate-500">Items 1–5 · price at origin port</div></div>
            <div className="font-display font-extrabold text-2xl text-cyan-300">{fmtCur(fobUnit, tc)}</div>
          </div>
          <div className="glass rounded-2xl px-5 py-4 flex items-center justify-between" data-testid="cc-cif-preview">
            <div><div className="text-[10px] text-slate-400 uppercase tracking-wider">CIF / {unit}</div><div className="text-[10px] text-slate-500">FOB + freight + insurance</div></div>
            <div className="font-display font-extrabold text-2xl text-gradient">{fmtCur(cifUnit, tc)}</div>
          </div>
        </div>
        <button data-testid="cc-submit" onClick={run} disabled={loading} className="btn-primary mt-5 disabled:opacity-50">
          {loading ? <><CircleNotch size={16} className="animate-spin" /> Building your command center…</> : <><Lightning size={16} weight="bold" /> Generate Command Center</>}
        </button>
        {err && <div data-testid="cc-error" className="mt-3 text-amber-300 text-sm">{err}</div>}
        {loading && <div className="mt-2 text-xs text-slate-500">Pulling live tariffs, FX and buyer landed costs across markets — first run for a new lane can take ~10s.</div>}
      </ToolCard>

      {d && (
        <div className="space-y-5" data-testid="cc-result" id="cc-print">
          {/* KPI cards */}
          <div className="glass-strong rounded-3xl p-6">
            <div className="flex items-center gap-2 text-sm flex-wrap mb-4">
              <Lightning size={18} weight="duotone" className="text-cyan-300" />
              <span className="font-display font-bold text-lg">Quote summary</span>
              <span className="ml-auto font-mono-display text-xs text-cyan-300">HS {d.hsCode} · {d.exporter.name} → {d.importer.name} · {d.quantity} {d.unit}</span>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="cc-kpis">
              <KpiCard label="FOB value" main={fmtCur(d.fob.total, tc)} sub1={fmtCur(d.currency.converted.fob.global, d.currency.global)} sub2={d.currency.converted.fob.exporterLocal} subCur={d.currency.exporterLocal} accent="text-cyan-300" />
              <KpiCard label="CIF value" main={fmtCur(d.cif.total, tc)} sub1={fmtCur(d.currency.converted.cif.global, d.currency.global)} sub2={d.currency.converted.cif.exporterLocal} subCur={d.currency.exporterLocal} accent="text-gradient" />
              <KpiCard label={`Landed in ${d.importer.name}`} main={fmtCur(d.destination.landed, tc)} sub1={fmtCur(d.currency.converted.landed.global, d.currency.global)} sub2={d.currency.converted.landed.exporterLocal} subCur={d.currency.exporterLocal} accent="text-emerald-300" />
              <KpiCard label={`Your selling price (${d.pricing.marginPct}% margin)`} main={fmtCur(d.pricing.selling, tc)} sub1={fmtCur(d.currency.converted.selling.global, d.currency.global)} sub2={d.pricing.profit} subCur={tc} subLabel="profit" accent="text-violet-300" />
            </div>
            <div className="flex flex-wrap gap-2 mt-4 no-print">
              <button data-testid="cc-print-btn" onClick={() => window.print()} className="btn-ghost"><Printer size={15} weight="bold" /> Print / Save quote (PDF)</button>
              <Link to={`/brain?q=${encodeURIComponent(`Full export plan for HS ${d.hsCode} (${d.description}) from ${d.exporter.name} to ${d.importer.name}`)}`} className="btn-ghost" data-testid="cc-ask-brain"><Brain size={15} weight="bold" /> Ask the Brain</Link>
            </div>
          </div>

          {/* AI Trade Advisor */}
          <div className="glass-strong rounded-3xl p-6" data-testid="cc-advisor">
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <Brain size={18} weight="duotone" className="text-cyan-300" />
              <span className="font-display font-bold text-lg">AI Trade Advisor</span>
              <span className="text-[10px] uppercase tracking-wider text-slate-400 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/20">LeadNation Brain</span>
            </div>
            <div className="mt-4">
              {advLoading && <div className="text-sm text-slate-400 flex items-center gap-2"><CircleNotch size={16} className="animate-spin" /> Analysing your costing, markets, savings and risks…</div>}
              {!advLoading && advisor && <MarkdownLite text={advisor} />}
              {!advLoading && !advisor && <p className="text-sm text-slate-500">Advisor unavailable for this run.</p>}
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-5">
            {/* Cost waterfall */}
            <Panel title="Cost Waterfall (per unit · total)" icon={Stack}>
              <div className="space-y-1" data-testid="cc-waterfall">
                {d.waterfall.map((w, i) => (
                  <div key={i} className={`flex items-center justify-between py-1.5 text-sm ${w.milestone ? "border-y border-cyan-400/20 my-1 font-semibold" : "border-b border-white/5"}`}>
                    <span className={w.milestone ? "text-cyan-300" : "text-slate-300"}>{w.stage}</span>
                    <span className="text-right"><span className={w.milestone ? "text-cyan-300" : "text-slate-200"}>{fmtCur(w.total, tc)}</span> <span className="text-[10px] text-slate-500">({fmtCur(w.perUnit, tc)}/{d.unit})</span></span>
                  </div>
                ))}
              </div>
            </Panel>

            {/* Destination duty/tax */}
            <Panel title={`Duty & Tax into ${d.importer.name}`} icon={Scales}>
              <div className="space-y-2.5 text-sm" data-testid="cc-destination">
                <Row label="Import duty rate" value={d.destination.dutyRate != null ? `${d.destination.dutyRate}% ${d.destination.dutyType || ""}${d.destination.fta ? " · FTA" : ""}` : "No tariff record"} />
                <Row label="Duty payable" value={fmtCur(d.destination.duty, tc)} />
                <Row label={`VAT / GST (${d.destination.vatRate}%)`} value={fmtCur(d.destination.vat, tc)} />
                <div className="flex justify-between pt-2 border-t border-white/10 font-semibold"><span>Landed cost</span><span className="text-emerald-300">{fmtCur(d.destination.landed, tc)}</span></div>
                {d.destination.fta && <div className="text-xs text-emerald-300/90 mt-1">✓ Preferential / FTA rate applied for {d.exporter.name} origin.</div>}
              </div>
            </Panel>
          </div>

          {/* Buyer landed-cost comparison */}
          <Panel title="Best markets — what your buyer pays (landed)" icon={ChartBar}>
            <div className="overflow-x-auto" data-testid="cc-comparison">
              <table className="w-full text-sm min-w-[640px]">
                <thead>
                  <tr className="text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                    <th className="text-left py-2">Destination</th><th className="text-right">Your CIF</th><th className="text-right">Buyer duty</th><th className="text-right">Buyer VAT</th><th className="text-right">Buyer total</th><th className="text-left pl-3">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {d.comparison.map((c, i) => (
                    <tr key={c.code} data-testid={`cc-market-${c.code}`} className={`border-b border-white/5 ${i === 0 ? "bg-emerald-500/5" : ""}`}>
                      <td className="py-2.5 font-medium">{i === 0 && <span className="text-emerald-300 mr-1">★</span>}{c.country}</td>
                      <td className="text-right text-slate-300">{fmtCur(c.cif, tc)}</td>
                      <td className="text-right text-slate-300">{c.dutyRate != null ? `${fmtCur(c.duty, tc)} (${c.dutyRate}%)` : "—"}</td>
                      <td className="text-right text-slate-300">{fmtCur(c.vat, tc)} ({c.vatRate}%)</td>
                      <td className="text-right font-semibold text-cyan-300">{fmtCur(c.buyerTotal, tc)}</td>
                      <td className="pl-3 text-xs text-emerald-300/80">{c.note || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-[11px] text-slate-500 mt-2">Lowest buyer landed cost ranked first — your most price-competitive markets. Duty/VAT are indicative; confirm at clearance.</div>
          </Panel>

          <div className="grid lg:grid-cols-2 gap-5">
            {/* Currency */}
            <Panel title="Multi-currency quote" icon={Coins}>
              <div className="text-sm space-y-2" data-testid="cc-currency">
                <Row label="Transaction currency" value={d.currency.transaction} />
                <Row label="Global quote currency" value={`${d.currency.global}${d.currency.rates[d.currency.global] ? ` · 1 ${tc} = ${d.currency.rates[d.currency.global]} ${d.currency.global}` : ""}`} />
                <Row label={`Exporter local (${d.exporter.name})`} value={d.currency.exporterLocal} />
                <div className="text-[11px] text-slate-500 pt-1">{d.currency.source}</div>
              </div>
            </Panel>
            {/* Incentives + routes */}
            <Panel title="Incentives & routes" icon={Gift}>
              <div className="space-y-2" data-testid="cc-incentives">
                {d.incentives.length > 0 ? d.incentives.map((it, i) => (
                  <div key={i} className="text-sm"><span className="text-cyan-300 font-medium">{it.scheme}</span> <span className="text-emerald-300">{it.value}</span><div className="text-xs text-slate-400">{it.detail}</div></div>
                )) : <div className="text-sm text-slate-400">No origin-specific export incentives detected for {d.exporter.name}.</div>}
              </div>
              <div className="mt-3 pt-3 border-t border-white/10 space-y-1.5">
                {d.routes.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm"><Truck size={14} className="text-cyan-300" /><span className="font-medium">{r.mode}</span><span className="text-xs text-slate-400">· {r.transit}</span></div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="text-[11px] text-slate-500 px-1">Sources: {d.sources.join(" · ")}. Figures are indicative for planning; verify duty, tax and freight at the time of shipment.</div>
        </div>
      )}
    </div>
  );
}

const Row = ({ label, value }) => (
  <div className="flex justify-between gap-3"><span className="text-slate-400">{label}</span><span className="text-slate-200 text-right">{value}</span></div>
);
const KpiCard = ({ label, main, sub1, sub2, subCur, subLabel, accent }) => (
  <div className="glass rounded-2xl px-5 py-4">
    <div className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</div>
    <div className={`font-display font-extrabold text-2xl mt-1 ${accent}`}>{main}</div>
    {sub1 && sub1 !== "—" && <div className="text-xs text-slate-400 mt-1">≈ {sub1}</div>}
    {sub2 != null && sub2 !== "—" && (
      <div className="text-[11px] text-slate-500">{subLabel ? `${subLabel}: ` : "≈ "}{fmtCur(sub2, subCur)}</div>
    )}
  </div>
);

/* ---------------- Duty & Benefits (global tariffs + India + RoDTEP) ---------------- */
function DutyBenefitsTool() {
  const [q, setQ] = useState("");
  const [sugg, setSugg] = useState([]);
  const [openSugg, setOpenSugg] = useState(false);
  const [hs, setHs] = useState("");
  const [origin, setOrigin] = useState("356");
  const [dest, setDest] = useState("842");
  const [countries, setCountries] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const lastPick = useRef("");

  React.useEffect(() => { api.get("/duty/countries").then(({ data }) => setCountries(data.countries || [])); }, []);
  React.useEffect(() => {
    const text = q.trim();
    if (text === lastPick.current) return;
    if (text.length < 2 || /^\d+$/.test(text)) { setSugg([]); return; }
    const t = setTimeout(async () => {
      try { const { data } = await api.get("/trade-intel/hs-search", { params: { q: text, limit: 8 } }); setSugg(data.results || []); setOpenSugg(true); } catch (_) {}
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const run = async (code) => {
    const hs6 = (code || hs || q.replace(/\D/g, "")).slice(0, 6);
    if (hs6.length < 6) { setErr("Search a product or enter a 6-digit HS code."); return; }
    setLoading(true); setErr(""); setData(null); setOpenSugg(false);
    try {
      const { data } = await api.get("/duty/lookup", { params: { hs: hs6, origin, destination: dest } });
      if (data.ok) setData(data); else setErr(data.error || "No data.");
    } catch (_) { setErr("Unable to fetch duty data."); }
    finally { setLoading(false); }
  };
  const pick = (s) => { const label = `${s.hs6} · ${s.description}`; lastPick.current = label; setQ(label); setHs(s.hs6); setSugg([]); setOpenSugg(false); };

  return (
    <div className="space-y-5">
      <ToolCard title="Duty & Benefits — any country, any product" desc="Real import tariffs worldwide (World Bank WITS / UNCTAD TRAINS) with India BCD/IGST/SWS breakdown and DGFT RoDTEP export benefit. Pick your origin and destination country.">
        <div className="grid lg:grid-cols-4 gap-3 items-end">
          <div className="lg:col-span-2 relative">
            <Field label="Product or HS code">
              <input data-testid="duty-search" className={inputCls} value={q}
                onChange={(e) => { setQ(e.target.value); setHs(""); }} onFocus={() => sugg.length && setOpenSugg(true)}
                placeholder="e.g. Coffee, Cars, or 090111" />
            </Field>
            {openSugg && sugg.length > 0 && (
              <div data-testid="duty-suggestions" className="absolute z-20 mt-1 w-full glass-strong rounded-2xl border border-white/10 max-h-72 overflow-auto shadow-2xl">
                {sugg.map((s) => (
                  <button key={s.hs6} type="button" data-testid={`duty-sugg-${s.hs6}`} onClick={() => pick(s)}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/5 flex items-center gap-3 border-b border-white/5 last:border-0">
                    <span className="font-mono-display text-xs text-cyan-300 shrink-0">{s.hs6}</span>
                    <span className="text-sm text-slate-200 truncate">{s.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <Field label="Origin (export from)">
            <select data-testid="duty-origin" className={inputCls} value={origin} onChange={(e) => setOrigin(e.target.value)}>
              <option value="">— Any —</option>
              {countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Destination (import to)">
            <select data-testid="duty-dest" className={inputCls} value={dest} onChange={(e) => setDest(e.target.value)}>
              {countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </Field>
        </div>
        <button data-testid="duty-submit" onClick={() => run()} disabled={loading} className="btn-primary mt-4 disabled:opacity-50">
          {loading ? <CircleNotch size={16} className="animate-spin" /> : <Scales size={16} weight="bold" />} Check duty & benefits
        </button>
        {err && <div data-testid="duty-error" className="mt-3 text-amber-300 text-sm">{err}</div>}
      </ToolCard>

      {data && (
        <div className="space-y-4" data-testid="duty-result">
          <div className="glass-strong rounded-3xl p-6">
            <div className="flex items-center gap-3 flex-wrap text-sm">
              <span className="font-mono-display text-cyan-300">HS {data.hsCode}</span>
              <span className="flex items-center gap-2 text-slate-300">
                {data.origin.name || "Any origin"} <ArrowRight size={14} className="text-cyan-300" /> {data.destination.name}
              </span>
              {data.refreshedAt && <span className="ml-auto text-[10px] text-slate-500 font-mono-display">updated {String(data.refreshedAt).slice(0, 10)}</span>}
            </div>

            <div className="grid sm:grid-cols-2 gap-3 mt-4">
              {data.importDuty ? (
                <div className="glass rounded-2xl p-5" data-testid="duty-import">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider">Import duty into {data.destination.name}</div>
                  <div className="font-display font-extrabold text-3xl gradient-text mt-1">{data.importDuty.rate}%</div>
                  <div className="text-xs text-slate-400 mt-1">{data.importDuty.type} · {data.importDuty.year} · {data.importDuty.source}</div>
                  {data.preferential && <div className="text-sm text-emerald-300 mt-2">Preferential available: {data.preferential.rate}% ({data.preferential.type})</div>}
                </div>
              ) : (
                <div className="glass rounded-2xl p-5 text-sm text-amber-300/90">No WITS tariff record for this pair/product. Try "Any" origin or another country.</div>
              )}
              {data.exportBenefit && (
                <div className="glass rounded-2xl p-5" data-testid="duty-benefit">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1"><Gift size={12} weight="duotone" className="text-cyan-300" /> Export benefit ({data.origin.name})</div>
                  <div className="font-display font-extrabold text-3xl text-emerald-300 mt-1">{data.exportBenefit.rate}%</div>
                  <div className="text-xs text-slate-400 mt-1">{data.exportBenefit.scheme} · {data.exportBenefit.unit} · {data.exportBenefit.source}</div>
                </div>
              )}
            </div>

            {data.indiaBreakdown && (
              <div className="mt-3" data-testid="duty-india-breakdown">
                <div className="text-xs font-mono-display tracking-widest uppercase text-cyan-300 mb-2">India import breakdown</div>
                <div className="grid sm:grid-cols-3 gap-3">
                  <Stat label="Basic Customs Duty" value={`${data.indiaBreakdown.basicCustomsDuty}%`} />
                  <Stat label="Social Welfare Surcharge" value={`${data.indiaBreakdown.socialWelfareSurcharge}%`} />
                  <Stat label="IGST" value={`${data.indiaBreakdown.igst}%`} />
                </div>
                <div className="text-[11px] text-slate-500 mt-2">{data.indiaBreakdown.note}</div>
              </div>
            )}

            {data.exportBenefit?.note && <div className="text-[11px] text-amber-300/80 mt-3">{data.exportBenefit.note}</div>}
          </div>

          <div className="glass-strong rounded-3xl p-5 flex items-center gap-4 flex-wrap">
            <Brain size={28} weight="duotone" className="text-cyan-300" />
            <div className="flex-1 min-w-[200px] text-sm text-slate-300">Ask the Brain for a full duty, documentation and savings plan for this trade lane.</div>
            <Link to={`/brain?q=${encodeURIComponent(`Duty, documents and benefits for HS ${data.hsCode} from ${data.origin.name || "any country"} to ${data.destination.name}`)}`} className="btn-primary" data-testid="duty-ask-brain">Ask the Brain</Link>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- Live Trade Statistics (global) ---------------- */
function TradeStatsTool() {
  const [q, setQ] = useState("");
  const [sugg, setSugg] = useState([]);
  const [openSugg, setOpenSugg] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const lastPick = useRef("");

  React.useEffect(() => {
    const text = q.trim();
    if (text === lastPick.current) return;
    if (text.length < 2 || /^\d+$/.test(text)) { setSugg([]); return; }
    const t = setTimeout(async () => {
      try { const { data } = await api.get("/trade-intel/hs-search", { params: { q: text, limit: 8 } }); setSugg(data.results || []); setOpenSugg(true); }
      catch (_) { setSugg([]); }
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const run = async (hs) => {
    setLoading(true); setErr(""); setData(null); setOpenSugg(false);
    try {
      const { data } = await api.get("/trade-intel/stats", { params: { hs } });
      if (data.ok) setData(data);
      else setErr(data.error || "No data found for this HS code.");
    } catch (_) { setErr("Unable to fetch trade data. Try again."); }
    finally { setLoading(false); }
  };

  const onSubmit = (e) => {
    e.preventDefault();
    const digits = q.replace(/\D/g, "");
    if (digits.length >= 6) run(digits.slice(0, 6));
    else if (sugg.length) run(sugg[0].hs6);
    else setErr("Search a product or enter a 6-digit HS code.");
  };

  const pick = (s) => { const label = `${s.hs6} · ${s.description}`; lastPick.current = label; setQ(label); setSugg([]); run(s.hs6); };
  const maxImp = data?.topImporters?.[0]?.value || 1;
  const maxExp = data?.topExporters?.[0]?.value || 1;
  const maxTrend = Math.max(...(data?.trend || []).map((t) => t.value), 1);

  return (
    <div className="space-y-5">
      <ToolCard title="Live Global Trade Statistics" desc="Real bilateral trade data for any product worldwide — top importing & exporting countries, total world trade value and multi-year trend. Powered by UN Comtrade / OEC World; the freshest source is used automatically.">
        <form onSubmit={onSubmit} className="relative">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <Field label="Product or HS code (global)">
                <input data-testid="trade-search" className={inputCls} value={q}
                  onChange={(e) => { setQ(e.target.value); }} onFocus={() => sugg.length && setOpenSugg(true)}
                  placeholder="e.g. Coffee, Smartphones, Crude Oil, or 090111" />
              </Field>
              {openSugg && sugg.length > 0 && (
                <div data-testid="trade-suggestions" className="absolute z-20 mt-1 w-full glass-strong rounded-2xl border border-white/10 max-h-72 overflow-auto shadow-2xl">
                  {sugg.map((s) => (
                    <button key={s.hs6} type="button" data-testid={`trade-sugg-${s.hs6}`} onClick={() => pick(s)}
                      className="w-full text-left px-4 py-2.5 hover:bg-white/5 flex items-center gap-3 border-b border-white/5 last:border-0">
                      <span className="font-mono-display text-xs text-cyan-300 shrink-0">{s.hs6}</span>
                      <span className="text-sm text-slate-200 truncate">{s.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button data-testid="trade-submit" type="submit" disabled={loading} className="btn-primary justify-center disabled:opacity-50">
              {loading ? <CircleNotch size={16} className="animate-spin" /> : <MagnifyingGlass size={16} weight="bold" />} Get data
            </button>
          </div>
        </form>
        {err && <div data-testid="trade-error" className="mt-4 text-amber-300 text-sm">{err}</div>}
      </ToolCard>

      {data && (
        <div className="space-y-5" data-testid="trade-result">
          <div className="glass-strong rounded-3xl p-6">
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div>
                <div className="text-[11px] font-mono-display tracking-widest uppercase text-cyan-300">HS {data.hsCode}</div>
                <h3 className="font-display font-bold text-2xl mt-1">{data.description || `HS ${data.hsCode}`}</h3>
              </div>
              <div className="text-right">
                <span data-testid="trade-source-badge" className="inline-flex items-center gap-1.5 text-[11px] font-mono-display uppercase px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-emerald-300">
                  <Globe size={12} weight="duotone" /> {data.source} · {data.year}
                </span>
                <div className="text-[10px] text-slate-500 mt-1">{data.comtradeEnabled ? "UN Comtrade + OEC" : "OEC World (add Comtrade key for fresher data)"}</div>
              </div>
            </div>
            <div className="mt-4 grid sm:grid-cols-3 gap-3">
              <div className="glass rounded-2xl px-5 py-4 sm:col-span-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">World trade value ({data.year})</div>
                <div className="font-display font-extrabold text-3xl gradient-text mt-1" data-testid="trade-world-value">{fmtUSD(data.totalWorldTradeUSD)}</div>
              </div>
              {data.trend?.length > 1 && (
                <div className="glass rounded-2xl px-5 py-4 sm:col-span-2">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-2">World trade trend</div>
                  <div className="flex items-end gap-3 h-16">
                    {data.trend.map((t) => (
                      <div key={t.year} className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full rounded-t bg-gradient-to-t from-cyan-500/40 to-violet-500/60" style={{ height: `${Math.max(8, (t.value / maxTrend) * 100)}%` }} title={fmtUSD(t.value)} />
                        <div className="text-[9px] text-slate-400 font-mono-display">{t.year}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-5">
            <Panel title="Top Importing Countries" icon={TrendUp}>
              <div className="space-y-2.5" data-testid="trade-importers">
                {data.topImporters.map((c, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm"><span>{c.country}</span><span className="text-cyan-300">{fmtUSD(c.value)}{c.share ? ` · ${c.share}%` : ""}</span></div>
                    <div className="h-1.5 rounded-full bg-white/5 mt-1 overflow-hidden"><div className="h-full bg-gradient-to-r from-cyan-400 to-cyan-500" style={{ width: `${(c.value / maxImp) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Top Exporting Countries" icon={TrendDown}>
              <div className="space-y-2.5" data-testid="trade-exporters">
                {data.topExporters.map((c, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm"><span>{c.country}</span><span className="text-violet-300">{fmtUSD(c.value)}</span></div>
                    <div className="h-1.5 rounded-full bg-white/5 mt-1 overflow-hidden"><div className="h-full bg-gradient-to-r from-violet-400 to-violet-500" style={{ width: `${(c.value / maxExp) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="glass-strong rounded-3xl p-5 flex items-center gap-4 flex-wrap">
            <Brain size={28} weight="duotone" className="text-cyan-300" />
            <div className="flex-1 min-w-[200px] text-sm text-slate-300">Ask the LeadNation Brain for a deeper read on demand, tariffs and opportunities for this product.</div>
            <Link to={`/brain?q=${encodeURIComponent(`Give me a full trade analysis for HS code ${data.hsCode} (${data.description}) — demand, top markets and opportunities`)}`} className="btn-primary" data-testid="trade-ask-brain">Ask the Brain</Link>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- Trade Terms (Incoterms / Payment / Insurance) ---------------- */
function TradeTermsTool() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  React.useEffect(() => {
    api.get("/customs/trade-terms").then(({ data }) => setData(data)).finally(() => setLoading(false));
  }, []);
  if (loading) return <div className="glass rounded-3xl p-10 text-center text-slate-400"><CircleNotch size={20} className="animate-spin inline" /> Loading trade terms…</div>;
  if (!data) return <div className="glass rounded-3xl p-10 text-center text-slate-400">Unable to load trade terms.</div>;
  return (
    <div className="space-y-5" data-testid="terms-result">
      <ToolCard title="Incoterms® 2020" desc="Who bears cost and risk, and where it transfers between seller and buyer.">
        <div className="grid sm:grid-cols-2 gap-3">
          {data.incoterms.map((t) => (
            <div key={t.code} data-testid={`terms-incoterm-${t.code}`} className="glass rounded-2xl p-4">
              <div className="flex items-center justify-between">
                <span className="font-mono-display font-bold text-cyan-300">{t.code}</span>
                <span className="text-[10px] uppercase tracking-wider text-slate-400">{t.name}</span>
              </div>
              <div className="text-xs text-emerald-300/90 mt-2">Risk: {t.risk}</div>
              <p className="text-sm text-slate-300 mt-1.5">{t.desc}</p>
            </div>
          ))}
        </div>
      </ToolCard>

      <ToolCard title="Payment Terms" desc="Methods to get paid — from safest to riskiest for the exporter.">
        <div className="space-y-2">
          {data.paymentTerms.map((p, i) => (
            <div key={i} className="glass rounded-xl px-4 py-3 flex flex-wrap items-center gap-2">
              <span className="font-semibold text-white">{p.term}</span>
              <span className="text-[10px] uppercase px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-400/30 text-violet-200">{p.risk}</span>
              <p className="text-sm text-slate-400 w-full">{p.desc}</p>
            </div>
          ))}
        </div>
      </ToolCard>

      <div className="grid lg:grid-cols-2 gap-5">
        <ToolCard title="Cargo Insurance" desc="Protecting goods in transit.">
          <div className="space-y-2">
            {data.insurance.map((it, i) => (
              <div key={i} className="glass rounded-xl px-4 py-3">
                <div className="font-medium text-cyan-300 text-sm">{it.type}</div>
                <p className="text-sm text-slate-400 mt-1">{it.desc}</p>
              </div>
            ))}
          </div>
        </ToolCard>
        <ToolCard title="Key Trade Terms" desc="The vocabulary customs and banks use.">
          <div className="space-y-2">
            {data.keyTerms.map((it, i) => (
              <div key={i} className="glass rounded-xl px-4 py-3">
                <div className="font-medium text-white text-sm">{it.term}</div>
                <p className="text-sm text-slate-400 mt-1">{it.desc}</p>
              </div>
            ))}
          </div>
        </ToolCard>
      </div>
      <div className="text-xs text-amber-300/80 px-1">{data.note}</div>
    </div>
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
