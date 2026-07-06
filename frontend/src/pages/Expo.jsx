import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { fetchEvents, fetchEventFilters } from "@/lib/api";
import { MapPin, CalendarBlank, Users, Buildings, Plus, Star, CircleNotch } from "@phosphor-icons/react";

const fmtDate = (s) => {
  if (!s) return "TBA";
  try { return new Date(s).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); }
  catch (_) { return s; }
};
const range = (a, b) => (a && b ? `${fmtDate(a)} – ${fmtDate(b)}` : fmtDate(a || b));

const selCls = "glass rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-400/40 bg-[#0a1024]";

export default function Expo() {
  const [items, setItems] = useState([]);
  const [filters, setFilters] = useState({ categories: [], industries: [], countries: [], audiences: [] });
  const [sel, setSel] = useState({ category: "", country: "", industry: "", q: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchEventFilters().then(setFilters).catch(() => {}); }, []);
  useEffect(() => {
    setLoading(true);
    const params = Object.fromEntries(Object.entries(sel).filter(([, v]) => v));
    fetchEvents(params).then((d) => setItems(d.items || [])).finally(() => setLoading(false));
  }, [sel]);

  const featured = useMemo(() => items.filter((i) => i.featured), [items]);
  const rest = useMemo(() => items.filter((i) => !i.featured), [items]);

  return (
    <>
      <SEO
        title="Global Trade Expos & Events · Live Calendar"
        description="Every major trade expo, import/export fair, business and industry event worldwide — filtered by sector, country and date. List your own event to reach exporters and buyers."
        path="/expo"
        keywords="trade expo 2026, import export events, Gulfood, Canton Fair, Hannover Messe, list my trade event, global expo calendar"
      />
      <PageHero
        testIdPrefix="expo"
        label="Expo & Events Engine"
        title="Every trade event on earth — on one calendar."
        sub="Track global expos, import/export fairs, business, agriculture and industry events by sector, country and date. Have an event? List it and reach thousands of exporters, importers and buyers."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        {/* Filter bar + List CTA */}
        <div className="glass-strong rounded-3xl p-4 sm:p-5 mb-8 flex flex-wrap items-end gap-3" data-testid="expo-filters">
          <div className="flex-1 min-w-[180px]">
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Search</div>
            <input data-testid="expo-search" value={sel.q} onChange={(e) => setSel({ ...sel, q: e.target.value })}
              placeholder="Event, city…" className={`${selCls} w-full`} />
          </div>
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Category</div>
            <select data-testid="expo-filter-category" value={sel.category} onChange={(e) => setSel({ ...sel, category: e.target.value })} className={selCls}>
              <option value="">All categories</option>
              {filters.categories.map((c) => <option key={c} value={c} className="bg-[#0a1024]">{c}</option>)}
            </select>
          </div>
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Country</div>
            <select data-testid="expo-filter-country" value={sel.country} onChange={(e) => setSel({ ...sel, country: e.target.value })} className={selCls}>
              <option value="">All countries</option>
              {filters.countries.map((c) => <option key={c} value={c} className="bg-[#0a1024]">{c}</option>)}
            </select>
          </div>
          <div>
            <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400 mb-1">Industry</div>
            <select data-testid="expo-filter-industry" value={sel.industry} onChange={(e) => setSel({ ...sel, industry: e.target.value })} className={selCls}>
              <option value="">All industries</option>
              {filters.industries.map((c) => <option key={c} value={c} className="bg-[#0a1024]">{c}</option>)}
            </select>
          </div>
          <Link to="/expo/submit" data-testid="expo-list-cta" className="btn-primary ml-auto"><Plus size={16} weight="bold" /> List your event</Link>
        </div>

        {loading ? (
          <div className="glass rounded-3xl p-16 text-center text-slate-400"><CircleNotch size={22} className="animate-spin inline" /> Loading events…</div>
        ) : items.length === 0 ? (
          <div className="glass rounded-3xl p-16 text-center">
            <div className="text-slate-300 font-display font-bold text-lg">No events match your filters.</div>
            <Link to="/expo/submit" className="btn-primary mt-4 inline-flex"><Plus size={16} weight="bold" /> Be the first — list an event</Link>
          </div>
        ) : (
          <>
            {featured.length > 0 && (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
                {featured.map((e, i) => <EventCard key={e.id} e={e} i={i} featured />)}
              </div>
            )}
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {rest.map((e, i) => <EventCard key={e.id} e={e} i={i} />)}
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

function EventCard({ e, i, featured }) {
  return (
    <Link to={`/expo/${e.id}`} data-testid={`expo-card-${i}`}
      className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group block">
      <div className="relative h-48 overflow-hidden">
        <img src={e.image || "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80"}
          alt={e.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-[#0a0f24]/40 to-transparent" />
        <div className="absolute top-3 left-3 glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{e.category}</div>
        {featured && <div className="absolute top-3 right-3 flex items-center gap-1 bg-amber-400/20 border border-amber-300/30 px-2 py-1 rounded-full text-[10px] text-amber-200"><Star size={10} weight="fill" /> Featured</div>}
        <div className="absolute bottom-3 left-3 right-3">
          <h3 className="font-display font-bold text-lg leading-tight text-white drop-shadow line-clamp-2">{e.name}</h3>
        </div>
      </div>
      <div className="p-5 space-y-2.5 text-sm">
        <div className="flex items-center gap-2 text-slate-300"><CalendarBlank size={14} className="text-cyan-300" weight="duotone" />{range(e.startDate, e.endDate)}</div>
        <div className="flex items-center gap-2 text-slate-300"><MapPin size={14} className="text-cyan-300" weight="duotone" />{[e.city, e.country].filter(Boolean).join(", ")}</div>
        {e.industry && <div className="flex items-center gap-2 text-slate-300"><Buildings size={14} className="text-cyan-300" weight="duotone" />{e.industry}</div>}
        {e.audience && <div className="flex items-center gap-2 text-slate-400 text-xs"><Users size={13} className="text-cyan-300" weight="duotone" />{e.audience}</div>}
      </div>
    </Link>
  );
}
