import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Brain, ArrowRight, Users, BookOpen, Lightning, Sparkle, CircleNotch, Crown, Buildings, CalendarBlank, GraduationCap } from "@phosphor-icons/react";
import { api } from "@/lib/api";
import { trackEvent as track } from "@/lib/analytics";

const ICON = { buyers: Users, guide: BookOpen, brain: Brain, workspace: Lightning, learn: GraduationCap, service: Buildings, expo: CalendarBlank, tool: Sparkle };

/** Vametra Brain "Next Steps" — an AI read of the user's own numbers + pre-filled links to the logical next tool.
 *  Deterministic links render immediately; the AI sentence streams in when ready. */
export const BrainNextSteps = ({ tool, inputs, result, testIdPrefix = "brain-next" }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const key = JSON.stringify([tool, inputs, result?.hsCode, result?.score, result?.year, result?.total]);
  const latest = useRef({ inputs, result });
  latest.current = { inputs, result };

  useEffect(() => {
    if (!result) return;
    let dead = false;
    const body = { tool, inputs: latest.current.inputs, result: latest.current.result };
    setLoading(true);
    api.post("/tools/next-steps", { ...body, ai: false })
      .then(({ data }) => { if (!dead) setData((d) => (d?.aiGenerated ? d : data)); })
      .catch(() => {});
    api.post("/tools/next-steps", { ...body, ai: true }, { timeout: 30000 })
      .then(({ data }) => { if (!dead) setData(data); })
      .catch(() => {})
      .finally(() => { if (!dead) setLoading(false); });
    return () => { dead = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  if (!result || !data) return null;
  return (
    <div data-testid={`${testIdPrefix}-panel`} className="glass-strong rounded-3xl p-6 sm:p-7 border border-cyan-400/20 relative overflow-hidden">
      <div className="absolute -top-24 -right-24 w-56 h-56 rounded-full bg-cyan-500/10 blur-3xl" />
      <div className="relative">
        <div className="flex items-center gap-2 flex-wrap">
          <Brain size={20} weight="duotone" className="text-cyan-300" />
          <span className="font-display font-bold text-lg">Vametra AI Brain · what this means for you</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/20">
            {loading ? "analysing…" : data.aiGenerated ? "AI read" : "instant read"}
          </span>
        </div>
        <p data-testid={`${testIdPrefix}-insight`} className="mt-3 text-sm sm:text-base text-slate-200 leading-relaxed max-w-3xl">
          {loading && !data.aiGenerated && <CircleNotch size={14} className="animate-spin inline mr-2 text-cyan-300" />}
          {data.insight}
        </p>

        <div className="mt-5 text-[11px] font-mono-display tracking-[0.25em] uppercase text-cyan-300">Recommended next steps</div>
        <div className="mt-3 grid sm:grid-cols-2 gap-3">
          {data.nextSteps.map((s, i) => {
            const I = ICON[s.kind] || Sparkle;
            return (
              <Link key={i} to={s.to} data-testid={`${testIdPrefix}-step-${i}`}
                onClick={() => track("tool_next_step", { tool, step: s.kind, location: s.to })}
                className="group glass rounded-2xl p-4 flex items-start gap-3 hover:border-cyan-400/40 hover:-translate-y-0.5 transition-all">
                <div className="w-9 h-9 shrink-0 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
                  <I size={18} weight="duotone" className="text-cyan-300" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm text-white flex items-center gap-1.5">
                    <span className="text-cyan-300 font-mono-display text-[10px]">{String(i + 1).padStart(2, "0")}</span>{s.label}
                    <ArrowRight size={13} weight="bold" className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all text-cyan-300" />
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{s.why}</div>
                </div>
              </Link>
            );
          })}
        </div>

        {data.upgrade && (
          <Link to={data.upgrade.to} data-testid={`${testIdPrefix}-upgrade`}
            onClick={() => track("upgrade_cta_click", { tool, location: "brain-next-steps" })}
            className="mt-4 flex items-center gap-3 rounded-2xl px-4 py-3 bg-gradient-to-r from-violet-500/15 to-cyan-500/15 border border-violet-400/20 hover:border-violet-400/40 transition-colors">
            <Crown size={18} weight="duotone" className="text-violet-300" />
            <span className="text-sm text-slate-200 flex-1">{data.upgrade.label}</span>
            <span className="text-xs font-semibold text-violet-200">See plans <ArrowRight size={12} weight="bold" className="inline" /></span>
          </Link>
        )}
      </div>
    </div>
  );
};
