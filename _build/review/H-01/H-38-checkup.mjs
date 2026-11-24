// After one report, a second check that fails leaves the first site's report on screen under the new error.
import { W, fakeWeb, base, load, wait, fail, pass } from './lib-checkup.mjs';
const good = await W.runCheck('goldencrust.com', fakeWeb(base()));
let n = 0;
const h = await load('checkup.html', { fetch: async () => new Response(JSON.stringify(n++ ? { ok: false, error: 'no-such-host' } : good), { headers: { 'Content-Type': 'application/json' } }) });
for (const v of ['goldencrust.com', 'goldencrustbakrey.com']) { h.type('site', v); h.submit('form'); await wait(100); }
console.log(h.text('msg'), '|', h.$('rep1').hidden ? 'report hidden' : 'report shown: ' + h.text('rep1-h'));
if (!h.$('rep1').hidden) fail('"' + h.text('msg') + '" shows above the old report "' + h.text('rep1-h') + '"');
pass();
