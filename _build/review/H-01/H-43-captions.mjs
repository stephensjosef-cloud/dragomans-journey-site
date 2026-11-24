import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
const why = h.text('verdicts'); const m = why.match(/About ([\d.]+) seconds to read, and the clip runs ([\d.]+)\. Time to spare/);
if (m && +m[1] >= +m[2]) fail('sample: "' + m[0] + '" with 0 s to spare');
pass();
