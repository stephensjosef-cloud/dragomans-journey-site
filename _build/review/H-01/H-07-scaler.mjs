// "1-1½ cups milk" at x1.5 reads as "2 ½ cups milks".
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const r = rows(await scale('1-1½ cups milk', 4, 6, 0))[0];
if (!/cup/.test(r[0])) fail('amount "' + r[0] + '", ingredient "' + r[1] + '" (want 1 1/2 cups to 2 1/4 cups)');
pass();
