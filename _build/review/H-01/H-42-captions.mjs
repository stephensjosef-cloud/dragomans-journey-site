import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
h.type('cap', ''); await h.wait(200);
h.click('copy'); await h.wait(20);
if (h.clip.length && h.clip[0] === '' && /copied/.test(h.text('toast'))) fail('empty caption: clipboard got "" and the toast says "' + h.text('toast') + '"');
pass();
