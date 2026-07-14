import React from "react";
import AppFeatureNote from "@/components/AppFeatureNote";
import SEO from "@/components/SEO";
import { UsersThree } from "@phosphor-icons/react";

export default function Network() {
  return (
    <>
      <SEO
        title="Trade Network · Connect with Verified Global Traders"
        description="Join the LeadNation Trade Network — connect with verified exporters, importers and customs house agents worldwide, build your trusted trade circle and collaborate in real time."
        path="/network"
        keywords="trade network, verified exporters, importers directory, customs house agents, global trade community"
      />
      <AppFeatureNote
        feature="The Trade Network"
        path="/network"
        icon={UsersThree}
        points={[
          "Connect with verified exporters, importers & CHAs worldwide",
          "Build your trusted trade circle",
          "Message and collaborate in real time",
        ]}
      />
    </>
  );
}
