// Tap every chore at $15 an hour: the printed lines add to $15,628, the TOTAL says $15,627.
import { load, fail, pass } from './harness.mjs';
const h = await load('receipt.html', { now: '2026-11-24T12:00:00' });
for (let i = 0; i < 12; i++) { const c = h.$(`[data-p="${i}"]`); if (!c.hasAttribute('aria-disabled')) h.click(c); }
h.type('rate', '15');
const n = (s) => +s.replace(/[^0-9.]/g, '');
const sum = h.$$('#rows [data-o=money]').reduce((a, e) => a + n(e.textContent), 0);
const tot = n(h.text('.rl.tot span:last-child'));
if (sum !== tot) fail('12 lines add to $' + sum.toLocaleString('en-US') + ' but TOTAL shows $' + tot.toLocaleString('en-US'));
pass();
