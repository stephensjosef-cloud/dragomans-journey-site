import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
h.click('#c-pos [data-v="top"]');
h.type('cap', 'Order at www.santarosasourdoughbakeryandcafe.com'); await h.wait(200);
const one = h.text('v-text'), why = h.text('verdicts');
const ctx = h.$('cv').getContext('2d'); ctx.font = "700 54px 'Barlow', 'Helvetica Neue', Arial, sans-serif"; const w = Math.round(ctx.measureText('www.santarosasourdoughbakeryandcafe.com').width);
console.log('word width', w, 'px of a 1080 px frame; why:', why);
if (/too wide/.test(why) && /It fits/.test(one)) fail('Why says a word is too wide, the line says: "' + one + '"');
pass();
