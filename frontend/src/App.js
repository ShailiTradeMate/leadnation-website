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
            <Route path="/tools/duty-calculator" element={<DutyCalculator />} />
            <Route path="/countries" element={<CountriesIndex />} />
            <Route path="/countries/:slug" element={<CountryProfile />} />
            <Route path="/academy" element={<Academy />} />
            <Route path="/intelligence" element={<Intelligence />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
