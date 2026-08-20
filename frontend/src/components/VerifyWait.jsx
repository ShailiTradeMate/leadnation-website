import React, { useState } from "react";
import { CircleNotch, Sparkle, CheckCircle, XCircle, ArrowRight } from "@phosphor-icons/react";

// Light-hearted GK trivia shown WHILE the AI verifies the selfie/document,
// so the 1–2 minute wait feels quick and fun.
const QUESTIONS = [
  { q: "Which country is the world's largest exporter of goods?", options: ["USA", "China", "Germany", "Japan"], answer: 1 },
  { q: "What does 'HS Code' stand for in global trade?", options: ["High Standard Code", "Harmonized System Code", "Handling & Shipping Code", "Home Sourcing Code"], answer: 1 },
  { q: "Which currency is used for most international trade invoicing?", options: ["Euro", "Yen", "US Dollar", "Pound"], answer: 2 },
  { q: "The Suez Canal connects the Mediterranean Sea to which sea?", options: ["Black Sea", "Red Sea", "Caspian Sea", "Arabian Sea"], answer: 1 },
  { q: "What does 'FOB' mean in shipping terms?", options: ["Free On Board", "Freight Over Border", "Full Order Batch", "Final Object Bill"], answer: 0 },
  { q: "Which port is the busiest container port in the world?", options: ["Singapore", "Rotterdam", "Shanghai", "Dubai"], answer: 2 },
  { q: "'IEC' code, required for Indian exporters, stands for?", options: ["Import Export Code", "Indian Export Card", "International Entry Code", "Inland Exchange Code"], answer: 0 },
  { q: "A 'bill of lading' is primarily a document of?", options: ["Insurance", "Title & shipment receipt", "Tax payment", "Customs duty"], answer: 1 },
  { q: "Which organization sets global tariff and trade rules?", options: ["IMF", "WTO", "World Bank", "OPEC"], answer: 1 },
  { q: "'Incoterms' are published by which body?", options: ["UN", "ICC", "WTO", "IATA"], answer: 1 },
  { q: "The Panama Canal links the Atlantic Ocean to which ocean?", options: ["Indian", "Arctic", "Pacific", "Southern"], answer: 2 },
  { q: "'LC' in trade finance stands for?", options: ["Load Cargo", "Letter of Credit", "Legal Contract", "Logistics Chain"], answer: 1 },
];

export default function VerifyWait({ label = "verifying your photo and documents" }) {
  const [qi, setQi] = useState(() => Math.floor(Math.random() * QUESTIONS.length));
  const [picked, setPicked] = useState(null);
  const q = QUESTIONS[qi];
  const next = () => { setPicked(null); setQi((i) => (i + 1) % QUESTIONS.length); };

  return (
    <div className="rounded-2xl border border-cyan-400/30 bg-gradient-to-br from-cyan-500/10 to-violet-500/5 p-5 mt-4 animate-[fadeIn_.4s_ease]" data-testid="verify-wait">
      <div className="flex items-center gap-3">
        <span className="relative flex h-9 w-9 items-center justify-center">
          <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400/30 animate-ping" />
          <CircleNotch size={20} className="animate-spin text-cyan-200 relative" />
        </span>
        <div>
          <div className="font-semibold text-cyan-100">Please stay tuned — we're {label}.</div>
          <div className="text-slate-300 text-sm">This usually takes <b className="text-white">1–2 minutes</b>. Here's a quick trivia while you wait.</div>
        </div>
      </div>

      <div className="mt-4 rounded-xl bg-black/20 border border-white/10 p-4">
        <div className="flex items-start gap-2 text-sm font-medium text-white">
          <Sparkle size={16} className="text-violet-300 mt-0.5 shrink-0" weight="fill" /> {q.q}
        </div>
        <div className="grid sm:grid-cols-2 gap-2 mt-3">
          {q.options.map((opt, i) => {
            const isAns = i === q.answer;
            const show = picked !== null;
            const cls = show
              ? isAns ? "border-emerald-400/50 bg-emerald-500/10 text-emerald-100"
                : i === picked ? "border-rose-400/50 bg-rose-500/10 text-rose-100" : "border-white/10 opacity-50"
              : "border-white/10 hover:border-cyan-400/40 hover:bg-white/5";
            return (
              <button key={i} disabled={show} onClick={() => setPicked(i)} data-testid={`quiz-option-${i}`}
                className={`flex items-center justify-between gap-2 text-left text-sm rounded-lg border px-3 py-2 transition-colors ${cls}`}>
                <span>{opt}</span>
                {show && isAns && <CheckCircle size={15} className="text-emerald-300 shrink-0" weight="fill" />}
                {show && i === picked && !isAns && <XCircle size={15} className="text-rose-300 shrink-0" weight="fill" />}
              </button>
            );
          })}
        </div>
        {picked !== null && (
          <button onClick={next} className="btn-ghost text-sm mt-3" data-testid="quiz-next">
            Next question <ArrowRight size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
