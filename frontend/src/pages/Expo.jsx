import React, { useEffect, useMemo, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import { fetchExpos } from "@/lib/api";
import { MapPin, CalendarBlank, Users } from "@phosphor-icons/react";

export default function Expo() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    fetchExpos().then(setItems);
  }, []);

  const categories = useMemo(() => {
    const set = new Set(items.map((i) => i.category));
    return ["All", ...Array.from(set)];
  }, [items]);

  const filtered = filter === "All" ? items : items.filter((i) => i.category === filter);

  return (
    <>
      <PageHero
        testIdPrefix="expo"
        label="Expo & Events Engine"
        title="Every trade show, on one calendar."
        sub="Track every meaningful global expo, summit and trade fair — by sector, city or date. Plan your year, not just your trip."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex gap-2 flex-wrap mb-8">
          {categories.map((c) => (
            <button
              key={c}
              data-testid={`expo-filter-${c.toLowerCase().replace(/\s+/g, "-")}`}
              onClick={() => setFilter(c)}
              className={`px-4 py-2 rounded-full text-xs font-medium transition-all ${
                filter === c
                  ? "tab-active text-white"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((e, i) => (
            <article
              key={e.id}
              data-testid={`expo-card-${i}`}
              className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group"
            >
              <div className="relative h-48 overflow-hidden">
                <img src={e.image} alt={e.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-[#0a0f24]/40 to-transparent" />
                <div className="absolute top-3 left-3 glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">
                  {e.category}
                </div>
                <div className="absolute bottom-3 left-3 right-3">
                  <h3 className="font-display font-bold text-lg leading-tight text-white drop-shadow">{e.name}</h3>
                </div>
              </div>
              <div className="p-5 space-y-2.5 text-sm">
                <div className="flex items-center gap-2 text-slate-300">
                  <CalendarBlank size={14} className="text-cyan-300" weight="duotone" />
                  {e.date}
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <MapPin size={14} className="text-cyan-300" weight="duotone" />
                  {e.city}, {e.country}
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Users size={14} className="text-cyan-300" weight="duotone" />
                  {e.attendees} attendees
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
