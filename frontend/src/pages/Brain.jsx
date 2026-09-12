import React, { useState, useRef, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Brain, PaperPlaneTilt, Sparkle, Cpu, Lightning, ArrowUpRight, CircleNotch, Package, MagnifyingGlass } from "@phosphor-icons/react";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api } from "@/lib/api";

const SUGGESTED = [
  "Can I export Agarbatti to UAE?",
  "Which HSN code should I use for Basmati rice?",
  "What documents are required to export pharmaceuticals?",
  "Which countries import the most spices from India?",
  "How do I get IEC registration?",
  "What is the duty on textiles to Australia?",
];

const ENGINE_LABELS = {
  country_context: "Country Context", trade_news: "Trade News",
  market_intelligence: "Market Intelligence", learning: "Learning",
  compliance: "Compliance", tariff: "Tariff", logistics: "Logistics",
  policy: "Policy", product_intelligence: "Product Intelligence",
  business_services: "Business Services", marketplace: "Marketplace", network: "Network",
};

function sessionId() {
  try {
    let s = localStorage.getItem("ln_brain_session");
    if (!s) { s = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now())); localStorage.setItem("ln_brain_session", s); }
    return s;
  } catch (_) { return String(Date.now()); }
}

function FormattedAnswer({ text }) {
  const lines = (text || "").split("\n");
  const out = [];
  let bullets = [];
  const inline = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith("**") && p.endsWith("**") ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span> : <span key={j}>{p}</span>);
  const flush = (k) => { if (bullets.length) { out.push(<ul key={"u" + k} className="list-disc pl-5 space-y-1 text-sm text-slate-300">{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>); bullets = []; } };
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

export default function BrainPage() {
  const [thread, setThread] = useState([
    { role: "assistant", answer: "I'm the **Vametra AI Brain** — the trade operating system. Ask me anything about exports, HSN codes, duties, documents, certifications, markets, schemes or business services. I orchestrate 12 trade engines to give you one clear answer." },
  ]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const sid = useRef(sessionId());
  const [searchParams] = useSearchParams();
  const [pf, setPf] = useState({ direction: "Export", product: "", origin: "India", destination: "", hsn: "" });

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [thread, loading]);

  useEffect(() => {
    const preset = searchParams.get("q");
    if (preset) ask(preset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const ask = async (question, mode) => {
    if (!question.trim() || loading) return;
    setThread((t) => [...t, { role: "user", answer: question }]);
    setQ("");
    setLoading(true);
    try {
      const { data } = await api.post("/brain/ask", { question, session_id: sid.current, mode });
      setThread((t) => [...t, {
        role: "assistant", answer: data.answer, isMock: data.isMock,
        engines: data.enginesUsed || [], sources: data.sources || [],
        ctas: data.ctas || [], buyerAccess: data.buyerAccess || null,
        recommendations: data.recommendations || [],
        entities: data.entities,
      }]);
    } catch (e) {
      setThread((t) => [...t, { role: "assistant", answer: "Something went wrong reaching the Brain. Please try again.", error: true }]);
    } finally { setLoading(false); }
  };

  const askProduct = () => {
    if (!pf.product.trim() || loading) return;
    const isExp = pf.direction === "Export";
    const q = `${pf.direction} ${pf.product}${pf.origin ? ` from ${pf.origin}` : ""}`
      + (pf.destination ? ` ${isExp ? "to" : "from"} ${pf.destination}` : "")
      + (pf.hsn ? ` (HSN ${pf.hsn})` : "")
      + `: give me the HSN code, import duty and taxes, required documents and licences, certifications,`
      + ` market demand, top importing countries, logistics options, export incentives and verified buyers.`;
    ask(q, "product");
  };

  return (
    <>
      <SEO title="Vametra AI Brain · ChatGPT for Global Trade"
        description="The Vametra AI Brain orchestrates 12 trade engines — compliance, tariffs, HSN, country intelligence, logistics and more — into one unified answer for global traders."
        path="/brain"
        keywords="trade AI, export AI, HSN AI, customs AI, trade brain, import export assistant, India trade intelligence"
      />

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-28 pb-10">
        <div className="flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
          <Brain size={16} weight="duotone" /> Vametra AI Intelligence Layer
        </div>
        <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl mt-4 max-w-4xl leading-[1.05]">
          The trade brain.<br /><span className="text-gradient">One mind for global trade.</span>
        </h1>
        <p className="mt-5 text-base sm:text-lg text-slate-300 max-w-2xl">
          Not a chatbot — an operating system. The Brain orchestrates 12 engines across compliance,
          tariffs, products, countries, logistics and policy to answer any trade question.
        </p>
        <div className="mt-6 flex flex-wrap gap-2" data-testid="brain-engine-badges">
          {Object.values(ENGINE_LABELS).map((l) => (
            <span key={l} className="glass rounded-full px-3 py-1 text-[11px] text-slate-300 border border-white/10">{l}</span>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-6 pb-16">
        {/* Suggestions + status */}
        <aside className="lg:col-span-4 space-y-6">
          {/* PRODUCT INTELLIGENCE — replaces the old standalone Product Info Engine */}
          <div className="glass-strong rounded-3xl p-6" data-testid="brain-product-panel">
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
              <Package size={14} weight="duotone" /> Product intelligence
            </div>
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              Any product, any border — HSN, duty, documents, certifications, demand, top markets and verified buyers in one answer.
            </p>
            <div className="mt-4 space-y-2.5">
              <div className="flex gap-1.5">
                {["Export", "Import"].map((d) => (
                  <button key={d} data-testid={`brain-pi-dir-${d.toLowerCase()}`} onClick={() => setPf({ ...pf, direction: d })}
                    className={`flex-1 py-2 rounded-xl text-xs ${pf.direction === d ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>{d}</button>
                ))}
              </div>
              <input data-testid="brain-pi-product" value={pf.product} onChange={(e) => setPf({ ...pf, product: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && askProduct()}
                placeholder="Product — e.g. Agarbatti, Basmati rice"
                className="w-full glass rounded-xl px-3 py-2.5 text-sm outline-none text-white placeholder:text-slate-500 focus:border-cyan-400/40" />
              <div className="grid grid-cols-2 gap-2">
                <input data-testid="brain-pi-origin" value={pf.origin} onChange={(e) => setPf({ ...pf, origin: e.target.value })}
                  onKeyDown={(e) => e.key === "Enter" && askProduct()} placeholder="Origin"
                  className="w-full glass rounded-xl px-3 py-2.5 text-sm outline-none text-white placeholder:text-slate-500 focus:border-cyan-400/40" />
                <input data-testid="brain-pi-destination" value={pf.destination} onChange={(e) => setPf({ ...pf, destination: e.target.value })}
                  onKeyDown={(e) => e.key === "Enter" && askProduct()} placeholder="Destination"
                  className="w-full glass rounded-xl px-3 py-2.5 text-sm outline-none text-white placeholder:text-slate-500 focus:border-cyan-400/40" />
              </div>
              <input data-testid="brain-pi-hsn" value={pf.hsn} onChange={(e) => setPf({ ...pf, hsn: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && askProduct()} placeholder="HSN / HS code (optional)"
                className="w-full glass rounded-xl px-3 py-2.5 text-sm outline-none text-white placeholder:text-slate-500 focus:border-cyan-400/40" />
              <button data-testid="brain-pi-submit" onClick={askProduct} disabled={loading || !pf.product.trim()}
                className="btn-primary w-full justify-center text-xs disabled:opacity-50">
                {loading ? <CircleNotch size={14} className="animate-spin" /> : <><MagnifyingGlass size={14} weight="bold" /> Analyse product</>}
              </button>
            </div>
          </div>

          <div className="glass-strong rounded-3xl p-6 h-fit">
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
              <Sparkle size={14} weight="duotone" /> Ask the Brain
            </div>
            <div className="mt-3 space-y-2">
              {SUGGESTED.map((s, i) => (
                <button key={i} data-testid={`brain-suggest-${i}`} onClick={() => ask(s)}
                  className="w-full text-left glass rounded-xl px-3 py-2.5 text-sm hover:border-cyan-400/40 transition-all">{s}</button>
              ))}
            </div>
          </div>
          <div className="glass-strong rounded-3xl p-6">
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-violet-300 flex items-center gap-2">
              <Cpu size={14} weight="duotone" /> How it works
            </div>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              <li className="flex gap-2"><Lightning size={16} weight="duotone" className="text-cyan-300 shrink-0 mt-0.5" /> Detects intent + entities (product, country, HSN, service)</li>
              <li className="flex gap-2"><Lightning size={16} weight="duotone" className="text-cyan-300 shrink-0 mt-0.5" /> Routes to the right engines & Knowledge Base</li>
              <li className="flex gap-2"><Lightning size={16} weight="duotone" className="text-cyan-300 shrink-0 mt-0.5" /> Composes one unified, sourced answer</li>
            </ul>
          </div>
        </aside>

        {/* Chat */}
        <div className="lg:col-span-8 glass-strong rounded-3xl p-6 flex flex-col min-h-[560px]">
          <div className="flex-1 space-y-4 overflow-auto max-h-[560px] pr-1" data-testid="brain-thread">
            {thread.map((m, i) => (
              <div key={i} data-testid={`brain-msg-${i}`} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && (
                  <div className="w-9 h-9 shrink-0 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-white/10">
                    <Brain size={18} weight="duotone" className="text-cyan-300" />
                  </div>
                )}
                <div className={`rounded-2xl px-4 py-3 max-w-[85%] ${m.role === "user" ? "bg-cyan-500/15 border border-cyan-400/30 text-white text-sm" : "bg-white/5 border border-white/10"}`}>
                  {m.role === "user" ? m.answer : <FormattedAnswer text={m.answer} />}
                  {m.engines?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5" data-testid={`brain-engines-${i}`}>
                      {m.engines.map((e) => (
                        <span key={e} className="text-[10px] font-mono-display tracking-wider uppercase px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-400/30 text-violet-200">{ENGINE_LABELS[e] || e}</span>
                      ))}
                    </div>
                  )}
                  {m.sources?.length > 0 && (
                    <div className="mt-3 grid sm:grid-cols-2 gap-2" data-testid={`brain-sources-${i}`}>
                      {m.sources.slice(0, 4).map((s, k) => (
                        <Link key={k} to={s.to} className="flex items-center justify-between gap-2 glass rounded-xl px-3 py-2 text-xs hover:border-cyan-400/30">
                          <span className="truncate">{s.title}</span>
                          <ArrowUpRight size={13} className="text-cyan-300 shrink-0" />
                        </Link>
                      ))}
                    </div>
                  )}
                  {m.buyerAccess && (
                    <div className="mt-3 glass rounded-xl px-3 py-2 text-xs flex flex-wrap items-center gap-2" data-testid={`brain-buyer-access-${i}`}>
                      <span className="text-cyan-300 font-mono-display uppercase tracking-widest text-[9px]">Verified buyers</span>
                      <span className="text-slate-300">{m.buyerAccess.count} matching</span>
                      {m.buyerAccess.locked
                        ? <Link to="/pricing" className="text-amber-300 hover:underline">Subscribe to unlock names →</Link>
                        : <Link to="/buyers" className="text-emerald-300 hover:underline">Open buyer list →</Link>}
                    </div>
                  )}
                  {m.ctas?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2" data-testid={`brain-ctas-${i}`}>
                      {m.ctas.map((c, k) => (
                        <Link key={k} to={c.to} className="text-[11px] px-3 py-1.5 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-500/30">{c.label}</Link>
                      ))}
                    </div>
                  )}
                  {m.isMock && <div className="mt-2 text-[10px] font-mono-display tracking-widest uppercase text-amber-300/80">Deterministic engine composition · live AI ready</div>}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-xl bg-cyan-500/20 grid place-items-center"><Brain size={18} weight="duotone" className="text-cyan-300" /></div>
                <div className="text-sm text-slate-400 px-4 py-3 flex items-center gap-2"><CircleNotch size={16} className="animate-spin" /> Orchestrating engines…</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form onSubmit={(e) => { e.preventDefault(); ask(q); }} className="mt-4 flex items-center gap-2 glass rounded-2xl px-3 py-2">
            <input data-testid="brain-input" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Ask about exports, HSN, duties, documents, markets, schemes…"
              className="flex-1 bg-transparent outline-none text-white placeholder:text-slate-500 px-2 py-2 text-sm" />
            <button data-testid="brain-send" type="submit" disabled={loading} className="btn-primary !py-2 !px-4 text-xs disabled:opacity-50">
              <PaperPlaneTilt size={14} weight="bold" />
            </button>
          </form>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>
    </>
  );
}
