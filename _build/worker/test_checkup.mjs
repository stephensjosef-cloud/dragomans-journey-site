// Checks the checkup Worker with no network: node test_checkup.mjs [path/to/local.html]
// Safety rules, the link classifier, and the "Can AI find you?" checks (8a to 8e),
// each on small made-up HTML and robots.txt strings (T-04, Nov 12, 2026).
// With a path (or when ../out/local.html exists), it also runs the site's own
// local.html through the structured-data check (T-04 step 12).
// Prints "<passed>/<total> passed" and exits 1 on any failure.
import fs from 'fs';
import os from 'os';
import path from 'path';
import { pathToFileURL, fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'checkup-'));
const NAMES = ['parseTarget', 'hostProblem', 'isPrivateIPv4', 'isPrivateIPv6', 'dnsProblem', 'safeFetch', 'readCapped',
  'actionKind', 'classifyHref', 'actionLinks', 'basics', 'parseRobots', 'robotsAllows', 'aiReaders', 'metaTags',
  'structuredData', 'textFacts', 'rawText', 'runCheck', 'tooSoon', 'AI_BOTS', 'UA', 'MAX_BYTES', 'MAX_LINKS'];
const src = fs.readFileSync(path.join(here, 'checkup.js'), 'utf8') + '\nexport const __t = { ' + NAMES.join(', ') + ' };\n';
const file = path.join(tmp, 'checkup.mjs');
fs.writeFileSync(file, src);
const mod = await import(pathToFileURL(file).href);
const W = mod.default, T = mod.__t;

// node test_checkup.mjs --sample: print the Worker's answer for a made-up site, for the page test in test_new.py.
if (process.argv.includes('--sample')) {
  const home = `<!doctype html><html><head><title>Crumb Bakery</title><meta property="og:site_name" content="Crumb Bakery">
    <script type="application/ld+json">{"@context":"https://schema.org","@type":"Bakery","name":"Crumb Bakery","telephone":"(707) 555-0199",
    "address":{"@type":"PostalAddress","streetAddress":"12 Main St","addressLocality":"Santa Rosa","addressRegion":"CA"},"url":"https://crumb.example/"}</script>
    </head><body><h1>Crumb Bakery</h1><p>${'Bread, buns and cakes baked every morning in Santa Rosa. '.repeat(12)}</p>
    <p>Call us at (707) 555-0134.</p><address>12 Main St, Santa Rosa, CA</address>
    <a href="/book">Book Now</a><a href="/order">Order online</a><a href="#">Donate</a><a href="mailto:hi@crumb.example">Email us</a></body></html>`;
  const fake = async (url, o) => {
    const at = {
      'https://crumb.example/': () => new Response(home, { headers: { 'Content-Type': 'text/html' } }),
      'http://crumb.example/': () => new Response(o.method === 'HEAD' ? null : home, { headers: { 'Content-Type': 'text/html' } }),
      'https://crumb.example/order': () => new Response(null, { status: 200 }),
      'https://crumb.example/book': () => new Response(null, { status: 500 }),
      'https://crumb.example/robots.txt': () => new Response('User-agent: OAI-SearchBot\nDisallow: /\n\nUser-agent: GPTBot\nDisallow: /\n', { headers: { 'Content-Type': 'text/plain' } })
    }[url];
    return at ? at() : new Response('', { status: 404 });
  };
  console.log(JSON.stringify(await T.runCheck('crumb.example', { fetch: fake, resolve: async () => ['93.184.216.34'] })));
  fs.rmSync(tmp, { recursive: true, force: true });
  process.exit(0);
}

const ok = [], bad = [];
const check = (name, cond, detail = '') => (cond ? ok : bad).push(name + (cond ? '' : '  ' + detail));
const J = (x) => JSON.stringify(x);

