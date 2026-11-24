// One out-of-range character reference anywhere in the page (&#99999999;) throws in decode(): the Worker answers 500
// and the owner gets "Something went wrong on my side" for any page holding it.
import { W, fakeWeb, base, shopPage, HOME, load, wait, fail, pass } from './lib-checkup.mjs';
const web = fakeWeb(base({ [HOME]: { body: shopPage({ body: '<p>Bread &#99999999; butter</p>' }) } }));
let out;
try { out = await W.runCheck('goldencrust.com', web); } catch (e) { out = { threw: String(e) }; }
console.log(out.threw || 'ok');
if (out.threw) fail('runCheck throws ' + out.threw + ' (Worker answers 500 "failed")');
pass();
