import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

const FAQ = [
  {
    q: "What does a country trade profile tell me that a guide does not?",
    a: "A country profile is market-level: what that economy imports and exports overall, its customs regime, the trade agreements it is party to, and the compliance culture you will meet at the border. A product-market export guide is lane-level: the applied tariff and measured demand for one HS code into that one country.",
  },
  {
    q: "Which markets are covered?",
    a: "Tariff and demand data is available for the 56 reporting countries in World Bank WITS / UNCTAD TRAINS, and we hold reference trade data for 195+ markets. Full written profiles are published where we can evidence the customs and agreement detail rather than paraphrase it.",
  },
  {
    q: "How do I check the import duty into a specific country?",
    a: "Open the Customs Duty Calculator, enter the 6-digit HS code and set your origin and that destination. You get the applied MFN rate plus any preferential rate your origin qualifies for, read live from World Bank WITS / UNCTAD TRAINS, with the data year shown beside the rate.",
  },
  {
    q: "Do free trade agreements automatically lower my duty?",
    a: "No. A preferential rate only applies if your goods meet that agreement's rules of origin and you present valid origin documentation at clearance. The calculator shows the preferential rate where one exists for your origin, but qualifying for it is a documentation exercise, not an automatic entitlement.",
  },
  {
    q: "Is this useful if I am importing rather than exporting?",
    a: "Yes. The duty and landed-cost engines are symmetric — set the origin to your supplier's country and the destination to your own, and you get the tariff, tax stack and landed cost you will pay, along with the documentation your clearance will require.",
  },
];

export default function CountriesIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/country-profiles").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO
        title="Country Trade Profiles · Imports, Exports, Customs & Opportunities"
        description="Country-by-country trade profiles — imports, exports, customs duties, trade agreements, compliance and live news for India, UAE, USA, Australia, Armenia and 250+ markets."
        path="/countries"
        keywords="country trade profiles, India trade, UAE trade, USA imports exports, Australia trade, Armenia EAEU"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Countries", path: "/countries" }]}
        faqs={FAQ}
      />
      <PageHero
        testIdPrefix="countries"
        label="Trade Country Profiles"
        title="Pick a market. See the playbook."
        sub="Every country profile gives you imports, exports, customs duties, FTAs, compliance and live news in one screen."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {list.map((c) => (
            <Link
              key={c.slug}
              to={`/countries/${c.slug}`}
              data-testid={`countries-card-${c.slug}`}
              className="glass rounded-3xl p-7 hover:border-cyan-400/30 hover:-translate-y-1 transition-all group"
            >
              <div className="text-5xl">{c.flag}</div>
              <h2 className="mt-4 font-display font-extrabold text-2xl">{c.name}</h2>
              <p className="mt-2 text-sm text-slate-400">{c.tagline}</p>
              <div className="mt-5 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                Open profile <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>
      <AnswerBlock testId="countries-answer" label="How to use these profiles"
        title="A market is a customs regime before it is an opportunity">
        <p>
          Exporters usually pick markets by demand and then discover the regime. It is cheaper to
          do it the other way round. The tariff schedule, the trade agreements a country belongs
          to, its import tax stack and its documentation culture are all knowable before you spend
          anything on samples or travel.
        </p>
        <p>
          That is what these profiles front-load. Read the regime, confirm whether your origin has
          preferential access and whether you can realistically meet the rules of origin, then size
          the demand for your specific HS code. A market with a modest import volume and zero
          preferential duty will frequently beat a large market with a double-digit applied rate.
        </p>
        <p>
          Rates and trade values are read from World Bank WITS / UNCTAD TRAINS and OEC World /
          CEPII BACI with the data year attached. Where a source holds no record for a
          country-product pair, the page states that rather than interpolating a figure.
        </p>
      </AnswerBlock>
      <PageFaq items={FAQ} testIdPrefix="countries-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
