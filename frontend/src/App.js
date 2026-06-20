import React from "react";
import "@/index.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import CustomsCompliance from "@/pages/CustomsCompliance";
import TradeNews from "@/pages/TradeNews";
import Expo from "@/pages/Expo";
import ProductInfo from "@/pages/ProductInfo";
import Contact from "@/pages/Contact";
import DutyCalculator from "@/pages/DutyCalculator";
import CountryProfile from "@/pages/CountryProfile";
import CountriesIndex from "@/pages/CountriesIndex";
import Academy from "@/pages/Academy";
import Intelligence from "@/pages/Intelligence";
import ToolsHub from "@/pages/ToolsHub";
import HsnFinder from "@/pages/tools/HsnFinder";
import LandedCostCalculator from "@/pages/tools/LandedCostCalculator";
import ExportIncentiveFinder from "@/pages/tools/ExportIncentiveFinder";
import ProductResearch from "@/pages/tools/ProductResearch";
import FindBuyers from "@/pages/tools/FindBuyers";
import ExportReadiness from "@/pages/tools/ExportReadiness";
import AiAssistant from "@/pages/AiAssistant";
import ProductDetail, { ProductsIndex } from "@/pages/Products";
import CorridorDetail, { CorridorsIndex } from "@/pages/Corridors";
import HsnDetail from "@/pages/HsnDetail";
import IndustryDetail, { IndustriesIndex } from "@/pages/Industries";
import BlogDetail, { BlogIndex } from "@/pages/Blog";
import Suppliers from "@/pages/Suppliers";
import Marketplace from "@/pages/Marketplace";
import Network from "@/pages/Network";

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/customs-compliance" element={<CustomsCompliance />} />
            <Route path="/trade-news" element={<TradeNews />} />
            <Route path="/expo" element={<Expo />} />
            <Route path="/product-info" element={<ProductInfo />} />
            <Route path="/contact" element={<Contact />} />

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
            <Route path="/ai-assistant" element={<AiAssistant />} />

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

            {/* Network & Marketplace */}
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/marketplace" element={<Marketplace />} />
            <Route path="/network" element={<Network />} />

            {/* Content */}
            <Route path="/academy" element={<Academy />} />
            <Route path="/intelligence" element={<Intelligence />} />
            <Route path="/blog" element={<BlogIndex />} />
            <Route path="/blog/:slug" element={<BlogDetail />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
