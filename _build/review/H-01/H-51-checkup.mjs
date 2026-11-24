// A picture button with no alt text gets an empty name: 'Your "" button leads to an error page'.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ body: '<a href="/order-online"><img src="order-button.png"></a>' }) } }));
const h = await e2e('goldencrust.com', web);
console.log(h.text('finds1'));
if (/""/.test(h.text('finds1'))) fail('headline item reads: ' + h.text('finds1').split('People')[0]);
pass();
