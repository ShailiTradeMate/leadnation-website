import React from "react";

/**
 * Visible answer-first content blocks. The same copy is passed to SEO `faqs`
 * so the rendered page and the FAQPage JSON-LD never disagree.
 */
export function AnswerBlock({ label, title, children, testId }) {
  return (
    <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-14" data-testid={testId}>
      <div className="max-w-3xl">
        {label && (
          <div className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">{label}</div>
        )}
        <h2 className="font-display font-bold text-base md:text-lg mt-3">{title}</h2>
        <div className="mt-4 space-y-4 text-[15px] text-slate-300 leading-relaxed">{children}</div>
      </div>
    </section>
  );
}

export function PageFaq({ items = [], heading = "Frequently asked questions", testIdPrefix = "faq" }) {
  if (!items.length) return null;
  return (
    <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-14" data-testid={`${testIdPrefix}-section`}>
      <h2 className="font-display font-bold text-base md:text-lg">{heading}</h2>
      <div className="mt-5 grid md:grid-cols-2 gap-4">
        {items.map((f, i) => (
          <div key={i} data-testid={`${testIdPrefix}-${i}`} className="glass rounded-2xl p-6">
            <h3 className="font-display font-bold text-sm">{f.q}</h3>
            <p className="mt-2.5 text-sm text-slate-400 leading-relaxed">{f.a}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
