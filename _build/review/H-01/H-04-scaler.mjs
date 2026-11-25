// One batch view + Copy the shopping list copies one batch, not what to buy.
import { scale, fail, pass } from './lib-scaler.mjs';
const h = await scale('2 large eggs\n1 cup flour', 2, 12, 0, 'one');
h.click('copy'); await h.wait(20);
const list = h.clip.at(-1) || '';
if (/\[ \] 4 large eggs/.test(list) && !/12/.test(list)) fail('shopping list says "4 large eggs" / "2 cups flour" for 3 batches that need 12 eggs, 6 cups: ' + JSON.stringify(list));
pass();
