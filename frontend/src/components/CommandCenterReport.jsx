import React from "react";

const fmt = (v, cur) => {
  if (v == null || isNaN(v)) return "—";
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur, maximumFractionDigits: 2 }).format(v); }
  catch (_) { return `${Number(v).toLocaleString()} ${cur}`; }
};

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

export default function CommandCenterReport({ project, compliance }) {
  const p = project || {};
  const q = p.lastQuote || {};
  const tc = (q.currency || {}).transaction || p.transactionCurrency || "USD";
  const dest = q.destination || {};
  const today = new Date().toLocaleDateString();
  const th = { textAlign: "left", fontSize: 10, textTransform: "uppercase", letterSpacing: 1, color: "#64748b", borderBottom: "1px solid #cbd5e1", padding: "4px 6px" };
  const td = { fontSize: 12, padding: "4px 6px", borderBottom: "1px solid #eef2f7" };

  return (
    <div id="cc-doc-print" style={{ display: "none" }}>
      <div style={{ fontFamily: "Arial, sans-serif", color: "#0A2540", padding: 8 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderBottom: "3px solid #00C2FF", paddingBottom: 8 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800 }}>LeadNation Trade Command Center™</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Trade Project Quote & Compliance Report</div>
          </div>
          <div style={{ textAlign: "right", fontSize: 11, color: "#64748b" }}>
            <div>{today}</div>
            <div>HS {q.hsCode || p.hs} · {q.exporter?.name || ""} → {q.importer?.name || ""}</div>
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

        {/* Sources / disclaimer */}
        <div style={{ marginTop: 18, fontSize: 9, color: "#94a3b8", borderTop: "1px solid #e2e8f0", paddingTop: 6 }}>
          Sources: {(q.sources || []).join(" · ")}. Figures are indicative for planning; verify duty, tax and freight at the time of shipment.
          Generated by LeadNation Trade Command Center · leadnation.app
        </div>
      </div>
    </div>
  );
}
