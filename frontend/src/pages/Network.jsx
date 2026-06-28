import React from "react";
import AppFeatureNote from "@/components/AppFeatureNote";
import { UsersThree } from "@phosphor-icons/react";

export default function Network() {
  return (
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
  );
}
