import React, { useEffect, useMemo, useRef, useState } from "react";
import { MagnifyingGlass, CaretDown, X } from "@phosphor-icons/react";
import { api } from "@/lib/api";

/**
 * HsCodePicker — searchable picker over the COMPLETE HS nomenclature
 * (all 5,606 six-digit WCO HS-2022 codes, served by /api/trade-intel/hs-directory).
 * Search by code prefix ("0910") or by description ("turmeric"). Touch + keyboard friendly.
 */
export const HsCodePicker = ({
  value = "",
  onChange,
  label = "HS / HSN code",
  placeholder = "Search 5,606 HS codes — e.g. turmeric or 0910",
  testId = "hs-code-picker",
}) => {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [hi, setHi] = useState(0);
  const boxRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    let dead = false;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const { data } = await api.get("/trade-intel/hs-directory", { params: { q, limit: 40 } });
        if (!dead) { setRows(data.results || []); setTotal(data.total || 0); setHi(0); }
      } catch (_) { if (!dead) setRows([]); }
      finally { if (!dead) setLoading(false); }
    }, 220);
    return () => { dead = true; clearTimeout(t); };
  }, [q, open]);

  useEffect(() => {
    const away = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", away);
    return () => document.removeEventListener("mousedown", away);
  }, []);

  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 30); }, [open]);

  const selected = useMemo(() => rows.find((r) => r.hs6 === value), [rows, value]);

  const pick = (row) => { onChange?.(row.hs6, row); setOpen(false); setQ(""); };

  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setHi((i) => Math.min(i + 1, rows.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setHi((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter" && rows[hi]) { e.preventDefault(); pick(rows[hi]); }
    else if (e.key === "Escape") { setOpen(false); }
  };

  return (
    <div className="relative" ref={boxRef}>
      {label && <div className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-400 mb-2">{label}</div>}
      <button
        type="button"
        data-testid={`${testId}-trigger`}
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-3 rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-left hover:border-cyan-400/40 transition-colors"
      >
        <span className={`min-w-0 flex-1 truncate text-sm ${value ? "text-white" : "text-slate-400"}`}>
          {value ? `HS ${value}${selected ? ` — ${selected.description}` : ""}` : placeholder}
        </span>
        <span className="flex items-center gap-2 shrink-0">
          {value && (
            <X
              size={14}
              data-testid={`${testId}-clear`}
              className="text-slate-400 hover:text-white"
              onClick={(e) => { e.stopPropagation(); onChange?.("", null); }}
            />
          )}
          <CaretDown size={14} className="text-cyan-300" />
        </span>
      </button>

      {open && (
        <div
          data-testid={`${testId}-panel`}
          className="absolute z-50 mt-2 w-full rounded-xl border border-white/10 bg-[#0a1120] shadow-2xl shadow-black/60 overflow-hidden"
        >
          <div className="flex items-center gap-2 px-3 py-2.5 border-b border-white/10">
            <MagnifyingGlass size={15} className="text-cyan-300 shrink-0" />
            <input
              ref={inputRef}
              data-testid={`${testId}-search`}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={onKey}
              placeholder="Type a product or an HS code…"
              className="w-full bg-transparent text-sm text-white placeholder:text-slate-500 outline-none"
            />
          </div>
          <div className="max-h-72 overflow-y-auto overscroll-contain">
            {loading && <div className="px-4 py-3 text-xs text-slate-400">Searching the HS nomenclature…</div>}
            {!loading && rows.length === 0 && (
              <div className="px-4 py-3 text-xs text-slate-400">No HS code matches that. Try a simpler word, or a 2-4 digit code.</div>
            )}
            {!loading && rows.map((r, i) => (
              <button
                key={r.hs6}
                type="button"
                data-testid={`${testId}-option-${r.hs6}`}
                onMouseEnter={() => setHi(i)}
                onClick={() => pick(r)}
                className={`w-full text-left px-4 py-2.5 flex items-start gap-3 ${i === hi ? "bg-cyan-500/10" : "hover:bg-white/5"}`}
              >
                <span className="font-mono-display text-[11px] text-cyan-300 pt-0.5 shrink-0">{r.hs6}</span>
                <span className="text-[13px] text-slate-200 leading-snug">{r.description}</span>
              </button>
            ))}
          </div>
          <div className="px-4 py-2 border-t border-white/10 text-[10px] font-mono-display tracking-wider text-slate-500">
            {total.toLocaleString()} MATCHES · WCO HS 2022 NOMENCLATURE
          </div>
        </div>
      )}
    </div>
  );
};

export default HsCodePicker;
