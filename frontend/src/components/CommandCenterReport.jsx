import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";

const fmt = (v, cur) => {
  if (v == null || isNaN(v)) return "—";
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(v); }
  catch (_) { return `${Number(v).toLocaleString()} ${cur}`; }
};

const scoreColor = (c) => (c === "emerald" ? "#059669" : c === "amber" ? "#d97706" : "#e11d48");

// Minimal markdown → plain blocks for print
function MD({ text }) {
  const lines = (text || "").split("\n");
  return (
    <div>
      {lines.map((l, i) => {
        const t = l.trim();
        if (!t || t === "---") return null;
        if (t.startsWith("### ")) return <h4 key={i} style={{ margin: "8px 0 2px", fontSize: 13 }}>{t.slice(4)}</h4>;
        if (t.startsWith("## ")) return <h3 key={i} style={{ margin: "10px 0 3px", fontSize: 15 }}>{t.slice(3)}</h3>;
        if (t.startsWith("- ") || t.startsWith("* ")) return <li key={i} style={{ fontSize: 12, marginLeft: 16 }}>{t.replace(/^[-*]\s/, "").replace(/\*\*/g, "")}</li>;
        return <p key={i} style={{ fontSize: 12, margin: "3px 0" }}>{t.replace(/\*\*/g, "")}</p>;
      })}
    </div>
  );
}

