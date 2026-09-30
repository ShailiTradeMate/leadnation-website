// Reproducible offline dataset. Source: country-state-city (ODbL-1.0).
const fs = require('fs');
const path = require('path');
const { Country, State, City } = require('country-state-city');
const root = path.resolve(__dirname, '..');
const names = { PS: 'Palestine', VA: 'Vatican City', TR: 'Turkey', CZ: 'Czech Republic' };
const countries = Country.getAllCountries().map(c => ({
  code: c.isoCode, name: names[c.isoCode] || c.name, flag: c.flag,
  dial: c.isoCode === 'VA' ? '+39' : `+${c.phonecode.replace(/\D/g, '')}`,
})).sort((a, b) => a.name.localeCompare(b.name, 'en'));
fs.mkdirSync(path.join(root, 'public/geo'), { recursive: true });
fs.writeFileSync(path.join(root, 'src/data/countries.json'), JSON.stringify(countries));
fs.mkdirSync(path.join(root, '../backend/data'), { recursive: true });
fs.writeFileSync(path.join(root, '../backend/data/countries.json'), JSON.stringify(countries));
const allStates = State.getAllStates();
const allCities = City.getAllCities();
for (const country of countries) {
  const states = allStates.filter(s => s.countryCode === country.code).map(s => ({ code: s.isoCode, name: s.name }));
  const cities = allCities.filter(c => c.countryCode === country.code).map(c => [c.name, c.stateCode]);
  fs.writeFileSync(path.join(root, `public/geo/${country.code}.json`), JSON.stringify({ states, cities }));
}
fs.copyFileSync(require.resolve('country-state-city/LICENSE'), path.join(root, 'public/geo/LICENSE'));
fs.copyFileSync(require.resolve('country-state-city/LICENSE'), path.join(root, '../backend/data/GEOGRAPHY_LICENSE'));
console.log(`Generated ${countries.length} countries, ${allStates.length} subdivisions, ${allCities.length} cities.`);