// ---------------------------------------------------------------- safety
for (const [input, want] of [
  ['https://example.com', 'https://example.com/'], ['example.com/menu', 'https://example.com/menu'],
  ['http://example.com:80/x', 'http://example.com/x'], ['https://example.com:443', 'https://example.com/'],
  ['http://example.com:443/', 'http://example.com:443/'], ['https://Example.COM/#top', 'https://example.com/']]) {
  check(`allowed: ${input}`, T.parseTarget(input).url === want, J(T.parseTarget(input)));
}
for (const [input, why] of [
  ['', 'empty'], ['ftp://example.com/', 'scheme'], ['file:///etc/passwd', 'scheme'], ['javascript:alert(1)', 'scheme'],
  ['https://example.com:8080/', 'port'], ['http://example.com:22', 'port'], ['https://user:pw@example.com/', 'credentials'],
  ['http://127.0.0.1/', 'ip'], ['http://10.0.0.5/', 'ip'], ['http://8.8.8.8/', 'ip'], ['http://2130706433/', 'ip'],
  ['http://0x7f.0.0.1/', 'ip'], ['http://[::1]/', 'ip'], ['http://[fd00::1]/', 'ip'], ['http://[2606:4700::1111]/', 'ip'],
  ['http://localhost/', 'private-name'], ['http://LOCALHOST./', 'private-name'], ['http://app.localhost/', 'private-name'],
  ['http://printer.local/', 'private-name'], ['http://db.internal/', 'private-name'], ['http://intranet/', 'private-name'],
  ['http://nas.home.arpa/', 'private-name']]) {
  check(`refused (${why}): ${input || '(empty)'}`, T.parseTarget(input).error === why, J(T.parseTarget(input)));
}
for (const [ip, priv] of [['10.1.2.3', true], ['172.16.0.1', true], ['172.31.255.255', true], ['172.32.0.1', false],
  ['192.168.1.1', true], ['127.0.0.1', true], ['169.254.169.254', true], ['100.64.0.1', true], ['0.0.0.0', true],
  ['224.0.0.1', true], ['192.0.2.10', true], ['192.0.78.9', false], ['8.8.8.8', false], ['104.16.1.1', false]]) {
  check(`IPv4 ${ip} is ${priv ? 'private' : 'public'}`, T.isPrivateIPv4(ip) === priv);
}
for (const [ip, priv] of [['::1', true], ['fd12:3456::1', true], ['fe80::1', true], ['::ffff:10.0.0.1', true],
  ['::ffff:8.8.8.8', false], ['2606:4700:4700::1111', false], ['2001:db8::1', true]]) {
  check(`IPv6 ${ip} is ${priv ? 'private' : 'public'}`, T.isPrivateIPv6(ip) === priv);
}
const zone = { 'shop.example': ['93.184.216.34'], 'rebind.example': ['192.168.0.10'], 'v6.example': ['2606:4700::6810:1'],
  'mixed.example': ['93.184.216.34', 'fd00::5'], 'gone.example': [], 'other.example': ['93.184.216.35'] };
const resolve = async (h) => (h in zone ? zone[h] : h === 'broken-dns.example' ? null : ['93.184.216.40']);
check('DNS: public address allowed', await T.dnsProblem('shop.example', { resolve }) === null);
check('DNS: name pointing at a private address refused', await T.dnsProblem('rebind.example', { resolve }) === 'private-ip');
check('DNS: one private address among public ones refused', await T.dnsProblem('mixed.example', { resolve }) === 'private-ip');
check('DNS: no such name', await T.dnsProblem('gone.example', { resolve }) === 'no-such-host');
check('DNS: lookup failure refused', await T.dnsProblem('broken-dns.example', { resolve }) === 'dns-failed');

