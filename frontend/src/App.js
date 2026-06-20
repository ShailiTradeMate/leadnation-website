import React from "react";
import "@/index.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import CustomsCompliance from "@/pages/CustomsCompliance";
import TradeNews from "@/pages/TradeNews";
import Expo from "@/pages/Expo";
import ProductInfo from "@/pages/ProductInfo";
import Contact from "@/pages/Contact";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/customs-compliance" element={<CustomsCompliance />} />
          <Route path="/trade-news" element={<TradeNews />} />
          <Route path="/expo" element={<Expo />} />
          <Route path="/product-info" element={<ProductInfo />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
