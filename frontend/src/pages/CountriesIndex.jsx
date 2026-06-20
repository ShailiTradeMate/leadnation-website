import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

export default function CountriesIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/country-profiles").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO
        title="Country Trade Profiles · Imports, Exports, Customs & Opportunities"
        description="Premium country-by-country trade profiles for India, UAE, USA, Australia, Armenia and 250+ markets — by LeadNation."
        path="/countries"
        keywords="country trade profiles, India trade, UAE trade, USA imports exports, Australia trade, Armenia EAEU"
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
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
