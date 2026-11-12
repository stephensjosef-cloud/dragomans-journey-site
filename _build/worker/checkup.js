// dj-checkup: the Website checkup tool's Worker (T-04, Nov 12, 2026).
// GET /?url=<https://...> fetches one public page the way a visitor's phone
// would and answers with plain facts as JSON. checkup.html turns them into
// words. Nothing is stored except a 20-second marker per IP (the rate limit).
// Separate from intake.js on purpose; no bindings needed.

const ORIGINS = [
  "https://dragomansjourney.com", "http://dragomansjourney.com",
  "https://www.dragomansjourney.com", "http://www.dragomansjourney.com",
  "https://stephensjosef-cloud.github.io", "http://localhost:8765"
];
const UA = "dragomansjourney-checkup/1.0 (+https://dragomansjourney.com/checkup.html)";
const MAX_HOPS = 3;            // redirects followed per request, each one re-checked
const TIMEOUT_MS = 8000;       // per request
const MAX_BYTES = 1572864;     // 1.5 MB of the page, at most
const MAX_LINKS = 25;          // links checked, at most
const RATE_S = 20;             // one check per IP every 20 seconds
const BUDGET = 46;             // outside requests per check: the Workers Free plan allows 50
const BLOCKED_SUFFIX = [".localhost", ".local", ".internal", ".home.arpa", ".lan", ".intranet", ".corp", ".private"];

// The AI crawlers, by their robots.txt names, from each company's own docs (read Nov 12, 2026).
// "answer": fetches pages to answer a question or a search. "training": collects training data.
const AI_BOTS = [
  { name: "OAI-SearchBot", company: "OpenAI", kind: "answer", what: "ChatGPT search" },
  { name: "ChatGPT-User", company: "OpenAI", kind: "answer", what: "ChatGPT, when someone asks it to look" },
  { name: "GPTBot", company: "OpenAI", kind: "training", what: "OpenAI's training data" },
  { name: "Claude-SearchBot", company: "Anthropic", kind: "answer", what: "Claude's search" },
  { name: "Claude-User", company: "Anthropic", kind: "answer", what: "Claude, when someone asks it to look" },
  { name: "ClaudeBot", company: "Anthropic", kind: "training", what: "Anthropic's training data" },
  { name: "PerplexityBot", company: "Perplexity", kind: "answer", what: "Perplexity search" },
  { name: "Perplexity-User", company: "Perplexity", kind: "answer", what: "Perplexity, when someone asks it to look" },
  { name: "Googlebot", company: "Google", kind: "answer", what: "Google Search, AI Overviews and AI Mode" },
  { name: "Google-Extended", company: "Google", kind: "training", what: "Gemini's training data" }
];

// ---------------------------------------------------------------- safety
function isPrivateIPv4(ip) {
  const p = ip.split(".").map(Number);
  if (p.length !== 4 || p.some((n) => !Number.isInteger(n) || n < 0 || n > 255)) return true;
  const [a, b] = p;
  return a === 0 || a === 10 || a === 127 || a >= 224 ||
    (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) ||
    (a === 192 && b === 0 && (p[2] === 0 || p[2] === 2)) || (a === 198 && (b === 18 || b === 19)) ||
    (a === 192 && b === 88 && p[2] === 99) || (a === 198 && b === 51 && p[2] === 100) ||
    (a === 203 && b === 0 && p[2] === 113);
}
function isPrivateIPv6(ip) {
  const s = ip.toLowerCase().replace(/^\[|\]$/g, "");
  if (s === "::" || s === "::1") return true;
  const v4 = /(?:^|:)(\d+\.\d+\.\d+\.\d+)$/.exec(s);           // ::ffff:10.0.0.1 and friends
  if (v4) return isPrivateIPv4(v4[1]);
  if (/^::ffff:/.test(s)) return true;
  const first = parseInt(s.split(":")[0] || "0", 16);
  return (first & 0xfe00) === 0xfc00 ||   // fc00::/7 unique local
    (first & 0xffc0) === 0xfe80 ||        // fe80::/10 link local
    (first & 0xff00) === 0xff00 ||        // multicast
    first === 0x2001 && parseInt(s.split(":")[1] || "0", 16) === 0x0db8 ||   // documentation
    first === 0 || first === 0x64;        // ::/8 and 64:ff9b:: (translation)
}
const isIPv4 = (h) => /^\d{1,3}(\.\d{1,3}){3}$/.test(h);

