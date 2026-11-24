// The on-screen caption hard-codes "Dec 1" for Giving Tuesday; in 2027 it is Nov 30.
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2027-11-10T12:00:00' });
h.click(h.$('.chip[data-k="type"][data-v="nonprofit"]'));
const cap = h.win._dj.find((c) => c.role === 'call').cap, when = h.text('when');
if (/Dec 1/.test(cap) && /Nov 30/.test(when)) fail('2027-11-10, Nonprofit: countdown "' + when + '" but caption "' + cap + '"');
pass();
