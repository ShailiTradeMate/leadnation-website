import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { Users } from "@phosphor-icons/react";

export default function Network() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/network").then((r) => setData(r.data)); }, []);

  return (
    <>
      <SEO title="LeadNation Network · The Global Trade Community"
        description="48,000+ verified exporters, importers, CHAs, logistics agents and buyers — the world's most active trade network."
        path="/network"
        keywords="trade network, exporter network, importer network, CHA directory, logistics network"
      />
      <PageHero testIdPrefix="nw" label="LeadNation Network"
        title="The world's trade community."
        sub="Connect with verified exporters, importers, CHAs, logistics agents and buyers in every major market."
      />

      {data && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 space-y-10">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.stats.map((s, i) => (
              <div key={i} data-testid={`nw-stat-${i}`} className="glass-strong rounded-3xl p-6">
                <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-cyan-300">{s.label}</div>
                <div className="mt-2 font-display font-extrabold text-3xl gradient-text">{s.value}</div>
              </div>
            ))}
          </div>

          <div>
            <div className="flex items-center gap-2 mb-4"><Users size={20} className="text-cyan-300" weight="duotone" /><h2 className="font-display font-bold text-2xl">Featured members</h2></div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.members.map((m, i) => (
                <div key={i} data-testid={`nw-member-${i}`} className="glass rounded-3xl p-5 flex items-center gap-4">
                  <img src={m.avatar} alt={m.name} className="w-14 h-14 rounded-full border border-white/10 object-cover" />
                  <div>
                    <div className="font-display font-bold">{m.name}</div>
                    <div className="text-xs text-cyan-300 font-mono-display tracking-widest uppercase mt-0.5">{m.role}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{m.city}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}
