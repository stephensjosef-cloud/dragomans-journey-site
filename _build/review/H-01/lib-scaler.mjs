import { load, fail, pass } from './harness.mjs';
export { load, fail, pass };
// rows of the result table as [amount, ingredient, note], amount without its "was ..." line
export function rows(h) {
  return h.$$('#out tr').map((tr) => [...tr.children].map((td) => {
    const c = td.cloneNode(true);
    c.querySelectorAll('.was').forEach((w) => w.parentNode.removeChild(w));
    return c.textContent.replace(/\s+/g, ' ').trim();
  }));
}
export async function scale(rec, serves, adults, kids, batch) {
  const h = await load('scaler.html');
  h.type('serves', String(serves)); h.type('adults', String(adults)); h.type('kids', String(kids));
  h.type('rec', rec);
  if (batch) h.click(`[data-b="${batch}"]`);
  return h;
}
