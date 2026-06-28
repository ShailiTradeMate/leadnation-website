import React from "react";
import { useNavigate } from "react-router-dom";
import { DeviceMobile, ArrowRight } from "@phosphor-icons/react";
import SEO from "@/components/SEO";
import { APP_LINKS } from "@/data/contact";

export default function AppFeatureNote({ feature = "This feature", path = "/", icon: Icon = DeviceMobile, points = [] }) {
  const navigate = useNavigate();
  return (
    <>
      <SEO title={`${feature} · In the LeadNation App`} description={`${feature} is built into the LeadNation mobile app. Download to connect with traders worldwide.`} path={path} />
      <section className="max-w-3xl mx-auto px-6 pt-36 pb-24 text-center">
        <div className="w-20 h-20 mx-auto rounded-3xl grid place-items-center bg-gradient-to-br from-cyan-500/25 to-violet-500/25 border border-white/10">
          <Icon size={40} weight="duotone" className="text-cyan-300" />
        </div>
        <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-6">{feature} lives in the app</h1>
        <p className="mt-4 text-base text-slate-300">
          {feature} is built right into the <span className="text-cyan-300 font-semibold">LeadNation app</span> —
          download it to build your connections worldwide, message verified traders and act on opportunities in real time.
        </p>
        {points.length > 0 && (
          <ul className="mt-6 inline-flex flex-col gap-2 text-left text-sm text-slate-300">
            {points.map((p, i) => <li key={i} className="flex items-center gap-2"><ArrowRight size={14} className="text-cyan-300" />{p}</li>)}
          </ul>
        )}
        <div className="mt-8 flex flex-wrap gap-3 justify-center">
          <a href={APP_LINKS.ios} data-testid="appnote-ios" className="btn-primary">Download for iOS</a>
          <a href={APP_LINKS.android} data-testid="appnote-android" className="btn-ghost">Get it on Android</a>
          <button onClick={() => navigate("/brain")} className="btn-ghost" data-testid="appnote-brain">Ask the Brain instead</button>
        </div>
      </section>
    </>
  );
}
