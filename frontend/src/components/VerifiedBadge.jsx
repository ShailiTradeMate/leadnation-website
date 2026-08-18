import React from "react";
import { SealCheck, Clock, XCircle, ShieldWarning } from "@phosphor-icons/react";

// Status pill for the Verified Buyer flow. "verified" is the only badge that
// signals a genuinely verified member — awarded only after identity + document
// checks pass (or a human review approves).
const MAP = {
  verified: { label: "Verified Member", Icon: SealCheck,
    cls: "bg-emerald-500/15 border-emerald-400/30 text-emerald-200" },
  needs_review: { label: "Verification in review", Icon: Clock,
    cls: "bg-amber-500/15 border-amber-400/30 text-amber-200" },
  pending: { label: "Verification in review", Icon: Clock,
    cls: "bg-amber-500/15 border-amber-400/30 text-amber-200" },
  rejected: { label: "Verification failed", Icon: XCircle,
    cls: "bg-rose-500/15 border-rose-400/30 text-rose-200" },
  unverified: { label: "Not verified", Icon: ShieldWarning,
    cls: "bg-slate-500/15 border-slate-400/30 text-slate-300" },
};

export default function VerifiedBadge({ status = "unverified", size = "sm" }) {
  const m = MAP[status] || MAP.unverified;
  const { Icon } = m;
  const pad = size === "lg" ? "px-3 py-1.5 text-sm" : "px-2.5 py-1 text-xs";
  return (
    <span data-testid={`verified-badge-${status}`}
      className={`inline-flex items-center gap-1.5 rounded-full border ${pad} ${m.cls}`}>
      <Icon size={size === "lg" ? 16 : 13} weight="fill" /> {m.label}
    </span>
  );
}
