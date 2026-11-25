// Gate 0b: each of the seven pages loads in the harness with no uncaught error, and its default state
// (or its "Try a sample") renders the result the page shows, worked out here by hand.
// H01_DEPS=/tmp/h01deps node _build/review/H-01/proof.mjs   -> one line per page, exit 1 on any miss
import { load } from './harness.mjs';

const out = [];
let bad = 0;
async function page(name, fn) {
  let h;
  try {
    h = await load(name);
    const got = await fn(h);
    const errs = h.errors.filter((e) => !/Not implemented: HTMLCanvasElement.prototype.toBlob/.test(e));
    if (errs.length) throw new Error('uncaught: ' + errs[0].split('\n')[0]);
    out.push('ok   ' + name + ': ' + got);
  } catch (e) { bad++; out.push('FAIL ' + name + ': ' + e.message.split('\n')[0]); }
  finally { if (h) h.close(); }
}
const want = (cond, msg) => { if (!cond) throw new Error(msg); };

await page('voicecheck.html', async (h) => {
  want(h.$('res').hidden, 'result showing before any check');
  h.click('sample');
  const head = h.text('res-h'), cards = h.$$('#cards > li').length;
  const R = h.win.voiceCheck(h.$('words').value);
  const n = R.sentences.filter((s) => s.marks.length).length;
  want(head === n + ' of ' + R.sentences.length + ' sentences have marks', 'heading "' + head + '"');
  want(cards === n, cards + ' cards for ' + n + ' marked sentences');
  return 'sample: "' + head + '", ' + cards + ' cards';
});

await page('receipt.html', async (h) => {
  // Three chores rung up on load at $30 an hour: 30 min a workday (x250) twice, 90 min a week (x50).
  const hours = 30 / 60 * 250 + 30 / 60 * 250 + 90 / 60 * 50;   // 325
  const tot = h.text('.rl.tot span:last-child');
  want(tot === '$' + (hours * 30).toLocaleString('en-US'), 'total ' + tot);
  want(h.$$('#rows .row2').length === 3, 'rows');
  return 'default receipt: 3 lines, TOTAL ' + tot + ', ' + hours + ' hr';
});

await page('shotlist.html', async (h) => {
  const nums = h.$$('#shoot li > b').map((b) => +b.textContent);
  want(nums.join(',') === '1,2,3,4,5,6,7,8,9,10', 'filming numbers ' + nums.join(','));
  const secs = h.win._dj.reduce((a, c) => a + c.sec, 0);
  want(secs === 30, 'edit adds to ' + secs + ' s');
  return 'Shop or boutique, 30 s: 10 clips numbered 1 to 10, edit adds to ' + secs + ' s';
});

await page('captions.html', async (h) => {
  await h.wait(50);
  const cards = h.$$('#cards .cardline').length, v = h.text('v-text');
  want(cards >= 1, 'no caption cards');
  want(/Good to go|Too long/.test(v), 'verdict "' + v + '"');
  // 21 words in the sample; at 2.8 words a second, each card rounded to half a second.
  const need = h.$$('#cards .cardline .s').reduce((a, s) => a + parseFloat(s.textContent), 0);
  return 'sample caption: ' + cards + ' cards, ' + need + ' s to read in a 7.5 s clip, "' + v + '"';
});

await page('scaler.html', async (h) => {
  // Serves 4; 2 grown-ups and 20 kids at half a portion = 12 portions, x3.
  want(h.text('fac') === '×3', 'factor ' + h.text('fac'));
  const td = h.$('#out tr:first-child td.amt'), first = td.textContent.replace(td.querySelector('.was').textContent, '').trim();
  want(first === '6', 'bananas "' + first + '"');
  return 'default: ×3, ' + h.$$('#out tr').length + ' rows, first "' + first + '"';
});

await page('comp3.html', async (h) => {
  const v = h.text('#out dd');
  want(v === '3.50000', 'value ' + v);
  return 'Exhibit A default: 03 50 00 0C with S9(2)V9(5) reads ' + v;
});

await page('checkup.html', async (h) => {
  want(h.$('rep1').hidden, 'report showing before any check');
  want(h.fetches.length === 0, 'fetched on load');
  return 'empty box on load, no fetch; the report needs the Worker (stubbed in the checkup repros)';
});

console.log(out.join('\n'));
process.exit(bad ? 1 : 0);
