import React, { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useSpring, useReducedMotion } from "framer-motion";
import TradeGlobe from "@/components/TradeGlobe";
import DownloadCTA from "@/components/DownloadCTA";
import SEO, { faqSchema } from "@/components/SEO";
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
  Brain,
} from "@phosphor-icons/react";
import { Link, useNavigate } from "react-router-dom";

const ICONS = { compass: Compass, receipt: Receipt, sparkle: Sparkle, buildings: Buildings, package: Package, translate: Translate };
const EASE = [0.16, 1, 0.3, 1];

/** Scroll-triggered entrance. Collapses to a plain div when reduced motion is on. */
function Reveal({ children, delay = 0, y = 40, className = "", ...rest }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className} {...rest}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.75, ease: EASE, delay }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export default function Home() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [focused, setFocused] = useState(false);
  const [india, setIndia] = useState([]);
  const navigate = useNavigate();
  const reduce = useReducedMotion();

  const heroRef = useRef(null);
  const storyRef = useRef(null);

  // page-level progress beam
  const { scrollYProgress } = useScroll();
  const beam = useSpring(scrollYProgress, { stiffness: 120, damping: 30, mass: 0.3 });

  // hero parallax
  const { scrollYProgress: heroP } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const globeY = useTransform(heroP, [0, 1], [0, 140]);
  const globeScale = useTransform(heroP, [0, 1], [1, 1.12]);
  const copyY = useTransform(heroP, [0, 1], [0, 60]);
  const copyOpacity = useTransform(heroP, [0, 0.75], [1, 0.15]);
  const chipTopY = useTransform(heroP, [0, 1], [0, -70]);
  const chipBottomY = useTransform(heroP, [0, 1], [0, 55]);

  // photo story drone-pan
  const { scrollYProgress: storyP } = useScroll({ target: storyRef, offset: ["start end", "end start"] });
  const tileA = useTransform(storyP, [0, 1], [-30, 30]);
  const tileB = useTransform(storyP, [0, 1], [26, -26]);

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
      <SEO
        title="Vametra AI · AI-Powered Global Trade Intelligence Platform"
        description="Search any product, country or HS code. Decode customs duties, calculate landed cost across all Incoterms, discover trade expos and follow live global trade news — powered by the Vametra AI Brain. Free to start, built for 195+ countries."
        path="/"
        keywords="global trade intelligence, customs duty calculator, HS code finder, landed cost calculator, Incoterms, FTA, export import platform, trade expos, trade news, Vametra AI, Intelligence Beyond Borders"
        schema={faqSchema([
          { q: "What is Vametra AI?", a: "Vametra AI is an AI-powered Global Trade Intelligence platform that helps exporters, importers and trade professionals calculate customs duties, find HS codes, compute landed cost across all Incoterms, analyse FTAs, discover trade expos and follow real-time trade news for 195+ countries." },
          { q: "Is Vametra AI free?", a: "Yes — you can explore the platform and generate your first trade report for free. Pro plans unlock unlimited reports and premium intelligence." },
          { q: "Which countries does Vametra AI cover?", a: "Vametra AI provides trade, customs and market intelligence for 195+ countries worldwide, with deep coverage of India and major trade corridors." },
          { q: "Does Vametra AI have a mobile app?", a: "Yes. Vametra AI works on web, iOS and Android with a single shared login, so your trade projects sync across devices." },
        ])}
      />

      {/* SCROLL PROGRESS BEAM */}
      {!reduce && <motion.div className="scroll-progress-bar" style={{ scaleX: beam }} aria-hidden="true" />}

      {/* ===================== HERO — cinematic command cockpit ===================== */}
      <section ref={heroRef} className="relative overflow-hidden lg:min-h-[92vh] flex items-center">
        <div className="aurora aurora-breathe" />

        {/* Globe stage — desktop: atmospheric centrepiece behind the copy */}
        <motion.div
          style={reduce ? undefined : { y: globeY, scale: globeScale }}
          className="hidden lg:block absolute top-[4%] right-[-3%] w-[56%] max-w-[760px] z-0 will-change-transform"
        >
          <div className="relative">
            <div className="absolute inset-[8%] globe-glow-disc rounded-full" />
            <div className="absolute inset-[-6%] tech-ring" />
            <div className="absolute inset-[6%] tech-ring tech-ring-rev" />
            <TradeGlobe height={620} interactive={false} />
          </div>
          <motion.div style={reduce ? undefined : { y: chipTopY }}
            className="absolute top-10 left-2 glass rounded-2xl px-3 py-2 flex items-center gap-2 floaty">
            <Lightning size={16} className="text-cyan-300" />
            <div className="text-xs">
              <div className="text-cyan-300 font-mono-display tracking-widest text-[9px] uppercase">Real-time</div>
              <div className="text-white font-semibold">Live trade lanes</div>
            </div>
          </motion.div>
          <motion.div style={reduce ? { animationDelay: "2s" } : { y: chipBottomY, animationDelay: "2s" }}
            className="absolute bottom-16 left-10 glass rounded-2xl px-3 py-2 flex items-center gap-2 floaty">
            <ShieldCheck size={16} className="text-violet-300" />
            <div className="text-xs">
              <div className="text-violet-300 font-mono-display tracking-widest text-[9px] uppercase">Compliance</div>
              <div className="text-white font-semibold">DGFT · CBAM · FTA</div>
            </div>
          </motion.div>
        </motion.div>

        <div className="cosmic-vignette hidden lg:block z-[1]" />

        {/* Copy + command bar */}
        <motion.div
          style={reduce ? undefined : { y: copyY, opacity: copyOpacity }}
          className="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-10 pt-24 pb-14 lg:pt-24 lg:pb-20"
        >
          <div className="max-w-2xl">
            <Reveal y={16}>
              <SectionLabel testId="home-eyebrow">Global Trade Intelligence · 195 Countries</SectionLabel>
            </Reveal>

            <Reveal delay={0.06} y={26}>
              <h1
                data-testid="home-hero-title"
                className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl leading-[1.06] mt-5"
              >
                Rule global trade.<br />
                <span className="gradient-text">Before cargo moves.</span>
              </h1>
            </Reveal>

            <Reveal delay={0.12} y={22}>
              <p className="mt-5 text-slate-300 text-sm sm:text-base lg:text-lg max-w-xl leading-relaxed">
                Landed cost, live customs duty, sanctions-screened verified buyers and AI clearance
                for any product across 195+ markets — from one command console.
              </p>
            </Reveal>

            {/* Search — the command bar */}
            <Reveal delay={0.18} y={22}>
              <div className="mt-7 relative" onBlur={() => setTimeout(() => setFocused(false), 150)}>
                <div className={`glass-strong rounded-2xl flex items-center gap-3 px-4 py-3 min-h-[56px] transition-all shadow-[0_20px_50px_rgba(0,194,255,0.12)] ${focused ? "cyan-glow" : ""}`}>
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
                  <div className="absolute z-30 mt-2 w-full glass-strong rounded-2xl p-2 max-h-72 overflow-auto">
                    {results.map((r, i) => (
                      <button
                        key={i}
                        data-testid={`home-search-result-${i}`}
                        onMouseDown={() => navigate(r.type === "product" ? `/brain?q=${encodeURIComponent(`${r.label}: HSN code, duty, documents, certifications, top markets and buyers`)}` : "/customs-compliance")}
                        className="w-full text-left flex items-center justify-between px-3 py-3 rounded-lg hover:bg-white/5"
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
                <button
                  className="sm:hidden btn-primary w-full justify-center mt-3 text-sm"
                  onClick={() => navigate(q.trim() ? `/brain?q=${encodeURIComponent(q)}` : "/brain")}
                >
                  Ask the Brain <ArrowRight size={15} weight="bold" />
                </button>
              </div>
            </Reveal>

            <Reveal delay={0.24} y={18}>
              <div className="mt-5 flex gap-2.5 text-xs text-slate-400 overflow-x-auto no-scrollbar pb-1">
                <Suggestion onClick={() => setQ("Basmati Rice")} label="Basmati Rice" />
                <Suggestion onClick={() => setQ("India")} label="India" />
                <Suggestion onClick={() => setQ("Pharmaceuticals")} label="Pharma" />
                <Suggestion onClick={() => setQ("Singapore")} label="Singapore" />
              </div>
            </Reveal>

            <Reveal delay={0.3} y={18}>
              <div className="mt-8 flex items-center gap-7 text-xs text-slate-400">
                <Stat value="186+" label="Countries" />
                <Stat value="32K" label="HS Codes" />
                <Stat value="1.2M" label="Data points" />
              </div>
            </Reveal>
          </div>

          {/* Globe — mobile / tablet: ambient, non-interactive, never steals the scroll */}
          <div className="lg:hidden relative mt-10 -mx-2">
            <div className="absolute inset-[10%] globe-glow-disc rounded-full" />
            <TradeGlobe height={340} heightMobile={300} interactive={false} />
            <div className="cosmic-vignette" />
            <div className="absolute inset-x-0 bottom-2 flex justify-center gap-2">
              <span className="glass rounded-full px-3 py-1.5 text-[10px] font-mono-display uppercase tracking-widest text-cyan-300 flex items-center gap-1.5">
                <Lightning size={11} weight="fill" /> Live trade lanes
              </span>
              <span className="glass rounded-full px-3 py-1.5 text-[10px] font-mono-display uppercase tracking-widest text-violet-300 flex items-center gap-1.5">
                <ShieldCheck size={11} weight="fill" /> DGFT · CBAM
              </span>
            </div>
          </div>
        </motion.div>
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
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 py-20 sm:py-24">
        <Reveal y={24}>
          <SectionLabel testId="home-features-label">What's inside the app</SectionLabel>
          <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 max-w-3xl leading-[1.05]">
            Five engines. One <span className="gradient-text">global advantage.</span>
          </h2>
        </Reveal>

        <div className="mt-10 sm:mt-12 grid md:grid-cols-6 gap-4 sm:gap-5">
          <Reveal className="md:col-span-3 md:row-span-2" delay={0.02}>
            <FeatureCard Icon={GlobeHemisphereEast} title="Customs & Compliance Engine"
              desc="Live HS codes, duty rates, FTA benefits and document checklists for 186+ markets — synced with DGFT, CBAM and customs authorities worldwide."
              link="/customs-compliance" testId="feat-customs" big full />
          </Reveal>
          <Reveal className="md:col-span-3" delay={0.1}>
            <FeatureCard Icon={Brain} title="Vametra AI Brain"
              desc="Ask any product, any border: HSN codes, duty, documents, certifications, demand and verified buyers — one answer, with links straight into the Command Center."
              link="/brain" testId="feat-brain" />
          </Reveal>
          <Reveal className="md:col-span-3" delay={0.18}>
            <FeatureCard Icon={CalendarBlank} title="Expo & Events Engine"
              desc="Every major trade expo on earth — filtered by sector, country and date." link="/expo" testId="feat-expo" />
          </Reveal>
          <Reveal className="md:col-span-3" delay={0.26}>
            <FeatureCard Icon={Newspaper} title="Trade News Engine"
              desc="Real-time global trade news, personalized to your country and role." link="/trade-news" testId="feat-news" />
          </Reveal>
        </div>
      </section>

      {/* TRADE COMMAND CENTER — flagship */}
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 py-10 sm:py-12" data-testid="home-command-center">
        <Reveal y={50}>
          <motion.div
            initial={reduce ? undefined : { scale: 0.965 }}
            whileInView={reduce ? undefined : { scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.9, ease: EASE }}
            className="relative glass-strong rounded-3xl p-6 sm:p-12 overflow-hidden border border-cyan-400/25 will-change-transform"
          >
            <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-24 -left-24 w-72 h-72 rounded-full bg-violet-500/15 blur-3xl pointer-events-none" />
            <div className="relative">
              <div className="inline-flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
                <Lightning size={14} weight="duotone" /> Vametra AI Trade Command Center™
              </div>
              <h2 className="font-display font-extrabold text-2xl sm:text-4xl lg:text-5xl mt-4 leading-[1.06] max-w-3xl">
                The World's First <span className="gradient-text">AI-Powered Global Trade Operating System.</span>
              </h2>
              <p className="mt-4 text-slate-300 text-sm sm:text-base max-w-2xl">
                Stop juggling ten different tools. Build your full FOB → CIF → landed-cost waterfall, compare what your buyer pays across markets, quote in any two currencies, and let the Vametra AI Brain flag savings, risks and the best market — for any product across 195 countries.
              </p>
              <div className="mt-7 grid sm:grid-cols-3 gap-3 max-w-2xl">
                {[
                  ["FOB · CIF · Landed cost", "Transparent cost waterfall"],
                  ["Buyer landed-cost comparison", "Find your best market"],
                  ["Dual-currency AI quote", "Your currency + any global one"],
                ].map(([t, s], i) => (
                  <Reveal key={t} delay={0.08 * i} y={20} className="h-full">
                    <div className="glass rounded-2xl px-4 py-3 h-full">
                      <div className="font-display font-bold text-sm">{t}</div>
                      <div className="text-[11px] text-cyan-300 mt-0.5">{s}</div>
                    </div>
                  </Reveal>
                ))}
              </div>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link to="/command-center" data-testid="home-command-center-cta" className="btn-primary">
                  Open Trade Command Center <ArrowRight size={16} weight="bold" />
                </Link>
                <Link to="/brain" className="btn-ghost">Ask the Vametra AI Brain</Link>
              </div>
            </div>
          </motion.div>
        </Reveal>
      </section>

      {/* VERIFIED BUYERS */}
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 py-10 sm:py-12" data-testid="home-verified-buyers">
        <div className="relative glass-strong rounded-3xl p-6 sm:p-12 overflow-hidden border border-violet-400/25">
          <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-violet-500/12 blur-3xl pointer-events-none" />
          <div className="relative grid lg:grid-cols-2 gap-8 items-center">
            <Reveal y={0} className="lg:pr-4">
              <motion.div
                initial={reduce ? undefined : { opacity: 0, x: -24 }}
                whileInView={reduce ? undefined : { opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.8, ease: EASE }}
              >
                <div className="inline-flex items-center gap-2 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
                  <ShieldCheck size={14} weight="fill" /> Verified Buyer Intelligence Engine
                </div>
                <h2 className="font-display font-extrabold text-2xl sm:text-4xl mt-4 leading-[1.08]">
                  Real global buyers — <span className="gradient-text">with the evidence to prove it.</span>
                </h2>
                <p className="mt-4 text-slate-300 text-sm sm:text-base max-w-xl">
                  Discover active importers and public-sector buyers, aggregated daily from government records, international trade data, public procurement records and business registries — every record sanctions-screened and backed by an explainable trust score.
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <Link to="/buyers" data-testid="home-buyers-cta" className="btn-primary">
                    Explore Verified Buyers <ArrowRight size={16} weight="bold" />
                  </Link>
                  <Link to="/pricing" className="btn-ghost">Plans to unlock profiles</Link>
                </div>
                <p className="mt-3 text-[11px] text-slate-500">Full buyer profiles require sign-in + an active plan.</p>
              </motion.div>
            </Reveal>
            <motion.div
              initial={reduce ? undefined : { opacity: 0, x: 24 }}
              whileInView={reduce ? undefined : { opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.8, ease: EASE, delay: 0.1 }}
              className="grid grid-cols-2 gap-3"
            >
              {[
                ["Official sources", "Government & trade records"],
                ["Sanctions-screened", "Denied-party hard gate"],
                ["Explainable trust", "Every score is broken down"],
                ["Screened provenance", "Aggregated, processed, verified"],
              ].map(([t, s]) => (
                <div key={t} className="glass rounded-2xl px-4 py-5">
                  <div className="font-display font-bold text-sm">{t}</div>
                  <div className="text-[11px] text-cyan-300 mt-1">{s}</div>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* SERVICES HIGHLIGHT */}
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 py-10 sm:py-12" data-testid="home-services-highlight">
        <Reveal>
          <div className="glass-strong rounded-3xl p-6 sm:p-10 grid lg:grid-cols-2 gap-8 items-center border border-cyan-400/20">
            <div>
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Done-for-you · Business Services</div>
              <h2 className="font-display font-extrabold text-2xl sm:text-4xl mt-3 leading-tight">IEC, GST, RCMC & company setup — handled end-to-end.</h2>
              <p className="mt-3 text-slate-300 text-sm sm:text-base">Skip the paperwork. Our experts get your export business registration-ready, fast. Transparent pricing, real humans, full compliance.</p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link to="/services" data-testid="home-services-cta" className="btn-primary">Explore Services <ArrowRight size={16} weight="bold" /></Link>
                <Link to="/services/iec-registration" className="btn-ghost">Apply for IEC</Link>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[["IEC Registration", "/services/iec-registration"], ["GST Registration", "/services/gst-registration"], ["RCMC", "/services/rcmc-registration"], ["Company Setup", "/services"]].map(([t, to], i) => (
                <Reveal key={t} delay={0.06 * i} y={18} className="h-full">
                  <Link to={to} className="block glass rounded-2xl px-4 py-5 h-full hover:border-cyan-400/40 hover:-translate-y-0.5 transition-all">
                    <div className="font-display font-bold">{t}</div>
                    <div className="text-xs text-cyan-300 mt-1 flex items-center gap-1">Get started <ArrowRight size={12} /></div>
                  </Link>
                </Reveal>
              ))}
            </div>
          </div>
        </Reveal>
      </section>

      {/* INDIA FEATURES */}
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 py-16">
        <Reveal y={24}>
          <div className="flex items-center gap-3 mb-4">
            <CurrencyInr size={24} className="text-cyan-300" />
            <SectionLabel testId="india-label">Engineered for India</SectionLabel>
          </div>
          <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl max-w-3xl leading-[1.06]">
            From <span className="gradient-text">Ahmedabad to Antarctica</span> — Indian exporters first.
          </h2>
        </Reveal>
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {india.map((f, i) => {
            const Icon = ICONS[f.icon] || Sparkle;
            return (
              <Reveal key={i} delay={0.08 * (i % 3)} y={34} className="h-full">
                <div
                  data-testid={`india-feature-${i}`}
                  className="glass rounded-2xl p-6 h-full hover:border-cyan-400/30 transition-all hover:-translate-y-1"
                >
                  <div className="w-11 h-11 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
                    <Icon size={22} weight="duotone" className="text-cyan-300" />
                  </div>
                  <div className="mt-4 font-display font-bold text-lg">{f.title}</div>
                  <p className="mt-2 text-sm text-slate-400 leading-relaxed">{f.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* SCROLLYTELLING STORY */}
      <section ref={storyRef} className="relative max-w-7xl mx-auto px-5 sm:px-10 py-20 sm:py-24">
        <div className="grid lg:grid-cols-2 gap-10 items-center">
          <Reveal className="order-2 lg:order-1" y={30}>
            <SectionLabel testId="story-label">Moving pictures, moving cargo</SectionLabel>
            <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.05]">
              See trade <span className="gradient-text">happen.</span>
            </h2>
            <p className="mt-5 text-slate-300 max-w-lg text-sm sm:text-base">
              From port cranes in Mundra to bonded warehouses in Jebel Ali — the
              Vametra AI app shows you every step, in motion.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/products" data-testid="story-cta-explore" className="btn-primary">Explore products <ArrowRight size={16} weight="bold" /></Link>
              <Link to="/expo" data-testid="story-cta-expos" className="btn-ghost">See expos</Link>
            </div>
          </Reveal>
          <div className="order-1 lg:order-2 grid grid-cols-2 gap-4">
            <motion.div style={reduce ? undefined : { y: tileA }} className="will-change-transform">
              <MotionTile src="https://images.unsplash.com/photo-1613690399151-65ea69478674?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" tall />
            </motion.div>
            <motion.div style={reduce ? undefined : { y: tileB }} className="grid grid-rows-2 gap-4 will-change-transform">
              <MotionTile src="https://images.unsplash.com/photo-1670121180530-cfcba4438038?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" />
              <MotionTile src="https://images.unsplash.com/photo-1571086291540-b137111fa1c7?crop=entropy&cs=srgb&fm=jpg&q=85&w=900" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* DOWNLOAD CTA */}
      <section className="relative max-w-7xl mx-auto px-5 sm:px-10 pb-20">
        <Reveal><DownloadCTA id="download" /></Reveal>
      </section>
    </div>
  );
}

function Suggestion({ label, onClick }) {
  return (
    <button onClick={onClick} className="glass px-3.5 py-2 min-h-[38px] shrink-0 rounded-full hover:border-cyan-400/40 transition-all">
      {label}
    </button>
  );
}
function Stat({ value, label }) {
  return (
    <div>
      <div className="font-display font-bold text-lg sm:text-xl">{value}</div>
      <div className="text-[9px] sm:text-[10px] uppercase tracking-[0.25em] text-slate-500 font-mono-display">{label}</div>
    </div>
  );
}
function Dot() {
  return <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60" />;
}
function FeatureCard({ Icon, title, desc, link, className = "", testId, big = false, full = false }) {
  return (
    <Link to={link} data-testid={testId} className={`group relative glass rounded-3xl p-6 sm:p-7 overflow-hidden hover:border-cyan-400/30 transition-all hover:-translate-y-1.5 ${full ? "h-full flex flex-col justify-center" : ""} ${className}`}>
      <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-cyan-500/10 blur-3xl group-hover:bg-cyan-500/20 transition-colors" />
      <div className="relative">
        <div className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
          <Icon size={24} weight="duotone" className="text-cyan-300" />
        </div>
        <h3 className={`mt-5 font-display font-bold leading-tight ${big ? "text-xl sm:text-3xl" : "text-lg sm:text-xl"}`}>{title}</h3>
        <p className={`mt-3 text-slate-400 leading-relaxed ${big ? "text-sm sm:text-base max-w-md" : "text-sm"}`}>{desc}</p>
        <div className="mt-5 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
          Explore <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </Link>
  );
}
function MotionTile({ src, tall = false }) {
  return (
    <div className={`relative rounded-3xl overflow-hidden border border-white/10 group ${tall ? "h-full min-h-[260px] sm:min-h-[300px]" : "h-[150px] sm:h-[210px]"}`}>
      <img src={src} alt="" className="absolute inset-0 w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-[3s]" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-transparent to-transparent" />
    </div>
  );
}
