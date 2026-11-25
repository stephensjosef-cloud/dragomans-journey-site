// Switching direction throws away the user's field and shows a demo instead, and blames the user for it.
import { load, fail, pass } from './harness.mjs';
const h = await load('comp3.html');
h.type('in', '00 12 34 56 7D'); h.type('pic', 'S9(7)V99');
const before = h.text('#out dd');                       // -12345.67
h.click('mode-enc');
const enc = h.text('#out dd'), encIn = h.$('in').value;
h.click('mode-dec');
const dec = h.text('#out');
if (encIn !== '-12345.67') fail('decoded ' + before + ', Value to bytes shows ' + encIn + ' -> ' + enc + '; back: "' + dec.slice(0, 52) + '"');
pass();