// A made-up web for fetches: url -> { status, headers, body } (or a function of the request).
function web(pages) {
  const log = [];
  const f = async (url, opts) => {
    log.push({ url, method: opts.method, headers: opts.headers, redirect: opts.redirect, signal: !!opts.signal });
    let p = pages[url];
    if (typeof p === 'function') p = p(opts);
    if (!p) return new Response('not found', { status: 404 });
    if (p.throws) throw new Error(p.throws);
    return new Response(opts.method === 'HEAD' ? null : (p.body ?? ''), { status: p.status || 200, headers: p.headers || { 'Content-Type': 'text/html' } });
  };
  return { fetch: f, resolve, log };
}
const hop = (to) => ({ status: 301, headers: { Location: to } });
{
  const w = web({ 'https://shop.example/a': hop('/b'), 'https://shop.example/b': hop('https://other.example/c'),
    'https://other.example/c': hop('https://shop.example/d'), 'https://shop.example/d': { body: 'ok' } });
  const r = await T.safeFetch('https://shop.example/a', 'GET', w);
  check('redirects: 3 hops followed', !r.error && r.status === 200 && r.url === 'https://shop.example/d' && r.hops === 3, J({ e: r.error, u: r.url }));
  check('requests: manual redirects, our User-Agent, a timeout signal, no cookies',
    w.log.every((x) => x.redirect === 'manual' && x.headers['User-Agent'] === T.UA && x.signal && !Object.keys(x.headers).some((k) => /cookie/i.test(k))));
  check('User-Agent is the one the item names', T.UA === 'dragomansjourney-checkup/1.0 (+https://dragomansjourney.com/checkup.html)');
  r.stop && r.stop();
}
{
  const w = web({ 'https://shop.example/1': hop('/2'), 'https://shop.example/2': hop('/3'), 'https://shop.example/3': hop('/4'),
    'https://shop.example/4': hop('/5'), 'https://shop.example/5': { body: 'too far' } });
  const r = await T.safeFetch('https://shop.example/1', 'GET', w);
  check('redirects: a 4th hop is refused', r.error === 'too-many-redirects' && !w.log.some((x) => x.url.endsWith('/5')), J(r.error));
}
for (const [to, why] of [['http://127.0.0.1/admin', 'ip'], ['http://localhost:8080/', 'port'], ['http://localhost/', 'private-name'],
  ['https://rebind.example/', 'private-ip'], ['ftp://shop.example/', 'scheme'], ['http://169.254.169.254/latest/', 'ip']]) {
  const w = web({ 'https://shop.example/go': hop(to) });
  const r = await T.safeFetch('https://shop.example/go', 'GET', w);
  check(`redirects: a hop to ${to} is re-checked and refused`, r.error === why && w.log.length === 1, J(r));
}
{
  const big = new Uint8Array(2 * 1024 * 1024).fill(97);
  const r = await T.readCapped(new Response(big), T.MAX_BYTES);
  check('reads at most 1.5 MB and says it was cut', r.bytes === 1572864 && r.cut === true && r.text.length === 1572864, J({ b: r.bytes, c: r.cut }));
  const s = await T.readCapped(new Response('<p>small</p>'), T.MAX_BYTES);
  check('a small page is read whole', s.bytes === 12 && !s.cut);
}
{
  const w = web({ 'https://shop.example/': { throws: 'connection refused' } });
  const r = await T.safeFetch('https://shop.example/', 'GET', w);
  check('an unreachable site is reported, not thrown', r.error === 'unreachable', J(r));
}

