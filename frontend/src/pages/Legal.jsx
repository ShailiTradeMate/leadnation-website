import React from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";

const COMPANY = "Vametra AI Technologies Pvt Ltd";
const PRODUCT = "LeadNation";
const EMAIL = "admin@leadnation.app";
const ADDRESS = "Tirthankar, Central Bank of India, Ekveera Chowk, Pipeline Rd, Savedi, Ahilyanagar, Maharashtra 414003, India";
const UPDATED = "5 July 2026";

// Reusable across footer, signup, checkout, reports, and app-store listings.
export const LEGAL_LINKS = [
  { to: "/legal/privacy", label: "Privacy Policy" },
  { to: "/legal/terms", label: "Terms of Service" },
  { to: "/legal/cookies", label: "Cookie Policy" },
  { to: "/legal/disclaimer", label: "Disclaimer" },
  { to: "/legal/refund", label: "Refund & Cancellation" },
];

function LegalLayout({ title, description, path, children }) {
  return (
    <section className="max-w-3xl mx-auto px-6 sm:px-10 pt-16 pb-28" data-testid="legal-page">
      <SEO title={`${title}`} description={description} path={path} />
      <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Legal</div>
      <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-3" data-testid="legal-title">{title}</h1>
      <p className="text-slate-400 text-sm mt-3">{PRODUCT}, operated by {COMPANY}. Last updated {UPDATED}.</p>
      <div className="glass-strong rounded-3xl p-6 sm:p-8 mt-8 space-y-6 text-slate-300 text-sm leading-relaxed">
        {children}
      </div>
      <nav className="flex flex-wrap gap-3 mt-8 text-xs" data-testid="legal-nav">
        {LEGAL_LINKS.map((l) => (
          <Link key={l.to} to={l.to} className="text-slate-400 hover:text-cyan-300 underline underline-offset-4">{l.label}</Link>
        ))}
      </nav>
      <p className="text-xs text-slate-500 mt-6">Questions? Contact <a href={`mailto:${EMAIL}`} className="text-cyan-300">{EMAIL}</a> · {COMPANY}, {ADDRESS}.</p>
    </section>
  );
}

const H = ({ children }) => <h2 className="font-display font-bold text-lg text-white mt-2">{children}</h2>;
const P = ({ children }) => <p>{children}</p>;
const UL = ({ items }) => <ul className="list-disc pl-5 space-y-1.5">{items.map((t, i) => <li key={i}>{t}</li>)}</ul>;

