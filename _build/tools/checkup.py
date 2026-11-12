"""Website checkup (T-04, Nov 12, 2026): one address box, a "Check it" button,
then two report cards built from what worker/checkup.js answers.
Until the Worker is live (CHECKUP_URL empty at the top of the script), the page
says "Coming this week" and shows no box."""
from chrome import write
import sys

CSS = r"""
.box{display:flex;flex-wrap:wrap;gap:12px;align-items:stretch}
.box input{flex:1 1 260px;width:auto;font-size:18px}
.box .btn{flex:0 0 auto}
.soon{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(40px,5vw,64px);line-height:.9;margin:0}
.rep h2{margin:0;font-size:24px;line-height:1.2}
.rep .label{margin-bottom:6px}
.addr{font-family:'JetBrains Mono',monospace;font-size:14px;color:#5A635D;margin:6px 0 0;overflow-wrap:anywhere}
.finds{list-style:none;margin:18px 0 0;padding:0;display:flex;flex-direction:column;gap:12px}
.find{border-left:4px solid #D9A520;background:#F9EEDA;padding:12px 14px}
.find.bad{border-left-color:#C2461B;background:#F8E3DA}
.find.info{border-left-color:#8A8F87;background:#EFEBE1}
.find h3{margin:0;font-size:18px;line-height:1.35}
.find p{margin:4px 0 0;font-size:16px;line-height:1.5}
.find .fix{font-size:15px;color:#3B4540}
.find .fix b{font-weight:600}
.oks{margin:18px 0 0;padding:0 0 0 20px;font-size:16px;line-height:1.7;color:#3B4540}
.note{font-size:15px;color:#5A635D;margin:14px 0 0}
.facts{margin-top:18px;background:#fff;border:1.5px solid #CFC6B2;padding:14px 16px}
.facts h3{margin:0 0 8px;font-size:18px}
.facts dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:6px 16px;margin:0;font-size:16px}
.facts dt{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#6B716A;padding-top:4px}
.facts dd{margin:0;overflow-wrap:anywhere}
.facts dd.none{color:#8A8F87}
.stat{font-size:16px;margin:0}
.stat a{font-size:14px}
.fixit{display:inline-flex;align-items:center;min-height:48px;margin-top:18px;font-weight:700;color:#16201C;font-size:18px}
@media (max-width:560px){.facts dl{grid-template-columns:minmax(0,1fr)}.facts dt{padding-top:6px}}
"""

BODY = r"""
  <section class="panel" id="soon" aria-labelledby="soon-h">
    <p class="soon" id="soon-h">Coming this week</p>
  </section>

  <section class="panel" id="ask" aria-labelledby="ask-h" hidden>
    <h2 id="ask-h" class="label">Your website's address</h2>
    <form id="form" class="box" novalidate>
      <label for="site" style="position:absolute;left:-9999px">Your website's address</label>
      <input id="site" name="site" type="text" inputmode="url" autocomplete="url" autocapitalize="off" spellcheck="false" placeholder="yourbusiness.com" required>
      <button type="submit" class="btn hot" id="go">Check it</button>
    </form>
    <p class="private" style="margin-top:10px">This checks your public page the way a visitor's phone would. Nothing is stored.</p>
    <p class="stat" id="msg" role="status" aria-live="polite" style="margin-top:10px"></p>
  </section>

  <section class="panel rep" id="rep1" aria-labelledby="rep1-h" hidden>
    <p class="label">Website checkup</p>
    <h2 id="rep1-h"></h2>
    <p class="addr" id="rep1-url"></p>
    <ul class="finds" id="finds1"></ul>
    <ul class="oks" id="oks1"></ul>
    <p class="note" id="note1"></p>
    <a class="fixit" href="call.html">Want me to fix it? →</a>
  </section>

  <p class="stat" id="stat" hidden>45% of people now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026). <a href="https://www.brightlocal.com/research/local-consumer-review-survey/" target="_blank" rel="noopener">See the source</a></p>

  <section class="panel rep" id="rep2" aria-labelledby="rep2-h" hidden>
    <h2 id="rep2-h">Can AI find you?</h2>
    <p style="margin:8px 0 0">This doesn't tell you what ChatGPT says about you. It checks whether a machine can read the facts it would need.</p>
    <ul class="finds" id="finds2"></ul>
    <div class="facts">
      <h3>The facts a machine reads off your page</h3>
      <dl id="facts"></dl>
      <p class="note" style="margin-top:12px">Check these against your Google Business Profile, letter for letter. I can't see your listing from here.</p>
    </div>
  </section>
"""

