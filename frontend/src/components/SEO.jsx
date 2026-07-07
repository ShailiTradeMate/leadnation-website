import React from "react";
import { Helmet } from "react-helmet-async";

const SITE = "https://leadnation.app";
const DEFAULT_IMAGE = "https://leadnation.app/og-default.png";

/**
 * SEO component — handles dynamic meta titles, descriptions, OG and structured schema.
 * Usage:
 *   <SEO title="..." description="..." path="/" schema={{...}} />
 */
export default function SEO({
  title,
  description,
  path = "/",
  image = DEFAULT_IMAGE,
  type = "website",
  schema,
  keywords,
}) {
  const fullTitle = title.includes("LeadNation") ? title : `${title} · LeadNation`;
  const url = `${SITE}${path}`;
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
      <meta property="og:site_name" content="LeadNation" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />

      {/* Robots */}
      <meta name="robots" content="index, follow, max-image-preview:large" />

      {/* Structured Data */}
      {schema && (
        <script type="application/ld+json">
          {JSON.stringify(schema)}
        </script>
      )}
    </Helmet>
  );
}

export const baseOrgSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "LeadNation",
  url: SITE,
  logo: `${SITE}/og-default.png`,
  sameAs: ["https://instagram.com/leadnation.app"],
  contactPoint: {
    "@type": "ContactPoint",
    telephone: "+91-8237161088",
    contactType: "customer support",
    email: "admin@leadnation.app",
    areaServed: "Worldwide",
  },
};
