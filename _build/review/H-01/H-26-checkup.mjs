// A server that answers HEAD with 405 (GET works): once the request budget runs out between the HEAD and the GET,
// the HEAD's 405 is kept and a working button is reported as leading to an error page.
import { e2e, fakeWeb, base, shopPage, HOME, fail, pass } from './lib-checkup.mjs';
const items = ['Sourdough', 'Baguette', 'Croissant', 'Danish', 'Scone', 'Muffin', 'Bagel', 'Brioche', 'Focaccia', 'Rye',
  'Challah', 'Ciabatta', 'Pretzel', 'Cookie', 'Brownie', 'Eclair', 'Tart', 'Pie', 'Cake', 'Cupcake', 'Donut'];
const links = '<a href="https://tables.example/goldencrust">Reserve a table</a> ' + items.map((n) => `<a href="/order/${n.toLowerCase()}">Order ${n}</a>`).join(' ');
const routes = base({ [HOME]: { body: shopPage({ body: links }) } });
const web = fakeWeb((u, o) => null, {});
web.fetch = fakeWeb(new Proxy(routes, { get: (t, u) => t[u] || (String(u).includes('tables.example') ? { status: 200, body: 'ok' } : String(u).includes('/order/') ? { status: 200, body: 'ok', head: { status: 405 } } : undefined), has: () => true })).fetch;
const h = await e2e('goldencrust.com', web);
console.log(h.out.links.map(l=>l.label+':'+l.status+':'+(l.code||'')).join(', '));
const bad = h.out.links.filter((l) => l.status === 'broken');
console.log(bad.map((l) => l.label + ' ' + l.code), '\n', h.text('rep1-h'), '|', h.text('finds1').slice(0, 160));
if (bad.length) fail('"' + bad[0].label + '" (GET answers 200) is reported broken with code ' + bad[0].code + ' because the budget ran out before its GET');
pass();