SCRIPT = r"""
var CHECKUP_URL = '';   // the dj-checkup Worker's address; empty until it's live (then the box shows)

(function () {
  var $ = function (id) { return document.getElementById(id); };
  if (!CHECKUP_URL) return;                        // "Coming this week" stays, no box
  $('soon').hidden = true; $('ask').hidden = false;

  var started = Date.now();
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
  var host = function (u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return u; } };
  var list = function (a) { return a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1]; };

  // What each kind of button costs when it fails.
  var LOSS = {
    book: "people who tap it can't book", order: "people who tap it can't order", contact: "people who tap it can't reach you",
    donate: "people who tap it can't give", menu: "people who tap it can't see your menu", schedule: "people who tap it can't find a time",
    appointment: "people who tap it can't make an appointment", reserve: "people who tap it can't reserve"
  };
  var cap = function (s) { return s.charAt(0).toUpperCase() + s.slice(1); };

  var ERR = {
    empty: "Type your website's address first.",
    'not-a-url': "That doesn't look like a web address. Try something like yourbusiness.com.",
    scheme: 'Only web addresses that start with http or https can be checked.',
    port: "That address uses an unusual port. I only check ordinary web addresses.",
    credentials: "Leave out the name and password, and I'll check the public page.",
    ip: "I only check addresses with a name, like yourbusiness.com, not a number.",
    'private-name': "That looks like an address inside a home or office network. I only check public sites.",
    'no-host': "That doesn't look like a web address. Try something like yourbusiness.com.",
    'private-ip': "That name points inside a private network, so I won't check it.",
    'no-such-host': "I couldn't find a site at that address. Check the spelling.",
    'dns-failed': "I couldn't look up that address just now. Try again in a minute.",
    timeout: "Your site took more than 8 seconds to answer. A visitor's phone would likely give up too.",
    unreachable: "Your site didn't answer. It may be down, or blocking checks like this one.",
    'too-many-redirects': 'Your address sends visitors through more than 3 redirects, so I stopped following them.',
    budget: "That took more checking than I can do at once. Try again in a minute.",
    wait: 'One check every 20 seconds. Try again in a moment.'
  };

  function finding(level, title, cost, fix) { return {level: level, title: title, cost: cost, fix: fix}; }
  var RANK = {bad: 0, warn: 1, info: 2};
  function render(ul, fs) {
    fs.sort(function (a, b) { return RANK[a.level] - RANK[b.level]; });
    ul.innerHTML = fs.map(function (f) {
      return '<li class="find ' + f.level + '"><h3>' + esc(f.title) + '</h3>' + (f.cost ? '<p>' + esc(f.cost) + '</p>' : '') +
        (f.fix ? '<p class="fix"><b>Fix:</b> ' + esc(f.fix) + '</p>' : '') + '</li>';
    }).join('');
  }

  function siteCard(r) {
    var f = [], good = [];
    if (r.status >= 400) f.push(finding('bad', 'Your page answers with an error (' + r.status + ')',
      'Anyone who opens this address sees an error instead of your page.',
      'Often quick once you find it: check the address, or ask whoever hosts your site.'));
    var broken = r.links.filter(function (l) { return l.status === 'broken'; });
    var nowhere = r.links.filter(function (l) { return l.status === 'nowhere'; });
    var working = r.links.filter(function (l) { return l.status === 'working'; });
    var seen = {};
    broken.forEach(function (l) {
      var k = 'b' + l.label + l.url; if (seen[k]) return; seen[k] = 1;
      f.push(finding('bad', 'Your "' + l.label + '" button ' + (l.code ? 'leads to an error page' : "leads to a page that doesn't load"),
        cap(LOSS[l.kind]) + '.', 'A five-minute fix in your site builder: point the button at the right page.'));
    });
    nowhere.forEach(function (l) {
      var k = 'n' + l.label; if (seen[k]) return; seen[k] = 1;
      f.push(finding('bad', 'Your "' + l.label + '" button goes nowhere',
        "Unless a script on your page catches the tap, " + LOSS[l.kind] + '.',
        'A five-minute fix in your site builder: give the button a real address.'));
    });
    if (!r.https) f.push(finding('bad', "Your site isn't on https",
      'Phones mark it "Not secure", and anything typed into a form on it can be read on the way.',
      'Usually free, and a few minutes with your host or site builder.'));
    else if (r.httpToHttps === false) f.push(finding('warn', "The plain http address doesn't send people on to https",
      'Anyone who types your address without https may land on a page marked "Not secure".',
      'Usually one setting with your host or site builder.'));
    if (!r.viewport) f.push(finding('bad', "Your page isn't set up for phones",
      'On a phone it shows as a tiny desktop page, and people pinch, zoom or leave.',
      'One line in your page, often a theme setting. A short fix for whoever built the site.'));
    if (!r.tel) f.push(r.facts.phone
      ? finding('warn', "Your phone number can't be tapped to call", 'On a phone, people have to copy it by hand.', 'A five-minute fix: make the number a phone link.')
      : finding('warn', "I couldn't find a phone number to tap", 'People who would rather call have to go looking.', 'A five-minute fix in your site builder: add your number as a phone link.'));
    if (!r.email && !r.contactForm) f.push(finding('warn', "I couldn't find an email address or a contact form",
      'People with a question have no easy way to write to you from this page.',
      'A short fix: add your email as a link, or a contact form.'));
    if (!r.title) f.push(finding('warn', 'Your page has no title',
      "Search results and browser tabs show your address instead of your name.",
      "A five-minute fix in your site builder's page settings."));
    if (!r.description) f.push(finding('warn', 'Your page has no description',
      'Search results and shared links make one up from whatever text they find first.',
      "A five-minute fix in your site builder's page settings, often called SEO."));
    if (r.cut) f.push(finding('warn', 'Your page is over 1.5 MB before any pictures',
      'It loads slowly on a phone with a weak signal. I only read the first 1.5 MB.',
      'Takes some digging, usually an add-on or pasted-in code. An hour with whoever built it.'));
    else if (r.bytes > 1048576) f.push(finding('warn', 'Your page is heavy: ' + (r.bytes / 1048576).toFixed(1) + ' MB before any pictures',
      'It loads slowly on a phone with a weak signal.',
      'Takes some digging, usually an add-on or pasted-in code. An hour with whoever built it.'));

    if (r.status < 400) good.push('Your page answers.');
    if (r.https) good.push('It uses https' + (r.httpToHttps ? ', and the plain http address sends people there.' : '.'));
    if (r.viewport) good.push("It's set up for phones.");
    if (r.tel) good.push('Your phone number can be tapped to call.');
    if (r.email || r.contactForm) good.push(r.contactForm ? 'It has a contact form.' : 'It has an email address.');
    if (r.title && r.description) good.push('It has a title and a description.');
    if (working.length) good.push(working.length + (working.length === 1 ? ' button works: ' : ' buttons work: ') +
      list(working.slice(0, 4).map(function (l) { return '"' + l.label + '"'; })) + (working.length > 4 ? ' and more' : '') + '.');
    if (!r.cut && r.bytes <= 1048576) good.push('It weighs ' + Math.max(1, Math.round(r.bytes / 1024)) + ' KB before pictures.');
    render($('finds1'), f);
    $('oks1').innerHTML = good.map(function (g) { return '<li>' + esc(g) + '</li>'; }).join('');
    var looked = r.links.length;
    var untested = r.links.filter(function (l) { return l.status === 'script' || l.status === 'unchecked' || l.status === 'refused'; }).length;
    $('note1').textContent = looked
      ? 'I tried every button and link that looks like booking, ordering, contact, donate, menu, schedule, appointment or reserve: ' + looked + ' in all' +
        (untested ? ', ' + untested + " of them I couldn't test from here" : '') + '.'
      : "I couldn't find a button for booking, ordering, contact, donating, a menu, a schedule, appointments or reservations on this page.";
    return f.length;
  }

  function aiCard(r) {
    var f = [], a = r.ai, s = r.structured, x = r.facts;
    var bots = function (names) { return a.bots.filter(function (b) { return names.indexOf(b.name) > -1; }); };
    if (a.starBlocksAll) f.push(finding('bad', 'Your robots.txt asks every crawler to stay out',
      "Search engines and AI tools that follow it won't read any page on your site.",
      'A five-minute fix, unless it was put there on purpose: remove "Disallow: /" under "User-agent: *" in robots.txt.'));
    if (a.answerBlocked.length) f.push(finding('bad', 'Your site turns AI readers away',
      'Your robots.txt asks ' + list(a.answerBlocked) + ' to stay out, so ' + list(bots(a.answerBlocked).map(function (b) { return b.what; })) +
      " can't read this page to answer questions about you.",
      'A five-minute fix: remove those lines from robots.txt.'));
    if (a.noindexMeta) f.push(finding('bad', 'Your page tells search engines not to list it',
      "Google, and AI tools that search the web, leave out a page marked noindex.",
      "A five-minute fix, unless it's on purpose: turn off \"hide from search engines\" in your page settings."));
    if (a.noindexHeader) f.push(finding('bad', 'Your server tells search engines not to list this page',
      "Google, and AI tools that search the web, leave out a page marked noindex.",
      'Needs whoever runs your hosting: the setting is called X-Robots-Tag.'));
    if (r.status === 200 && !r.cut && x.textLength < 600) f.push(finding('bad',
      'Your page holds almost no text a machine can read without running scripts or reading images.',
      "Tools that don't run scripts see an almost empty page, so they can't tell what you do or where.",
      'Takes some work: put your key facts on the page as plain text, not only in pictures or widgets.'));
    if (x.phoneMismatch) f.push(finding('warn', 'Your page gives two different phone numbers',
      'The number in your structured data, ' + x.structuredPhone + ", isn't the one in your page text, " + list(x.phones) + '. A machine has to guess which is right.',
      'A five-minute fix: make them match.'));
    if (!s.business) f.push(finding('warn', "Your page doesn't describe your business in structured data",
      'Structured data is a short block of plain facts made for machines. Without it, they guess your name, address and hours from the page text.',
      'Under an hour. Many site builders add it from a business info setting.'));
    else {
      var miss = [['name', 'name'], ['address', 'address'], ['telephone', 'phone number'], ['openingHours', 'opening hours'], ['url', 'web address']]
        .filter(function (k) { return !s.business.has[k[0]]; }).map(function (k) { return k[1]; });
      if (miss.length) f.push(finding('warn', 'Your structured data leaves out your ' + list(miss),
        'Your page describes itself as a ' + s.business.type + ' for machines, but without those facts.',
        'A short fix, wherever that block is set up.'));
    }
    if (!x.phone) f.push(finding('warn', "I couldn't find a phone number in your page text", 'A machine reading the page may not find one either.', 'A five-minute fix: put it on the page as plain text.'));
    if (!x.hours) f.push(finding('warn', "I couldn't find your opening hours in your page text", 'A machine reading the page may not find them either.', 'A five-minute fix: put them on the page as plain text, with the day names.'));
    if (!x.address) f.push(finding('warn', "I couldn't find a street address in your page text", 'A machine reading the page may not find one either.', 'A five-minute fix: put it on the page as plain text.'));
    if (typeof a.robotsStatus !== 'number' || a.robotsStatus >= 500) f.push(finding('info', "I couldn't read your robots.txt", '', ''));
    if (a.trainingBlocked.length) f.push(finding('info', 'Your robots.txt keeps ' + list(a.trainingBlocked) +
      " from collecting your pages for AI training. That's a choice, not a fault.", '', ''));
    render($('finds2'), f);

    var none = "I couldn't find it";
    var name = (s.business && s.business.name) || r.siteName || '';
    var rows = [['Name', name], ['Phone', x.phone || (s.business && s.business.telephone) || ''], ['Address', x.address || ''],
      ['Hours', x.hours || (s.business && s.business.openingHours) || '']];
    $('facts').innerHTML = rows.map(function (row) {
      return '<dt>' + row[0] + '</dt><dd' + (row[1] ? '>' + esc(row[1]) : ' class="none">' + none) + '</dd>';
    }).join('');
  }

  $('form').addEventListener('submit', function (e) {
    e.preventDefault();
    var v = $('site').value.trim(), go = $('go'), msg = $('msg');
    if (!v) { msg.textContent = ERR.empty; $('site').focus(); return; }
    go.disabled = true; go.textContent = 'Checking…'; msg.textContent = 'Checking ' + v + '. This can take up to 30 seconds.';
    fetch(CHECKUP_URL + '?url=' + encodeURIComponent(v), {method: 'GET', mode: 'cors', credentials: 'omit'})
      .then(function (res) { return res.json().catch(function () { return {ok: false, error: 'failed'}; }); })
      .then(function (r) {
        if (!r.ok) { msg.textContent = ERR[r.error] || "Something went wrong on my side. Try again in a minute."; return; }
        msg.textContent = '';
        $('rep1-h').textContent = host(r.finalUrl);
        $('rep1-url').textContent = r.finalUrl;
        var n = siteCard(r);
        aiCard(r);
        $('rep1').hidden = false; $('stat').hidden = false; $('rep2').hidden = false;
        $('rep1-h').textContent = (n ? n + (n === 1 ? ' thing to fix on ' : ' things to fix on ') : 'Nothing broken on ') + host(r.finalUrl);
        $('rep1').scrollIntoView({behavior: 'smooth', block: 'start'});
      })
      .catch(function () { msg.textContent = "I couldn't reach the checker just now. Try again in a minute."; })
      .then(function () { go.disabled = false; go.textContent = 'Check it'; });
  });
})();
"""

write(sys.argv[1], "checkup.html",
      title="Website Checkup",
      description="A free check for small businesses and nonprofits: paste your site's address and get a plain report of what's broken, and whether a machine can read your facts.",
      kicker="Free tool · checks your public page",
      h1="Website<br>checkup",
      lede="Paste your site's address. You get a plain report of what's broken, worst first: what it costs you and how hard it is to fix. Then whether AI tools can read the facts about your business.",
      css=CSS, body=BODY, script=SCRIPT,
      cta_h="Rather hand it off?", cta_p="Start with a free 15-minute call.",
      cta_href="call.html", cta_btn="Free 15-minute call")
