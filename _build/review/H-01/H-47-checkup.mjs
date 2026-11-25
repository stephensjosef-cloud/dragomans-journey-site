// The Worker must refuse a site whose address points inside a private network. A name that resolves to
// fec0::1 (old site-local) or 2002:7f00:1:: (6to4 wrapping 127.0.0.1) is checked as if it were public.
// DNS and fetch are stubbed; nothing leaves the machine. Cloudflare's own network may stop the request
// anyway, so this is the Worker's own check, read offline.
import { W, fakeWeb, base, fail, pass } from './lib-checkup.mjs';
const let_through = [];
for (const ip of ['fec0::1', '2002:7f00:1::']) {
  const web = fakeWeb(base(), { 'goldencrust.com': [ip] });
  const out = await W.runCheck('goldencrust.com', { fetch: web.fetch, resolve: web.resolve });
  if (out.ok) let_through.push(ip);
}
if (let_through.length) fail('a site resolving to ' + let_through.join(' or ') + ' is checked, not refused as private');
pass('both refused');
