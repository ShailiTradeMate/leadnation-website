import React from "react";
import "@/index.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import CustomsCompliance from "@/pages/CustomsCompliance";
import TradeNews from "@/pages/TradeNews";
import TradeNewsDetail from "@/pages/TradeNewsDetail";
import Expo from "@/pages/Expo";
import ProductInfo from "@/pages/ProductInfo";
import Contact from "@/pages/Contact";
import DutyCalculator from "@/pages/DutyCalculator";
import CountryProfile from "@/pages/CountryProfile";
import CountriesIndex from "@/pages/CountriesIndex";
import Academy from "@/pages/Academy";
import AcademyDetail from "@/pages/AcademyDetail";
import Intelligence from "@/pages/Intelligence";
import ToolsHub from "@/pages/ToolsHub";
import HsnFinder from "@/pages/tools/HsnFinder";
import LandedCostCalculator from "@/pages/tools/LandedCostCalculator";
import ExportIncentiveFinder from "@/pages/tools/ExportIncentiveFinder";
import ProductResearch from "@/pages/tools/ProductResearch";
import FindBuyers from "@/pages/tools/FindBuyers";
import ExportReadiness from "@/pages/tools/ExportReadiness";
import AiAssistant from "@/pages/AiAssistant";
import BrainPage from "@/pages/Brain";
import ProductDetail, { ProductsIndex } from "@/pages/Products";
import CorridorDetail, { CorridorsIndex } from "@/pages/Corridors";
import HsnDetail from "@/pages/HsnDetail";
import IndustryDetail, { IndustriesIndex } from "@/pages/Industries";
import BlogDetail, { BlogIndex } from "@/pages/Blog";
import Suppliers from "@/pages/Suppliers";  // retired route
import Marketplace from "@/pages/Marketplace";
import Network from "@/pages/Network";
import ServiceDetail, { ServicesHub } from "@/pages/Services";
import DirectoryDetail, { DirectoryHub } from "@/pages/Directory";
import GlobalSearch from "@/pages/GlobalSearch";
import AdminDashboard, { AdminLogin } from "@/pages/admin/AdminDashboard";
import AdminBrain from "@/pages/admin/AdminBrain";
import { AuthProvider } from "@/lib/AuthContext";
import { ProjectProvider } from "@/lib/ProjectContext";
import CommandCenter from "@/pages/CommandCenter";
import { Login, Signup, ForgotPassword, Account } from "@/pages/Auth";
import AccountPage from "@/pages/AccountPage";

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <ProjectProvider>
          <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/command-center" element={<CommandCenter />} />
            <Route path="/customs-compliance" element={<CustomsCompliance />} />
            <Route path="/trade-news" element={<TradeNews />} />
            <Route path="/trade-news/:id" element={<TradeNewsDetail />} />
            <Route path="/expo" element={<Expo />} />
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
        </Layout>
          </ProjectProvider>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
