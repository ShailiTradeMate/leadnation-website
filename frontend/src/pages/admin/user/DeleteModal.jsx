import React, { useState } from "react";
import { Modal, Banner, Field, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { Warning } from "@phosphor-icons/react";

export default function DeleteModal({ u, onClose, onDone }) {
  const [confirm, setConfirm] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const remove = async () => {
    setBusy(true); setErr(""); setOk("");
    try {
      await adminOps.remove(u.uid, { confirm, note: note || null });
      setOk("Records archived and removed. The buyer has been notified.");
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Delete failed.")); }
    finally { setBusy(false); }
  };

  return (
    <Modal testid="delete-modal" kicker="Danger zone" onClose={onClose}
      title={`Delete records for ${u.name || u.email || "this buyer"}`}>
      <Banner testid="delete-error">{err}</Banner>
      <Banner kind="ok" testid="delete-ok">{ok}</Banner>
      <div className="text-sm text-rose-200 bg-rose-500/10 rounded-xl p-4 flex gap-3">
        <Warning size={20} className="shrink-0 mt-0.5" />
        <div>
          This permanently removes the verification application, profile overlay and contact notes.
          A full copy is archived for audit. The buyer's sign-in identity, Customer ID and GEID on the
          shared identity backend are <b>not</b> destroyed.
        </div>
      </div>
      <div className="mt-4 space-y-3">
        <Field label="Reason (sent to the buyer)">
          <input data-testid="delete-note" className={input} value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
        <Field label='Type DELETE to confirm'>
          <input data-testid="delete-confirm" className={input} value={confirm}
            onChange={(e) => setConfirm(e.target.value)} placeholder="DELETE" />
        </Field>
      </div>
      <button data-testid="delete-submit" onClick={remove} disabled={busy || confirm.trim().toUpperCase() !== "DELETE"}
        className="btn-primary mt-5 w-full justify-center !bg-rose-500/80 hover:!bg-rose-500 disabled:opacity-40">
        {busy ? "Deleting…" : "Permanently delete records"}
      </button>
    </Modal>
  );
}
