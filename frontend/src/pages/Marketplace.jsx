import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import { Card } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { PlayCircle, ShoppingBag, ChatCenteredText } from "@phosphor-icons/react";

export default function Marketplace() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/marketplace").then((r) => setData(r.data)); }, []);

  return (
    <>
      <SEO title="LeadNation Marketplace · Product Listings, Reels & RFQs"
        description="Preview the LeadNation Marketplace — verified product listings, trade reels and live buyer RFQs from across the world."
        path="/marketplace"
        keywords="trade marketplace India, B2B marketplace, supplier listings, RFQ, buyer requests"
      />
      <PageHero testIdPrefix="mp" label="LeadNation Marketplace"
        title="A live shop window for global trade."
        sub="Verified listings, trade reels and live buyer RFQs — the LeadNation marketplace is where deals get done."
      />

      {data && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 space-y-10">
          <div>
            <div className="flex items-center gap-2 mb-4"><ShoppingBag size={20} className="text-cyan-300" weight="duotone" /><h2 className="font-display font-bold text-2xl">Featured listings</h2></div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.listings.map((l, i) => (
                <div key={l.id} data-testid={`mp-listing-${i}`} className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
                  <div className="h-40 relative overflow-hidden">
                    <img src={l.image} alt={l.title} className="absolute inset-0 w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                  </div>
                  <div className="p-5">
                    <div className="font-display font-bold">{l.title}</div>
                    <div className="text-xs text-slate-400 mt-1">{l.supplier}</div>
                    <div className="mt-3 flex items-center justify-between">
                      <div className="text-sm font-display font-bold text-cyan-300">{l.price}</div>
                      <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-500">MOQ {l.moq}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-4"><PlayCircle size={20} className="text-cyan-300" weight="duotone" /><h2 className="font-display font-bold text-2xl">Trade reels</h2></div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {data.reels.map((r, i) => (
                <div key={r.id} data-testid={`mp-reel-${i}`} className="relative rounded-3xl overflow-hidden h-72 group cursor-pointer">
                  <img src={r.thumb} alt={r.title} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-[#050816]/40 to-transparent" />
                  <PlayCircle size={56} weight="fill" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/90" />
                  <div className="absolute bottom-3 left-3 right-3 text-sm font-display font-bold drop-shadow">{r.title}</div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-4"><ChatCenteredText size={20} className="text-cyan-300" weight="duotone" /><h2 className="font-display font-bold text-2xl">Live buyer requests</h2></div>
            <div className="space-y-3">
              {data.buyerRequests.map((b, i) => (
                <div key={b.id} data-testid={`mp-rfq-${i}`} className="glass rounded-2xl px-5 py-4 flex items-center gap-4">
                  <div className="text-2xl">{b.country}</div>
                  <div className="flex-1 text-sm">{b.title}</div>
                  <a href="https://wa.me/918237161088" target="_blank" rel="noopener noreferrer" className="btn-ghost !py-2 !px-4 text-xs">Reply on WhatsApp</a>
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
