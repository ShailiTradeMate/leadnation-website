import React, { useEffect, useState } from "react";
import TradeGlobe from "@/components/TradeGlobe";
import DownloadCTA from "@/components/DownloadCTA";
import SEO, { baseOrgSchema } from "@/components/SEO";
import { SectionLabel } from "@/components/PageHero";
import { searchAll, fetchIndiaFeatures } from "@/lib/api";
import {
  MagnifyingGlass,
  ArrowRight,
  Lightning,
  ShieldCheck,
  Compass,
  Package,
  CalendarBlank,
  Newspaper,
  GlobeHemisphereEast,
  Translate,
  CurrencyInr,
  Receipt,
  Sparkle,
  Buildings,
} from "@phosphor-icons/react";
import { Link, useNavigate } from "react-router-dom";

const ICONS = { compass: Compass, receipt: Receipt, sparkle: Sparkle, buildings: Buildings, package: Package, translate: Translate };

export default function Home() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [focused, setFocused] = useState(false);
  const [india, setIndia] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchIndiaFeatures().then(setIndia).catch(() => {});
  }, []);

  useEffect(() => {
    if (!q) {
      setResults([]);
      return;
    }
    const t = setTimeout(() => {
      searchAll(q).then((d) => setResults(d.results)).catch(() => {});
    }, 220);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="relative">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10 pt-14 pb-10 lg:pt-20 lg:pb-14 grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 reveal-up">
            <SectionLabel testId="home-eyebrow">Global Trade Intelligence Portal</SectionLabel>
            <h1
              data-testid="home-hero-title"
              className="font-display font-extrabold tracking-tight text-[40px] sm:text-6xl lg:text-7xl leading-[1.02] mt-5"
            >
              The world's<br />
              trade desk,<br />
              <span className="gradient-text">re-engineered.</span>
            </h1>
            <p className="mt-6 text-slate-300 text-lg max-w-xl leading-relaxed">
              Search any product, country or HS code. Decode customs, discover expos,
              follow live trade news — all powered by the LeadNation engine.
            </p>

            {/* Search */}
            <div className="mt-8 relative" onBlur={() => setTimeout(() => setFocused(false), 150)}>
              <div className={`glass-strong rounded-2xl flex items-center gap-3 px-4 py-3 transition-all ${focused ? "cyan-glow" : ""}`}>
                <MagnifyingGlass size={20} className="text-cyan-300 shrink-0" />
                <input
                  data-testid="home-search-input"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  onFocus={() => setFocused(true)}
                  placeholder="Ask anything — Can I export Agarbatti to UAE? HS code for basmati?"
                  className="flex-1 bg-transparent outline-none text-white placeholder:text-slate-500 text-[15px]"
                  onKeyDown={(e) => { if (e.key === "Enter" && q.trim()) navigate(`/brain?q=${encodeURIComponent(q)}`); }}
                />
                <button
                  data-testid="home-search-submit"
                  className="hidden sm:inline-flex btn-primary !py-2 !px-4 text-[13px]"
                  onClick={() => navigate(q.trim() ? `/brain?q=${encodeURIComponent(q)}` : "/brain")}
                >
                  Ask the Brain <ArrowRight size={14} weight="bold" />
                </button>
              </div>
              {focused && results.length > 0 && (
                <div className="absolute z-20 mt-2 w-full glass-strong rounded-2xl p-2 max-h-72 overflow-auto">
                  {results.map((r, i) => (
                    <button
                      key={i}
                      data-testid={`home-search-result-${i}`}
                      onMouseDown={() => navigate(r.type === "product" ? "/product-info" : "/customs-compliance")}
                      className="w-full text-left flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-white/5"
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-cyan-300 text-[10px] font-mono-display tracking-widest uppercase">
                          {r.type === "country" ? r.flag || "•" : "#"}
                        </span>
                        <span className="text-sm text-white">{r.label}</span>
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono-display uppercase tracking-widest">{r.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-6 flex flex-wrap gap-3 text-xs text-slate-400">
              <Suggestion onClick={() => setQ("Basmati Rice")} label="Basmati Rice" />
              <Suggestion onClick={() => setQ("India")} label="India" />
              <Suggestion onClick={() => setQ("Pharmaceuticals")} label="Pharma" />
              <Suggestion onClick={() => setQ("Singapore")} label="Singapore" />
            </div>

            <div className="mt-8 flex items-center gap-6 text-xs text-slate-400">
              <Stat value="186+" label="Countries" />
              <Stat value="32K" label="HS Codes" />
              <Stat value="1.2M" label="Data points" />
            </div>
          </div>

          <div className="lg:col-span-6 relative reveal-up" style={{ animationDelay: ".15s" }}>
            <TradeGlobe height={560} />
            {/* Floating chips */}
            <div className="hidden md:flex absolute top-6 left-2 glass rounded-2xl px-3 py-2 items-center gap-2 floaty">
              <Lightning size={16} className="text-cyan-300" />
              <div className="text-xs">
                <div className="text-cyan-300 font-mono-display tracking-widest text-[9px] uppercase">Real-time</div>
                <div className="text-white font-semibold">Live trade lanes</div>
              </div>
            </div>
            <div className="hidden md:flex absolute bottom-10 right-2 glass rounded-2xl px-3 py-2 items-center gap-2 floaty" style={{animationDelay:"2s"}}>
              <ShieldCheck size={16} className="text-violet-300" />
              <div className="text-xs">
                <div className="text-violet-300 font-mono-display tracking-widest text-[9px] uppercase">Compliance</div>
                <div className="text-white font-semibold">DGFT · CBAM · FTA</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MARQUEE */}
      <section className="relative py-8 border-y border-white/5 overflow-hidden">
        <div className="marquee-track text-slate-400 text-sm font-mono-display tracking-[0.3em] uppercase">
          {Array(2).fill(0).map((_, k) => (
            <div key={k} className="flex items-center gap-10 px-6">
              <span>India → UAE · 0% CEPA</span><Dot />
              <span>Red Sea reroutes +38%</span><Dot />
              <span>EU CBAM Q2 reporting</span><Dot />
              <span>Gulfood Dubai · Feb 26</span><Dot />
              <span>India Exports $450B</span><Dot />
              <span>RoDTEP Extended 2026</span><Dot />
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES BENTO */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 py-24">
        <SectionLabel testId="home-features-label">What's inside the app</SectionLabel>
        <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-5xl mt-4 max-w-3xl leading-[1.05]">
          Five engines. One <span className="gradient-text">global advantage.</span>
        </h2>

        <div className="mt-12 grid md:grid-cols-6 gap-5">
          <FeatureCard className="md:col-span-3 md:row-span-2" Icon={GlobeHemisphereEast} title="Customs & Compliance Engine"
            desc="Live HS codes, duty rates, FTA benefits and document checklists for 186+ markets — synced with DGFT, CBAM and customs authorities worldwide."
            link="/customs-compliance" testId="feat-customs" big />
          <FeatureCard className="md:col-span-3" Icon={Package} title="Product Info Engine"
            desc="Pick a country, business type and product. Get market size, top buyers, tariffs and certifications in seconds."
            link="/product-info" testId="feat-product" />
          <FeatureCard className="md:col-span-3" Icon={CalendarBlank} title="Expo & Events Engine"
            desc="Every major trade expo on earth — filtered by sector, country and date." link="/expo" testId="feat-expo" />
          <FeatureCard className="md:col-span-3" Icon={Newspaper} title="Trade News Engine"
            desc="Real-time global trade news, personalized to your country and role." link="/trade-news" testId="feat-news" />
        </div>
      </section>

      {/* TRADE COMMAND CENTER — flagship */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 py-12" data-testid="home-command-center">
        <div className="relative glass-strong rounded-3xl p-8 sm:p-12 overflow-hidden border border-cyan-400/25">
          <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full bg-violet-500/10 blur-3xl pointer-events-none" />
          <div className="relative">
            <div className="inline-flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
              <Lightning size={14} weight="duotone" /> LeadNation Trade Command Center™
            </div>
            <h2 className="font-display font-extrabold text-3xl sm:text-5xl mt-4 leading-[1.05] max-w-3xl">
              The World's First <span className="gradient-text">AI-Powered Global Trade Operating System.</span>
            </h2>
            <p className="mt-4 text-slate-300 text-sm sm:text-base max-w-2xl">
              Stop juggling ten different tools. Build your full FOB → CIF → landed-cost waterfall, compare what your buyer pays across markets, quote in any two currencies, and let the LeadNation Brain flag savings, risks and the best market — for any product across 195 countries.
            </p>
            <div className="mt-7 grid sm:grid-cols-3 gap-3 max-w-2xl">
              {[
                ["FOB · CIF · Landed cost", "Transparent cost waterfall"],
                ["Buyer landed-cost comparison", "Find your best market"],
                ["Dual-currency AI quote", "Your currency + any global one"],
              ].map(([t, s]) => (
                <div key={t} className="glass rounded-2xl px-4 py-3">
                  <div className="font-display font-bold text-sm">{t}</div>
                  <div className="text-[11px] text-cyan-300 mt-0.5">{s}</div>
                </div>
              ))}
            </div>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/command-center" data-testid="home-command-center-cta" className="btn-primary">
                Open Trade Command Center <ArrowRight size={16} weight="bold" />
              </Link>
              <Link to="/brain" className="btn-ghost">Ask the LeadNation Brain</Link>
            </div>
          </div>
        </div>
      </section>

      {/* SERVICES HIGHLIGHT */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 py-12" data-testid="home-services-highlight">
        <div className="glass-strong rounded-3xl p-8 sm:p-10 grid lg:grid-cols-2 gap-8 items-center border border-cyan-400/20">
          <div>
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Done-for-you · Business Services</div>
            <h2 className="font-display font-extrabold text-3xl sm:text-4xl mt-3 leading-tight">IEC, GST, RCMC & company setup — handled end-to-end.</h2>
            <p className="mt-3 text-slate-300 text-sm sm:text-base">Skip the paperwork. Our experts get your export business registration-ready, fast. Transparent pricing, real humans, full compliance.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/services" data-testid="home-services-cta" className="btn-primary">Explore Services <ArrowRight size={16} weight="bold" /></Link>
              <Link to="/services/iec-registration" className="btn-ghost">Apply for IEC</Link>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[["IEC Registration", "/services/iec-registration"], ["GST Registration", "/services/gst-registration"], ["RCMC", "/services/rcmc-registration"], ["Company Setup", "/services"]].map(([t, to]) => (
              <Link key={t} to={to} className="glass rounded-2xl px-4 py-5 hover:border-cyan-400/40 hover:-translate-y-0.5 transition-all">
                <div className="font-display font-bold">{t}</div>
                <div className="text-xs text-cyan-300 mt-1 flex items-center gap-1">Get started <ArrowRight size={12} /></div>
              </Link>
            ))}
          </div>
        </div>
      </section>


      {/* INDIA FEATURES */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 py-16">
        <div className="flex items-center gap-3 mb-4">
          <CurrencyInr size={24} className="text-cyan-300" />
          <SectionLabel testId="india-label">Engineered for India</SectionLabel>
        </div>
        <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-5xl max-w-3xl">
          From <span className="gradient-text">Ahmedabad to Antarctica</span> — Indian exporters first.
        </h2>
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {india.map((f, i) => {
            const Icon = ICONS[f.icon] || Sparkle;
            return (
              <div
                key={i}
                data-testid={`india-feature-${i}`}
                className="glass rounded-2xl p-6 hover:border-cyan-400/30 transition-all hover:-translate-y-1"
              >
                <div className="w-11 h-11 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
                  <Icon size={22} weight="duotone" className="text-cyan-300" />
                </div>
                <div className="mt-4 font-display font-bold text-lg">{f.title}</div>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">{f.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* APPLE-STYLE STORY */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 py-24">
        <div className="grid lg:grid-cols-2 gap-10 items-center">
          <div className="order-2 lg:order-1">
            <SectionLabel testId="story-label">Moving pictures, moving cargo</SectionLabel>
            <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-5xl mt-4 leading-[1.05]">
              See trade <span className="gradient-text">happen.</span>
            </h2>
            <p className="mt-5 text-slate-300 max-w-lg">
              From port cranes in Mundra to bonded warehouses in Jebel Ali — the
              LeadNation app shows you every step, in motion.
            </p>
            <div className="mt-7 flex gap-3">
              <Link to="/product-info" data-testid="story-cta-explore" className="btn-primary">Explore products <ArrowRight size={16} weight="bold" /></Link>
              <Link to="/expo" data-testid="story-cta-expos" className="btn-ghost">See expos</Link>
            </div>
          </div>
          <div className="order-1 lg:order-2 grid grid-cols-2 gap-4">
            <MotionTile src="https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=900&q=80" tall />
            <div className="grid grid-rows-2 gap-4">
              <MotionTile src="https://images.unsplash.com/photo-1577017040065-650ee4d43339?auto=format&fit=crop&w=900&q=80" />
              <MotionTile src="https://images.unsplash.com/photo-1605902711622-cfb43c4437b5?auto=format&fit=crop&w=900&q=80" />
            </div>
          </div>
        </div>
      </section>

      {/* DOWNLOAD CTA */}
      <section className="relative max-w-7xl mx-auto px-6 sm:px-10 pb-20">
        <DownloadCTA id="download" />
      </section>
    </div>
  );
}

function Suggestion({ label, onClick }) {
  return (
    <button onClick={onClick} className="glass px-3 py-1.5 rounded-full hover:border-cyan-400/40 transition-all">
      {label}
    </button>
  );
}
function Stat({ value, label }) {
  return (
    <div>
      <div className="font-display font-bold text-lg sm:text-xl">{value}</div>
      <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500 font-mono-display">{label}</div>
    </div>
  );
}
function Dot() {
  return <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60" />;
}
function FeatureCard({ Icon, title, desc, link, className = "", testId, big = false }) {
  return (
    <Link to={link} data-testid={testId} className={`group relative glass rounded-3xl p-7 overflow-hidden hover:border-cyan-400/30 transition-all hover:-translate-y-1 ${className}`}>
      <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-cyan-500/10 blur-3xl group-hover:bg-cyan-500/20 transition-colors" />
      <div className="relative">
        <div className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
          <Icon size={24} weight="duotone" className="text-cyan-300" />
        </div>
        <h3 className={`mt-5 font-display font-bold leading-tight ${big ? "text-2xl sm:text-3xl" : "text-xl"}`}>{title}</h3>
        <p className={`mt-3 text-slate-400 leading-relaxed ${big ? "text-base max-w-md" : "text-sm"}`}>{desc}</p>
        <div className="mt-5 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
          Explore <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </Link>
  );
}
function MotionTile({ src, tall = false }) {
  return (
    <div className={`relative rounded-3xl overflow-hidden border border-white/10 group ${tall ? "row-span-2 h-full min-h-[300px]" : "h-[210px]"}`}>
      <img src={src} alt="" className="absolute inset-0 w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-[3s]" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-transparent to-transparent" />
    </div>
  );
}