// ---------------------------------------------------------------- the link classifier
for (const [text, href, kind] of [['Book Now', '/x', 'book'], ['Book an appointment', '', 'book'], ['Order online', '/x', 'order'],
  ['Contact us', '/x', 'contact'], ['Donate', '/x', 'donate'], ['Give now', '/x', 'donate'], ['See the menu', '/x', 'menu'],
  ['Schedule a visit', '/x', 'schedule'], ['Appointments', '/x', 'appointment'], ['Reserve a table', '/x', 'reserve'],
  ['Reservations', '/x', 'reserve'], ['Go', '/reservations', 'reserve'], ['Click here', 'https://order.example.com/', 'order'],
  ['Start', '/contact-us', 'contact'], ['About us', '/about', null], ['Border collies', '/dogs', null], ['Facebook', 'https://facebook.com/x', null]]) {
  check(`looks like ${kind || 'nothing'}: "${text}" ${href}`, T.actionKind(text, href) === kind, J(T.actionKind(text, href)));
}
for (const [href, kind] of [['#', 'nowhere'], ['', 'nowhere'], ['   ', 'nowhere'], ['javascript:void(0)', 'nowhere'], ['JavaScript:;', 'nowhere'],
  ['#!', 'nowhere'], [undefined, 'nowhere'], ['#menu', 'anchor'], ['tel:+17075550100', 'other'], ['mailto:a@b.co', 'other'],
  ['/book', 'check'], ['https://booking.example/x#y', 'check']]) {
  check(`href ${J(href)} is ${kind}`, T.classifyHref(href, 'https://shop.example/').kind === kind, J(T.classifyHref(href, 'https://shop.example/')));
}
check('relative links resolve against the page, without the #', T.classifyHref('/book#now', 'https://shop.example/a/').url === 'https://shop.example/book');
{
  const html = `<a href="/book">Book <b>Now</b></a><a href="#">Order online</a><a href="javascript:void(0)" class="btn">Donate</a>
    <a href="/about">About</a><button type="button">Reserve</button><a href="tel:7075550100">Call to book</a>
    <a href="#hours">Menu</a><a href="https://pay.example/give"><img src="x.png" alt="Donate today"></a>`;
  const l = T.actionLinks(html, 'https://shop.example/');
  check('finds the action links and buttons in a page', J(l.map((x) => [x.kind, x.url || x.status])) ===
    J([['book', 'https://shop.example/book'], ['order', 'nowhere'], ['donate', 'nowhere'], ['reserve', 'script'], ['donate', 'https://pay.example/give']]), J(l));
}
{
  // Whole check: a broken Book Now, a working Order, a "#" Donate, and more links than the limit.
  const many = Array.from({ length: 30 }, (_, i) => `<a href="/contact-${i}">Contact ${i}</a>`).join('');
  const home = `<!doctype html><html><head><title>Shop</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="A shop."></head><body><a href="/book">Book Now</a><a href="/order">Order</a>
    <a href="#">Donate</a><a href="/book">Book again</a>${many}</body></html>`;
  const pages = { 'https://shop.example/': { body: home }, 'http://shop.example/': hop('https://shop.example/'),
    'https://shop.example/order': { body: 'ok' }, 'https://shop.example/robots.txt': { body: 'User-agent: GPTBot\nDisallow: /\n', headers: { 'Content-Type': 'text/plain' } } };
  for (let i = 0; i < 30; i++) pages[`https://shop.example/contact-${i}`] = { body: 'ok' };
  pages['https://shop.example/book'] = (o) => (o.method === 'HEAD' ? { status: 405 } : { status: 500, body: 'error' });
  const w = { ...web(pages), left: 1000 };
  const r = await T.runCheck('shop.example', w);
  const by = (u) => r.links.find((x) => x.url === u) || {};
  check('whole check: page facts', r.ok && r.status === 200 && r.https && r.httpToHttps === true && r.viewport && r.title === 'Shop' && r.description === 'A shop.', J(r).slice(0, 300));
  check('whole check: HEAD refused, GET says 500, so Book Now is broken', by('https://shop.example/book').status === 'broken' && by('https://shop.example/book').code === 500);
  check('whole check: the same address is checked once', w.log.filter((x) => x.url === 'https://shop.example/book').length === 2);
  check('whole check: Order works', by('https://shop.example/order').status === 'working');
  check('whole check: "#" Donate goes nowhere', r.links.some((x) => x.kind === 'donate' && x.status === 'nowhere'));
  check('whole check: at most 25 links checked, the rest marked unchecked', r.linksChecked === 25 && r.links.filter((x) => x.status === 'unchecked').length === 7,
    J({ n: r.linksChecked, u: r.links.filter((x) => x.status === 'unchecked').length }));
  check('whole check: robots.txt read from the same host', r.ai.trainingBlocked.includes('GPTBot') && r.ai.answerBlocked.length === 0);
}
{
  // Free plan: 50 outside requests per check. The budget runs out before the requests do.
  const many = Array.from({ length: 25 }, (_, i) => `<a href="https://h${i}.example/">Book ${i}</a>`).join('');
  const w = web({ 'https://shop.example/': { body: `<title>x</title>${many}` }, 'http://shop.example/': hop('https://shop.example/') });
  const r = await T.runCheck('https://shop.example/', w);
  check('whole check: stays inside 50 outside requests (DNS lookups count twice)', w.log.length + 2 * new Set(w.log.map((x) => new URL(x.url).hostname)).size <= 50
    && r.links.some((x) => x.status === 'unchecked'), J(w.log.length));
}

