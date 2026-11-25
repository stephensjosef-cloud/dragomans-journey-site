// <meta name="robots" content="index, follow, max-image-preview:none"> is read as noindex.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ head: '<meta name="robots" content="index, follow, max-image-preview:none">' }) } }));
const h = await e2e('goldencrust.com', web);
console.log(h.text('finds2'));
if (/not to list it/.test(h.text('finds2'))) fail('an indexable page (index, follow, max-image-preview:none) is told "Your page tells search engines not to list it"');
pass();
