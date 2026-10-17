import React, { useEffect, useState } from "react";
import { Brain } from "@phosphor-icons/react";

const STEPS = [
  "Resolving HS code and lane",
  "Reading live tariff schedules",
  "Measuring import demand",
  "Matching verified buyers",
  "Writing the report",
];

/** "The Brain is working" loader — pulsing neural core, firing synapses and live step read-out. */
export const BrainThinking = ({ testId = "brain-thinking", note = "Usually 10–30 seconds." }) => {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStep((s) => (s + 1 < STEPS.length ? s + 1 : s)), 4200);
    return () => clearInterval(t);
  }, []);

  return (
    <div data-testid={testId} className="glass-strong rounded-3xl p-8 sm:p-10 border border-cyan-400/15 overflow-hidden">
      <div className="flex flex-col items-center text-center">
        <div className="relative w-28 h-28 grid place-items-center">
          {[0, 1, 2].map((i) => (
            <span key={i} style={{ animationDelay: `${i * 0.85}s` }}
              className="brain-ring absolute inset-0 rounded-full border border-cyan-400/40" />
          ))}
          <span className="absolute inset-4 rounded-full bg-cyan-400/10 blur-xl" />
          {[
            "top-1 left-1/2", "bottom-2 left-4", "bottom-2 right-4", "top-6 right-1", "top-6 left-1",
          ].map((pos, i) => (
            <span key={pos} style={{ animationDelay: `${i * 0.28}s` }}
              className={`synapse absolute ${pos} w-1.5 h-1.5 rounded-full bg-cyan-300`} />
          ))}
          <Brain size={46} weight="duotone" className="brain-float relative text-cyan-300 drop-shadow-[0_0_14px_rgba(0,194,255,0.55)]" />
        </div>

        <div className="mt-5 text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">
          Vametra AI Brain · working
        </div>
        <div data-testid={`${testId}-step`} className="mt-2 text-sm text-slate-200 font-medium">
          {STEPS[step]}…
        </div>

        <div className="mt-5 w-full max-w-sm h-1 rounded-full bg-white/8 relative overflow-hidden">
          <div className="brain-bar h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-400" />
          <div className="brain-scan absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/40 to-transparent" />
        </div>

        <div className="mt-4 flex flex-wrap justify-center gap-1.5">
          {STEPS.map((s, i) => (
            <span key={s} className={`h-1.5 rounded-full transition-all duration-500 ${i <= step ? "w-7 bg-cyan-400/80" : "w-3 bg-white/15"}`} />
          ))}
        </div>

        <p className="mt-4 text-[12px] text-slate-400 max-w-md">
          Reading live tariff, demand and buyer data, then writing the report. {note}
        </p>
      </div>

      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-3" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="glass rounded-2xl p-4 relative overflow-hidden">
            <div className="h-2 w-20 rounded-full bg-white/10" />
            <div className="mt-3 h-4 w-28 rounded-full bg-white/8" />
            <div className="brain-scan absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-cyan-300/10 to-transparent"
              style={{ animationDelay: `${i * 0.22}s` }} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default BrainThinking;
