// Checks the intake Worker with no network and no Cloudflare: node test_intake.mjs
// Runs intake.js and intake.deployed.js side by side with a stand-in email
// binding, and checks what each would answer and send (T-10, Nov 11, 2026).
// Prints "<passed>/<total> passed" and exits 1 on any failure.
import fs from 'fs';
import os from 'os';
import path from 'path';
import { pathToFileURL, fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'intake-'));
async function load(name) {
  const src = fs.readFileSync(path.join(here, name), 'utf8')
    .replace(/import\s*\{\s*EmailMessage\s*\}\s*from\s*"cloudflare:email";/, 'class EmailMessage{constructor(f,t,r){this.raw=r}};');
  const out = path.join(tmp, name.replace(/\.js$/, '.mjs'));
  fs.writeFileSync(out, src);
  return (await import(pathToFileURL(out).href)).default;
}
function decode(raw) {
  const [head, body] = raw.split('\r\n\r\n');
  return {
    subject: Buffer.from(/Subject: =\?UTF-8\?B\?(.*)\?=/.exec(head)[1], 'base64').toString('utf8'),
    replyTo: /Reply-To: (.*)/.exec(head)[1].trim(),
    body: Buffer.from(body.replace(/\r\n/g, ''), 'base64').toString('utf8').replace(/, [^\n]* GMT\n/, ', <date>\n'),
  };
}
async function run(w, data, origin = 'https://dragomansjourney.com') {
  let sent = null;
  const env = { SEB: { send: async (m) => { sent = decode(m.raw); } } };
  const r = await w.fetch(new Request('https://dj-intake.example/', {
    method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json' }, body: JSON.stringify(data) }), env);
  return { status: r.status, json: await r.json(), sent };
}

const L = (fields, extra = {}) => ({ form: 'list', fields, ms: 3000, ...extra });
// [name, request, status, error or subject (null: nothing sent), origin]
const cases = [
  ['list deepcuts', L({ email: 'a@example.com', list: 'deepcuts' }), 200, 'List: deepcuts · a@example.com'],
  ['list birdleague', L({ email: 'b@example.com', list: 'birdleague' }), 200, 'List: birdleague · b@example.com'],
  ['list album', L({ email: 'c@example.com', list: 'album' }), 200, 'List: album · c@example.com'],
  ['list spots-feb, with a name', L({ email: 'd@example.com', list: 'spots-feb', name: 'Pat' }), 200, 'List: spots-feb · d@example.com'],
  ['list not one of the four', L({ email: 'a@example.com', list: 'other' }), 400, 'list'],
  ['list missing', L({ email: 'a@example.com' }), 400, 'missing list'],
  ['email missing', L({ list: 'deepcuts' }), 400, 'missing email'],
  ['email not an address', L({ email: 'a@b', list: 'deepcuts' }), 400, 'email'],
  ['honeypot filled: ok, nothing sent', L({ email: 'a@example.com', list: 'deepcuts' }, { website: 'x' }), 200, null],
  ['under 2.5 seconds: ok, nothing sent', L({ email: 'a@example.com', list: 'deepcuts' }, { ms: 1200 }), 200, null],
  ['another site', L({ email: 'a@example.com', list: 'deepcuts' }), 403, 'origin', 'https://elsewhere.example'],
  ['drop-in form as before', { form: 'dropin', fields: { email: 'e@example.com', org: 'Shop' }, ms: 3000 }, 200, 'Drop-in list: Shop'],
  ['blueprint form as before', { form: 'blueprint', fields: { name: 'Pat', email: 'p@example.com' }, ms: 3000 }, 200, 'Blueprint request: Pat'],
  ['briefing form as before', { form: 'briefing', fields: { name: 'Dana', email: 'd@bank.example', org: 'CU' }, ms: 3000 }, 200, 'Briefing request: CU'],
  ['call form as before', { form: 'call', fields: { name: 'Al', email: 'al@example.com' }, ms: 3000 }, 200, 'Call request: Al'],
];

const ok = [], bad = [];
const check = (name, cond, detail = '') => (cond ? ok : bad).push(name + (cond ? '' : '  ' + detail));
const src = await load('intake.js'), dep = await load('intake.deployed.js');
for (const [name, data, status, want, origin] of cases) {
  const a = await run(src, data, origin), b = await run(dep, data, origin);
  check(`${name}: intake.js and intake.deployed.js agree`, JSON.stringify(a) === JSON.stringify(b), JSON.stringify([a, b]));
  const sends = status === 200 && want !== null;
  const got = sends ? (a.sent && a.sent.subject) : a.json.error === undefined ? null : a.json.error;
  check(`${name}: ${status}, ${sends ? 'subject' : 'answer'} ${JSON.stringify(want)}`,
    a.status === status && a.json.ok === (status === 200) && got === want && (sends ? a.sent !== null : a.sent === null), JSON.stringify(a));
  if (sends && data.form === 'list') {
    check(`${name}: reply goes to the visitor, body lists the fields`, a.sent !== null && a.sent.replyTo === data.fields.email
      && a.sent.body.startsWith('List:\n' + data.fields.list + '\n\nEmail:\n' + data.fields.email + '\n')
      && (data.fields.name ? a.sent.body.includes('\nName:\n' + data.fields.name + '\n') : !a.sent.body.includes('Name:')), JSON.stringify(a.sent && a.sent.body));
  }
}
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`${ok.length}/${ok.length + bad.length} passed`);
for (const x of bad) console.log('FAIL', x);
process.exit(bad.length ? 1 : 0);
