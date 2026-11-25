// A small page whose server stops sending mid-page (or is slow past 8 s) is reported as "over 1.5 MB".
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const html = new TextEncoder().encode(shopPage());
const web = fakeWeb(base({ [HOME]: { stream: () => new ReadableStream({
  start(c) { c.enqueue(html.slice(0, 4000)); },          // 4 KB arrives...
  pull(c) { c.error(new TypeError('connection reset')); } // ...then the connection drops
}) } }));
const h = await e2e('goldencrust.com', web);
const r = h.report();
console.log('bytes', h.out.bytes, 'cut', h.out.cut, '\n', h.text('finds1'));
if (/over 1\.5 MB/.test(r)) fail('a 4 KB page that stopped mid-send is reported as "over 1.5 MB"');
pass();
