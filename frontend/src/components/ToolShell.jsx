import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "@phosphor-icons/react";

export function Crumbs({ items }) {
  return (
    <nav className="text-xs font-mono-display tracking-widest uppercase text-slate-400 flex flex-wrap items-center gap-2">
      {items.map((it, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="text-slate-600">·</span>}
          {it.to ? (
            <Link to={it.to} className="hover:text-cyan-300">{it.label}</Link>
          ) : (
            <span className="text-slate-200">{it.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

export function ToolShell({ label, title, sub, children, testIdPrefix = "tool" }) {
  return (
    <section className="relative pt-20 pb-12 sm:pt-24 sm:pb-12">
      <div className="aurora" />
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
        <Crumbs items={[{ to: "/tools", label: "Tools" }, { label }]} />
        <h1
          data-testid={`${testIdPrefix}-title`}
          className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-5 leading-[1.05] max-w-4xl"
        >
          {title}
        </h1>
        {sub && (
          <p className="mt-5 text-slate-300 max-w-2xl text-base sm:text-lg leading-relaxed">{sub}</p>
        )}
        <div className="mt-10">{children}</div>
      </div>
    </section>
  );
}

export function CTARow({ testIdPrefix = "cta" }) {
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      <Link to="/contact" data-testid={`${testIdPrefix}-create`} className="btn-primary">
        Create free account <ArrowRight size={14} weight="bold" />
      </Link>
      <a href="/#download" data-testid={`${testIdPrefix}-download`} className="btn-ghost">Download app</a>
      <a
        href="https://wa.me/918237161088"
        target="_blank" rel="noopener noreferrer"
        data-testid={`${testIdPrefix}-whatsapp`}
        className="btn-ghost"
      >Chat on WhatsApp</a>
    </div>
  );
}

export function Card({ title, Icon, children, className = "" }) {
  return (
    <div className={`glass rounded-3xl p-6 ${className}`}>
      <div className="flex items-center gap-2">
        {Icon && <Icon size={18} className="text-cyan-300" weight="duotone" />}
        <div className="font-display font-bold">{title}</div>
      </div>
      {children}
    </div>
  );
}

export function ChipList({ items, testIdPrefix = "chip", variant = "cyan" }) {
  const color = variant === "violet" ? "bg-violet-500/10 border-violet-400/20" : "bg-cyan-500/10 border-cyan-400/20";
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((m, i) => (
        <span key={m + i} data-testid={`${testIdPrefix}-${i}`} className={`px-3 py-1.5 rounded-full text-sm border ${color} text-white`}>{m}</span>
      ))}
    </div>
  );
}
