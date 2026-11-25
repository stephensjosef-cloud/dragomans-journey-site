// Small ml / oz amounts round to 0.
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const a = rows(await scale('2 ml almond extract', 4, 4, 0))[0];
const b = rows(await scale('5 ml vanilla extract\n0.25 oz yeast', 4, 1, 0));
const zero = [a, ...b].filter((r) => /^0 (ml|oz)$/.test(r[0]));
if (zero.length) fail(zero.map((r) => r.join(' ')).join('; '));
pass();
