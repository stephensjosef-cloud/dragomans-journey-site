// Pressing any chip rebuilds all chips; keyboard focus falls to <body>.
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2026-11-24T12:00:00' });
h.$('.chip[data-k="type"][data-v="cafe"]').focus();
h.click(h.doc.activeElement);
const a = h.doc.activeElement;
if (!a.classList.contains('chip')) fail('focus on "Cafe or bakery" chip, press it: focus ends on <' + a.tagName.toLowerCase() + '>');
pass();
