// A site that only works on plain http (no certificate) is reported as down: "Your site didn't answer".
import { e2e, fakeWeb, shopPage, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb({
  'https://goldencrust.com/': { throws: 'TLS handshake failed' },
  'http://goldencrust.com/': { body: shopPage() },
  'http://goldencrust.com/robots.txt': { status: 404 }
});
const h = await e2e('goldencrust.com', web);
console.log(h.text('msg'), h.out);
if (/didn't answer/.test(h.text('msg'))) fail('http://goldencrust.com answers 200, but the owner is told "' + h.text('msg') + '"');
pass();
