import React, { useState } from "react";
import { Modal, Banner, Field, input } from "./Modal";
import { adminOps, errText } from "@/lib/adminOps";
import { Warning } from "@phosphor-icons/react";

export default function DeleteModal({ u, isMain, onClose, onDone }) {
  const [confirm, setConfirm] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const run = async () => {
    setBusy(true); setErr(""); setOk("");
    try {
      if (isMain) {
        const res = await adminOps.hardDelete(u.uid, { confirm, note: note || null });
        setOk(`Identity registry: ${res.identity?.do_registry}; sign-in account: ${res.identity?.firebase}. User records and file contents removed. Only a deletion audit remains.`);
        if (res.warnings?.length) setErr(`Partial removal — ${res.warnings.join("; ")}. Please retry or escalate.`);
      } else {
        const res = await adminOps.requestDelete(u.uid, { business_case: note });
        setOk(res.message || "Hard-delete request sent to the main admin for approval.");
      }
      onDone && onDone();
    } catch (e) { setErr(errText(e, "Action failed.")); }
    finally { setBusy(false); }
  };

  const ready = isMain ? confirm.trim().toUpperCase() === "DELETE" : note.trim().length >= 10;

  return (
    <Modal testid="delete-modal" kicker="Danger zone" onClose={onClose}
      title={isMain ? `Hard delete ${u.name || u.email || "this user"}`
        : `Request hard delete · ${u.name || u.email || "user"}`}>
      <Banner testid="delete-error">{err}</Banner>
      <Banner kind="ok" testid="delete-ok">{ok}</Banner>

      {isMain ? (
        <div className="text-sm text-rose-200 bg-rose-500/10 rounded-xl p-4 flex gap-3">
          <Warning size={20} className="shrink-0 mt-0.5" />
          <div>
            This erases the user from <b>every system in one action</b>: identity registry
            (Customer ID {u.customer_id || "—"}), shared profile, sign-in account, verification
            records, documents, contact notes, activity and subscriptions. They would have to
            register again from scratch. Only a minimal deletion audit is retained, not a copy of their personal data.
          </div>
        </div>
      ) : (
        <div className="text-sm text-amber-200 bg-amber-500/10 rounded-xl p-4">
          Sub-admins cannot delete users. Describe the business case and the main admin will
          approve or decline it. Nothing is deleted until then.
        </div>
      )}

      <div className="mt-4 space-y-3">
        <Field label={isMain ? "Reason (sent to the user)" : "Business case (min 10 characters)"}>
          <textarea data-testid="delete-note" rows={3} className={input} value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={isMain ? "Why is this account being removed?" : "Why must this user be deleted?"} />
        </Field>
        {isMain && (
          <Field label="Type DELETE to confirm">
            <input data-testid="delete-confirm" className={input} value={confirm}
              onChange={(e) => setConfirm(e.target.value)} placeholder="DELETE" />
          </Field>
        )}
      </div>

      <button data-testid="delete-submit" onClick={run} disabled={busy || !ready}
        className={`btn-primary mt-5 w-full justify-center disabled:opacity-40 ${isMain ? "!bg-rose-500/80 hover:!bg-rose-500" : ""}`}>
        {busy ? "Working…" : isMain ? "Permanently delete from everywhere" : "Send request to main admin"}
      </button>
    </Modal>
  );
}
