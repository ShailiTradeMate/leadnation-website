import React from "react";
import { X } from "@phosphor-icons/react";

export const Modal = ({ title, kicker, onClose, children, testid, wide }) => (
  <div className="fixed inset-0 z-[210] grid place-items-center p-4 bg-black/70 backdrop-blur-sm"
    data-testid={testid} onClick={onClose}>
    <div className={`glass-strong rounded-3xl w-full ${wide ? "max-w-3xl" : "max-w-xl"} max-h-[88vh] overflow-auto p-6 sm:p-7 relative`}
      onClick={(e) => e.stopPropagation()}>
      <button onClick={onClose} data-testid={`${testid}-close`}
        className="absolute right-5 top-5 text-slate-400 hover:text-white"><X size={18} /></button>
      {kicker && <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">{kicker}</div>}
      <h3 className="font-display font-extrabold text-xl mt-1 pr-8">{title}</h3>
      <div className="mt-5">{children}</div>
    </div>
  </div>
);

export const Banner = ({ kind = "error", children, testid }) => {
  if (!children) return null;
  const cls = kind === "error" ? "text-rose-300 bg-rose-500/10"
    : kind === "ok" ? "text-emerald-300 bg-emerald-500/10"
    : "text-amber-200 bg-amber-500/10";
  return <div data-testid={testid} className={`text-sm rounded-xl p-3 mb-4 ${cls}`}>{children}</div>;
};

export const Field = ({ label, children }) => (
  <label className="block">
    <span className="text-[10px] uppercase tracking-wider text-slate-500">{label}</span>
    <div className="mt-1">{children}</div>
  </label>
);

export const input = "glass rounded-xl px-3 py-2.5 text-sm outline-none w-full";
