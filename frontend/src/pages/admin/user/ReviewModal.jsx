import React, { useState } from "react";
import { Modal, Banner, Field, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { CheckCircle, XCircle, PencilSimple } from "@phosphor-icons/react";

const CORRECTION_FIELDS = [
  "Mobile / contact number", "Company name", "Company email", "Company contact number",
  "Country or state", "Document is unclear / unreadable", "Document does not match company name",
  "Selfie photo quality",
];

export default function ReviewModal({ u, isMain, onClose, onDone }) {
  const [decision, setDecision] = useState("approve");
  const [note, setNote] = useState("");
  const [fields, setFields] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const toggle = (f) => setFields((p) => ({ ...p, [f]: !p[f] }));

  const submit = async () => {
    setBusy(true); setErr(""); setOk("");
    try {
      const res = await adminOps.review(u.uid, {
        decision, note: note || null,
        fields: decision === "correction" ? Object.keys(fields).filter((f) => fields[f]) : null,
      });
      setOk(res.message || (res.stage === "awaiting_signoff"
        ? "Sent to the main admin for final sign-off."
        : `Done — buyer marked ${res.status || decision} and notified by email.`));
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Could not save the review.")); }
    finally { setBusy(false); }
  };

  const OPTS = [
    { k: "approve", l: isMain ? "Approve" : "Recommend approval", I: CheckCircle, c: "emerald" },
    { k: "reject", l: isMain ? "Reject" : "Recommend rejection", I: XCircle, c: "rose" },
    { k: "correction", l: "Request correction", I: PencilSimple, c: "amber" },
  ];

  return (
    <Modal testid="review-modal" kicker="Verification review" onClose={onClose}
      title={`${u.name || u.email || "Buyer"} · ${u.customer_id || "—"}`}>
      <Banner testid="review-error">{err}</Banner>
      <Banner kind="ok" testid="review-ok">{ok}</Banner>

      {!isMain && (
        <p className="text-xs text-amber-200 bg-amber-500/10 rounded-xl p-3 mb-4" data-testid="review-twotier-note">
          Your approve / reject goes to the main admin as a recommendation. The buyer is only
          notified after the main admin signs off.
        </p>
      )}

      <div className="grid sm:grid-cols-3 gap-2">
        {OPTS.map(({ k, l, I }) => (
          <button key={k} type="button" data-testid={`review-opt-${k}`} onClick={() => setDecision(k)}
            className={`px-3 py-3 rounded-xl border text-xs flex items-center gap-2 justify-center ${decision === k ? "border-cyan-400/60 bg-cyan-400/10 text-white" : "border-white/10 bg-white/5 text-slate-300"}`}>
            <I size={15} /> {l}
          </button>
        ))}
      </div>

      {decision === "correction" && (
        <div className="mt-4">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">What must the buyer fix?</div>
          <div className="grid sm:grid-cols-2 gap-1.5">
            {CORRECTION_FIELDS.map((f) => (
              <button key={f} type="button" data-testid={`review-field-${f.slice(0, 12).replace(/\W+/g, "-").toLowerCase()}`}
                onClick={() => toggle(f)}
                className={`text-left text-xs px-3 py-2 rounded-lg border ${fields[f] ? "border-cyan-400/50 bg-cyan-400/10" : "border-white/10 bg-white/5 text-slate-300"}`}>
                {f}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4">
        <Field label={decision === "reject" ? "Reason (sent to the buyer)" : "Note"}>
          <textarea data-testid="review-note" rows={3} value={note} onChange={(e) => setNote(e.target.value)}
            className={input} placeholder={decision === "approve" ? "Optional note for the buyer" : "Explain clearly — this is emailed to the buyer"} />
        </Field>
      </div>

      <button data-testid="review-submit" onClick={submit} disabled={busy}
        className="btn-primary mt-5 w-full justify-center disabled:opacity-50">
        {busy ? "Saving…" : isMain ? "Confirm & notify buyer" : "Send to main admin"}
      </button>
    </Modal>
  );
}
