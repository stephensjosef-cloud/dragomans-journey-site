// "1 or 2 eggs" at x1.5 shows "2 | or 2 eggs".
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const r = rows(await scale('1 or 2 eggs', 4, 6, 0))[0];
if (/^or /.test(r[1])) fail('amount "' + r[0] + '", ingredient "' + r[1] + '" (want 2 to 3 eggs)');
pass();
