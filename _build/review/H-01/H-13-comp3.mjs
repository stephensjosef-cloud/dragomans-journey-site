// An unsigned picture with a D sign shows a negative value, beside a note calling the minus "usually harmless".
import { load, fail, pass } from './harness.mjs';
const E = encodeURIComponent;
const h = await load('comp3.html', { hash: 'm=dec&v=' + E('12 3D') + '&p=' + E('PIC 9(3) COMP-3') });
const v = h.text('#out dd');
if (v === '-123') fail('unsigned PIC 9(3), bytes 12 3D, Value "' + v + '"');
pass();