// Is this host one we may fetch, before any DNS? Returns null when allowed, or the reason.
function hostProblem(host) {
  const h = String(host || "").toLowerCase().replace(/\.$/, "");
  if (!h) return "no-host";
  if (h.startsWith("[") || h.includes(":")) return "ip";
  if (isIPv4(h) || /^[\d.]+$/.test(h) || /^0x/i.test(h)) return "ip";
  if (h === "localhost" || BLOCKED_SUFFIX.some((s) => h.endsWith(s))) return "private-name";
  if (!h.includes(".")) return "private-name";
  return null;
}

// Parse what someone typed into a URL we may fetch. Returns { url } or { error }.
function parseTarget(input) {
  let s = String(input || "").trim();
  if (!s) return { error: "empty" };
  if (!/^[a-z][a-z0-9+.-]*:/i.test(s)) s = "https://" + s;
  let u;
  try { u = new URL(s); } catch (e) { return { error: "not-a-url" }; }
  if (u.protocol !== "http:" && u.protocol !== "https:") return { error: "scheme" };
  if (u.port && u.port !== "80" && u.port !== "443") return { error: "port" };
  if (u.username || u.password) return { error: "credentials" };
  const why = hostProblem(u.hostname);
  if (why) return { error: why };
  u.hash = "";
  return { url: u.href };
}

// Ask Cloudflare's own resolver where a name points, and refuse private addresses.
async function dnsProblem(host, deps) {
  if (!deps.dns) deps.dns = new Map();
  if (!deps.dns.has(host)) {
    if (!spend(deps, 2)) return "budget";
    deps.dns.set(host, await deps.resolve(host));
  }
  const answers = deps.dns.get(host);
  if (answers === null) return "dns-failed";
  if (!answers.length) return "no-such-host";
  for (const a of answers) {
    if (a.includes(":") ? isPrivateIPv6(a) : isPrivateIPv4(a)) return "private-ip";
  }
  return null;
}
async function dohResolve(host) {
  const out = [];
  try {
    for (const type of ["A", "AAAA"]) {
      const j = await withTimeout(async (signal) => {
        const r = await fetch("https://cloudflare-dns.com/dns-query?name=" + encodeURIComponent(host) + "&type=" + type,
          { headers: { Accept: "application/dns-json" }, signal });
        return r.ok ? r.json() : null;
      });
      if (!j) return null;
      for (const a of j.Answer || []) if (a.type === 1 || a.type === 28) out.push(String(a.data));
    }
  } catch (e) { return null; }
  return out;
}

function timer() {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  if (t && t.unref) t.unref();
  return { signal: ctl.signal, stop: () => clearTimeout(t) };
}
async function withTimeout(go) {
  const k = timer();
  try { return await go(k.signal); } finally { k.stop(); }
}
// Every outside request comes out of one budget per check.
function spend(deps, n) {
  if (deps.left === undefined) deps.left = BUDGET;
  if (deps.left < n) return false;
  deps.left -= n;
  return true;
}

// Fetch with every hop checked: scheme, port, host name and DNS. Never sends cookies.
// Returns { status, url, headers, response, hops, redirectedFrom } or { error, url }.
async function safeFetch(url, method, deps) {
  let current = url;
  for (let hop = 0; hop <= MAX_HOPS; hop++) {
    const p = parseTarget(current);
    if (p.error) return { error: p.error, url: current };
    const why = await dnsProblem(new URL(p.url).hostname, deps);
    if (why) return { error: why, url: p.url };
    if (!spend(deps, 1)) return { error: "budget", url: p.url };
    // The 8 seconds cover the answer and reading its body (readCapped), so the timer runs on.
    const k = timer();
    let r;
    try {
      r = await deps.fetch(p.url, {
        method, redirect: "manual", signal: k.signal,
        headers: { "User-Agent": UA, "Accept": method === "GET" ? "text/html,application/xhtml+xml,*/*;q=0.8" : "*/*" }
      });
    } catch (e) {
      k.stop();
      return { error: k.signal.aborted ? "timeout" : "unreachable", url: p.url };
    }
    if (r.status >= 300 && r.status < 400 && r.headers.get("Location")) {
      k.stop();
      if (r.body) try { await r.body.cancel(); } catch (e) {}
      if (hop === MAX_HOPS) return { error: "too-many-redirects", url: p.url };
      current = new URL(r.headers.get("Location"), p.url).href;
      continue;
    }
    return { status: r.status, url: p.url, headers: r.headers, response: r, hops: hop, stop: k.stop };
  }
  return { error: "too-many-redirects", url: current };
}

