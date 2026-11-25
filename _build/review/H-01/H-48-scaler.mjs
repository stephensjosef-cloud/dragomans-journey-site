// "One onion" / "an egg" are not scaled and told "Season to taste".
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const R = rows(await scale('One onion, diced\nan egg', 4, 2, 20));
const bad = R.filter((r) => r[0] === '' && /Season to taste/.test(r[2]));
if (bad.length) fail(bad.map((r) => r[1] + ' -> "' + r[2] + '"').join('; '));
pass();
