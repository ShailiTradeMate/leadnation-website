import React, { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { Package, MagnifyingGlass, CircleNotch, Brain, ArrowUpRight } from "@phosphor-icons/react";

const ENGINE_LABELS = {
  country_context: "Country", trade_news: "News", market_intelligence: "Market",
  learning: "Learning", compliance: "Compliance", tariff: "Tariff", logistics: "Logistics",
  policy: "Policy", product_intelligence: "Product", business_services: "Services",
  marketplace: "Marketplace", network: "Network",
};

function Formatted({ text }) {
  const lines = (text || "").split("\n");
  const out = [];
  let bullets = [];
  const flush = (k) => { if (bullets.length) { out.push(<ul key={"u" + k} className="list-disc pl-5 space-y-1 text-sm text-slate-300">{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>); bullets = []; } };
  const inline = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith("**") && p.endsWith("**") ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span> : <span key={j}>{p}</span>);
  lines.forEach((raw, k) => {
    const l = raw.trim();
    if (!l || l === "---") { flush(k); return; }
    if (l.startsWith("### ")) { flush(k); out.push(<h4 key={k} className="font-display font-bold text-base mt-4 text-white">{inline(l.slice(4))}</h4>); }
    else if (l.startsWith("## ")) { flush(k); out.push(<h3 key={k} className="font-display font-bold text-lg mt-5 text-cyan-200">{inline(l.slice(3))}</h3>); }
    else if (l.startsWith("- ") || l.startsWith("* ")) { bullets.push(l.slice(2)); }
    else { flush(k); out.push(<p key={k} className="text-sm leading-relaxed text-slate-200">{inline(l)}</p>); }
  });
  flush("end");
  return <div className="space-y-2">{out}</div>;
}

const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none text-white placeholder:text-slate-500 focus:border-cyan-400/40";
const Field = ({ label, children }) => (
  <label className="block">
    <span className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400">{label}</span>
    <div className="mt-1.5">{children}</div>
  </label>
);

export default function ProductInfo() {
  const [f, setF] = useState({ direction: "Export", product: "", origin: "India", destination: "", hsn: "" });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const sid = useRef("pi-" + (crypto.randomUUID ? crypto.randomUUID() : Date.now()));

  const analyze = async () => {
    if (!f.product.trim() || loading) return;
    setLoading(true); setRes(null);
    const isExp = f.direction === "Export";
    const q = `${f.direction} ${f.product} ${isExp ? "from" : "to"} ${f.origin || "India"}`
      + (f.destination ? ` ${isExp ? "to" : "from"} ${f.destination}` : "")
      + (f.hsn ? ` (HSN ${f.hsn})` : "")
      + `: which countries import/export this, the HSN code, applicable duty, required documents, certifications, market demand and government benefits.`;
    try {
      const { data } = await api.post("/brain/ask", {
        question: q, session_id: sid.current,
        page_context: f.hsn ? { type: "hsn", slug: f.hsn } : (f.product ? { type: "product", slug: f.product.toLowerCase().replace(/\s+/g, "-") } : undefined),
      });
      setRes(data);
      setTimeout(() => document.getElementById("pi-result")?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e) {
      setRes({ answer: e?.response?.status === 429 ? "You're asking quickly — please wait a moment." : "Something went wrong. Please try again.", error: true });
    } finally { setLoading(false); }
  };

  return (
    <>
      <SEO title="Product Info Engine · Any product, any market (AI-powered)"
        description="Type any product, any country, import or export — the LeadNation Brain returns HSN, duty, documents, certifications, markets and government benefits."
        path="/product-info"
        keywords="product trade intelligence, HSN finder, import export duty, top markets, certifications, AI trade assistant" />
      <PageHero testIdPrefix="pi" label="Product Info Engine · Brain-powered"
        title="Any product. Any border. Real answers."
        sub="Type any product in the world, choose import or export, add origin/destination (and HSN if you know it). The LeadNation Brain analyses markets, duty, documents, certifications and benefits — instantly." />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="glass-strong rounded-3xl p-6 sm:p-8 grid grid-cols-1 md:grid-cols-6 gap-4">
          <Field label="Direction">
            <div className="flex gap-1.5">
              {["Export", "Import"].map((d) => (
                <button key={d} data-testid={`pi-dir-${d.toLowerCase()}`} onClick={() => setF({ ...f, direction: d })}
                  className={`flex-1 py-3 rounded-xl text-sm ${f.direction === d ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>{d}</button>
              ))}
            </div>
          </Field>
          <Field label="Product name"><input data-testid="pi-product" className={inputCls} placeholder="e.g. Agarbatti, Saffron, Lithium battery" value={f.product} onChange={(e) => setF({ ...f, product: e.target.value })} onKeyDown={(e) => e.key === "Enter" && analyze()} /></Field>
          <Field label="Origin"><input data-testid="pi-origin" className={inputCls} placeholder="India" value={f.origin} onChange={(e) => setF({ ...f, origin: e.target.value })} onKeyDown={(e) => e.key === "Enter" && analyze()} /></Field>
          <Field label="Destination"><input data-testid="pi-destination" className={inputCls} placeholder="e.g. UAE, USA, Germany" value={f.destination} onChange={(e) => setF({ ...f, destination: e.target.value })} onKeyDown={(e) => e.key === "Enter" && analyze()} /></Field>
          <Field label="HSN (optional)"><input data-testid="pi-hsn" className={inputCls} placeholder="e.g. 33074100" value={f.hsn} onChange={(e) => setF({ ...f, hsn: e.target.value })} onKeyDown={(e) => e.key === "Enter" && analyze()} /></Field>
          <div className="flex items-end">
            <button data-testid="pi-submit" onClick={analyze} disabled={loading || !f.product.trim()} className="btn-primary w-full justify-center disabled:opacity-50">
              {loading ? <CircleNotch size={16} className="animate-spin" /> : <><MagnifyingGlass size={16} weight="bold" /> Analyze</>}
            </button>
          </div>
        </div>

        {loading && <div className="mt-8 text-slate-400 flex items-center gap-2"><CircleNotch size={18} className="animate-spin" /> The Brain is analysing {f.product}…</div>}

        {res && (
          <div id="pi-result" data-testid="pi-result" className="mt-8 grid lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 glass-strong rounded-3xl p-6 sm:p-8">
              <div className="flex items-center gap-2 mb-4">
                <Package size={20} weight="duotone" className="text-cyan-300" />
                <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">{f.direction} · {f.product || "Product"}{f.destination ? ` · ${f.destination}` : ""}</div>
              </div>
              <Formatted text={res.answer} />
              {res.enginesUsed?.length > 0 && (
                <div className="mt-5 flex flex-wrap gap-1.5">
                  {res.enginesUsed.map((e) => <span key={e} className="text-[10px] font-mono-display uppercase px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-400/30 text-violet-200">{ENGINE_LABELS[e] || e}</span>)}
                </div>
              )}
              <Link to={`/brain?q=${encodeURIComponent(`Tell me more about ${f.direction.toLowerCase()}ing ${f.product}${f.destination ? " to " + f.destination : ""}`)}`} className="btn-ghost mt-5 inline-flex" data-testid="pi-ask-brain"><Brain size={15} weight="duotone" /> Continue in the Brain</Link>
            </div>
            <aside className="lg:col-span-4 space-y-4">
              {res.sources?.length > 0 && (
                <div className="glass-strong rounded-3xl p-5">
                  <div className="text-xs font-mono-display tracking-widest uppercase text-cyan-300 mb-3">Sources</div>
                  <div className="space-y-2">{res.sources.slice(0, 5).map((s, i) => (
                    <Link key={i} to={s.to} className="flex items-center justify-between gap-2 glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30"><span className="truncate">{s.title}</span><ArrowUpRight size={12} className="text-cyan-300 shrink-0" /></Link>
                  ))}</div>
                </div>
              )}
              {res.recommendations?.length > 0 && (
                <div className="glass-strong rounded-3xl p-5">
                  <div className="text-xs font-mono-display tracking-widest uppercase text-violet-300 mb-3">Related</div>
                  <div className="space-y-2">{res.recommendations.slice(0, 6).map((r, i) => (
                    <Link key={i} to={r.to} className="block glass rounded-xl px-3 py-2 text-xs hover:border-violet-400/30"><span className="text-[9px] uppercase text-slate-500 mr-1">{r.kind}</span>{r.label}</Link>
                  ))}</div>
                </div>
              )}
              {res.ctas?.length > 0 && (
                <div className="flex flex-wrap gap-2">{res.ctas.map((c, i) => (
                  <Link key={i} to={c.to} className="text-xs px-3 py-1.5 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-500/30">{c.label}</Link>
                ))}</div>
              )}
            </aside>
          </div>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}
