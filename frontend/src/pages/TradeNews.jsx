import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import { fetchTradeNews } from "@/lib/api";
import { Clock, ArrowUpRight } from "@phosphor-icons/react";

export default function TradeNews() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetchTradeNews().then(setItems);
  }, []);

  return (
    <>
      <PageHero
        testIdPrefix="news"
        label="Trade News Engine"
        title="The world's trade pulse — without the noise."
        sub="Curated, deduped, signal-only. Track tariffs, lanes, FTAs and policy in one editorial feed."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        {items.length > 0 && (
          <article
            data-testid="news-featured"
            className="relative rounded-3xl overflow-hidden border border-white/10 mb-8 group cursor-pointer"
          >
            <img src={items[0].image} alt="" className="absolute inset-0 w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-[2s]" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-[#050816]/70 to-transparent" />
            <div className="relative p-8 sm:p-12 h-[420px] flex flex-col justify-end">
              <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">{items[0].category}</div>
              <h2 className="font-display font-extrabold tracking-tight text-3xl sm:text-5xl mt-3 max-w-3xl leading-[1.08]">
                {items[0].title}
              </h2>
              <p className="mt-3 text-slate-300 max-w-2xl">{items[0].excerpt}</p>
              <div className="mt-5 flex items-center gap-4 text-xs text-slate-400 font-mono-display tracking-widest uppercase">
                <span className="flex items-center gap-1"><Clock size={12} />{items[0].date}</span>
                <span>·</span>
                <span>{items[0].source}</span>
              </div>
            </div>
          </article>
        )}

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.slice(1).map((n, i) => (
            <article
              key={n.id}
              data-testid={`news-card-${i}`}
              className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group cursor-pointer"
            >
              <div className="relative h-48 overflow-hidden">
                <img src={n.image} alt="" className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                <div className="absolute top-3 left-3 glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">
                  {n.category}
                </div>
              </div>
              <div className="p-5">
                <h3 className="font-display font-bold text-lg leading-tight">{n.title}</h3>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed line-clamp-2">{n.excerpt}</p>
                <div className="mt-4 flex items-center justify-between text-[11px] text-slate-500 font-mono-display tracking-widest uppercase">
                  <span>{n.date}</span>
                  <ArrowUpRight size={14} className="text-cyan-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
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
