// "When will you film? Evening" still tells a cafe to film the sign "in daylight".
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2026-11-24T12:00:00' });
h.click(h.$('.chip[data-k="type"][data-v="cafe"]')); h.click(h.$('.chip[data-k="light"][data-v="pm"]'));
const c = h.win._dj.find((c) => /in daylight/.test(c.text));
if (c && /Evening/.test(h.text('#c-light .chip[aria-pressed="true"]'))) fail('Cafe + Evening: clip ' + c.no + ' says "' + c.text + '"');
pass();
