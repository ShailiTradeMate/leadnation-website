import React from "react";
import { Helmet } from "react-helmet-async";
import { SITE_URL, BRAND_NAME, LEGAL_NAME, TAGLINE, PHONE, EMAIL, SAME_AS } from "@/lib/brand";

const SITE = SITE_URL;
const DEFAULT_IMAGE = `${SITE}/og-default.png`;

/**
 * SEO — dynamic per-page title/description/OG/Twitter/canonical + JSON-LD.
 * `schema` accepts a single object OR an array of schema objects (all rendered).
 */
export default function SEO({
  title,
  description,
  path = "/",
  image = DEFAULT_IMAGE,
  type = "website",
  schema,
  keywords,
  noindex = false,
}) {
  const fullTitle = title?.includes(BRAND_NAME) ? title : `${title} · ${BRAND_NAME}`;
  const url = `${SITE}${path}`;
  const schemas = schema ? (Array.isArray(schema) ? schema : [schema]) : [];
  return (
    <Helmet prioritizeSeoTags>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords} />}
      <link rel="canonical" href={url} />

      {/* Open Graph */}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={image} />
      <meta property="og:image:alt" content={`${BRAND_NAME} — ${TAGLINE}`} />
      <meta property="og:site_name" content={BRAND_NAME} />
      <meta property="og:locale" content="en_US" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
      <meta name="twitter:image:alt" content={`${BRAND_NAME} — ${TAGLINE}`} />

      {/* Robots */}
      <meta
        name="robots"
        content={noindex ? "noindex, nofollow" : "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"}
      />

      {schemas.map((s, i) => (
        <script key={i} type="application/ld+json">{JSON.stringify(s)}</script>
      ))}
    </Helmet>
  );
}

// ── Reusable JSON-LD builders (Entity + Rich-snippet + Knowledge-Graph ready) ──

export const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": `${SITE}/#organization`,
  name: BRAND_NAME,
  legalName: LEGAL_NAME,
  url: SITE,
  logo: { "@type": "ImageObject", url: `${SITE}/icon-512.png`, width: 512, height: 512 },
  image: `${SITE}/og-default.png`,
  slogan: TAGLINE,
  description:
    "LeadNation is an AI-powered Global Trade Intelligence platform for exporters, importers, suppliers, customs house agents and trade consultants — unifying customs duty calculation, HS/HSN code lookup, FTA analysis, landed cost across all Incoterms, trade expos, market intelligence and real-time trade news for 195+ countries.",
  foundingDate: "2025",
  founder: { "@type": "Person", name: "Vaibhav Deshmane" },
  foundingLocation: { "@type": "Place", name: "Ahilyanagar, Maharashtra, India" },
  knowsAbout: [
    "International trade", "Export", "Import", "Customs duty", "HS codes", "HSN codes",
    "Incoterms", "Free Trade Agreements", "Landed cost", "Trade compliance",
    "Trade finance", "Global logistics", "Market intelligence", "Trade expos",
  ],
  areaServed: { "@type": "Place", name: "Worldwide" },
  address: {
    "@type": "PostalAddress",
    streetAddress: "Ekveera Chowk, Pipeline Rd, Savedi",
    addressLocality: "Ahilyanagar",
    addressRegion: "Maharashtra",
    postalCode: "414003",
    addressCountry: "IN",
  },
  sameAs: SAME_AS,
  contactPoint: {
    "@type": "ContactPoint",
    telephone: PHONE,
    contactType: "customer support",
    email: EMAIL,
    areaServed: "Worldwide",
    availableLanguage: ["en"],
  },
};
// Back-compat alias (older imports).
export const baseOrgSchema = organizationSchema;

export const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: BRAND_NAME,
  alternateName: "LeadNation Global Trade Intelligence",
  url: SITE,
  publisher: { "@type": "Organization", name: LEGAL_NAME },
  potentialAction: {
    "@type": "SearchAction",
    target: { "@type": "EntryPoint", urlTemplate: `${SITE}/search?q={search_term_string}` },
    "query-input": "required name=search_term_string",
  },
};

export const softwareApplicationSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: BRAND_NAME,
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web, iOS, Android",
  description:
    "AI-powered Global Trade Intelligence platform: customs duty calculator, HS/HSN code finder, landed cost across all Incoterms, FTA analysis, trade expos, market data and real-time trade news for 195+ countries.",
  url: SITE,
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  publisher: { "@type": "Organization", name: LEGAL_NAME, url: SITE },
  aggregateRating: { "@type": "AggregateRating", ratingValue: "4.8", ratingCount: "126" },
};

export const faqSchema = (faqs = []) => ({
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqs.map((f) => ({
    "@type": "Question",
    name: f.q,
    acceptedAnswer: { "@type": "Answer", text: f.a },
  })),
});

// items: [{ name, path }] — path relative to SITE (last item = current page)
export const breadcrumbSchema = (items = []) => ({
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: items.map((it, i) => ({
    "@type": "ListItem",
    position: i + 1,
    name: it.name,
    item: `${SITE}${it.path}`,
  })),
});

export const eventSchema = (e) => ({
  "@context": "https://schema.org",
  "@type": "Event",
  name: e.name,
  description: e.description,
  startDate: e.startDate,
  endDate: e.endDate,
  eventStatus: "https://schema.org/EventScheduled",
  eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
  ...(e.location && {
    location: {
      "@type": "Place",
      name: e.location,
      address: e.address || e.location,
    },
  }),
  ...(e.image && { image: e.image }),
  organizer: { "@type": "Organization", name: e.organizer || BRAND_NAME, url: SITE },
});

// a.type = "Article" | "NewsArticle" (default NewsArticle)
export const articleSchema = (a) => ({
  "@context": "https://schema.org",
  "@type": a.type || "NewsArticle",
  headline: a.headline,
  description: a.description,
  ...(a.image && { image: a.image }),
  ...(a.datePublished && { datePublished: a.datePublished }),
  ...(a.dateModified && { dateModified: a.dateModified }),
  mainEntityOfPage: { "@type": "WebPage", "@id": `${SITE}${a.path || "/"}` },
  author: { "@type": "Organization", name: a.author || BRAND_NAME, url: SITE },
  publisher: {
    "@type": "Organization",
    name: BRAND_NAME,
    logo: { "@type": "ImageObject", url: `${SITE}/icon-512.png` },
  },
  ...(a.keywords && { keywords: a.keywords }),
  ...(a.section && { articleSection: a.section }),
});

export const productSchema = (p) => ({
  "@context": "https://schema.org",
  "@type": "Product",
  name: p.name,
  description: p.description,
  ...(p.image && { image: p.image }),
  ...(p.category && { category: p.category }),
  ...(p.sku && { sku: p.sku }),
  brand: { "@type": "Brand", name: BRAND_NAME },
});

// steps: [{ name, text }]
export const howToSchema = (h) => ({
  "@context": "https://schema.org",
  "@type": "HowTo",
  name: h.name,
  description: h.description,
  step: (h.steps || []).map((s, i) => ({
    "@type": "HowToStep",
    position: i + 1,
    name: s.name,
    text: s.text,
  })),
});
