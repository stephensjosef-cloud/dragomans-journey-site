// Picking Nonprofit forces goal "Ask for support"; switching back to Shop keeps it, silently.
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2026-11-24T12:00:00' });
const chip = (k, v) => h.$('.chip[data-k="' + k + '"][data-v="' + v + '"]');
h.click(chip('type', 'nonprofit')); h.click(chip('type', 'shop'));
const cap = h.win._dj.find((c) => c.role === 'call').cap;
if (/Giving Tuesday/.test(cap) || /Giving Tuesday/.test(h.text('when'))) fail('Nonprofit then Shop: shop reel says "' + cap + '" / "' + h.text('when') + '" (details panel still folded: ' + h.$('details').hidden + ')');
pass();
