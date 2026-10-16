"""Part 6 batch 3 — detail templates (services, countries, corridors, products, industries, academy)."""
import sys
ROOT = "/app/frontend/src/pages/"
IMP = 'import { AnswerFirst } from "@/components/AnswerFirst";\n'

def patch(f, reps, imports=()):
    s = open(ROOT + f).read()
    for a, b in reps:
        if a not in s:
            sys.exit(f"MISSING in {f}: {a[:100]}")
        s = s.replace(a, b, 1)
    for line in imports:
        if line not in s:
            s = s.replace('import SEO from "@/components/SEO";\n', 'import SEO from "@/components/SEO";\n' + line, 1)
    open(ROOT + f, "w").write(s)
    print("ok", f)

# ── /services/{slug} ─────────────────────────────────────────────────────────
patch("Services.jsx", [
 ('      <SEO title={`${s.name} · ${s.tagline}`}\n        description={s.overview.substring(0, 160)}\n        path={`/services/${s.slug}`}',
  '      <SEO title={SERVICE_SEO[s.slug]?.title || `${s.name} · ${s.tagline}`}\n        description={s.overview.substring(0, 160)}\n        path={`/services/${s.slug}`}\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Services", path: "/services" }, { name: s.name, path: `/services/${s.slug}` }]}\n        faqs={s.faqs}'),
 ('            <h1 data-testid="service-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-6xl mt-4">{s.name}</h1>',
  '            <h1 data-testid="service-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4">{SERVICE_SEO[s.slug]?.h1 || s.name}</h1>'),
 ('                  {openFaq === i && <div className="pb-3 text-sm text-slate-300">{f.a}</div>}',
  '                  <div className={`pb-3 text-sm text-slate-300 ${openFaq === i ? "" : "hidden"}`}>{f.a}</div>'),
 ('''        </aside>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>''',
  '''        </aside>
      </section>

      <AnswerFirst testId="service-answer" eyebrow={`${s.name} · direct answer`}
        answer={s.overview}
        rows={[
          { label: "Starts at", value: s.priceFrom },
          { label: "Documents listed", value: String((s.documents || []).length) },
          { label: "Process steps", value: String((s.process || []).length) },
          { label: "Handled by", value: s.category === "Govt Documentation" ? "Certified CA" : "Certified trade consultant" },
        ]}
        source="Vametra AI Services; DGFT / GST / MCA requirements as published"
        links={[
          { to: "/tools/export-readiness", label: "Export readiness assessment" },
          { to: "/tools/export-incentive-finder", label: "Export incentive calculator" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/countries/india", label: "India trade profile" },
          { to: "/services", label: "All services" },
        ]} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>'''),
], imports=['import { SERVICE_SEO } from "@/data/seoTitles";\n'])

# ── /countries/{slug} ────────────────────────────────────────────────────────
patch("CountryProfile.jsx", [
 ('        title={`${data.name} Trade Profile — Imports, Exports, Customs & Compliance`}\n        description={`${data.tagline}. Discover ${data.name}\'s major imports, exports, customs duties, FTA opportunities, trade events and compliance — updated for ${new Date().getFullYear()}.`}',
  '        title={countrySeo(data.name).title}\n        description={`${data.name} trade profile: ${data.tagline}. Major imports and exports, applied customs duties, FTA opportunities, trade events, compliance and verified buyer coverage — updated ${new Date().getFullYear()}.`}'),
 ('''            <h1 data-testid="cp-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-7xl">
              {data.name}
            </h1>''',
  '''            <h1 data-testid="cp-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl">
              {countrySeo(data.name).h1}
            </h1>'''),
 ('      <PageFaq items={faqs} heading={`Exporting to ${data.name} — frequently asked questions`} testIdPrefix="cp-faq" />',
  '''      <AnswerFirst testId="cp-answer-first" eyebrow={`${data.name} · direct answer`}
        answer={`${data.name} trade profile in one line: ${data.tagline}. Applied import duty for any HS code comes from World Bank WITS, measured import demand from OEC/BACI, and the verified buyer count for ${data.name} is stated honestly on this page — with a published export guide linked for every product we cover in this market.`}
        rows={[
          { label: "Capital", value: data.capital },
          { label: "Currency", value: data.currency },
          { label: "Tariff data", value: "WITS / TRAINS · HS6" },
          { label: "Export guides for this market", value: guides?.total != null ? String(guides.total) : "See below" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; OEC World (BACI); official registries"
        links={[
          { to: "/tools/duty-calculator", label: `Duty into ${data.name}` },
          { to: "/tools/find-buyers", label: `Verified buyers in ${data.name}` },
          { to: "/export", label: "Export guides" },
          { to: "/countries", label: "All country profiles" },
          { to: "/corridors", label: "India trade corridors" },
        ]} />
      <PageFaq items={faqs} heading={`Exporting to ${data.name} — frequently asked questions`} testIdPrefix="cp-faq" />'''),
], imports=[IMP, 'import { countrySeo } from "@/data/seoTitles";\n'])

