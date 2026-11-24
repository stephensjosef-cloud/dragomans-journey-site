// "butter" matched inside buttermilk / peanut butter / butternut squash -> stick counts.
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const h = await scale('1 cup buttermilk\n1/2 cup peanut butter\n2 cups butternut squash', 4, 2, 20);
const bad = rows(h).filter((r) => /stick/.test(r[2]));
if (bad.length) fail(bad.map((r) => r.join(' / ')).join('; '));
pass();
