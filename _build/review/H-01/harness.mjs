// H-01 harness: loads one of the site's root pages into jsdom, the way a phone would get it, with nothing
// leaving the machine. Every fetch is stubbed (a test passes its own), the clipboard, print, matchMedia,
// IntersectionObserver, ResizeObserver, scrollIntoView and URL.createObjectURL are stubbed, and any outside
// resource (Google Fonts) is answered with nothing. Read only: it never writes to the repo.
//
// Needs jsdom (and canvas, for the caption fitter) installed outside the repo:
//   mkdir /tmp/h01deps && cd /tmp/h01deps && npm init -y && npm install jsdom@26.1.0 canvas   (jsdom 31 has no ResourceLoader)
//   H01_DEPS=/tmp/h01deps node _build/review/H-01/H-18-voicecheck.mjs
// A repro exits 1 with one line when its bug is present, and 0 once it is fixed.

import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(here, '..', '..', '..');
const deps = process.env.H01_DEPS ? path.join(path.resolve(process.env.H01_DEPS), 'package.json') : import.meta.url;
const require = createRequire(deps);
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');

class LocalOnly extends ResourceLoader {
  fetch(url, options) {
    const u = new URL(url);
    if (u.hostname === 'localhost') {
      const f = path.join(ROOT, decodeURIComponent(u.pathname));
      if (f.startsWith(ROOT) && fs.existsSync(f) && fs.statSync(f).isFile()) return Promise.resolve(fs.readFileSync(f));
    }
    return Promise.resolve(Buffer.from(''));   // outside resources: nothing, never the network
  }
}

// A Date frozen at `iso` (or ticking from it with tick:true), for countdowns and "today".
function fakeDate(win, iso, tick) {
  const Real = win.Date, start = Real.now(), at = new Real(iso).getTime();
  const now = () => (tick ? at + (Real.now() - start) : at);
  class D extends Real {
    constructor(...a) { if (a.length) super(...a); else super(now()); }
    static now() { return now(); }
  }
  win.Date = D;
}

// load('receipt.html', {hash, now, fetch, beforeScripts(win)}) -> page handle
export async function load(page, opts = {}) {
  const file = path.join(ROOT, page);
  const html = fs.readFileSync(file, 'utf8');
  const errors = [], clip = [], prints = [], fetches = [], downloads = [];
  const vc = new VirtualConsole();
  vc.on('jsdomError', (e) => { if (!/Could not parse CSS stylesheet/.test(String(e && e.message))) errors.push(String(e && (e.stack || e.message))); });
  vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));
  const dom = new JSDOM(html, {
    url: 'http://localhost/' + page + (opts.hash ? (opts.hash.startsWith('#') ? opts.hash : '#' + opts.hash) : ''),
    runScripts: 'dangerously', resources: new LocalOnly(), pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(win) {
      if (opts.now) fakeDate(win, opts.now, opts.tick);
      Object.defineProperty(win.navigator, 'clipboard', { configurable: true,
        value: { writeText: (t) => { clip.push(String(t)); return Promise.resolve(); } } });
      win.print = () => { prints.push(Date.now()); };
      win.matchMedia = win.matchMedia || ((q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }));
      win.IntersectionObserver = win.IntersectionObserver || class { observe() {} unobserve() {} disconnect() {} };
      win.ResizeObserver = win.ResizeObserver || class { observe() {} unobserve() {} disconnect() {} };
      win.HTMLElement.prototype.scrollIntoView = function () {};
      win.scrollTo = () => {};
      win.URL.createObjectURL = (b) => { downloads.push(b); return 'blob:h01/' + downloads.length; };
      win.URL.revokeObjectURL = () => {};
      win.fetch = (u, o) => { fetches.push({ url: String(u), opts: o }); return opts.fetch ? opts.fetch(String(u), o) : Promise.reject(new TypeError('network blocked by the H-01 harness')); };
      win.addEventListener('error', (e) => errors.push('window error: ' + (e.error && e.error.stack || e.message)));
      win.addEventListener('unhandledrejection', (e) => errors.push('unhandled rejection: ' + String(e.reason)));
      if (opts.beforeScripts) opts.beforeScripts(win);
    }
  });
  const win = dom.window, doc = win.document;
  await new Promise((r) => { if (doc.readyState === 'complete') r(); else win.addEventListener('load', () => r()); });
  await wait(30);
  const $ = (sel) => (sel.startsWith('#') || /[ .[>:]/.test(sel) ? doc.querySelector(sel) : doc.getElementById(sel));
  const h = {
    dom, win, doc, $, errors, clip, prints, fetches, downloads,
    $$: (sel) => [...doc.querySelectorAll(sel)],
    text: (sel) => { const e = $(sel); return e ? e.textContent.replace(/\s+/g, ' ').trim() : null; },
    click: (el) => { el = typeof el === 'string' ? $(el) : el; if (!el) throw new Error('nothing to click'); el.dispatchEvent(new win.MouseEvent('click', { bubbles: true, cancelable: true })); },
    // type: sets the value and fires input (and change with {change:true}), the way typing ends up
    type: (el, value, o = {}) => {
      el = typeof el === 'string' ? $(el) : el;
      el.value = value;
      el.dispatchEvent(new win.Event('input', { bubbles: true }));
      if (o.change) el.dispatchEvent(new win.Event('change', { bubbles: true }));
    },
    select: (el, value) => { el = typeof el === 'string' ? $(el) : el; el.value = value; el.dispatchEvent(new win.Event('change', { bubbles: true })); },
    submit: (form) => { form = typeof form === 'string' ? $(form) : form; form.dispatchEvent(new win.Event('submit', { bubbles: true, cancelable: true })); },
    wait,
    close: () => win.close()
  };
  return h;
}

export function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

// fail('message') when the bug is there; pass() when it isn't. Both end the run.
export function fail(msg) { console.log('FAIL ' + msg); process.exit(1); }
export function pass(msg) { console.log('ok   ' + (msg || 'bug not present')); process.exit(0); }

// The dj-checkup Worker's logic, offline: checkup.js with its inner functions exported, imported from a temp copy.
// Never touches the live Worker; every outside request goes through the fetch and resolve a test passes to runCheck.
export async function loadWorker() {
  const os = await import('os');
  const { pathToFileURL } = await import('url');
  const NAMES = ['parseTarget', 'hostProblem', 'isPrivateIPv4', 'isPrivateIPv6', 'dnsProblem', 'safeFetch', 'readCapped',
    'actionKind', 'classifyHref', 'actionLinks', 'basics', 'parseRobots', 'robotsAllows', 'aiReaders', 'metaTags',
    'structuredData', 'textFacts', 'rawText', 'runCheck', 'tooSoon'];
  const src = fs.readFileSync(path.join(ROOT, '_build', 'worker', 'checkup.js'), 'utf8') + '\nexport const __t = { ' + NAMES.join(', ') + ' };\n';
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'h01-worker-'));
  const file = path.join(dir, 'checkup.mjs');
  fs.writeFileSync(file, src);
  const mod = await import(pathToFileURL(file).href);
  fs.rmSync(dir, { recursive: true, force: true });
  return { worker: mod.default, ...mod.__t };
}
