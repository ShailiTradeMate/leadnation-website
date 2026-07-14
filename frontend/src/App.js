import React, { Suspense, lazy } from "react";
import "@/index.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Layout from "@/components/Layout";
import CookieConsent from "@/components/CookieConsent";
import ScrollToTop from "@/components/ScrollToTop";
import { AuthProvider } from "@/lib/AuthContext";
import { ProjectProvider } from "@/lib/ProjectContext";
import Home from "@/pages/Home"; // eager — LCP-critical landing page

// Route-level code splitting: every non-landing page is a separate chunk,
// shrinking the initial JS bundle and improving first-load Core Web Vitals.
const CommandCenter = lazy(() => import("@/pages/CommandCenter"));
const CustomsCompliance = lazy(() => import("@/pages/CustomsCompliance"));
const TradeNews = lazy(() => import("@/pages/TradeNews"));
const TradeNewsDetail = lazy(() => import("@/pages/TradeNewsDetail"));
const Expo = lazy(() => import("@/pages/Expo"));
const EventSubmit = lazy(() => import("@/pages/EventSubmit"));
const EventDetail = lazy(() => import("@/pages/EventDetail"));
const ProductInfo = lazy(() => import("@/pages/ProductInfo"));
const Contact = lazy(() => import("@/pages/Contact"));
const GlobalSearch = lazy(() => import("@/pages/GlobalSearch"));
const Pricing = lazy(() => import("@/pages/Pricing"));

const ToolsHub = lazy(() => import("@/pages/ToolsHub"));
const DutyCalculator = lazy(() => import("@/pages/DutyCalculator"));
const HsnFinder = lazy(() => import("@/pages/tools/HsnFinder"));
const LandedCostCalculator = lazy(() => import("@/pages/tools/LandedCostCalculator"));
const ExportIncentiveFinder = lazy(() => import("@/pages/tools/ExportIncentiveFinder"));
const ProductResearch = lazy(() => import("@/pages/tools/ProductResearch"));
const FindBuyers = lazy(() => import("@/pages/tools/FindBuyers"));
const ExportReadiness = lazy(() => import("@/pages/tools/ExportReadiness"));

const BrainPage = lazy(() => import("@/pages/Brain"));
const AiAssistant = lazy(() => import("@/pages/AiAssistant"));

const CountriesIndex = lazy(() => import("@/pages/CountriesIndex"));
const CountryProfile = lazy(() => import("@/pages/CountryProfile"));
const ProductsIndex = lazy(() => import("@/pages/Products").then((m) => ({ default: m.ProductsIndex })));
const ProductDetail = lazy(() => import("@/pages/Products"));
const CorridorsIndex = lazy(() => import("@/pages/Corridors").then((m) => ({ default: m.CorridorsIndex })));
const CorridorDetail = lazy(() => import("@/pages/Corridors"));
const HsnDetail = lazy(() => import("@/pages/HsnDetail"));
const IndustriesIndex = lazy(() => import("@/pages/Industries").then((m) => ({ default: m.IndustriesIndex })));
const IndustryDetail = lazy(() => import("@/pages/Industries"));

const Marketplace = lazy(() => import("@/pages/Marketplace"));
const Network = lazy(() => import("@/pages/Network"));
const ServicesHub = lazy(() => import("@/pages/Services").then((m) => ({ default: m.ServicesHub })));
const ServiceDetail = lazy(() => import("@/pages/Services"));

const Academy = lazy(() => import("@/pages/Academy"));
const AcademyDetail = lazy(() => import("@/pages/AcademyDetail"));
const Intelligence = lazy(() => import("@/pages/Intelligence"));
const BlogIndex = lazy(() => import("@/pages/Blog").then((m) => ({ default: m.BlogIndex })));
const BlogDetail = lazy(() => import("@/pages/Blog"));

const Login = lazy(() => import("@/pages/Auth").then((m) => ({ default: m.Login })));
const Signup = lazy(() => import("@/pages/Auth").then((m) => ({ default: m.Signup })));
const ForgotPassword = lazy(() => import("@/pages/Auth").then((m) => ({ default: m.ForgotPassword })));
const AccountPage = lazy(() => import("@/pages/AccountPage"));

const AdminDashboard = lazy(() => import("@/pages/admin/AdminDashboard"));
const AdminLogin = lazy(() => import("@/pages/admin/AdminDashboard").then((m) => ({ default: m.AdminLogin })));
const AdminBrain = lazy(() => import("@/pages/admin/AdminBrain"));