/* ============================ PRIVACY POLICY ============================ */
export function PrivacyPolicy() {
  return (
    <LegalLayout title="Privacy Policy" path="/legal/privacy"
      description="How LeadNation (Vametra AI Technologies Pvt Ltd) collects, uses, stores and protects your data across our website and mobile app.">
      <P>This Privacy Policy explains how {COMPANY} ("we", "us") collects, uses, discloses and safeguards your information when you use the {PRODUCT} website, mobile application and related services (collectively, the "Service"). It applies to users worldwide. By using the Service you agree to this Policy.</P>

      <H>1. Information we collect</H>
      <UL items={[
        "Account & identity data: name, email, phone, country, and a unique 5-digit Customer ID, managed through our authentication provider (Google Firebase Authentication).",
        "Profile & business information you provide: company details, trade role (exporter/importer), preferences and settings.",
        "Trade Project content: products, HS codes, cost inputs, buyers, suppliers, scenarios, notes and any business information or documents you upload.",
        "Generated content: quotes, landed-cost calculations, simulations, decision analyses, trade scores and downloadable reports.",
        "Payment data: processed by our payment providers (Stripe and Razorpay). We do not store full card numbers; we retain transaction references, amounts, currency and subscription status.",
        "Usage & device data: pages viewed, features used, IP address, browser/device type, and diagnostic logs.",
        "Cookies and similar technologies (see our Cookie Policy).",
      ]} />

      <H>2. How we use your information</H>
      <UL items={[
        "To provide the Trade Command Center: create and sync Trade Projects, run costing, simulations, scoring and decision analyses.",
        "To power AI features: your project context is processed by AI models to generate explanations, recommendations and summaries (see 'AI processing' below).",
        "To authenticate you and maintain one shared identity across our website and mobile app.",
        "To process payments, subscriptions, and downloads.",
        "To improve, secure and support the Service, and to communicate service updates.",
        "To comply with legal obligations.",
      ]} />

      <H>3. AI processing and limitations</H>
      <P>{PRODUCT} uses third-party large-language-model providers to interpret and explain trade data (the "LeadNation Brain"). Deterministic engines compute all figures; AI is used to explain, recommend and summarise — it does not fabricate numbers. Project context you submit may be sent to these AI providers to generate responses. AI output may be incomplete or inaccurate and must not be relied upon as legal, financial, customs or professional advice (see our Disclaimer).</P>

      <H>4. Data storage and security</H>
      <UL items={[
        "Your data is stored in a managed MongoDB database. Authentication is handled by Google Firebase.",
        "We apply industry-standard safeguards including encryption in transit (HTTPS/TLS), access controls, and role-based admin protection.",
        "No method of transmission or storage is 100% secure; we cannot guarantee absolute security.",
        "Data may be processed on servers located in different countries; by using the Service you consent to such cross-border processing.",
      ]} />

      <H>5. Sharing and disclosure</H>
      <P>We share data only with sub-processors that help us operate the Service — including Google Firebase (authentication), our database host, AI model providers, and payment providers (Stripe, Razorpay) — and with analytics tools where enabled. We may disclose information to comply with law or protect our rights. We do not sell your personal data.</P>

      <H>6. User-generated content & marketplace</H>
      <P>Information you publish (e.g., marketplace listings, network profiles, uploaded documents) may be visible to other users or the public as intended by the feature you use. You are responsible for the accuracy and legality of the content you submit.</P>

      <H>7. Your rights</H>
      <P>Depending on your jurisdiction (including GDPR/EEA and Indian data-protection law), you may have rights to access, correct, export or delete your personal data, and to object to or restrict processing. To exercise these rights, contact {EMAIL}. Your Customer ID is immutable and cannot be changed once assigned.</P>

      <H>8. Data retention</H>
      <P>We retain your data while your account is active and as needed to provide the Service, comply with legal obligations, resolve disputes and enforce agreements. You may request deletion subject to legal retention requirements.</P>

      <H>9. Children</H>
      <P>The Service is intended for business users and is not directed to individuals under 18. We do not knowingly collect data from children.</P>

      <H>10. Changes and contact</H>
      <P>We may update this Policy from time to time; material changes will be posted here with a revised date. For any privacy request, contact {EMAIL}.</P>
    </LegalLayout>
  );
}

