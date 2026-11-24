// Chinese (no spaces between words) skips the English-only gate and is told "Nothing jumped out".
import { load, fail, pass } from './harness.mjs';
const h = await load('voicecheck.html');
h.type('words', '我们是一家家庭面包店，每天早上六点前烤六十个面包。我们的黑麦面包中午就卖完了。欢迎光临我们的店，我们提供无缝的解决方案，满足您的独特需求。');
h.click('check');
const head = h.text('res-h');
if (head !== "This reads English only, so I can't check these words.") fail('Chinese paragraph got "' + head + '"');
pass();
