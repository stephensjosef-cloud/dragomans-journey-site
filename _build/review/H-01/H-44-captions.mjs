import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
h.click('#c-size [data-v="s"]');
h.type('cap', 'Order at www.santarosasourdoughbakeryandcafe.com'); await h.wait(200);
const why = h.text('verdicts');
if (h.$('#c-size [data-v="s"]').getAttribute('aria-pressed') === 'true' && /Pick a smaller size/.test(why)) fail('size already Small (the smallest), still told: Pick a smaller size');
pass();
