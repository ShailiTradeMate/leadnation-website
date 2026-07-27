import React from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, MapPin, Package, ArrowRight } from "@phosphor-icons/react";
import { TRUST_COLORS } from "@/lib/vbieApi";

export function TrustBadge({ trust, size = "sm" }) {
  const c = TRUST_COLORS[trust?.color] || TRUST_COLORS.slate;
  const pad = size === "lg" ? "px-3 py-1.5 text-xs" : "px-2 py-1 text-[10px]";
  return (
    <span data-testid="buyer-trust-badge"
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono-display tracking-widest uppercase ${pad} ${c}`}>
      <ShieldCheck size={size === "lg" ? 14 : 12} weight="fill" />
      {trust?.band || "Unverified"} · {trust?.score ?? "—"}
    </span>
  );
}

export default function BuyerCard({ buyer, index }) {
  return (
    <Link
      to={`/buyers/${buyer.geid}`}
      data-testid={`buyer-card-${index}`}
      className="group glass rounded-3xl p-5 flex flex-col gap-3 transition-transform duration-300 hover:-translate-y-1 hover:glass-strong border border-white/5"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-display font-bold leading-tight">{buyer.display_name}</div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <MapPin size={12} weight="duotone" /> {buyer.city} · {buyer.country_name}
          </div>
        </div>
        <TrustBadge trust={buyer.trust} />
      </div>

      <div className="text-[11px] font-mono-display tracking-[0.2em] uppercase text-cyan-300/80">{buyer.sector}</div>

      <div className="flex flex-wrap gap-1.5">
        {(buyer.products || []).slice(0, 3).map((p) => (
          <span key={p} className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-white/5 text-slate-300">
            <Package size={11} weight="duotone" /> {p}
          </span>
        ))}
      </div>

      <div className="mt-auto flex items-center justify-between pt-2 border-t border-white/5">
        <span className="text-[11px] text-slate-500">{buyer.evidence_count} evidence source{buyer.evidence_count === 1 ? "" : "s"}</span>
        <span className="text-xs text-cyan-300 flex items-center gap-1 group-hover:gap-2 transition-all">
          View intelligence <ArrowRight size={13} weight="bold" />
        </span>
      </div>
    </Link>
  );
}
