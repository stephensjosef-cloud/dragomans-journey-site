// Gym one-lap order films "people walking in at class time" after "high fives at the end of class".
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2026-11-24T12:00:00' });
h.click(h.$('.chip[data-k="type"][data-v="gym"]'));
const li = h.$$('#shoot li'), num = (re) => +li.find((l) => re.test(l.textContent)).querySelector('b').textContent;
const walkIn = num(/door at class time/), end = num(/end of class/);
if (walkIn > end) fail('Gym: film #' + walkIn + ' "door at class time, people walking in" comes after film #' + end + ' "high fives at the end of class"');
pass();
