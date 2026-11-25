// A bullet in front of "Whether you're..." hides the warm-up mark (and the whole card) the bare line gets.
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
const line = "Whether you're hungry or not, our rye sells out by noon.";
h.type('words', line); h.click('check');
const bare = /warms up/.test(h.text('cards'));
h.type('words', '- ' + line); h.click('check');
const bullet = /warms up/.test(h.text('cards'));
if (bare && !bullet) fail('"- ' + line + '" got "' + h.text('res-h') + '", no warm-up mark');
pass();