// Read at most `limit` bytes of a body. Returns { text, bytes, cut }.
async function readCapped(response, limit) {
  if (!response.body) return { text: "", bytes: 0, cut: false };
  const reader = response.body.getReader();
  const chunks = [];
  let bytes = 0, cut = false;
  while (true) {
    let step;
    try { step = await reader.read(); } catch (e) { cut = true; break; }   // timed out mid-page
    const { done, value } = step;
    if (done) break;
    if (bytes + value.length > limit) {
      chunks.push(value.slice(0, limit - bytes)); bytes = limit; cut = true;
      try { await reader.cancel(); } catch (e) {}
      break;
    }
    chunks.push(value); bytes += value.length;
  }
  const all = new Uint8Array(bytes);
  let at = 0;
  for (const c of chunks) { all.set(c, at); at += c.length; }
  return { text: new TextDecoder("utf-8").decode(all), bytes, cut };
}

// ---------------------------------------------------------------- reading the page
const decode = (s) => String(s || "")
  .replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/&lt;/gi, "<").replace(/&gt;/gi, ">")
  .replace(/&quot;/gi, '"').replace(/&#39;|&apos;/gi, "'")
  .replace(/&#(\d+);/g, (m, n) => String.fromCodePoint(Number(n)))
  .replace(/&#x([0-9a-f]+);/gi, (m, n) => String.fromCodePoint(parseInt(n, 16)));
const squash = (s) => decode(s).replace(/\s+/g, " ").trim();
function attr(tag, name) {
  const m = new RegExp("\\s" + name + "\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)'|([^\\s>]+))", "i").exec(tag);
  return m ? decode(m[1] ?? m[2] ?? m[3]) : null;
}
function metaTags(html) {
  return (html.match(/<meta\b[^>]*>/gi) || []).map((t) => ({
    name: (attr(t, "name") || attr(t, "property") || attr(t, "http-equiv") || "").toLowerCase(),
    content: attr(t, "content") || ""
  }));
}
// The page's words with scripts, styles and tags stripped, JavaScript not run.
function rawText(html) {
  return squash(String(html)
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<(script|style|noscript|template|svg)\b[\s\S]*?<\/\1\s*>/gi, " ")
    .replace(/<[^>]+>/g, " "));
}

const ACTION_WORDS = [
  ["book", /\bbook(ing|ings)?\b|\bbook\s*now\b/i], ["order", /\border(ing)?\b/i],
  ["contact", /\bcontact\b/i], ["donate", /\bdonat(e|ion|ions)\b|\bgive\s+now\b/i],
  ["menu", /\bmenus?\b/i], ["schedule", /\bschedul(e|ing)\b/i],
  ["appointment", /\bappointments?\b|\bappt\b/i], ["reserve", /\breserv(e|ation|ations)\b/i]
];
// Which kind of action a link or button looks like, from its words or its address. null: not one.
function actionKind(text, href) {
  const words = String(text || "");
  for (const [k, rx] of ACTION_WORDS) if (rx.test(words)) return k;
  let path = "";
  try { const u = new URL(href, "https://x.invalid/"); path = (u.hostname === "x.invalid" ? "" : u.hostname) + " " + u.pathname; } catch (e) {}
  path = path.replace(/[-_/.]+/g, " ");
  for (const [k, rx] of ACTION_WORDS) if (rx.test(path)) return k;
  return null;
}
// What a link's address does before anyone checks it. "nowhere": #, empty or javascript:.
// "other": tel:, mailto:, sms: and the like. "check": a web address to try.
function classifyHref(href, base) {
  const h = String(href ?? "").trim();
  if (!h || h === "#" || /^#!?$/.test(h) || /^javascript:/i.test(h)) return { kind: "nowhere" };
  if (h.startsWith("#")) return { kind: "anchor" };
  let u;
  try { u = new URL(h, base); } catch (e) { return { kind: "nowhere" }; }
  if (u.protocol !== "http:" && u.protocol !== "https:") return { kind: "other", scheme: u.protocol.slice(0, -1) };
  u.hash = "";
  return { kind: "check", url: u.href };
}
function actionLinks(html, base) {
  const out = [];
  const rx = /<(a|button)\b([^>]*)>([\s\S]*?)<\/\1\s*>/gi;
  let m;
  while ((m = rx.exec(html))) {
    const tag = "<" + m[1] + m[2] + ">";
    const inner = m[3];
    const label = squash(inner.replace(/<[^>]+>/g, " ")) || attr(tag, "aria-label") || attr(tag, "title") ||
      (attr(inner, "alt") || "");
    const isA = m[1].toLowerCase() === "a";
    const href = isA ? attr(tag, "href") : attr(tag, "formaction") || attr(tag, "data-href");
    const kind = actionKind(label, href || "");
    if (!kind) continue;
    if (!isA && href === null) { out.push({ kind, label: label.slice(0, 80), tag: "button", status: "script" }); continue; }
    const c = classifyHref(href, base);
    if (c.kind === "anchor" || c.kind === "other") continue;
    out.push({ kind, label: label.slice(0, 80), tag: isA ? "a" : "button", href: href || "", ...(c.kind === "check" ? { url: c.url } : { status: "nowhere" }) });
  }
  return out;
}

function basics(html, base) {
  const metas = metaTags(html);
  const title = squash((/<title\b[^>]*>([\s\S]*?)<\/title>/i.exec(html) || [])[1] || "");
  const desc = (metas.find((m) => m.name === "description") || {}).content || "";
  const vp = (metas.find((m) => m.name === "viewport") || {}).content || "";
  const hrefs = (html.match(/<a\b[^>]*>/gi) || []).map((t) => attr(t, "href") || "");
  const forms = html.match(/<form\b[\s\S]*?<\/form\s*>/gi) || [];
  const contactForm = forms.some((f) => /<textarea\b/i.test(f) || /type\s*=\s*["']?email/i.test(f) || /name\s*=\s*["']?[^"'>]*(email|message)/i.test(f));
  const text = rawText(html);
  return {
    title: title.slice(0, 200), description: squash(desc).slice(0, 300),
    siteName: squash((metas.find((m) => m.name === "og:site_name") || {}).content || "").slice(0, 200),
    viewport: /width\s*=\s*device-width/i.test(vp), viewportContent: vp.slice(0, 200),
    tel: hrefs.some((h) => /^\s*tel:/i.test(h)),
    email: hrefs.some((h) => /^\s*mailto:/i.test(h)) || /[\w.+-]+@[\w-]+(\.[\w-]+)+/.test(text),
    contactForm
  };
}

// ---------------------------------------------------------------- 8a: AI readers
function parseRobots(txt) {
  const groups = [];
  let cur = null, lastWasAgent = false;
  for (let line of String(txt || "").split(/\r?\n/)) {
    line = line.replace(/#.*/, "").trim();
    const m = /^([a-z-]+)\s*:\s*(.*)$/i.exec(line);
    if (!m) continue;
    const key = m[1].toLowerCase(), val = m[2].trim();
    if (key === "user-agent") {
      if (!cur || !lastWasAgent) { cur = { agents: [], rules: [] }; groups.push(cur); }
      cur.agents.push(val.toLowerCase());
      lastWasAgent = true;
    } else if (key === "allow" || key === "disallow") {
      if (cur) cur.rules.push({ allow: key === "allow", path: val });
      lastWasAgent = false;
    } else {
      lastWasAgent = false;
    }
  }
  return groups;
}
function ruleMatches(rule, path) {
  if (!rule) return false;
  let rx = rule.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
  if (rx.endsWith("\\$")) rx = rx.slice(0, -2) + "$";
  return new RegExp("^" + rx).test(path);
}
// RFC 9309: the group naming this agent (all of them merged), else "*"; the longest matching rule wins, allow on a tie.
function robotsAllows(groups, agent, path) {
  const a = agent.toLowerCase();
  let mine = groups.filter((g) => g.agents.includes(a));
  if (!mine.length) mine = groups.filter((g) => g.agents.includes("*"));
  let best = null;
  for (const g of mine) for (const r of g.rules) {
    if (r.path === "" ) continue;            // "Disallow:" with nothing means allow everything
    if (!ruleMatches(r.path, path)) continue;
    if (!best || r.path.length > best.path.length || (r.path.length === best.path.length && r.allow)) best = r;
  }
  return !best || best.allow;
}
function aiReaders(robotsTxt, path, metas, xRobots) {
  const groups = parseRobots(robotsTxt);
  const bots = AI_BOTS.map((b) => ({ ...b, allowed: robotsAllows(groups, b.name, path) }));
  const starBlocksAll = groups.some((g) => g.agents.includes("*")) && !robotsAllows(groups, "*", "/");
  const noindexMeta = metas.some((m) => (m.name === "robots" || m.name === "googlebot" || /bot$/.test(m.name)) && /\b(noindex|none)\b/i.test(m.content));
  const noindexHeader = /\b(noindex|none)\b/i.test(String(xRobots || ""));
  return {
    bots,
    answerBlocked: bots.filter((b) => b.kind === "answer" && !b.allowed).map((b) => b.name),
    trainingBlocked: bots.filter((b) => b.kind === "training" && !b.allowed).map((b) => b.name),
    starBlocksAll, noindexMeta, noindexHeader
  };
}

// ---------------------------------------------------------------- 8b: structured data
const BUSINESS_TYPES = new Set(["organization", "localbusiness", "corporation", "ngo", "nonprofitorganization", "professionalservice",
  "restaurant", "foodestablishment", "cafeorcoffeeshop", "bakery", "barorpub", "winery", "brewery", "store", "autorepair",
  "automotivebusiness", "dentist", "medicalbusiness", "medicalclinic", "physician", "medicalorganization", "healthandbeautybusiness",
  "beautysalon", "hairsalon", "dayspa", "homeandconstructionbusiness", "plumber", "electrician", "hvacbusiness", "roofingcontractor",
  "generalcontractor", "housepainter", "locksmith", "movingcompany", "legalservice", "attorney", "accountingservice", "financialservice",
  "insuranceagency", "realestateagent", "lodgingbusiness", "hotel", "sportsactivitylocation", "exercisegym", "entertainmentbusiness",
  "childcare", "educationalorganization", "school", "preschool", "animalshelter", "veterinarycare", "travelagency", "employmentagency",
  "selfstorage", "drycleaningorlaundry", "florist", "clothingstore", "bookstore", "petstore", "hardwarestore", "grocerystore",
  "onlinebusiness", "sportsorganization", "performinggroup", "governmentorganization", "library", "museum", "place"]);
function isBusinessType(t) {
  const list = Array.isArray(t) ? t : [t];
  return list.some((x) => {
    const s = String(x || "").replace(/^https?:\/\/schema\.org\//i, "").replace(/^schema:/i, "").toLowerCase();
    return s !== "place" && (BUSINESS_TYPES.has(s) || /(business|store|organization|service|restaurant|shop|clinic|agency|contractor)$/.test(s));
  });
}
function jsonLd(html) {
  const out = [];
  const rx = /<script\b[^>]*type\s*=\s*["']?application\/ld\+json["']?[^>]*>([\s\S]*?)<\/script\s*>/gi;
  let m;
  while ((m = rx.exec(html))) { try { out.push(JSON.parse(m[1].trim())); } catch (e) { out.push(undefined); } }
  return out;
}
function* walk(n) {
  if (Array.isArray(n)) { for (const x of n) yield* walk(x); return; }
  if (n && typeof n === "object") { yield n; for (const v of Object.values(n)) yield* walk(v); }
}
const flat = (v) => typeof v === "string" ? v : Array.isArray(v) ? v.map(flat).filter(Boolean).join("; ") :
  v && typeof v === "object" ? ["streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"].some((k) => v[k])
    ? ["streetAddress", "addressLocality", "addressRegion", "postalCode"].map((k) => flat(v[k])).filter(Boolean).join(", ")
    : flat(v.name || v["@id"] || "") : v == null ? "" : String(v);
function hoursText(n) {
  if (n.openingHours) return flat(n.openingHours);
  const spec = n.openingHoursSpecification;
  if (!spec) return "";
  return (Array.isArray(spec) ? spec : [spec]).map((s) => {
    const days = (Array.isArray(s.dayOfWeek) ? s.dayOfWeek : [s.dayOfWeek]).filter(Boolean)
      .map((d) => String(d).replace(/^https?:\/\/schema\.org\//i, "")).join(", ");
    return (days + " " + (s.opens || "") + (s.closes ? "-" + s.closes : "")).trim();
  }).filter(Boolean).join("; ");
}
function structuredData(html) {
  const blocks = jsonLd(html);
  const nodes = [];
  for (const b of blocks) if (b !== undefined) for (const n of walk(b)) if (n["@type"] && isBusinessType(n["@type"])) nodes.push(n);
  const best = nodes.sort((x, y) => score(y) - score(x))[0];
  function score(n) { return ["name", "address", "telephone", "url"].filter((k) => n[k]).length + (n.openingHours || n.openingHoursSpecification ? 1 : 0); }
  if (!best) return { blocks: blocks.length, broken: blocks.filter((b) => b === undefined).length, business: null };
  const type = Array.isArray(best["@type"]) ? best["@type"].join(", ") : String(best["@type"]);
  return {
    blocks: blocks.length, broken: blocks.filter((b) => b === undefined).length,
    business: {
      type,
      has: { name: !!best.name, address: !!best.address, telephone: !!best.telephone, openingHours: !!(best.openingHours || best.openingHoursSpecification), url: !!best.url },
      name: flat(best.name).slice(0, 200), address: flat(best.address).slice(0, 300),
      telephone: flat(best.telephone).slice(0, 60), openingHours: hoursText(best).slice(0, 300), url: flat(best.url).slice(0, 300)
    }
  };
}

// ---------------------------------------------------------------- 8c to 8e: facts in the raw text
const PHONE_RX = /(?:\+?1[\s.-]?)?\(?\b([2-9]\d{2})\)?[\s.-]?([2-9]\d{2})[\s.-](\d{4})\b/g;
const DAY = "(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day|sday|nesday|rsday|urday)?\\.?";
const TIME = "(?:\\b\\d{1,2}(?::\\d{2})?\\s*(?:a\\.?m\\.?|p\\.?m\\.?)|\\b\\d{1,2}:\\d{2}\\b|\\bnoon\\b|\\bmidnight\\b)";
const HOURS_RX = new RegExp("\\b" + DAY + "[^.]{0,40}?" + TIME + "|" + TIME + "[^.]{0,40}?\\b" + DAY + "\\b", "i");
const STREET_RX = /\b\d{1,6}\s+(?:[NSEW]\.?\s+)?(?:[A-Z0-9][\w.'-]*\s+){0,4}(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place|Hwy|Highway|Pkwy|Parkway|Cir|Circle|Ter|Terrace|Sq|Square|Trl|Trail)\b\.?/;
const digits = (s) => { const d = String(s || "").replace(/\D/g, ""); return d.length === 11 && d[0] === "1" ? d.slice(1) : d; };
function textFacts(html, sd) {
  const text = rawText(html);
  const phones = [];
  for (const m of text.matchAll(PHONE_RX)) { const p = m[0].trim(); if (!phones.some((x) => digits(x) === digits(p))) phones.push(p); }
  const hours = HOURS_RX.exec(text);
  const tag = /<address\b[^>]*>([\s\S]*?)<\/address\s*>/i.exec(html);
  const street = STREET_RX.exec(text);
  let address = null, addressFrom = null;
  if (tag && squash(tag[1].replace(/<[^>]+>/g, " "))) { address = squash(tag[1].replace(/<[^>]+>/g, " ")); addressFrom = "address-tag"; }
  else if (sd && sd.business && sd.business.address) { address = sd.business.address; addressFrom = "structured-data"; }
  else if (street) { address = street[0]; addressFrom = "text"; }
  const sdPhone = sd && sd.business && sd.business.telephone;
  const phoneMismatch = !!(sdPhone && phones.length && digits(sdPhone).length >= 10 && !phones.some((p) => digits(p) === digits(sdPhone)));
  return {
    phone: phones[0] || null, phones: phones.slice(0, 5),
    hours: hours ? squash(hours[0]).slice(0, 120) : null,
    address: address ? address.slice(0, 200) : null, addressFrom,
    textLength: text.length, phoneMismatch, structuredPhone: sdPhone || null
  };
}

// ---------------------------------------------------------------- the check
async function done(r) {
  if (r.stop) r.stop();
  if (r.response && r.response.body) try { await r.response.body.cancel(); } catch (e) {}
}
// HEAD first; a server that won't answer HEAD gets a GET.
async function checkLink(url, deps) {
  let r = await safeFetch(url, "HEAD", deps);
  await done(r);
  if (!r.error && [400, 403, 404, 405, 501].includes(r.status)) {
    const g = await safeFetch(url, "GET", deps);
    await done(g);
    if (g.error !== "budget") r = g;
  }
  if (r.error === "budget") return { status: "unchecked" };
  if (r.error) return { status: ["timeout", "unreachable", "too-many-redirects"].includes(r.error) ? "broken" : "refused", why: r.error };
  return { status: r.status >= 400 ? "broken" : "working", code: r.status };
}

async function runCheck(input, deps) {
  const t = parseTarget(input);
  if (t.error) return { ok: false, error: t.error };
  const page = await safeFetch(t.url, "GET", deps);
  if (page.error) return { ok: false, error: page.error, url: t.url };
  const body = await readCapped(page.response, MAX_BYTES);
  page.stop();
  const final = new URL(page.url);
  const ctype = page.headers.get("Content-Type") || "";
  const html = !ctype || /html|xml|text\/plain/i.test(ctype) ? body.text : "";

  // Does the plain http address send people on to https? null: couldn't tell.
  let httpToHttps = null;
  if (final.protocol === "https:") {
    const plain = new URL(final.href); plain.protocol = "http:";
    const h = await safeFetch(plain.href, "HEAD", deps);
    await done(h);
    if (!h.error) httpToHttps = h.hops > 0 && h.url.startsWith("https:");
  }

  // robots.txt on the same host, under the same rules. Missing (4xx) means no rules.
  let robots = "", robotsStatus = null;
  const rr = await safeFetch(final.origin + "/robots.txt", "GET", deps);
  if (!rr.error) {
    robotsStatus = rr.status;
    const rb = await readCapped(rr.response, 512000);
    rr.stop();
    if (rr.status >= 200 && rr.status < 300) robots = rb.text;
  } else robotsStatus = rr.error;

  // The action links last: each address once, at most 25, while the budget lasts.
  const links = actionLinks(html, page.url);
  const seen = new Map();
  let checked = 0;
  for (const l of links) {
    if (!l.url) continue;
    if (!seen.has(l.url)) {
      if (checked >= MAX_LINKS) { seen.set(l.url, { status: "unchecked" }); }
      else { checked++; seen.set(l.url, await checkLink(l.url, deps)); }
    }
    Object.assign(l, seen.get(l.url));
  }

  const metas = metaTags(html);
  const sd = structuredData(html);
  return {
    ok: true,
    url: t.url, finalUrl: page.url, status: page.status, redirects: page.hops,
    https: final.protocol === "https:", httpToHttps,
    bytes: body.bytes, cut: body.cut, contentType: ctype.slice(0, 100),
    ...basics(html, page.url),
    links: links.slice(0, 60), linksChecked: checked,
    ai: { ...aiReaders(robots, final.pathname + final.search, metas, page.headers.get("X-Robots-Tag")), robotsStatus },
    structured: sd,
    facts: textFacts(html, sd)
  };
}

// ---------------------------------------------------------------- the Worker
function cors(origin) {
  const h = { "Access-Control-Allow-Methods": "GET, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
  if (ORIGINS.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}
function reply(origin, status, obj) {
  return new Response(JSON.stringify(obj), { status, headers: { ...cors(origin), "Content-Type": "application/json", "Cache-Control": "no-store" } });
}
const recent = new Map();   // backup for the Cache API, per instance
async function tooSoon(ip, cache, now) {
  const key = "https://dj-checkup.invalid/rate/" + encodeURIComponent(ip);
  const last = recent.get(ip);
  if (last && now - last < RATE_S * 1000) return true;
  if (cache && await cache.match(key)) return true;
  recent.set(ip, now);
  if (recent.size > 5000) for (const [k, v] of recent) if (now - v > RATE_S * 1000) recent.delete(k);
  if (cache) await cache.put(key, new Response("1", { headers: { "Cache-Control": "max-age=" + RATE_S } }));
  return false;
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (request.method !== "GET") return reply(origin, 405, { ok: false, error: "method" });
    const q = new URL(request.url).searchParams.get("url");
    if (q === null) return new Response("dj-checkup is running", { headers: cors(origin) });
    if (!ORIGINS.includes(origin)) return reply(origin, 403, { ok: false, error: "origin" });
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const cache = typeof caches !== "undefined" ? caches.default : null;
    if (await tooSoon(ip, cache, Date.now())) return reply(origin, 429, { ok: false, error: "wait", seconds: RATE_S });
    try {
      const out = await runCheck(q, { fetch: (u, o) => fetch(u, o), resolve: dohResolve });
      return reply(origin, out.ok ? 200 : 400, out);
    } catch (e) {
      return reply(origin, 500, { ok: false, error: "failed" });
    }
  }
};
