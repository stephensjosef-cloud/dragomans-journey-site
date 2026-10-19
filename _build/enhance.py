#!/usr/bin/env python3
"""Second build stage, run after build.py on the same output folder.

Adds what the canvas mock doesn't carry: the packed-decimal decoder page,
tap-a-number sources on the receipts, the raw-to-reel timeline, the intake
quiz that writes the first email, drop-in hours, and stand-ins for missing
photos. Every edit must match exactly once.
"""
import re
import shutil
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent

# Fill these in when Josef sets the first drop-in. Leave None until then.
DROPIN_DATE = None    # e.g. "Thursday, November 12 · 3 to 5 PM"
DROPIN_PLACE = None   # e.g. "Santa Rosa Central Library, 211 E Street"
EMAIL = "hello@dragomansjourney.com"
ENDPOINT = "https://dj-intake.stephens-josef.workers.dev/"
LINKEDIN = None
# Case-study client. Swap in the real name once Teresa says yes in writing.
CLIENT_LONG = "A Sonoma County children's nonprofit"
CLIENT_SHORT = "a Sonoma County children's nonprofit"
PHOTO = HERE / "assets" / "josef.jpg"   # drop Josef's photo here and rebuild      # Josef's profile URL; until then the footer link is left out


def rep(text, old, new, count=1):
    n = text.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    return text.replace(old, new)


def rep_re(text, pattern, new, count=1):
    rx = re.compile(pattern, re.S)
    n = len(rx.findall(text))
    assert n == count, f"expected {count} of /{pattern[:60]}/, found {n}"
    return rx.sub(lambda m: new, text)


MONO = "font-family: 'JetBrains Mono', monospace"
BIG = "font-family: 'Big Shoulders Display', Impact, sans-serif; font-weight: 800; text-transform: uppercase"

# ------------------------------------------------------------------ local
LOCAL_CSS = """<style>
.src-btn{font:inherit;cursor:pointer;background:none;border:0;padding:0;text-decoration:underline dotted #F07A4E 1.5px;text-underline-offset:5px}
.src-btn:hover,.src-btn[aria-expanded="true"]{color:#FFFFFF!important}
.src-note{grid-column:1 / -1;font-family:'Instrument Sans',sans-serif;font-size:14px;line-height:1.5;color:#93A39A;padding:2px 0 4px;border-left:2px solid #F07A4E;padding-left:12px}
.iq{font:inherit;cursor:pointer;min-height:48px;padding:0 16px;border-radius:2px;border:1.5px solid #3A4D44;background:transparent;color:#E9EEE9;font-size:16px;font-weight:600;text-align:left}
.iq:hover{border-color:#F07A4E}
.iq[aria-pressed="true"]{background:#E8592B;border-color:#E8592B;color:#0E1B17}
#iq-send[disabled]{opacity:.45;cursor:not-allowed}
</style>"""


def iq_group(gid, question, options):
    btns = "".join(f'<button type="button" class="iq" data-q="{gid}" aria-pressed="false">{o}</button>' for o in options)
    return (f'<div role="group" aria-labelledby="{gid}-l" style="display: flex; flex-direction: column; gap: 10px">'
            f'<span id="{gid}-l" style="{MONO}; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: #93A39A">{question}</span>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 8px">{btns}</div></div>')


