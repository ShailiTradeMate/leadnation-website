import React from "react";
import AppFeatureNote from "@/components/AppFeatureNote";
import SEO from "@/components/SEO";
import { ShoppingBag } from "@phosphor-icons/react";

export default function Marketplace() {
  return (
    <>
      <SEO
        title="Trade Marketplace · Live RFQs & Product Listings"
        description="The LeadNation Marketplace connects verified exporters, importers and suppliers worldwide — post and browse live RFQs, negotiate, sample and close cross-border deals in-app."
        path="/marketplace"
        keywords="trade marketplace, export RFQ, import listings, B2B trade platform, connect buyers suppliers"
      />
      <AppFeatureNote
        feature="The Marketplace"
        path="/marketplace"
        icon={ShoppingBag}
        points={[
          "Post & browse live RFQs and product listings",
          "Connect directly with verified buyers and suppliers",
          "Negotiate, sample and close deals in-app",
        ]}
      />
    </>
  );
}
