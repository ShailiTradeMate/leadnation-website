import { social, EMAIL, PHONE } from "@/lib/brand";

const ig = social("instagram");
const li = social("linkedin");

export const CONTACT = {
  email: EMAIL,
  whatsapp: "+918237161088",
  whatsappDisplay: "+91 82371 61088",
  address:
    "Savedi, Ahilyanagar, Maharashtra 414003, India",
  lat: 19.126793986535226,
  lng: 74.7452378072622,
  phone: PHONE,
  instagram: ig?.handle,
  instagramUrl: ig?.url,
  linkedin: li?.display,
  linkedinUrl: li?.url,
};