INTAKE = f"""
    <div id="intake" hidden="" style="display: flex; flex-direction: column; gap: 20px; padding: clamp(18px, 2.4vw, 28px); border: 1px solid #3A4D44; background: #1A2822; border-radius: 2px">
      <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px">
        <h3 style="margin: 0; {BIG}; font-size: clamp(26px, 2.6vw, 32px); line-height: 1">Three taps and I'll write your first email</h3>
        <span style="{MONO}; font-size: 13px; color: #93A39A">You can change anything before it sends.</span>
      </div>
      {iq_group("q1", "What do you run?", ["A small business", "A nonprofit", "A school or youth program"])}
      {iq_group("q2", "Who says yes to spending money?", ["I do", "Me and one other person", "A board or committee"])}
      {iq_group("q3", "When would you want to start?", ["This month", "In the next few months", "Just looking for now"])}
      <label style="display: flex; flex-direction: column; gap: 10px; max-width: 520px">
        <span style="{MONO}; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: #93A39A">Name of your business or program (optional)</span>
        <input id="iq-name" autocomplete="organization" style="min-height: 52px; padding: 10px 14px; border: 1.5px solid #3A4D44; border-radius: 2px; background: #0E1B17; color: #E9EEE9; font: 500 17px 'Instrument Sans', sans-serif">
      </label>
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 16px">
        <button type="button" id="iq-send" disabled="" class="btn-blaze" style="min-height: 56px; padding: 0 26px; border: 0; border-radius: 2px; background: #E8592B; color: #0E1B17; font: 700 17px 'Instrument Sans', sans-serif; cursor: pointer">Continue to my Blueprint →</button>
        <span style="font-size: 15px; color: #93A39A">Your answers carry over. Nothing is sent yet.</span>
      </div>
    </div>"""

if DROPIN_DATE:
    drop_when, drop_where, drop_cta = DROPIN_DATE, DROPIN_PLACE or "Santa Rosa", "Save me a seat →"
else:
    drop_when = "The list hears first"
    drop_where = "Twenty minutes, your pile and my full attention, somewhere in Santa Rosa with decent coffee. Dates go to the list before they go anywhere else."
    drop_cta = "Put me on the list →"

DROPIN = f"""<!-- ============ DROP-IN HOURS ============ -->
<section id="dropin" aria-labelledby="dropin-h" style="background: #E8E1D1">
  <div style="max-width: 1240px; margin: 0 auto; padding: clamp(64px, 8vw, 104px) clamp(16px, 4vw, 48px); display: grid; grid-template-columns: repeat(auto-fit, minmax(min(380px, 100%), 1fr)); gap: clamp(28px, 5vw, 72px); align-items: center">
    <div style="display: flex; flex-direction: column; gap: 16px">
      <span style="{MONO}; font-size: 13px; letter-spacing: 0.1em; color: #A93F17">ONCE A MONTH · SANTA ROSA · FREE</span>
      <h2 id="dropin-h" style="margin: 0; {BIG}; font-size: clamp(44px, 5.6vw, 80px); line-height: 0.9; color: #16201C">Bring your pile</h2>
      <p style="margin: 0; max-width: 54ch; font-size: 19px; color: #3B4540">Bring the binder, the phone full of clips or the spreadsheet you dread. We sit down for twenty minutes and look at it together, and you leave knowing one thing you could do about it that week, with or without me.</p>
    </div>
    <div style="display: flex; flex-direction: column; gap: 14px; padding: clamp(22px, 3vw, 32px); border: 2px solid #16201C; background: #F2EDE1">
      <span style="{MONO}; font-size: 12px; letter-spacing: 0.1em; color: #6B716A">NEXT DROP-IN</span>
      <strong style="{BIG}; font-size: 34px; line-height: 1; color: #16201C">{drop_when}</strong>
      <span style="font-size: 17px; color: #3B4540">{drop_where}</span>
      <form id="dl" novalidate style="display: flex; flex-direction: column; gap: 10px; margin-top: 6px">
        <div style="position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden" aria-hidden="true"><input id="dl-website" tabindex="-1" autocomplete="off"></div>
        <label style="display: flex; flex-direction: column; gap: 6px"><span style="{MONO}; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #6B716A">Email</span>
          <input id="dl-email" type="email" autocomplete="email" required style="min-height: 52px; padding: 10px 14px; border: 1.5px solid #B9B09C; border-radius: 2px; background: #FBF8F1; color: #16201C; font: 500 17px 'Instrument Sans', sans-serif"></label>
        <label style="display: flex; flex-direction: column; gap: 6px"><span style="{MONO}; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #6B716A">Name (optional)</span>
          <input id="dl-name" autocomplete="name" style="min-height: 52px; padding: 10px 14px; border: 1.5px solid #B9B09C; border-radius: 2px; background: #FBF8F1; color: #16201C; font: 500 17px 'Instrument Sans', sans-serif"></label>
        <button type="submit" id="dl-send" style="align-self: flex-start; min-height: 52px; padding: 0 22px; border: 0; background: #16201C; color: #F2EDE1; font: 700 16px 'Instrument Sans', sans-serif; border-radius: 2px; cursor: pointer">{drop_cta}</button>
        <p id="dl-msg" role="status" style="margin: 0; font-size: 16px; color: #3B4540" hidden></p>
      </form>
    </div>
  </div>
</section>

"""

