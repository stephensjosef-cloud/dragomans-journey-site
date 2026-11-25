// A valid all-fraction picture (SV9(5), the usual shape of a rate field) is refused.
import { load, fail, pass } from './harness.mjs';
const E = encodeURIComponent;
const h = await load('comp3.html', { hash: 'm=dec&v=' + E('03 50 0C') + '&p=' + E('05 WS-RATE PIC SV9(5) COMP-3.') });
const v = h.text('#out dd');
if (v !== '.03500' && v !== '0.03500') fail('SV9(5) with 03 50 0C shows "' + h.text('#out').slice(0, 70) + '", no value');
pass();
