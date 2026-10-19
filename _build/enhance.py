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
EMAIL = "stephens.josef@gmail.com"
LINKEDIN = None      # Josef's profile URL; until then the footer link is left out


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
.tl-row{display:grid;grid-template-columns:minmax(150px,220px) minmax(0,1fr) 64px;gap:16px;align-items:center}
.tl-track{height:28px;background:#15261F;border:1px solid #2B3D35;position:relative}
.tl-bar{position:absolute;inset:0 auto 0 0;width:0;transition:width 1100ms cubic-bezier(.2,.7,.2,1)}
.tl.on .tl-bar{width:var(--w)}
@media (max-width:640px){.tl-row{grid-template-columns:minmax(0,1fr) 56px}.tl-row>span:first-child{grid-column:1 / -1}}
@media (prefers-reduced-motion:reduce){.tl-bar{transition:none}}
.iq{font:inherit;cursor:pointer;min-height:48px;padding:0 16px;border-radius:2px;border:1.5px solid #3A4D44;background:transparent;color:#E9EEE9;font-size:16px;font-weight:600;text-align:left}
.iq:hover{border-color:#F07A4E}
.iq[aria-pressed="true"]{background:#E8592B;border-color:#E8592B;color:#0E1B17}
#iq-send[disabled]{opacity:.45;cursor:not-allowed}
</style>"""

TIMELINE = f"""  <div style="max-width: 1240px; margin: 0 auto; padding: 0 clamp(16px, 4vw, 48px) clamp(72px, 9vw, 120px); display: flex; flex-direction: column; gap: 20px">
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 12px; border-top: 1px solid #2B3D35; padding-top: 36px">
      <h3 style="margin: 0; {BIG}; font-size: clamp(30px, 3.4vw, 44px); line-height: 1">Where 21 minutes of footage went</h3>
      <span style="{MONO}; font-size: 13px; color: #93A39A">The same August shoot · drawn to scale</span>
    </div>
    <div class="tl" id="tl" role="img" aria-label="Filmed 21 minutes 28 seconds. Kept by the motion scan 13 minutes 33 seconds. In the finished reel 1 minute 21 seconds." style="display: flex; flex-direction: column; gap: 14px">
      <div class="tl-row"><span style="{MONO}; font-size: 14px; color: #B5C2BA">Filmed</span><div class="tl-track"><div class="tl-bar" style="--w: 100%; background: #4C5F56"></div></div><strong style="{MONO}; font-size: 17px; text-align: right">21:28</strong></div>
      <div class="tl-row"><span style="{MONO}; font-size: 14px; color: #B5C2BA">Kept by the motion scan</span><div class="tl-track"><div class="tl-bar" style="--w: 63.1%; background: #93A39A"></div></div><strong style="{MONO}; font-size: 17px; text-align: right">13:33</strong></div>
      <div class="tl-row"><span style="{MONO}; font-size: 14px; color: #B5C2BA">In the finished reel</span><div class="tl-track"><div class="tl-bar" style="--w: 6.3%; background: #E8592B"></div></div><strong style="{MONO}; font-size: 17px; text-align: right; color: #F07A4E">1:21</strong></div>
    </div>
    <p style="margin: 0; max-width: 64ch; font-size: 18px; color: #C9D2CB">About 94 of every 100 seconds filmed never reach the reel. The motion scan drops the cleanup and the empty pots, and the edit keeps the 81 seconds that walk through the recipe one step at a time.</p>
  </div>
"""


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
        <button type="button" id="iq-send" disabled="" class="btn-blaze" style="min-height: 56px; padding: 0 26px; border: 0; border-radius: 2px; background: #E8592B; color: #0E1B17; font: 700 17px 'Instrument Sans', sans-serif; cursor: pointer">Write my email →</button>
        <span style="font-size: 15px; color: #93A39A">It opens in your own email app. Nothing sends until you press send.</span>
      </div>
    </div>"""

if DROPIN_DATE:
    drop_when, drop_where, drop_cta, drop_subj = DROPIN_DATE, DROPIN_PLACE or "Santa Rosa", "Tell me you're coming →", "Drop-in%20hours%3A%20I%27m%20coming"
else:
    drop_when = "The list hears first"
    drop_where = "Twenty minutes, your pile and my full attention, somewhere in Santa Rosa with decent coffee. Dates go to the list before they go anywhere else."
    drop_cta, drop_subj = "Put me on the list →", "Drop-in%20hours%3A%20put%20me%20on%20the%20list"

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
      <a href="mailto:{EMAIL}?subject={drop_subj}" style="align-self: flex-start; display: inline-flex; align-items: center; min-height: 52px; padding: 0 22px; margin-top: 6px; background: #16201C; color: #F2EDE1; text-decoration: none; font-weight: 700; border-radius: 2px">{drop_cta}</a>
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
      "Total running time of the raw clips from the shoot, as the Reels Engine logged them before the scan.",
      "What the motion scan kept, from the same run log. Cleanup and empty-pot shots are cut automatically.",
      "The finished file: 1080×1920, 81 seconds, one caption for each recipe step.",
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

  // 2. Timeline bars grow when they come into view.
  var tl = document.getElementById('tl');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { tl.classList.add('on'); io.disconnect(); } });
    }, { threshold: 0.4 });
    io.observe(tl);
  } else { tl.classList.add('on'); }

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
    var subject = 'Blueprint question' + (name ? ': ' + name : '');
    var body = 'Hi Josef,\n\n' +
      'What I have a pile of: ' + pile + '\n' +
      'What I run: ' + answers.q1 + (name ? ' (' + name + ')' : '') + '\n' +
      'Who says yes: ' + answers.q2 + '\n' +
      'When: ' + answers.q3 + '\n\n' +
      'The part that never gets done:\n\n\n' +
      'Thanks,\n';
    var url = 'mailto:EMAIL?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    send.setAttribute('data-mailto', url);
    window.location.href = url;
  });
})();
</script>
""".replace("EMAIL", EMAIL)


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
    t = rep(t, "  </div>\n</section>\n\n<!-- ============ THE ROUTE ============ -->",
            "  </div>\n" + TIMELINE + "</section>\n\n<!-- ============ THE ROUTE ============ -->")

    # Intake quiz under the picker message.
    t, n = re.subn(r'<div id="pick-msg".*?</div>', lambda m: m.group(0) + INTAKE, t, flags=re.S)
    assert n == 1, "pick-msg"


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


def add_decoder():
    shutil.copy(HERE / "comp3.html", OUT / "comp3.html")


fix_linkedin()
enhance_local()
enhance_mainframe()
add_decoder()
for f in ("index.html", "local.html", "mainframe.html", "comp3.html"):
    assert "—" not in (OUT / f).read_text(encoding="utf-8"), "em dash in " + f
print("enhanced")
