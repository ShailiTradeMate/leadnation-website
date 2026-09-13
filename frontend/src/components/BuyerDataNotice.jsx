import React, { useState } from "react";
import { Link } from "react-router-dom";
import { ShieldWarning, Scales, CheckCircle } from "@phosphor-icons/react";
import { USAGE_NOTE } from "@/lib/sourceCategories";

const ACK_KEY = "vametra_buyer_data_ack";

/** Blocking acknowledgement gate shown before any Verified Buyer data is visible. */
export default function BuyerDataNotice() {
  const [ack, setAck] = useState(() => {
    try { return sessionStorage.getItem(ACK_KEY) === "1"; } catch (_) { return false; }
  });
  const [checked, setChecked] = useState(false);

  if (ack) return null;

  const accept = () => {
    try { sessionStorage.setItem(ACK_KEY, "1"); } catch (_) {}
    setAck(true);
  };

  return (
    <div data-testid="buyer-data-notice" role="dialog" aria-modal="true"
      className="fixed inset-0 z-[100] grid place-items-center px-5 py-8 bg-[#050816]/85 backdrop-blur-xl overflow-y-auto">
      <div className="w-full max-w-xl glass-strong rounded-3xl p-7 sm:p-9 border border-amber-400/25">
        <div className="flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-amber-300">
          <ShieldWarning size={15} weight="fill" /> Data usage terms
        </div>
        <h2 className="font-display font-extrabold text-2xl sm:text-3xl mt-3 leading-tight">
          Before you access Verified Buyers
        </h2>
        <p className="mt-4 text-sm text-slate-300 leading-relaxed">
          Vametra AI combines information from government records, international trade data, public
          procurement records, business registries, industry sources and company-published information.
          Buyer intelligence is licensed to you for your own sourcing and sales activity only.
        </p>
        <div className="mt-5 rounded-2xl border border-amber-400/25 bg-amber-400/[0.06] p-4 flex items-start gap-3">
          <Scales size={18} weight="duotone" className="text-amber-300 shrink-0 mt-0.5" />
          <p data-testid="buyer-usage-note" className="text-xs text-amber-100/90 leading-relaxed">{USAGE_NOTE}</p>
        </div>
        <p className="mt-4 text-[11px] text-slate-400 leading-relaxed">
          Vametra AI has no contact arrangement with the organisations behind these records. Always verify
          buyer details directly and treat any business you conduct as at your own risk. Full terms in our{" "}
          <Link to="/legal" className="text-cyan-300 hover:underline">legal policies</Link>.
        </p>

        <label className="mt-5 flex items-start gap-3 cursor-pointer select-none">
          <input data-testid="buyer-notice-checkbox" type="checkbox" checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-0.5 w-4 h-4 accent-cyan-400" />
          <span className="text-xs text-slate-300 leading-relaxed">
            I have read and understood this notice. I will not resell, expose or monetise Vametra AI buyer data.
          </span>
        </label>

        <div className="mt-6 flex flex-wrap gap-3">
          <button data-testid="buyer-notice-accept" onClick={accept} disabled={!checked}
            className="btn-primary text-sm disabled:opacity-40 disabled:cursor-not-allowed">
            <CheckCircle size={16} weight="bold" /> I understand & agree
          </button>
          <Link data-testid="buyer-notice-decline" to="/" className="btn-ghost text-sm">Go back</Link>
        </div>
      </div>
    </div>
  );
}
