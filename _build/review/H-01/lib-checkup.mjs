// Shared helpers for the checkup repros. Nothing leaves the machine: every fetch and DNS lookup is stubbed.
import { load, loadWorker, wait, fail, pass } from './harness.mjs';
export { load, loadWorker, wait, fail, pass };

export const W = await loadWorker();

// A fake web. routes: { 'https://x.com/': {status, headers, body (string|Uint8Array), hang, throws, head:{...}} }
// A route may also be a function (url, opts) -> same object. Unknown URLs answer 404.
export function fakeWeb(routes, dns = {}) {
  const log = [];
  const fetch = async (url, opts = {}) => {
    log.push((opts.method || 'GET') + ' ' + url);
    let r = routes[url];
    if (typeof r === 'function') r = r(url, opts);
    if (r && opts.method === 'HEAD' && r.head) r = r.head;
    if (!r) r = { status: 404, body: 'not found' };
    if (r.throws) throw new TypeError(r.throws);
    if (r.hang) return new Promise((res, rej) => opts.signal.addEventListener('abort', () => rej(new DOMException('aborted', 'AbortError'))));
    const headers = new Headers({ 'Content-Type': 'text/html; charset=utf-8', ...(r.headers || {}) });
    const body = opts.method === 'HEAD' ? null : r.stream ? r.stream(opts) : (r.body ?? '');
    return new Response(body, { status: r.status || 200, headers });
  };
  const resolve = async (host) => (host in dns ? dns[host] : ['93.184.216.34']);
  return { fetch, resolve, log };
}

// Run the Worker's check, then hand its JSON to the page the way the live Worker would, and submit `typed`.
export async function e2e(typed, web) {
  const out = await W.runCheck(typed, { fetch: web.fetch, resolve: web.resolve });
  const h = await load('checkup.html', {
    fetch: async () => new Response(JSON.stringify(out), { status: out.ok ? 200 : 400, headers: { 'Content-Type': 'application/json' } })
  });
  h.type('site', typed);
  h.submit('form');
  for (let i = 0; i < 50 && h.$('go').disabled; i++) await wait(20);
  h.out = out;
  h.report = () => [h.text('msg'), h.text('rep1-h'), h.text('finds1'), h.text('oks1'), h.text('note1'), h.$('rep2').hidden ? '' : h.text('finds2'), h.$('aiok').hidden ? '' : 'AIOK', h.text('facts')].join(' | ');
  return h;
}

// A plain, healthy small-business page; pieces can be swapped in.
export function shopPage(o = {}) {
  const filler = 'Golden Crust Bakery bakes bread, pastries and cakes every morning in Santa Rosa. ' .repeat(10);
  return `<!doctype html><html><head><meta charset="utf-8"><title>${o.title ?? 'Golden Crust Bakery'}</title>
<meta name="description" content="Fresh bread and pastries in Santa Rosa.">
<meta name="viewport" content="width=device-width, initial-scale=1">${o.head || ''}</head><body>
<h1>Golden Crust Bakery</h1><p>${filler}</p>
${o.address ?? '<p>412 Fourth Street, Santa Rosa, CA 95404</p>'}
${o.hours ?? '<p>Open Tuesday to Sunday, 7am to 3pm.</p>'}
<p>Call <a href="tel:+17075550100">(707) 555-0100</a> or write <a href="mailto:hi@goldencrust.example">hi@goldencrust.example</a></p>
${o.body || ''}
</body></html>`;
}
export const HOME = 'https://goldencrust.com/';
export const base = (extra = {}) => ({
  [HOME]: { body: shopPage() },
  'http://goldencrust.com/': { status: 301, headers: { Location: HOME } },
  'https://goldencrust.com/robots.txt': { status: 404, body: '' },
  ...extra
});
