import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { Brain, PaperPlaneTilt, Sparkle, Cpu, Lightning, ArrowUpRight, CircleNotch } from "@phosphor-icons/react";
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
  return (
    <div className="space-y-3">
      {text.split("\n\n").map((para, i) => {
        const parts = para.split(/(\*\*[^*]+\*\*)/g);
        return (
          <p key={i} className="text-sm leading-relaxed text-slate-200">
            {parts.map((p, j) =>
              p.startsWith("**") && p.endsWith("**")
                ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span>
                : <span key={j}>{p}</span>
            )}
          </p>
        );
      })}
    </div>
  );
}

export default function BrainPage() {
  const [thread, setThread] = useState([
    { role: "assistant", answer: "I'm the **LeadNation Brain** — the trade operating system. Ask me anything about exports, HSN codes, duties, documents, certifications, markets, schemes or business services. I orchestrate 12 trade engines to give you one clear answer." },
  ]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const sid = useRef(sessionId());

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [thread, loading]);

  const ask = async (question) => {
    if (!question.trim() || loading) return;
    setThread((t) => [...t, { role: "user", answer: question }]);
    setQ("");
    setLoading(true);
    try {
      const { data } = await api.post("/brain/ask", { question, session_id: sid.current });
      setThread((t) => [...t, {
        role: "assistant", answer: data.answer, isMock: data.isMock,
        engines: data.enginesUsed || [], sources: data.sources || [],
        entities: data.entities,
      }]);
    } catch (e) {
      setThread((t) => [...t, { role: "assistant", answer: "Something went wrong reaching the Brain. Please try again.", error: true }]);
    } finally { setLoading(false); }
  };

  return (
    <>
      <SEO title="LeadNation Brain · ChatGPT for Global Trade"
        description="The LeadNation Brain orchestrates 12 trade engines — compliance, tariffs, HSN, country intelligence, logistics and more — into one unified answer for global traders."
        path="/brain"
        keywords="trade AI, export AI, HSN AI, customs AI, trade brain, import export assistant, India trade intelligence"
      />

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-28 pb-10">
        <div className="flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
          <Brain size={16} weight="duotone" /> LeadNation Intelligence Layer
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