PHOTO_LOCAL = f"""<div role="img" aria-label="Josef Stephens, Santa Rosa" style="aspect-ratio: 4 / 5; width: 100%; max-width: 420px; background: #16201C; border: 2px solid #16201C; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; padding: 24px; color: #E9EEE9">
        <svg aria-hidden="true" viewBox="0 0 420 525" preserveAspectRatio="none" style="position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0.5"><path d="M-10 120 C 90 90, 180 150, 280 110 S 400 90, 430 120" fill="none" stroke="rgba(147,163,154,0.4)"/><path d="M-10 190 C 90 150, 190 230, 290 180 S 400 160, 430 190" fill="none" stroke="rgba(147,163,154,0.4)"/><path d="M-10 260 C 90 210, 200 310, 300 250 S 400 230, 430 260" fill="none" stroke="rgba(240,122,78,0.6)"/><path d="M-10 330 C 90 290, 190 370, 290 320 S 400 300, 430 330" fill="none" stroke="rgba(147,163,154,0.4)"/><path d="M-10 400 C 90 370, 180 430, 280 390 S 400 370, 430 400" fill="none" stroke="rgba(147,163,154,0.4)"/></svg>
        <span style="position: relative; {MONO}; font-size: 12px; letter-spacing: 0.12em; color: #93A39A">38.44° N · 122.71° W</span>
        <span style="position: relative; {BIG}; font-weight: 900; font-size: clamp(96px, 12vw, 150px); line-height: 0.8">JS</span>
      </div>"""

PHOTO_MF = """<div role="img" aria-label="Josef Stephens" style="margin-top: 8px; aspect-ratio: 4 / 5; width: 100%; background: #12161F; border: 1px solid #12161F; display: flex; flex-direction: column; justify-content: space-between; padding: 20px; color: #E6E2D8">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.14em; color: #B7BDC9">SIGNATORY</span>
        <span style="display: flex; flex-direction: column; gap: 6px"><em style="font-family: 'Newsreader', Georgia, serif; font-weight: 300; font-size: clamp(52px, 5vw, 68px); line-height: 1">J. S.</em><span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.14em; color: #B7BDC9">SANTA ROSA, CALIFORNIA</span></span>
      </div>"""

