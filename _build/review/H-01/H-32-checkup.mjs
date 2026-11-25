// A page served as ISO-8859-1 is decoded as UTF-8: "Café Verde" shows as "Caf� Verde" in the
// "should match your Google listing exactly" box.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const body = Uint8Array.from(Buffer.from(shopPage({ title: 'Café Verde' }).replace('charset="utf-8"', 'charset="iso-8859-1"'), 'latin1'));
const web = fakeWeb(base({ [HOME]: { body, headers: { 'Content-Type': 'text/html; charset=iso-8859-1' } } }));
const h = await e2e('goldencrust.com', web);
const name = h.$$('#facts dd')[0].textContent;
console.log(JSON.stringify(name));
if (name !== 'Café Verde') fail('Name row shows ' + JSON.stringify(name) + ' for "Café Verde"');
pass();
