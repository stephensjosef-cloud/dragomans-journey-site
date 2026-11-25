// "St." ends a sentence, so two sentences count as three and get a false "Three short sentences" mark.
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
h.type('words', 'Find us at 410 Fourth St. in Santa Rosa. We bake seamless rye.');
h.click('check');
const head = h.text('res-h'), cards = h.text('cards');
if (/Three short sentences/.test(cards) || /of 3 sentences/.test(head)) fail('two sentences got "' + head + '" and a slogan mark: ' + /Three short/.test(cards));
pass();
