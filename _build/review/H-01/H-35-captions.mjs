import { load, fail, pass } from './harness.mjs';
const h = await load('captions.html'); await h.wait(50);
const ctx = h.$('cv').getContext('2d'), real = ctx.measureText.bind(ctx), memo = new Map(); let calls = 0;
ctx.measureText = (t) => { calls++; const k = ctx.font + '|' + t; if (!memo.has(k)) memo.set(k, real(t)); return memo.get(k); };   // memoised only so the run ends
const s = 'Fresh sourdough comes out of the oven at 7 every morning. Come early, because the first batch is always gone by 9. '; let t = ''; while (t.split(' ').length < 101) t += s; t = t.split(' ').slice(0, 100).join(' ');
h.$('cap').value = t; calls = 0; h.type('secs', '30');   // one keystroke in the clip-length box = one render
console.log('100-word caption: one render =', calls, 'measureText calls');
if (calls > 200000) fail('100-word caption: ' + calls + ' text measurements per render (each chip tap / clip keystroke)');
pass();
