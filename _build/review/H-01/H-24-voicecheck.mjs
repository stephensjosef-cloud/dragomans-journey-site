// The AI-word list matches the plain name of a trade: elevators (elevat*) and unlock (locksmith).
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
const bad = [];
for (const t of ['We repair elevators and lifts across Sonoma County.', 'We unlock cars and homes in Santa Rosa, day or night.']) {
  h.type('words', t); h.click('check');
  const c = h.text('cards');
  if (/one of the words AI reaches for/.test(c)) bad.push(c.match(/"([^"]+)" is one of the words/)[1]);
}
if (bad.length) fail('trade words marked as AI words: ' + bad.join(', '));
pass();
