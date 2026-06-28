import React, { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { Brain, X, PaperPlaneTilt, Sparkle, ArrowUpRight, CircleNotch } from "@phosphor-icons/react";
import { api } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";

const ENGINE_LABELS = {
  country_context: "Country", trade_news: "News", market_intelligence: "Market",
  learning: "Learning", compliance: "Compliance", tariff: "Tariff", logistics: "Logistics",
  policy: "Policy", product_intelligence: "Product", business_services: "Services",
  marketplace: "Marketplace", network: "Network",
};

const PROMPTS = {
  country: ["What products are most exported from this country?", "What documents are required?", "What are the latest trade opportunities?"],
  product: ["Can I export this product?", "What certifications are required?", "Who imports this product?"],
  hsn: ["Explain this HSN code.", "Which countries import this product?", "What benefits are available?"],
  service: ["What documents do I need?", "How long does registration take?", "What is the government fee?"],
  corridor: ["What documents are required for this corridor?", "What is the duty?", "Which products are popular here?"],
  industry: ["Who are the top exporters?", "What compliance is required?", "Which markets import most?"],
  marketplace: ["Find buyers for my product", "How do RFQs work?", "Show me verified suppliers"],
  academy: ["How do I start exporting?", "Explain Incoterms in simple terms", "What is RoDTEP?"],
  default: ["Can I export agarbatti to UAE?", "How do I get IEC registration?", "Which HSN code for basmati rice?"],
};

function derivePage(pathname) {
  const seg = pathname.split("/").filter(Boolean);
  const map = { countries: "country", products: "product", hsn: "hsn", services: "service", corridors: "corridor", industries: "industry" };
  if (seg.length >= 2 && map[seg[0]]) return { type: map[seg[0]], slug: seg[1] };
  if (seg[0] === "marketplace") return { type: "marketplace" };
  if (seg[0] === "academy") return { type: "academy" };
  return { type: "default" };
}

function sessionId() {
  try {
    let s = localStorage.getItem("ln_brain_session");
    if (!s) { s = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now())); localStorage.setItem("ln_brain_session", s); }
    return s;
  } catch (_) { return String(Date.now()); }
}

function Formatted({ text }) {
  const lines = (text || "").split("\n");
  const out = [];
  let bullets = [];
  const inline = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith("**") && p.endsWith("**") ? <span key={j} className="font-semibold text-cyan-300">{p.slice(2, -2)}</span> : <span key={j}>{p}</span>);
  const flush = (k) => { if (bullets.length) { out.push(<ul key={"u" + k} className="list-disc pl-4 space-y-0.5 text-[12px] text-slate-300">{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>); bullets = []; } };
  lines.forEach((raw, k) => {
    const l = raw.trim();
    if (!l || l === "---") { flush(k); return; }
    if (l.startsWith("### ")) { flush(k); out.push(<div key={k} className="font-semibold text-[13px] mt-2 text-white">{inline(l.slice(4))}</div>); }
    else if (l.startsWith("## ")) { flush(k); out.push(<div key={k} className="font-bold text-[13px] mt-2 text-cyan-200">{inline(l.slice(3))}</div>); }
    else if (l.startsWith("- ") || l.startsWith("* ")) { bullets.push(l.slice(2)); }
    else { flush(k); out.push(<p key={k} className="text-[13px] leading-relaxed text-slate-200">{inline(l)}</p>); }
  });
  flush("end");
  return <div className="space-y-1.5">{out}</div>;
}

