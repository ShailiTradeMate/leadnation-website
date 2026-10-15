import React from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import DownloadCTA from "@/components/DownloadCTA";
import { BRAND_NAME, LEGAL_NAME, TAGLINE, SITE_URL, SOCIALS, EMAIL, FOUNDED, FOUNDER, HQ } from "@/lib/brand";
import { ArrowRight, Buildings, Globe, ShieldCheck, Database } from "@phosphor-icons/react";

const FAQ = [
  {
    q: "What is Vametra AI?",
    a: "Vametra AI is an AI-powered global trade intelligence platform for exporters, importers, suppliers, customs house agents and trade consultants. It unifies customs duty lookup, HS and HSN classification, free trade agreement analysis, landed cost across all Incoterms, verified buyer intelligence, market demand data and trade news, with contact-verified buyer records across 32 countries.",
  },
  {
    q: "What does the name Vametra mean, and how is it spelled?",
    a: "Vametra is a coined brand name, not a dictionary word — which is why search engines sometimes try to autocorrect it. It is spelled V-A-M-E-T-R-A and is used interchangeably as Vametra, Vametra AI and vametra.com. The registered entity behind it is Vametra AI Technologies Pvt Ltd.",
  },
  {
    q: "Who operates Vametra AI?",
    a: `${LEGAL_NAME}, founded in ${FOUNDED} and headquartered in ${HQ}. The platform was founded by ${FOUNDER} and serves users worldwide.`,
  },
  {
    q: "Where does Vametra AI get its data?",
    a: "Applied and preferential tariffs come from World Bank WITS and UNCTAD TRAINS at HS6 level across 56 reporting countries. Trade values and demand rankings come from OEC World and CEPII BACI. Classification follows WCO HS-2022. Export-support rates come from the administering authority, including DGFT Appendix 4R for India. Buyer records come from official trade registries, screened before publication.",
  },
  {
    q: "Is Vametra AI free to use?",
    a: "The trade tools — HS code finder, customs duty calculator, landed cost calculator, export incentive finder, product research, buyer discovery and the export readiness score — are free and need no signup. An account is required to save work as a Trade Project in the Command Center and for premium buyer intelligence.",
  },
  {
    q: "Does Vametra AI have a mobile app?",
    a: "Not yet. Vametra AI is a web platform that runs in any modern mobile or desktop browser with nothing to install, and every tool is fully usable on a phone. A native app is on the roadmap and will be announced when it actually exists.",
  },
];

const STATS = [
  { Icon: Globe, k: "32", v: "Countries with contact-verified buyer records" },
  { Icon: Database, k: "5,606", v: "HS codes indexed from WCO HS-2022" },
  { Icon: ShieldCheck, k: "56", v: "Reporting countries with live applied tariffs" },
  { Icon: Buildings, k: FOUNDED, v: `Founded · ${HQ}` },
];

