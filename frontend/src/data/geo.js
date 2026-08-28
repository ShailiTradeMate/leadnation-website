// Countries + states for the Verified Buyer profile form.
// States provided for major trading nations; others fall back to a free-text input.
export const COUNTRIES = [
  "India", "United States", "United Arab Emirates", "United Kingdom", "China", "Germany",
  "Singapore", "Australia", "Canada", "France", "Netherlands", "Italy", "Spain", "Japan",
  "South Korea", "Saudi Arabia", "Qatar", "Kuwait", "Oman", "Bahrain", "Turkey", "Vietnam",
  "Thailand", "Malaysia", "Indonesia", "Philippines", "Bangladesh", "Sri Lanka", "Nepal",
  "Pakistan", "Brazil", "Mexico", "Argentina", "Chile", "Colombia", "South Africa", "Nigeria",
  "Kenya", "Egypt", "Morocco", "Ethiopia", "Ghana", "Tanzania", "Russia", "Poland", "Belgium",
  "Switzerland", "Sweden", "Norway", "Denmark", "Finland", "Ireland", "Portugal", "Austria",
  "Greece", "Czech Republic", "Hungary", "Romania", "Ukraine", "Israel", "Jordan", "Lebanon",
  "New Zealand", "Hong Kong", "Taiwan", "Myanmar", "Cambodia", "Kazakhstan", "Uzbekistan",
  "Peru", "Ecuador", "Venezuela", "Other",
];

const STATES = {
  "India": [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
  ],
  "United States": [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
    "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
  ],
  "United Arab Emirates": ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"],
  "Canada": ["Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Northwest Territories", "Nunavut", "Yukon"],
  "Australia": ["New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia", "Tasmania", "Australian Capital Territory", "Northern Territory"],
};

export const statesFor = (country) => STATES[country] || [];
