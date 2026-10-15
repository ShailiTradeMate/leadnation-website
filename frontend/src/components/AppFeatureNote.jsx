import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { Sparkle, ArrowRight } from "@phosphor-icons/react";

/**
 * Placeholder for a module that is not live yet. It must not imply a native app
 * exists — Vametra AI is a browser platform.
 */
export default function AppFeatureNote({ feature = "This feature", icon: Icon = Sparkle, points = [] }) {
  const navigate = useNavigate();
  return (
    <section className="max-w-3xl mx-auto px-6 pt-36 pb-24 text-center">
      <div className="w-20 h-20 mx-auto rounded-3xl grid place-items-center bg-gradient-to-br from-cyan-500/25 to-violet-500/25 border border-white/10">
        <Icon size={40} weight="duotone" className="text-cyan-300" />
      </div>
      <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-6">{feature} is in development</h1>
      <p className="mt-4 text-base text-slate-300">
        {feature} is being built into the Vametra AI platform. It is not live yet, so rather than
        show you a half-working screen we would rather say so plainly — everything else on the
        platform is fully available in your browser right now.
      </p>
      {points.length > 0 && (
        <ul className="mt-6 inline-flex flex-col gap-2 text-left text-sm text-slate-300">
          {points.map((p, i) => <li key={i} className="flex items-center gap-2"><ArrowRight size={14} className="text-cyan-300" />{p}</li>)}
        </ul>
      )}
      <div className="mt-8 flex flex-wrap gap-3 justify-center">
        <button onClick={() => navigate("/brain")} className="btn-primary" data-testid="appnote-brain">
          Ask the Vametra AI Brain <ArrowRight size={18} weight="bold" />
        </button>
        <Link to="/buyers" className="btn-ghost" data-testid="appnote-buyers">Find verified buyers</Link>
        <Link to="/tools" className="btn-ghost" data-testid="appnote-tools">Browse free tools</Link>
      </div>
    </section>
  );
}
