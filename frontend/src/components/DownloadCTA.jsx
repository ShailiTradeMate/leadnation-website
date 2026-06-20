import React from "react";
import { useNavigate } from "react-router-dom";
import { AppleLogo, AndroidLogo, ArrowRight } from "@phosphor-icons/react";
import { APP_LINKS } from "@/data/contact";

export default function DownloadCTA({ compact = false, id }) {
  const navigate = useNavigate();
  return (
    <section id={id} className="relative">
      <div className={`relative overflow-hidden rounded-3xl glass-strong ${compact ? "p-8 sm:p-10" : "p-10 sm:p-14"}`}>
        <div className="absolute -top-32 -right-32 w-[420px] h-[420px] rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-[420px] h-[420px] rounded-full bg-violet-500/20 blur-3xl" />
        <div className="relative grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">
              Take it with you
            </div>
            <h3 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight mt-3 leading-[1.05]">
              Trade intelligence,<br />
              <span className="gradient-text">in your pocket.</span>
            </h3>
            <p className="mt-5 text-slate-300 max-w-md">
              Search products, check customs duties, scan expos and chase leads from
              anywhere on earth — the LeadNation app is built for traders on the move.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={APP_LINKS.ios}
                data-testid={`cta-download-ios${compact ? "-compact" : ""}`}
                className="glass rounded-2xl px-5 py-3 flex items-center gap-3 hover:border-cyan-400/50 hover:-translate-y-0.5 transition-all"
              >
                <AppleLogo size={32} weight="fill" />
                <div className="leading-tight text-left">
                  <div className="text-[10px] uppercase tracking-wider text-slate-400">Coming soon on</div>
                  <div className="text-base font-semibold">App Store</div>
                </div>
              </a>
              <a
                href={APP_LINKS.android}
                data-testid={`cta-download-android${compact ? "-compact" : ""}`}
                className="glass rounded-2xl px-5 py-3 flex items-center gap-3 hover:border-cyan-400/50 hover:-translate-y-0.5 transition-all"
              >
                <AndroidLogo size={32} weight="fill" />
                <div className="leading-tight text-left">
                  <div className="text-[10px] uppercase tracking-wider text-slate-400">Coming soon on</div>
                  <div className="text-base font-semibold">Google Play</div>
                </div>
              </a>
              <button
                onClick={() => navigate("/contact")}
                data-testid={`cta-create-account${compact ? "-compact" : ""}`}
                className="btn-primary"
              >
                Create Account <ArrowRight size={18} weight="bold" />
              </button>
            </div>
          </div>

          <div className="relative h-[280px] lg:h-[360px]">
            <PhoneMock />
          </div>
        </div>
      </div>
    </section>
  );
}

function PhoneMock() {
  return (
    <div className="absolute inset-0 grid place-items-center">
      <div className="relative w-[200px] h-[400px] rounded-[40px] bg-gradient-to-b from-[#0d1330] to-[#050816] border border-white/10 shadow-2xl floaty">
        <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-5 bg-black rounded-full" />
        <div className="absolute inset-3 rounded-[32px] overflow-hidden border border-white/5">
          <div className="absolute inset-0 bg-gradient-to-b from-[#0A2540] via-[#0a0f24] to-[#050816]" />
          <div className="absolute inset-0 p-3">
            <div className="text-[8px] text-cyan-300 font-mono-display tracking-[0.3em] uppercase">LeadNation</div>
            <div className="mt-1 text-xs font-display font-bold leading-tight">Find your next<br/>global buyer</div>
            <div className="mt-3 space-y-1.5">
              {[1,2,3,4].map((i)=>(
                <div key={i} className="glass rounded-lg px-2 py-1.5">
                  <div className="h-1.5 w-12 bg-cyan-400/60 rounded-full" />
                  <div className="h-1 w-20 bg-white/20 rounded-full mt-1" />
                </div>
              ))}
            </div>
            <div className="absolute bottom-3 left-3 right-3">
              <div className="h-7 rounded-full bg-cyan-400 grid place-items-center text-[9px] font-bold text-black">
                Open in app
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="absolute -left-2 top-10 glass rounded-xl p-2 text-[10px] floaty" style={{animationDelay:"1.5s"}}>
        <div className="text-cyan-300 font-mono-display tracking-widest">DUTY</div>
        <div className="font-semibold">0% · CEPA</div>
      </div>
      <div className="absolute -right-2 bottom-12 glass rounded-xl p-2 text-[10px] floaty" style={{animationDelay:"3s"}}>
        <div className="text-violet-300 font-mono-display tracking-widest">EXPO</div>
        <div className="font-semibold">Gulfood ‘26</div>
      </div>
    </div>
  );
}
