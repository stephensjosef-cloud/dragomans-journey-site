// A binary (COMP) field whose USAGE comes after its VALUE clause is decoded as COMP-3, with "Clean field".
import { load, fail, pass } from './harness.mjs';
const E = encodeURIComponent;
const h = await load('comp3.html', { hash: 'm=dec&v=' + E('00 01 2C') + '&p=' + E('05 WS-CNT PIC S9(4) VALUE ZERO COMP.') });
const out = h.text('#out');
if (!/COMP is plain binary/.test(out)) fail('COMP field read as packed: ' + out.slice(0, 90));
pass();
