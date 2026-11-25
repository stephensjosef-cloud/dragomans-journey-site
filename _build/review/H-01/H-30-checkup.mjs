// Hours written the everyday way, "Mon-Fri 9-5, Sat 10-4", are reported as missing.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ hours: '<p>Hours: Mon–Fri 9–5, Sat 10–4</p>' }) } }));
const h = await e2e('goldencrust.com', web);
console.log(h.text('finds2'));
if (/couldn't find your opening hours/.test(h.text('finds2'))) fail('"Hours: Mon–Fri 9–5, Sat 10–4" on the page, yet: "I couldn\'t find your opening hours in your page text"');
pass();
