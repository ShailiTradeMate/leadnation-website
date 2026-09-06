import React, { useState } from "react";
import ReviewModal from "./ReviewModal";
import EditProfileModal from "./EditProfileModal";
import ContactModal from "./ContactModal";
import PaymentsModal from "./PaymentsModal";
import DocumentsModal from "./DocumentsModal";
import DeleteModal from "./DeleteModal";
import { adminOps } from "@/lib/adminOps";
import { Gavel, PencilSimple, Phone, CreditCard, FileArrowUp, Trash, DownloadSimple, TestTube } from "@phosphor-icons/react";

const Btn = ({ I, label, onClick, testid, danger, disabled }) => (
  <button data-testid={testid} onClick={onClick} disabled={disabled}
    className={`text-xs px-3 py-2 rounded-xl border flex items-center gap-1.5 transition-colors disabled:opacity-50 ${danger
      ? "border-rose-400/30 bg-rose-500/10 text-rose-200 hover:bg-rose-500/20"
      : "border-white/10 bg-white/5 text-slate-200 hover:border-cyan-400/40 hover:bg-cyan-400/10"}`}>
    <I size={13} /> {label}
  </button>
);

export default function ActionBar({ u, perms, isMain, onRefresh }) {
  const [modal, setModal] = useState("");
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const can = (p) => (perms || []).includes(p);
  const close = () => setModal("");
  const done = () => onRefresh && onRefresh();

  const download = async () => {
    setBusy("download"); setMsg("");
    try {
      const data = await adminOps.exportUser(u.uid);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `vametra-user-${u.customer_id || u.uid}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      setMsg("Complete record downloaded.");
    } catch (e) { setMsg("Could not download the record."); }
    finally { setBusy(""); }
  };

  const toggleTest = async () => {
    setBusy("test"); setMsg("");
    try {
      await adminOps.testFlag(u.uid, { is_test: !u.is_test_account, reason: "Marked from admin console" });
      setMsg(!u.is_test_account ? "Marked as a test account." : "Test flag removed.");
      done();
    } catch (e) { setMsg("Could not update the test flag."); }
    finally { setBusy(""); }
  };

  return (
    <div className="pt-1" data-testid={`user-actions-${u.uid}`}>
      <div className="flex flex-wrap gap-2">
        {can("users.review_recommend") && u.applied && (
          <Btn I={Gavel} label={isMain ? "Approve / Reject" : "Review & recommend"}
            testid={`action-review-${u.uid}`} onClick={() => setModal("review")} />
        )}
        {can("users.edit") && <Btn I={PencilSimple} label="Edit profile" testid={`action-edit-${u.uid}`} onClick={() => setModal("edit")} />}
        {can("users.contact") && <Btn I={Phone} label="Contact" testid={`action-contact-${u.uid}`} onClick={() => setModal("contact")} />}
        {can("payments.view") && <Btn I={CreditCard} label="Payment details" testid={`action-payments-${u.uid}`} onClick={() => setModal("payments")} />}
        {can("users.documents") && <Btn I={FileArrowUp} label="Documents" testid={`action-documents-${u.uid}`} onClick={() => setModal("documents")} />}
        <Btn I={DownloadSimple} label={busy === "download" ? "Preparing…" : "Download record"}
          testid={`action-download-${u.uid}`} onClick={download} disabled={busy === "download"} />
        {can("users.edit") && (
          <Btn I={TestTube} label={u.is_test_account ? "Unmark test account" : "Mark as test account"}
            testid={`action-test-flag-${u.uid}`} onClick={toggleTest} disabled={busy === "test"} />
        )}
        <Btn I={Trash} danger testid={`action-delete-${u.uid}`} onClick={() => setModal("delete")}
          label={isMain ? "Hard delete" : "Request hard delete"} />
      </div>

      {msg && <div className="mt-2 text-[11px] text-cyan-300" data-testid={`action-msg-${u.uid}`}>{msg}</div>}

      {u.review_stage === "awaiting_signoff" && (
        <div className="mt-2 text-[11px] text-amber-200" data-testid={`awaiting-signoff-${u.uid}`}>
          {u.recommendation?.decision?.toUpperCase()} recommended by {u.recommendation?.by} — awaiting main-admin sign-off.
        </div>
      )}
      {u.review_stage === "correction_requested" && (
        <div className="mt-2 text-[11px] text-amber-200" data-testid={`correction-requested-${u.uid}`}>
          Correction requested by {u.correction_requested?.by} — waiting on the buyer.
        </div>
      )}

      {modal === "review" && <ReviewModal u={u} isMain={isMain} onClose={close} onDone={done} />}
      {modal === "edit" && <EditProfileModal u={u} onClose={close} onDone={done} />}
      {modal === "contact" && <ContactModal u={u} onClose={close} />}
      {modal === "payments" && <PaymentsModal u={u} onClose={close} />}
      {modal === "documents" && <DocumentsModal u={u} onClose={close} onDone={done} />}
      {modal === "delete" && <DeleteModal u={u} isMain={isMain} onClose={close} onDone={done} />}
    </div>
  );
}