export default function CommandCenterReport({ project, compliance, session }) {
  const p = project || {};
  const q = p.lastQuote || {};
  const tc = (q.currency || {}).transaction || p.transactionCurrency || "USD";
  const dest = q.destination || {};
  const today = new Date().toLocaleDateString();
  const th = { textAlign: "left", fontSize: 10, textTransform: "uppercase", letterSpacing: 1, color: "#64748b", borderBottom: "1px solid #cbd5e1", padding: "4px 6px" };
  const td = { fontSize: 12, padding: "4px 6px", borderBottom: "1px solid #eef2f7" };

  // Volume 2: fetch decision (scores + recommended actions) and scenario comparison for the PDF.
  const [vol2, setVol2] = useState({ scores: null, decision: null, compare: null });
  useEffect(() => {
    if (!p.id) return;
    const cfg = session ? { headers: { "X-Trade-Session": session } } : {};
    (async () => {
      try {
        const [dec, cmp] = await Promise.all([
          api.post("/decision", { projectId: p.id }, cfg).then((r) => r.data).catch(() => null),
          api.post("/simulation/compare", { projectId: p.id }, cfg).then((r) => r.data).catch(() => null),
        ]);
        setVol2({ scores: dec?.scores || null, decision: dec?.decision || null, compare: (cmp?.rows?.length ? cmp : null) });
      } catch (_) {}
    })();
  }, [p.id, session]);

  const scores = vol2.scores;
  const decision = vol2.decision;
  const reportId = `LN-TCC-${(p.id || "0000").slice(0, 6).toUpperCase()}-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}`;
  const qrData = encodeURIComponent(`LeadNation Trade Report ${reportId} | ${q.exporter?.name || ""}->${q.importer?.name || ""} | HS ${q.hsCode || p.hs || ""}`);
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=90x90&data=${qrData}`;

  return (
    <div id="cc-doc-print" style={{ display: "none" }}>
      <div style={{ fontFamily: "Arial, sans-serif", color: "#0A2540", padding: 8 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderBottom: "3px solid #00C2FF", paddingBottom: 8 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800 }}>LeadNation Trade Command Center™</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Trade Intelligence Report</div>
          </div>
          <div style={{ textAlign: "right", fontSize: 11, color: "#64748b", display: "flex", gap: 10, alignItems: "flex-end" }}>
            <div>
              <div>{today}</div>
              <div>HS {q.hsCode || p.hs} · {q.exporter?.name || ""} → {q.importer?.name || ""}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9 }}>{reportId}</div>
            </div>
            <img src={qrUrl} alt="QR" width={54} height={54} style={{ border: "1px solid #e2e8f0", borderRadius: 6 }} />
          </div>
        </div>

        <h2 style={{ fontSize: 16, marginTop: 12 }}>{p.title || "Trade Project"}</h2>
        <div style={{ fontSize: 12, color: "#475569" }}>{q.description || p.product} · {q.quantity || p.quantity} {q.unit || p.unit} · Incoterm {p.incoterm}</div>

        {/* KPI summary */}
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          {[["FOB value", q.fob?.total], ["CIF value", q.cif?.total], [`Landed (${q.importer?.name || ""})`, dest.landed], [`Selling (${q.pricing?.marginPct || 0}% margin)`, q.pricing?.selling]].map(([l, v], i) => (
            <div key={i} style={{ flex: 1, border: "1px solid #cbd5e1", borderRadius: 8, padding: 8 }}>
              <div style={{ fontSize: 9, textTransform: "uppercase", color: "#64748b" }}>{l}</div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>{fmt(v, tc)}</div>
            </div>
          ))}
        </div>

        {/* Waterfall */}
        {q.waterfall && (
          <>
            <h3 style={{ fontSize: 14, marginTop: 14 }}>Cost Waterfall (Ex-Works → CIF)</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th style={th}>Cost stage</th><th style={{ ...th, textAlign: "right" }}>Per {q.unit}</th><th style={{ ...th, textAlign: "right" }}>Total ({tc})</th></tr></thead>
              <tbody>{q.waterfall.map((w, i) => (
                <tr key={i} style={w.milestone ? { fontWeight: 700, background: "#f1f5f9" } : {}}>
                  <td style={td}>{w.stage}</td><td style={{ ...td, textAlign: "right" }}>{fmt(w.perUnit, tc)}</td><td style={{ ...td, textAlign: "right" }}>{fmt(w.total, tc)}</td>
                </tr>))}</tbody>
            </table>
          </>
        )}

        {/* Buyer comparison */}
        {q.comparison && (
          <>
            <h3 style={{ fontSize: 14, marginTop: 14 }}>Best Markets — Buyer Landed Cost</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th style={th}>Destination</th><th style={{ ...th, textAlign: "right" }}>Your CIF</th><th style={{ ...th, textAlign: "right" }}>Buyer duty</th><th style={{ ...th, textAlign: "right" }}>Buyer VAT</th><th style={{ ...th, textAlign: "right" }}>Buyer total</th></tr></thead>
              <tbody>{q.comparison.map((c, i) => (
                <tr key={i} style={i === 0 ? { fontWeight: 700, background: "#ecfdf5" } : {}}>
                  <td style={td}>{i === 0 ? "★ " : ""}{c.country}</td><td style={{ ...td, textAlign: "right" }}>{fmt(c.cif, tc)}</td>
                  <td style={{ ...td, textAlign: "right" }}>{c.dutyRate != null ? `${fmt(c.duty, tc)} (${c.dutyRate}%)` : "—"}</td>
                  <td style={{ ...td, textAlign: "right" }}>{fmt(c.vat, tc)} ({c.vatRate}%)</td><td style={{ ...td, textAlign: "right" }}>{fmt(c.buyerTotal, tc)}</td>
                </tr>))}</tbody>
            </table>
          </>
        )}

        {/* Compliance report (per destination country) */}
        {compliance?.ok && (
          <div style={{ marginTop: 16, pageBreakInside: "avoid" }}>
            <h3 style={{ fontSize: 14, borderTop: "2px solid #00C2FF", paddingTop: 8 }}>Compliance Report — {compliance.importer?.name}</h3>
            {compliance.duty?.importDuty && <p style={{ fontSize: 12 }}>Import duty: <b>{compliance.duty.importDuty.rate}% {compliance.duty.importDuty.type}</b> ({compliance.duty.importDuty.year}). {compliance.duty.preferential ? `Preferential available: ${compliance.duty.preferential.rate}%.` : ""}</p>}
            <h4 style={{ fontSize: 12, marginTop: 8 }}>Required documents</h4>
            <div style={{ fontSize: 12 }}>{(compliance.documents || []).join(" · ")}</div>
            {compliance.narrative && <div style={{ marginTop: 8 }}><MD text={compliance.narrative} /></div>}
          </div>
        )}

        {/* ============ VOLUME 2 — Simulation & Decision ============ */}
        {scores && (
          <div style={{ marginTop: 16, pageBreakInside: "avoid" }}>
            <h3 style={{ fontSize: 14, borderTop: "2px solid #00C2FF", paddingTop: 8 }}>Trade Scores</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {["overall", "profitability", "risk", "compliance", "competition", "market", "buyer", "supplier"].map((k) => scores[k] && (
                <div key={k} style={{ flex: "1 1 22%", minWidth: 110, border: "1px solid #cbd5e1", borderRadius: 8, padding: 6 }}>
                  <div style={{ fontSize: 9, textTransform: "uppercase", color: "#64748b" }}>{scores[k].label}</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: scoreColor(scores[k].color) }}>{scores[k].value}<span style={{ fontSize: 10, color: "#94a3b8" }}>/100</span></div>
                </div>
              ))}
            </div>
          </div>
        )}

        {vol2.compare?.rows?.length > 1 && (
          <div style={{ marginTop: 14, pageBreakInside: "avoid" }}>
            <h3 style={{ fontSize: 14 }}>Scenario Comparison</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th style={th}>Scenario</th><th style={{ ...th, textAlign: "right" }}>CIF</th><th style={{ ...th, textAlign: "right" }}>Landed</th><th style={{ ...th, textAlign: "right" }}>Selling</th><th style={{ ...th, textAlign: "right" }}>Profit</th><th style={{ ...th, textAlign: "right" }}>Score</th></tr></thead>
              <tbody>{vol2.compare.rows.map((r, i) => {
                const win = vol2.compare.winners?.overall === r.id;
                return (
                  <tr key={i} style={win ? { fontWeight: 700, background: "#ecfdf5" } : {}}>
                    <td style={td}>{win ? "★ " : ""}{r.label}</td>
                    <td style={{ ...td, textAlign: "right" }}>{fmt(r.summary?.cif, tc)}</td>
                    <td style={{ ...td, textAlign: "right" }}>{fmt(r.summary?.landed, tc)}</td>
                    <td style={{ ...td, textAlign: "right" }}>{fmt(r.summary?.selling, tc)}</td>
                    <td style={{ ...td, textAlign: "right" }}>{fmt(r.summary?.profit, tc)}</td>
                    <td style={{ ...td, textAlign: "right" }}>{r.overall}/100</td>
                  </tr>);
              })}</tbody>
            </table>
          </div>
        )}

        {decision?.recommendedActions?.length > 0 && (
          <div style={{ marginTop: 14, pageBreakInside: "avoid" }}>
            <h3 style={{ fontSize: 14 }}>Decision Engine — Recommendations & Action Plan</h3>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 4 }}>Overall verdict: <b style={{ color: scoreColor(decision.overallScore >= 70 ? "emerald" : decision.overallScore >= 45 ? "amber" : "rose") }}>{(decision.overallVerdict || "").toUpperCase()}</b> · confidence {Math.round((decision.confidence || 0) * 100)}%</div>
            <ol style={{ margin: 0, paddingLeft: 18 }}>
              {decision.recommendedActions.map((a, i) => (
                <li key={i} style={{ fontSize: 12, marginBottom: 3 }}><b>[{a.priority}] {a.title}</b> — {a.detail}</li>
              ))}
            </ol>
          </div>
        )}

        {/* Sources / disclaimer */}
        <div style={{ marginTop: 18, fontSize: 9, color: "#94a3b8", borderTop: "1px solid #e2e8f0", paddingTop: 6 }}>
          Report ID {reportId} · Generated {today}. Sources: {(q.sources || []).join(" · ")}. Deterministic engines compute all figures; the LeadNation Brain interprets — it never fabricates numbers. Figures are indicative for planning; verify duty, tax and freight at the time of shipment.
          Generated by LeadNation Trade Command Center · leadnation.app
        </div>
      </div>
    </div>
  );
}
