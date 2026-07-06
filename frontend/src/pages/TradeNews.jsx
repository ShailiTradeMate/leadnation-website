import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { fetchNewsFeed } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Link } from "react-router-dom";
import { Clock, ArrowUpRight, Broadcast, Sparkle, PencilSimple, CircleNotch, UserFocus } from "@phosphor-icons/react";

const Badge = ({ kind }) => {
  const map = {
    live: { I: Broadcast, t: "Live", c: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" },
    ai: { I: Sparkle, t: "AI", c: "text-violet-300 border-violet-400/30 bg-violet-500/10" },
    admin: { I: PencilSimple, t: "Editorial", c: "text-cyan-300 border-cyan-400/30 bg-cyan-500/10" },
  };
  const b = map[kind] || map.ai;
  return <span className={`inline-flex items-center gap-1 text-[9px] font-mono-display uppercase tracking-widest px-2 py-0.5 rounded-full border ${b.c}`}><b.I size={9} weight="fill" />{b.t}</span>;
};

export default function TradeNews() {
  const { isAuthed } = useAuth();
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({ personalized: false, context: {}, categories: ["All"], live: false });
  const [cat, setCat] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchNewsFeed({ category: cat, limit: 24 })
      .then((d) => { setItems(d.items || []); setMeta(d); })
      .finally(() => setLoading(false));
  }, [cat, isAuthed]);

  const featured = items[0];

  return (
    <>
      <SEO
        title="Global Trade News · Real-time Tariffs, FTAs, Logistics & Policy"
        description="Real-time, personalized global trade news for exporters and importers — tariffs, FTAs, customs, logistics and policy, tailored to your country and role."
        path="/trade-news"
        keywords="trade news today, real time trade news, India exports news, customs policy update, FTA news, supply chain news"
      />
      <PageHero
        testIdPrefix="news"
        label="Trade News Engine"
        title="The world's trade pulse — in real time."
        sub="Live global trade news, personalized to your country and role when you're signed in. Tariffs, lanes, FTAs and policy — the signal, not the noise."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        {/* Personalization banner + category filter */}
        <div className="flex flex-wrap items-center gap-3 mb-6" data-testid="news-context-bar">
          {meta.personalized ? (
            <div className="glass rounded-full px-4 py-2 text-xs text-emerald-300 flex items-center gap-2" data-testid="news-personalized">
              <UserFocus size={14} weight="duotone" /> Personalized for {meta.context?.country || "you"}{meta.context?.role ? ` · ${meta.context.role}` : ""}
            </div>
          ) : (
            <Link to="/login" className="glass rounded-full px-4 py-2 text-xs text-slate-300 hover:text-cyan-300 flex items-center gap-2" data-testid="news-signin-hint">
              <UserFocus size={14} weight="duotone" /> Sign in for news tailored to your country & products
            </Link>
          )}
          {meta.live && <span className="text-[10px] text-emerald-300 font-mono-display uppercase tracking-widest flex items-center gap-1"><Broadcast size={11} weight="fill" /> Live feed active</span>}
          <div className="flex gap-2 flex-wrap ml-auto">
            {(meta.categories || ["All"]).map((c) => (
              <button key={c} data-testid={`news-cat-${c.toLowerCase().replace(/\s+/g, "-").replace(/&/g, "and")}`} onClick={() => setCat(c)}
                className={`px-3 py-1.5 rounded-full text-[11px] font-medium transition-all ${cat === c ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
                {c}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="glass rounded-3xl p-16 text-center text-slate-400"><CircleNotch size={22} className="animate-spin inline" /> Loading latest trade news…</div>
        ) : items.length === 0 ? (
          <div className="glass rounded-3xl p-16 text-center text-slate-400">No news right now — check back shortly.</div>
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
                      <span>{n.date}</span>
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
