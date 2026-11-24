// Over a year of chores: the finish date lands in 2028 but the receipt prints only month and day.
import { load, fail, pass } from './harness.mjs';
const h = await load('receipt.html', { now: '2026-11-24T12:00:00' });
h.click(h.$('[data-p="11"]'));                       // + Talking with customers and families (60 min a workday)
const mins = h.$$('#rows input[data-f=min]');
h.type(mins[3], '480');                              // the owner talks with customers all day: 8 h a workday
const c = h.text('.big2');
// 325 h default + 2000 h = 2325 h = 291 workdays of 8 h from Fri 1 Jan 2027; 2027 has 261 weekdays.
const d = new Date(2027, 0, 1); let left = 2325;
while (left > 0) { const w = d.getDay(); if (w > 0 && w < 6) left -= 8; if (left > 0) d.setDate(d.getDate() + 1); }
if (d.getFullYear() !== 2028) fail('setup: expected a 2028 finish, got ' + d);
if (!/2028/.test(c)) fail('finish date shows "' + c + '" with no year; the real finish is ' + d.toDateString());
pass('finish date shows the year: ' + c);
