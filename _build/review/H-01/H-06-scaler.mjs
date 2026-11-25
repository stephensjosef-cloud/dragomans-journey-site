// Units it doesn't know become counts: rounded up to whole, last word pluralised.
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const R = rows(await scale('1 pint heavy cream\n1,000 g flour\n2 heaping tbsp cocoa', 4, 6, 0));
const bad = R.filter((r) => /^\d+$/.test(r[0]));
if (bad.length) fail(bad.map((r) => r.join(' ')).join('; '));
pass();
