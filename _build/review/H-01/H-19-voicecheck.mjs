// A plain English list of services (14 words, one "and") is refused as not English.
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
h.type('words', 'Haircuts, beard trims, hot towel shaves, kids cuts, color, highlights, perms, waxing and braids.');
h.click('check');
const head = h.text('res-h');
if (/English only/.test(head)) fail('English service list got "' + head + '"');
pass();
