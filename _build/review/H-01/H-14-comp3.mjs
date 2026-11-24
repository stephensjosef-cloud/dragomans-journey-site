// "3,5" in Value to bytes is silently read as 35 (ten times the value), with no warning.
import { load, fail, pass } from './harness.mjs';
const E = encodeURIComponent;
const h = await load('comp3.html', { hash: 'm=enc&v=' + E('3,5') + '&p=' + E('S9(2)V9(5)') });
const b = h.text('#out dd'), warned = h.$$('#out .warn').length;
if (b === '35 00 00 0C' && !warned) fail('"3,5" encodes as ' + b + ' (35.00000) with no warning');
pass();
