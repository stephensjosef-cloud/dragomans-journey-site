// A "Book now" button pointing at a booking site whose domain no longer exists is counted as
// "couldn't test from here", and the headline says nothing is broken.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ body: '<a href="https://oldbookingsite.com/goldencrust">Book now</a>' }) } }),
  { 'oldbookingsite.com': [] });   // DNS: no such host
const h = await e2e('goldencrust.com', web);
console.log(h.out.links, '\n', h.text('rep1-h'), '|', h.text('note1'));
if (!/Book now/.test(h.text('finds1'))) fail('"Book now" to a domain that does not exist is not reported; note says: ' + h.text('note1'));
pass();