/* ============================ TERMS OF SERVICE ============================ */
export function TermsOfService() {
  return (
    <LegalLayout title="Terms of Service" path="/legal/terms"
      description="The terms governing your use of the LeadNation website, mobile app and Trade Command Center services.">
      <P>These Terms of Service ("Terms") govern your access to and use of the {PRODUCT} website, mobile application and services operated by {COMPANY}. By accessing or using the Service, you agree to these Terms.</P>

      <H>1. The Service</H>
      <P>{PRODUCT} provides a global trade-intelligence platform including the Trade Command Center (Trade Projects, costing, simulations, scenarios, decision analysis and reports), trade tools, and an AI assistant (the "LeadNation Brain"). Features are provided on an "as-is" and "as-available" basis.</P>

      <H>2. Accounts and identity</H>
      <UL items={[
        "Authentication is provided via Google Firebase; you are responsible for keeping your credentials secure.",
        "One shared identity (same Firebase account and 5-digit Customer ID) is used across our website and mobile app. Customer IDs are numeric, five digits, unique, immutable, and 00001 is reserved for the platform Super Admin.",
        "You must provide accurate information and are responsible for all activity under your account.",
      ]} />

      <H>3. Acceptable use</H>
      <UL items={[
        "Do not misuse the Service, attempt to breach security, reverse engineer, scrape at scale, or disrupt operations.",
        "Do not upload unlawful, infringing, or harmful content.",
        "Do not use the Service to violate export controls, sanctions, or applicable trade laws.",
      ]} />

      <H>4. Subscriptions, payments and downloads</H>
      <UL items={[
        "Paid plans, pay-per-report downloads and subscriptions are billed through Stripe and/or Razorpay in the currency shown at checkout.",
        "Prices are set by us and may change; the price shown at the time of purchase applies to that purchase.",
        "Subscriptions renew for the stated period unless cancelled. Refunds are governed by our Refund & Cancellation Policy.",
      ]} />

      <H>5. AI features and no professional advice</H>
      <P>AI-generated explanations, recommendations, scores and reports are informational aids only. They are not legal, tax, customs, financial, or professional advice. You are solely responsible for verifying duties, taxes, freight, compliance requirements and any decisions you make. See our Disclaimer.</P>

      <H>6. Intellectual property</H>
      <P>The Service, including software, engines, content and branding, is owned by {COMPANY} and protected by law. You retain ownership of the business data and content you submit; you grant us a limited license to process it to operate the Service.</P>

      <H>7. User content & marketplace</H>
      <P>You are responsible for content you post (listings, profiles, documents). We may remove content that violates these Terms. We do not guarantee the accuracy of any user or third-party content.</P>

      <H>8. Limitation of liability</H>
      <P>To the maximum extent permitted by law, {COMPANY} is not liable for indirect, incidental, special or consequential damages, or for losses arising from reliance on trade data, AI output, or reports. Our total liability for any claim is limited to the amount you paid us in the 12 months preceding the claim.</P>

      <H>9. Indemnity</H>
      <P>You agree to indemnify {COMPANY} against claims arising from your misuse of the Service or violation of these Terms or applicable law.</P>

      <H>10. Termination</H>
      <P>We may suspend or terminate access for breach of these Terms. You may stop using the Service at any time; certain provisions survive termination.</P>

      <H>11. Governing law</H>
      <P>These Terms are governed by the laws of India, with courts at Ahilyanagar, Maharashtra having jurisdiction, without prejudice to mandatory consumer-protection rights in your country of residence.</P>

      <H>12. Contact</H>
      <P>Questions about these Terms: {EMAIL}.</P>
    </LegalLayout>
  );
}

/* ============================ COOKIE POLICY ============================ */
export function CookiePolicy() {
  return (
    <LegalLayout title="Cookie Policy" path="/legal/cookies"
      description="How LeadNation uses cookies and similar technologies on its website and app.">
      <P>This Cookie Policy explains how {PRODUCT} ({COMPANY}) uses cookies and similar technologies.</P>

      <H>1. What are cookies</H>
      <P>Cookies are small files stored on your device. Similar technologies include local storage and mobile identifiers used by our app.</P>

      <H>2. Types we use</H>
      <UL items={[
        "Essential: required for authentication (Firebase session), security, and core functionality — these cannot be disabled.",
        "Preferences: remember settings such as region, currency and language.",
        "Analytics (optional): Google Analytics 4 / Google Tag Manager, Microsoft Clarity and Meta Pixel — enabled only when configured. These help us understand usage and improve the Service.",
        "Payment/anti-fraud: set by Stripe/Razorpay during checkout.",
      ]} />

      <H>3. Managing cookies</H>
      <P>You can control cookies through your browser settings and, for mobile, your device advertising/identifier settings. Blocking essential cookies may break sign-in and core features. Analytics tools load only when valid IDs are configured; no analytics run with placeholder configuration.</P>

      <H>4. Mobile app</H>
      <P>Our mobile app uses local storage (e.g., AsyncStorage) to cache projects and enable offline drafts. This data stays on your device unless synced to your account.</P>

      <H>5. Changes and contact</H>
      <P>We may update this Policy; the revised date will appear above. Contact {EMAIL} for questions.</P>
    </LegalLayout>
  );
}