LOCAL_JS = r"""
<script>
(function () {
  // 1. Tap a number on a receipt to see where it comes from.
  var SRC = {
    reels: [
      "Each class gives 16 to 20 clips, from ten seconds to a couple of minutes each.",
      "One caption for each recipe step in the finished 1080×1920 reel.",
      "Machine time from the run log, scan through render. The people reviewing it come on top of this.",
      "The client reviewer's three notes from the first rounds. Each one is now an automatic check in the caption code.",
      "Every reel waits for the client's yes before it posts. None has gone out without it."
    ],
    app: [
      "The app's test suite on the latest release, Oct 7, 2026.",
      "The checks a release has to pass before it ships, all passing on that release.",
      "A rule in the database itself. A save without a photo is refused.",
      "Also a database rule. A step marked heat or knife won't save until it says what the grown-up does.",
      "Families never sign in, and no table stores anything about a child.",
      "One codebase, laid out for all three screen sizes."
    ],
    method: [
      "Two separate AI translations of the same program, both in the public repo with their prompts.",
      "Each translation checked against the original program in the findings file. A byte-level run over one shared input file hasn't been done yet.",
      "The findings file lists the misses beside what each translation got right.",
      "Code, prompts and findings are on GitHub for anyone to rerun."
    ]
  };
  var FOOT = {
    reels: "These logs hold a client's footage, so they stay private. I'll open any of them on a call.",
    app: "This is a client's app, so the repo stays private. I'll share my screen and run the tests while you watch.",
    method: "All of it is public. Open the repo and check it yourself."
  };
  var rowsEl = document.getElementById('rc-rows');
  var foot = document.getElementById('rc-src-foot');
  function current() {
    var on = document.querySelector('button[data-tab][aria-selected="true"]');
    return on ? on.getAttribute('data-tab') : 'reels';
  }
  var busy = false;
  function decorate() {
    if (busy) return;
    busy = true;
    var tab = current();
    Array.prototype.forEach.call(rowsEl.children, function (row, i) {
      var s = (SRC[tab] || [])[i];
      var strong = row.querySelector('strong');
      if (!s || !strong) return;
      var id = 'src-' + tab + '-' + i;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'src-btn';
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-controls', id);
      btn.setAttribute('aria-label', strong.textContent + ', show where this number comes from');
      btn.setAttribute('style', strong.getAttribute('style'));
      btn.textContent = strong.textContent;
      strong.parentNode.replaceChild(btn, strong);
      var note = document.createElement('span');
      note.id = id;
      note.className = 'src-note';
      note.hidden = true;
      note.textContent = s;
      row.appendChild(note);
      btn.addEventListener('click', function () {
        var open = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!open));
        note.hidden = open;
      });
    });
    foot.textContent = FOOT[tab] || '';
    busy = false;
  }
  new MutationObserver(function () { decorate(); }).observe(rowsEl, { childList: true });
  decorate();

  // 3. The picker opens three more questions, then writes the first email.
  var intake = document.getElementById('intake');
  var pile = '';
  document.querySelectorAll('button[data-pick]').forEach(function (b) {
    b.addEventListener('click', function () {
      var spans = b.querySelectorAll('span');
      pile = spans.length ? spans[spans.length - 1].textContent : b.textContent;
      intake.hidden = false;
    });
  });
  var answers = {};
  var send = document.getElementById('iq-send');
  document.querySelectorAll('button.iq').forEach(function (b) {
    b.addEventListener('click', function () {
      var q = b.getAttribute('data-q');
      document.querySelectorAll('button.iq[data-q="' + q + '"]').forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
      answers[q] = b.textContent;
      send.disabled = !(answers.q1 && answers.q2 && answers.q3);
    });
  });
  send.addEventListener('click', function () {
    if (send.disabled) return;
    var name = document.getElementById('iq-name').value.trim();
    var q = { pile: pile, run: answers.q1, yes: answers.q2, when: answers.q3, org: name };
    var url = 'start.html#' + Object.keys(q).filter(function (k) { return q[k]; })
      .map(function (k) { return k + '=' + encodeURIComponent(q[k]); }).join('&');
    send.setAttribute('data-href', url);
    window.location.href = url;
  });

  // 4. Drop-in list.
  var loaded = Date.now();
  var dl = document.getElementById('dl');
  dl.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var email = document.getElementById('dl-email').value.trim();
    var msg = document.getElementById('dl-msg');
    var btn = document.getElementById('dl-send');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { msg.textContent = 'I need an email to send the date to.'; msg.hidden = false; return; }
    btn.disabled = true;
    fetch('ENDPOINT', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ form: 'dropin', fields: { email: email, name: document.getElementById('dl-name').value.trim() }, website: document.getElementById('dl-website').value, ms: Date.now() - loaded }) })
      .then(function (r) { return r.json().then(function (j) { return r.ok && j.ok; }); })
      .catch(function () { return false; })
      .then(function (ok) {
        btn.disabled = false;
        if (ok) { dl.querySelectorAll('label, button').forEach(function (n) { n.hidden = true; }); msg.textContent = "You're on the list. The next date comes to your inbox first."; }
        else { msg.innerHTML = 'That didn\'t go through. Try again, or write to <a href="mailto:EMAIL">EMAIL</a>.'; }
        msg.hidden = false;
      });
  });
})();
</script>
""".replace("ENDPOINT", ENDPOINT).replace("EMAIL", EMAIL)


