// Unit words mangled: pincheses, dasheses, pkg.s, bunche.
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const x3 = rows(await scale('2 pinches salt\n2 dashes hot sauce\n1 pkg. yeast', 4, 2, 20)).map((r) => r[0]);
const q = rows(await scale('2 bunches cilantro', 4, 1, 0)).map((r) => r[0]);
const bad = [...x3, ...q].filter((s) => /pincheses|dasheses|pkg\.s|bunche$/.test(s));
if (bad.length) fail(bad.join(', '));
pass();
