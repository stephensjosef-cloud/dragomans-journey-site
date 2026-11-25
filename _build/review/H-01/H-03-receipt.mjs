// All chores at 0 minutes: no work at all, yet the receipt says you'd finish on January 1.
import { load, fail, pass } from './harness.mjs';
const h = await load('receipt.html', { now: '2026-11-24T12:00:00' });
for (const i of h.$$('#rows input[data-f=min]')) h.type(i, '0');
const f = h.$('p-foot').textContent.replace(/\s+/g, ' ');
if (/0 hr/.test(f) && /you'd finish on\s*January 1/.test(f)) fail('0 hours rung up, receipt still says "you\'d finish on January 1"');
pass();
