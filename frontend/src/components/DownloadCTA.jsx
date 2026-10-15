import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, Lightning, Brain, Calculator } from "@phosphor-icons/react";
import { trackEvent } from "@/lib/analytics";

/**
 * Web product CTA. Deliberately makes no claim about a native mobile app —
 * Vametra AI is a browser platform and the marketing must say only that.
 * Export name and props are unchanged so all existing pages keep working.
 */
export default function DownloadCTA({ compact = false, id }) {
  const navigate = useNavigate();
  return (
    <section id={id} className="relative" data-testid="platform-cta">
      <div className={`relative overflow-hidden rounded-3xl glass-strong ${compact ? "p-8 sm:p-10" : "p-10 sm:p-14"}`}>
        <div aria-hidden="true" className="pointer-events-none absolute top-0 right-0 w-[min(420px,100%)] h-full bg-cyan-500/10 blur-3xl" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-32 -left-32 w-[420px] h-[420px] rounded-full bg-violet-500/20 blur-3xl" />
        <div className="relative grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">
              Explore Vametra AI
            </div>
            <h3 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight mt-3 leading-[1.05]">
              Your global trade<br />
              <span className="gradient-text">command center.</span>
            </h3>
            <p className="mt-5 text-slate-300 max-w-md">
              Check real import duty by HS code, build the full FOB → CIF → landed-cost
              waterfall, size real import demand by market and reach verified buyers across 32
              countries — all in your browser, nothing to install.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                onClick={() => { trackEvent("explore_platform_click", { location: "cta_section" }); navigate("/command-center"); }}
                data-testid={`cta-command-center${compact ? "-compact" : ""}`}
                className="btn-primary"
              >
                Open Trade Command Center <ArrowRight size={18} weight="bold" />
              </button>
              <Link
                to="/tools"
                onClick={() => trackEvent("explore_tools_click", { location: "cta_section" })}
                data-testid={`cta-free-tools${compact ? "-compact" : ""}`}
                className="btn-ghost"
              >
                Free trade tools
              </Link>
              <Link
                to="/signup"
                onClick={() => trackEvent("create_account_click", { location: "cta_section" })}
                data-testid={`cta-create-account${compact ? "-compact" : ""}`}
                className="btn-ghost"
              >
                Create free account
              </Link>
            </div>
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-[12px] text-slate-400">
              <span className="inline-flex items-center gap-1.5"><Calculator size={14} weight="duotone" className="text-cyan-300" /> Live WITS duty data</span>
              <span className="inline-flex items-center gap-1.5"><Brain size={14} weight="duotone" className="text-violet-300" /> Vametra AI Brain</span>
              <span className="inline-flex items-center gap-1.5"><Lightning size={14} weight="duotone" className="text-cyan-300" /> No signup for the free tools</span>
            </div>
          </div>

          <div className="relative h-[280px] lg:h-[360px]">
            <BrowserMock />
          </div>
        </div>
      </div>
    </section>
  );
}

function BrowserMock() {
  return (
    <div className="absolute inset-0 grid place-items-center">
      <div className="relative w-full max-w-[420px] rounded-2xl bg-gradient-to-b from-[#0d1330] to-[#050816] border border-white/10 shadow-2xl overflow-hidden floaty">
        <div className="flex items-center gap-1.5 px-3 py-2.5 border-b border-white/5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-400/60" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400/60" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/60" />
          <div className="ml-2 flex-1 h-5 rounded-md bg-white/5 grid place-items-center">
            <span className="text-[9px] font-mono-display tracking-widest text-slate-400">vametra.com</span>
          </div>
        </div>
        <div className="p-4">
          <div className="text-[9px] font-brand tracking-[0.3em] text-cyan-300">VAMETRA AI</div>
          <div className="mt-1.5 text-sm font-display font-bold leading-tight">Duty &amp; landed cost, any lane</div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {[
              { k: "HS CODE", v: "091030" },
              { k: "DUTY", v: "0%" },
              { k: "DEMAND", v: "$8.4M" },
            ].map((s) => (
              <div key={s.k} className="glass rounded-lg px-2 py-2">
                <div className="text-[7px] font-mono-display tracking-widest text-slate-400">{s.k}</div>
                <div className="text-[11px] font-semibold mt-0.5">{s.v}</div>
              </div>
            ))}
          </div>
          <div className="mt-2.5 space-y-1.5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass rounded-lg px-2 py-1.5">
                <div className="h-1.5 w-16 bg-cyan-400/60 rounded-full" />
                <div className="h-1 w-24 bg-white/20 rounded-full mt-1" />
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="hidden sm:block absolute -left-1 top-6 glass rounded-xl p-2 text-[10px] floaty" style={{ animationDelay: "1.5s" }}>
        <div className="text-cyan-300 font-mono-display tracking-widest">DUTY</div>
        <div className="font-semibold">0% · CEPA</div>
      </div>
      <div className="hidden sm:block absolute -right-1 bottom-8 glass rounded-xl p-2 text-[10px] floaty" style={{ animationDelay: "3s" }}>
        <div className="text-violet-300 font-mono-display tracking-widest">EXPO</div>
        <div className="font-semibold">Gulfood ‘26</div>
      </div>
    </div>
  );
}