// ---------------------------------------------------------------- the Worker's door
{
  const call = (url, origin, method = 'GET') => W.fetch(new Request(url, { method, headers: origin ? { Origin: origin } : {} }), {}, {});
  const r1 = await call('https://dj-checkup.example/?url=example.com', 'https://evil.example');
  check('other sites are refused', r1.status === 403 && !r1.headers.get('Access-Control-Allow-Origin'));
  const r2 = await call('https://dj-checkup.example/?url=example.com', 'https://dragomansjourney.com', 'OPTIONS');
  check('CORS: the site may ask', r2.status === 204 && r2.headers.get('Access-Control-Allow-Origin') === 'https://dragomansjourney.com');
  const r3 = await call('https://dj-checkup.example/', '');
  check('no address: says it is running', r3.status === 200 && (await r3.text()) === 'dj-checkup is running');
  const r4 = await call('https://dj-checkup.example/?url=http://127.0.0.1/', 'http://localhost:8765');
  check('a refused address answers 400 with the reason', r4.status === 400 && (await r4.json()).error === 'ip');
  const store = new Map();
  const cache = { match: async (k) => store.get(k), put: async (k, v) => { store.set(k, v); } };
  check('rate: the first check from an IP goes', await T.tooSoon('203.0.113.9', cache, 1000000) === false && store.size === 1);
  check('rate: a second within 20 seconds waits', await T.tooSoon('203.0.113.9', cache, 1015000) === true);
  check('rate: the marker lives 20 seconds in the Cache API', (await [...store.values()][0]).headers.get('Cache-Control') === 'max-age=20');
  check('rate: another IP goes', await T.tooSoon('203.0.113.10', cache, 1015000) === false);
  check('rate: after 20 seconds it goes again (backup map)', await T.tooSoon('203.0.113.9', null, 1021000) === false);
}

