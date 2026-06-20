import React from "react";

export function SectionLabel({ children, testId }) {
  return (
    <div
      data-testid={testId}
      className="inline-flex items-center gap-2 text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300"
    >
      <span className="block w-6 h-px bg-cyan-400/60" />
      {children}
    </div>
  );
}

export function PageHero({ label, title, sub, children, testIdPrefix = "page" }) {
  return (
    <section className="relative pt-20 pb-12 sm:pt-28 sm:pb-16">
      <div className="aurora" />
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
        <SectionLabel testId={`${testIdPrefix}-label`}>{label}</SectionLabel>
        <h1
          data-testid={`${testIdPrefix}-title`}
          className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-5 leading-[1.04] max-w-4xl"
        >
          {title}
        </h1>
        {sub && (
          <p
            data-testid={`${testIdPrefix}-sub`}
            className="mt-5 text-slate-300 max-w-2xl text-base sm:text-lg leading-relaxed"
          >
            {sub}
          </p>
        )}
        {children && <div className="mt-8">{children}</div>}
      </div>
    </section>
  );
}
