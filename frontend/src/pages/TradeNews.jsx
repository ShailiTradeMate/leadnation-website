import React, { useEffect, useMemo, useRef, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { fetchNewsFeed, fetchNewsTopics, fetchNewsCountries } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Link } from "react-router-dom";
import { Clock, ArrowUpRight, Broadcast, Sparkle, PencilSimple, CircleNotch, UserFocus, MagnifyingGlass, ArrowsClockwise, GlobeHemisphereWest } from "@phosphor-icons/react";

const Badge = ({ kind }) => {
  const map = {
    live: { I: Broadcast, t: "Live", c: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" },
    ai: { I: Sparkle, t: "AI", c: "text-violet-300 border-violet-400/30 bg-violet-500/10" },
    admin: { I: PencilSimple, t: "Editorial", c: "text-cyan-300 border-cyan-400/30 bg-cyan-500/10" },
  };
  const b = map[kind] || map.ai;
  return <span className={`inline-flex items-center gap-1 text-[9px] font-mono-display uppercase tracking-widest px-2 py-0.5 rounded-full border ${b.c}`}><b.I size={9} weight="fill" />{b.t}</span>;
};

const stamp = (iso) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }); }
  catch (_) { return "—"; }
};

export default function TradeNews() {
  const { isAuthed } = useAuth();
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({ personalized: false, context: {}, live: false, lastUpdated: null });
  const [topics, setTopics] = useState([{ key: "all", label: "Top Stories" }]);
  const [countries, setCountries] = useState([]);
  const [topic, setTopic] = useState("all");
  const [country, setCountry] = useState("");
  const [countryTouched, setCountryTouched] = useState(false);
  const [term, setTerm] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const debounce = useRef(null);

  useEffect(() => {
    fetchNewsTopics().then((d) => setTopics(d.topics || [])).catch(() => {});
    fetchNewsCountries().then((d) => setCountries(d.countries || [])).catch(() => {});
  }, []);

  useEffect(() => {
    clearTimeout(debounce.current);
    debounce.current = setTimeout(() => setQuery(term.trim()), 450);
    return () => clearTimeout(debounce.current);
  }, [term]);

  const load = (refresh = false) => {
    setLoading(true);
    return fetchNewsFeed({ topic, country, q: query, limit: 24, refresh: refresh ? 1 : 0 })
      .then((d) => {
        setItems(d.items || []);
        setMeta(d);
        // signed-in users get their profile country pre-selected (they can change it)
        if (!countryTouched && !country && d.context?.countryCode) setCountry(d.context.countryCode);
      })
      .finally(() => setLoading(false));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(false); }, [topic, country, query, isAuthed]);

  const refresh = async () => {
    setRefreshing(true);
    await load(true);
    setRefreshing(false);
  };

  const featured = items[0];
  const topicLabel = useMemo(() => (topics.find((t) => t.key === topic)?.label || "Top Stories"), [topics, topic]);

  return (
    <>
      <SEO
        title="Global Trade News · Tariffs, Geopolitics, Currency, Shipping & Business"
        description="Live global news for traders — tariffs, trade deals, currency, geopolitics, conflict, energy, shipping and business events. Filter by country and topic, updated daily."
        path="/trade-news"
        keywords="trade news today, global business news, tariff news, geopolitics news, currency news, shipping news, country news filter"
      />
      <PageHero
        testIdPrefix="news"
        label="Trade News Engine"
        title="The world's trade pulse — in real time."
        sub="Global news that moves business: tariffs, geopolitics, currency, energy, shipping, policy and major events. Filter by country and topic — refreshed daily, newest first."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        {/* Topic tabs */}
        <div className="flex gap-2 flex-wrap mb-4" data-testid="news-topics">
          {topics.map((t) => (
            <button key={t.key} data-testid={`news-topic-${t.key}`} onClick={() => setTopic(t.key)}
              className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all ${topic === t.key ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Filter bar */}
        <div className="glass-strong rounded-3xl p-4 sm:p-5 mb-6 flex flex-wrap items-end gap-3" data-testid="news-filters">
          <div className="flex-1 min-w-[200px]">
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Search any news</div>
            <div className="glass rounded-xl flex items-center gap-2 px-3 py-2.5">
              <MagnifyingGlass size={16} className="text-cyan-300 shrink-0" />
              <input data-testid="news-search" value={term} onChange={(e) => setTerm(e.target.value)}
                placeholder="e.g. steel tariff, Red Sea, rupee, CBAM"
                className="flex-1 bg-transparent outline-none text-sm text-white placeholder:text-slate-500" />
            </div>
          </div>
          <div className="min-w-[200px]">
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Country</div>
            <select data-testid="news-country" value={country}
              onChange={(e) => { setCountryTouched(true); setCountry(e.target.value); }}
              className="glass rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-400/40 bg-[#0a1024] w-full">
              <option value="" className="bg-[#0a1024]">🌐 Global</option>
              {countries.map((c) => <option key={c.code} value={c.code} className="bg-[#0a1024]">{c.name}</option>)}
            </select>
          </div>
          <button data-testid="news-refresh" onClick={refresh} disabled={refreshing}
            className="btn-ghost !py-2.5 text-xs disabled:opacity-50">
            <ArrowsClockwise size={14} weight="bold" className={refreshing ? "animate-spin" : ""} /> Refresh
          </button>
        </div>

        {/* Context / freshness bar */}
        <div className="flex flex-wrap items-center gap-3 mb-6 text-xs" data-testid="news-context-bar">
          <span className="glass rounded-full px-3 py-1.5 text-slate-300 flex items-center gap-2" data-testid="news-scope">
            <GlobeHemisphereWest size={13} weight="duotone" className="text-cyan-300" />
            {topicLabel} · {meta.country?.name || "Global"}{query ? ` · “${query}”` : ""}
          </span>
          <span className="glass rounded-full px-3 py-1.5 text-slate-400 flex items-center gap-2" data-testid="news-last-updated">
            <Clock size={13} /> Updated {stamp(meta.lastUpdated)}
          </span>
          {meta.live && <span className="text-[10px] text-emerald-300 font-mono-display uppercase tracking-widest flex items-center gap-1"><Broadcast size={11} weight="fill" /> Live feed</span>}
          {meta.personalized ? (
            <span className="glass rounded-full px-3 py-1.5 text-emerald-300 flex items-center gap-2" data-testid="news-personalized">
              <UserFocus size={13} weight="duotone" /> Pre-set to your profile country
            </span>
          ) : (
            <Link to="/login" className="glass rounded-full px-3 py-1.5 text-slate-300 hover:text-cyan-300 flex items-center gap-2" data-testid="news-signin-hint">
              <UserFocus size={13} weight="duotone" /> Sign in for news tailored to your country & products
            </Link>
          )}
        </div>

        {loading ? (
          <div className="glass rounded-3xl p-16 text-center text-slate-400" data-testid="news-loading"><CircleNotch size={22} className="animate-spin inline" /> Loading latest trade news…</div>
        ) : items.length === 0 ? (
          <div className="glass rounded-3xl p-16 text-center text-slate-400" data-testid="news-empty">No stories match this filter. Try another topic or country.</div>
        ) : (
          <>
            {featured && (
              <Link to={`/trade-news/${featured.id}`} data-testid="news-featured"
                className="block relative rounded-3xl overflow-hidden border border-white/10 mb-8 group cursor-pointer">
                <img src={featured.image} alt="" className="absolute inset-0 w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-[#050816]/70 to-transparent" />
                <div className="relative p-8 sm:p-12 h-[420px] flex flex-col justify-end">
                  <div className="flex items-center gap-2">
                    <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">{featured.category}</div>
                    <Badge kind={featured.badge} />
                  </div>
                  <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-5xl mt-3 max-w-3xl leading-[1.08]">{featured.title}</h2>
                  <p className="mt-3 text-slate-300 max-w-2xl line-clamp-2">{featured.excerpt}</p>
                  <div className="mt-5 flex items-center gap-4 text-xs text-slate-400 font-mono-display tracking-widest uppercase">
                    <span className="flex items-center gap-1"><Clock size={12} />{featured.date}</span><span>·</span><span>{featured.source}</span>
                    {featured.country && featured.country !== "Global" && <><span>·</span><span>{featured.country}</span></>}
                  </div>
                </div>
              </Link>
            )}

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
              {items.slice(1).map((n, i) => (
                <Link to={`/trade-news/${n.id}`} key={n.id} data-testid={`news-card-${i}`}
                  className="block glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group cursor-pointer">
                  <div className="relative h-48 overflow-hidden">
                    <img src={n.image} alt="" className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                    <div className="absolute top-3 left-3 flex items-center gap-2">
                      <span className="glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{n.category}</span>
                      <Badge kind={n.badge} />
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-display font-bold text-lg leading-tight line-clamp-2">{n.title}</h3>
                    <p className="mt-2 text-sm text-slate-400 leading-relaxed line-clamp-2">{n.excerpt}</p>
                    <div className="mt-4 flex items-center justify-between text-[11px] text-slate-500 font-mono-display tracking-widest uppercase">
                      <span className="flex items-center gap-1"><Clock size={11} />{n.date}</span>
                      <ArrowUpRight size={14} className="text-cyan-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