export default function About() {
  const aboutSchema = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "@id": `${SITE_URL}/about#webpage`,
    url: `${SITE_URL}/about`,
    name: `About ${BRAND_NAME}`,
    description: `${BRAND_NAME} (${LEGAL_NAME}) is an AI-powered global trade intelligence platform for exporters and importers, covering customs duty, HS codes, FTAs, landed cost, demand data and contact-verified buyers across 32 countries.`,
    isPartOf: { "@id": `${SITE_URL}/#website` },
    about: { "@id": `${SITE_URL}/#organization` },
    mainEntity: { "@id": `${SITE_URL}/#organization` },
  };

  return (
    <>
      <SEO
        title={`About ${BRAND_NAME} — Global Trade Intelligence Platform`}
        description={`${BRAND_NAME} (${LEGAL_NAME}) is an AI-powered global trade intelligence platform for exporters and importers — customs duty, HS codes, FTAs, landed cost, demand data and verified buyers in 32 countries. Founded ${FOUNDED}, headquartered in ${HQ}.`}
        path="/about"
        keywords="Vametra, Vametra AI, vametra.com, Vametra AI Technologies, about Vametra AI, global trade intelligence platform, who is Vametra AI"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "About", path: "/about" }]}
        faqs={FAQ}
        schema={[aboutSchema]}
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-28 pb-6">
        <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">
          About the company
        </div>
        <h1 className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4 leading-[1.05]">
          <span className="gradient-text">Vametra AI</span> — intelligence<br className="hidden sm:block" /> beyond borders.
        </h1>
        <p className="mt-6 text-[15px] md:text-base text-slate-300 max-w-3xl leading-relaxed">
          Vametra AI is an AI-powered global trade intelligence platform. It answers the questions
          that actually decide whether a shipment makes money — what duty the destination applies to
          your HS code, what your buyer pays landed, whether that market genuinely imports your
          product, and who the verified importers are. Also known as{" "}
          <strong className="text-white">Vametra</strong> and{" "}
          <strong className="text-white">vametra.com</strong>, and operated by {LEGAL_NAME}.
        </p>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6" data-testid="about-stats">
        {STATS.map(({ Icon, k, v }) => (
          <div key={k} className="glass rounded-2xl p-6">
            <Icon size={22} weight="duotone" className="text-cyan-300" />
            <div className="font-display font-extrabold text-2xl mt-3">{k}</div>
            <div className="text-xs text-slate-400 mt-1 leading-relaxed">{v}</div>
          </div>
        ))}
      </section>

      <AnswerBlock testId="about-what" label="What we do" title="One engine, four questions">
        <p>
          Exporters lose money in predictable places: a misclassified HS code, a preferential tariff
          they never qualified for, a destination tax they forgot compounds on top of duty, and a
          market they chose on instinct rather than on measured import demand. Vametra AI exists to
          close those four gaps before capital is committed.
        </p>
        <p>
          Underneath sits a single Customs &amp; Compliance Engine. The free tools, the published
          export guides, the regional hubs and the Trade Command Center all read from it, so a rate
          you see on a guide is the same rate the calculator uses. There is no simplified public
          dataset and no separate marketing figure.
        </p>
        <p>
          Every number carries its source and its reporting year on screen. Where a source holds no
          record for a country-product pair, the platform says so rather than substituting an
          estimate — and product-market guides are only published once both a verified tariff and
          measured demand exist for that lane.
        </p>
      </AnswerBlock>

      <AnswerBlock testId="about-name" label="The name" title="Vametra, Vametra AI, vametra.com">
        <p>
          Vametra is a coined name rather than an existing word, so search engines occasionally try
          to correct the spelling to something more common. For the record, the brand is spelled{" "}
          <strong className="text-white">V-A-M-E-T-R-A</strong>, and the three forms{" "}
          <strong className="text-white">Vametra</strong>,{" "}
          <strong className="text-white">Vametra AI</strong> and{" "}
          <strong className="text-white">vametra.com</strong> all refer to the same platform,
          operated by {LEGAL_NAME}.
        </p>
      </AnswerBlock>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-14" data-testid="about-entity">
        <h2 className="font-display font-bold text-base md:text-lg">Company details</h2>
        <div className="mt-5 grid md:grid-cols-2 gap-4">
          <dl className="glass rounded-2xl p-6 text-sm space-y-3">
            {[
              ["Brand name", BRAND_NAME],
              ["Also known as", "Vametra · vametra.com"],
              ["Legal entity", LEGAL_NAME],
              ["Founded", FOUNDED],
              ["Founder", FOUNDER],
              ["Headquarters", HQ],
              ["Area served", "Worldwide"],
              ["Tagline", TAGLINE],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-6 border-b border-white/5 pb-2.5 last:border-0 last:pb-0">
                <dt className="text-slate-400">{k}</dt>
                <dd className="text-right font-medium">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="glass rounded-2xl p-6">
            <h3 className="font-display font-bold text-sm">Official channels</h3>
            <p className="mt-2 text-sm text-slate-400 leading-relaxed">
              These are the only accounts operated by {LEGAL_NAME}. Anything else using the Vametra
              name is not affiliated with us.
            </p>
            <ul className="mt-4 space-y-2 text-sm">
              <li>
                <a href={SITE_URL} className="text-cyan-300 hover:underline" data-testid="about-link-site">vametra.com</a>
              </li>
              {SOCIALS.map((s) => (
                <li key={s.key}>
                  <a href={s.url} target="_blank" rel="noopener noreferrer me" className="text-cyan-300 hover:underline" data-testid={`about-link-${s.key}`}>
                    {s.label} · {s.display}
                  </a>
                </li>
              ))}
              <li>
                <a href={`mailto:${EMAIL}`} className="text-cyan-300 hover:underline" data-testid="about-link-email">{EMAIL}</a>
              </li>
            </ul>
            <div className="mt-6 flex flex-wrap gap-2">
              <Link to="/contact" className="btn-ghost text-sm" data-testid="about-cta-contact">
                Contact us <ArrowRight size={15} weight="bold" />
              </Link>
              <Link to="/tools" className="btn-ghost text-sm" data-testid="about-cta-tools">Free trade tools</Link>
            </div>
          </div>
        </div>
      </section>

      <PageFaq items={FAQ} heading="About Vametra AI — frequently asked questions" testIdPrefix="about-faq" />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-16">
        <DownloadCTA />
      </section>
    </>
  );
}
