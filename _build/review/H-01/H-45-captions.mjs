import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
h.type('cap', 'Order at www.santarosasourdoughbakeryandcafe.com'); await h.wait(200);   // Reels, Bottom, Medium (defaults)
const before = h.text('verdicts'); console.log('at Bottom:', before.match(/On Instagram[^.]*\.[^.]*\./)[0]);
h.click('#c-pos [data-v="mid"]'); await h.wait(50);   // follow the advice
const after = h.text('verdicts'); console.log('at Middle:', (after.match(/On Instagram[^.]*\.[^.]*\./) || ['clear'])[0]);
if (/cover screen/.test(after) && /Move it to the middle/.test(after)) fail('moved to Middle as told; still covered and still told to move it to the middle');
pass();