/* ============================ DISCLAIMER ============================ */
export function Disclaimer() {
  return (
    <LegalLayout title="Disclaimer" path="/legal/disclaimer"
      description="Trade data, AI output and reports provided by LeadNation are for informational purposes only.">
      <H>1. Informational purpose only</H>
      <P>All information provided by {PRODUCT} — including customs duties, taxes, FX rates, freight estimates, landed costs, trade scores, simulations, decision analyses, buyer/supplier and market intelligence, and generated reports — is for general informational and planning purposes only. It does not constitute legal, tax, customs, financial, or professional advice.</P>

      <H>2. Trade data accuracy</H>
      <P>Trade data is aggregated from third-party and government sources (e.g., World Bank WITS/UNCTAD TRAINS, OEC, exchange-rate feeds) and may be delayed, incomplete, or inaccurate. Tariffs, taxes, incentives and regulations change frequently and vary by product, origin, destination and shipment. You must independently verify all figures with official authorities and licensed professionals before acting.</P>

      <H>3. AI limitations</H>
      <P>The LeadNation Brain and other AI features generate explanations, recommendations and summaries based on the context provided. AI output can be incomplete or wrong and must not be relied upon as authoritative. Deterministic engines produce the underlying numbers; AI narrates them. Always confirm critical decisions with qualified experts.</P>

      <H>4. Estimates and confidence</H>
      <P>Where a value is estimated (for example, freight where no live feed is connected), it is labelled as an estimate with an indicative confidence and assumptions. Estimates are not quotations and are not binding on any carrier, authority or counterparty.</P>

      <H>5. No warranty & limitation</H>
      <P>The Service is provided "as is" without warranties of any kind. {COMPANY} is not liable for any loss or damage arising from reliance on the information, AI output, or reports provided. Your use is at your own risk.</P>

      <H>6. Contact</H>
      <P>Questions: {EMAIL}.</P>
    </LegalLayout>
  );
}

/* ============================ REFUND & CANCELLATION ============================ */
export function RefundPolicy() {
  return (
    <LegalLayout title="Refund & Cancellation Policy" path="/legal/refund"
      description="LeadNation refund, cancellation and billing policy for subscriptions and paid reports.">
      <P>This Policy governs payments made to {COMPANY} for {PRODUCT} subscriptions and pay-per-report downloads, processed via Stripe and/or Razorpay.</P>

      <H>1. Subscriptions</H>
      <UL items={[
        "Subscriptions (monthly or annual) grant unlimited report downloads for the billing period.",
        "You may cancel at any time; cancellation stops future renewals. Access continues until the end of the current paid period.",
        "Unless required by applicable law, subscription fees already paid are non-refundable for the current period.",
      ]} />

      <H>2. Pay-per-report downloads</H>
      <P>Because a paid report delivers digital content immediately upon purchase, these purchases are generally non-refundable once the report has been generated or downloaded. Your first report download is provided free.</P>

      <H>3. Eligible refunds</H>
      <UL items={[
        "Duplicate or accidental charges.",
        "A confirmed technical failure on our side that prevented delivery of the purchased content and could not be resolved.",
        "Any refund required by mandatory consumer-protection law in your jurisdiction.",
      ]} />

      <H>4. How to request</H>
      <P>Email {EMAIL} within 7 days of the charge with your Customer ID, transaction reference and reason. Approved refunds are issued to the original payment method via the relevant provider (Stripe/Razorpay); processing times depend on the provider and your bank.</P>

      <H>5. Chargebacks</H>
      <P>Please contact us before initiating a chargeback so we can resolve the issue directly.</P>

      <H>6. Changes and contact</H>
      <P>We may update this Policy; the revised date appears above. Questions: {EMAIL}.</P>
    </LegalLayout>
  );
}
