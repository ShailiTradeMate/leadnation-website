import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { useProject } from "@/lib/ProjectContext";
import { useAuth } from "@/lib/AuthContext";
import CommandCenterReport from "@/components/CommandCenterReport";
import {
  Lightning, Gauge, Stack, ChartBar, ShieldCheck, FileText, Truck, Warning,
  UsersThree, Brain, Gear, Plus, PushPin, Copy, Trash, ArrowRight,
  CircleNotch, Question, CheckCircle, Clock, Printer, CaretDown, Command, X,
  PaperPlaneTilt, MagnifyingGlass, FloppyDisk, Sparkle, Info, List, MagicWand, Anchor, User, CrownSimple,
} from "@phosphor-icons/react";

const WORKFLOW = ["Created", "Research", "Costing", "Compliance", "Documentation", "Quotation", "Negotiation", "Shipment", "Completed"];
const STAGE_DESC = {
  Created: "Project set up. Add product, route and quantity to begin.",
  Research: "Explore markets & buyers before you commit to a costing.",
  Costing: "Build the FOB → CIF cost waterfall and set your margin.",
  Compliance: "Confirm duties, FTA eligibility and required documents.",
  Documentation: "Prepare and check off the shipment documents.",
  Quotation: "Generate and export the buyer quote (PDF).",
  Negotiation: "Share the quote and align on Incoterm & payment terms.",
  Shipment: "Book freight & insurance and track the shipment.",
  Completed: "Deal done — archive or reuse this project as a template.",
};
const MODULES = [
  ["overview", "Overview", Gauge], ["costing", "Trade Costing", Stack],
  ["market", "Market Research", ChartBar], ["compliance", "Compliance", ShieldCheck],
  ["documents", "Documents", FileText], ["routes", "Routes", Truck],
  ["risk", "Risk", Warning], ["buyers", "Buyers & Suppliers", UsersThree],
  ["reports", "Reports", FileText], ["brain", "Brain", Brain], ["settings", "Settings", Gear],
];
const CUR = ["USD", "EUR", "GBP", "INR", "AED", "CNY", "JPY", "AUD", "SGD", "SAR", "CAD", "CHF"];
const INCOTERMS = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"];
const INCOTERM_INFO = {
  EXW: "Ex-Works — buyer bears all cost/risk from your factory gate.",
  FCA: "Free Carrier — you deliver, cleared for export, to the carrier at a named place.",
  FAS: "Free Alongside Ship — you place goods alongside the vessel at origin port.",
  FOB: "Free On Board — you cover costs until goods are loaded on the vessel.",
  CFR: "Cost & Freight — you pay freight to destination port (risk passes at origin).",
  CIF: "Cost, Insurance & Freight — you pay freight + insurance to destination port.",
  CPT: "Carriage Paid To — you pay carriage to a named destination place.",
  CIP: "Carriage & Insurance Paid — carriage + insurance to a named destination.",
  DAP: "Delivered At Place — you deliver to destination, buyer clears import.",
  DPU: "Delivered at Place Unloaded — you deliver and unload at destination.",
  DDP: "Delivered Duty Paid — you cover everything incl. import duty at destination.",
};
const UNITS = [
  ["unit", "Unit / Piece"], ["kg", "Kilogram (KG)"], ["mt", "Metric Ton (MT)"], ["ton", "Ton"],
  ["lb", "Pound (LB)"], ["qtl", "Quintal (100 KG)"], ["ltr", "Litre"], ["cbm", "Cubic Meter (CBM)"],
  ["dozen", "Dozen"], ["carton", "Carton / Box"], ["bag", "Bag / Sack"], ["pallet", "Pallet"],
  ["fcl20", "Container 20ft (FCL)"], ["fcl40", "Container 40ft (FCL)"],
];
const COST_FIELDS = [
  ["exw", "Ex-Works (EXW)", "Base price of the goods at your factory gate, before any logistics. Everything else builds on top of this."],
  ["packing", "Packing & labelling", "Export-grade packing, cartons, pallets, marking & labelling required for international shipping."],
  ["inland", "Inland transport", "Cost to move goods from your factory to the origin port/airport (trucking, local haulage)."],
  ["thc", "Port handling (THC)", "Terminal Handling Charges at the origin port — loading, stuffing, port & terminal fees."],
  ["customsDocs", "Customs & docs", "Origin customs clearance: CHA/agent fees, shipping bill, certificates, inspection, fumigation."],
  ["freight", "Freight", "Main international carriage — ocean or air freight from origin port to the destination port."],
  ["insurance", "Insurance", "Marine/cargo insurance covering loss or damage in transit (typically 0.1%–0.5% of CIF value)."],
];
const num = (v) => (v === "" || v == null ? 0 : parseFloat(v) || 0);
const fmtCur = (v, cur) => {
  if (v == null || isNaN(v)) return "—";
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(v); }
  catch (_) { return `${Number(v).toLocaleString()} ${cur}`; }
};
const inputCls = "w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 outline-none text-white text-sm focus:border-cyan-400/40";

/* ---------- markdown-lite ---------- */
function MD({ text }) {
  const lines = (text || "").split("\n"); const out = []; let bul = [];
  const inl = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith("**") && p.endsWith("**") ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span> : <span key={j}>{p}</span>);
  const flush = (k) => { if (bul.length) { out.push(<ul key={"u" + k} className="list-disc pl-5 space-y-1 text-sm text-slate-300">{bul.map((b, i) => <li key={i}>{inl(b)}</li>)}</ul>); bul = []; } };
  lines.forEach((raw, k) => { const l = raw.trim();
    if (!l || l === "---") { flush(k); return; }
    if (l.startsWith("### ")) { flush(k); out.push(<div key={k} className="font-display font-bold text-sm mt-2 text-white">{inl(l.slice(4))}</div>); }
    else if (l.startsWith("## ")) { flush(k); out.push(<div key={k} className="font-display font-bold text-base mt-3 text-cyan-200">{inl(l.slice(3))}</div>); }
    else if (l.startsWith("- ") || l.startsWith("* ")) bul.push(l.replace(/^[-*]\s/, ""));
    else { flush(k); out.push(<p key={k} className="text-sm leading-relaxed text-slate-200">{inl(l)}</p>); }
  });
  flush("end"); return <div className="space-y-1.5">{out}</div>;
}

