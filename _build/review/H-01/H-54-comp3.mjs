// One stray % in a shared link drops the whole link silently; the page shows Exhibit A's 3.50000 as if it were the shared field.
import { load, fail, pass } from './harness.mjs';
const h = await load('comp3.html', { hash: 'm=dec&v=00%2012%203C&p=S9(3)V99%' });
const v = h.text('#out dd'), warned = /link|couldn/i.test(h.text('#out'));
if (h.$('in').value !== '00 12 3C' && !warned) fail('link for 00 12 3C shows ' + h.$('in').value + ' = ' + v + ', no warning');
pass();