// ---------------------------------------------------------------- 8a: AI readers
const ai = (robots, html = '', header = null, p = '/') => T.aiReaders(robots, p, T.metaTags(html), header);
{
  const r = ai('User-agent: GPTBot\nDisallow: /\n\nUser-agent: ClaudeBot\nUser-agent: Google-Extended\nDisallow: /\n');
  check('8a: blocking only the training kind is not turning AI readers away', r.answerBlocked.length === 0 && J(r.trainingBlocked) === J(['GPTBot', 'ClaudeBot', 'Google-Extended']), J(r));
}
{
  const r = ai('User-agent: OAI-SearchBot\nDisallow: /\n\nUser-agent: PerplexityBot\nDisallow: /\n');
  check('8a: blocking the answer kind is turning AI readers away', J(r.answerBlocked) === J(['OAI-SearchBot', 'PerplexityBot']) && r.trainingBlocked.length === 0, J(r));
}
{
  const r = ai('User-agent: *\nDisallow: /\n');
  check('8a: "User-agent: *" with "Disallow: /" is reported', r.starBlocksAll && r.answerBlocked.length === 7 && r.trainingBlocked.length === 3, J(r));
}
{
  const r = ai('User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nUser-agent: OAI-SearchBot\nAllow: /\n');
  check('8a: a bot\'s own group wins over "*"', r.starBlocksAll && !r.answerBlocked.includes('Googlebot') && !r.answerBlocked.includes('OAI-SearchBot') && r.answerBlocked.includes('Claude-SearchBot'), J(r));
}
{
  const r = ai('User-agent: *\nDisallow: /private\nDisallow:\n');
  check('8a: rules elsewhere on the site don\'t block this page', !r.starBlocksAll && r.answerBlocked.length === 0, J(r));
  const r2 = ai('User-agent: claude-searchbot\nDisallow: /menu\nAllow: /menu/today\n', '', null, '/menu/today');
  check('8a: names match without case, the longest rule wins', !r2.answerBlocked.length, J(r2));
  const r3 = ai('User-agent: Claude-SearchBot\nDisallow: /*.html$\n', '', null, '/menu.html');
  check('8a: * and $ in rules', J(r3.answerBlocked) === J(['Claude-SearchBot']), J(r3));
  check('8a: no robots.txt means nothing is blocked', ai('').answerBlocked.length === 0 && !ai('').starBlocksAll);
}
check('8a: a noindex meta tag', ai('', '<meta name="robots" content="noindex, follow">').noindexMeta);
check('8a: a googlebot "none" meta tag', ai('', '<meta name="googlebot" content="none">').noindexMeta);
check('8a: an ordinary robots meta is fine', !ai('', '<meta name="robots" content="index, follow">').noindexMeta);
check('8a: X-Robots-Tag noindex', ai('', '', 'noindex').noindexHeader && ai('', '', 'googlebot: none').noindexHeader && !ai('', '', 'nosnippet').noindexHeader);
check('8a: the crawler list has both kinds from all four companies',
  ['OpenAI', 'Anthropic', 'Perplexity', 'Google'].every((c) => T.AI_BOTS.some((b) => b.company === c && b.kind === 'answer'))
  && ['OpenAI', 'Anthropic', 'Google'].every((c) => T.AI_BOTS.some((b) => b.company === c && b.kind === 'training')));

// ---------------------------------------------------------------- 8b: structured data
const ld = (o) => `<script type="application/ld+json">${typeof o === 'string' ? o : J(o)}</script>`;
{
  const s = T.structuredData(ld({ '@context': 'https://schema.org', '@type': 'Bakery', name: 'Crumb', telephone: '(707) 555-0100',
    address: { '@type': 'PostalAddress', streetAddress: '12 Main St', addressLocality: 'Santa Rosa', addressRegion: 'CA' },
    openingHoursSpecification: [{ dayOfWeek: 'Monday', opens: '07:00', closes: '15:00' }], url: 'https://crumb.example/' }));
  check('8b: a business block, its type and all five facts', s.business && s.business.type === 'Bakery' && Object.values(s.business.has).every(Boolean)
    && s.business.address === '12 Main St, Santa Rosa, CA' && s.business.openingHours === 'Monday 07:00-15:00', J(s));
}
{
  const s = T.structuredData(ld({ '@context': 'https://schema.org', '@graph': [{ '@type': 'WebSite', name: 'x' }, { '@type': ['LocalBusiness', 'Plumber'], name: 'Pipes' }] }));
  check('8b: inside an @graph, with a list of types, and what\'s missing', s.business && s.business.type === 'LocalBusiness, Plumber' && s.business.has.name
    && !s.business.has.address && !s.business.has.telephone && !s.business.has.openingHours && !s.business.has.url, J(s));
}
check('8b: a WebSite block alone is not a business', T.structuredData(ld({ '@type': 'WebSite', name: 'x' })).business === null);
check('8b: no block at all', T.structuredData('<p>hi</p>').blocks === 0 && T.structuredData('<p>hi</p>').business === null);
check('8b: a broken block is counted, not thrown', T.structuredData(ld('{"@type": "LocalBusiness",')).broken === 1);

