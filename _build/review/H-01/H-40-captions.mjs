import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
h.type('secs', '');   // clip length cleared (a real browser also gives '' for 'abc' or '7,5')
await h.wait(50);
const one = h.text('v-text'), why = h.text('verdicts');
if (/read it in time/.test(one) && !/seconds to read|Reading all of it/.test(why)) fail('no clip length, yet the line says: "' + one + '"');
pass();