/* ---------- reusable chips ---------- */
const SRC = {
  government: ["Government", "emerald"], live: ["Live API", "cyan"], brain: ["Brain", "violet"],
  manual: ["Manual", "slate"], historical: ["Historical", "amber"], estimated: ["AI Estimate", "amber"],
};
const SourceBadge = ({ kind }) => {
  const [label, c] = SRC[kind] || SRC.live;
  const map = { emerald: "bg-emerald-500/10 border-emerald-400/30 text-emerald-300", cyan: "bg-cyan-500/10 border-cyan-400/30 text-cyan-300", violet: "bg-violet-500/10 border-violet-400/30 text-violet-300", slate: "bg-white/5 border-white/15 text-slate-300", amber: "bg-amber-500/10 border-amber-400/30 text-amber-300" };
  return <span className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-full border ${map[c]}`} data-testid={`source-${kind}`}>{label}</span>;
};

function ExplainBtn({ field, quote }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setOpen(true); if (data) return; setLoading(true);
    try { const { data } = await api.post("/command-center/explain", { field, quote }); setData(data); }
    catch (_) {} finally { setLoading(false); }
  };
  return (
    <>
      <button data-testid={`explain-${field}`} onClick={run} className="text-cyan-300/70 hover:text-cyan-300" title="Explain this value"><Question size={14} weight="bold" /></button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <div className="glass-strong rounded-3xl p-6 max-w-lg w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()} data-testid="explain-modal">
            <div className="flex items-center justify-between mb-3"><div className="font-display font-bold text-lg flex items-center gap-2"><Brain size={18} className="text-cyan-300" /> Explain · {field.toUpperCase()}</div><button onClick={() => setOpen(false)}><X size={18} /></button></div>
            {loading && <div className="text-sm text-slate-400 flex items-center gap-2"><CircleNotch size={16} className="animate-spin" /> Asking the Brain…</div>}
            {data && (<div className="space-y-3">
              <div className="text-xs font-mono-display text-cyan-300 bg-cyan-500/5 border border-cyan-400/20 rounded-xl px-3 py-2">{data.formula}</div>
              <MD text={data.explanation} />
              <div className="text-[11px] text-slate-500 border-t border-white/10 pt-2">Source: {data.source}</div>
            </div>)}
          </div>
        </div>
      )}
    </>
  );
}

const ringColor = { emerald: "#10b981", amber: "#f59e0b", rose: "#f43f5e" };
function ScoreRing({ label, score, size = 64 }) {
  const v = score?.value ?? 0; const c = ringColor[score?.color] || "#00C2FF";
  const r = size / 2 - 6; const circ = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center gap-1" data-testid={`score-${label.toLowerCase().replace(/\s/g, "-")}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={c} strokeWidth="6" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={circ * (1 - v / 100)} />
      </svg>
      <div className="-mt-[calc(50%+2px)] text-base font-display font-bold" style={{ color: c }}>{v}</div>
      <div className="mt-[calc(50%-14px)] text-[10px] text-slate-400 text-center leading-tight">{label}</div>
    </div>
  );
}

const Card = ({ title, icon: I, children, action, testid }) => (
  <div className="glass rounded-3xl p-5" data-testid={testid}>
    {title && <div className="flex items-center justify-between mb-3"><div className="text-xs font-mono-display tracking-[0.2em] uppercase text-cyan-300 flex items-center gap-2">{I && <I size={14} weight="duotone" />}{title}</div>{action}</div>}
    {children}
  </div>
);

// (i) info tooltip — hover to see why a field / value matters
function InfoTip({ text, testid }) {
  return (
    <span className="relative inline-flex group align-middle" data-testid={testid}>
      <Info size={13} weight="bold" className="text-slate-500 hover:text-cyan-300 cursor-help" />
      <span className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-full mb-1.5 w-52 z-40 opacity-0 group-hover:opacity-100 transition-opacity glass-strong rounded-xl px-3 py-2 text-[11px] leading-snug text-slate-200 border border-white/10 shadow-2xl">{text}</span>
    </span>
  );
}

