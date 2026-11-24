// A link to a PDF menu (not a web page) gets the full web-page report: "10 things to fix", no title,
// not set up for phones, no phone number, and so on. Every fetch is stubbed; the live Worker is never called.
import { e2e, fakeWeb, base, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ 'https://goldencrust.com/menu.pdf': { body: '%PDF-1.4 binary', headers: { 'Content-Type': 'application/pdf' } } }));
const h = await e2e('goldencrust.com/menu.pdf', web);
const head = h.text('rep1-h') || '';
if (/things? to fix/.test(head) && /no title/.test(h.text('finds1') || '')) fail('a PDF is checked as a web page: "' + head + '", including "Your page has no title"');
pass(head || h.text('msg'));
