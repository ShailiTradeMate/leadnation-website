import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "@phosphor-icons/react";
import { api } from "@/lib/api";

// Production-verified fallbacks so no page ever renders a raw {token} before /api/seo/facts answers.
const DEFAULTS = {
  asOf: new Date().toLocaleString("en-US", { month: "long", year: "numeric" }),
  hsCodes: 5606, tariffCountries: 56, buyerRecords: 30821, buyerCountries: 32, buyerSectors: 21,
  guides: 392, products: 8, regions: 5,
};
let factsPromise;
const loadFacts = () => (factsPromise ||= api.get("/seo/facts").then((r) => ({ ...DEFAULTS, ...r.data })).catch(() => DEFAULTS));

export function useFacts() {
  const [facts, setFacts] = useState(DEFAULTS);
  useEffect(() => { loadFacts().then(setFacts); }, []);
  return facts;
}

const num = (v) => (typeof v === "number" ? v.toLocaleString("en-US") : v);
export const fill = (text, facts) =>
  typeof text === "string" ? text.replace(/\{(\w+)\}/g, (_, k) => (facts[k] != null ? num(facts[k]) : _)) : text;
export const fillFaqs = (faqs, facts) => faqs.map((f) => ({ q: fill(f.q, facts), a: fill(f.a, facts) }));

/**
 * Answer-first block: a direct 40-60 word answer, one dated data table with its source,
 * and the internal links that make the page part of the graph instead of a dead end.
 * `{token}` placeholders in any string are replaced with live figures from /api/seo/facts.
 */
export function AnswerFirst({ testId = "answer-first", eyebrow = "Direct answer", answer, rows = [], source, links = [], className = "" }) {
  const facts = useFacts();
  return (
    <section data-testid={testId} className={`max-w-7xl mx-auto px-6 sm:px-10 mt-10 ${className}`}>
      <div className="grid lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 glass-strong rounded-3xl p-6 sm:p-8">
          <div className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">{eyebrow}</div>
          <p data-testid={`${testId}-answer`} className="mt-3 text-base sm:text-lg text-slate-100 leading-relaxed">{fill(answer, facts)}</p>
          {links.length > 0 && (
            <div className="mt-5 flex flex-wrap gap-2" data-testid={`${testId}-links`}>
              {links.map((l) => (
                <Link key={l.to} to={l.to} data-testid={`${testId}-link-${l.to.replace(/\W+/g, "-").replace(/^-|-$/g, "")}`}
                  className="inline-flex items-center gap-1.5 text-[12px] glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">
                  {l.label} <ArrowRight size={11} />
                </Link>
              ))}
            </div>
          )}
        </div>
        {rows.length > 0 && (
          <div className="lg:col-span-2 glass rounded-3xl p-6" data-testid={`${testId}-data`}>
            <table className="w-full text-sm">
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-white/5 last:border-0">
                    <td className="py-2 pr-3 text-slate-400">{fill(r.label, facts)}</td>
                    <td className="py-2 text-right font-semibold text-slate-100 tabular-nums">{fill(r.value, facts)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 text-[11px] text-slate-500 leading-relaxed" data-testid={`${testId}-source`}>
              As of {facts.asOf}{source ? ` · Source: ${fill(source, facts)}` : ""}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
