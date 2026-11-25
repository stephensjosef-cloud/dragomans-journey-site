// 45 s reel tells you to film ~5 s per clip, yet some clips must stay on screen longer than 5 s.
import { load, fail, pass } from './harness.mjs';
const h = await load('shotlist.html', { now: '2026-11-24T12:00:00' });
h.click(h.$('.chip[data-k="len"][data-v="45"]'));
const long = h.win._dj.filter((c) => c.sec > 5);
const said = /about five seconds/.test(h.text('#cut')) && /Count to five on every clip/.test(h.text('rules'));
if (said && long.length) fail('45 s, Shop/Bring people in: clips ' + long.map((c) => c.no + '=' + c.sec + ' s').join(', ') + ' outlast the 5 s the page says to film');
pass();
