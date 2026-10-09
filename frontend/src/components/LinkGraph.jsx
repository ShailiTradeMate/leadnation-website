import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Package, Globe, Path, Buildings } from "@phosphor-icons/react";

const money = (v) => {
  if (!v) return "";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${(v / 1e3).toFixed(0)}K`;
};

const Chip = ({ to, children, testId }) => (
  <Link to={to} data-testid={testId}
    className="text-[12px] glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">
    {children}
  </Link>
);

/** Sibling links on an export guide so no page is a dead end. */
export const RelatedGuides = ({ related, productName, countryName }) => {
  if (!related) return null;
  const { sameProductMarkets = [], sameCountryProducts = [] } = related;
  return (
    <section className="mt-14 grid md:grid-cols-2 gap-5" data-testid="epc-related">
      <div className="glass-strong rounded-3xl p-6">
        <div className="flex items-center gap-2 mb-1">
          <Globe size={16} weight="duotone" className="text-cyan-300" />
          <h2 className="font-display font-bold text-lg">{productName} to other markets</h2>
        </div>
        <p className="text-[12px] text-slate-400 mb-4">Same product, ranked by that market's own import demand.</p>
        <div className="flex flex-wrap gap-1.5">
          {sameProductMarkets.map((m) => (
            <Chip key={m.url} to={m.url} testId={`epc-same-product-${m.countrySlug}`}>
              {m.country} <span className="text-slate-500">{m.dutyRate != null ? `${m.dutyRate}%` : ""} {money(m.importsUSD)}</span>
            </Chip>
          ))}
        </div>
        <Link to={related.productHub} data-testid="epc-product-hub"
          className="mt-4 inline-flex items-center gap-1.5 text-sm text-cyan-300 hover:underline">
          <Package size={14} /> All {productName} markets <ArrowRight size={12} />
        </Link>
      </div>

      <div className="glass-strong rounded-3xl p-6">
        <div className="flex items-center gap-2 mb-1">
          <Buildings size={16} weight="duotone" className="text-cyan-300" />
          <h2 className="font-display font-bold text-lg">Other products to {countryName}</h2>
        </div>
        <p className="text-[12px] text-slate-400 mb-4">Same market, other product families we publish.</p>
        <div className="flex flex-wrap gap-1.5">
          {sameCountryProducts.map((m) => (
            <Chip key={m.url} to={m.url} testId={`epc-same-country-${m.productSlug}`}>
              {m.product} <span className="text-slate-500">{m.dutyRate != null ? `${m.dutyRate}%` : ""}</span>
            </Chip>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {related.regionHub && (
            <Link to={related.regionHub} data-testid="epc-related-region" className="text-sm text-cyan-300 hover:underline inline-flex items-center gap-1.5">
              <Globe size={14} /> {related.regionName} hub
            </Link>
          )}
          {related.corridor && (
            <Link to={related.corridor} data-testid="epc-related-corridor" className="text-sm text-cyan-300 hover:underline inline-flex items-center gap-1.5">
              <Path size={14} /> Trade corridor
            </Link>
          )}
          {related.countryProfile && (
            <Link to={related.countryProfile} data-testid="epc-related-profile" className="text-sm text-cyan-300 hover:underline inline-flex items-center gap-1.5">
              <Buildings size={14} /> Country profile
            </Link>
          )}
          {related.marketingProduct && (
            <Link to={related.marketingProduct} data-testid="epc-related-product-page" className="text-sm text-cyan-300 hover:underline inline-flex items-center gap-1.5">
              <Package size={14} /> Product overview
            </Link>
          )}
        </div>
      </div>
    </section>
  );
};

/** Published guides for one market — used by country profiles and corridor pages. */
export const CountryGuides = ({ data, heading = "Export guides for this market", testIdPrefix = "cg" }) => {
  if (!data || !data.total) return null;
  return (
    <section className="glass-strong rounded-3xl p-6" data-testid={`${testIdPrefix}-root`}>
      <div className="flex items-center gap-2 mb-1">
        <Package size={16} weight="duotone" className="text-cyan-300" />
        <h2 className="font-display font-bold text-lg">{heading}</h2>
      </div>
      <p className="text-[12px] text-slate-400 mb-4">
        {data.total} published guide{data.total === 1 ? "" : "s"} for {data.country} — applied duty, real demand,
        documents and buyer coverage.
      </p>
      <div className="space-y-1.5">
        {data.guides.map((g) => (
          <Link key={g.url} to={g.url} data-testid={`${testIdPrefix}-${g.productSlug}`}
            className="flex items-center gap-2 text-[13px] text-slate-300 hover:text-cyan-300 transition-colors">
            <ArrowRight size={12} className="text-cyan-400/70 shrink-0" />
            <span className="truncate">{g.product}</span>
            <span className="ml-auto text-[11px] text-slate-500 shrink-0">
              {g.dutyRate != null ? `${g.dutyRate}%` : "—"} {money(g.importsUSD)}
            </span>
          </Link>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {data.regionHub && <Chip to={data.regionHub} testId={`${testIdPrefix}-region`}>Region hub</Chip>}
        <Chip to="/export" testId={`${testIdPrefix}-all`}>All export guides</Chip>
      </div>
    </section>
  );
};
