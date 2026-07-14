import { social, EMAIL, PHONE } from "@/lib/brand";

const ig = social("instagram");
const li = social("linkedin");

export const CONTACT = {
  email: EMAIL,
  whatsapp: "+918237161088",
  whatsappDisplay: "+91 82371 61088",
  address:
    "Tirthankar, Central Bank of India, Ekveera Chowk, Pipeline Rd, Savedi, Ahilyanagar, Maharashtra 414003, India",
  lat: 19.126793986535226,
  lng: 74.7452378072622,
  phone: PHONE,
  instagram: ig?.handle,
  instagramUrl: ig?.url,
  linkedin: li?.handle,
  linkedinUrl: li?.url,
};

export const APP_LINKS = {
  android: "#coming-soon-android",
  ios: "#coming-soon-ios",
};