// ---------------------------------------------------------------- 8c: facts in the raw text
{
  const f = T.textFacts('<p>Call (707) 555-0134.</p><p>Open Monday to Friday, 9am to 5pm.</p><address>12 Main St<br>Santa Rosa, CA</address>', null);
  check('8c: phone found', f.phone === '(707) 555-0134', J(f));
  check('8c: hours found (day names near times)', !!f.hours && /Monday/.test(f.hours), J(f.hours));
  check('8c: address from an <address> tag', f.address === '12 Main St Santa Rosa, CA' && f.addressFrom === 'address-tag', J(f));
}
{
  const f = T.textFacts('<p>Find us at 455 W. College Ave, Santa Rosa. Hours: Tue-Sat 11:00-20:00</p>', null);
  check('8c: address from a US street pattern', f.addressFrom === 'text' && /455 W\. College Ave/.test(f.address), J(f));
  check('8c: hours with a 24-hour time', !!f.hours, J(f));
}
{
  const f = T.textFacts('<p>Welcome!</p><script>var phone="(707) 555-0134"; var h="Monday 9am"</script><style>.x{}</style>', null);
  check('8c: nothing found when the facts sit only in scripts', f.phone === null && f.hours === null && f.address === null, J(f));
  const g = T.textFacts('<p>Open 24 hours. Since 1999 on 4th Street.</p>', null);
  check('8c: no false finds from years and plain numbers', g.phone === null && g.hours === null, J(g));
  const sd = T.structuredData(ld({ '@type': 'LocalBusiness', name: 'A', address: { streetAddress: '9 Elm St', addressLocality: 'Petaluma' } }));
  check('8c: address from structured data', T.textFacts('<p>Hi</p>', sd).addressFrom === 'structured-data');
}

// ---------------------------------------------------------------- 8d: readable text
{
  const thin = T.textFacts('<div id="app"></div><script>' + 'x'.repeat(5000) + '</script><p>Loading</p>', null);
  check('8d: a script-built page holds almost no readable text', thin.textLength < 600, J(thin.textLength));
  const full = T.textFacts('<p>' + 'Fresh bread every morning. '.repeat(40) + '</p>', null);
  check('8d: a page of words holds plenty', full.textLength >= 600, J(full.textLength));
}

// ---------------------------------------------------------------- 8e: two phone numbers
{
  const sd = (tel) => T.structuredData(ld({ '@type': 'LocalBusiness', name: 'A', telephone: tel }));
  check('8e: the same number, written differently, matches', T.textFacts('<p>(707) 555-0134</p>', sd('+1-707-555-0134')).phoneMismatch === false);
  check('8e: different numbers are flagged', T.textFacts('<p>(707) 555-0134</p>', sd('707.555.0199')).phoneMismatch === true);
  check('8e: nothing to compare without a number in the text', T.textFacts('<p>Hi</p>', sd('707.555.0199')).phoneMismatch === false);
}

// ---------------------------------------------------------------- step 12: the site's own local.html
const local = process.argv[2] || path.join(here, '..', 'out', 'local.html');
if (fs.existsSync(local)) {
  const s = T.structuredData(fs.readFileSync(local, 'utf8'));
  check('local.html: the 8b check finds the business block', s.business && s.business.type === 'ProfessionalService'
    && s.business.name === "Dragoman's Journey" && s.business.has.address && s.business.has.url, J(s));
} else {
  check('local.html: found for the 8b check', false, local);
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(`${ok.length}/${ok.length + bad.length} passed`);
for (const x of bad) console.log('FAIL', x);
process.exit(bad.length ? 1 : 0);
