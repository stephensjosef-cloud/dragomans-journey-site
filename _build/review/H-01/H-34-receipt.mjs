// A fat-fingered minutes value freezes the page: finishDate() walks one day at a time, and once the date
// passes year 275760 it is Invalid, getDay() is NaN, `left` never drops and the while loop never ends.
// Run with `timeout 30`: the child is killed after 10 s and the repro fails.
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { fail, pass } from './harness.mjs';
if (process.argv[2] === 'child') {
  const { load } = await import('./harness.mjs');
  const h = await load('receipt.html', { now: '2026-11-24T12:00:00' });
  h.click(h.$$('#rows .fold')[0]);
  h.type(h.$$('#rows input[data-f=min]')[0], '300000000');   // input on "Answering the same questions"
  console.log('rendered: ' + h.text('.big2'));
  process.exit(0);
}
const r = spawnSync(process.execPath, [fileURLToPath(import.meta.url), 'child'], { timeout: 10000, encoding: 'utf8', env: process.env });
if (r.error || r.status !== 0) fail('typing 300000000 minutes hangs the page (no render after 10 s): ' + (r.error ? r.error.code : 'exit ' + r.status));
pass(r.stdout.trim());
