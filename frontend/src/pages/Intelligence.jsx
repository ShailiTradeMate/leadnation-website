import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
import { api } from "@/lib/api";
import { TrendUp, TrendDown, CurrencyCircleDollar, Drop, Lightning, Coins, FlowArrow } from "@phosphor-icons/react";

const ICONS = {
  gold: Coins, silver: Coins, oil: Drop, metal: FlowArrow, gas: Lightning,
};

export default function Intelligence() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/intelligence").then((r) => setData(r.data));
  }, []);

  return (
    <>
      <SEO
        title="Trade Intelligence: Rates, Commodities & Trends | Vametra AI"
        description="Trade intelligence hub for exporters and importers: gold, silver and oil prices, currency rates and global trade trends in one view, linked to duty, demand and buyer data for 56 countries."
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Trade Intelligence", path: "/intelligence" }]}
        path="/intelligence"
        keywords="gold price today, silver price, oil price brent wti, USD INR rate, USD AED rate, trade trends, global market intelligence"
      />

      <PageHero
        testIdPrefix="intel"
        label="Trade Intelligence Hub"
        title="Trade intelligence hub — gold, oil, currency and trade trends."
        sub="Commodity prices, currency rates and global trade trends — refreshed in real-time, distilled for traders."
      />

      {!data ? (
        <div className="max-w-7xl mx-auto px-6 sm:px-10 text-slate-400">Loading intelligence…</div>
      ) : (
        <>
          {/* Commodities */}
          <section className="max-w-7xl mx-auto px-6 sm:px-10">
            <h2 className="font-display font-bold text-2xl sm:text-3xl">Commodities</h2>
            <div className="mt-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.commodities.map((c, i) => {
                const Icon = ICONS[c.icon] || Coins;
                const up = c.change >= 0;
                return (
                  <div key={c.symbol} data-testid={`intel-commodity-${i}`} className="glass rounded-3xl p-6 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
                      <Icon size={22} weight="duotone" className="text-cyan-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="font-display font-bold">{c.name}</div>
                        <div className={`text-xs font-mono-display ${up ? "text-emerald-400" : "text-rose-400"} flex items-center gap-1`}>
                          {up ? <TrendUp size={12} weight="bold" /> : <TrendDown size={12} weight="bold" />}
                          {c.change > 0 ? "+" : ""}{c.change}%
                        </div>
                      </div>
                      <div className="text-2xl font-display font-extrabold mt-1">{c.price.toLocaleString()}</div>
                      <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">{c.unit}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Currencies */}
          <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-14">
            <div className="flex items-center gap-2">
              <CurrencyCircleDollar size={22} className="text-cyan-300" weight="duotone" />
              <h2 className="font-display font-bold text-2xl sm:text-3xl">Currency Rates</h2>
            </div>
            <div className="mt-6 glass-strong rounded-3xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
                  <tr><th className="text-left px-5 py-3">Pair</th><th className="text-right px-5 py-3">Rate</th><th className="text-right px-5 py-3">24h Δ</th></tr>
                </thead>
                <tbody>
                  {data.currencies.map((c, i) => {
                    const up = c.change >= 0;
                    return (
                      <tr key={c.pair} data-testid={`intel-fx-${i}`} className="border-t border-white/5">
                        <td className="px-5 py-3 font-mono-display tracking-widest">{c.pair}</td>
                        <td className="px-5 py-3 text-right font-display font-bold">{c.rate}</td>
                        <td className={`px-5 py-3 text-right ${up ? "text-emerald-400" : "text-rose-400"}`}>
                          {c.change > 0 ? "+" : ""}{c.change}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Trends */}
          <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-14">
            <h2 className="font-display font-bold text-2xl sm:text-3xl">Global Market Trends</h2>
            <div className="mt-6 grid md:grid-cols-2 gap-4">
              {data.trends.map((t, i) => (
                <div key={i} data-testid={`intel-trend-${i}`} className="glass rounded-3xl p-6">
                  <div className={`text-[10px] font-mono-display tracking-widest uppercase ${
                    t.impact === "high" ? "text-rose-300" : t.impact === "medium" ? "text-amber-300" : "text-cyan-300"
                  }`}>
                    Impact · {t.impact}
                  </div>
                  <div className="mt-2 font-display font-bold text-lg leading-tight">{t.title}</div>
                  <div className="mt-2 text-sm text-slate-400">{t.detail}</div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <AnswerFirst testId="intel-answer" className="!px-0 !max-w-none !mt-0 mb-10"
          answer="Trade intelligence is the set of numbers that decide whether a shipment is still profitable when it lands: commodity prices that move your input cost, the currency pair you invoice in, and the tariff and demand data for the destination. This hub puts the market indicators on one screen and links each to the duty, demand and buyer tools for {tariffCountries} countries."
          rows={[
            { label: "Indicators", value: "Gold · silver · oil · FX" },
            { label: "Tariff countries", value: "{tariffCountries}" },
            { label: "Export guides", value: "{guides}" },
          ]}
          source="Market feeds as shown on screen; World Bank WITS; OEC World (BACI)"
          links={[
            { to: "/tools/product-research", label: "Import demand by HS code" },
            { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
            { to: "/trade-news", label: "Global trade news" },
            { to: "/export", label: "Export guides" },
            { to: "/regions/europe", label: "Europe export hub" },
          ]} />
        <DownloadCTA />
      </section>
    </>
  );
}
