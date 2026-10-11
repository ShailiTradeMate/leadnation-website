import React from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";

/**
 * Rendered while live page data is in flight. It carries the route's real title,
 * canonical, breadcrumbs, h1 and substantive non-numeric content, so a crawler
 * snapshot taken during this window is still a legitimate indexable page.
 * It never states a tariff, demand figure or buyer count — those only exist once
 * the live data has arrived.
 */
export function GuideLoading({ product, country }) {
  const pn = titleize(product);
  const cn = titleize(country);
  const path = `/export/${product}/to/${country}`;
  const faqs = [
    {
      q: `What decides the import duty on ${pn} entering ${cn}?`,
      a: `The 6-digit HS code of your exact article, and the origin of the goods. ${cn} publishes an applied MFN rate against each HS line, and a lower preferential rate may exist if a trade agreement covers Indian origin. The live rate and its reporting year are read from World Bank WITS / UNCTAD TRAINS and shown on this guide.`,
    },
    {
      q: `Will a trade agreement automatically reduce my duty into ${cn}?`,
      a: `No. A preferential rate is conditional on the goods meeting that agreement's rules of origin and on a valid certificate of origin being presented at clearance in ${cn}. Price the applied rate as your base case and treat the preferential rate as upside you must document.`,
    },
    {
      q: `What documents travel with a shipment of ${pn} to ${cn}?`,
      a: `The commercial baseline is a commercial invoice, packing list, shipping bill and bill of lading or airway bill, plus a certificate of origin where you are claiming preference. Food, plant, pharmaceutical and chemical consignments additionally require the health, phytosanitary or regulatory certificate ${cn} specifies for that HS chapter.`,
    },
    {
      q: `What export incentive can an Indian exporter claim on ${pn}?`,
      a: `RoDTEP is the principal scheme, published by DGFT against the 8-digit code in Appendix 4R and issued as a transferable e-scrip; duty drawback may apply instead depending on the line. Both are claimed, not granted — the scheme has to be declared correctly on the shipping bill at the time of export.`,
    },
    {
      q: `How should I work out the landed cost in ${cn}?`,
      a: `Landed cost is your FOB price plus freight and insurance to the agreed Incoterm, plus ${cn}'s applied import duty, plus its own VAT or GST charged on the duty-inclusive value, plus clearance and handling. The Landed Cost Calculator builds that waterfall with live duty and exchange rates.`,
    },
    {
      q: `How do I find verified buyers of ${pn} in ${cn}?`,
      a: `Vametra Buyer Intelligence indexes contact-verified importer records by HS code and destination, sourced from official trade records and sanctions-screened before publication. Coverage is reported honestly per market — where no verified records exist for a lane, the guide says so rather than listing unvetted contacts.`,
    },
  ];
  return (
    <div data-testid="epc-loading" className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 pb-20">
      <SEO
        title={`Export ${pn} from India to ${cn} — Duty, HS Code & Buyers`}
        description={`${pn} export guide for ${cn}: applied import duty and HS code, measured import demand, documents, export incentives, verified buyers and landed cost — Vametra AI.`}
        path={path}
        type="article"
        faqs={faqs}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Export Guides", path: "/export" },
          { name: pn, path: `/export/${product}` },
          { name: cn, path },
        ]}
      />
      <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
        <Link to="/export" className="hover:text-cyan-300">Export guides</Link> ·{" "}
        <Link to={`/export/${product}`} className="hover:text-cyan-300">{pn}</Link> · {cn}
      </nav>
      <h1 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
        Export <span className="gradient-text">{pn}</span> from India to {cn}
      </h1>
      <p className="mt-5 text-[15px] text-slate-300 max-w-3xl leading-relaxed">
        Loading the live tariff, demand and buyer-coverage figures for this lane. Every number on
        this guide is read from a named source with its reporting year attached, so nothing is shown
        until it has actually been retrieved.
      </p>
      <AnswerBlock testId="epc-loading-answer" label="What this guide covers"
        title={`The four things that decide whether ${pn} works into ${cn}`}>
        <p>
          Classification first. Customs in {cn} assesses duty against the HS code, not the
          description on your invoice, and two articles that sound identical can sit in different
          lines with different tariffs and different certification regimes. Everything downstream
          depends on getting this right.
        </p>
        <p>
          Then the applied rate and whether Indian origin qualifies for anything better. Then{" "}
          {cn}'s own import tax, which is levied on the duty-inclusive value and therefore amplifies
          the tariff rather than sitting beside it — on many lanes it is the larger of the two
          numbers. Then real demand: whether {cn} actually imports meaningful volume of this HS
          code, measured from reported trade flows rather than inferred from the size of the market.
        </p>
        <p>
          Only after those four is buyer outreach worth the effort, because a quote you cannot hold
          is worse than no quote at all. This guide states all four for this specific lane, with the
          source and data year on every figure, and links the tools you need to vary the inputs.
        </p>
      </AnswerBlock>
      <PageFaq items={faqs} heading={`Exporting ${pn} to ${cn} — frequently asked questions`} testIdPrefix="epc-loading-faq" />
      <div className="max-w-7xl mx-auto mt-12 flex flex-wrap gap-2 text-sm">
        <Link to="/tools/duty-calculator" className="btn-ghost">Duty calculator</Link>
        <Link to="/tools/landed-cost-calculator" className="btn-ghost">Landed cost calculator</Link>
        <Link to="/tools/hsn-finder" className="btn-ghost">HS code finder</Link>
        <Link to={`/export/${product}`} className="btn-ghost">All {pn} markets</Link>
      </div>
    </div>
  );
}
