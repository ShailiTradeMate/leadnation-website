import React from "react";
import AppFeatureNote from "@/components/AppFeatureNote";
import { ShoppingBag } from "@phosphor-icons/react";

export default function Marketplace() {
  return (
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
  );
}