# ── /corridors/{slug} ────────────────────────────────────────────────────────
patch("Corridors.jsx", [
 ('      <SEO title={`${c.from} → ${c.to} Trade Corridor — Customs, Documents, Duties`}\n        description={`${c.tagline}. Complete playbook: export process, import process, customs information, documents, duties and opportunities.`}',
  '      <SEO title={c.from === "India" ? corridorSeo(c.to).title : `${c.from} → ${c.to} Trade Corridor — Customs, Documents, Duties`}\n        description={`Export from ${c.from} to ${c.to}: ${c.tagline}. Export and import process, customs regime, applied duty and taxes, required documents and logistics, linked to per-product export guides.`}'),
 ('''          <SectionLabel>Trade Corridor</SectionLabel>
          <h1 data-testid="cd-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-7xl mt-4 flex flex-wrap items-center gap-3">
            <span>{c.fromFlag}</span> {c.from} <ArrowsLeftRight size={36} className="text-cyan-300 mx-2" /> {c.to} <span>{c.toFlag}</span>
          </h1>''',
  '''          <SectionLabel>Trade Corridor · {c.fromFlag} {c.from} <ArrowsLeftRight size={12} className="inline text-cyan-300 mx-1" /> {c.to} {c.toFlag}</SectionLabel>
          <h1 data-testid="cd-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4 max-w-4xl">
            {c.from === "India" ? corridorSeo(c.to).h1 : `${c.from} → ${c.to} trade corridor — duty, documents and shipping`}
          </h1>'''),
 ('      <PageFaq items={faqs} heading={`${c.from} → ${c.to} — frequently asked questions`} testIdPrefix="cd-faq" />',
  '''      <AnswerFirst testId="cd-answer-first" eyebrow={`${c.from} → ${c.to} · direct answer`}
        answer={`To export from ${c.from} to ${c.to}: ${c.tagline}. ${c.customsInfo || ""} The applied duty and any preferential rate for your HS code are read live from World Bank WITS, and each established product on this lane links to an export guide with measured import demand and verified buyer coverage.`}
        rows={[
          { label: "Documents listed", value: String((c.documents || []).length) },
          { label: "Established products", value: String((c.popularProducts || []).length) },
          { label: "Export guides on this lane", value: guides?.total != null ? String(guides.total) : "See below" },
          { label: "Duty source", value: "WITS / TRAINS · HS6" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; customs authorities of both countries as published"
        links={[
          { to: "/tools/duty-calculator", label: `Duty into ${c.to}` },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/tools/find-buyers", label: `Buyers in ${c.to}` },
          { to: "/export", label: "Export guides" },
          { to: "/corridors", label: "All corridors" },
        ]} />
      <PageFaq items={faqs} heading={`${c.from} → ${c.to} — frequently asked questions`} testIdPrefix="cd-faq" />'''),
], imports=[IMP, 'import { corridorSeo } from "@/data/seoTitles";\n'])

# ── /products/{slug} ─────────────────────────────────────────────────────────
patch("Products.jsx", [
 ('      <SEO title={`${p.name} — Export Guide, HSN, Compliance & Markets`}\n        description={`${p.overview.substring(0, 160)}`}',
  '      <SEO title={productSeo(p.name).title}\n        description={`${p.name} export from India: HSN ${p.hsn}, ${p.overview.substring(0, 110)}`}'),
 ('            <h1 data-testid="pd-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-6xl mt-4">{p.name}</h1>',
  '            <h1 data-testid="pd-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4">{productSeo(p.name).h1}</h1>'),
 ('      <PageFaq items={faqs} heading={`Exporting ${p.name} — frequently asked questions`} testIdPrefix="pd-faq" />',
  '''      <AnswerFirst testId="pd-answer-first" eyebrow={`${p.name} · direct answer`}
        answer={`${p.name} export from India starts with HSN ${p.hsn}. ${p.overview} The applied import duty per destination comes from World Bank WITS, demand from OEC/BACI, and verified buyers from official registries — each market we publish links to its own export guide below.`}
        rows={[
          { label: "HSN", value: String(p.hsn) },
          { label: "Duty source", value: "WITS / TRAINS · HS6" },
          { label: "Demand source", value: "OEC World (BACI)" },
          { label: "Verified buyer countries", value: "{buyerCountries}" },
        ]}
        source="WCO HS-2022; World Bank WITS / UNCTAD TRAINS; OEC World (BACI); official registries"
        links={[
          { to: `/tools/duty-calculator?hs=${String(p.hsn).replace(/\\D/g, "").slice(0, 6)}`, label: `Duty for ${p.name}` },
          { to: `/tools/find-buyers`, label: `Buyers for ${p.name}` },
          { to: "/export", label: "Export guides" },
          { to: "/products", label: "All export products" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
        ]} />
      <PageFaq items={faqs} heading={`Exporting ${p.name} — frequently asked questions`} testIdPrefix="pd-faq" />'''),
], imports=[IMP, 'import { productSeo } from "@/data/seoTitles";\n'])