def enhance_local():
    p = OUT / "local.html"
    t = p.read_text(encoding="utf-8")
    t = rep(t, "</head>", LOCAL_CSS + "\n</head>")

    # Stand-ins for things Josef hasn't sent yet.
    t = rep_re(t, r'<div role="img" aria-label="Photo of Josef goes here".*?\[PHOTO OF JOSEF, OUTSIDE\]</div>', PHOTO_LOCAL)
    t = rep(t, " [ONE TRUE ALASKA STORY, TWO SENTENCES.]", "")
    t, n = re.subn(r'<a href="\[BOOKING LINK\]"([^>]*)>Or book 15 minutes first</a>',
                   lambda m: '<a href="#dropin"' + m.group(1) + '>Or come to drop-in hours</a>', t)
    assert n == 1, "booking link"


    # Receipts: hint, sources footer, timeline.
    t = rep(t, '>One shoot, one finished reel</h3>',
            '>One shoot, one finished reel</h3>\n      <span style="margin-top: -8px; font-size: 13px; color: #93A39A">Tap any orange number to see where it comes from.</span>')
    t = rep(t, '<a id="rc-link"',
            '<p id="rc-src-foot" style="margin: 0; font-family: \'Instrument Sans\', sans-serif; font-size: 14px; color: #93A39A"></p>\n      <a id="rc-link"')

    # Intake quiz under the picker message.
    t, n = re.subn(r'<div id="pick-msg".*?</div>', lambda m: m.group(0) + INTAKE, t, flags=re.S)
    assert n == 1, "pick-msg"


    # Receipts rule in one line, plus a way into the full Work page.
    t = rep(t, "Real numbers from real runs, every one tied to a log. Pick a tab, tap a number, and ask me to open the log on a call.",
            "Every number here comes from a run I can show you. If I can't show it, it isn't on this site. Pick a tab and tap a number to see where it came from. <a href=\"work.html\" style=\"color: #F07A4E; white-space: nowrap\">See all the work →</a>")
    t = rep(t, '<a href="#faq">Questions</a>', '<a href="#faq">Questions</a>\n        <a href="work.html">The work</a>')
    t = rep(t, 'href="#dropin" class="ghost"', 'href="call.html" class="ghost"')
    t = rep(t, '>Or come to drop-in hours</a>', '>Or grab a free 15-minute call</a>')
    if PHOTO.exists():
        t = rep(t, PHOTO_LOCAL, '<img src="josef.jpg" alt="Josef Stephens" style="aspect-ratio: 4 / 5; width: 100%; max-width: 420px; object-fit: cover; border: 2px solid #16201C; display: block">')

    # Every "start a Blueprint" button goes to the start page.
    for label in ("Start a Blueprint", "Start with a Blueprint"):
        t, k = re.subn(r'href="#blueprint"([^>]*>' + label + ')', lambda m: 'href="start.html"' + m.group(1), t)
        assert k == 1, label
    t = rep(t, 'href="mailto:stephens.josef@gmail.com?subject=Blueprint%20for%20%5Byour%20business%5D"', 'href="start.html"')

    # Drop-in hours before the contact band.
    t = rep(t, '<section id="contact"', DROPIN + '<section id="contact"')

    t = rep(t, "</body>", LOCAL_JS + "</body>")
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    left = re.findall(r"\[[A-Z ,.]{6,}\]", body)
    assert not left, f"bracket placeholder left in local.html: {left}"
    p.write_text(t, encoding="utf-8")