/* ============================= WORKSPACE ============================= */
export default function CommandCenter() {
  const P = useProject();
  const [module, setModule] = useState("overview");
  const [palette, setPalette] = useState(false);
  const [compliance, setCompliance] = useState(null);
  const [compLoading, setCompLoading] = useState(false);
  const cur = P.current;

  useEffect(() => {
    const h = (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPalette((v) => !v); } };
    window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h);
  }, []);

  // reactive compliance fetch when lane changes
  const lane = cur ? `${cur.hs}:${cur.exporter}:${cur.importer}:${cur.incoterm}` : "";
  useEffect(() => {
    if (!cur || (!cur.hs && !cur.product)) { setCompliance(null); return; }
    setCompLoading(true);
    const t = setTimeout(() => {
      api.post("/command-center/compliance", { hs: cur.hs, product: cur.hs ? "" : cur.product, exporter: cur.exporter, importer: cur.importer, incoterm: cur.incoterm }, { timeout: 90000 })
        .then(({ data }) => setCompliance(data.ok ? data : null)).catch(() => {}).finally(() => setCompLoading(false));
    }, 500);
    return () => clearTimeout(t);
  }, [lane]); // eslint-disable-line

  return (
    <>
      <SEO title="Trade Command Center · Workspace · LeadNation" description="Your stateful global-trade workspace — one Trade Project, one Brain, every module connected." path="/command-center" />
      <CommandCenterReport project={cur} compliance={compliance} />
      {palette && <CommandPalette P={P} setModule={setModule} close={() => setPalette(false)} />}

      {!cur ? (
        <StartScreen P={P} />
      ) : (
        <div className="max-w-[1700px] mx-auto px-3 sm:px-5 py-4" data-testid="cc-workspace">
          <TopBar P={P} cur={cur} openPalette={() => setPalette(true)} />
          <div className="grid grid-cols-12 gap-4 mt-4">
            {/* LEFT SIDEBAR */}
            <aside className="col-span-12 lg:col-span-2">
              <div className="glass rounded-3xl p-2 lg:sticky lg:top-4 flex lg:flex-col gap-1 overflow-x-auto">
                {MODULES.map(([k, label, I]) => (
                  <button key={k} data-testid={`cc-mod-${k}`} title={label} onClick={() => setModule(k)}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm whitespace-nowrap transition-all ${module === k ? "bg-cyan-500/15 text-cyan-200 border border-cyan-400/30" : "text-slate-300 hover:bg-white/5"}`}>
                    <I size={16} weight="duotone" /> <span className="hidden lg:inline">{label}</span>
                  </button>
                ))}
              </div>
            </aside>
            {/* CENTER */}
            <main className="col-span-12 lg:col-span-7 space-y-4" data-testid="cc-center">
              {module === "overview" && <Overview P={P} cur={cur} compliance={compliance} setModule={setModule} />}
              {module === "costing" && <Costing P={P} cur={cur} />}
              {module === "market" && <Market cur={cur} />}
              {module === "compliance" && <Compliance cur={cur} compliance={compliance} loading={compLoading} />}
              {module === "documents" && <Documents P={P} cur={cur} compliance={compliance} />}
              {module === "routes" && <Routes cur={cur} />}
              {module === "risk" && <Risk cur={cur} />}
              {module === "buyers" && <Buyers cur={cur} />}
              {module === "reports" && <Reports P={P} cur={cur} compliance={compliance} />}
              {module === "brain" && <BrainModule cur={cur} P={P} />}
              {module === "settings" && <Settings P={P} cur={cur} />}
            </main>
            {/* RIGHT BRAIN PANEL */}
            <aside className="col-span-12 lg:col-span-3">
              <BrainPanel P={P} cur={cur} setModule={setModule} />
            </aside>
          </div>
        </div>
      )}
    </>
  );
}

/* ---------------- Top bar (project + workflow) ---------------- */
function TopBar({ P, cur, openPalette }) {
  const [open, setOpen] = useState(false);
  const idx = WORKFLOW.indexOf(cur.stage);
  return (
    <div className="glass-strong rounded-3xl p-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative">
          <button data-testid="cc-project-switcher" onClick={() => setOpen(!open)} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-sm font-medium">
            <Lightning size={15} weight="duotone" className="text-cyan-300" /> {cur.title} <CaretDown size={13} />
          </button>
          {open && (
            <div className="absolute z-30 mt-1 w-72 glass-strong rounded-2xl border border-white/10 max-h-80 overflow-auto p-2" data-testid="cc-project-list">
              <button onClick={() => { P.setCurrent(null); setOpen(false); }} className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 text-sm text-cyan-300 flex items-center gap-2"><Plus size={14} /> New / open another project</button>
              {P.projects.map((p) => (
                <button key={p.id} data-testid={`cc-switch-${p.id}`} onClick={() => { P.loadProject(p.id); setOpen(false); }} className={`w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 ${p.id === cur.id ? "bg-white/5" : ""}`}>
                  <div className="text-sm flex items-center gap-1.5">{p.pinned && <PushPin size={11} weight="fill" className="text-cyan-300" />}{p.title}</div>
                  <div className="text-[11px] text-slate-500">{p.origin} → {p.destination} · {p.stage}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        <span className="text-xs text-slate-400 hidden sm:inline">{cur.summary?.origin} → {cur.summary?.destination}</span>
        <button onClick={openPalette} className="ml-auto flex items-center gap-1.5 text-xs text-cyan-200 px-3 py-1.5 rounded-lg border border-cyan-400/25 bg-cyan-500/10 hover:bg-cyan-500/20" data-testid="cc-palette-btn" title="Open the quick menu (Ctrl/⌘ + K)"><List size={14} weight="bold" /> Menu <span className="text-[10px] text-slate-400 hidden sm:inline">Ctrl K</span></button>
      </div>
      {/* current stage indicator */}
      <div className="mt-3 flex items-center gap-2 text-sm" data-testid="cc-current-stage">
        <span className="text-[11px] font-mono-display uppercase tracking-widest text-cyan-300 bg-cyan-500/10 border border-cyan-400/25 rounded-full px-2.5 py-1">Stage {idx + 1} of {WORKFLOW.length}</span>
        <span className="font-display font-bold text-white">{cur.stage}</span>
        <span className="text-slate-400 text-xs hidden md:inline">— {STAGE_DESC[cur.stage]}</span>
      </div>
      {/* workflow stepper */}
      <div className="flex items-center gap-1 mt-2 overflow-x-auto pb-1" data-testid="cc-workflow">
        {WORKFLOW.map((s, i) => (
          <button key={s} data-testid={`cc-stage-${s.toLowerCase()}`} onClick={() => P.update({ stage: s }, `Stage → ${s}`)}
            className={`text-[11px] px-2.5 py-1 rounded-full whitespace-nowrap transition-all ${i === idx ? "bg-cyan-500/25 text-cyan-100 border border-cyan-400/50 font-semibold" : i < idx ? "text-emerald-300/80" : "text-slate-500 hover:text-slate-300"}`}>
            {i < idx && <CheckCircle size={10} weight="fill" className="inline mr-1" />}{i === idx && "▶ "}{s}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ---------------- Start screen (no project) ---------------- */
function StartScreen({ P }) {
  const [f, setF] = useState({ title: "", product: "", hs: "", exporter: "356", importer: "842" });
  const [countries, setCountries] = useState([]);
  const [busy, setBusy] = useState(false);
  const [sugg, setSugg] = useState([]);
  const [openSugg, setOpenSugg] = useState(false);
  const lastPick = useRef("");
  useEffect(() => { api.get("/command-center/markets").then(({ data }) => setCountries(data.countries || [])); }, []);
  useEffect(() => {
    const text = (f.product || "").trim();
    if (text === lastPick.current) return;
    if (text.length < 2) { setSugg([]); return; }
    const t = setTimeout(async () => {
      try { const { data } = await api.get("/trade-intel/hs-search", { params: { q: text, limit: 8 } }); setSugg(data.results || []); setOpenSugg(true); } catch (_) {}
    }, 300);
    return () => clearTimeout(t);
  }, [f.product]);
  const pickProduct = (s) => { lastPick.current = s.description; setF((x) => ({ ...x, product: s.description, hs: s.hs6 })); setSugg([]); setOpenSugg(false); };
  const create = async () => {
    setBusy(true);
    try { await P.createProject({ ...f, title: f.title || `${f.product || "New"} · trade project`, stage: "Created" }); }
    finally { setBusy(false); }
  };
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <SEO title="Trade Command Center · LeadNation" description="Start a Trade Project — the stateful workspace for global trade." path="/command-center" />
      <div className="inline-flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300"><Lightning size={14} weight="duotone" /> LeadNation Trade Command Center™</div>
      <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-3 leading-[1.05]">Start a <span className="gradient-text">Trade Project.</span></h1>
      <p className="text-slate-400 mt-3 max-w-2xl">Every calculation, quote, document and Brain conversation lives inside one persistent project — no re-entry, ever. Create one and the whole workspace knows your context.</p>

      <div className="glass-strong rounded-3xl p-6 mt-8" data-testid="cc-create-form">
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="block sm:col-span-2"><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">Project name</span>
            <input data-testid="cc-new-title" className={`${inputCls} mt-1`} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder="e.g. Export Basmati Rice · India → UAE" /></label>
          <label className="block relative"><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">Product</span>
            <input data-testid="cc-new-product" className={`${inputCls} mt-1`} value={f.product} autoComplete="off"
              onChange={(e) => { setF({ ...f, product: e.target.value, hs: "" }); }} onFocus={() => sugg.length && setOpenSugg(true)}
              placeholder="Search a product, e.g. Basmati Rice, Towels…" />
            {openSugg && sugg.length > 0 && (
              <div data-testid="cc-new-product-suggestions" className="absolute z-30 mt-1 w-full glass-strong rounded-2xl border border-white/10 max-h-72 overflow-auto shadow-2xl">
                {sugg.map((s) => (
                  <button key={s.hs6} type="button" data-testid={`cc-new-sugg-${s.hs6}`} onClick={() => pickProduct(s)}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/5 flex items-center gap-3 border-b border-white/5 last:border-0">
                    <span className="font-mono-display text-xs text-cyan-300 shrink-0">{s.hs6}</span>
                    <span className="text-sm text-slate-200 truncate">{s.description}</span>
                  </button>
                ))}
              </div>
            )}</label>
          <label className="block"><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">HS code (auto-filled)</span>
            <input data-testid="cc-new-hs" className={`${inputCls} mt-1`} value={f.hs} onChange={(e) => setF({ ...f, hs: e.target.value })} placeholder="Select a product above →" /></label>
          <label className="block"><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">Export from</span>
            <select data-testid="cc-new-exporter" className={`${inputCls} mt-1`} value={f.exporter} onChange={(e) => setF({ ...f, exporter: e.target.value })}>{countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}</select></label>
          <label className="block"><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">Import to</span>
            <select data-testid="cc-new-importer" className={`${inputCls} mt-1`} value={f.importer} onChange={(e) => setF({ ...f, importer: e.target.value })}>{countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}</select></label>
        </div>
        <button data-testid="cc-create-btn" onClick={create} disabled={busy} className="btn-primary mt-4 disabled:opacity-50">{busy ? <CircleNotch size={16} className="animate-spin" /> : <Plus size={16} weight="bold" />} Create Trade Project</button>
      </div>

      {P.projects.length > 0 && (
        <div className="mt-8">
          <div className="text-xs font-mono-display tracking-[0.2em] uppercase text-slate-400 mb-3">Your projects</div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="cc-projects-grid">
            {P.projects.map((p) => (
              <div key={p.id} data-testid={`cc-card-${p.id}`} className="glass rounded-2xl p-4 hover:border-cyan-400/30 transition-all">
                <button onClick={() => P.loadProject(p.id)} className="text-left w-full">
                  <div className="font-display font-bold text-sm flex items-center gap-1.5">{p.pinned && <PushPin size={12} weight="fill" className="text-cyan-300" />}{p.title}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{p.origin} → {p.destination} · {p.stage}</div>
                  <div className="flex items-center gap-2 mt-2"><span className="text-[10px] text-slate-400">Health</span><span className="text-sm font-bold text-cyan-300">{p.health?.value ?? "—"}</span></div>
                </button>
                <div className="flex gap-2 mt-3 text-slate-400">
                  <button onClick={() => P.pinProject(p.id)} title="Pin" className="hover:text-cyan-300"><PushPin size={14} /></button>
                  <button onClick={() => P.duplicateProject(p.id)} title="Duplicate" className="hover:text-cyan-300"><Copy size={14} /></button>
                  <button onClick={() => P.deleteProject(p.id)} title="Delete" className="hover:text-rose-400"><Trash size={14} /></button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- Command Palette ---------------- */
function CommandPalette({ P, setModule, close }) {
  const [q, setQ] = useState("");
  const actions = [
    ...MODULES.map(([k, label, I]) => ({ label: `Go to ${label}`, run: () => { setModule(k); close(); }, I })),
    { label: "New / switch project", run: () => { P.setCurrent(null); close(); }, I: Plus },
    { label: "Ask the Brain", run: () => { setModule("brain"); close(); }, I: Brain },
    { label: "Export quote PDF", run: () => { close(); setTimeout(() => window.print(), 100); }, I: Printer },
    ...P.projects.map((p) => ({ label: `Open: ${p.title}`, run: () => { P.loadProject(p.id); close(); }, I: Lightning })),
  ];
  const filtered = actions.filter((a) => a.label.toLowerCase().includes(q.toLowerCase())).slice(0, 8);
  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-24 px-4 bg-black/60 backdrop-blur-sm" onClick={close}>
      <div className="glass-strong rounded-2xl w-full max-w-lg overflow-hidden" onClick={(e) => e.stopPropagation()} data-testid="cc-palette">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10"><MagnifyingGlass size={16} className="text-slate-400" />
          <input autoFocus data-testid="cc-palette-input" className="flex-1 bg-transparent outline-none text-sm" placeholder="Type a command or project…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <div className="max-h-80 overflow-auto p-2">
          {filtered.map((a, i) => (
            <button key={i} onClick={a.run} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 text-sm text-left"><a.I size={15} className="text-cyan-300" />{a.label}</button>
          ))}
          {!filtered.length && <div className="px-3 py-6 text-center text-sm text-slate-500">No matches.</div>}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Modules ---------------- */
function Overview({ P, cur, compliance, setModule }) {
  const h = cur.health || {}; const s = cur.summary || {}; const q = cur.lastQuote;
  const tc = s.currency || cur.transactionCurrency;
  const alerts = [];
  if (!q) alerts.push(["Complete your costing to unlock analysis", "costing"]);
  if (h.risk?.color === "rose") alerts.push(["Risk score is low — review payment terms", "risk"]);
  if (h.compliance?.value < 60) alerts.push(["Compliance incomplete — confirm duties & documents", "compliance"]);
  if ((cur.documents || []).length === 0) alerts.push(["No documents prepared yet", "documents"]);
  return (
    <>
      <Card title="Project Summary" icon={Gauge} testid="cc-overview-summary">
        <div className="grid sm:grid-cols-4 gap-3">
          <Kpi label="Revenue (quote)" value={fmtCur(s.revenue, tc)} />
          <Kpi label="Profit" value={fmtCur(s.profit, tc)} accent="text-emerald-300" />
          <Kpi label="Destination" value={s.destination || "—"} />
          <Kpi label="Status / Stage" value={`${s.status} · ${s.stage}`} />
        </div>
        <div className="mt-3 glass rounded-2xl p-4 flex items-start gap-3">
          <Sparkle size={18} weight="duotone" className="text-cyan-300 mt-0.5" />
          <div className="text-sm"><span className="text-cyan-300 font-medium">Next action:</span> {s.nextAction}</div>
        </div>
      </Card>

      <Card title="Project Health" icon={ChartBar} testid="cc-overview-health">
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
          <ScoreRing label="Overall" score={h.overall} />
          <ScoreRing label="Profit" score={h.profitability} />
          <ScoreRing label="Risk" score={h.risk} />
          <ScoreRing label="Compliance" score={h.compliance} />
          <ScoreRing label="Docs" score={h.documentation} />
          <ScoreRing label="Timeline" score={h.timeline} />
          <ScoreRing label="Cash Flow" score={h.cashFlow} />
        </div>
      </Card>

      <Card title="Executive Dashboard · Alerts & Tasks" icon={Warning} testid="cc-overview-alerts">
        {alerts.length ? (
          <div className="space-y-2">
            {alerts.map(([t, mod], i) => (
              <button key={i} onClick={() => setModule(mod)} className="w-full text-left glass rounded-xl px-4 py-2.5 hover:border-cyan-400/30 flex items-center gap-2 text-sm">
                <Warning size={14} className="text-amber-300" /> {t} <ArrowRight size={13} className="ml-auto text-cyan-300" />
              </button>
            ))}
          </div>
        ) : <div className="text-sm text-emerald-300">All clear — your project is on track.</div>}
        {q?.comparison?.[0] && <div className="mt-3 text-xs text-slate-400">📈 Best market: <span className="text-cyan-300">{q.comparison[0].country}</span> (lowest buyer landed cost). FX source: live (open.er-api.com).</div>}
      </Card>

      <Card title="Activity Timeline" icon={Clock} testid="cc-overview-timeline">
        <div className="space-y-2 max-h-64 overflow-auto">
          {(cur.timeline || []).slice().reverse().map((t, i) => (
            <div key={i} className="flex gap-3 text-sm"><span className="text-[11px] text-slate-500 font-mono-display whitespace-nowrap">{String(t.at).slice(5, 16).replace("T", " ")}</span><span className="text-slate-300">{t.text}</span></div>
          ))}
        </div>
      </Card>
    </>
  );
}

function Costing({ P, cur }) {
  const q = cur.lastQuote; const tc = cur.transactionCurrency;
  const setCost = (k, v) => P.patchCosts(k, v);
  const fobUnit = ["exw", "packing", "inland", "thc", "customsDocs"].reduce((s, k) => s + num((cur.costs || {})[k]), 0);
  const cifUnit = fobUnit + num((cur.costs || {}).freight) + num((cur.costs || {}).insurance);
  const [ports, setPorts] = useState([]);
  const [autoBusy, setAutoBusy] = useState(false);
  const [autoNote, setAutoNote] = useState("");
  const unitLabel = (UNITS.find((u) => u[0] === cur.unit) || [null, cur.unit])[1];

  useEffect(() => {
    api.get("/command-center/ports", { params: { country: cur.importer } }).then(({ data }) => setPorts(data.ports || [])).catch(() => {});
  }, [cur.importer]);

  const autofill = async () => {
    setAutoBusy(true); setAutoNote("");
    try {
      const { data } = await api.post("/command-center/autofill", {
        hs: cur.hs, product: cur.hs ? "" : cur.product, exporter: cur.exporter, importer: cur.importer,
        quantity: num(cur.quantity) || 1, unit: cur.unit, incoterm: cur.incoterm, transactionCurrency: cur.transactionCurrency,
      }, { timeout: 90000 });
      if (data.ok) { P.update({ costs: { ...(cur.costs || {}), ...data.costs } }, "Brain autofilled costing"); setAutoNote(data.note); }
      else setAutoNote(data.error || "Could not estimate — enter manually.");
    } catch (_) { setAutoNote("Autofill unavailable — please try again."); }
    finally { setAutoBusy(false); }
  };

  return (
    <>
      <Card title="Trade lane" icon={Stack} testid="cc-costing-lane">
        <div className="grid sm:grid-cols-3 gap-3">
          <Lbl t="Quantity"><input data-testid="cc-qty" type="number" className={inputCls} value={cur.quantity} onChange={(e) => P.update({ quantity: e.target.value })} /></Lbl>
          <Lbl t={<span className="inline-flex items-center gap-1">Unit of measure <InfoTip text="Choose the trade unit your prices are quoted in (e.g. per Metric Ton, per KG, per Container). All costing is calculated per this unit." /></span>}>
            <select data-testid="cc-unit" className={inputCls} value={cur.unit} onChange={(e) => P.update({ unit: e.target.value }, `Unit → ${e.target.value}`)}>{UNITS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
          </Lbl>
          <Lbl t={<span className="inline-flex items-center gap-1">Incoterm <InfoTip text={INCOTERM_INFO[cur.incoterm]} /></span>}>
            <select data-testid="cc-incoterm" className={inputCls} value={cur.incoterm} onChange={(e) => P.update({ incoterm: e.target.value }, `Incoterm → ${e.target.value}`)}>{INCOTERMS.map((i) => <option key={i} value={i}>{i} — {INCOTERM_INFO[i].split("—")[0].trim()}</option>)}</select>
          </Lbl>
          <Lbl t={<span className="inline-flex items-center gap-1">Destination port <InfoTip text="The buyer's port/airport of discharge. It refines freight and the Incoterm delivery point for accurate pricing." /></span>}>
            <select data-testid="cc-dest-port" className={inputCls} value={cur.destinationPort || ""} onChange={(e) => P.update({ destinationPort: e.target.value }, `Destination port → ${e.target.value}`)}>
              <option value="">— Select port —</option>{ports.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </Lbl>
          <Lbl t="Margin %"><input data-testid="cc-margin" type="number" className={inputCls} value={cur.marginPct} onChange={(e) => P.update({ marginPct: e.target.value })} /></Lbl>
          <Lbl t="Your currency"><select data-testid="cc-txn-cur" className={inputCls} value={cur.transactionCurrency} onChange={(e) => P.update({ transactionCurrency: e.target.value })}>{CUR.map((c) => <option key={c}>{c}</option>)}</select></Lbl>
          <Lbl t="Global currency"><select data-testid="cc-global-cur" className={inputCls} value={cur.globalCurrency} onChange={(e) => P.update({ globalCurrency: e.target.value })}>{CUR.map((c) => <option key={c}>{c}</option>)}</select></Lbl>
        </div>
        <div className="mt-2 text-[11px] text-slate-400 inline-flex items-center gap-1"><Info size={12} className="text-cyan-300" /> {INCOTERM_INFO[cur.incoterm]}</div>
      </Card>
      <Card title="Cost build-up — Ex-Works → FOB → CIF" icon={Stack} testid="cc-costing-inputs"
        action={<button data-testid="cc-autofill" onClick={autofill} disabled={autoBusy} className="btn-ghost !py-1.5 !px-3 !text-xs disabled:opacity-50">{autoBusy ? <CircleNotch size={13} className="animate-spin" /> : <MagicWand size={13} weight="bold" />} Autofill with Brain</button>}>
        <div className="text-[11px] text-slate-400 mb-3 inline-flex items-center gap-1"><MagicWand size={12} className="text-cyan-300" /> Let the Brain estimate market rates, then tweak any field — all values are per {unitLabel}.</div>
        <div className="grid sm:grid-cols-2 gap-3">
          {COST_FIELDS.map(([k, label, info]) => (
            <Lbl key={k} t={<span className="inline-flex items-center gap-1">{label} (per {unitLabel}) <InfoTip text={info} testid={`cc-info-${k}`} /></span>}>
              <input data-testid={`cc-cost-${k}`} type="number" className={inputCls} value={(cur.costs || {})[k] ?? ""} onChange={(e) => setCost(k, e.target.value)} placeholder="0" />
            </Lbl>
          ))}
        </div>
        {autoNote && <div className="mt-3 text-[11px] text-cyan-300/90 flex items-start gap-1.5"><Sparkle size={12} className="mt-0.5" /> {autoNote}</div>}
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <div className="glass rounded-2xl px-4 py-3 flex justify-between items-center"><span className="text-[10px] uppercase text-slate-400">FOB / {unitLabel}</span><span className="font-display font-bold text-xl text-cyan-300">{fmtCur(fobUnit, tc)}</span></div>
          <div className="glass rounded-2xl px-4 py-3 flex justify-between items-center"><span className="text-[10px] uppercase text-slate-400">CIF / {unitLabel}</span><span className="font-display font-bold text-xl text-gradient">{fmtCur(cifUnit, tc)}</span></div>
        </div>
        {P.quoteLoading && <div className="mt-3 text-xs text-slate-500 flex items-center gap-2"><CircleNotch size={14} className="animate-spin" /> Recomputing everything…</div>}
      </Card>
      {q && (
        <Card title="Quote summary" icon={Lightning} testid="cc-costing-result">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Kpi label="FOB" value={fmtCur(q.fob.total, tc)} explain="fob" quote={q} sub={fmtCur(q.currency.converted.fob.global, q.currency.global)} />
            <Kpi label="CIF" value={fmtCur(q.cif.total, tc)} explain="cif" quote={q} sub={fmtCur(q.currency.converted.cif.global, q.currency.global)} />
            <Kpi label={`Landed (${q.importer.name})`} value={fmtCur(q.destination.landed, tc)} explain="landed" quote={q} accent="text-emerald-300" sub={fmtCur(q.currency.converted.landed.global, q.currency.global)} />
            <Kpi label="Selling" value={fmtCur(q.pricing.selling, tc)} explain="selling" quote={q} accent="text-violet-300" sub={`profit ${fmtCur(q.pricing.profit, tc)}`} />
          </div>
          <div className="mt-4 space-y-1" data-testid="cc-waterfall">
            {q.waterfall.map((w, i) => (
              <div key={i} className={`flex justify-between py-1.5 text-sm ${w.milestone ? "border-y border-cyan-400/20 my-1 font-semibold text-cyan-300" : "border-b border-white/5 text-slate-300"}`}>
                <span>{w.stage}</span><span>{fmtCur(w.total, tc)} <span className="text-[10px] text-slate-500">({fmtCur(w.perUnit, tc)}/{unitLabel})</span></span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </>
  );
}

function Market({ cur }) {
  const q = cur.lastQuote; const tc = cur.transactionCurrency;
  if (!q) return <Empty msg="Build your costing first — market comparison uses your CIF." />;
  return (
    <Card title="Best markets — buyer landed cost" icon={ChartBar} testid="cc-market" action={<SourceBadge kind="live" />}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[560px]">
          <thead><tr className="text-[10px] uppercase text-slate-400 border-b border-white/10"><th className="text-left py-2">Market</th><th className="text-right">Your CIF</th><th className="text-right">Buyer duty</th><th className="text-right">Buyer VAT</th><th className="text-right">Buyer total</th></tr></thead>
          <tbody>{q.comparison.map((c, i) => (
            <tr key={c.code} data-testid={`cc-market-${c.code}`} className={`border-b border-white/5 ${i === 0 ? "bg-emerald-500/5" : ""}`}>
              <td className="py-2.5">{i === 0 && <span className="text-emerald-300 mr-1">★</span>}{c.country}</td>
              <td className="text-right text-slate-300">{fmtCur(c.cif, tc)}</td>
              <td className="text-right text-slate-300">{c.dutyRate != null ? `${c.dutyRate}%` : "—"}</td>
              <td className="text-right text-slate-300">{c.vatRate}%</td>
              <td className="text-right font-semibold text-cyan-300">{fmtCur(c.buyerTotal, tc)}</td>
            </tr>))}</tbody>
        </table>
      </div>
    </Card>
  );
}

function Compliance({ cur, compliance, loading }) {
  if (loading) return <Empty msg="Loading compliance for this lane…" spin />;
  if (!compliance) return <Empty msg="Add a product/HS code to load compliance." />;
  return (
    <>
      <Card title={`Compliance · ${compliance.importer.name}`} icon={ShieldCheck} testid="cc-compliance" action={<SourceBadge kind="government" />}>
        {compliance.duty?.importDuty ? (
          <div className="text-sm">Import duty: <span className="text-cyan-300 font-semibold">{compliance.duty.importDuty.rate}% {compliance.duty.importDuty.type}</span> ({compliance.duty.importDuty.year}) {compliance.duty.preferential && <span className="text-emerald-300">· Preferential {compliance.duty.preferential.rate}%</span>}</div>
        ) : <div className="text-sm text-amber-300/90">No tariff record for this lane.</div>}
        <div className="mt-3 text-xs font-mono-display uppercase tracking-wider text-slate-400 mb-1.5">Required documents</div>
        <div className="flex flex-wrap gap-2">{compliance.documents.map((d, i) => <span key={i} className="glass rounded-full px-3 py-1.5 text-xs">{d}</span>)}</div>
      </Card>
      {compliance.narrative && <Card title="Compliance brief" icon={Brain} testid="cc-compliance-brief" action={<SourceBadge kind="brain" />}><MD text={compliance.narrative} /></Card>}
    </>
  );
}

function Documents({ P, cur, compliance }) {
  const docs = cur.documents || [];
  const required = compliance?.documents || [];
  const has = (n) => docs.find((d) => d.name === n);
  const toggle = (n) => {
    const exists = has(n);
    const next = exists ? docs.map((d) => d.name === n ? { ...d, ready: !d.ready } : d) : [...docs, { name: n, ready: true }];
    P.update({ documents: next }, `Document '${n}' ${exists && exists.ready ? "unmarked" : "marked ready"}`);
  };
  return (
    <Card title="Documents" icon={FileText} testid="cc-documents" action={<SourceBadge kind="government" />}>
      {required.length === 0 && <Empty msg="Load Compliance to see required documents." />}
      <div className="space-y-2">
        {required.map((n, i) => (
          <button key={i} data-testid={`cc-doc-${i}`} onClick={() => toggle(n)} className="w-full flex items-center gap-3 glass rounded-xl px-4 py-2.5 text-sm hover:border-cyan-400/30">
            <CheckCircle size={16} weight={has(n)?.ready ? "fill" : "regular"} className={has(n)?.ready ? "text-emerald-400" : "text-slate-500"} />
            <span className={has(n)?.ready ? "text-slate-200" : "text-slate-400"}>{n}</span>
          </button>
        ))}
      </div>
      {required.length > 0 && <div className="text-xs text-slate-500 mt-3">{docs.filter((d) => d.ready).length}/{required.length} documents ready.</div>}
    </Card>
  );
}

function Routes({ cur }) {
  const q = cur.lastQuote;
  if (!q) return <Empty msg="Build your costing to see routes." />;
  return (
    <Card title="Shipment routes" icon={Truck} testid="cc-routes" action={<SourceBadge kind="estimated" />}>
      <div className="space-y-2">{q.routes.map((r, i) => (
        <div key={i} className="glass rounded-xl px-4 py-3 flex items-center gap-3"><Truck size={16} className="text-cyan-300" /><div className="flex-1"><div className="font-medium text-sm">{r.mode}</div><div className="text-xs text-slate-400">{r.detail}</div></div><div className="text-sm text-cyan-300">{r.transit}</div></div>
      ))}</div>
    </Card>
  );
}

function Risk({ cur }) {
  const h = cur.health || {};
  const items = [["Profitability", h.profitability], ["Payment / Risk", h.risk], ["Compliance", h.compliance], ["Documentation", h.documentation], ["Cash Flow", h.cashFlow]];
  return (
    <Card title="Risk analysis" icon={Warning} testid="cc-risk" action={<SourceBadge kind="brain" />}>
      <div className="space-y-3">
        {items.map(([l, s]) => (
          <div key={l}><div className="flex justify-between text-sm mb-1"><span>{l}</span><span style={{ color: ringColor[s?.color] || "#00C2FF" }}>{s?.value ?? "—"}</span></div>
            <div className="h-2 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full" style={{ width: `${s?.value || 0}%`, background: ringColor[s?.color] || "#00C2FF" }} /></div></div>
        ))}
      </div>
      <div className="text-xs text-slate-500 mt-3">Scores are computed from your margin, payment method, Incoterm and compliance completeness. Improve them in Settings & Documents.</div>
    </Card>
  );
}

function Buyers({ cur }) {
  return (
    <Card title="Buyers & Suppliers" icon={UsersThree} testid="cc-buyers" action={<SourceBadge kind="brain" />}>
      <p className="text-sm text-slate-300">Verified buyer & supplier contacts for <span className="text-cyan-300">{cur.product || `HS ${cur.hs}`}</span> in <span className="text-cyan-300">{cur.summary?.destination}</span> are available in the LeadNation app, with live contact details and verification.</p>
      <div className="flex flex-wrap gap-2 mt-4">
        <a href="#download" className="btn-primary">Find buyers in the app <ArrowRight size={15} weight="bold" /></a>
        <Link to={`/brain?q=${encodeURIComponent(`Who are the top importers/buyers of ${cur.product || `HS ${cur.hs}`} in ${cur.summary?.destination}?`)}`} className="btn-ghost">Ask the Brain</Link>
      </div>
    </Card>
  );
}

function Reports({ P, cur, compliance }) {
  const q = cur.lastQuote;
  const versions = cur.versions || [];
  const { isAuthed } = useAuth();
  const [gate, setGate] = useState(null); // {mode:'login'|'pay', price, currency, region}
  const [busy, setBusy] = useState(false);
  const region = (P.current?.transactionCurrency === "INR") ? "IN" : "INTL";
  const s = () => ({ headers: { "X-Trade-Session": P.session } });

  const doExport = async () => {
    if (!isAuthed) { setGate({ mode: "login" }); return; }
    setBusy(true);
    try {
      const { data: chk } = await api.get("/downloads/check", { params: { projectId: cur.id, region }, ...s() });
      if (chk.allowed) {
        await api.post("/downloads/record", { projectId: cur.id, projectTitle: cur.title, region }, s());
        window.print();
      } else {
        setGate({ mode: "pay", price: chk.price, currency: chk.currency, region: chk.region });
      }
    } catch (_) { setGate({ mode: "pay", price: region === "IN" ? 25 : 1, currency: region === "IN" ? "inr" : "usd", region }); }
    finally { setBusy(false); }
  };
  const pay = async (kind) => {
    const { data } = await api.post("/payments/checkout", { kind, region, projectId: cur.id, origin: window.location.origin }, s());
    window.location.href = data.url;
  };

  return (
    <>
      <Card title="Export & Reports" icon={FileText} testid="cc-reports">
        <p className="text-sm text-slate-300">Download a branded Quote & Compliance PDF for <span className="text-cyan-300">{cur.title}</span> — includes the full cost waterfall, buyer-market comparison and the {compliance?.importer?.name || "destination"} compliance report.</p>
        <div className="flex flex-wrap gap-2 mt-4">
          <button data-testid="cc-export-pdf" onClick={doExport} disabled={!q || busy} className="btn-primary disabled:opacity-50">{busy ? <CircleNotch size={15} className="animate-spin" /> : <Printer size={15} weight="bold" />} Export Quote PDF</button>
          <button data-testid="cc-save-version" onClick={() => P.addVersion("quote", `Quote ${new Date().toLocaleString()}`, q)} disabled={!q} className="btn-ghost disabled:opacity-50"><FloppyDisk size={15} weight="bold" /> Save quote version</button>
        </div>
        <div className="text-[11px] text-slate-500 mt-2">Your first report download is free. After that it's {region === "IN" ? "₹25" : "$1"} each — or get an unlimited monthly pass in your Account.</div>
        {!q && <div className="text-xs text-amber-300/80 mt-2">Complete your costing to enable the PDF.</div>}
      </Card>
      <Card title="Version history" icon={Clock} testid="cc-versions">
        {versions.length ? (
          <div className="space-y-2">{versions.slice().reverse().map((v) => (
            <div key={v.id} className="glass rounded-xl px-4 py-2.5 text-sm flex items-center gap-2"><FloppyDisk size={14} className="text-cyan-300" /><span>{v.label}</span><span className="ml-auto text-[11px] text-slate-500">{String(v.at).slice(5, 16).replace("T", " ")}</span></div>
          ))}</div>
        ) : <Empty msg="No saved versions yet. Save a quote version to keep history." />}
      </Card>

      {gate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setGate(null)}>
          <div className="glass-strong rounded-3xl p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()} data-testid="cc-paywall">
            {gate.mode === "login" ? (
              <>
                <div className="font-display font-bold text-lg flex items-center gap-2"><User size={18} className="text-cyan-300" /> Sign in to download</div>
                <p className="text-sm text-slate-400 mt-2">Create a free account (shared with the LeadNation app) to download your report and keep it in your account.</p>
                <Link to="/login" className="btn-primary w-full justify-center mt-4" data-testid="cc-paywall-login">Sign in / Create account</Link>
              </>
            ) : (
              <>
                <div className="font-display font-bold text-lg flex items-center gap-2"><Printer size={18} className="text-cyan-300" /> Unlock this download</div>
                <p className="text-sm text-slate-400 mt-2">You've used your free download. Pay <span className="text-cyan-300 font-semibold">{gate.currency === "inr" ? `₹${gate.price}` : `$${gate.price}`}</span> for this report, or get an unlimited monthly pass.</p>
                <div className="flex flex-col gap-2 mt-4">
                  <button data-testid="cc-paywall-pay" onClick={() => pay("download")} className="btn-primary justify-center">Pay {gate.currency === "inr" ? `₹${gate.price}` : `$${gate.price}`} & download</button>
                  <button data-testid="cc-paywall-sub" onClick={() => pay("subscription")} className="btn-ghost justify-center"><CrownSimple size={15} weight="bold" /> Get unlimited monthly pass</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function BrainModule({ cur, P }) {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const ask = async (text) => {
    const question = text || q; if (!question.trim()) return;
    setMsgs((m) => [...m, { role: "user", text: question }]); setQ(""); setBusy(true);
    try {
      const { data } = await api.post("/brain/ask", { question, session_id: `tcc-${cur.id}`, page_context: { type: "tcc", workspace: "brain", product: cur.product, hs: cur.hs, exporter: cur.exporter, importer: cur.importer, stage: cur.stage } });
      setMsgs((m) => [...m, { role: "assistant", text: data.answer || "No answer." }]);
    } catch (_) { setMsgs((m) => [...m, { role: "assistant", text: "Brain unavailable, try again." }]); }
    finally { setBusy(false); }
  };
  const prompts = [`Best Incoterm for ${cur.summary?.origin} → ${cur.summary?.destination}?`, `How can I cut duty on this lane?`, `What documents am I missing?`];
  return (
    <Card title="LeadNation Brain · project-aware" icon={Brain} testid="cc-brain">
      <div className="space-y-3 max-h-[420px] overflow-auto mb-3">
        {msgs.length === 0 && <div className="flex flex-wrap gap-2">{prompts.map((p, i) => <button key={i} onClick={() => ask(p)} className="glass rounded-full px-3 py-1.5 text-xs hover:border-cyan-400/30">{p}</button>)}</div>}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div className={`inline-block rounded-2xl px-4 py-2.5 text-sm ${m.role === "user" ? "bg-cyan-500/15 text-cyan-100" : "glass text-left"}`}>{m.role === "user" ? m.text : <MD text={m.text} />}</div>
          </div>
        ))}
        {busy && <div className="text-sm text-slate-400 flex items-center gap-2"><CircleNotch size={14} className="animate-spin" /> Thinking…</div>}
      </div>
      <div className="flex gap-2">
        <input data-testid="cc-brain-input" className={inputCls} value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} placeholder="Ask about this trade project…" />
        <button data-testid="cc-brain-send" onClick={() => ask()} className="btn-primary !px-4"><PaperPlaneTilt size={16} weight="bold" /></button>
      </div>
    </Card>
  );
}

function Settings({ P, cur }) {
  const a = cur.assumptions || {};
  const setA = (k, v) => P.update({ assumptions: { ...a, [k]: v } });
  const ASSUME = [["insurancePct", "Insurance %"], ["commissionPct", "Commission %"], ["interestPct", "Interest %"], ["containerCost", "Container cost"]];
  return (
    <>
      <Card title="Project details" icon={Gear} testid="cc-settings">
        <div className="grid sm:grid-cols-2 gap-3">
          <Lbl t="Title"><input data-testid="cc-set-title" className={inputCls} value={cur.title} onChange={(e) => P.update({ title: e.target.value })} /></Lbl>
          <Lbl t="Buyer"><input data-testid="cc-set-buyer" className={inputCls} value={cur.buyer || ""} onChange={(e) => P.update({ buyer: e.target.value })} placeholder="Buyer / importer name" /></Lbl>
          <Lbl t="Supplier"><input className={inputCls} value={cur.supplier || ""} onChange={(e) => P.update({ supplier: e.target.value })} placeholder="Supplier name" /></Lbl>
          <Lbl t="Payment method"><select data-testid="cc-set-payment" className={inputCls} value={cur.paymentMethod || ""} onChange={(e) => P.update({ paymentMethod: e.target.value })}><option value="">—</option>{["Advance", "LC (Letter of Credit)", "DA", "DP", "CAD", "Open Account"].map((x) => <option key={x}>{x}</option>)}</select></Lbl>
        </div>
        <Lbl t="Notes" className="mt-3"><textarea className={`${inputCls} h-20`} value={cur.notes || ""} onChange={(e) => P.update({ notes: e.target.value })} /></Lbl>
      </Card>
      <Card title="Assumptions (used by Digital Twin)" icon={Sparkle} testid="cc-assumptions" action={<SourceBadge kind="manual" />}>
        <div className="grid sm:grid-cols-2 gap-3">
          {ASSUME.map(([k, l]) => <Lbl key={k} t={l}><input type="number" className={inputCls} value={a[k] ?? ""} onChange={(e) => setA(k, num(e.target.value))} /></Lbl>)}
        </div>
        <div className="text-xs text-slate-500 mt-2">Exchange rate: <span className="text-cyan-300">live</span> (open.er-api.com). These assumptions will feed scenario simulation in Volume 2.</div>
      </Card>
      <Card title="Danger zone" icon={Trash} testid="cc-danger">
        <button onClick={() => { if (window.confirm("Delete this project?")) P.deleteProject(cur.id); }} className="btn-ghost !text-rose-300 !border-rose-400/30"><Trash size={15} /> Delete project</button>
      </Card>
    </>
  );
}

/* ---------------- Right Brain panel ---------------- */
function BrainPanel({ P, cur, setModule }) {
  const h = cur.health || {};
  const warnings = [];
  if (h.risk?.color === "rose") warnings.push("High payment/currency risk");
  if (h.compliance?.value < 60) warnings.push("Compliance not confirmed");
  if (h.profitability?.value < 40) warnings.push("Thin margin — review pricing");
  const q = cur.lastQuote;
  return (
    <div className="glass-strong rounded-3xl p-4 lg:sticky lg:top-4 space-y-4" data-testid="cc-brain-panel">
      <div className="flex items-center gap-2"><Brain size={18} weight="duotone" className="text-cyan-300" /><span className="font-display font-bold">LeadNation Brain</span><SourceBadge kind="brain" /></div>

      <div>
        <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5">Recommendations</div>
        {P.insightsLoading && <div className="text-xs text-slate-400 flex items-center gap-2"><CircleNotch size={12} className="animate-spin" /> Analysing…</div>}
        {!P.insightsLoading && P.insights ? <div className="text-sm max-h-72 overflow-auto"><MD text={P.insights} /></div>
          : !P.insightsLoading && <div className="text-xs text-slate-500">Complete your costing — the Brain will analyse savings, the best market and risks here.</div>}
      </div>

      {warnings.length > 0 && (
        <div><div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5">Warnings</div>
          <div className="space-y-1.5">{warnings.map((w, i) => <div key={i} className="text-xs text-amber-300 flex items-center gap-2"><Warning size={12} /> {w}</div>)}</div>
        </div>
      )}

      <div>
        <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5">Quick actions</div>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => setModule("brain")} className="glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30 flex items-center gap-1.5"><Brain size={13} className="text-cyan-300" /> Ask</button>
          <button onClick={() => setModule("reports")} className="glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30 flex items-center gap-1.5"><Printer size={13} className="text-cyan-300" /> Export PDF</button>
          <button onClick={() => setModule("market")} className="glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30 flex items-center gap-1.5"><ChartBar size={13} className="text-cyan-300" /> Markets</button>
          <button onClick={() => setModule("compliance")} className="glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30 flex items-center gap-1.5"><ShieldCheck size={13} className="text-cyan-300" /> Compliance</button>
        </div>
      </div>

      {q?.comparison?.[0] && <div className="text-xs text-slate-400 border-t border-white/10 pt-3">Best market now: <span className="text-cyan-300 font-medium">{q.comparison[0].country}</span></div>}
    </div>
  );
}

/* ---------------- small helpers ---------------- */
const Lbl = ({ t, children, className = "" }) => (
  <label className={`block ${className}`}><span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400">{t}</span><div className="mt-1">{children}</div></label>
);
function Kpi({ label, value, sub, accent = "text-white", explain, quote }) {
  return (
    <div className="glass rounded-2xl px-4 py-3" data-testid={`kpi-${label.toLowerCase().replace(/[^a-z]/g, "-").slice(0, 20)}`}>
      <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center gap-1">{label} {explain && <ExplainBtn field={explain} quote={quote} />}</div>
      <div className={`font-display font-bold text-xl mt-0.5 ${accent}`}>{value}</div>
      {sub && <div className="text-[11px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
const Empty = ({ msg, spin }) => <div className="glass rounded-3xl p-8 text-center text-slate-400 text-sm flex items-center justify-center gap-2">{spin && <CircleNotch size={16} className="animate-spin" />}{msg}</div>;