export default function BrainWidget() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [thread, setThread] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const sid = useRef(sessionId());

  const page = derivePage(pathname);
  const prompts = PROMPTS[page.type] || PROMPTS.default;

  useEffect(() => { setThread([]); }, [pathname]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [thread, loading, open]);

  if (pathname.startsWith("/admin") || pathname === "/brain") return null;

  const ask = async (question) => {
    if (!question.trim() || loading) return;
    setThread((t) => [...t, { role: "user", answer: question }]);
    setQ("");
    setLoading(true);
    trackEvent("brain_widget_ask", { page: page.type });
    try {
      let user_id; try { user_id = localStorage.getItem("ln_user_id") || undefined; } catch (_) {}
      const { data } = await api.post("/brain/ask", {
        question, session_id: sid.current, user_id,
        page_context: page.slug ? { type: page.type, slug: page.slug } : undefined,
      });
      setThread((t) => [...t, {
        role: "assistant", answer: data.answer, engines: data.enginesUsed || [],
        sources: data.sources || [], recommendations: data.recommendations || [], ctas: data.ctas || [],
      }]);
    } catch (e) {
      const msg = e?.response?.status === 429 ? "You're asking quickly — give me a moment and try again." : "Something went wrong. Please try again.";
      setThread((t) => [...t, { role: "assistant", answer: msg, error: true }]);
    } finally { setLoading(false); }
  };

  const onCta = (c) => { trackEvent("brain_cta_click", { action: c.action }); navigate(c.to); setOpen(false); };

  return (
    <>
      {/* Launcher (above WhatsApp button) */}
      <button data-testid="brain-widget-fab" onClick={() => setOpen((o) => !o)}
        aria-label="Open LeadNation Brain"
        className="fixed bottom-24 right-6 z-[61] grid place-items-center w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 shadow-[0_10px_40px_rgba(0,194,255,0.45)] hover:scale-110 transition-transform">
        {open ? <X size={24} weight="bold" color="#fff" /> : <Brain size={26} weight="duotone" color="#fff" />}
        {!open && <span className="absolute inset-0 rounded-full bg-cyan-400 animate-ping opacity-20" />}
      </button>

      {open && (
        <div data-testid="brain-widget-panel"
          className="fixed bottom-[10.5rem] right-6 z-[61] w-[360px] max-w-[calc(100vw-2rem)] glass-strong rounded-3xl border border-white/10 shadow-2xl flex flex-col overflow-hidden"
          style={{ maxHeight: "min(70vh, 560px)" }}>
          <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 bg-gradient-to-r from-cyan-500/10 to-violet-500/10">
            <div className="w-8 h-8 rounded-lg grid place-items-center bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-white/10">
              <Brain size={16} weight="duotone" className="text-cyan-300" />
            </div>
            <div className="leading-tight">
              <div className="text-sm font-display font-bold">LeadNation Brain</div>
              <div className="text-[10px] text-cyan-300/80 uppercase tracking-widest font-mono-display">Ask anything · {page.type}</div>
            </div>
            <Link to="/brain" onClick={() => setOpen(false)} className="ml-auto text-[11px] text-slate-400 hover:text-cyan-300">Open full ↗</Link>
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-3" data-testid="brain-widget-thread">
            {thread.length === 0 && (
              <div>
                <div className="text-[11px] font-mono-display tracking-widest uppercase text-cyan-300 flex items-center gap-1.5 mb-2"><Sparkle size={12} weight="duotone" /> Try asking</div>
                <div className="space-y-2">
                  {prompts.map((p, i) => (
                    <button key={i} data-testid={`brain-widget-suggest-${i}`} onClick={() => ask(p)}
                      className="w-full text-left glass rounded-xl px-3 py-2 text-[13px] hover:border-cyan-400/40 transition-all">{p}</button>
                  ))}
                </div>
              </div>
            )}
            {thread.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : ""}`} data-testid={`brain-widget-msg-${i}`}>
                <div className={`rounded-2xl px-3 py-2 max-w-[92%] ${m.role === "user" ? "bg-cyan-500/15 border border-cyan-400/30 text-white text-[13px]" : "bg-white/5 border border-white/10"}`}>
                  {m.role === "user" ? m.answer : <Formatted text={m.answer} />}
                  {m.engines?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {m.engines.map((e) => <span key={e} className="text-[9px] font-mono-display uppercase px-1.5 py-0.5 rounded-full bg-violet-500/15 border border-violet-400/30 text-violet-200">{ENGINE_LABELS[e] || e}</span>)}
                    </div>
                  )}
                  {m.sources?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {m.sources.slice(0, 3).map((s, k) => (
                        <Link key={k} to={s.to} onClick={() => setOpen(false)} className="flex items-center justify-between gap-2 glass rounded-lg px-2.5 py-1.5 text-[11px] hover:border-cyan-400/30">
                          <span className="truncate">{s.title}</span><ArrowUpRight size={11} className="text-cyan-300 shrink-0" />
                        </Link>
                      ))}
                    </div>
                  )}
                  {m.ctas?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5" data-testid={`brain-widget-ctas-${i}`}>
                      {m.ctas.map((c, k) => (
                        <button key={k} onClick={() => onCta(c)} className="text-[11px] px-2.5 py-1 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-500/30">{c.label}</button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && <div className="text-[13px] text-slate-400 flex items-center gap-2"><CircleNotch size={14} className="animate-spin" /> Thinking…</div>}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={(e) => { e.preventDefault(); ask(q); }} className="p-3 border-t border-white/10 flex items-center gap-2">
            <input data-testid="brain-widget-input" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Ask the Brain…" className="flex-1 bg-white/5 rounded-xl px-3 py-2 text-[13px] outline-none text-white placeholder:text-slate-500 border border-white/10 focus:border-cyan-400/40" />
            <button data-testid="brain-widget-send" type="submit" disabled={loading} className="btn-primary !py-2 !px-3 text-xs disabled:opacity-50"><PaperPlaneTilt size={14} weight="bold" /></button>
          </form>
        </div>
      )}
    </>
  );
}