def enhance_mainframe():
    p = OUT / "mainframe.html"
    t = p.read_text(encoding="utf-8")
    t = rep_re(t, r'<div role="img" aria-label="Portrait of Josef Stephens goes here".*?\[PORTRAIT, BLACK AND WHITE\]</div>', PHOTO_MF)
    t = rep_re(t, r'\s*<div style="[^"]*"><dt[^>]*>CREDENTIALS</dt><dd[^>]*>\[IBM Z XPLORE BADGE, ONCE EARNED\]</dd></div>', "")
    t = rep(t, "The job is finding that answer and proving the new system honors it.</p>",
            'The job is finding that answer and proving the new system honors it. <a href="comp3.html" style="color: #F07A4E; white-space: nowrap">Decode your own bytes →</a></p>')
    corr = ('<a href="https://github.com/stephensjosef-cloud/cobol-behavioral-equivalence" class="quiet"')
    i = t.index(corr)
    j = t.index("</a>", i) + 4
    t = t[:j] + ('\n      <a href="comp3.html" class="quiet" style="display: flex; justify-content: space-between; align-items: center; gap: 16px; min-height: 76px; padding: 0 4px; border-bottom: 1px solid #12161F; color: #12161F; text-decoration: none; transition: background 160ms ease, color 160ms ease">'
                 '<span style="font-family: \'Newsreader\', Georgia, serif; font-size: 26px">Decode a packed field</span>'
                 '<span aria-hidden="true" style="font-family: \'JetBrains Mono\', monospace">→</span></a>') + t[j:]
    t = rep(t, 'href="mailto:stephens.josef@gmail.com?subject=Briefing%20request%3A%20%5Binstitution%5D"', 'href="briefing.html#ask=briefing"')
    t = rep(t, 'href="mailto:stephens.josef@gmail.com?subject=Survey%3A%20one%20program%20family"', 'href="briefing.html#ask=survey"')
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    assert not re.search(r"\[[A-Z ,.]{6,}\]", body), "bracket placeholder left in mainframe.html"
    p.write_text(t, encoding="utf-8")


def fix_linkedin():
    for f in ("index.html", "local.html", "mainframe.html"):
        p = OUT / f
        t = p.read_text(encoding="utf-8")
        if LINKEDIN:
            t = rep(t, 'href="[LINKEDIN URL]"', f'href="{LINKEDIN}"')
        else:
            t, n = re.subn(r'\n\s*<a href="\[LINKEDIN URL\]"[^>]*>LinkedIn</a>', "", t)
            assert n == 1, f
        p.write_text(t, encoding="utf-8")


def add_pages():
    for f in ("comp3.html", "start.html", "briefing.html", "work.html", "case-reels.html", "call.html"):
        t = (HERE / f).read_text(encoding="utf-8")
        t = t.replace("CLIENT_LONG", CLIENT_LONG).replace("CLIENT_SHORT", CLIENT_SHORT)
        (OUT / f).write_text(t, encoding="utf-8")
    if PHOTO.exists():
        shutil.copy(PHOTO, OUT / "josef.jpg")


def enhance_index():
    p = OUT / "index.html"
    t = p.read_text(encoding="utf-8")
    t = rep(t, '<span style="font-family: \'JetBrains Mono\', monospace; font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: #5D6576">Josef Stephens · Santa Rosa, California</span>',
            '<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px 20px; font-size: 15px">'
            '<a href="work.html" style="color: #3A4252; text-decoration: none">The work</a>'
            '<a href="call.html" style="display: inline-flex; align-items: center; min-height: 44px; padding: 0 16px; border: 1px solid #12161F; color: #12161F; text-decoration: none; font-weight: 600">Free 15-min call</a></span>')
    p.write_text(t, encoding="utf-8")


def use_hello():
    # The site's public address is hello@, which forwards to Josef's Gmail.
    for p in OUT.glob("*.html"):
        t = p.read_text(encoding="utf-8")
        p.write_text(t.replace("stephens.josef@gmail.com", EMAIL), encoding="utf-8")


fix_linkedin()
enhance_local()
enhance_mainframe()
add_pages()
enhance_index()
use_hello()
for f in ("index.html", "local.html", "mainframe.html", "comp3.html", "start.html", "briefing.html", "work.html", "case-reels.html", "call.html"):
    assert "—" not in (OUT / f).read_text(encoding="utf-8"), "em dash in " + f
print("enhanced")
