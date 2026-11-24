// An old button left inside an HTML comment (invisible to visitors) is reported as a broken button.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ body: '<!-- old: <a href="/book-2019">Book a cake tasting</a> -->' }) } }));
const h = await e2e('goldencrust.com', web);
console.log(h.text('rep1-h'), '|', h.text('finds1'));
if (/Book a cake tasting/.test(h.text('finds1'))) fail('a link inside <!-- --> (not on the page) is reported: ' + h.text('finds1').split('People')[0]);
pass();
