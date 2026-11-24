// A storefront bakery whose structured data is the common name-and-url Organization block (no address) is taken
// for a business with no shop: no word that its address and hours can't be read, and "AI tools can read your basic facts."
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const ld = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Golden Crust Bakery","url":"https://goldencrust.com/","telephone":"+1-707-555-0100"}</script>';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ head: ld, address: '<img src="map.png" alt="map">', hours: '<img src="hours.png" alt="our hours">' }) } }));
const h = await e2e('goldencrust.com', web);
console.log(h.report());
const r = h.text('finds2') + ' ' + h.text('facts');
if (!/address/i.test(r) && !/hours/i.test(r)) fail('no address and no hours anywhere readable, yet the AI card never mentions either' + (h.$('aiok').hidden ? '' : ' and says "AI tools can read your basic facts."'));
pass();
