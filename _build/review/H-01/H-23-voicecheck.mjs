// Plain notes a person writes get AI marks: a word stem matches inside an ordinary word, and a
// friendly "Hey," in front of a question trips the stage-move rule.
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
const notes = [
  "The elevation gain on Sunday's hike was brutal.",
  'Our journey to Tahoe took six hours because of snow.',
  "Hey, can you cover my shift Saturday? I'll owe you one."
];
const bad = [];
for (const n of notes) {
  h.type('words', n); h.click('check');
  const head = h.text('res-h') || '';
  if (/have marks|has a mark/.test(head)) bad.push('"' + n + '" -> ' + head + ': ' + (h.text('cards') || '').slice(0, 90));
}
if (bad.length) fail(bad.length + ' of ' + notes.length + ' plain notes marked; first: ' + bad[0]);
pass('plain notes get no marks');