const PrivacyPolicy = lazy(() => import("@/pages/Legal").then((m) => ({ default: m.PrivacyPolicy })));
const TermsOfService = lazy(() => import("@/pages/Legal").then((m) => ({ default: m.TermsOfService })));
const CookiePolicy = lazy(() => import("@/pages/Legal").then((m) => ({ default: m.CookiePolicy })));
const Disclaimer = lazy(() => import("@/pages/Legal").then((m) => ({ default: m.Disclaimer })));
const RefundPolicy = lazy(() => import("@/pages/Legal").then((m) => ({ default: m.RefundPolicy })));

function RouteFallback() {
  return (
    <div className="min-h-[60vh] grid place-items-center" data-testid="route-loading">
      <div className="w-8 h-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
    </div>
  );
}

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <ProjectProvider>
            <Layout>
              <ScrollToTop />
              <Suspense fallback={<RouteFallback />}>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/pricing" element={<Pricing />} />
                  <Route path="/legal/privacy" element={<PrivacyPolicy />} />
                  <Route path="/legal/terms" element={<TermsOfService />} />
                  <Route path="/legal/cookies" element={<CookiePolicy />} />
                  <Route path="/legal/disclaimer" element={<Disclaimer />} />
                  <Route path="/legal/refund" element={<RefundPolicy />} />
                  <Route path="/command-center" element={<CommandCenter />} />
                  <Route path="/customs-compliance" element={<CustomsCompliance />} />
                  <Route path="/trade-news" element={<TradeNews />} />
                  <Route path="/trade-news/:id" element={<TradeNewsDetail />} />
                  <Route path="/expo" element={<Expo />} />
                  <Route path="/expo/submit" element={<EventSubmit />} />
                  <Route path="/expo/:id" element={<EventDetail />} />
                  <Route path="/product-info" element={<ProductInfo />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/search" element={<GlobalSearch />} />

                  {/* Tools */}
                  <Route path="/tools" element={<ToolsHub />} />
                  <Route path="/tools/duty-calculator" element={<DutyCalculator />} />
                  <Route path="/tools/hsn-finder" element={<HsnFinder />} />
                  <Route path="/tools/landed-cost-calculator" element={<LandedCostCalculator />} />
                  <Route path="/tools/export-incentive-finder" element={<ExportIncentiveFinder />} />
                  <Route path="/tools/product-research" element={<ProductResearch />} />
                  <Route path="/tools/find-buyers" element={<FindBuyers />} />
                  <Route path="/tools/export-readiness" element={<ExportReadiness />} />

                  {/* AI */}
                  <Route path="/brain" element={<BrainPage />} />
                  <Route path="/ai-assistant" element={<Navigate to="/brain" replace />} />
                  <Route path="/ai-assistant-legacy" element={<AiAssistant />} />

                  {/* Discovery layer */}
                  <Route path="/countries" element={<CountriesIndex />} />
                  <Route path="/countries/:slug" element={<CountryProfile />} />
                  <Route path="/products" element={<ProductsIndex />} />
                  <Route path="/products/:slug" element={<ProductDetail />} />
                  <Route path="/corridors" element={<CorridorsIndex />} />
                  <Route path="/corridors/:slug" element={<CorridorDetail />} />
                  <Route path="/hsn/:code" element={<HsnDetail />} />
                  <Route path="/industries" element={<IndustriesIndex />} />
                  <Route path="/industries/:slug" element={<IndustryDetail />} />

                  {/* In-app features */}
                  <Route path="/suppliers" element={<Navigate to="/" replace />} />
                  <Route path="/marketplace" element={<Marketplace />} />
                  <Route path="/network" element={<Network />} />

                  {/* Business Services */}
                  <Route path="/services" element={<ServicesHub />} />
                  <Route path="/services/:slug" element={<ServiceDetail />} />

                  {/* Directory (retired — fake data removed) */}
                  <Route path="/directory" element={<Navigate to="/" replace />} />
                  <Route path="/directory/:kind" element={<Navigate to="/" replace />} />

                  {/* Content */}
                  <Route path="/academy" element={<Academy />} />
                  <Route path="/academy/:slug" element={<AcademyDetail />} />
                  <Route path="/intelligence" element={<Intelligence />} />
                  <Route path="/blog" element={<BlogIndex />} />
                  <Route path="/blog/:slug" element={<BlogDetail />} />

                  {/* Accounts (shared Firebase identity) */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/signup" element={<Signup />} />
                  <Route path="/forgot-password" element={<ForgotPassword />} />
                  <Route path="/account" element={<AccountPage />} />

                  {/* Admin */}
                  <Route path="/admin-login" element={<AdminLogin />} />
                  <Route path="/admin-cms" element={<AdminDashboard />} />
                  <Route path="/admin/brain" element={<AdminBrain />} />
                  <Route path="/admin/leads" element={<AdminDashboard />} />
                </Routes>
              </Suspense>
            </Layout>
            <CookieConsent />
          </ProjectProvider>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