# ── /industries/{slug} ───────────────────────────────────────────────────────
patch("Industries.jsx", [
 ('      <SEO title={`${i.name} Industry · Exports, Markets, Compliance`}\n        description={i.overview}',
  '      <SEO title={industrySeo(i.name).title}\n        description={`${i.name} exports from India: ${i.overview.substring(0, 125)}`}'),
 ('      <PageHero testIdPrefix="id" label={`Industry · ${i.name}`} title={i.name} sub={i.overview} />',
  '''      <PageHero testIdPrefix="id" label={`Industry · ${i.name}`} title={industrySeo(i.name).h1} sub={i.overview} />'''),
 ('      <PageFaq items={faqs} heading={`${i.name} exports — frequently asked questions`} testIdPrefix="id-faq" />',
  '''      <AnswerFirst testId="id-answer-first" eyebrow={`${i.name} · direct answer`}
        answer={`${i.name} exports from India: ${i.overview} Start at the sector, pick a category, then open the product-market export guide for the exact lane — applied duty from World Bank WITS, measured demand from OEC/BACI and verified buyer coverage stated per market.`}
        rows={[
          { label: "Export categories", value: String((i.exports || []).length) },
          { label: "Top markets listed", value: String((i.topMarkets || []).length) },
          { label: "Compliance items", value: String((i.compliance || []).length) },
          { label: "Tariff countries", value: "{tariffCountries}" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; OEC World (BACI); sector regulators as listed"
        links={[
          { to: "/export", label: "Export guides" },
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/tools/product-research", label: "Import demand by HS code" },
          { to: "/industries", label: "All export industries" },
          { to: "/countries/usa", label: "USA trade profile" },
        ]} />
      <PageFaq items={faqs} heading={`${i.name} exports — frequently asked questions`} testIdPrefix="id-faq" />'''),
], imports=[IMP, 'import { industrySeo } from "@/data/seoTitles";\n'])

# ── /academy/{slug} ──────────────────────────────────────────────────────────
patch("AcademyDetail.jsx", [
 ('      <SEO title={`${course.title} · Vametra AI Academy`} description={course.summary} path={`/academy/${slug}`}',
  '      <SEO title={clampTitle(courseSeo(course.title).title)} description={`${course.title} — free ${course.level.toLowerCase()} course for exporters and importers: ${course.summary}`} path={`/academy/${slug}`}\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Academy", path: "/academy" }, { name: course.title, path: `/academy/${slug}` }]}'),
 ('            <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-4 leading-[1.05]">{course.title}</h1>',
  '            <h1 data-testid="course-title" className="font-display font-extrabold text-4xl sm:text-5xl mt-4 leading-[1.05]">{courseSeo(course.title).h1}</h1>'),
 ('''      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>''',
  '''      <AnswerFirst testId="course-answer" eyebrow={`${course.title} · what you will learn`}
        answer={`${course.summary} This free ${course.level.toLowerCase()} course has ${course.outline.length} lessons (${course.duration}) and links each concept to the live Vametra AI tool that applies it, so what you learn can be checked against real duty, HS and demand data straight away.`}
        rows={[
          { label: "Level", value: course.level },
          { label: "Lessons", value: String(course.outline.length) },
          { label: "Duration", value: course.duration },
          { label: "Cost", value: "Free" },
        ]}
        source="Vametra AI Academy curriculum"
        links={[
          { to: "/academy", label: "All courses" },
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/export-readiness", label: "Export readiness assessment" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
        ]} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>'''),
], imports=[IMP, 'import { courseSeo, clampTitle } from "@/data/seoTitles";\n'])
