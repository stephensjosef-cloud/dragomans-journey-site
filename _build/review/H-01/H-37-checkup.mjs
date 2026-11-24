// The Worker has no overall deadline: 25 action links on a host that never answers take 25 x 8 s, past the page's
// 2-minute limit, so the owner waits 2 minutes and is told "I couldn't reach the checker just now".
// Timers are sped up 1000x and the virtual time added up; nothing waits for real.
import { W, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const links = Array.from({ length: 25 }, (_, i) => '<a href="https://slowbooking.example/slot/' + i + '">Book slot ' + (i + 1) + '</a>').join(' ');
const routes = base({ [HOME]: { body: shopPage({ body: links }) } });
const web = fakeWeb(new Proxy(routes, { get: (t, u) => t[u] || (String(u).includes('slowbooking') ? { hang: true } : undefined) }));
let virtual = 0;
const real = globalThis.setTimeout;
globalThis.setTimeout = (fn, ms, ...a) => { const t = real(() => { virtual += ms; fn(...a); }, ms / 1000, ...a); t.unref = () => t; return t; };
const out = await W.runCheck('goldencrust.com', web);
globalThis.setTimeout = real;
console.log('virtual seconds', virtual / 1000, 'links', out.links.length, out.links.map((l) => l.status).join(','));
if (virtual > 120000) fail('one check runs ' + virtual / 1000 + ' s; checkup.html gives up at 120 s and says "I couldn\'t reach the checker just now"');
pass();
