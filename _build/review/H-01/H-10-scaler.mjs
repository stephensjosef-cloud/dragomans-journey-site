// "rice" matched inside "Rice Krispies cereal": weighed at 185 g a cup.
import { scale, rows, fail, pass } from './lib-scaler.mjs';
const h = await scale('6 cups Rice Krispies cereal', 4, 2, 20);
const r = rows(h)[0];
if (/kg/.test(r[2])) fail(r.join(' / ') + ' (puffed rice is ~25 g a cup, about 0.5 kg)');
pass();
