// A numbered list "1. ..." counts each number as its own sentence (3 lines -> "of 6 sentences").
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
h.type('words', '1. We deliver seamless bread daily.\n2. We roast our own coffee.\n3. We close at noon on Sundays.');
h.click('check');
const head = h.text('res-h');
if (head !== '1 of 3 sentences has a mark') fail('three list lines got "' + head + '"');
pass();
