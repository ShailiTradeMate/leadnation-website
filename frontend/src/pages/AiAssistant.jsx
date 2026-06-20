import React, { useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { Link } from "react-router-dom";
import { Robot, PaperPlaneTilt, Sparkle } from "@phosphor-icons/react";

const SUGGESTED = [
  "Can I export agarbatti to UAE?",
  "What documents are required to export Basmati rice?",
  "Which countries import the most pharmaceuticals from India?",
  "What certifications are needed for FSSAI exports?",
  "Which HSN code should I use for cotton textiles?",
];

export default function AiAssistant() {
  const [thread, setThread] = useState([
    { role: "assistant", text: "Hi — I'm the LeadNation Trade Copilot. Ask me anything about exports, HSN, documents, certifications or markets." },
  ]);
  const [q, setQ] = useState("");
  const [suggestedTools, setSuggestedTools] = useState([]);
  const [loading, setLoading] = useState(false);

  const ask = async (question) => {
    if (!question.trim()) return;
    setThread((t) => [...t, { role: "user", text: question }]);
    setQ("");
    setLoading(true);
    try {
      const { data } = await api.post("/ai-ask", { question });
      setThread((t) => [...t, { role: "assistant", text: data.answer, isMock: data.isMock }]);
      setSuggestedTools(data.suggestedTools || []);
    } finally { setLoading(false); }
  };

  return (
    <>
      <SEO title="AI Trade Copilot · Ask Anything About Global Trade"
        description="LeadNation's AI Trade Copilot answers any export, HSN, FTA or certification question instantly. Free preview."
        path="/ai-assistant"
        keywords="AI trade assistant, export AI, GPT for trade, HSN AI, customs AI, trade chatbot"
      />
      <PageHero testIdPrefix="ai" label="LeadNation AI · Trade Copilot"
        title="Ask anything. Export anywhere."
        sub="The AI copilot for global traders. Ask about HSN codes, customs, certifications, markets — get a clear answer in seconds."
      />

      <section className="max-w-6xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-4 glass-strong rounded-3xl p-6 h-fit">
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2">
            <Sparkle size={14} weight="duotone" /> Try asking
          </div>
          <div className="mt-3 space-y-2">
            {SUGGESTED.map((s, i) => (
              <button
                key={i}
                data-testid={`ai-suggest-${i}`}
                onClick={() => ask(s)}
                className="w-full text-left glass rounded-xl px-3 py-2.5 text-sm hover:border-cyan-400/40 transition-all"
              >{s}</button>
            ))}
          </div>
          {suggestedTools.length > 0 && (
            <>
              <div className="mt-6 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Try these tools</div>
              <div className="mt-3 space-y-2">
                {suggestedTools.map((t) => (
                  <Link key={t.to} to={t.to} className="block glass rounded-xl px-3 py-2 text-sm hover:border-cyan-400/30">{t.label}</Link>
                ))}
              </div>
            </>
          )}
        </aside>

        <div className="lg:col-span-8 glass-strong rounded-3xl p-6 flex flex-col min-h-[520px]">
          <div className="flex-1 space-y-3 overflow-auto max-h-[520px] pr-1">
            {thread.map((m, i) => (
              <div key={i} data-testid={`ai-msg-${i}`} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && (
                  <div className="w-9 h-9 shrink-0 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-white/10">
                    <Robot size={18} weight="duotone" className="text-cyan-300" />
                  </div>
                )}
                <div className={`rounded-2xl px-4 py-3 max-w-[80%] text-sm ${m.role === "user" ? "bg-cyan-500/15 border border-cyan-400/30 text-white" : "bg-white/5 border border-white/10 text-slate-200"}`}>
                  {m.text}
                  {m.isMock && <div className="mt-2 text-[10px] font-mono-display tracking-widest uppercase text-amber-300/80">Mocked response — live AI coming soon</div>}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3"><div className="w-9 h-9 rounded-xl bg-cyan-500/20 grid place-items-center"><Robot size={18} weight="duotone" /></div><div className="text-sm text-slate-400 px-4 py-3">Thinking…</div></div>
            )}
          </div>
          <form onSubmit={(e) => { e.preventDefault(); ask(q); }} className="mt-4 flex items-center gap-2 glass rounded-2xl px-3 py-2">
            <input
              data-testid="ai-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ask about HSN, FTA, certifications, buyers…"
              className="flex-1 bg-transparent outline-none text-white placeholder:text-slate-500 px-2 py-2 text-sm"
            />
            <button data-testid="ai-send" type="submit" className="btn-primary !py-2 !px-4 text-xs">
              <PaperPlaneTilt size={14} weight="bold" />
            </button>
          </form>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
