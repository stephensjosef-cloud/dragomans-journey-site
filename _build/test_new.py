"""Checks for the Oct 18 additions: decoder, sources, timeline, intake, drop-in.

T-31 (Nov 19, 2026): every "# ----------------" section is a function with a short id (its T-number, or a slug of its
header). python _build/test_new.py BASE SHOTS runs them all, serially, as before; add --only T-30,T-29 to run just those,
and --results FILE to write every check to a JSON file. _build/run_tests.py runs them in parallel (see _build/README.md).
"""
import glob, hashlib, json, os, socket, sys, tempfile, time, traceback
from playwright.sync_api import sync_playwright

# T-31: UTF-8 out on every platform (a Windows console's code page crashed the failure list at T-30), a line at a time.
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
BASE = sys.argv[1]
SHOTS = sys.argv[2]
os.makedirs(SHOTS, exist_ok=True)
# T-31: the Linux Chromium where it is, otherwise Playwright's own installed Chromium (so no Windows copy is needed).
exe = (glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome') or [None])[0]
FONT_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts-test.css')).read()
FONT_DIR = '/tmp/claude-0/-home-claude/16ca1681-18c1-58d3-954a-5698233dc3a8/scratchpad/fonts'
FONT_FILES = {os.path.basename(f): f for f in glob.glob(FONT_DIR + '/*/package/files/*.woff2')}
ok, bad = [], []


def check(name, cond, detail=''):
    (ok if cond else bad).append(name + ('' if cond else f'  {detail}'))
    _report(name, cond, detail)   # T-31: printed (or sent to run_tests.py) the moment it is made


# T-31: each section registers itself here, in the file's order, under its short id.
SECTIONS = []


def section(sid):
    def reg(fn):
        SECTIONS.append((sid, fn))
        return fn
    return reg


# T-21 (Nov 16, 2026) changes line breaking only: a hyphen pair sits in a no-wrap span, a " · "
# is held to its neighbours by no-break spaces, a call button's words sit in one plain span,
# and the tool pages carry the call band rule and the djNw() helper. un21() takes those back
# out, for the older checks that compare markup with a build from before T-21. The T-21 block
# checks each of them on its own.
def un21(s):
    import re as _r
    s = _r.sub(r'<span>((?:(?!</?span)[^<])*<span style="white-space: nowrap">[^<]*</span>(?:(?!</?span)[^<])*)</span>', r'\1', s)
    s = _r.sub(r'<span style="white-space: nowrap">([^<]*)</span>', r'\1', s)
    s = s.replace('&nbsp;·&nbsp;', ' · ').replace(chr(160) + chr(183) + chr(160), ' ' + chr(183) + ' ')   # escaped, or read with html.unescape
    s = _r.sub(r'\n@media \(min-width:800px\)\{section\[aria-labelledby="more-h"\][^\n]*', '', s)
    s = _r.sub(r'\nfunction djNw\(s\)[^\n]*', '', s)
    return s


# T-23 (Nov 16, 2026): Josef's four lines K3b, K5b, K7b, K8b, and L1 to L7 (layout only).
# un23(s, name) takes them back out of a page's source, for the older checks that compare a
# page with T-22's build or one before it; the T-23 block checks each of them on its own.
T23_LINES = [   # (T-22's line, T-23's line)
    ("She films the class on her phone. The clips and the recipe card go through the engine. It finds the action, "
     "cuts the dead time and captions every step in her style. Every note she has given becomes a rule it checks on "
     "every reel after. Nothing posts until she says yes.",
     "She films the class on her phone. The clips and the recipe card go through the engine, which finds the action and "
     "cuts the dead time. I look over what's left and choose the cuts, and it captions every step in her style. Every "
     "mistake she has caught becomes a rule it checks on every reel after. Nothing posts until she says yes."),
    ('Every note she gives becomes a rule the engine checks on every reel after, so nobody catches the same thing twice.',
     'She caught three things in the first rounds: uneven caption boxes, square corners and words left alone on a line. '
     'The engine now checks for all three on every reel.'),
    ('Your staff try every update before any family sees it.',
     "It won't take a broken entry, like a recipe with no photo, and your staff try every update before any family sees it."),
    ("The program's own recipes, in an app teachers cook from in class. iPhone, iPad, Android and the web.",
     "The program's own recipes, in an app teachers cook from in class, with a grocery list that scales to the class and "
     "pages that print like their own cards. iPhone, iPad, Android and the web."),
]
T23_MORE_OLD = '<p class="noprint" style="margin:8px 0 0;font-size:15px;line-height:2;color:#5A635D">More free tools: %s</p>'
T23_STUDIO_CSS = ('.logsec{margin-top:0}\n.loghead{display:flex;flex-direction:column;gap:48px}\n'
                  '@media (min-width:800px){.loghead{flex-direction:row-reverse;flex-wrap:wrap-reverse;justify-content:flex-end;align-items:baseline;gap:8px clamp(24px,3vw,40px)}\n'
                  '.loghead .stats{border:0}.loghead .stats p{padding:0}\n'
                  '.loghead .stats strong{display:inline;font-size:clamp(38px,4.6vw,60px);margin-right:.18em}}\n')


def back23(t):
    """A line of text with T-23's four lines read as T-22's."""
    for old, new in T23_LINES:
        t = t.replace(new, old)
    return t


def un23(s, name):
    import re as _r
    for old, new in T23_LINES:
        s = s.replace(new, old)
    s = s.replace('<!-- T-22 K3; text is T-23 K3b -->', '<!-- T-22 K3 -->').replace('<!-- T-22 K8; body is T-23 K8b -->', '<!-- T-22 K8 -->')
    s = s.replace('<!-- T-22 K6; T-23 L5 keeps "4 minutes." on one line -->', '<!-- T-22 K6 -->')
    s = s.replace('about <span style="white-space: nowrap">4 minutes.</span>', 'about 4 minutes.')                                    # L5
    s = _r.sub(r'<span style="white-space: nowrap">([^\W_]+-[^\W_]+-[^\W_]+)</span>', r'\1', s)                                     # L1
    s = s.replace('h1.big{line-height:1}/* T-23 L2: the comma and any descender on the first line clear the line below */\n', '')    # L2
    s = s.replace('@media (max-width:699px){#sr-dot{display:none}}\n', '')                                                            # L3
    def more(m):                                                                                                                      # L4
        links = _r.findall(r'<a href="([^"]*)"><span style="white-space: nowrap">([^<]*)</span></a>', m.group(0))
        return T23_MORE_OLD % '&nbsp;·&nbsp;'.join(f'<a href="{h}">{t}</a>' for h, t in links)
    s = _r.sub(r'<p class="noprint" style="margin:4px 0 -4px -6px;padding:4px 0 4px 6px;overflow:hidden;[^"]*">.*?</p>', more, s, flags=_r.S)
    if name.startswith('studio'):
        s = s.replace(T23_STUDIO_CSS, '')                                                                                             # L7
        m = _r.search(r'\n  <section class="sec logsec" aria-labelledby="log-h">\n    <div class="loghead">(\n      <div class="stats".*?\n      </div>)'
                      r'\n      (<h2 id="log-h" class="big">Shipped lately</h2>)\n    </div>', s, _r.S)
        if m:
            s = s[:m.start()] + m.group(1).replace('\n    ', '\n') + '\n  <section class="sec" aria-labelledby="log-h">\n    ' + m.group(2) + s[m.end():]
    if name == 'studio.html':                                                                                                         # L6
        s = _r.sub(r'\n  <section aria-labelledby="next-h".*?</section>(?=\n</main>)', '', s, flags=_r.S)
    return s


# T-24 (Nov 17, 2026): Josef's seven lines A1 to A7, Exhibit A says what is stored (mainframe A1 to A5,
# comp3 A6 and A7). un24(s) takes them back out of a page's source or text, for the older checks that
# compare a page with T-23's build or one before it; the T-24 block checks each of them on its own.
T24_LINES = [   # (ID, page, T-23's words, T-24's words), in the order un24() swaps them back
    ('A1', 'mainframe.html', 'The code never divides by 100. The field definition allows two readings. See each one:',
                             'The code never divides by 100, and the field fits 3.5% stored either way. See each one:'),
    ('A2', 'mainframe.html', 'A fraction', 'Stored as 0.035'),
    ('A3', 'mainframe.html', 'A percentage', 'Stored as 3.5'),
    ('A4', 'mainframe.html', 'What the bank means: 3.5% a year, stored as a fraction.', 'Same code, right answer: 3.5% a year.'),
    ('A5', 'mainframe.html', "The only one that can't be wrong about what your business actually stored.",
                             "Reads 0.035: a fraction. The only one that can't be wrong about what your business actually stored."),
    ('A6', 'comp3.html', 'Exhibit A, read as a percentage', 'Exhibit A, stored as 3.5'),
    ('A6', 'comp3.html', 'Exhibit A, as the bank stored it', 'Exhibit A, stored as 0.035'),
    ('A7', 'comp3.html', 'Read as a fraction', 'What the code charges'),
    ('A7', 'comp3.html', 'Read as a percentage', 'If it means a percent'),
]
T24_NOTES = ("        <!-- T-24 A6: each example names what Exhibit A's field stores -->\n",
             "    // T-24 A7: the box labels say what each figure means; the math and figures stay.\n")


def un24(s):
    """A page's source or text with T-24's seven lines read as T-23's (and its two code comments out)."""
    for c in T24_NOTES:
        s = s.replace(c, '').replace(c.replace('\n', '\r\n'), '')
    for _id, _n, old, new in T24_LINES:
        s = s.replace(new, old).replace(new.upper(), old.upper())   # upper: comp3's labels as innerText shows them
    return s


# T-25 (Nov 17, 2026): F1 to F5 and T1, layout, wrapping and test code only, not one word. un25(s, name)
# swaps T-25's changes back out of a built page's source, for the older checks that compare markup with
# T-24's build or one before it; the T-25 block checks each of them on its own.
T25_SWAPS = [   # (page, T-24's text, T-25's text), exactly as built; un25() swaps each back
    ('captions.html',
     '.cardline .t{white-space:pre-line;font-size:15px;line-height:1.35;text-wrap:pretty}\n',
     "/* T-25 F3: each part is drawn the way the reel draws it: the fitter's own lines, never\n   reflowed to the page's width. The text box is the reel's caption width (--k = text size\n   over that width, set by render()), scaled down to fit the card, never above 15px. */\n.cardline .t{container-type:inline-size;min-width:0}\n.cardline .t>span{display:block;white-space:pre;font-size:min(15px,calc(100cqi * var(--k,0.066)));line-height:1.35}\n/* On a small phone the seconds sit under the words, so the drawing gets the card's width. */\n@media (max-width:420px){.cardline{grid-template-columns:auto minmax(0,1fr);row-gap:4px}.cardline .s{grid-column:2}}\n"),
    ('captions.html',
     '  document.getElementById(\'cards\').innerHTML=cards.map(function(c,i){return \'<button type="button" class="cardline" data-card="\'+i+\'" aria-pressed="\'+(i===st.card)+\'"><span class="n">\'+(i+1)+\'</span><span class="t">\'+esc(c.lines.join(\'\\n\'))+\'</span><span class="s">\'+readSecs(c.text)+\' s</span></button>\'}).join(\'\');\n',
     '  document.getElementById(\'cards\').style.setProperty(\'--k\',String(SIZES[st.size][1]/MAXW));\n  document.getElementById(\'cards\').innerHTML=cards.map(function(c,i){return \'<button type="button" class="cardline" data-card="\'+i+\'" aria-pressed="\'+(i===st.card)+\'"><span class="n">\'+(i+1)+\'</span><span class="t"><span>\'+esc(c.lines.join(\'\\n\'))+\'</span></span><span class="s">\'+readSecs(c.text)+\' s</span></button>\'}).join(\'\');\n'),
    ('case-reels.html',
     '',
     '<style>@media (min-width:900px){section[aria-labelledby="next-h"],section[aria-labelledby="c7"]{grid-template-columns:minmax(0,1fr) auto!important}}</style>\n'),
    ('local.html',   # this session: djNb() moved just outside the tabs' function, so LOCAL_JS's notes use the same one copy
     '<script>\n(function () {\n  var D = ',
     '<script>\nfunction djNb(s){return String(s).split(/(\\s+|&nbsp;|&#160;)/).map(function(p){if(p.indexOf(\'-\')<0)return p;var m=p.match(/^((?:[(\\["\'“‘]|&(?:quot|#x27|#39|ldquo|lsquo);)*)([\\p{L}\\p{N}]+(?:-[\\p{L}\\p{N}]+){1,2})((?:(?:[\'’]|&#x27;|&#39;|&rsquo;)s)?(?:[)\\]"\'”’.,;:!?…]|&(?:quot|#x27|#39|rdquo|rsquo|hellip);)*)$/u);return m&&m[2].length<=24?m[1]+\'<span style="white-space: nowrap">\'+m[2]+\'</span>\'+m[3]:p;}).join(\'\').replace(/[ \\t\\r\\n]+·[ \\t\\r\\n]+/g,\'&nbsp;·&nbsp;\')}\n(function () {\n  var D = '),
    ('local.html',   # the "grown-up" finding: the tap-to-see notes and their footer go through djNb()
     "  var foot = document.getElementById('rc-src-foot');\n",
     "  var foot = document.getElementById('rc-src-foot');\n  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }\n"),
    ('local.html',
     '      note.textContent = s;\n',
     '      // T-25 T1: a note is text this script writes, so it gets final.py\'s spans (djNb, from\n      // the tabs\' script): "grown-up" in the Apps tab\'s fourth note stays whole when shown.\n      note.innerHTML = djNb(esc(s));\n'),
    ('local.html',
     "    foot.textContent = FOOT[tab] || '';\n",
     "    foot.innerHTML = djNb(esc(FOOT[tab] || ''));\n"),
    ('local.html',
     '    $(\'rc-head\').textContent = rc.head;\n    $(\'rc-date\').textContent = rc.date;\n    $(\'rc-title\').textContent = rc.title;\n    // T-21 G2: a value like "iPhone · iPad · Android" keeps each dot with its neighbours, as on the built page.\n    $(\'rc-rows\').innerHTML = rc.rows.map(function (r) { return D.row.replace(\'{k}\', esc(r.k)).replace(\'{v}\', esc(r.v).replace(/ · /g, \'&nbsp;·&nbsp;\')); }).join(\'\');\n    $(\'rc-note\').textContent = rc.note;\n',
     "    // T-25 T1: redrawn text gets final.py's spans and held dots (djNb), so switching tabs\n    // and back gives the markup the page was built with (T-21 G2 did this for the values only).\n    $('rc-head').innerHTML = djNb(esc(rc.head));\n    $('rc-date').innerHTML = djNb(esc(rc.date));\n    $('rc-title').innerHTML = djNb(esc(rc.title));\n    $('rc-rows').innerHTML = rc.rows.map(function (r) { return D.row.replace('{k}', djNb(esc(r.k))).replace('{v}', djNb(esc(r.v))); }).join('');\n    $('rc-note').innerHTML = djNb(esc(rc.note));\n"),
    ('mainframe.html',
     '',
     '  function djNb(s){return String(s).split(/(\\s+|&nbsp;|&#160;)/).map(function(p){if(p.indexOf(\'-\')<0)return p;var m=p.match(/^((?:[(\\["\'“‘]|&(?:quot|#x27|#39|ldquo|lsquo);)*)([\\p{L}\\p{N}]+(?:-[\\p{L}\\p{N}]+){1,2})((?:(?:[\'’]|&#x27;|&#39;|&rsquo;)s)?(?:[)\\]"\'”’.,;:!?…]|&(?:quot|#x27|#39|rdquo|rsquo|hellip);)*)$/u);return m&&m[2].length<=24?m[1]+\'<span style="white-space: nowrap">\'+m[2]+\'</span>\'+m[3]:p;}).join(\'\').replace(/[ \\t\\r\\n]+·[ \\t\\r\\n]+/g,\'&nbsp;·&nbsp;\')}\n'),
    ('mainframe.html',
     "    $('xb-code').textContent = x.code;\n    $('xb-title').textContent = x.title;\n    $('xb-body').textContent = x.body;\n    $('xb-lesson').textContent = x.lesson;\n    $('xb-rows').innerHTML = x.rows.map(function (r) { return D.row.replace('{k}', esc(r.k)).replace('{v}', esc(r.v)); }).join('');\n",
     '    // T-25 T1: redrawn text gets final.py\'s spans (djNb), so Exhibit B after a round trip\n    // keeps "year-to-date" and "DEP-INTEREST-YTD" whole, as the page was built.\n    $(\'xb-code\').innerHTML = djNb(esc(x.code));\n    $(\'xb-title\').innerHTML = djNb(esc(x.title));\n    $(\'xb-body\').innerHTML = djNb(esc(x.body));\n    $(\'xb-lesson\').innerHTML = djNb(esc(x.lesson));\n    $(\'xb-rows\').innerHTML = x.rows.map(function (r) { return D.row.replace(\'{k}\', djNb(esc(r.k))).replace(\'{v}\', djNb(esc(r.v))); }).join(\'\');\n'),
    ('scaler.html',
     '      <p class="private" style="margin-top:8px">One ingredient per line, any format: 1 1/2 cups, 1½ cups, 3 Tbsp, 200 g, 2 large eggs.</p>\n',
     '      <p class="private" style="margin-top:8px">One ingredient per line, any format: <span style="white-space: nowrap">1 1/2 cups</span>, <span style="white-space: nowrap">1½ cups</span>, <span style="white-space: nowrap">3 Tbsp</span>, <span style="white-space: nowrap">200 g</span>, <span style="white-space: nowrap">2 large eggs.</span></p>\n'),
    ('scaler.html',
     '',
     'function amtNw(h){return String(h).replace(/(^|[\\s(])((?:\\d+\\s+\\d+\\/\\d+|\\d+\\s*[¼-¾⅐-⅞]|\\d+\\/\\d+|\\d*\\.?\\d+|[¼-¾⅐-⅞])(?:\\s+(?:(?:large|small|medium|ripe)\\s+)?[A-Za-z][A-Za-z.]*)?)/g,function(m,a,b){return /\\s/.test(b)?a+\'<span style="white-space: nowrap">\'+b+\'</span>\':m})}\n'),
    ('scaler.html',
     '  document.getElementById(\'facl\').textContent=(Math.round(portions*10)/10)+\' portions from a recipe that serves \'+serves+\'.\';\n  document.getElementById(\'warn\').innerHTML=batches>1?\'<p class="warn"><b>Make it in \'+batches+\' batches.</b> Most home pots, pans and mixing bowls top out at two or three times a recipe. Past that, things cook unevenly and pans crowd. Switch to "One batch" for the amounts per round.</p>\':\'\';\n',
     '  document.getElementById(\'facl\').innerHTML=amtNw(esc((Math.round(portions*10)/10)+\' portions from a recipe that serves \'+serves+\'.\'));\n  document.getElementById(\'warn\').innerHTML=batches>1?\'<p class="warn"><b>\'+amtNw(\'Make it in \'+batches+\' batches.\')+\'</b> Most home pots, pans and mixing bowls top out at two or three times a recipe. Past that, things cook unevenly and pans crowd. Switch to "One batch" for the amounts per round.</p>\':\'\';\n'),
    ('scaler.html',
     '  document.getElementById(\'out\').innerHTML=rows.map(function(r){return \'<tr><td class="amt">\'+esc(r.amt)+(r.was?\'<span class="was">was \'+esc(r.was)+\'</span>\':\'\')+\'</td><td>\'+esc(r.name)+\'</td><td class="note">\'+esc(r.note||\'\')+\'</td></tr>\'}).join(\'\')||\'<tr><td colspan="3" class="note">Paste some ingredients to start.</td></tr>\';\n',
     '  document.getElementById(\'out\').innerHTML=rows.map(function(r){return \'<tr><td class="amt">\'+amtNw(esc(r.amt))+(r.was?\'<span class="was">was \'+amtNw(esc(r.was))+\'</span>\':\'\')+\'</td><td>\'+amtNw(esc(r.name))+\'</td><td class="note">\'+amtNw(esc(r.note||\'\'))+\'</td></tr>\'}).join(\'\')||\'<tr><td colspan="3" class="note">Paste some ingredients to start.</td></tr>\';\n'),
    ('studio.html',
     '',
     '@media (max-width:799px){.loghead{flex-direction:row-reverse;flex-wrap:wrap-reverse;justify-content:flex-end;align-items:baseline;gap:8px 24px}\n.loghead .stats{border:0}.loghead .stats p{padding:0}\n.loghead .stats strong{display:inline;font-size:clamp(38px,4.6vw,60px);margin-right:.18em}}\n\n'),
    ('studio.html',
     '',
     '<style>@media (min-width:900px){section[aria-labelledby="next-h"],section[aria-labelledby="c7"]{grid-template-columns:minmax(0,1fr) auto!important}}</style>\n'),
    ('work.html',
     '',
     '<style>@media (min-width:900px){section[aria-labelledby="next-h"],section[aria-labelledby="c7"]{grid-template-columns:minmax(0,1fr) auto!important}}</style>\n'),
    ('work.html',    # Josef's ruling (Nov 17, 2026): the "2 AI" figure gets the headings' balanced wrap
     '',
     "/* T-25, Josef's ruling (Nov 17, 2026): the banking card's figure gets the balanced wrap the site's headings use. Same size, same words. */\n"
     '.card[data-k="banking"] .num{text-wrap:balance}\n'),
    ('work.html',
     '      <!-- T-22 K6; T-23 L5 keeps "4 minutes." on one line -->\n      <p class="num">An evening of editing, now about <span style="white-space: nowrap">4 minutes.</span></p>\n',
     '      <!-- T-22 K6; T-23 L5 keeps "4 minutes." on one line; T-25 F1: "of editing," and "now about" are held too, so no line holds one word ("about 4 minutes." whole is wider than the card at 320 and 1440) -->\n      <p class="num">An evening <span style="white-space: nowrap">of editing,</span> <span style="white-space: nowrap">now about</span> <span style="white-space: nowrap">4 minutes.</span></p>\n'),
]


def un25(s, name=None):
    """A built page's source with T-25's changes swapped back (name: only that page's)."""
    for n, old, new in T25_SWAPS:
        if name is None or n == name:
            s = s.replace(new, old)
    return s


# T-26 (Nov 18, 2026): "Inside the apps", a gallery on studio.html (its CSS and one section), nothing else.
# un26(s, name) takes both back out of a built page's source, for the older checks that compare studio.html
# with T-25's build or one before it; the T-26 block checks the gallery on its own.
def un26(s, name=None):
    import re as _r
    if name not in (None, 'studio.html'):
        return s
    if '\r\n' in s:   # a page read as served on Windows (CRLF): swap in LF, then back
        return un26(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    s = un27(s, name)   # T-27: the shelf out first, so every older check that reads through un26() sees T-26's page
    s = _r.sub(r'\.gal\{gap:28px\}\n(?:[^\n]*\n)*?@media \(min-width:800px\)\{\.grow\{[^\n]*\n\n', '', s)
    return _r.sub(r'\n  <section class="sec gal" aria-labelledby="gallery-h">.*?\n  </section>', '', s, flags=_r.S)


# T-27 (Nov 18, 2026): the ChuckleFits shelf on studio.html (its CSS and one block inside the ChuckleFits card),
# and the card's "Visit the shop" address tagged. un27(s, name) takes the shelf back out and the tag off that
# address, for the older checks that compare studio.html with T-26's build or one before it (un26() calls it
# first); the T-27 block checks the shelf on its own.
T27_TAG = 'utm_source=dragomansjourney&utm_medium=studio&utm_campaign=shelf'
T27_WHAT = ('My humor shirt shop. I write every line on every shirt.', 'My humor shirt shop.')   # (T-26's line, T-27's: Josef cut the second sentence, Nov 18)


def un27(s, name=None):
    import re as _r
    if name not in (None, 'studio.html'):
        return s
    if '\r\n' in s:
        return un27(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    s = un29(s, name)   # T-29: the cards back first, so every older check that reads through un27() or un26() sees T-27's page
    s = _r.sub(r'\.shelf\{margin:[^\n]*\n(?:[^\n]*\n)*?@media \(min-width:1200px\)\{\.shelf ul\{[^\n]*\n\n', '', s)
    s = _r.sub(r'\n        <div class="shelf" role="region".*?\n        </div>', '', s, flags=_r.S)
    s = s.replace(f'<p>{T27_WHAT[1]}</p>', f'<p>{T27_WHAT[0]}</p>')
    return s.replace('href="https://chucklefits.com/?' + T27_TAG.replace('&', '&amp;') + '"', 'href="https://chucklefits.com"')


def back27(t):
    """A page's text with T-27's cut line read back as T-26's (Josef cut "I write every line on every shirt.", Nov 18)."""
    return t.replace(T27_WHAT[1] + ' Visit the shop', T27_WHAT[0] + ' Visit the shop')


# T-29 (Nov 18, 2026): one block per app on studio.html. Bird League's and Deepcuts' cards are gone from the products
# grid; their words (pill, what, proof, "More on" link, join form, same markup) open their "Inside the apps" block
# instead; the section moved to right after "Shipped lately"; the Bird League card's then/now image is off the page;
# Free tools now spans its row (T-21 G4: it's alone on it), and the new placement's CSS is added. un29(s, name) puts
# T-27's page back byte for byte (the stamp line aside), rebuilding each card from its block's own markup, for the
# older checks that read studio.html as it was at T-27 (un27() calls it first); the T-29 block checks the new page.
T29_IDS = ('birdleague', 'deepcuts')   # studio.json's product order, the cards' order at T-27
T29_FEATURE_IMG = {'birdleague': '<img src="bird-league-then-now.jpg" width="1200" height="1331" loading="lazy" '
                                 'alt="Then: an early Bird League screen that still says mock data. Now: build 49\'s life list wall.">'}
T29_GPROD = (r'\n      <div class="gprod">\n        <div class="gtext">\n          (<div class="meta">.*?</div>)\n          (<p>.*?</p>)'
             r'(?:\n          (<p class="proof">.*?</p>))?\n          (<a class="go" data-page href="studio-([a-z0-9-]+)\.html">.*?</a>)'
             r'\n        </div>(?:\n        <div class="gjoin">(.*?)</div>)?\n      </div>(?=\n      <div class="ggroup">)')


def un29(s, name=None):
    import re as _r
    if name in (None, 'studio.html'):
        s = un30(s, 'studio.html')   # T-30: the two "what" lines back first, so every older check through un29() sees T-29's page
    if name not in (None, 'studio.html') or '<div class="gprod">' not in s:
        return s
    if '\r\n' in s:
        return un29(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    s = _r.sub(r'\.gprod\{[^\n]*\n(?:[^\n]*\n)*?\.gjoin\{flex:1 1 0;min-width:0\}\}\n\n', '', s, count=1)
    cards = {}
    def take(m):
        meta, what, proof, link, pid, join = m.groups()
        h3 = _r.findall(r'<h3>(.*?)</h3>', s[:m.start()])[-1]
        body = [f'<h2>{h3}</h2>', meta, what] + ([proof] if proof else []) + [f'<div class="acts">{link}{join or ""}</div>']
        if pid in T29_FEATURE_IMG:
            cards[pid] = (f'\n    <article class="prod feature" data-id="{pid}">\n      <div class="fb">\n        ' + '\n        '.join(body)
                          + f'\n      </div>\n      {T29_FEATURE_IMG[pid]}\n    </article>')
        else:
            cards[pid] = f'\n    <article class="prod" data-id="{pid}">\n        ' + '\n        '.join(body) + '\n    </article>'
        return ''
    s = _r.sub(T29_GPROD, take, s, flags=_r.S)
    gal = _r.search(r'\n  <section class="sec gal" aria-labelledby="gallery-h">.*?\n  </section>', s, _r.S)
    if gal:
        s = s[:gal.start()] + s[gal.end():]
    s = s.replace('<article class="prod wide" data-id="tools">', '<article class="prod" data-id="tools">')
    head = '\n  <div class="sec prods" id="products">'
    s = s.replace(head, head + ''.join(cards[i] for i in T29_IDS if i in cards), 1)
    if gal:
        m = _r.search(r'\n  <div class="sec prods" id="products">.*?\n  </div>', s, _r.S)
        s = s[:m.end()] + gal.group(0) + s[m.end():]
    return s


# T-30 (Nov 18, 2026): each paragraph lives on one page. The kids' app and COBOL cards on studio.html print no "what"
# line (studio.json's "what" is null), the four tool cards on local.html print no description (enhance.py's
# tool_cards() reads only each name and link from work.html), and a studio card that spans its row keeps its
# description at most 34em wide (one CSS rule). work.html keeps all six paragraphs. un30(s, name) puts the six
# paragraphs back byte for byte where they were and takes the rule out, so studio.html and local.html read as at
# T-29 (studio's stamp line aside), for the older checks that read those pages as they were at T-29 (un29() calls it
# first for studio.html); the T-30 block checks the new pages, and proves un30() against T-29's own files from git.
T30_STUDIO = [   # (card id, the paragraph as T-29 built it, right after the card's pill)
    ('kids', "<p>The program's own recipes, in an app teachers cook from in class, with a grocery list that scales to the class "
             "and pages that print like their own cards. iPhone, iPad, Android and the web.</p>"),
    ('cobol', '<p>Two different AIs translated the same COBOL interest program. The code, the prompts and every miss are '
              'published for anyone to rerun.</p>'),
]
T30_LOCAL = [   # (tool page, the paragraph's inner HTML as T-29 built it on local.html, right after the card's h3)
    ('shotlist.html', 'Pick what you run and what the reel should do. Get the 10 clips to film, how long each lasts, and the order '
                      'to shoot them in one lap of the room.'),
    ('captions.html', "Type a caption once. It breaks the lines evenly, splits it into screens, checks it against each app's buttons, "
                      'times it, and hands you a <span style="white-space: nowrap">see-through</span> PNG.'),
    ('receipt.html', 'Tap the chores that eat your week and get a receipt for a year of them, with an honest read on which ones '
                     'could come back and which should stay human.'),
    ('scaler.html', 'Paste any ingredient list, count <span style="white-space: nowrap">grown-ups</span> and kids, and get amounts '
                    'you can actually measure, eggs rounded up, and a <span style="white-space: nowrap">heads-up</span> when it\'s '
                    'time to cook in batches.'),
]
# T-30 (Josef, Nov 19): the Website checkup card, which shows on local.html only once CHECKUP_URL is set (T-20 F2), loses its
# description the same way; un30() puts it back when that card is on the page. Today it isn't, so this changes nothing.
T30_LOCAL_LIVE = [('checkup.html', "Paste your site's address and get a plain report of what's broken, worst first, and whether a machine "
                                   'can read the facts AI tools need.')]
T30_LOCAL_P = '<p style="margin: 0; font-size: 15px; line-height: 1.55; color: #3B4540">'
T30_CSS = '.prod.wide>p:not(.proof){max-width:34em}\n\n'
T30_LINK = ('<a href="{}" style="margin-top: auto; display: inline-flex; align-items: center; min-height: 44px; '
            'font-weight: 700; color: #16201C; text-decoration: none">')


def t30_text(h):
    """A paragraph's visible words: its HTML with the tags out."""
    import re as _r
    return _r.sub(r'<[^>]+>', '', h)


# T-33 (Nov 20, 2026): Josef's lines R2 to R23 change index, local, work, start, studio and the five tool pages.
# un33(s, name) takes them back out of a page from out/, for the older checks that compare a page with an earlier
# build: t33_undo.json holds each of T-33's changes in out/ (one unchanged line around it) beside origin/main's lines
# (the studio pages' build-day stamp aside), and under "_live" the same for a build with CHECKUP_URL set (T-20's temp
# build), tried first. The T-33 block proves the first: each page through un33(), themed by theme.py, is origin/main's
# root page byte for byte. T-20's address-set checks prove the second: its temp build, through un33(), gives back
# exactly what origin/main gave. un30() calls it first, as un29() calls un30(). Idempotent: on origin/main's own pages
# nothing matches.
T33_UNDO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't33_undo.json'), encoding='utf-8'))


def un33(s, name=None):
    if name not in T33_UNDO:
        return s
    if '\r\n' in s:
        return un33(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    for new, old in T33_UNDO['_live'].get(name, []) + T33_UNDO[name]:
        if s.count(new) == 1:
            s = s.replace(new, old)
    return s


# T-34 (Nov 20, 2026): the home opening, no italic switches and bigger Then and Now change index, 404, briefing, comp3,
# mainframe and studio. un34(s, name) takes them back out of a page from out/: t34_undo.json holds each changed block of
# lines in out/ beside origin/main's (61adbc7), each taken out wherever it stands (Studio's Now line stands twice). The
# T-34 block proves it: each page of out/ through un34(), themed by theme.py, is origin/main's root page byte for byte. Every older
# check that read a page through un33() now reads it through un33(un34()), and un30() calls un34() first. Idempotent.
T34_H1, T34_H1_OLD = 'AI, made easy.', 'AI, made easy'
T34_LINE = "Hey, I'm Josef. Take a deep breath. AI is a set of power tools, and I know how to run them. Hand me the job that never gets done, and I'll take it from here."
T34_LINE_OLD = "Hey, I'm Josef. Take a deep breath. AI is a set of power tools, and I already know how to run them. Tell me the job that never gets done, and I'll take it from here."
T34_UNDO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't34_undo.json'), encoding='utf-8'))


def un34(s, name=None):
    if name not in T34_UNDO:
        return s
    if '\r\n' in s:
        return un34(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    for new, old in T34_UNDO[name]:
        s = s.replace(new, old)
    return s


def un30(s, name=None):
    """studio.html or local.html as T-29 built it: the six paragraphs back, T-30's CSS rule out. Idempotent.
    T-33: any page goes through un33() first. T-34: and through un34() before that."""
    import re as _r
    s = un33(un34(s, name), name)
    if name not in (None, 'studio.html', 'local.html'):
        return s
    if '\r\n' in s:
        return un30(s.replace('\r\n', '\n'), name).replace('\n', '\r\n')
    if name in (None, 'studio.html'):
        s = s.replace(T30_CSS, '', 1)
        for pid, para in T30_STUDIO:
            s = _r.sub(r'(\n    <article class="prod[^"]*" data-id="' + pid + r'">\n        <h2>[^<]*</h2>\n        <div class="meta">[^\n]*?</div>)'
                       r'(?!\n        ' + _r.escape(para) + ')', lambda m: m.group(1) + '\n        ' + para, s, count=1)
    if name in (None, 'local.html'):
        for href, inner in T30_LOCAL + T30_LOCAL_LIVE:
            s = _r.sub(r'(<h3 style="[^"]*">[^<]*</h3>)(\n        ' + _r.escape(T30_LINK.format(href)) + ')',
                       lambda m: m.group(1) + '\n        ' + T30_LOCAL_P + inner + '</p>' + m.group(2), s, count=1)
    return s


T30_WHAT29 = {pid: t30_text(para) for pid, para in T30_STUDIO}   # kids' and COBOL's "what" in studio.json as at T-29


def what29(p):
    """A studio.json product's "what" as at T-29: T-30 set kids' and COBOL's to null (their words live on work.html)."""
    return T30_WHAT29[p['id']] if p.get('what') is None and p.get('id') in T30_WHAT29 else p.get('what')


# The snapshot's six, in its order (T-27, chucklefits-shelf-2026-11-18.json): (handle, name, kind, price as shown).
T27_SHELF = [
    ('thats-coo-womens-baby-tee', "That's Coo", 'Baby tee', 'From $28'),
    ('i-hold-a-grudge-womens-t-shirt', 'I Hold A Grudge', "Women's tee", 'From $28'),
    ('bird-watchin-buddies-unisex-classic-tee', 'Bird Watchin Buddies', 'Tee', 'From $26'),
    ('easy-tiger-unisex-classic-tee', 'Easy Tiger', 'Tee', 'From $26'),
    ('as-far-as-i-know-im-delightful', "As Far As I Know, I'm Delightful", 'Tee', 'From $26'),
    ('love-your-mother-5-panel-cap', 'Love Your Mother', 'Cap', 'From $26'),
]


# The item's words, as given (T-26): (app, [(group label, group caption, numbered, [(file, caption, alt)])]).
T26_HEADING = 'Inside the apps'
T26_APPS = [
    ('Deepcuts', [
        ('Then', None, False, [
            ('deepcuts-then-spreadsheet.jpg', 'A spreadsheet', 'Deepcuts as a spreadsheet: indie games ranked by match score, each with its developer.')]),
        ('Now', 'November 2026', False, [
            ('deepcuts-now-dig.jpg', None, "Today's Dig in the Deepcuts app: one game picked for you, with its fit score and why it was picked."),
            ('deepcuts-now-keeps.jpg', None, 'Your Keeps: the games you saved, each with Started, Finished and Bounced buttons.'),
            ('deepcuts-now-rooms.jpg', None, 'The Rooms screen: rooms for games, gifts, records and books, each marked open.'),
            ('deepcuts-now-taste.jpg', None, 'A taste profile, The Grand Strategist, with sliders from Depth to Breadth and Solo to Social.')])]),
    ('Bird League', [
        ('Then', None, False, [
            ('birdleague-then-sketch.jpg', 'A Figma sketch', 'A photo of the first Bird League sketch in Figma: a green header, a gray map box and four tabs.'),
            ('birdleague-then-firstbuild.jpg', 'The first build', 'An early Bird League screen that names birds by sound and still says mock data.')]),
        ('Now', 'November 2026', False, [
            ('birdleague-now-home.jpg', None, "Bird League's home screen: a countdown to the Winter Big Day, the trophy case and recent sightings."),
            ('birdleague-now-log.jpg', None, "The Log screen: type a bird's name or identify it by sound or photo, then log it to your leagues or your life list."),
            ('birdleague-now-leagues.jpg', None, "A league card: this week's matchup, your rank, your points and the days left in the season."),
            ('birdleague-now-wall.jpg', None, "The life list wall: birds grouped by family, with the ones you've seen in color."),
            ('birdleague-now-lifelist.jpg', None, "The life list: 141 species, and how many of the birds reported near home you've seen."),
            ('birdleague-now-records.jpg', None, 'Life list records: the heaviest, lightest and widest-winged birds seen, and a size parade.'),
            ('birdleague-now-profile.jpg', None, 'A player profile: lifetime points, species, sightings, leagues and the next goals.'),
            ('birdleague-now-badges.jpg', None, 'The badge case: earned badges in color and locked ones in gray.')])]),
    ('Birdsighted', [
        ('One case, start to finish', None, True, [
            ('birdsighted-1-cases.jpg', 'Pick a case', "Birdsighted's case files: twelve cases, two marked solved, plus a training case and an eye test."),
            ('birdsighted-2-read.jpg', 'Read the clues', 'Case 01, Creek at First Light: a question about jays diving at one pine, with two answers to choose from.'),
            ('birdsighted-3-results.jpg', 'See what you missed', "The case's results: rings on the scene mark each clue found or missed, a lookalike, the hidden bird and a secret."),
            ('birdsighted-4-lesson.jpg', 'Learn why', "A clue's lesson: whitewash on a cliff ledge, and what it says about the birds that perch there."),
            ('birdsighted-5-rank.jpg', 'Earn your rank', 'The marks earned on a case and the field rank they add up to.')])]),
]


# T-31: with no FONT_DIR (Windows, or any machine without it), the Google Fonts are recorded once and replayed. The first
# request for each address is fetched live and saved, keyed by its full URL, in dj-test-fonts in the system temp folder
# (outside the repository); every later request, in this run and every later one, is served from there with the same
# body, content type and CORS headers. With FONT_DIR present (Linux), fonts come from it, as before.
FONT_CACHE = os.path.join(tempfile.gettempdir(), 'dj-test-fonts')
FONT_KEEP = ('content-type', 'access-control-allow-origin', 'timing-allow-origin', 'cross-origin-resource-policy', 'cache-control')


def font_status():
    if FONT_FILES:
        return f'fonts: FONT_DIR ({len(FONT_FILES)} files)'
    n = len(glob.glob(os.path.join(FONT_CACHE, '*.json')))
    return f'fonts: cache ({n} files)' if n else 'fonts: recording'


def cached_font(route):
    u = route.request.url
    key = os.path.join(FONT_CACHE, hashlib.sha256(u.encode('utf-8')).hexdigest())
    try:
        meta = json.load(open(key + '.json', encoding='utf-8'))
        body = open(key + '.bin', 'rb').read()
    except (OSError, ValueError):
        try:
            r = route.fetch(timeout=60000)
            body = r.body()
        except Exception as e:
            print(f'fonts: could not record {u}: {e}', file=sys.stderr)
            return route.abort()
        meta = {'url': u, 'status': r.status, 'headers': {k: v for k, v in r.headers.items() if k.lower() in FONT_KEEP}}
        if r.status == 200:   # saved whole or not at all: the body first, then the record that points to it
            os.makedirs(FONT_CACHE, exist_ok=True)
            for ext, data, mode in (('.bin', body, 'wb'), ('.json', json.dumps(meta, indent=1), 'w')):
                tmp = f'{key}{ext}.{os.getpid()}.tmp'
                with open(tmp, mode, **({} if mode == 'wb' else {'encoding': 'utf-8'})) as f:
                    f.write(data)
                os.replace(tmp, key + ext)
    return route.fulfill(status=meta['status'], headers=meta['headers'], body=body)


def route_fonts(page):
    if not FONT_FILES:   # T-31: no FONT_DIR here, so record and replay
        page.route('**/fonts.googleapis.com/**', cached_font)
        page.route('**/fonts.gstatic.com/**', cached_font)
        return

    def gf(route):
        u = route.request.url
        if 'fonts.googleapis.com' in u:
            return route.fulfill(status=200, content_type='text/css', body=FONT_CSS)
        name = os.path.basename(u.split('?')[0])
        if name in FONT_FILES:
            return route.fulfill(status=200, content_type='font/woff2', body=open(FONT_FILES[name], 'rb').read())
        return route.abort()
    page.route('**/fonts.googleapis.com/**', gf)
    page.route('**/fonts.gstatic.com/**', gf)
    page.route('**/__fonts/**', gf)


# ================================================================ helpers the sections share
# T-31 (Nov 19, 2026): each "# ----------------" section below is a function, so it can run on its own or in a
# worker of its own (_build/run_tests.py). What a later section reads from an earlier one lives here, above them all,
# moved from where it was with its body unchanged. Values a section built while it ran and a later one read are
# built here on first use and kept (studio_log(), sample(), thin18()), so a section run alone builds them itself.

b = None        # the browser, launched by the runner at the bottom of this file
errors = []     # page errors, from every page newpage() opens

# T-29: BASE + '__un29/<file>' serves this build with un29() applied, so studio.html there is T-27's page byte for
# byte (the stamp line aside); the older checks that read studio.html's layout as it was at T-27 open UN29.
UN29 = BASE + '__un29/'

def serve29(route):
    path = route.request.url.split('/__un29/', 1)[1].split('?')[0].split('#')[0]
    body = urlopen(BASE + path).read()
    if path.endswith('.html'):
        body = un29(body.decode('utf-8').replace('\r\n', '\n'), path).encode('utf-8')
    route.fulfill(status=200, body=body, content_type='text/html; charset=utf-8' if path.endswith('.html') else
                  'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')

# T-30: BASE + '__un30/<file>' serves this build with un30() applied, so studio.html and local.html there are T-29's
# pages (the stamp line aside); the older checks that read those pages' text or layout as at T-29 open UN30.
UN30 = BASE + '__un30/'

def serve30(route):
    path = route.request.url.split('/__un30/', 1)[1].split('?')[0].split('#')[0]
    body = urlopen(BASE + path).read()
    if path.endswith('.html'):
        body = un30(body.decode('utf-8').replace('\r\n', '\n'), path).encode('utf-8')
    route.fulfill(status=200, body=body, content_type='text/html; charset=utf-8' if path.endswith('.html') else
                  'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')

# T-33: BASE + '__un33/<file>' serves this build with un33() alone applied (T-33's lines out, T-30's change kept), for the
# T-30 checks that compare the T-30 page with T-29's in the browser.
UN33 = BASE + '__un33/'

def serve33(route):
    path = route.request.url.split('/__un33/', 1)[1].split('?')[0].split('#')[0]
    body = urlopen(BASE + path).read()
    if path.endswith('.html'):
        body = un33(un34(body.decode('utf-8').replace('\r\n', '\n'), path), path).encode('utf-8')   # T-34: its changes out too
    route.fulfill(status=200, body=body, content_type='text/html; charset=utf-8' if path.endswith('.html') else
                  'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')

def newpage(w, h=900):
    pg = b.new_page(viewport={'width': w, 'height': h})
    route_fonts(pg)
    pg.route('**/__un29/**', serve29)
    pg.route('**/__un30/**', serve30)
    pg.route('**/__un33/**', serve33)
    pg.on('pageerror', lambda e: errors.append(str(e)))
    return pg

# The imports the sections share (each was at the top of the section that first needed it).
import json as _json
import re as _re, struct as _struct
from urllib.request import urlopen
import json as _json, html as _html
import shutil as _shutil, subprocess as _sp, tempfile as _tmp
import datetime as _dt
from urllib.parse import unquote as _unquote
import subprocess as _sp18
import json as _json26

# start, briefing, drop-in: the intake Worker, mocked (T-10 and T-29 post to it too).
posts = []
def mock_ok(route):
    if route.request.method == 'POST':
        posts.append(_json.loads(route.request.post_data or '{}'))
    return route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
def mock_fail(route):
    return route.fulfill(status=502, content_type='application/json', body='{"ok":false}', headers={'Access-Control-Allow-Origin': '*'})

# T-20 F2: the checkup card and links show only once CHECKUP_URL is set in tools/checkup.py.
CK_LIVE = "\nvar CHECKUP_URL = '';" not in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'checkup.py'), encoding='utf-8').read()

SHARED = ('index', 'local', 'mainframe', 'work', 'comp3', 'shotlist', 'captions', 'receipt',
          'scaler', 'start', 'call', 'case-reels', 'briefing', 'studio', 'checkup')
# Plus a page per open Studio product with a join list (T-09).
SHARED += tuple('studio-' + x['id'] for x in _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'studio.json'), encoding='utf-8'))['products']
                if x.get('gate') is None and x.get('list'))
# T-16: every header except the three Mainframe pages, which carry neither Studio nor Free tools.
MAINFRAME_PAGES = ('mainframe', 'briefing', 'comp3')

def ld_blocks(src):
    return _re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, _re.S)

def page_text(src):
    # The page's words with the tags stripped: scripts and styles out first, so the block can't vouch for itself.
    src = _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S)
    return _re.sub(r'\s+', ' ', _html.unescape(_re.sub(r'<[^>]+>', ' ', src)))

ALL_HTML = [n + '.html' for n in SHARED] + ['404.html']
here = os.path.dirname(os.path.abspath(__file__))

STUDIO_J = _json.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
SHIPPED_J = _json.load(open(os.path.join(here, 'shipped.json'), encoding='utf-8'))
open_p = [x for x in STUDIO_J['products'] if x.get('gate') is None]

def short(d, today):
    s = d.strftime('%b') + ' ' + str(d.day)
    return s if d.year == today.year else f'{s}, {d.year}'

_LOG08 = []


def studio_log():
    """T-08: the day studio.html was built, the gated products' ids and the log lines that should show. T-08's
    section and T-09's read them; built once, on first use, from the page and shipped.json as T-08's section did."""
    if not _LOG08:
        gated_p = [x for x in STUDIO_J['products'] if x.get('gate') is not None]
        src = urlopen(BASE + 'studio.html').read().decode('utf-8')
        built = _re.search(r'id="stats" data-built="(\d{4}-\d\d-\d\d)"', src)
        today = _dt.date.fromisoformat(built.group(1)) if built else _dt.date.today()
        # The log lines that should show: not from a gated product, not older than 120 days, newest first.
        hide = {x['id'] for x in gated_p}
        rows = [e for e in SHIPPED_J['entries'] if e['project'] not in hide
                and _dt.date.fromisoformat(e['date']) >= today - _dt.timedelta(days=120)]
        rows.sort(key=lambda e: e['date'], reverse=True)
        _LOG08.extend([today, hide, rows])
    return _LOG08

sys.path.insert(0, os.path.join(here, 'tools'))
import studio as _studio

page_p = [x for x in open_p if x.get('list')]
wk = open(os.path.join(here, 'worker', 'intake.js'), encoding='utf-8').read()
# Catch the fallback mailto instead of letting the browser open a mail app.
CATCH_MAILTO = ("window.__mailto = []; document.addEventListener('click', function (e) {"
                " var a = e.target.closest && e.target.closest('a[href^=\"mailto:\"]');"
                " if (a && a.hidden) { window.__mailto.push(a.getAttribute('href')); e.preventDefault(); } }, true);")

def mock_abort(route):
    return route.abort()

_SAMPLE = []


def sample():
    """The checkup Worker's sample answer (test_checkup.mjs --sample). The checkup section, T-18 and T-19 read it; built once."""
    if not _SAMPLE:
        SAMPLE = _json.loads(_sp.run(['node', 'test_checkup.mjs', '--sample'], cwd=os.path.join(here, 'worker'), capture_output=True, text=True).stdout)
        _SAMPLE.append(SAMPLE)
    return _SAMPLE[0]

def settle(q):
    q.wait_for_load_state('networkidle'); q.evaluate('document.fonts.ready.then(() => 1)'); q.wait_for_timeout(100)
U = lambda s: _html.unescape(s)
def click_chips(q, picks):
    for k, v in picks:
        q.evaluate(f"document.querySelector('.chip[data-k=\"{k}\"][data-v=\"{v}\"]').click()")
def set_val(q, sel, v):
    q.evaluate("([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})) }", [sel, v])
def grab_copy(q, btn):
    q.evaluate('window.djCopy = t => { window.__copied = t }')
    q.evaluate(f"document.querySelector('{btn}').click()")
    return q.evaluate('window.__copied')

SHOT_JS = '''(() => ({
  edit: [...document.querySelectorAll('#edit .clip')].map(c => [c.querySelector('.no').textContent, c.querySelector('.role').className, c.querySelector('.sec').textContent, c.querySelector('p').textContent, (c.querySelector('.cap') || {}).textContent || '']),
  shoot: [...document.querySelectorAll('#shoot .spot')].map(s => [s.querySelector('h3').textContent, [...s.querySelectorAll('li')].map(l => l.textContent)]),
  strip: [...document.querySelectorAll('#strip span')].map(s => [s.className, s.style.flex, s.textContent]), striplabel: document.getElementById('striplabel').textContent,
  rules: [...document.querySelectorAll('#rules li')].map(l => l.textContent),
  days: document.getElementById('days').textContent, dayslabel: document.getElementById('dayslabel').textContent, when: document.getElementById('when').hidden,
  pressed: [...document.querySelectorAll('.chip[aria-pressed=true]')].map(c => c.dataset.k + '=' + c.dataset.v)}))()'''

CAP_JS = '''(() => { const d = document.getElementById('cv').toDataURL(); let h = 0; for (let i = 0; i < d.length; i++) h = (h * 31 + d.charCodeAt(i)) | 0;
  return {verdicts: [...document.querySelectorAll('#verdicts li')].map(l => [l.querySelector('.dot').className, l.textContent]),
          cards: [...document.querySelectorAll('#cards .cardline')].map(c => c.textContent), canvas: h,
          pressed: [...document.querySelectorAll('.chip[aria-pressed=true]')].map(c => c.dataset.k + '=' + c.dataset.v)} })()'''
CAP_IN = ((None, [], '5'), ('New fall sweaters just landed.', [('size', 'l'), ('pos', 'top'), ('app', 'tiktok')], '2'),
          ('Supercalifragilisticexpialidocious bakery opens at nine tomorrow morning on Fourth Street', [('size', 's'), ('box', 'none'), ('app', 'shorts'), ('pos', 'mid')], '20'))

def rec_in(presets, rate, edit):
    def rec(q):
        for i in presets:
            q.evaluate(f"document.querySelector('[data-p=\"{i}\"]').click()")
        if rate:
            set_val(q, '#rate', rate)
        if edit:
            set_val(q, '[data-f=min]', '60'); set_val(q, '[data-f=per]', 'week')
            q.evaluate("document.getElementById('addown').click()"); q.wait_for_timeout(60)
            set_val(q, 'input[data-f=name]', 'Renamed chore')
            q.evaluate("document.querySelector('[data-del=\"1\"]').click()")
        q.wait_for_timeout(100)
        paper = q.evaluate("(() => { const c = document.getElementById('paper').cloneNode(true); c.querySelectorAll('.ed, .fold').forEach(e => e.remove()); return c.textContent.replace(/\\s+/g, ' ').trim() })()")
        paper = paper.replace('You could get back', 'BACK').replace('COULD COME BACK', 'BACK')
        return {'paper': paper, 'bring': q.get_attribute('#bring', 'href'),
                'copy': grab_copy(q, '#copy').replace('You could get back:', 'BACK:').replace('Could come back:', 'BACK:'),
                'chips': q.evaluate("[...document.querySelectorAll('#presets .chip')].map(c => [c.textContent, c.className, c.getAttribute('aria-disabled')])")}
    return rec

_THIN18 = []


def thin18():
    """T-18's thin page: the sample answer with 120 characters of text. T-18 and T-19 read it; built once."""
    if not _THIN18:
        SAMPLE = sample()
        thin = _json.loads(_json.dumps(SAMPLE)); thin['facts']['textLength'] = 120
        _THIN18.append(thin)
    return _THIN18[0]

def worker_(a_):
    return lambda route: route.fulfill(status=200 if a_.get('ok') else 400, content_type='application/json',
                                       body=_json.dumps(a_), headers={'Access-Control-Allow-Origin': '*'})

def fill_start(q):
    q.locator('.chips[data-key="pile"] .chip').nth(1).click()
    q.locator('.chips[data-key="days"] .chip').first.click()
    q.fill('#org', 'Test Bakery'); q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com')
def fill_call(q):
    q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com'); q.fill('#org', 'Test Bakery')
def fill_brief(q):
    q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com'); q.fill('#family', 'Month-end batch'); q.fill('#role', 'Lead')

sys.path.insert(0, os.path.join(here, 'tools'))
import chrome as _chrome20
ck_src = open(os.path.join(here, 'tools', 'checkup.py'), encoding='utf-8').read()

def fill_start20(q):
    fill_start(q)
    for t in ('Mornings', 'Friday'):
        q.locator('.chips[data-key="days"] .chip', has_text=t).click()

# T-26: the page text readers leave the gallery section out (on older builds it isn't there); the T-26 block checks its words.
# T-27: and the ChuckleFits shelf (.shelf), likewise; the T-27 block checks its words.
TEXT_JS = '''(() => { const c = document.body.cloneNode(true); c.querySelectorAll('script, style, section[aria-labelledby="gallery-h"], .shelf').forEach(e => e.remove());
  return c.textContent.replace(/[\\s\\u00a0]+/g, ' ').trim() })()'''

K5_ROWS = [('Editing each reel, before', 'An evening'), ('Engine time each reel', '~4 min'), ('Reels in the series', '40'),
           ('Her notes it now checks on every reel', '3 of 3'), ('Posted without her yes', '0')]
stamp25 = lambda s: _re.sub(r'<!-- studio\.py \d{4}-\d\d-\d\d [0-9a-f]+ -->', '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))
STAMP26 = r'<!-- studio\.py \d{4}-\d\d-\d\d [0-9a-f]+ -->'
rb26 = lambda f: open(os.path.join(here, '..', f), 'rb').read().replace(b'\r\n', b'\n')   # a Windows checkout may hold CRLF
outd = os.path.join(here, 'out')
stamp27 = lambda s: _re.sub(STAMP26, '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); n = s.getsockname()[1]; s.close()
    return n


TEMP_PORT = free_port()   # T-31: T-21's temp server (once always on 8767) gets a free port in each process, so workers don't collide

# T-32 (Nov 20, 2026): theme.py (step 6c) writes the themed copy of out/ to out-themed/, and the root is copied from
# there. The older checks that compared the root with out/ compare it with out-themed/ through t32_root_off().
T32_DIR = os.path.join(here, 'out-themed')


def t32_read(d, n):
    return open(os.path.join(d, n), encoding='utf-8', newline='').read().replace('\r\n', '\n')


def t32_root_off(names):
    """The pages whose root copy is not the themed build's."""
    return [n for n in names if t32_read(os.path.join(here, '..'), n) != t32_read(T32_DIR, n)]



# ---------------- decoder
@section('decoder')
def s_decoder():
    pg = newpage(1440)
    pg.goto(BASE + 'comp3.html'); pg.wait_for_timeout(300)
    out = lambda: pg.inner_text('#out')
    check('decoder default value 3.50000', '3.50000' in out(), out()[:200])
    check('decoder default fraction reading $291.67', '$291.67' in out())
    check('decoder default percentage reading $2.92', '$2.92' in out())
    pg.click('text=Exhibit A, stored as 0.035'); pg.wait_for_timeout(100)   # T-24 A6: was "Exhibit A, as the bank stored it"
    check('bank-stored value 0.03500', '0.03500' in out(), out()[:200])
    check('bank-stored fraction reading $2.92', '$2.92' in out())
    pg.click('text=A negative balance'); pg.wait_for_timeout(100)
    check('negative balance -12345.67', '-12345.67' in out(), out()[:200])
    check('no rate block for a balance', 'ANNUAL RATE' not in out().upper())
    pg.click('text=A damaged field'); pg.wait_for_timeout(100)
    check('damaged field warns S0C7', 'S0C7' in out(), out()[:300])
    pg.fill('#in', '0350000C'); pg.fill('#pic', 'PIC S9(2)V9(5) COMP-3.'); pg.wait_for_timeout(100)
    check('full PIC clause parsed', '3.50000' in out(), out()[:200])
    pg.fill('#pic', '9(5)'); pg.fill('#in', '12345F'); pg.wait_for_timeout(100)
    check('unsigned 9(5) value 12345 clean', '12345' in out() and 'Clean field' in out(), out()[:300])
    pg.fill('#in', '01 23 4C'); pg.fill('#pic', 'S9(6)'); pg.wait_for_timeout(100)
    check('length mismatch flagged', 'packs into 3 bytes' in out() or 'You pasted' in out(), out()[:300])
    pg.click('#mode-enc'); pg.wait_for_timeout(100)
    pg.fill('#pic', 'S9(7)V99'); pg.fill('#in', '-12345.67'); pg.wait_for_timeout(100)
    check('encode -12345.67 -> 00 12 34 56 7D', '00 12 34 56 7D' in out(), out()[:200])
    pg.fill('#pic', 'S9(2)V9(5)'); pg.fill('#in', '0.035'); pg.wait_for_timeout(100)
    check('encode 0.035 -> 00 03 50 0C', '00 03 50 0C' in out(), out()[:200])
    pg.fill('#in', '123.5'); pg.wait_for_timeout(100)
    check('encode overflow warns', 'Too many digits' in out(), out()[:200])
    # shared link
    pg2 = newpage(1440)
    pg2.goto(BASE + 'comp3.html#m=dec&v=00%2003%2050%200C&p=S9(2)V9(5)'); pg2.wait_for_timeout(300)
    check('shared link restores field', '0.03500' in pg2.inner_text('#out'))
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'comp3.html'); q.wait_for_timeout(400)
        check(f'decoder no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/comp3-{w}.png', full_page=True)


# ---------------- local page
@section('local-page')
def s_local_page():
    pg = newpage(1440)
    pg.goto(BASE + 'local.html'); pg.wait_for_timeout(500)
    btns = pg.locator('#rc-rows .src-btn')
    check('reels receipt has 5 source buttons', btns.count() == 5, str(btns.count()))
    btns.nth(0).click(); pg.wait_for_timeout(100)
    check('first source note opens', pg.locator('#src-reels-0').is_visible())
    check('reels foot text', 'stay private' in pg.inner_text('#rc-src-foot'))
    pg.click('button[data-tab="app"]'); pg.wait_for_timeout(150)
    check('app receipt decorated after tab switch', pg.locator('#rc-rows .src-btn').count() == 6, str(pg.locator('#rc-rows .src-btn').count()))
    check('app foot text', 'share my screen' in pg.inner_text('#rc-src-foot'))
    pg.click('button[data-tab="method"]'); pg.wait_for_timeout(150)
    check('method receipt has 4 source buttons', pg.locator('#rc-rows .src-btn').count() == 4)
    check('method link visible', pg.locator('#rc-link').is_visible())
    pg.click('button[data-tab="reels"]'); pg.wait_for_timeout(150)
    check('back to reels, 5 buttons', pg.locator('#rc-rows .src-btn').count() == 5)


    check('intake hidden before pick', not pg.locator('#intake').is_visible())
    pg.click('button[data-pick="reels"]'); pg.wait_for_timeout(100)
    check('intake shown after pick', pg.locator('#intake').is_visible())
    check('send disabled until answered', pg.locator('#iq-send').is_disabled())
    pg.click('button.iq[data-q="q1"]:has-text("A nonprofit")')
    pg.click('button.iq[data-q="q2"]:has-text("I do")')
    check('send still disabled with 2 of 3', pg.locator('#iq-send').is_disabled())
    pg.click('button.iq[data-q="q3"]:has-text("This month")')
    check('send enabled with 3 of 3', not pg.locator('#iq-send').is_disabled())
    pg2 = newpage(1440)
    pg2.goto(BASE + 'local.html'); pg2.wait_for_timeout(400)
    pg2.click('button[data-pick="app"]')
    for q, txt in (('q1', 'A small business'), ('q2', 'A board or committee'), ('q3', 'Just looking for now')):
        pg2.click(f'button.iq[data-q="{q}"]:has-text("{txt}")')
    pg2.fill('#iq-name', 'Test Kitchen')
    pg2.click('#iq-send'); pg2.wait_for_timeout(600)
    # T-12: start.html reads its # and then clears it, so the typed business name isn't left in the address.
    check('quiz hands off to start page, # cleared after load', pg2.url.endswith('/start.html'), pg2.url)
    check('start page preselects pile', pg2.locator('.chips[data-key="pile"] .chip[aria-pressed="true"]').inner_text() == "Know-how stuck in binders, docs or one person's head")   # T-33 R5: the same choice's new words
    check('start page preselects run/yes/when', pg2.locator('.chip[aria-pressed="true"]').count() == 4, str(pg2.locator('.chip[aria-pressed="true"]').count()))
    check('start page carries org name', pg2.input_value('#org') == 'Test Kitchen')

    check('drop-in section present', pg.locator('#dropin').count() == 1)
    check('no bracket placeholders visible', '[' not in pg.inner_text('body').replace('[n]', '').replace('[MONTH]', ''), '')
    for w in (390, 768, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(500)
        q.click('button[data-pick="flow"]'); q.wait_for_timeout(100)
        check(f'local no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.locator('#proof').screenshot(path=f'{SHOTS}/proof-{w}.png')
        q.locator('section[aria-labelledby="start"]').screenshot(path=f'{SHOTS}/start-{w}.png')
        q.locator('#dropin').screenshot(path=f'{SHOTS}/dropin-{w}.png')
        q.locator('#josef').screenshot(path=f'{SHOTS}/josef-{w}.png')


# ---------------- start, briefing, drop-in (endpoint mocked)
@section('start-briefing-dropin')
def s_start_briefing_dropin():

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'local.html'); pg.wait_for_timeout(300)
    check('all Blueprint buttons go to start.html', pg.locator('a[href="start.html"]').count() == 3, str(pg.locator('a[href="start.html"]').count()))
    check('no gmail anywhere on local', 'stephens.josef@gmail.com' not in pg.content())
    pg.fill('#dl-email', 'list@example.com'); pg.wait_for_timeout(2700); pg.click('#dl-send'); pg.wait_for_timeout(400)
    check('drop-in posts form=dropin', posts and posts[-1].get('form') == 'dropin' and posts[-1]['fields']['email'] == 'list@example.com', str(posts[-1:]))
    check('drop-in confirms', "on the list" in pg.inner_text('#dl-msg'))

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'start.html'); pg.wait_for_timeout(300)
    check('start success panel hidden on load', not pg.locator('#bp-done').is_visible())
    pg.click('#bp-send'); pg.wait_for_timeout(200)
    check('start validates empty form', pg.locator('#bp-err').is_visible() and 'step 1' in pg.inner_text('#bp-err'))
    pg.click('.chips[data-key="pile"] .chip >> nth=0')
    pg.click('.chips[data-key="days"] .chip >> nth=1'); pg.click('.chips[data-key="days"] .chip >> nth=3')
    pg.fill('#name', 'Pat Test'); pg.fill('#email', 'pat@example.com'); pg.fill('#never', 'We film and never post.')
    n0 = len(posts)
    pg.click('#bp-send'); pg.wait_for_timeout(500)
    check('start posts form=blueprint', len(posts) == n0 + 1 and posts[-1]['form'] == 'blueprint', str(posts[-1:]))
    check('start sends multi-select days', posts[-1]['fields'].get('days') == 'Tuesday, Thursday', str(posts[-1]['fields']))
    check('start shows success', pg.locator('#bp-done').is_visible() and not pg.locator('#bp').is_visible())

    pg = newpage(390); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_fail)
    pg.goto(BASE + 'start.html'); pg.wait_for_timeout(300)
    pg.click('.chips[data-key="pile"] .chip >> nth=2'); pg.fill('#name', 'Pat'); pg.fill('#email', 'pat@example.com')
    pg.click('#bp-send'); pg.wait_for_timeout(500)
    check('start failure keeps form and offers email', pg.locator('#bp').is_visible() and pg.locator('#bp-err a[href^="mailto:hello@dragomansjourney.com"]').count() == 1)
    check('start no overflow at 390', pg.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
    pg.screenshot(path=f'{SHOTS}/start-390.png', full_page=True)
    q = newpage(1440); q.goto(BASE + 'start.html'); q.wait_for_timeout(400); q.screenshot(path=f'{SHOTS}/start-1440.png', full_page=True)

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'briefing.html#ask=survey'); pg.wait_for_timeout(300)
    check('briefing success panel hidden on load', not pg.locator('#br-done').is_visible())
    check('briefing preselects survey', pg.locator('.chips[data-key="ask"] .chip[aria-pressed="true"]').inner_text() == 'A quote for the Survey')
    pg.fill('#name', 'Dana Test'); pg.fill('#email', 'dana@bank.example'); pg.fill('#org', 'Example Credit Union')
    pg.click('.chips[data-key="stage"] .chip >> nth=2')
    n0 = len(posts)
    pg.click('#br-send'); pg.wait_for_timeout(500)
    check('briefing posts form=briefing', len(posts) == n0 + 1 and posts[-1]['form'] == 'briefing' and posts[-1]['fields'].get('ask') == 'A quote for the Survey', str(posts[-1:]))
    check('briefing shows success', pg.locator('#br-done').is_visible())
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'briefing.html'); q.wait_for_timeout(400)
        check(f'briefing no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/briefing-{w}.png', full_page=True)


# ---------------- work, case study, free call
@section('work-case-study')
def s_work_case_study():
    pg = newpage(1440)
    pg.goto(BASE + 'work.html'); pg.wait_for_timeout(300)
    check('work has 10 cards (T-04 adds the Website checkup; 9 while it isn\'t live, T-20 F2)', pg.locator('#cards .card').count() == (10 if CK_LIVE else 9))
    # T-33 R11: the Banking tab is now Mainframe (the same two cards); the Nonprofits tab is now Apps (the kids' app,
    # Bird League and Birdsighted); R21: the recipe scaler card is off the free tools.
    pg.click('.filt[data-f="mainframe"]'); pg.wait_for_timeout(100)
    check('mainframe filter shows 2 (T-33 R11, was banking)', pg.locator('#cards .card:visible').count() == 2, str(pg.locator('#cards .card:visible').count()))
    pg.click('.filt[data-f="apps"]'); pg.wait_for_timeout(100)
    check('apps filter shows 3 (T-33 R11, was nonprofit: two jobs + the recipe scaler)', pg.locator('#cards .card:visible').count() == 3)
    pg.click('.filt[data-f="free"]'); pg.wait_for_timeout(100)
    check('free tools filter shows 5 (4 while the checkup isn\'t live, T-20 F2; T-33 R21: no recipe scaler)', pg.locator('#cards .card:visible').count() == (5 if CK_LIVE else 4))
    q = newpage(1440); q.goto(BASE + 'work.html#free'); q.wait_for_timeout(300)
    check('work.html#free opens on free tools', q.locator('#cards .card:visible').count() == (5 if CK_LIVE else 4))
    check('no CLIENT_ token left on work', 'CLIENT_' not in pg.content())
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'work.html'); q.wait_for_timeout(400)
        check(f'work no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/work-{w}.png', full_page=True)
        q = newpage(w); q.goto(BASE + 'case-reels.html'); q.wait_for_timeout(400)
        check(f'case no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        # T-22 K1 to K3: the sentences that named "a Sonoma County children's nonprofit" are off case-reels; the page now says "the program's creator".
        check(f'case client filled at {w}', 'CLIENT_' not in q.content() and "the program's creator" in q.inner_text('header'))
        q.screenshot(path=f'{SHOTS}/case-{w}.png', full_page=True)

    calls = []
    def mock_old_worker(route):
        body = _json.loads(route.request.post_data or '{}'); calls.append(body)
        if body.get('form') == 'call':
            return route.fulfill(status=400, content_type='application/json', body='{"ok":false,"error":"form"}', headers={'Access-Control-Allow-Origin': '*'})
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_old_worker)
    pg.goto(BASE + 'call.html'); pg.wait_for_timeout(300)
    check('call success hidden on load', not pg.locator('#cl-done').is_visible())
    pg.click('.chips[data-key="topic"] .chip >> nth=0'); pg.click('.chips[data-key="days"] .chip >> nth=5')
    pg.fill('#name', 'Sam Test'); pg.fill('#email', 'sam@example.com'); pg.fill('#note', 'Hi')
    pg.wait_for_timeout(2600); pg.click('#cl-send'); pg.wait_for_timeout(700)
    check('call tries call form first', calls and calls[0]['form'] == 'call', str(calls[:1]))
    check('call falls back to labeled blueprint', len(calls) == 2 and calls[1]['form'] == 'blueprint' and 'CALL REQUEST' in calls[1]['fields'].get('heard', ''), str(calls))
    check('call shows success', pg.locator('#cl-done').is_visible())
    calls.clear()
    pg = newpage(390); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'call.html'); pg.wait_for_timeout(300)
    pg.fill('#name', 'Sam'); pg.fill('#email', 'sam@example.com'); pg.click('#cl-send'); pg.wait_for_timeout(500)
    check('call posts natively when worker knows it', posts and posts[-1]['form'] == 'call', str(posts[-1:]))
    check('call no overflow at 390', pg.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
    pg.screenshot(path=f'{SHOTS}/call-390.png', full_page=True)

    pg = newpage(1440); pg.goto(BASE + 'index.html'); pg.wait_for_timeout(300)
    check('front door links work + call', pg.locator('a[href="work.html"]').count() >= 1 and pg.locator('a[href="call.html"]').count() >= 1)
    pg = newpage(1440); pg.goto(BASE + 'local.html'); pg.wait_for_timeout(300)
    check('local links work + call', pg.locator('a[href="work.html"]').count() >= 2 and pg.locator('#contact a[href="call.html"]').count() == 1)
    check('local results link, no slogan (intent L17)', pg.locator('#proof a[href="work.html"]').count() == 1 and "If I can't show it" not in pg.inner_text('#proof'))


# ---------------- mainframe
@section('mainframe')
def s_mainframe():
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); q.wait_for_timeout(500)
        check(f'mainframe no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'mainframe decoder links at {w}', q.locator('a[href="comp3.html"]').count() == 2)
        check(f'mainframe no placeholders at {w}', '[' not in q.inner_text('#s7'))
        q.locator('#s7').screenshot(path=f'{SHOTS}/mf-s7-{w}.png')


# ---------------- free tools (Nov 8, 2026)
@section('free-tools')
def s_free_tools():
    for w in (390, 1440):
        for t in ('shotlist', 'captions', 'receipt', 'scaler', 'checkup'):
            q = newpage(w); q.goto(BASE + t + '.html'); q.wait_for_timeout(500)
            check(f'{t} no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.screenshot(path=f'{SHOTS}/{t}-{w}.png', full_page=True)
    q = newpage(1440); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    check('shot list has 10 clips', q.locator('#edit .clip').count() == 10)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 30', abs(secs - 30) < 0.01, str(secs))
    q.click('#f-details'); q.click('#f-cut')   # T-18: "How long?" and the edit sit under two folds now
    q.click('.chip[data-v="15"]'); q.wait_for_timeout(100)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 15', abs(secs - 15) < 0.01, str(secs))
    check('shoot order covers all 10 clips', q.locator('#shoot li').count() == 10)
    q = newpage(1440); q.goto(BASE + 'captions.html'); q.wait_for_timeout(400)
    check('captions split into screens', q.locator('#cards .cardline').count() >= 2)
    q.fill('#cap', 'New fall sweaters just landed.'); q.wait_for_timeout(300)
    check('short caption is one screen', q.locator('#cards .cardline').count() == 1)
    q = newpage(1440); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    check('receipt starts with 3 lines', q.locator('#rows .row2').count() == 3)   # T-18: the lines sit on the receipt
    check('receipt default total $9,750', '$9,750' in q.inner_text('#paper'), q.inner_text('#paper')[:300])
    q.click('[data-p="11"]'); q.wait_for_timeout(100)
    check('keep-human chore adds nothing to come back', '$6,225' in q.inner_text('#paper'))
    href = q.get_attribute('#bring', 'href')
    check('receipt hands off to start with never=', href.startswith('start.html#pile=') and '&never=' in href, href[:80])
    q.goto(BASE + href); q.wait_for_timeout(300)
    check('start form takes the receipt', 'busywork receipt' in q.input_value('#never'))
    check('start clears the receipt text from the address after load', q.url.endswith('/start.html') and '#' not in q.url, q.url[:120])
    check('start keeps the receipt pick after clearing the address',
          q.locator('.chips[data-key="pile"] .chip[aria-pressed="true"]').count() == 1)
    q = newpage(1440); q.goto(BASE + 'scaler.html'); q.wait_for_timeout(300)
    out = q.inner_text('#out')
    check('scaler default x3', q.inner_text('#fac').strip() == '\u00d73', q.inner_text('#fac'))
    check('scaler 1/2 cup milk x3 = 1 1/2 cups', '1 1/2 cups' in out, out[:300])
    check('scaler 1 1/2 tbsp x3 = 4 1/2 tbsp', '4 1/2 tbsp' in out, out[:300])
    q.fill('#kids', '40'); q.wait_for_timeout(100)
    check('scaler warns about batches past x3', 'batches' in q.inner_text('#warn'))


# ---------------- share cards (T-01, Nov 9, 2026)
@section('share-cards')
def s_share_cards():
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        imgs = _re.findall(r'<meta property="og:image" content="([^"]*)">', src)
        check(f'{name} has exactly one og:image', len(imgs) == 1, str(imgs))
        if len(imgs) != 1:
            continue
        check(f'{name} og:image is its own absolute card', imgs[0] == f'https://dragomansjourney.com/og/{name}.png', imgs[0])
        check(f'{name} card size tags and large twitter card',
              '<meta property="og:image:width" content="1200">' in src and '<meta property="og:image:height" content="630">' in src
              and src.count('<meta name="twitter:card" content="summary_large_image">') == 1)
        try:
            png = urlopen(BASE + 'og/' + imgs[0].rsplit('/', 1)[1]).read()
            size = _struct.unpack('>II', png[16:24]) if png[:8] == b'\x89PNG\r\n\x1a\n' else None
        except Exception as e:
            size = str(e)
        check(f'{name} card file exists in out/og at 1200x630', size == (1200, 630), str(size))
    check('404 page carries no share card', 'og:image' not in urlopen(BASE + '404.html').read().decode('utf-8'))


# ---------------- free tools, findable (T-02, Nov 10, 2026)
@section('free-tools-findable')
def s_free_tools_findable():
    TOOLS = {'shotlist.html': 'Reel shot list', 'captions.html': 'Caption fitter',
             'receipt.html': 'Busywork receipt', 'scaler.html': 'Recipe scaler', 'checkup.html': 'Website checkup'}
    LINKED = {k: v for k, v in TOOLS.items() if k != 'checkup.html' or CK_LIVE}   # T-20 F2
    LINKED33 = {k: v for k, v in LINKED.items() if k != 'scaler.html'}   # T-33 R21: the recipe scaler is off the lists (local.html is read below as at T-29)
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        # The header nav: <nav> where the page has one, else its <header>, else the home page's letterhead bar.
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="work\.html#free"[^>]*>([^<]*)</a>', top)
        if name in MAINFRAME_PAGES:
            check(f'{name} header has no Free tools link (T-16)', bool(top) and links == [] and 'Free tools' not in top, str(links))
            continue
        check(f'{name} nav links Free tools to work.html#free', links == ['Free tools'], str(links))
        if 'Free 15-min call' in top:
            check(f'{name} Free tools sits before the free call', -1 < top.find('work.html#free') < top.index('Free 15-min call'))
    q = newpage(1440); q.goto(BASE + 'work.html#free'); q.wait_for_timeout(300)
    check('work.html#free opens on the free tools', q.get_attribute('.filt[data-f="free"]', 'aria-pressed') == 'true'
          and q.locator('#cards .card:visible').count() == q.locator('#cards .card[data-k~="free"]').count())
    src = un30(urlopen(BASE + 'local.html').read().decode('utf-8'), 'local.html')   # T-30: the four descriptions back (they live on work.html now; the T-30 block checks it)
    sec = _re.search(r'<section id="tools".*?</section>', src, _re.S)
    sec = sec.group(0) if sec else ''
    check('local free tools section sits right before contact', bool(sec) and bool(_re.search(_re.escape(sec) + r'\s*<section id="contact"', src)))
    check('local free tools heading', '>Free tools for your pile</h2>' in sec)
    check(f'local free tools section links the {len(LINKED)} tools (the checkup only once it is live, T-20 F2)', sorted(_re.findall(r'href="([a-z]+\.html)"', sec)) == sorted(LINKED), sec[:200])
    work = un21(urlopen(BASE + 'work.html').read().decode('utf-8'))   # T-21: compared without its line-breaking spans
    sec = un21(sec)
    for href, title in LINKED33.items():   # T-33 R21: the work page has no recipe scaler card
        para = _re.search(r'<h2>' + title + r'</h2>\s*<p>([^<]*)</p>\s*<a class="go" href="' + href, work)
        check(f'local card for {href} matches the work page', bool(para) and f'>{title}</h3>' in sec and f'>{para.group(1)}</p>' in sec)
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(300)
        xs = q.eval_on_selector_all('#tools article', 'e => e.map(a => Math.round(a.getBoundingClientRect().left))')
        check(f'local free tools: {"one column" if w == 390 else "one row of all " + str(len(LINKED33))} at {w}',   # T-33 R21
              len(xs) == len(LINKED33) and (len(set(xs)) == 1 if w == 390 else len(set(xs)) == len(LINKED33)), str(xs))
    for href in TOOLS:
        q = newpage(1440); q.goto(BASE + href); q.wait_for_timeout(300)
        line = q.locator('main > p', has_text='More free tools:')
        got = line.locator('a').evaluate_all('e => e.map(a => [a.getAttribute("href"), a.textContent])') if line.count() == 1 else []
        check(f'{href} links the other tools by name (the checkup only once it is live, T-20 F2)', sorted(got) == sorted([k, v] for k, v in LINKED33.items() if k != href), str(got))   # T-33 R21
        if line.count() == 1:
            check(f'{href} more-tools line sits above the dark panel',
                  line.bounding_box()['y'] < q.locator('#more-h').bounding_box()['y'])
        # T-16 N14: the dark panel keeps its own button and no longer has "More free tools".
        panel = q.locator('section[aria-labelledby="more-h"]')
        check(f'{href} dark panel: one button, its own, no "More free tools" (T-16)', panel.locator('a').count() == 1
              and panel.locator('a').get_attribute('href') == ('start.html' if href == 'receipt.html' else 'call.html')
              and 'More free tools' not in panel.inner_text(),
              str(panel.locator('a').all_inner_texts()))
        # T-16 N13: the line over the title is just "Free tool".
        check(f'{href} kicker reads "Free tool" (T-16)', q.locator('header .kick').count() == 1
              and q.locator('header .kick').text_content().strip() == 'Free tool', q.locator('header .kick').text_content())
    for name in SHARED:
        q = newpage(390); q.goto(BASE + name + '.html'); q.wait_for_timeout(300)
        sw = q.evaluate('document.documentElement.scrollWidth')
        check(f'{name} has no sideways scroll at 390', sw <= 390, str(sw))
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(150)
            q.screenshot(path=f'{SHOTS}/t02-{name}-{w}.png', full_page=True)


# ---------------- facts a machine can read (T-11, Nov 11, 2026)
@section('machine-facts')
def s_machine_facts():


    def walk(node):
        yield node
        for v in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()):
            yield from walk(v)

    def dollars(n):
        return '$' + f'{n:,}'

    LD = {}
    for name in ('local', 'mainframe'):
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        blocks = ld_blocks(src)
        check(f'{name} has exactly one ld+json block', len(blocks) == 1, str(len(blocks)))
        check(f'{name} ld+json sits just before </head>', _re.search(r'</script>\s*</head>', src) is not None
              and src.index('application/ld+json') < src.index('</head>'))
        try:
            data = _json.loads(blocks[0]) if blocks else None
        except ValueError as e:
            data = None
            check(f'{name} ld+json parses as JSON', False, str(e))
        else:
            check(f'{name} ld+json parses as JSON', data is not None)
        LD[name] = data
        if data is None:
            continue
        text = page_text(src)
        nodes = list(walk(data))
        prices = [n.get('price', n.get('minPrice')) for n in nodes if isinstance(n, dict) and n.get('@type') in ('Offer', 'PriceSpecification', 'UnitPriceSpecification')]
        prices = [p for p in prices if p is not None]
        check(f'{name} ld+json carries prices', len(prices) >= 3, str(prices))
        for pr in prices:
            check(f'{name} price {dollars(pr)} is in the page text', dollars(pr) in text)
        for n in nodes:
            if isinstance(n, dict) and n.get('unitText') == 'month':
                check(f'{name} monthly price {dollars(n["minPrice"])}/month is in the page text', dollars(n['minPrice']) + '/month' in text)
        for s in (n for n in nodes if isinstance(n, str)):
            for amt in _re.findall(r'\$[\d,]+', s):
                check(f'{name} amount {amt} in the block is in the page text', amt in text)
        for n in nodes:
            if isinstance(n, dict) and n.get('@type') == 'Offer':
                check(f'{name} offer "{n["name"]}" is named on the page', n['name'] in page_text(un21(src)))   # T-33 R8: "know-how" sits in a no-wrap span; read without them (un21)
                if 'description' in n:
                    check(f'{name} offer "{n["name"]}" description is word for word', n['description'] in text, n['description'])
                cur = [n.get('priceCurrency')] + [n['priceSpecification'].get('priceCurrency')] if 'priceSpecification' in n else [n.get('priceCurrency')]
                check(f'{name} offer "{n["name"]}" is in USD', set(cur) == {'USD'}, str(cur))
        check(f'{name} ld+json has no long dash', '—' not in blocks[0] and '–' not in blocks[0])
        flat = _json.dumps(data)
        for word in ('aggregateRating', 'review', 'openingHours', 'telephone', 'streetAddress', 'postalCode'):
            check(f'{name} ld+json has no {word}', f'"{word}' not in flat)
        desc = _re.search(r'<meta name="description" content="([^"]*)">', src).group(1)
        top = data['@graph'][0] if '@graph' in data else data
        check(f'{name} ld+json description is the meta description', top.get('description') == _html.unescape(desc))

    if LD.get('local'):
        src = urlopen(BASE + 'local.html').read().decode('utf-8')
        biz = next((n for n in LD['local'].get('@graph', []) if n.get('@type') == 'ProfessionalService'), {})
        faq = next((n for n in LD['local'].get('@graph', []) if n.get('@type') == 'FAQPage'), {})
        check('local business facts', biz.get('name') == "Dragoman's Journey" and biz.get('url') == 'https://dragomansjourney.com/local.html'
              and biz.get('email') == 'hello@dragomansjourney.com' and biz.get('founder') == {'@type': 'Person', 'name': 'Josef Stephens'}
              and biz.get('areaServed') == 'Sonoma County, California'
              and biz.get('address') == {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa', 'addressRegion': 'CA', 'addressCountry': 'US'}, str(biz)[:300])
        check('local email is on the page', 'hello@dragomansjourney.com' in src)
        index_ld = _json.loads(ld_blocks(urlopen(BASE + 'index.html').read().decode('utf-8'))[0])
        gh = [u for n in index_ld['@graph'] for u in n.get('sameAs', [])]
        check('local sameAs is the GitHub link index uses', biz.get('sameAs') == gh, str(biz.get('sameAs')))
        offers = biz.get('makesOffer', [])
        check('local has the Blueprint and the three cards as offers', [o.get('name') for o in offers][:1] == ['The Blueprint'] and len(offers) == 4
              and [o.get('name') for o in offers][1:] == [_html.unescape(_re.sub(r'<[^>]+>', '', h)) for h in
                                                         _re.findall(r'data-card="[^"]+".*?<h3[^>]*>(.*?)</h3>', src, _re.S)], str([o.get('name') for o in offers]))
        check('local Blueprint is a fixed $1,500 as the page says', offers and offers[0].get('price') == 1500 and '>The Blueprint · $1,500</h3>' in un21(src), str(offers[:1]))   # T-21 G2: the dot's spaces don't break
        qs = faq.get('mainEntity', [])
        nbtn = len(_re.findall(r'<button[^>]*data-faq="', src))
        check('local FAQ count equals the data-faq buttons', len(qs) == nbtn and nbtn > 0, f'{len(qs)} vs {nbtn}')
        text = page_text(src)
        check('local FAQ questions and answers are the page\'s own words',
              all(q['name'] in text and q['acceptedAnswer']['text'] in text for q in qs) and all('<' not in q['acceptedAnswer']['text'] for q in qs))
    if LD.get('mainframe'):
        svc = LD['mainframe']
        src = urlopen(BASE + 'mainframe.html').read().decode('utf-8')
        check('mainframe service facts', svc.get('@type') == 'Service' and svc.get('name') == 'The Mainframe Route'
              and svc.get('provider', {}).get('name') == "Dragoman's Journey"
              and svc.get('provider', {}).get('founder') == {'@type': 'Person', 'name': 'Josef Stephens'}, str(svc)[:300])
        steps = _re.search(r'id="s3-h".*?<ol.*?</ol>', src, _re.S).group(0)
        priced = [_re.sub(r'<[^>]+>', '', _re.search(r'<h3[^>]*>(.*?)</h3>', li, _re.S).group(1)) for li in _re.findall(r'<li.*?</li>', steps, _re.S)
                  if '$' in _re.findall(r'<p[^>]*>(.*?)</p>', li, _re.S)[-1]]
        check('mainframe has one offer per step that prints a price', [o.get('name') for o in svc.get('offers', [])] == priced, str(priced))
    idx = ld_blocks(urlopen(BASE + 'index.html').read().decode('utf-8'))
    check('index ld+json block is unchanged', len(idx) == 1 and _json.loads(idx[0]) == {
        '@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', 'name': "Dragoman's Journey", 'alternateName': "Dragoman's Journey · Josef Stephens", 'url': 'https://dragomansjourney.com/'},
            {'@type': 'Person', 'name': 'Josef Stephens', 'jobTitle': "Founder, Dragoman's Journey",
             'address': {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa', 'addressRegion': 'CA'},
             'sameAs': ['https://github.com/stephensjosef-cloud']}]})
    for name in ('local', 'mainframe'):
        for w in (390, 1440):
            q = newpage(w); q.goto(BASE + name + '.html'); q.wait_for_timeout(300)
            q.screenshot(path=f'{SHOTS}/t11-{name}-{w}.png')


# ---------------- visit counter (T-12, Nov 11, 2026)
@section('visit-counter')
def s_visit_counter():
    COUNTER_LINE = 'This site counts page visits with Cloudflare Web Analytics, which uses no cookies.'
    for name in ALL_HTML:
        src = urlopen(BASE + name).read().decode('utf-8')
        check(f'{name} has no beacon while the token is empty', 'cloudflareinsights' not in src)
        check(f'{name} has no counter sentence while the token is empty', COUNTER_LINE not in src)
    # A temp copy of the pipeline with a made-up token: build it all, then count.
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        fp = os.path.join(bd, 'final.py')
        fsrc = open(fp, encoding='utf-8').read()
        check('final.py starts with the token empty', fsrc.count('\nCF_BEACON_TOKEN = ""\n') == 1)
        open(fp, 'w', encoding='utf-8').write(fsrc.replace('\nCF_BEACON_TOKEN = ""\n', '\nCF_BEACON_TOKEN = "0123456789abcdef0123456789abcdef"\n', 1))
        steps = [['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'],
                 [sys.executable, 'enhance.py', 'out'], [sys.executable, 'plain.py', 'out'],
                 [sys.executable, 'intent.py', 'out'], [sys.executable, 'final.py', 'out']]
        built = True
        for st in steps:
            r = _sp.run(st, cwd=bd, capture_output=True, text=True)
            if r.returncode:
                built = False
                check('temp build with a made-up token runs', False, ' '.join(st[1:2]) + ': ' + (r.stdout + r.stderr)[-300:])
                break
        if built:
            out = os.path.join(bd, 'out')
            names = sorted(f for f in os.listdir(out) if f.endswith('.html'))
            check('temp build has every page', sorted(ALL_HTML) == names, str(names))
            for name in names:
                src = open(os.path.join(out, name), encoding='utf-8').read()
                n = src.count('https://static.cloudflareinsights.com/beacon.min.js')
                if name == 'comp3.html':
                    check('comp3.html gets no beacon with a token set', n == 0 and 'cloudflareinsights' not in src, str(n))
                else:
                    check(f'{name} has exactly one beacon with a token set', n == 1, str(n))
                    check(f'{name} beacon is the docs\' form, just before </body>',
                          _re.search(r'<script\n\ttype="module"\n\tsrc="https://static\.cloudflareinsights\.com/beacon\.min\.js"\n'
                                     r'\tdata-cf-beacon=\'\{"token": "0123456789abcdef0123456789abcdef"\}\'\n></script>\n</body>', src) is not None)
            loc = open(os.path.join(out, 'local.html'), encoding='utf-8').read()
            check('local.html has the counter sentence once on the page', page_text(loc).count(COUNTER_LINE) == 1)
            a = _re.search(r'<p id="faq-a-3"[^>]*>(.*?)</p>', loc, _re.S)
            check('counter sentence ends the "What do you do with our data?" answer',
                  'What do you do with our data?</span>' in loc and a is not None and a.group(1).endswith(' ' + COUNTER_LINE))
            ld = _json.loads(ld_blocks(loc)[0])
            faq = next(n for n in ld['@graph'] if n.get('@type') == 'FAQPage')['mainEntity']
            data_a = [x['acceptedAnswer']['text'] for x in faq if x['name'] == 'What do you do with our data?']
            check('FAQPage data carries the counter sentence too', len(data_a) == 1 and data_a[0].endswith(' ' + COUNTER_LINE), str(data_a)[:200])
            others = [n for n in names if n != 'local.html']
            check('no other page has the counter sentence', not any(COUNTER_LINE in open(os.path.join(out, n), encoding='utf-8').read() for n in others))
            check('the counter adds no long dash', '—' not in COUNTER_LINE and '–' not in COUNTER_LINE)
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)


# ---------------- the Studio page and the public build log (T-08, Nov 11, 2026)
@section('studio-log')
def s_studio_log():
    gated_p = [x for x in STUDIO_J['products'] if x.get('gate') is not None]
    label_of = dict({x['id']: x['name'] for x in open_p}, site='dragomansjourney.com')


    src = urlopen(BASE + 'studio.html').read().decode('utf-8')
    check('sitemap lists studio.html', 'https://dragomansjourney.com/studio.html' in urlopen(BASE + 'sitemap.xml').read().decode('utf-8'))
    check('studio has no long dash', '—' not in src and '–' not in src)
    built = _re.search(r'id="stats" data-built="(\d{4}-\d\d-\d\d)"', src)
    check('studio numbers strip says its build date', bool(built))
    today, hide, rows = studio_log()   # T-31: built once, by studio_log() above (T-09 reads them too)
    N = len(rows)
    oldest = min(_dt.date.fromisoformat(e['date']) for e in rows)

    q = newpage(1440); q.goto(UN29 + 'studio.html'); q.wait_for_timeout(400)   # T-29: the cards, as at T-27 (un29); the T-29 block checks the blocks
    stats =[s.strip() for s in q.locator('#stats p').all_inner_texts()]
    stats = [_re.sub(r'\s+', ' ', s) for s in stats]
    # T-16 N4: one count, still from the log; "in the last 30 days" and "projects" are gone.
    # T-19 W28: "shipped" became "finished".
    check('studio count matches shipped.json, and is the only one', stats == [f'{N} things finished since {short(oldest, today)}'], str(stats))
    check('studio count is one block, not a three-column box (T-16)', q.eval_on_selector('#stats', 'e => getComputedStyle(e).display') == 'block'
          and abs(q.locator('#stats p').bounding_box()['width'] - q.locator('#stats').bounding_box()['width']) <= 1)
    # T-16 N2: no line over the title.
    check('studio shows the h1 from studio.json and no kicker (T-16)', q.inner_text('h1').replace('\n', ' ').upper() == _re.sub(r'<br\s*/?>', ' ', STUDIO_J['hero']['h1']).upper()
          and q.locator('header .kick').count() == 0 and 'updated as things ship' not in src)
    check('studio title unchanged', '<title>The studio · Dragoman\'s Journey</title>' in src)
    # T-16 N3: the hero keeps only its first sentence; the meta description stays as it was, and
    # still names the album only while the album card shows (fix approved Nov 11, 2026).
    INTRO = "Everything I'm building right now, and the date each piece was finished."   # T-19 W27
    HIDDEN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools and shirts, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    SHOWN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools, shirts and an album, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    album_hidden = any(x['id'] == 'album' for x in gated_p)
    hero_p = q.locator('header p').last.inner_text().strip()
    check('studio hero is the intro\'s first sentence only (T-16)', hero_p == INTRO and 'Get on a list' not in q.inner_text('header'), hero_p)
    check('studio meta description unchanged, names the album only when its card shows',
          _html.unescape(_re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) == (HIDDEN_LEDE if album_hidden else SHOWN_LEDE))
    if album_hidden:
        check('studio says no "album" while the album is hidden', 'album' not in q.inner_text('body').lower() and 'album' not in src.split('<style>')[0].lower())
    # Both states, from studio.py in a temp copy: the album hidden, then shown.
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        os.makedirs(bd)
        _shutil.copytree(os.path.join(here, 'tools'), os.path.join(bd, 'tools'), ignore=_shutil.ignore_patterns('__pycache__'))
        _shutil.copy(os.path.join(here, 'shipped.json'), bd)
        _shutil.copytree(os.path.join(here, 'assets', 'gallery'), os.path.join(bd, 'assets', 'gallery'))   # T-26: studio.py reads the gallery's images
        _shutil.copytree(os.path.join(here, 'assets', 'shelf'), os.path.join(bd, 'assets', 'shelf'))   # T-27: studio.py reads the shelf's photos
        for state in ('hidden', 'shown'):
            sj = _json.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
            for x in sj['products']:
                if x['id'] == 'album':
                    x['gate'] = 'test gate' if state == 'hidden' else None
            _json.dump(sj, open(os.path.join(bd, 'studio.json'), 'w', encoding='utf-8'))
            r = _sp.run([sys.executable, 'studio.py', '..'], cwd=os.path.join(bd, 'tools'), capture_output=True, text=True)
            page_src = open(os.path.join(bd, 'studio.html'), encoding='utf-8').read() if r.returncode == 0 else ''
            hero_txt = _re.search(r'<p style="margin:0;max-width:56ch[^"]*">([^<]*)</p>', page_src)
            hero_txt = _html.unescape(hero_txt.group(1)) if hero_txt else ''
            meta = _re.search(r'<meta name="description" content="([^"]*)"', page_src)
            want_lede = HIDDEN_LEDE if state == 'hidden' else SHOWN_LEDE
            check(f'album {state}: hero is the first sentence only (T-16)', hero_txt == INTRO, (r.stderr or hero_txt)[-200:])
            check(f'album {state}: meta description reads as approved', bool(meta) and _html.unescape(meta.group(1)) == want_lede)
            check(f'album {state}: album card ' + ('absent' if state == 'hidden' else 'present'),
                  ('data-id="album"' in page_src) == (state == 'shown'))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)
    check('studio "Shipped lately" heading', q.locator('#log-h').inner_text().strip().lower() == 'shipped lately')
    lis = q.locator('#log li')
    check('studio log holds every line that should show', lis.count() == N, f'{lis.count()} vs {N}')
    check('studio log shows the 8 newest first', q.locator('#log li:visible').count() == min(8, N), str(q.locator('#log li:visible').count()))
    got = [[lis.nth(i).locator('time').get_attribute('datetime'), lis.nth(i).locator('time').inner_text(),
            lis.nth(i).locator('.proj').inner_text(), lis.nth(i).locator('.line').inner_text()] for i in range(lis.count())]
    want = [[e['date'], short(_dt.date.fromisoformat(e['date']), today), label_of[e['project']], e['line']] for e in rows]
    check('studio log lines, dates and labels match shipped.json, newest first', got == want, str(got[:2]))
    check('studio log leaves out gated products', not any(e['project'] in hide and e['line'] in src for e in SHIPPED_J['entries']))
    btn = q.locator('#log-all')
    check('studio "See all" names the count', btn.count() == 1 and btn.inner_text().strip() == f'See all {N}', btn.inner_text() if btn.count() else 'none')
    if btn.count():
        btn.click(); q.wait_for_timeout(150)
        check('studio "See all" reveals the rest in place', q.locator('#log li:visible').count() == N and not btn.is_visible() and q.url.endswith('studio.html'))
    arts = q.locator('#products article')
    check('studio renders every open product, in order', arts.evaluate_all('e => e.map(a => a.dataset.id)') == [x['id'] for x in open_p],
          str(arts.evaluate_all('e => e.map(a => a.dataset.id)')))
    for x in gated_p:
        check(f'studio leaves out gated product {x["id"]}', f'data-id="{x["id"]}"' not in src and x['name'] not in src and x['what'] not in src)
    for x in open_p:
        card = q.locator(f'#products article[data-id="{x["id"]}"]')
        txt = card.inner_text()
        check(f'studio card {x["id"]}: name, status and what from the JSON',
              card.locator('h2').inner_text().upper() == x['name'].upper() and card.locator('.pill').inner_text() == x['status']
              and what29(x) in txt)   # T-30: kids' and COBOL's "what" as at T-29 (null in studio.json now), as on the page through un29()/un30()
        # T-16 N6: the kind stays in the JSON but isn't printed on the card.
        check(f'studio card {x["id"]}: no kind label (T-16)', card.locator('.kind').count() == 0
              and x['kind'].upper() not in card.locator('.meta').inner_text().upper(), card.locator('.meta').inner_text())
        if x.get('proof'):
            check(f'studio card {x["id"]}: proof line in bold', card.locator('strong', has_text=x['proof']).count() == 1)
        if x.get('image'):
            check(f'studio card {x["id"]}: image', card.locator(f'img[src="{x["image"]}"]').get_attribute('alt') == x['image_alt'])
        if x.get('link'):
            lhref = x['link']['href'].rstrip('/') + '/?' + x['link_tag'] if x.get('link_tag') else x['link']['href']   # T-27: the shop link carries the shelf tag
            lk = card.locator(f'a[href="{lhref}"]')
            check(f'studio card {x["id"]}: link', lk.count() == 1 and lk.inner_text().startswith(x['link']['label']))
        if x.get('list'):
            # T-10: the join button sits in a small form; its mailto is the form's action and the fallback.
            jf = card.locator('form.jf[data-list]')
            href = jf.get_attribute('action') if jf.count() == 1 else ''
            check(f'studio card {x["id"]}: join box for list {x["list"]["id"]}, mailto "List: {x["name"]}" as its fallback',
                  jf.count() == 1 and jf.get_attribute('data-list') == x['list']['id'] and jf.locator('button').inner_text() == x['list']['button']
                  and href.startswith('mailto:hello@dragomansjourney.com?subject=')
                  and _unquote(href.split('subject=', 1)[1]) == 'List: ' + x['name'], href)
            check(f'studio card {x["id"]}: list count shows only at 10 or more',
                  ('people on the list' in txt) == (x['list'].get('count', 0) >= 10))
    # The count rule, on a made-up count either side of 10.
    p41 = dict(open_p[0], list=dict(open_p[0].get('list') or {'id': 'x', 'button': 'b'}, count=41))
    p9 = dict(p41, list=dict(p41['list'], count=9))
    check('a list of 41 says "41 people on the list"', '>41 people on the list<' in _studio.product_card(p41))
    check('a list of 9 shows no count', 'on the list' not in _studio.product_card(p9))
    for w in (390, 1440):
        q = newpage(w); q.goto(UN29 + 'studio.html'); q.wait_for_timeout(400)   # T-29: the grid as at T-27 (un29); the T-29 block checks the new one
        check(f'studio no overflow at {w}',q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        boxes = q.locator('#products article').evaluate_all('e => e.map(a => [a.dataset.id, Math.round(a.getBoundingClientRect().left), Math.round(a.getBoundingClientRect().width)])')
        grid_w = round(q.locator('#products').bounding_box()['width'])
        full = [b_[0] for b_ in boxes if abs(b_[2] - grid_w) <= 2]
        if w == 390:
            check('studio products in one column at 390', len({b_[1] for b_ in boxes}) == 1 and len(full) == len(boxes), str(boxes))
        else:
            check('studio products in two columns at 1440', len({b_[1] for b_ in boxes}) == 2, str(boxes))
            # T-21 G4: a card alone on the last row spans it too (today Chucklefits), so no row ends in an empty cell.
            check('Bird League spans the full width at 1440 (and, T-21 G4, a card alone on its row)', full == ['birdleague', 'chucklefits'], str(full))
        q.screenshot(path=f'{SHOTS}/t08-studio-{w}.png', full_page=True)

    # T-16 N1: the home page's "Shipped lately" strip is gone; the header's Studio link stays.
    src = urlopen(BASE + 'index.html').read().decode('utf-8')
    check('home has no "Shipped lately" strip (T-16)', 'id="shipped"' not in src and 'Shipped lately' not in src
          and "See everything I'm building" not in _html.unescape(src) and not any(e['line'] in _html.unescape(src) for e in SHIPPED_J['entries']))
    check('home hero runs straight into the two routes (T-16)', _re.search(r'</header>\s*<!-- the two routes -->', src) is not None)
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(300)
        check(f'home no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'home header keeps its Studio link at {w}', q.locator('a[href="studio.html"]').count() == 1)
        q.screenshot(path=f'{SHOTS}/t16-home-top-{w}.png')

    # Studio in every header, before Free tools, except the three Mainframe pages (T-16).
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="studio\.html"[^>]*>([^<]*)</a>', top)
        if name in MAINFRAME_PAGES:
            check(f'{name} header has no Studio link (T-16)', bool(top) and links == [] and '>Studio<' not in top, str(links))
            continue
        check(f'{name} nav links Studio', links == ['Studio'], str(links))
        check(f'{name} Studio sits before Free tools', -1 < top.find('href="studio.html"') < top.find('work.html#free'))

    # enhance.py refuses a studio.html that is older than its JSON.
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        with open(os.path.join(bd, 'shipped.json'), 'a', encoding='utf-8') as f:
            f.write('\n')
        r = None
        for st in ([['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'], [sys.executable, 'enhance.py', 'out']]):
            r = _sp.run(st, cwd=bd, capture_output=True, text=True)
            if r.returncode:
                break
        check('enhance.py stops when studio.html is older than shipped.json', r.returncode != 0 and 'studio.html is older' in r.stdout + r.stderr, (r.stdout + r.stderr)[-200:])
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)


# ---------------- a page per Studio product (T-09, Nov 11, 2026)
@section('studio-pages')
def s_studio_pages():
    today, _hide, rows = studio_log()   # T-31: as T-08 built them (built here when T-09 runs alone)
    check('one page per open product with a join list', [x['id'] for x in page_p] == ['birdleague', 'deepcuts'], str([x['id'] for x in page_p]))
    sitemap = urlopen(BASE + 'sitemap.xml').read().decode('utf-8')
    for x in STUDIO_J['products']:
        slug = f'studio-{x["id"]}.html'
        if x in page_p:
            continue
        try:
            urlopen(BASE + slug); served = True
        except Exception:
            served = False
        check(f'no page for {x["id"]} ({"gated" if x.get("gate") else "no join list"})', not served and slug not in sitemap)
    q = newpage(1440); q.goto(UN29 + 'studio.html'); q.wait_for_timeout(300)   # T-29: the cards' links, as at T-27 (un29); the T-29 block checks the blocks'
    for x in open_p:
        mv =q.locator(f'#products article[data-id="{x["id"]}"] a[data-page]')
        if x in page_p:
            check(f'studio card {x["id"]} links "More on {x["name"]} →" to its page (T-16)',
                  mv.count() == 1 and mv.inner_text().strip() == f'More on {x["name"]} →' and mv.get_attribute('href') == f'studio-{x["id"]}.html')
        else:
            check(f'studio card {x["id"]} has no page link', mv.count() == 0)
    for x in page_p:
        slug = f'studio-{x["id"]}.html'
        src = urlopen(BASE + slug).read().decode('utf-8')
        check(f'{slug} in the sitemap', f'https://dragomansjourney.com/{slug}' in sitemap)
        check(f'{slug} has no long dash', '—' not in src and '–' not in src)
        check(f'{slug} title and meta description from the JSON',
              f'<title>{_html.escape(x["name"], quote=False)} · Dragoman\'s Journey</title>' in src
              and _html.unescape(_re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) == x['what'])
        q = newpage(1440); q.goto(BASE + slug); q.wait_for_timeout(300)
        hd = q.locator('header')
        check(f'{slug}: the name big', q.locator('h1').count() == 1 and q.inner_text('h1').strip().upper() == x['name'].upper())
        check(f'{slug}: status pill under the name', hd.locator('.hero-pill').inner_text() == x['status']
              and hd.locator('.hero-pill').bounding_box()['y'] > q.locator('h1').bounding_box()['y'])
        check(f'{slug}: what, from the JSON', x['what'] in hd.inner_text())
        # T-16 N8: the line over the title is one link back, "← The Studio", and nothing else.
        check(f'{slug}: the line over the title is one link, "← The Studio", to studio.html (T-16)',
              hd.locator('.kick a').count() == 1 and hd.locator('.kick a').get_attribute('href') == 'studio.html'
              and hd.locator('.kick').text_content().strip() == '← The Studio' and hd.locator('.kick a').text_content() == '← The Studio',
              hd.locator('.kick').text_content())
        main_ = q.locator('main')
        if x.get('proof'):
            check(f'{slug}: proof line in bold', main_.locator('strong', has_text=x['proof']).count() == 1)
        else:
            check(f'{slug}: no proof line when the JSON has none', main_.locator('.proof').count() == 0)
        if x.get('image'):
            check(f'{slug}: image', main_.locator(f'img[src="{x["image"]}"]').get_attribute('alt') == x['image_alt'])
        else:
            check(f'{slug}: no image when the JSON has none', main_.locator('img').count() == 0)
        mine = [e for e in rows if e['project'] == x['id']]
        lis = q.locator('#log li')
        got = [[lis.nth(i).locator('time').get_attribute('datetime'), lis.nth(i).locator('time').inner_text(),
                lis.nth(i).locator('.line').inner_text()] for i in range(lis.count())]
        want = [[e['date'], short(_dt.date.fromisoformat(e['date']), today), e['line']] for e in mine]
        check(f'{slug}: log matches shipped.json for {x["id"]}, newest first, with dates', got == want and len(want) > 0, str(got[:2]))
        check(f'{slug}: every log line shows', q.locator('#log li:visible').count() == len(mine) and q.locator('#log-all').count() == 0)
        check(f'{slug}: "Shipped lately" heading', q.locator('#log-h').inner_text().strip().lower() == 'shipped lately')
        check(f'{slug}: no other project\'s lines', not any(e['line'] in src for e in SHIPPED_J['entries'] if e['project'] != x['id']))
        jf = q.locator('#join form.jf[data-list]')
        href = jf.get_attribute('action') if jf.count() == 1 else ''
        check(f'{slug}: one join box, mailto "List: {x["name"]}" as its fallback', q.locator('#join').count() == 1 and q.locator('form.jf').count() == 1
              and jf.get_attribute('data-list') == x['list']['id']
              and jf.locator('button').inner_text() == x['list']['button'] and href.startswith('mailto:hello@dragomansjourney.com?subject=')
              and _unquote(href.split('subject=', 1)[1]) == 'List: ' + x['name'], href)
        check(f'{slug}: the line under the join box', q.locator('#join p').inner_text().strip() == x['list']['line'])
        check(f'{slug}: join box comes last, after the log', q.locator('#join').bounding_box()['y'] > q.locator('#log').bounding_box()['y'])
        check(f'{slug}: list count shows only at 10 or more', ('people on the list' in q.inner_text('#join')) == (x['list'].get('count', 0) >= 10))
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            check(f'{slug}: no sideways scroll at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.screenshot(path=f'{SHOTS}/t09-{x["id"]}-{w}.png', full_page=True)
    # The page list follows the JSON: a product that loses its gate and has a list gets a page.
    sj = _json.loads(_json.dumps(STUDIO_J))
    for x in sj['products']:
        x['gate'] = None
    check('a product gets a page once its gate clears', [s for s, _ in _studio.product_pages(sj)] == ['studio-birdleague.html', 'studio-deepcuts.html', 'studio-album.html'])


# ---------------- real join lists (T-10, Nov 11, 2026)
@section('join-lists')
def s_join_lists():
    # The Worker, with no network: intake.js and intake.deployed.js agree, the list form works, the old forms don't change.
    r = _sp.run(['node', 'test_intake.mjs'], cwd=os.path.join(here, 'worker'), capture_output=True, text=True)
    check('worker: node test_intake.mjs passes', r.returncode == 0 and ' passed' in r.stdout, (r.stdout + r.stderr)[-400:])
    check('worker: the four lists, as the item names them', 'const LISTS = ["birdleague", "deepcuts", "album", "spots-feb"];' in wk)
    check('worker: every Studio join list is one the Worker takes',
          all(x['list']['id'] in ('birdleague', 'deepcuts', 'album', 'spots-feb') for x in STUDIO_J['products'] if x.get('list')))
    start_ep = _re.search(r"var ENDPOINT = '([^']+)'", open(os.path.join(here, 'start.html'), encoding='utf-8').read()).group(1)
    check('join boxes post to the same Worker as start.html', _studio.ENDPOINT == start_ep, _studio.ENDPOINT)

    join_pages = [('studio.html', x) for x in open_p if x.get('list')] + [(f'studio-{x["id"]}.html', x) for x in page_p]
    for slug, x in join_pages:
        box = (f'#products article[data-id="{x["id"]}"] ' if slug == 'studio.html' else '#join ') + 'form.jf'
        tag = f'{slug} ({x["id"]})' if slug == 'studio.html' else slug
        shoot = slug != 'studio.html' or x['id'] == 'deepcuts'
        # Success: the right fields go to the Worker, and the box says so.
        q = newpage(1440); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok); q.add_init_script(CATCH_MAILTO)
        q.goto((UN29 if slug == 'studio.html' else BASE) + slug); q.wait_for_timeout(300)   # T-29: studio's boxes in their cards, as at T-27 (un29); the T-29 block runs the same in the blocks
        f = q.locator(box)
        check(f'{tag}: email field is required, type email, labeled "Email"',
              f.locator('input[name="email"][type="email"][required]').count() == 1 and f.locator('label.jf-e span').inner_text().strip().lower() == 'email')
        check(f'{tag}: honeypot is there and off screen', f.locator('.hp input[name="website"]').count() == 1
              and f.locator('.hp').bounding_box()['x'] < -1000)
        n0 = len(posts)
        f.locator('button').click(); q.wait_for_timeout(300)
        check(f'{tag}: an empty email sends nothing', len(posts) == n0 and q.evaluate('window.__mailto.length') == 0)
        f.locator('input[name="email"]').fill('  fan@example.com '); q.wait_for_timeout(2700)
        f.locator('button').click(); q.wait_for_timeout(600)
        sent = posts[-1] if len(posts) == n0 + 1 else {}
        check(f'{tag}: posts form=list with the email and list {x["list"]["id"]}, honeypot and time',
              sent.get('form') == 'list' and sent.get('fields') == {'email': 'fan@example.com', 'list': x['list']['id']}
              and sent.get('website') == '' and sent.get('ms', 0) >= 2500, str(sent))
        check(f'{tag}: success says "You\'re on the list"', f.locator('.jf-ok').inner_text().strip() == "You're on the list"
              and f.locator('.jf-ok').get_attribute('role') == 'status')
        check(f'{tag}: success hides the field and the button', not f.locator('input[name="email"]').is_visible() and not f.locator('button').is_visible())
        check(f'{tag}: success opens no mailto', q.evaluate('window.__mailto.length') == 0)
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            check(f'{tag}: no sideways scroll after success at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            if shoot:
                f.scroll_into_view_if_needed(); q.screenshot(path=f'{SHOTS}/t10-{slug[:-5]}-ok-{w}.png')
        # Failure (the Worker says no, or can't be reached): the mailto opens, the box stays as it was.
        for how, mock in (('an error answer', mock_fail), ('no connection', mock_abort)):
            q = newpage(390); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock); q.add_init_script(CATCH_MAILTO)
            q.goto((UN29 if slug == 'studio.html' else BASE) + slug); q.wait_for_timeout(300)   # T-29: as above
            f = q.locator(box)
            f.locator('input[name="email"]').fill('fan@example.com'); q.wait_for_timeout(2700)
            f.locator('button').click(); q.wait_for_timeout(600)
            got = q.evaluate('window.__mailto')
            check(f'{tag}: on {how}, falls back to the mailto "List: {x["name"]}"', len(got) == 1 and got[0] == f.get_attribute('action')
                  and _unquote(got[0].split('subject=', 1)[1]) == 'List: ' + x['name'], str(got))
            check(f'{tag}: on {how}, the box stays ready to try again', f.locator('input[name="email"]').is_visible()
                  and f.locator('button').is_enabled() and f.locator('button').inner_text() == x['list']['button']
                  and f.locator('.jf-ok').inner_text().strip() == '')
            if how == 'an error answer' and shoot:
                f.scroll_into_view_if_needed(); q.screenshot(path=f'{SHOTS}/t10-{slug[:-5]}-fail-390.png')
    check('join boxes: no long dash in the join script', '—' not in _studio.JOIN_SCRIPT and '–' not in _studio.JOIN_SCRIPT)


# ---------------- website checkup (T-04, Nov 12, 2026)
@section('checkup')
def s_checkup():
    # The Worker, with no network: safety rules, link classifier, 8a to 8e, and local.html through 8b (step 12).
    import tempfile as _tf
    lp = os.path.join(_tf.mkdtemp(), 'local.html')
    open(lp, 'w', encoding='utf-8').write(urlopen(BASE + 'local.html').read().decode('utf-8'))
    r = _sp.run(['node', 'test_checkup.mjs', lp], cwd=os.path.join(here, 'worker'), capture_output=True, text=True)
    check('checkup worker: node test_checkup.mjs passes (with local.html from the build)', r.returncode == 0 and ' passed' in r.stdout, (r.stdout + r.stderr)[-600:])
    check('checkup worker: local.html ran through the 8b check', 'FAIL local.html' not in r.stdout and r.stdout.strip().split('/')[0] == r.stdout.strip().split('/')[1].split()[0])
    ck = open(os.path.join(here, 'worker', 'checkup.js'), encoding='utf-8').read()
    check('checkup worker: separate from intake (no email, no intake code)', 'cloudflare:email' not in ck and 'SEB' not in ck)
    check('checkup worker: CORS for the same origins as intake', _re.search(r'const ORIGINS = \[[^\]]*\];', ck).group(0) == _re.search(r'const ORIGINS = \[[^\]]*\];', wk).group(0))
    check('checkup worker: no long dash', '—' not in ck and '–' not in ck)
    SAMPLE = sample()   # T-31: built once, by sample() above (T-18 and T-19 read it too)

    src = urlopen(BASE + 'checkup.html').read().decode('utf-8')
    check('checkup: sitemap lists it once it is live, and not before (T-20 F2)', ('https://dragomansjourney.com/checkup.html' in urlopen(BASE + 'sitemap.xml').read().decode('utf-8')) == CK_LIVE)
    check('checkup: CHECKUP_URL is one empty constant at the top of the script', src.count("var CHECKUP_URL = '';") == 1
          and _re.search(r"<script>\s*function djToast[\s\S]*?\n\s*var CHECKUP_URL = '';", src) is not None)
    check('checkup: the line under the box', "This checks your public page the way a visitor's phone would. Nothing is stored." in src)
    check('checkup: no long dash', '—' not in src and '–' not in src)
    work = urlopen(BASE + 'work.html').read().decode('utf-8')
    card = _re.search(r'<article class="card" data-k="([^"]*)">((?:(?!</article>).)*href="checkup\.html"(?:(?!</article>).)*)</article>', work, _re.S)
    # T-16 N10: the card keeps its place but no longer carries the "25 links" figure.
    if CK_LIVE:
        check('checkup: a fifth tool card on the work page, data-k free, "Website checkup", no figure', bool(card) and card.group(1) == 'free'
              and 'class="num"' not in card.group(2) and '25 links' not in card.group(2) and '<h2>Website checkup</h2>' in card.group(2))
    else:
        check('checkup: no card on the work page while it isn\'t live (T-20 F2)', card is None)

    # Until the Worker is live: "Coming this week", no box, nothing sent.
    sent = []
    for w in (390, 1440):
        q = newpage(w); q.on('request', lambda rq: sent.append(rq.url) if 'checkup' in rq.url and not rq.url.startswith(BASE) else None)
        q.goto(BASE + 'checkup.html'); q.wait_for_timeout(400)
        check(f'checkup: says "Coming this week" at {w}', q.locator('#soon').is_visible() and q.inner_text('#soon').strip().upper() == 'COMING THIS WEEK')
        check(f'checkup: no box while CHECKUP_URL is empty at {w}', not q.locator('#ask').is_visible() and not q.locator('#site').is_visible() and not q.locator('#go').is_visible())
        check(f'checkup: no report cards before a check at {w}', not q.locator('#rep1').is_visible() and not q.locator('#rep2').is_visible() and not q.locator('#stat').is_visible())
        check(f'checkup: no sideways scroll, coming soon, at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/t04-soon-{w}.png', full_page=True)
    check('checkup: nothing sent while it says coming this week', not sent, str(sent))

    # With a Worker address set (in the browser only, the file is untouched) and the Worker answering the sample.
    def live_page(w, answer):
        q = newpage(w, 1000)
        calls = []
        def page_route(route):
            body = route.fetch().text().replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1)
            route.fulfill(status=200, content_type='text/html', body=body)
        def worker(route):
            calls.append(route.request.url)
            route.fulfill(status=200 if answer.get('ok') else 400, content_type='application/json', body=_json.dumps(answer), headers={'Access-Control-Allow-Origin': '*'})
        q.route(BASE + 'checkup.html', page_route)
        q.route('https://dj-checkup.test/**', worker)
        q.goto(BASE + 'checkup.html'); q.wait_for_timeout(400)
        return q, calls
    q, calls = live_page(1440, SAMPLE)
    check('checkup live: the box shows, coming soon hides', q.locator('#site').is_visible() and q.inner_text('#go') == 'Check it' and not q.locator('#soon').is_visible())
    check('checkup live: nothing sent before the button', calls == [])
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: one GET with the address', len(calls) == 1 and calls[0] == 'https://dj-checkup.test/?url=crumb.example', str(calls))
    heads = q.locator('#finds1 .find h3').all_inner_texts()
    levels = q.eval_on_selector_all('#finds1 .find', 'e => e.map(x => x.classList.contains("bad") ? 0 : x.classList.contains("warn") ? 1 : 2)')
    check('checkup live: the worst finding first', heads[:1] == ['Your "Book Now" button leads to an error page'], str(heads))
    check('checkup live: worst to mildest, all the way down', levels == sorted(levels), str(levels))
    first = q.locator('#finds1 .find').first.inner_text()
    check('checkup live: a finding says what it costs and how hard it is to fix', "People who tap it can't book." in first and 'A five-minute fix in your site builder' in first, first)
    check('checkup live: the "#" Donate button goes nowhere', 'Your "Donate" button goes nowhere' in heads)
    check('checkup live: no phone layout, no tap-to-call, no description, http not sent on', all(h in heads for h in (
        "Your page isn't set up for phones", "Your phone number can't be tapped to call", 'Your page has no description',
        "The plain http address doesn't send people on to https")), str(heads))
    check('checkup live: what works is listed', '1 button works: "Order online".' in q.inner_text('#oks1'), q.inner_text('#oks1'))
    rep1 = q.locator('#rep1')
    check('checkup live: ends with "Want me to fix it?" to call.html', rep1.locator('a').last.get_attribute('href') == 'call.html'
          and rep1.locator('a').last.inner_text().startswith('Want me to fix it?')
          and q.evaluate("document.querySelector('#rep1').lastElementChild.getAttribute('href')") == 'call.html')
    st = q.locator('#stat')
    check('checkup live: the BrightLocal line sits above the second card, with its year and source', st.is_visible()
          and '45%' in st.inner_text() and '2026' in st.inner_text() and 'BrightLocal' in st.inner_text()
          and st.locator('a').get_attribute('href') == 'https://www.brightlocal.com/research/local-consumer-review-survey/'
          and st.bounding_box()['y'] < q.locator('#rep2').bounding_box()['y'] and q.locator('#rep1').bounding_box()['y'] < st.bounding_box()['y'])
    check('checkup live: second card heading', q.inner_text('#rep2-h') == 'Can AI find you?')
    check('checkup live: its first line, exactly', q.locator('#rep2 > p').first.inner_text() ==
          "This doesn't tell you what ChatGPT says about you. It checks whether a computer can find the basic facts about your business on your page.")   # T-19 W22
    heads2 = q.locator('#finds2 .find h3').all_inner_texts()
    levels2 = q.eval_on_selector_all('#finds2 .find', 'e => e.map(x => x.classList.contains("bad") ? 0 : x.classList.contains("warn") ? 1 : 2)')
    check('checkup live: blocking a search crawler turns AI readers away, worst first', heads2[:1] == ['Your site turns AI readers away']
          and 'OAI-SearchBot' in q.locator('#finds2 .find').first.inner_text() and levels2 == sorted(levels2), str(heads2))
    check('checkup live: blocking only training is a choice, in one plain line',
          'Your robots.txt keeps GPTBot from collecting your pages for AI training. That\'s a choice, not a fault.' in heads2
          and not any('GPTBot' in h for h in heads2[:1]), str(heads2))
    check('checkup live: two phone numbers are flagged', 'Your page gives two different phone numbers' in heads2)
    check('checkup live: hours not found, said as "I couldn\'t find"', "I couldn't find your opening hours in your page text" in heads2)
    check('checkup live: never says "missing"', 'missing' not in q.inner_text('#rep2').lower() and 'missing' not in q.inner_text('#rep1').lower())
    facts = dict(zip(q.locator('#facts dt').all_text_contents(), q.locator('#facts dd').all_text_contents()))
    check('checkup live: the facts card, as found', q.inner_text('#rep2 .facts h3') == 'What a computer can read off your page'   # T-19 W23
          and list(facts) == ['Name', 'Phone', 'Address', 'Hours'] and facts['Name'] == 'Crumb Bakery' and facts['Phone'] == '(707) 555-0134'
          and facts['Address'] == '12 Main St, Santa Rosa, CA' and facts['Hours'] == "I couldn't find it", str(facts))
    check('checkup live: the facts card ends with the profile line', q.locator('#rep2 .facts p').last.inner_text() ==
          "Compare these with your Google listing. They should match exactly. I can't see your listing from here.")   # T-19 W24
    for w in (390, 1440):
        q.set_viewport_size({'width': w, 'height': 1000}); q.wait_for_timeout(200)
        check(f'checkup live: no sideways scroll with both reports at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.evaluate('scrollTo(0, 0)'); q.wait_for_timeout(100)
        q.screenshot(path=f'{SHOTS}/t04-report-{w}.png', full_page=True)
    # 8d's exact sentence, on a page with almost no readable text.
    thin = _json.loads(_json.dumps(SAMPLE)); thin['facts']['textLength'] = 120
    q, calls = live_page(390, thin)
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: almost no readable text, in the item\'s words', "Your page holds almost no text a machine can read without running scripts or reading images." in q.locator('#finds2 .find h3').all_inner_texts())
    thin['cut'] = True
    q, calls = live_page(390, thin)
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: no text warning when the page was cut at 1.5 MB', not any('almost no text' in h for h in q.locator('#finds2 .find h3').all_inner_texts()))
    # A refused address: a plain answer, no report.
    q, calls = live_page(390, {'ok': False, 'error': 'private-name'})
    q.fill('#site', 'printer.local'); q.click('#go'); q.wait_for_timeout(600)
    check('checkup live: a refused address gets a plain answer and no report', 'inside a home or office network' in q.inner_text('#msg')
          and not q.locator('#rep1').is_visible() and q.inner_text('#go') == 'Check it')
    q.screenshot(path=f'{SHOTS}/t04-refused-390.png', full_page=True)


# ---------------- intent pass 2 (T-16, Nov 12, 2026)
@section('intent-pass-2')
def s_intent_pass_2():
    def text_of(src):
        return _html.unescape(_re.sub(r'<[^>]+>', ' ', _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S)))
    T16_PAGES = ('index', 'studio', 'studio-birdleague', 'studio-deepcuts', 'work', 'shotlist', 'captions', 'receipt',
                 'scaler', 'checkup', 'local', 'mainframe', 'briefing', 'comp3')
    site = {n: urlopen(BASE + n + '.html').read().decode('utf-8') for n in SHARED + ('index',)}

    # N5: four log lines gone everywhere, one shortened, the stranger rule written down.
    GONE = ["Bird League build 50 runs on Apple's newest tools.", 'Deepcuts build 4 works end to end on iPhone.',
            "Build 2 of the kids' cooking app, checked screen by screen on a real phone.",
            "Every word on dragomansjourney.com rechecked: if it isn't there for a reader, it's gone.",
            'Deepcuts got its new look, built and walked through on iPhone.']
    check('N5: the removed log lines are on no page', not any(g in text_of(s) for g in GONE for s in site.values()))
    check('N5: shipped.json no longer holds them', not any(g == e['line'] for g in GONE for e in SHIPPED_J['entries']) and len(SHIPPED_J['entries']) == 12)   # T-22 K9 removed two lines
    check('N5: the Deepcuts line reads "Deepcuts got its new look."', any(e['line'] == 'Deepcuts got its new look.' and e['date'] == '2026-11-04' for e in SHIPPED_J['entries'])
          and 'Deepcuts got its new look.' in text_of(site['studio']) and 'Deepcuts got its new look.' in text_of(site['studio-deepcuts']))
    RULE = 'A line stays only if a stranger can picture what changed: no build number without what a person can now do.'
    check('N5: the stranger rule ends shipped.json\'s _about and is in the README\'s "To log a ship" line',
          SHIPPED_J['_about'].endswith(RULE) and any(l.startswith('   To log a ship:') and RULE in l for l in open(os.path.join(here, 'README.md'), encoding='utf-8')))
    # N9: each product page's log is the JSON's, already checked above; and none of the removed lines.
    for slug in ('studio-birdleague', 'studio-deepcuts'):
        check(f'N9: {slug} log follows shipped.json, without the removed lines', not any(g in text_of(site[slug]) for g in GONE))

    # N10 to N12: the work page.
    q = newpage(1440); q.goto(BASE + 'work.html'); q.wait_for_timeout(400)
    figs = dict(q.locator('#cards .card').evaluate_all('e => e.map(c => [c.querySelector("h2").textContent, c.querySelector(".num") ? c.querySelector(".num").textContent : null])'))
    # T-19 W4 to W6: the three figures now say what they count.
    # T-22 K6 and K8: the reels card's title and headline, and the app card's headline, are Josef's new lines.
    KEEP = {'A 40-reel series on one engine.': 'An evening of editing, now about 4 minutes.', 'A seasonal cooking app for teachers': 'Their recipe cards, now an app.',
            'A banking program, checked in public': '2 AI translations of one bank program'}
    check('N10: only the three cards with a real result keep their figure', {k: v for k, v in figs.items() if v} == KEEP and len(figs) == (10 if CK_LIVE else 9), str(figs))   # T-20 F2
    for gone in ('0 → real users', 'Free</p>', '10 clips', '0 stranded words', '1 year, rung up', '×3, measurable', '25 links'):
        check(f'N10: figure "{gone.replace("</p>", "")}" is gone', f'<p class="num">{gone}' not in site['work'])

    def lined_up(pg, label):
        # Cards in one row share their top and height, and their links sit on one line.
        cards = pg.locator('#cards .card:visible:not(.feature)').evaluate_all(
            'e => e.map(c => { const r = c.getBoundingClientRect(), g = c.querySelector("a.go").getBoundingClientRect();'
            ' return [Math.round(r.top), Math.round(r.height), Math.round(g.bottom - r.top), !!c.querySelector(".num")]; })'
            .replace('c.querySelector("a.go")', '[...c.querySelectorAll("a.go")].pop()'))   # T-33 R21: the kids' app card's last link lines up
        rows_ = {}
        for c in cards:
            rows_.setdefault(c[0], []).append(c)
        mixed = [r for r in rows_.values() if len({c[3] for c in r}) == 2]
        ok_ = all(len({c[1] for c in r}) == 1 and max(c[2] for c in r) - min(c[2] for c in r) <= 1 for r in rows_.values())
        check(f'N10: cards line up, with and without a figure ({label})', ok_ and len(cards) > 0, str(rows_))
        return mixed
    lined_up(q, 'all cards at 1440')
    for f_ in ('apps', 'mainframe'):   # T-33 R11: the tabs that were nonprofit and banking
        q.click(f'.filt[data-f="{f_}"]'); q.wait_for_timeout(150)
        mixed = lined_up(q, f'{f_} filter at 1440')
        check(f'N10: the {f_} filter puts cards with and without a figure in one row', len(mixed) == 1, str(mixed))
        q.screenshot(path=f'{SHOTS}/t16-work-{f_}-1440.png', full_page=True)
    bl = q.locator('#cards .card.feature a.go')
    check('N11: the Bird League card links "See Bird League →" to studio-birdleague.html', bl.count() == 1 and bl.inner_text().strip() == 'See Bird League →'
          and bl.get_attribute('href') == 'studio-birdleague.html')
    check('N11: "More about how I work" is gone', 'More about how I work' not in site['work'])
    check('N12: the cooking app card says "iPhone, iPad, Android and the web."', 'iPhone, iPad, Android and the web.</p>' in site['work']
          and 'iPhone, iPad and Android.</p>' not in site['work'])

    # N15: the scaler intro.
    # T-18 S25 replaced the intro; it still leaves "Kids count as half a portion." out.
    check('N15: the scaler intro drops "Kids count as half a portion."', 'Kids count as half a portion.' not in site['scaler']
          and "Paste a recipe and say who's eating. You get amounts you can actually measure." in _html.unescape(site['scaler']))
    check('N15: the line under the boxes still says it', 'A kid counts as half a portion.' in site['scaler'])

    # N16: the shot list countdown shows from 42 days out to the day itself, and not before.
    def shot_at(when, nonprofit=False):
        pg = newpage(390); pg.clock.set_fixed_time(when); pg.goto(BASE + 'shotlist.html'); pg.wait_for_timeout(300)
        if nonprofit:
            pg.click('.chip[data-k="type"][data-v="nonprofit"]'); pg.wait_for_timeout(100)
        return pg
    for when, np_, want in (('2026-10-17T12:00:00', False, '42 days'), ('2026-10-16T12:00:00', False, None),
                            ('2026-10-20T12:00:00', True, '42 days'), ('2026-10-19T12:00:00', True, None),
                            ('2026-11-28T09:00:00', False, 'Today'), ('2026-11-12T12:00:00', False, '16 days')):
        pg = shot_at(when, np_)
        who = 'Giving Tuesday' if np_ else 'Small Business Saturday'
        if want:
            check(f'N16: {when[:10]}, {who}: countdown shows "{want}"', pg.locator('#when').is_visible() and pg.inner_text('#days').strip() == want
                  and who in pg.inner_text('#dayslabel'), pg.inner_text('#days'))
        else:
            # T-18 S9: the countdown is its own box now, so with no countdown the whole box is gone.
            check(f'N16: {when[:10]}, {who}: 43 days out, no countdown and no empty box', not pg.locator('#when').is_visible()
                  and pg.locator('#when').bounding_box() is None and who not in pg.inner_text('main'))
        if when.startswith('2026-10-1') and not np_:
            pg.locator('main').screenshot(path=f'{SHOTS}/t16-shotlist-countdown-{when[:10]}-390.png')

    # N17, N18: local.html.
    lt = text_of(site['local'])
    check('N17: "Recently finished" and its four lines are gone', 'Recently finished' not in lt and 'id="log-h"' not in site['local']
          and 'Export to eBird goes live' not in lt and 'First run on a real shoot' not in lt and 'SHIPPED LOG' not in site['local'])
    q = newpage(390); q.goto(BASE + 'local.html'); q.wait_for_timeout(300)
    card = q.locator('#dropin form#dl').locator('xpath=..')
    ct = card.inner_text()
    check('N18: no date set, the drop-in box says it in one line', "No date set yet. Leave your email and you'll get it first." in ct
          and 'NEXT DROP-IN' not in ct.upper() and 'Get the next date' not in ct and "Sign up and you'll hear the date first." not in ct, ct[:200])
    check('N18: the form and its button stay', q.locator('#dl-email').count() == 1 and q.locator('#dl-name').count() == 1
          and q.inner_text('#dl-send').strip() == 'Put me on the list →')
    q.locator('#dropin').screenshot(path=f'{SHOTS}/t16-dropin-390.png')

    # N22: the BrightLocal line.
    check('N22: the line above the second card names who was asked',
          '45% of US adults surveyed now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026). <a href="https://www.brightlocal.com/research/local-consumer-review-survey/" target="_blank" rel="noopener">See the source</a>' in site['checkup']
          and '45% of people now' not in site['checkup'])

    # N24: the lone 05 and 06 are gone; the audit report's 01 to 07 stay.
    q = newpage(1440); q.goto(BASE + 'mainframe.html'); q.wait_for_timeout(300)
    toc = q.locator('[data-toc] span').evaluate_all('e => e.map(s => s.textContent.trim()).filter(t => /^0[0-9]$/.test(t))')
    check('N24: the audit report still lists 01 to 07', toc == ['01', '02', '03', '04', '05', '06', '07'], str(toc))
    lone = q.evaluate('[...document.querySelectorAll("span")].filter(s => /^0[0-9]$/.test(s.textContent.trim()) && !s.closest("[data-toc], pre")).length')   # T-21 G3: the code's own "05" token sits in a span now
    check('N24: no lone section number left on the page', lone == 0, str(lone))
    check('N24: no empty column left where 05 was', q.eval_on_selector('#s5 > div', 'e => e.children.length === 1 && !!e.firstElementChild.querySelector("#s6-h")'))
    check('N24: the section about Josef keeps its photo column', q.locator('#s7 > div > div').first.locator('img, [role="img"]').count() == 1
          and q.locator('#s7 > div > div').first.inner_text().strip() == '')

    # Look rule: every changed page at 320, 390 and 1440, no sideways scroll on phones.
    for n in T16_PAGES:
        q = newpage(320); q.goto(BASE + n + '.html'); q.wait_for_timeout(400)
        for w in (320, 390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            if w < 1440:
                sw = q.evaluate('document.documentElement.scrollWidth')
                check(f'T-16: {n} has no sideways scroll at {w}', sw <= w, str(sw))
            q.screenshot(path=f'{SHOTS}/t16-{n}-{w}.png', full_page=True)


# ---------------- T-17: voice pass, home (voice2.py V1 to V6)
@section('T-17')
def s_t_17():
    src = _html.unescape(urlopen(BASE + 'index.html').read().decode('utf-8'))
    V_NEW = {
        'V1': T34_LINE,   # T-34 (Nov 20, 2026): Josef reworded it
        'V2': T33_R2,   # T-19 W2; T-33 R2
        'V3 bold': "Nothing goes out until a person has looked at it.",
        'V3 line': "First me, then you.",
        'V4 bold': "You never have to take my word for it.",
        'V4 line': "The checks stay with you, and you can run them again any time.",
        'V5 bold': "The first step is small and the price is fixed.",
        'V5 line': "And if you don't need me, I'll tell you. I sold insurance for years and learned to give the honest answer even when it cost me the sale.",
        'V6 bold': "What's yours stays yours.",
        'V6 line': "Your accounts, your data, and it's in the contract.",
    }
    V_OLD = {
        'V1': "I'm Josef. I build AI tools that take real work off your plate, and I explain every one of them in plain English. Pick the one that sounds like you, and I'll take it from here.",
        'V2': "For small businesses and nonprofits in Sonoma County. Hand me the videos you never get to, the lessons in a binder or the chore that eats your week. I'll turn it into reels, an app with your name on it, or a chore that runs itself, and show you that it works.",
        'V3 bold': "A person checks everything first.",
        'V3 line': "Nothing reaches your customers or your live systems until a real person has looked at it.",
        'V4 bold': "You can check my work without me.",
        'V4 line': "The tests stay with you, so you can rerun them any time you like.",
        'V5 line': "If the honest answer is that you don't need me, that's the answer you get.",
        'V6 line': "Your data stays in your own accounts, and the contract says so.",
    }
    for k, v in V_NEW.items():
        check(f'T-17 {k}: new line on the home page exactly once', un21(src).count(v) == 1, str(un21(src).count(v)))   # T-33 R2: "follow-ups" sits in a no-wrap span
    for k, v in V_OLD.items():
        check(f'T-17 {k}: old line gone from the home page', v not in src)
    check('T-17: no em dash on the home page', '—' not in src)
    pairs = _re.findall(r'<li[^>]*><strong[^>]*>([^<]*)</strong><span[^>]*>([^<]*)</span></li>', src)
    check('T-17: "How I work" is four items, each a bold line over its second line, in order',
          pairs == [(V_NEW[f'V{i} bold'], V_NEW[f'V{i} line']) for i in (3, 4, 5, 6)], str(pairs))
    for keep in ('AI that works the first day', 'Proof your new system', 'The Blueprint: two weeks, $1,500, fixed. If you go ahead, the $1,500 comes off the price.',   # T-19 W1
                 'The Survey · one group of programs · from $8,000 · counts toward the next step', 'Take the Local Route →',
                 'Take the Mainframe Route →', 'How I work, on either side',
                 'For banks, insurers and agencies moving off COBOL with AI.'):
        check(f'T-17: home keeps "{keep[:40]}"', un21(src).count(keep) == 1)   # T-21: read without its line-breaking spans
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(400)
        sw = q.evaluate('document.documentElement.scrollWidth')
        check(f'T-17: home has no sideways scroll at {w}', sw <= w, str(sw))
        cards = q.locator('a.route').evaluate_all('e => e.map(a => { const r = a.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.height), a.scrollHeight - a.clientHeight, a.scrollWidth - a.clientWidth] })')
        check(f'T-17: neither route card spills at {w}', len(cards) == 2 and all(c[3] <= 0 and c[4] <= 0 for c in cards), str(cards))
        lis = q.locator('#rules-h + ol > li').evaluate_all('e => e.map(l => { const r = l.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.height), l.scrollWidth - l.clientWidth] })')
        check(f'T-17: four "How I work" items, none spilling sideways, at {w}', len(lis) == 4 and all(l[3] <= 0 for l in lis), str(lis))
        if w == 1440:
            check('T-17: the two route cards sit side by side, same top and height, at 1440',
                  cards[0][1] == cards[1][1] and cards[0][2] == cards[1][2] and cards[0][0] < cards[1][0], str(cards))
            check('T-17: the four "How I work" items sit in one row, same top and height, at 1440',
                  len({l[1] for l in lis}) == 1 and len({l[2] for l in lis}) == 1, str(lis))
            begins = q.locator('a.route').evaluate_all('e => e.map(a => Math.round([...a.querySelectorAll("span")].find(s => s.textContent.trim() === "BEGINS WITH").getBoundingClientRect().y))')
            # The Mainframe card has a 1 px border and the Local card has none, so allow 1 px.
            check('T-17: both "Begins with" lines sit at the same height at 1440 (within the 1 px border)', len(begins) == 2 and abs(begins[0] - begins[1]) <= 1, str(begins))
        else:
            check(f'T-17: route cards stack in one column at {w}', cards[0][0] == cards[1][0] and cards[0][1] < cards[1][1], str(cards))
        q.screenshot(path=f'{SHOTS}/t17-home-{w}.png', full_page=True)
        q.locator('section[aria-label="Routes"]').screenshot(path=f'{SHOTS}/t17-home-routes-{w}.png')
        q.locator('section[aria-labelledby="rules-h"]').screenshot(path=f'{SHOTS}/t17-home-rules-{w}.png')
        q.locator('header:has(h1)').screenshot(path=f'{SHOTS}/t17-home-hero-{w}.png')


# ---------------- T-18: simple pass, the six tools and the phone header (Nov 13, 2026)
@section('T-18')
def s_t_18():
    SAMPLE = sample()   # T-31: as the checkup section built it (built here when T-18 runs alone)
    T17 = 'd0a24616f56f85eb6a252d3a4f98ad2449d1ca04'   # trip/T-17: the pages as they were before this item
    T17_FILES = {}

    def t17_file(path):
        if path not in T17_FILES:
            r = _sp18.run(['git', 'show', f'{T17}:{path}'], cwd=here, capture_output=True)
            T17_FILES[path] = r.stdout if r.returncode == 0 else None
        return T17_FILES[path]

    def old_page(w, h=900):
        """A page that can open the T-17 build at BASE + '__t17/<file>', straight from git."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t17/', 1)[1].split('?')[0].split('#')[0]
            body = t17_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'application/octet-stream')
        q.route('**/__t17/**', serve)
        return q
    OLD = BASE + '__t17/'
    check('T-18: the T-17 pages can be read from git for comparison', t17_file('shotlist.html') is not None and t17_file('comp3.html') is not None)
    TOOLS6 = ('shotlist', 'captions', 'receipt', 'scaler', 'checkup', 'comp3')
    MENU = ('index', 'work', 'call', 'case-reels', 'start', 'shotlist', 'captions', 'receipt', 'scaler', 'checkup',
            'studio', 'studio-birdleague', 'studio-deepcuts')
    # Built on Windows the pages end lines with CRLF and git holds LF, so compare without CR.
    new_src = {n: urlopen(BASE + n + '.html').read().decode('utf-8').replace('\r', '') for n in TOOLS6 + MENU}
    old_src = {n: t17_file(n + '.html').decode('utf-8').replace('\r', '') for n in TOOLS6 + MENU}


    # Left as they are: title tags, meta descriptions, share cards, the dark panels and the "More free tools" lines.
    for n in TOOLS6 + ('index',):
        for rx in (r'<title>.*?</title>', r'<meta name="description"[^>]*>', r'<meta property="og:[^"]*"[^>]*>', r'<meta name="twitter:card"[^>]*>'):
            check(f'T-18: {n} keeps its {rx[1:12]}... as at T-17', _re.findall(rx, new_src[n], _re.S) == _re.findall(rx, old_src[n], _re.S))
    for n in TOOLS6[:5]:
        for rx in (r'<p class="noprint"[^>]*>More free tools:.*?</p>', r'<section aria-labelledby="more-h".*?</section>'):
            a, b_ = _re.findall(rx, un23(un33(un34(new_src[n], n + '.html'), n + '.html'), n + '.html'), _re.S), _re.findall(rx, old_src[n], _re.S)   # T-23 L4: the line's new markup out; T-33: R20's order out
            if n == 'receipt' and 'more-h' in rx:   # T-19 W21 changed the panel's line; the rest stays as at T-17
                b_ = [x.replace('Day 1 of a Blueprint is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the build price.',
                                'The first step is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the price if you go ahead.') for x in b_]
            if not CK_LIVE:   # T-20 F2: no checkup link while it isn't live
                b_ = [x.replace(' · <a href="checkup.html">Website checkup</a>', '') for x in b_]
            a = [un21(x).replace('#0E1A17', '#0E1B17') for x in a]   # T-20 F9: the orange button's text is one shade darker; T-21: line-breaking spans out
            check(f'T-18: {n} keeps its {"More free tools line" if "More" in rx else "dark panel"} as at T-17', a == b_ and len(a) == 1)

    # The words, exactly once where they are in the page itself, and the old ones gone.
    NEW_LINES = {
        'shotlist': ["Tell me what you run. You get 10 clips to film, in the order you walk your shop.", "What do you run?",
                     "Change the details", "Your 10 clips. Film them in this order.", "Start at the top of the list and film as you go. You never walk back.",   # T-19 W13, W14
                     "How it gets cut together"],
        'captions': ["Type the words that go on your video. See them on a phone, and find out if people can read them before they're gone.", "Change how it looks",   # T-19 W17
                     "Which app?", "How long is your clip?", "Try it on your own video", "Add a screenshot from your video. It stays on your phone.",
                     "Your caption, split up", "Save this caption as an image", "Save all of them", "Copy the text",
                     "This picture is see-through except for your words. Lay it over your video in CapCut or the Instagram editor and the words land right where you see them here."],   # T-19 W19
        'receipt': ["Tap the chores that eat your week. See what a year of them costs you.", "Guess. Close is good enough."],
        'scaler': ["Paste a recipe and say who's eating. You get amounts you can actually measure."],
        'checkup': ["Paste your website's address. You get a plain list of what's broken, worst first, and whether AI tools can find your business."],
        'comp3': ["One stored number. Two ways to read it. On a $1,000 balance, one reading charges $2.92 of interest a month and the other charges $291.67. The code can't tell you which is right. Paste your own below. Nothing you paste leaves this page.",
                  "The line in the program that says how the number is stored. Paste it however it appears: PIC S9(7)V99 COMP-3. works."],
    }
    OLD_LINES = {
        'shotlist': ["Ten clips.", "Tell it four things", "The shoot: one lap, no backtracking",
                     "Film by where you're standing, not by the edit order. Numbers match the edit.",
                     "Pick what you run and what the reel should do.", "'Payoff'", "'Where'", "'Hook'"],
        'captions': ["Type it once.", "Upper third", "Lower third", "Check against", "This clip is on screen for", "Try it on your own frame",
                     "A screenshot from your video. It stays on your device.", "The checkup", ">Screens<", "Download this screen as a PNG",
                     "Download every screen", "Copy the line breaks", "The PNG is see-through", "Two lines fit comfortably", "Fits on one screen. Tap it to preview."],
        'receipt': ["How long, how often", "Change any name to match how you'd say it.", "COULD COME BACK", "Could come back:",
                    "Tap a chore above to start your receipt.", "You get a receipt for a year of them", "tag2"],
        'scaler': ["Paste any ingredient list and say who's eating."],
        'checkup': ["Paste your site's address. You get a plain report"],
        'comp3': ["A free tool · runs in your browser", "Paste the raw bytes of a COMP-3", "Paste the bytes of a COMP-3 field and its picture clause. You get"],
    }
    def visible_text(src):
        return U(_re.sub(r'\s+', ' ', _re.sub(r'<[^>]+>', ' ', _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S))))
    for n, lines in NEW_LINES.items():
        page_text = visible_text(new_src[n]) + ' ' + U(new_src[n])   # words in the markup, or in the script that writes them
        flat = U(_re.sub(r'<[^>]+>', '', new_src[n]))
        for s in lines:
            c = flat.count(s) + (flat.count(s.replace("'", "\\'")) if "'" in s else 0)
            check(f'T-18: {n} has "{s[:50]}" exactly once', c == 1, str(c))
    for n, lines in OLD_LINES.items():
        for s in lines:
            check(f'T-18: {n} no longer has "{s[:50]}"', s not in U(new_src[n]) and s.replace("'", "\\'") not in U(new_src[n]))

    # Every page that gains the phone menu, and the folds: at 390, 48 px or taller, closed on load.
    def fold_ok(q, btn, target, label):
        b_ = q.locator(btn)
        t_ = q.locator(target)
        h_ = b_.bounding_box()['height'] if b_.is_visible() else 0
        tag = b_.evaluate('e => e.tagName')
        check(f'T-18: {label}: a real button, closed on load, 48 px or taller at 390', tag == 'BUTTON' and b_.get_attribute('aria-expanded') == 'false'
              and not t_.is_visible() and h_ >= 48 and b_.get_attribute('aria-controls') == t_.get_attribute('id'), f'{tag} {h_}')
        b_.click(); q.wait_for_timeout(60)
        o1 = b_.get_attribute('aria-expanded') == 'true' and t_.is_visible()
        b_.click(); q.wait_for_timeout(60)
        c1 = b_.get_attribute('aria-expanded') == 'false' and not t_.is_visible()
        check(f'T-18: {label}: opens and closes by click, aria-expanded follows', o1 and c1)
        b_.focus(); q.keyboard.press('Enter'); q.wait_for_timeout(60)
        o2 = b_.get_attribute('aria-expanded') == 'true' and t_.is_visible()
        q.keyboard.press('Space'); q.wait_for_timeout(60)
        c2 = b_.get_attribute('aria-expanded') == 'false' and not t_.is_visible()
        check(f'T-18: {label}: opens with Enter and closes with Space from the keyboard', o2 and c2)
        q.keyboard.press('Shift+Tab'); q.keyboard.press('Tab')
        check(f'T-18: {label}: reachable with Tab', q.evaluate('document.activeElement') is not None and b_.evaluate('e => e === document.activeElement'))

    q = newpage(390, 844); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    fold_ok(q, '#f-details', '#details', 'shot list "Change the details"')
    fold_ok(q, '#f-cut', '#cut', 'shot list "How it gets cut together"')
    q = newpage(390, 844); q.goto(BASE + 'captions.html'); q.wait_for_timeout(300)
    fold_ok(q, '#f-look', '#look', 'caption fitter "Change how it looks"')
    q = newpage(390, 844); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    for i in range(3):
        fold_ok(q, f'#rows .row2:nth-child({i + 1}) .fold', f'#rows .row2:nth-child({i + 1}) .ed', f'receipt line {i + 1} "Change"')

    # The answer first: where each tool's answer starts at 390 wide (one phone screen is 844 px).
    ANSWER = {'shotlist': "document.querySelector('section[aria-labelledby=shoot-h]')", 'captions': "document.querySelector('.phone')",
              'receipt': "document.getElementById('paper')", 'scaler': "document.getElementById('out').closest('table')",
              'checkup': "document.getElementById('soon')",
              'comp3': "[...document.querySelectorAll('#out .label')].find(e => e.textContent === 'If this field is an annual rate').parentElement"}
    for n, js in ANSWER.items():
        tops = []
        for base_, pgf in ((BASE, lambda: newpage(390, 844)), (OLD, lambda: old_page(390, 844))):
            q = pgf(); q.goto(base_ + n + '.html'); settle(q)
            tops.append(q.evaluate('(() => Math.round(' + js + '.getBoundingClientRect().top + scrollY))()'))
        check(f'T-18: {n}: the answer starts on the first or second phone screen at 390 (was {tops[1]} px, now {tops[0]} px)',
              tops[0] < 2 * 844 and tops[0] <= tops[1], str(tops))

    # Same choices, same results: three inputs per tool, against the page as it was at T-17.
    def both(name, fn, w=1440):
        out_ = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD, lambda: old_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')], [('type', 'nonprofit'), ('len', '45'), ('light', 'mid')]):
        def shot(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT_JS)
            r['copy'] = _re.sub(r'(?m)^(\d+)\. [^(\n]+ \(', r'\1. (', grab_copy(q, '#copy'))   # S8 renames the clip labels
            return r
        a, b_ = both('shotlist', shot)
        check(f'T-18: shot list gives the same clips, seconds, stops, rules, countdown and copy as T-17 for {picks or "the defaults"} (T-20 F1: the offer is gone)', a == b_,
              str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    q.click('#f-cut'); q.wait_for_timeout(60)
    check('T-18 S8: the ten clip labels in the order people see them', q.locator('#edit .role').all_text_contents() ==
          ['Opening', 'Your place', 'Hands', "How it's made", 'Close-up', 'You', 'A customer', 'The best part', 'Your sign', 'The ask'],
          str(q.locator('#edit .role').all_text_contents()))
    qo = old_page(390); qo.goto(OLD + 'shotlist.html'); qo.wait_for_timeout(300)
    st_js = 'e => { const s = getComputedStyle(e); return [e.className, s.fontFamily, s.fontSize, s.textTransform, s.backgroundColor, s.color, s.padding] }'
    check('T-18 S8: the labels keep their styling', q.locator('#edit .role').evaluate_all(f'es => es.map({st_js})') == qo.locator('#edit .role').evaluate_all(f'es => es.map({st_js})'))
    q.click('#f-cut')
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-18: printed, the shot list shows both lists, the edit fold open', q.locator('#cut').is_visible() and q.locator('#edit .clip').count() == 10
          and q.locator('#shoot li').count() == 10 and not q.locator('#f-cut').is_visible())
    q.emulate_media(media='screen')

    for text, picks, secs in CAP_IN:
        def cap(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks)
            if secs:
                set_val(q, '#secs', secs)
            q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS)
            r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both('captions', cap)
        check(f'T-18: caption fitter gives the same screens, checks, preview and copy as T-17 for {(text or "the default")[:24]} {picks}', a == b_,
              str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390, 844); q.goto(BASE + 'captions.html'); q.wait_for_timeout(500)
    v = q.locator('#verdict')
    check('T-18 S11: the verdict line has role="status"', v.get_attribute('role') == 'status')
    set_val(q, '#secs', '5'); q.wait_for_timeout(100)   # T-20 F7: the clip starts at 7.5 s now, so set the old 5 s
    check('T-18 S11: too long, with today\'s numbers', v.inner_text().strip() == 'Too long for this clip. People need about 7.5 seconds and your clip is 5.', v.inner_text())
    set_val(q, '#secs', '10'); q.wait_for_timeout(100)
    check('T-18 S11: good to go when it fits and there is time', v.inner_text().strip() == 'Good to go. It fits, and people can read it in time.', v.inner_text())
    set_val(q, '#cap', 'Supercalifragilisticexpialidocious'); click_chips(q, [('size', 'l')]); set_val(q, '#secs', '1'); q.wait_for_timeout(300)
    check('T-18 S11: covered comes first, before too long', v.inner_text().strip() == "The app's buttons cover part of it. Move it up."
          and 'cover screen' in q.inner_text('#verdicts'), v.inner_text())
    set_val(q, '#cap', 'New fall sweaters just landed.'); set_val(q, '#secs', '5'); click_chips(q, [('size', 'm')]); q.wait_for_timeout(300)
    before_ = v.inner_text().strip()
    q.locator('#cap').click(); q.keyboard.press('Control+A')
    q.keyboard.type('Fresh sourdough comes out of the oven at 7 every morning. Come early, because the first batch is always gone by 9.'); q.wait_for_timeout(400)
    check('T-18 S11: the line updates as the visitor types', before_.startswith('Good to go.') and v.inner_text().strip().startswith('Too long for this clip.'), before_ + ' / ' + v.inner_text())
    st_ = q.locator('.stage').bounding_box(); vb = v.bounding_box(); fb = q.locator('#f-look').bounding_box(); cb = q.locator('.a-in').bounding_box()
    lb_ = q.locator('.a-len').bounding_box()
    check('T-18 S11: at 390, the caption box, then the phone, then the verdict, then "Change how it looks" (T-20 F7: the clip length sits between the phone and the verdict)',
          cb['y'] < st_['y'] < lb_['y'] < vb['y'] < fb['y'] and vb['y'] - (lb_['y'] + lb_['height']) < 40, f'{cb} {st_} {lb_} {vb} {fb}')
    check('T-18 S13: where on screen is Top / Middle / Bottom, Bottom chosen as before', q.locator('#c-pos .chip').all_text_contents() == ['Top', 'Middle', 'Bottom']
          and q.locator('#c-pos .chip[aria-pressed=true]').inner_text() == 'Bottom')
    check('T-18 S16: the checkup list is headed "Why" and sits under the verdict and the settings link', q.inner_text('#v-h') == 'Why'
          and q.locator('#v-h').bounding_box()['y'] > fb['y'])
    check('T-18 S17: the note counts the parts', q.inner_text('#k-sub') == 'Two lines fit on a phone, so this caption shows in 3 parts. Tap one to see it.', q.inner_text('#k-sub'))
    set_val(q, '#cap', 'New fall sweaters just landed.'); q.wait_for_timeout(300)
    check('T-18 S17: one part, no note', not q.locator('#k-sub').is_visible() and q.locator('#cards .cardline').count() == 1)
    with q.expect_download() as dl:
        q.click('#png')
    check('T-18 S18: "Save this caption as an image" still saves the PNG', dl.value.suggested_filename == 'caption-1.png', dl.value.suggested_filename)

    for args in (([], None, False), ([4, 11], '45', False), ([1, 9], None, True)):
        a, b_ = both('receipt', rec_in(*args))
        check(f'T-18: receipt gives the same lines, totals, hand-off and copy as T-17 for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]) + ' ' + str(a)[:300])
    q = newpage(390, 844); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    y = lambda s: q.locator(s).bounding_box()['y']
    check('T-18 S21/S22: at 390, the chips, then "+ Something else" and the hourly rate, then the receipt (T-20 F7: measured from the first chip)',
          y('#presets .chip >> nth=0') < y('#addown') < y('#paper') and y('#rate') < y('#paper'))
    n0 = q.locator('#rows .row2').count()
    q.click('[data-p="4"]')
    check('T-18 S21: the receipt changes the moment a chore is tapped', q.locator('#rows .row2').count() == n0 + 1 and 'Editing videos or photos' in q.inner_text('#paper'))
    check('T-18 S22: "How long, how often" is gone as a block', q.locator('#lines').count() == 0 and 'How long, how often' not in q.inner_text('main'))
    check('T-18 S22: every receipt line has its own "Change"', q.locator('#rows .row2 > .fold').all_text_contents() == ['Change'] * (n0 + 1))
    q.click('#rows .row2:nth-child(1) .fold'); q.wait_for_timeout(60)
    ed = q.locator('#rows .row2:nth-child(1) .ed')
    check('T-18 S22: "Change" opens that chore\'s name, minutes, how often and remove, with "Guess. Close is good enough."',
          ed.locator('input[data-f=name]').input_value() == 'Answering the same questions' and ed.locator('input[data-f=min]').input_value() == '30'
          and ed.locator('select[data-f=per]').input_value() == 'day' and ed.locator('[data-del]').count() == 1
          and ed.locator('p').inner_text() == 'Guess. Close is good enough.')
    check('T-18 S23: the small tag is not repeated in the fields', 'AI drafts it, you approve' not in ed.inner_text()
          and 'AI drafts it, you approve' in q.locator('#rows .row2:nth-child(1) .rs').inner_text())
    ed.locator('input[data-f=min]').fill('60'); q.wait_for_timeout(60)
    check('T-18 S22: changing minutes keeps the field and its focus while the receipt updates', '$7,500' in q.inner_text('#rows .row2:nth-child(1)')
          and ed.locator('input[data-f=min]').evaluate('e => e === document.activeElement'))
    check('T-18: the fields are 48 px or taller at 390', all(h >= 48 for h in ed.locator('input, select, button').evaluate_all('es => es.map(e => e.getBoundingClientRect().height)')))
    q.click('#addown'); q.wait_for_timeout(60)
    last = q.locator('#rows .row2').last
    check('T-18 S22: "+ Something else" opens its own line with its name selected and "What fixes it?" kept',
          last.locator('.ed').is_visible() and last.locator('input[data-f=name]').evaluate('e => e === document.activeElement')
          and last.locator('select[data-f=v]').count() == 1)
    check('T-18 S24: "You could get back" on the receipt', 'You could get back' in q.inner_text('#paper') and 'COULD COME BACK' not in q.inner_text('#paper').upper())
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-18: printed, the receipt has no "Change" and no fields', q.locator('#paper .fold:visible').count() == 0 and q.locator('#paper .ed:visible').count() == 0)
    q.emulate_media(media='screen')

    for k, v_ in (([], None), ([('#kids', '40')], None), ([('#serves', '6'), ('#adults', '10'), ('#kids', '0')], None)):
        def sc(q):
            for s, val in k:
                set_val(q, s, val)
            q.wait_for_timeout(100)
            return [q.inner_text('#fac'), q.inner_text('#facl'), q.inner_text('#warn'), q.inner_text('#out')]
        a, b_ = both('scaler', sc)
        check(f'T-18: scaler gives the same amounts as T-17 for {k or "the defaults"}', a == b_)

    thin = thin18()   # T-31: built once, by thin18() above (T-19 reads it too)
    for ans in (SAMPLE, thin, {'ok': False, 'error': 'private-name'}):
        res = []
        for base_, pgf in ((BASE, lambda: newpage(1440)), (OLD, lambda: old_page(1440))):
            q = pgf()
            def page_route(route, request=None, base_=base_):   # T-19: Playwright hands a second argument (the request) to a two-argument handler
                body = route.fetch().text() if base_ == BASE else t17_file('checkup.html').decode('utf-8')
                route.fulfill(status=200, content_type='text/html', body=body.replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1))
            q.route(base_ + 'checkup.html', page_route)
            q.route('https://dj-checkup.test/**', worker_(ans))
            q.goto(base_ + 'checkup.html'); q.wait_for_timeout(400)
            q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            res.append([q.inner_text('#msg')] + [q.inner_text(s) if q.locator(s).is_visible() else '' for s in ('#rep1', '#stat', '#rep2')])
            if base_ == BASE:   # T-19 W22 to W24 changed three lines of the second card; the rest stays as at T-17
                for new_, old_ in (("It checks whether a computer can find the basic facts about your business on your page.", "It checks whether a machine can read the facts it would need."),
                                   ('What a computer can read off your page', 'The facts a machine reads off your page'),
                                   ("Compare these with your Google listing. They should match exactly.", "Check these against your Google Business Profile, letter for letter.")):
                    res[-1][3] = res[-1][3].replace(new_, old_, 1)
        check(f'T-18: checkup gives the same report as T-17 for {"a refusal" if not ans.get("ok") else "a thin page" if ans is thin else "the sample"}', res[0] == res[1] and any(res[0]))

    def dec(q, steps):
        for s in steps:
            if s[0] == 'chip':
                q.click(f'text={s[1]}')
            elif s[0] == 'mode':
                q.click(s[1])
            else:
                q.fill(s[0], s[1])
        q.wait_for_timeout(100)
        return [sorted(l for l in q.inner_text('#out').split('\n') if l.strip()), _re.sub(r'.*#', '#', q.url)]
    for steps in ([], [('chip', 'A damaged field')], [('chip', 'A negative balance')], [('mode', '#mode-enc'), ('#in', '-12.345'), ('#pic', 'S9(5)V99')]):
        a, b_ = both('comp3', lambda q: dec(q, steps))
        a = [sorted(un24(l) for l in a[0]), a[1]]   # T-24 A7: the two result labels read back as T-23's
        check(f'T-18: decoder shows the same readouts and share link as T-17 for {steps or "the opening example"}', a == b_)
    q = newpage(390, 844); q.goto(BASE + 'comp3.html'); q.wait_for_timeout(300)
    check('T-18 S27: "Free tool" over the title', q.locator('h1').evaluate('e => e.previousElementSibling.textContent') == 'Free tool')
    out_t = q.inner_text('#out')
    check('T-18 S28: the intro\'s figures are what the tool computes on load', '$2.92' in out_t and '$291.67' in out_t
          and q.locator('#out > div').first.inner_text().upper().startswith('IF THIS FIELD IS AN ANNUAL RATE'), out_t[:200])
    order = q.evaluate('''(() => { const k = [...document.querySelectorAll('#out > *')]; const f = p => k.findIndex(p);
      return [f(e => e.classList.contains('ok')), f(e => e.textContent.startsWith('If this field is an annual rate')), f(e => e.tagName === 'DL'), f(e => e.textContent.startsWith('Every half-byte'))] })()''')
    check('T-18 S29: clean message, then the dollar readings and their sentence, then value, digits, sign and length, then the half-byte boxes', order == [0, 1, 2, 3], str(order))
    gap = q.evaluate("document.querySelector('#out > .ok').getBoundingClientRect().top - [...document.querySelectorAll('.chip[data-b]')].pop().getBoundingClientRect().bottom")
    check('T-18 S29: the clean-or-damaged message sits right under the examples at 390', 0 < gap <= 64, str(gap))
    q.click('text=A damaged field'); q.wait_for_timeout(100)
    check('T-18 S29: a damaged field still leads with its warning', q.locator('#out > *').first.evaluate('e => e.className') == 'warn')

    # S1: the phone header.
    def header_links(q):
        return q.evaluate('''(() => { const L = document.querySelector('a[href="work.html#free"]').parentElement;
          return [...L.querySelectorAll('a')].map(a => [a.getAttribute('href'), a.textContent.trim()]) })()''')
    for n in MENU:
        q = old_page(390); q.goto(OLD + n + '.html'); q.wait_for_timeout(200)
        want = header_links(q)
        for w in (320, 390):
            q = newpage(w, 844); q.goto(BASE + n + '.html'); q.wait_for_timeout(300)
            btn = q.locator('.djm-btn')
            links = q.locator('#djm-links')
            logo = q.locator('.djm > a, .djm > span').first.bounding_box()
            bb = btn.bounding_box() if btn.is_visible() else None
            check(f'T-18 S1: {n} at {w}: one row, the site name and "Menu", links closed', bb is not None and btn.inner_text() == 'Menu'
                  and btn.get_attribute('aria-expanded') == 'false' and not links.is_visible() and bb['height'] >= 48
                  and abs((bb['y'] + bb['height'] / 2) - (logo['y'] + logo['height'] / 2)) <= 6 and bb['x'] > logo['x'] + logo['width'], f'{bb} {logo}')
            btn.click(); q.wait_for_timeout(80)
            items = links.locator('a').evaluate_all('es => es.map(a => { const r = a.getBoundingClientRect(); return [a.getAttribute("href"), a.textContent.trim(), Math.round(r.top), r.height] })')
            check(f'T-18 S1: {n} at {w}: "Menu" opens the same links and call button, in the same order, under the header row',
                  btn.get_attribute('aria-expanded') == 'true' and [i[:2] for i in items] == want and all(i[3] >= 48 for i in items)
                  and [i[2] for i in items] == sorted(i[2] for i in items) and items[0][2] >= bb['y'] + bb['height'], f'{items} {want}')
            sw = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-18 S1: {n} at {w}: no sideways scroll with the menu open', sw <= w, str(sw))
            if w == 390 and n in ('index', 'captions'):
                q.screenshot(path=f'{SHOTS}/t18-menu-{n}-390.png')
            btn.click(); q.wait_for_timeout(60)
            check(f'T-18 S1: {n} at {w}: pressing again closes it', btn.get_attribute('aria-expanded') == 'false' and not links.is_visible())
            btn.focus(); q.keyboard.press('Enter'); q.wait_for_timeout(60)
            o = links.is_visible()
            q.keyboard.press('Escape'); q.wait_for_timeout(60)
            check(f'T-18 S1: {n} at {w}: opens from the keyboard, Escape closes it and leaves focus on "Menu"', o and not links.is_visible()
                  and btn.evaluate('e => e === document.activeElement'))
        # 700 px and wider: the header as it was at T-17, to the pixel.
        HJS = '''(() => { const L = document.querySelector('a[href="work.html#free"]').parentElement.parentElement;
          const r = e => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] };
          return [r(L), [...L.querySelectorAll('*')].filter(e => e.getBoundingClientRect().width > 0 && !(e.tagName === 'SPAN' && e.closest('a') && (e.getAttribute('style') === 'white-space: nowrap' || (!e.attributes.length && e.querySelector('span[style="white-space: nowrap"]'))))).map(e => [e.tagName, e.tagName === 'svg' ? '' : e.textContent.trim().slice(0, 30), r(e)]),
                  Math.round(document.querySelector('h1').getBoundingClientRect().top)] })()'''
        for w in (700, 1024, 1440):
            got = []
            for base_, pgf in ((BASE, lambda: newpage(w)), (OLD, lambda: old_page(w))):
                q = pgf(); q.goto(base_ + n + '.html'); settle(q)
                got.append(q.evaluate(HJS))
            # T-21 G1: the call button's words now sit in one span, which can move the right-hand links by
            # a sub-pixel amount (1 px after rounding, at 1024); everything else must match exactly.
            near = lambda a, b: type(a) == type(b) and (abs(a - b) <= 1 if isinstance(a, (int, float)) else
                                                        (len(a) == len(b) and all(near(x, y) for x, y in zip(a, b))) if isinstance(a, list) else a == b)
            check(f'T-18 S1: {n} at {w}: the header matches T-17 (no Menu button, every link where it was; T-21: within 1 px)', near(got[0], got[1]), str(got[0])[:200] + ' | ' + str(got[1])[:200])
    for n in ('local', 'mainframe', 'briefing', 'comp3', '404'):
        src_ = urlopen(BASE + n + '.html').read().decode('utf-8')
        check(f'T-18 S1: {n} keeps its header, no Menu button', 'djm-btn' not in src_)

    # S31: "How I work" on phones; 700 px and up as at T-17.
    LI = 'es => es.map(l => { const r = l.getBoundingClientRect(), s = getComputedStyle(l); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), s.paddingLeft, s.paddingRight, s.borderRightWidth] })'
    for w in (320, 390, 600, 699):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(300)
        lis = q.locator('#rules-h + ol > li').evaluate_all(LI)
        check(f'T-18 S31: at {w}, the four "How I work" items share one left edge, no line at the right', len(lis) == 4 and len({l[0] for l in lis}) == 1
              and all(l[3] == '0px' and l[5] == '0px' for l in lis) and [l[1] for l in lis] == sorted(l[1] for l in lis), str(lis))
        if w in (320, 390):
            q.locator('section[aria-labelledby="rules-h"]').screenshot(path=f'{SHOTS}/t18-home-rules-{w}.png')
    for w in (700, 1024, 1440):
        got = []
        for base_, pgf in ((UN30, lambda: newpage(w)), (OLD, lambda: old_page(w))):   # T-33: R2's card line out (it moves the section)
            q = pgf(); q.goto(base_ + 'index.html'); settle(q)
            got.append(q.locator('#rules-h + ol > li').evaluate_all(LI))
        check(f'T-18 S31: at {w}, "How I work" is as it was at T-17', got[0] == got[1], str(got))

    # No sideways scroll at 320 and 390 on every changed page, folds closed and open.
    for n in MENU + ('comp3',):
        for w in (320, 390):
            q = newpage(w); q.goto(BASE + n + '.html'); q.wait_for_timeout(300)
            a = q.evaluate('document.documentElement.scrollWidth')
            q.evaluate("document.querySelectorAll('.fold[aria-expanded=false]').forEach(b => b.click())"); q.wait_for_timeout(100)
            b2 = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-18: {n} has no sideways scroll at {w}, folds closed and open', a <= w and b2 <= w, f'{a} {b2}')


# ---------------- T-19: harness lines 01, 33 word changes (W1 to W33), Nov 13, 2026
@section('T-19')
def s_t_19():
    SAMPLE = sample()   # T-31: as the checkup section built it (built here when T-19 runs alone)
    thin = thin18()   # T-31: as T-18 built it (built here when T-19 runs alone)
    # Every check here is against the pages as they were at T-18, read straight from git.
    T18 = '5ab14f363bc9ae99bf2a7e110871b097ac01d4e6'   # origin/main after T-18
    T18_FILES = {}

    def t18_file(path):
        if path not in T18_FILES:
            r = _sp18.run(['git', 'show', f'{T18}:{path}'], cwd=here, capture_output=True)
            T18_FILES[path] = r.stdout if r.returncode == 0 else None
        return T18_FILES[path]

    def t18_page(w, h=900):
        """A page that can open the T-18 build at BASE + '__t18/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t18/', 1)[1].split('?')[0].split('#')[0]
            body = t18_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t18/**', serve)
        return q
    OLD18 = BASE + '__t18/'
    check('T-19: the T-18 pages can be read from git for comparison', t18_file('index.html') is not None and t18_file('briefing.html') is not None)

    def both18(name, fn, w=1440):
        out_ = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD18, lambda: t18_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    # (ID, page, old words, new words, old in the markup, new in the markup); None: the markup is the words.
    W19 = [
        ('W1', 'index', "The Blueprint · $1,500 · two weeks · counts toward the build", "The Blueprint: two weeks, $1,500, fixed. If you go ahead, the $1,500 comes off the price.", None, None),
        ('W2', 'index', "you watch it work before you decide on the build", "you watch it work before you decide to go ahead", None, None),
        ('W3', 'local', "Two weeks · fixed price · the $1,500 comes off your build", "Two weeks · fixed price · the $1,500 comes off the price if you go ahead", None, None),
        ('W4', 'work', "~4 min", "An 81-second reel in about 4 minutes", '<p class="num">~4 min</p>', '<p class="num">An 81-second reel in about 4 minutes</p>'),
        ('W5', 'work', "535 tests", "535 automatic checks", '<p class="num">535 tests</p>', '<p class="num">535 automatic checks</p>'),
        ('W6', 'work', "2 AI translations", "2 AI translations of one bank program", '<p class="num">2 AI translations</p>', '<p class="num">2 AI translations of one bank program</p>'),
        ('W7', 'work', "A competitive birding app I built from zero lines of code. Its first sound screen ran on mock data. Build 49 names birds from a photo or a song, has real players, and sends sightings to eBird in one tap.",
                       "A competitive birding app I built from zero lines of code. It names birds from a photo or a song, has real players, and sends sightings to eBird in one tap.", None, None),
        ('W8', 'start', "Who says yes, and when?", "Who says yes to spending money, and when?", None, None),
        ('W9', 'start', "Good days for Day 1", "Good days for my first visit", '<h2 id="s5">Good days for Day 1</h2>', '<h2 id="s5">Good days for my first visit</h2>'),
        ('W10', 'start', "Start my Blueprint →", "Send my answers →", 'id="bp-send">Start my Blueprint →<', 'id="bp-send">Send my answers →<'),
        ('W11', 'start', "You get the one-page Blueprint agreement and an invoice for $1,500.", "You get a one-page agreement and an invoice for $1,500.", None, None),
        ('W12', 'call', "Tell me what you run and when you're free.", "Fifteen minutes, free. Tell me what you run and when you're free.",
                        '">Tell me what you run and when you\'re free. I\'ll call you', '">Fifteen minutes, free. Tell me what you run and when you\'re free. I\'ll call you'),
        ('W13', 'shotlist', "Your 10 clips, in walking order", "Your 10 clips. Film them in this order.", None, None),
        ('W14', 'shotlist', "Start at stop 1 and film as you go. You never walk back.", "Start at the top of the list and film as you go. You never walk back.", None, None),
        ('W15', 'shotlist', "Seconds are what each clip gets in the finished reel. Film every one for about five seconds anyway; the edit trims.",
                            "Film each one for about five seconds. The number beside it is how long it stays in the finished video.", None, None),
        ('W16', 'captions', "Will your caption survive the phone?", "Can people read the words on your video?", "Will your caption<br>survive the phone?", "Can people read the words on your video?"),
        ('W17', 'captions', "Type your caption. See it on a phone, and find out if people can read it in time.",
                            "Type the words that go on your video. See them on a phone, and find out if people can read them before they're gone.", None, None),
        ('W18', 'captions', "Box", "Box behind the words", 'id="l-box">Box</p>', 'id="l-box">Box behind the words</p>'),
        ('W19', 'captions', "The image is clear except for the caption. Drop it over your clip in CapCut or the Instagram editor and it lands right where you see it here.",
                            "This picture is see-through except for your words. Lay it over your video in CapCut or the Instagram editor and the words land right where you see them here.", None, None),
        ('W20', 'receipt', 'The "can come back" numbers are a rough rule of thumb for each kind of chore, not a promise. Day 1 of a Blueprint is where the real numbers come from.',
                           "The hours you could get back are a rough rule of thumb for each kind of chore, not a promise. The real numbers come from me watching how the work actually gets done.", None, None),
        ('W21', 'receipt', "Day 1 of a Blueprint is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the build price.",
                           "The first step is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the price if you go ahead.", None, None),
        ('W22', 'checkup', "This doesn't tell you what ChatGPT says about you. It checks whether a machine can read the facts it would need.",
                           "This doesn't tell you what ChatGPT says about you. It checks whether a computer can find the basic facts about your business on your page.", None, None),
        ('W23', 'checkup', "The facts a machine reads off your page", "What a computer can read off your page", None, None),
        ('W24', 'checkup', "Check these against your Google Business Profile, letter for letter. I can't see your listing from here.",
                           "Compare these with your Google listing. They should match exactly. I can't see your listing from here.", None, None),
        ('W25', 'case-reels', "and the tool puts together a finished vertical reel with the program's own title art.",
                              "and the tool puts together a finished reel, upright for phones, with the program's own title card.", None, None),
        ('W26', 'studio', "Built in the open", "Follow along while I piece it together", "Built in<br>the open", "Follow along<br>while I piece it together"),
        ('W27', 'studio', "Everything I'm building right now, and the date each piece shipped.", "Everything I'm building right now, and the date each piece was finished.",
                          ">Everything I'm building right now, and the date each piece shipped.</p>", ">Everything I'm building right now, and the date each piece was finished.</p>"),
        ('W28', 'studio', "things shipped since", "things finished since", None, None),
        ('W29', 'mainframe', "The code never divides by 100. The field definition allows two readings. Pick one:",
                             "The code never divides by 100. The field definition allows two readings. See each one:", None, None),
        ('W30', 'mainframe', "Every record tells a different story. The real data settles it.",
                             "The code, the layouts, the job setup and the data each tell a different story. The real data settles it.",
                             "Every record tells a different story. <em", "The code, the layouts, the job setup and the data each tell a different story. <em"),
        ('W31', 'mainframe', "Send one program and see what I find", "Tell me about one program and see what I'd look at first",
                             '>Send one program <em style="color: #A93F17">and see what I find</em>', '>Tell me about one program <em style="color: #A93F17">and see what I\'d look at first</em>'),
        ('W32', 'briefing', "Request a briefing", "Ask me about your system",
                            '>Request a <em style="color:#A93F17">briefing</em></h1>', '>Ask me about your <em style="color:#A93F17">system</em></h1>'),
        ('W33', 'briefing', "Which programs", "Which programs (a rough description is enough)",
                            '<span class="label">Which programs</span>', '<span class="label">Which programs (a rough description is enough)</span>'),
    ]
    # Words set again by script: the start button's label after a send that didn't go through.
    W19_SCRIPT = [('W10 script', 'start', None, None, "btn.textContent = 'Start my Blueprint →';", "btn.textContent = 'Send my answers →';")]
    check('T-19: 33 lines', len(W19) == 33 and [w[0] for w in W19] == [f'W{i}' for i in range(1, 34)])

    def words19(src):
        """What a visitor reads: the body, scripts and styles out, a line break read as a space."""
        b_ = src[src.index('<body'):]
        b_ = _re.sub(r'<(script|style)\b.*?</\1>', ' ', b_, flags=_re.S)
        b_ = _re.sub(r'<br\s*/?>', ' ', b_)
        return _re.sub(r'\s+', ' ', U(_re.sub(r'<[^>]+>', '', b_)))
    P19 = ['index', 'local', 'work', 'start', 'call', 'shotlist', 'captions', 'receipt', 'checkup', 'case-reels', 'studio', 'mainframe', 'briefing']
    check('T-19: the 13 pages named in the item', sorted(P19) == sorted({w[1] for w in W19}))
    src19 = {n: urlopen(BASE + n + '.html').read().decode('utf-8').replace('\r', '') for n in P19}
    # T-22 replaces W4 and W5 (K6, K8) and takes W25's section off case-reels (K3); for those three
    # lines, T-21's own page is read from git (trip/T-21's last commit).
    T22_DONE = {'W4', 'W5', 'W25'}
    git21 = lambda f: _sp18.run(['git', 'show', 'a0c77c98a2213a618efd2e2831d03fae424963c4:' + f], cwd=here, capture_output=True).stdout.decode('utf-8').replace('\r', '')
    # T-24 A1 replaces W29's line (the mainframe lead-in); for that line, T-23's own page is read from git
    # (origin/main at 78bf1e6, the base T-24 was cut from). The T-24 block checks A1.
    T24_DONE = {'W29'}
    git23 = lambda f: _sp18.run(['git', 'show', '78bf1e632a752b8ea9ef89536e342bcf9ed90758:' + f], cwd=here, capture_output=True).stdout.decode('utf-8').replace('\r', '')
    for wid, n, old, new, _o, _n in W19:
        t = words19(git21(n + '.html') if wid in T22_DONE else git23(n + '.html') if wid in T24_DONE else src19[n])
        check(f'T-19 {wid}: {n} has the new line exactly once', t.count(new) == 1, str(t.count(new)))
        if old in new:
            check(f'T-19 {wid}: on {n} the old words are only inside the new line', t.count(old) == 1, str(t.count(old)))
        else:
            check(f'T-19 {wid}: the old line is gone from {n}', t.count(old) == 0, str(t.count(old)))
    check('T-19 W10: the script puts back the new label after a send that fails', "btn.textContent = 'Send my answers →';" in src19['start']
          and 'Start my Blueprint' not in src19['start'])
    for n in P19:
        check(f'T-19: no em dash on {n}', '—' not in src19[n])

    # Nothing else changed: the T-18 page with only these lines swapped is the new page, byte for byte
    # (the Studio build stamp aside: it is a hash of studio.json, which holds W26 and W27).
    STAMP = lambda s: _re.sub(r'<!-- studio\.py [^>]* -->', '<!-- studio.py -->', s)
    # T-20 changes every page, so T-19's own pages are read from git at its last commit.
    git19 = lambda f: _sp18.run(['git', 'show', 'cbaa0d86e85b7033c9e9c76dc704ab77a415c556:' + f], cwd=here, capture_output=True).stdout.decode('utf-8').replace('\r', '')
    for n in P19:
        was = t18_file(n + '.html').decode('utf-8').replace('\r', '')
        miss = []
        for wid, n_, old, new, o_raw, n_raw in W19 + W19_SCRIPT:
            if n_ != n:
                continue
            o, nw = o_raw or old, n_raw or new
            if was.count(o) != 1:
                miss.append(f'{wid}: {was.count(o)} matches')
                continue
            was = was.replace(o, nw)
        a, b_ = STAMP(was), STAMP(git19(n + '.html'))
        i = next((k for k in range(min(len(a), len(b_))) if a[k] != b_[k]), min(len(a), len(b_)))
        check(f'T-19: {n} differs from T-18 only by its lines in this item (T-19\'s page, read from git)', not miss and a == b_, str(miss) + ' first difference: ' + repr(b_[max(0, i - 60):i + 60]))
    for f in ('scaler.html', 'comp3.html', '404.html', 'studio-birdleague.html', 'studio-deepcuts.html', 'sitemap.xml', 'robots.txt'):
        now_ = git19(f)   # T-20 changes these too, so T-19's own files are read from git
        check(f'T-19: {f} is as it was at T-18 (the Studio build stamp aside; T-19\'s file, read from git)', STAMP(now_) == STAMP(t18_file(f).decode('utf-8').replace('\r', '')))

    # Accessible names follow the new words; names that point at the old ones are gone.
    q = newpage(1440); q.goto(BASE + 'start.html'); q.wait_for_timeout(300)
    check('T-19 W8: step 4 is named by its new heading', q.get_by_role('region', name='Who says yes to spending money, and when?', exact=True).count() == 1)
    check('T-19 W9: the day choices are named by the new heading', q.get_by_role('group', name='Good days for my first visit', exact=True).count() == 1)
    check('T-19 W10: the send button is named "Send my answers →"', q.get_by_role('button', name='Send my answers →', exact=True).count() == 1)
    q.route('**/dj-intake.stephens-josef.workers.dev/**', lambda r: r.fulfill(status=502, content_type='application/json', body='{"ok":false}', headers={'Access-Control-Allow-Origin': '*'}))
    q.locator('.chips[data-key="pile"] .chip').first.click()
    q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com')
    q.click('#bp-send'); q.wait_for_timeout(600)
    check('T-19 W10: after a send that fails, the button says "Send my answers →" again', q.inner_text('#bp-send').strip() == 'Send my answers →'
          and q.locator('#bp-err').is_visible(), q.inner_text('#bp-send'))
    q = newpage(1440); q.goto(BASE + 'captions.html'); q.wait_for_timeout(300)
    check('T-19 W18: the box choices are named "Box behind the words", with the same three choices',
          q.get_by_role('group', name='Box behind the words', exact=True, include_hidden=True).count() == 1
          and q.locator('#c-box .chip').all_text_contents() == ['Dark box', 'Light box', 'No box'])
    q = newpage(1440); q.goto(BASE + 'briefing.html'); q.wait_for_timeout(300)
    check('T-19 W33: the programs field is named by its new label', q.get_by_role('textbox', name='Which programs (a rough description is enough)', exact=True).evaluate('e => e.id') == 'family')
    check('T-19 W33: "Which programs" still finds the same field', q.get_by_label('Which programs').evaluate('e => e.id') == 'family')
    check('T-19 W32: the briefing form\'s own send button is untouched', q.inner_text('#br-send').strip() == 'Send the request →')

    # Every form still sends exactly what it sent at T-18 (the Worker intercepted, nothing leaves).
    def sent18(base_, name, fill, btn, done):
        q = newpage(1440) if base_ == BASE else t18_page(1440)
        got = []
        def grab(route):
            if route.request.method == 'POST':
                got.append(_json.loads(route.request.post_data or '{}'))
            route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
        q.route('**/dj-intake.stephens-josef.workers.dev/**', grab)
        q.goto(base_ + name + '.html'); settle(q)
        fill(q); q.click(btn); q.wait_for_timeout(700)
        for g in got:
            g.pop('ms', None)
        return got, q.locator(done).is_visible()
    for name, fill, btn, done in (('start', fill_start, '#bp-send', '#bp-done'), ('call', fill_call, '#cl-send', '#cl-done'), ('briefing', fill_brief, '#br-send', '#br-done')):
        a, b_ = sent18(BASE, name, fill, btn, done), sent18(OLD18, name, fill, btn, done)
        check(f'T-19: {name} still sends, and sends exactly what it sent at T-18', a == b_ and len(a[0]) == 1 and a[1], str(a)[:300] + ' | ' + str(b_)[:300])

    # Same input, same result, against T-18: two inputs per changed tool.
    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')]):
        def shot18(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT_JS); r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both18('shotlist', shot18)
        check(f'T-19: shot list gives the same clips, stops, countdown and copy as T-18 for {picks or "the defaults"} (T-20 F1: the offer is gone)', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    cp = grab_copy(q, '#copy')
    check('T-19 W13 to W15: the copied shot list repeats none of the old lines', not any(w[2] in cp for w in W19 if w[1] == 'shotlist'))
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-19 W13 to W15: printed, the shot list shows the new lines', all(q.get_by_text(w[3], exact=True).is_visible() for w in W19 if w[1] == 'shotlist'))
    q.emulate_media(media='screen')
    for text, picks, secs in CAP_IN[:2]:
        def cap18(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks)
            if secs:
                set_val(q, '#secs', secs)
            q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS); r['copy'] = grab_copy(q, '#copy'); r['verdict'] = q.inner_text('#verdict')
            return r
        a, b_ = both18('captions', cap18)
        check(f'T-19: caption fitter gives the same verdict, checks, preview and copy as T-18 for {(text or "the default")[:24]} {picks}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for args in (([], None, False), ([4, 11], '45', False)):
        a, b_ = both18('receipt', rec_in(*args))
        check(f'T-19: receipt gives the same lines, totals, hand-off and copy as T-18 for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]))

    def checkup_live(q, base_):
        def page_route(route, request=None, base_=base_):   # T-19: Playwright hands a second argument (the request) to a two-argument handler
            body = route.fetch().text() if base_ == BASE else t18_file('checkup.html').decode('utf-8')
            route.fulfill(status=200, content_type='text/html', body=body.replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1))
        q.route(base_ + 'checkup.html', page_route)
    W22_24 = [(w[3], w[2]) for w in W19 if w[0] in ('W22', 'W23', 'W24')]
    for ans in (SAMPLE, thin):
        res = []
        for base_, pgf in ((BASE, lambda: newpage(1440)), (OLD18, lambda: t18_page(1440))):
            q = pgf(); checkup_live(q, base_)
            q.route('https://dj-checkup.test/**', worker_(ans))
            q.goto(base_ + 'checkup.html'); q.wait_for_timeout(400)
            q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            r2 = q.inner_text('#rep2')
            if base_ == BASE:
                for new, old in W22_24:   # the three lines of this item read back as they were; everything else must match
                    r2 = r2.replace(new, old, 1)
            res.append([q.inner_text('#msg'), q.inner_text('#rep1'), q.inner_text('#stat'), r2])
        check(f'T-19: checkup gives the same report as T-18 for {"a thin page" if ans is thin else "the sample"}, only the three lines changed', res[0] == res[1] and any(res[0]))

    # The look: each new line sits inside its own box at 320, 390 and 1440, nothing spills, no sideways scroll.
    # (Titles and labels set in capitals read back in capitals, so the match ignores case. W11 is in the
    # panel that shows after a send, so the start form is sent, to an intercepted Worker, before W11.)
    FIT_JS = '''(line) => {
      const norm = s => s.replace(/\\s+/g, ' ').trim();
      const els = [...document.querySelectorAll('body *')].filter(e => {
        const d = getComputedStyle(e).display; const r = e.getBoundingClientRect();
        return d !== 'inline' && d !== 'contents' && r.width > 0 && r.height > 0 && norm(e.innerText || '').toLowerCase().includes(line.toLowerCase()); });
      if (!els.length) return null;
      els.sort((a, b) => a.innerText.length - b.innerText.length);
      const e = els[0], r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
      const kids = [...e.querySelectorAll('*')].map(k => k.getBoundingClientRect()).filter(k => k.width > 0);
      return {spill: e.scrollWidth - e.clientWidth, inParent: r.left >= p.left - 1 && r.right <= p.right + 1,
              kidsIn: kids.every(k => k.left >= r.left - 1 && k.right <= r.right + 1), w: Math.round(r.width), h: Math.round(r.height)};
    }'''
    for n in P19:
        for w in (320, 390, 1440):
            q = newpage(w)
            if n == 'checkup':
                checkup_live(q, BASE)
                q.route('https://dj-checkup.test/**', lambda route: route.fulfill(status=200, content_type='application/json', body=_json.dumps(SAMPLE), headers={'Access-Control-Allow-Origin': '*'}))
            if n == 'start':
                q.route('**/dj-intake.stephens-josef.workers.dev/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'}))
            q.goto(BASE + n + '.html'); settle(q)
            if n == 'checkup':
                q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            q.evaluate("document.querySelectorAll('.fold[aria-expanded=false]').forEach(b => b.click())"); q.wait_for_timeout(150)
            for wid, n_, old, new, _o, _n in W19:
                if n_ != n:
                    continue
                # T-22: W4, W5 and W25 are replaced by K6's and K8's headlines and K3's paragraph; the same fit check runs on those.
                new = {'W4': 'An evening of editing, now about 4 minutes.', 'W5': 'Their recipe cards, now an app.',
                       'W25': 'She films the class on her phone.',
                       'W29': 'The code never divides by 100, and the field fits 3.5% stored either way. See each one:'}.get(wid, new)   # T-24 A1 replaces W29
                if wid == 'W11':
                    fill_start(q); q.click('#bp-send'); q.wait_for_timeout(700)
                f_ = q.evaluate(FIT_JS, new)
                check(f'T-19 {wid}: on {n} at {w} the new line sits inside its box', f_ is not None and f_['spill'] <= 0 and f_['inParent'] and f_['kidsIn'], str(f_))
            if w < 1440:
                sw = q.evaluate('document.documentElement.scrollWidth')
                check(f'T-19: {n} has no sideways scroll at {w}', sw <= w, str(sw))


# ---------------- T-20: walk fixes 01 (F1 to F9), Nov 15, 2026
@section('T-20')
def s_t_20():
    # Comparisons are against origin/main before this item (T-19's last commit), read straight from git.
    T19 = 'cbaa0d86e85b7033c9e9c76dc704ab77a415c556'
    T19_FILES = {}

    def t19_file(path):
        if path not in T19_FILES:
            r = _sp18.run(['git', 'show', f'{T19}:{path}'], cwd=here, capture_output=True)
            T19_FILES[path] = r.stdout if r.returncode == 0 else None
        return T19_FILES[path]

    def t19_page(w, h=900):
        """A page that can open the T-19 build at BASE + '__t19/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t19/', 1)[1].split('?')[0].split('#')[0]
            body = t19_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t19/**', serve)
        return q
    OLD19 = BASE + '__t19/'
    check('T-20: the T-19 pages can be read from git for comparison', t19_file('index.html') is not None and t19_file('sitemap.xml') is not None)

    def both19(name, fn, w=1440):
        out_ = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD19, lambda: t19_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    SRC20 = {n: un26(urlopen(BASE + n).read().decode('utf-8'), n) for n in ALL_HTML}   # T-26: the gallery out (its block checks it; "November 2026" holds "November 20")
    WRAP20 = _chrome20.WRAP_CSS

    # F1: the free-reel offer is gone; the countdown stays. (The words are put together here, so a
    # search of the repository for them finds no copy in this file.)
    OFFER_WORDS = ['three ' + 'reels', 'free ' + 'reel', 'Claim a ' + 'free ' + 'reel', 'November ' + '20', 'Want it edited ' + 'for free']
    for n in ALL_HTML:
        low = SRC20[n].lower()
        check(f'T-20 F1: {n} carries none of the offer\'s words', not any(w.lower() in low for w in OFFER_WORDS), str([w for w in OFFER_WORDS if w.lower() in low]))
    sl = SRC20['shotlist.html']
    check('T-20 F1: the shot list has no offer block, no offer styles and no offer date check',
          'id="offer"' not in sl and '.offer' not in sl and 'new Date(2026,10,20' not in sl and 'Free%20reel' not in sl)
    for day, expect in (('2026-11-15T10:00:00', '13 days'), ('2026-10-17T10:00:00', '42 days'), ('2026-11-28T10:00:00', 'Today'), ('2026-10-16T10:00:00', None)):
        q = newpage(390)
        q.clock.set_fixed_time(day)
        q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
        shown = q.locator('#when').is_visible()
        if expect:
            check(f'T-20 F1: the countdown still shows inside its 42-day window ({day[:10]}: {expect})', shown and q.inner_text('#days').strip() == expect
                  and 'Small Business Saturday' in q.inner_text('#dayslabel'), q.inner_text('#when'))
        else:
            check(f'T-20 F1: the countdown stays hidden outside its window ({day[:10]})', not shown)
        check(f'T-20 F1: no offer on the shot list on {day[:10]}', q.locator('#offer, .offer').count() == 0)
    q = newpage(390); q.clock.set_fixed_time('2026-11-15T10:00:00'); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    click_chips(q, [('type', 'nonprofit')]); q.wait_for_timeout(80)
    check('T-20 F1: nonprofits still count down to Giving Tuesday', q.inner_text('#days').strip() == '16 days' and 'Giving Tuesday' in q.inner_text('#dayslabel'), q.inner_text('#when'))

    # F2: no links to the checkup while CHECKUP_URL is empty; it all comes back once it is set.
    check('T-20 F2: CHECKUP_URL is still empty in checkup.py', "\nvar CHECKUP_URL = '';" in ck_src and _chrome20.checkup_url() == '')
    for n in ALL_HTML:
        if n != 'checkup.html':
            check(f'T-20 F2: {n} does not link to or list the checkup while it isn\'t live', 'checkup.html' not in SRC20[n] and 'Website checkup' not in SRC20[n])
    sm = urlopen(BASE + 'sitemap.xml').read().decode('utf-8')
    check('T-20 F2: checkup.html is not in sitemap.xml while it isn\'t live', 'checkup.html' not in sm and sm.count('<url>') == t19_file('sitemap.xml').decode('utf-8').count('<url>') - 1)
    old_ck = t19_file('checkup.html').decode('utf-8').replace('\r\n', '\n')
    new_ck = un21(un23(un33(un34(SRC20['checkup.html'], 'checkup.html'), 'checkup.html'), 'checkup.html')).replace('\r\n', '\n').replace(WRAP20 + '\n', '', 1).replace('#0E1A17', '#0E1B17')   # T-21: line-breaking spans out; T-33: R20's row order out
    check('T-20 F2: checkup.html itself is unchanged (apart from the wrapping rules and the darker button text)', new_ck == old_ck,
          next((f'...{old_ck[max(0, i - 80):i + 80]}... | ...{new_ck[max(0, i - 80):i + 80]}...' for i in range(min(len(old_ck), len(new_ck))) if old_ck[i] != new_ck[i]), f'{len(old_ck)} vs {len(new_ck)}'))   # T-33: the first difference, when there is one
    check('T-20 F2: checkup.html still says "Coming this week"', '>Coming this week<' in SRC20['checkup.html'])
    WORK_CARD = r'\n    <article class="card" data-k="free">(?:(?!</article>).)*?href="checkup\.html".*?</article>'
    TOOLS_SEC = r'<section id="tools".*?</section>'
    MORE = r'<p class="noprint"[^>]*>More free tools: .*?</p>'
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        fp = os.path.join(bd, 'tools', 'checkup.py')
        open(fp, 'w', encoding='utf-8').write(ck_src.replace("\nvar CHECKUP_URL = '';", "\nvar CHECKUP_URL = 'https://dj-checkup.example.test/';", 1))
        steps = [([sys.executable, t + '.py', '..'], os.path.join(bd, 'tools')) for t in ('shotlist', 'captions', 'receipt', 'scaler', 'checkup', 'studio')]
        steps += [(st, bd) for st in (['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'],
                                      [sys.executable, 'enhance.py', 'out'], [sys.executable, 'plain.py', 'out'], [sys.executable, 'intent.py', 'out'],
                                      [sys.executable, 'voice2.py', 'out'], [sys.executable, 'final.py', 'out'])]
        built = True
        for st, cwd_ in steps:
            r = _sp18.run(st, cwd=cwd_, capture_output=True, text=True)
            if r.returncode:
                built = False
                check('T-20 F2: the temp build with a checkup address runs', False, ' '.join(st[1:2]) + ': ' + (r.stdout + r.stderr)[-300:])
                break
        if built:
            outd = os.path.join(bd, 'out')
            rd = lambda f: un21(un23(un30(open(os.path.join(outd, f), encoding='utf-8').read(), f), f))   # T-21: line-breaking spans out; T-23: its changes out; T-30: the descriptions back
            old = lambda f: t19_file(f).decode('utf-8')
            check('T-20 F2 (address set): the work page card comes back exactly as before',
                  _re.findall(WORK_CARD, rd('work.html'), _re.S) == _re.findall(WORK_CARD, old('work.html'), _re.S) and len(_re.findall(WORK_CARD, rd('work.html'), _re.S)) == 1)
            check('T-20 F2 (address set): the local.html free tools section comes back exactly as before',
                  _re.findall(TOOLS_SEC, rd('local.html'), _re.S) == _re.findall(TOOLS_SEC, old('local.html'), _re.S) and 'checkup.html' in rd('local.html'))
            for t in ('shotlist', 'captions', 'receipt', 'scaler', 'checkup'):
                check(f'T-20 F2 (address set): {t}.html\'s "More free tools" line comes back exactly as before',
                      _re.findall(MORE, rd(t + '.html'), _re.S) == _re.findall(MORE, old(t + '.html'), _re.S))
            check('T-20 F2 (address set): the sitemap line comes back, the sitemap exactly as before', rd('sitemap.xml') == old('sitemap.xml'))
            links = sorted(f for f in os.listdir(outd) if f.endswith('.html') and 'checkup.html' in rd(f) and f != 'checkup.html')
            check('T-20 F2 (address set): the same pages link to the checkup as before',
                  links == ['captions.html', 'local.html', 'receipt.html', 'scaler.html', 'shotlist.html', 'work.html'], str(links))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)
    check('T-20 F2: the temp copy is gone, and the real checkup.py still has no address',
          not os.path.exists(tmp) and "\nvar CHECKUP_URL = '';" in open(os.path.join(here, 'tools', 'checkup.py'), encoding='utf-8').read())

    # F3 and F4: the three word changes, each on its page exactly once, the old words gone.
    mf, br = SRC20['mainframe.html'], SRC20['briefing.html']
    q = newpage(1440); q.goto(BASE + 'mainframe.html'); settle(q)
    check('T-20 F3: "Comparing the code, line by line" is on the Mainframe page once', q.inner_text('main').count('Comparing the code, line by line') == 1)
    check('T-20 F3: the old "Caught by" value is gone from the page and from every tab state', 'Comparing the output, not reading the code' not in mf and 'not reading the code' not in mf)
    check('T-20 F3: the tab state data carries the new value', '"Caught by", "v": "Comparing the code, line by line"' in mf)
    q.click('[role=tab][data-ex="c"]'); q.wait_for_timeout(100); q.click('[role=tab][data-ex="b"]'); q.wait_for_timeout(100)
    check('T-20 F3: back on Exhibit B, the row reads the new value', 'Caught by\nComparing the code, line by line' in q.inner_text('#xb-panel').replace('\t', '\n'), q.inner_text('#xb-panel')[-200:])
    hero = q.locator('a.seal')
    check('T-20 F4: the hero button reads "Tell me about one program" and still points to #correspondence',
          hero.count() == 1 and hero.inner_text().strip() == 'Tell me about one program' and hero.get_attribute('href') == '#correspondence')
    check('T-20 F4: "Tell me about one program" as a button once, "Send one program" gone', mf.count('>Tell me about one program</a>') == 1 and 'Send one program' not in mf)
    old_br = t19_file('briefing.html').decode('utf-8')
    check('T-20 F4: the briefing placeholder reads "For example: deposit interest", once', br.count('placeholder="For example: deposit interest"') == 1 and 'month-end batch' not in br)
    check('T-20 F4: the other briefing placeholder is untouched',
          [p for p in _re.findall(r'placeholder="([^"]*)"', br) if not p.startswith('For example')] == [p for p in _re.findall(r'placeholder="([^"]*)"', old_br) if not p.startswith('For example')])

    # F9 landmarks, F5 wrapping: one <main> and one copy of the wrapping rules on every page.
    for n in ALL_HTML:
        check(f'T-20 F9: {n} has exactly one <main>', len(_re.findall(r'<main[\s>]', SRC20[n])) == 1)
        check(f'T-20 F5: {n} carries the wrapping rules exactly once', SRC20[n].count(WRAP20) == 1)
    for n in ('index.html', '404.html'):
        q = newpage(390); q.goto(BASE + n); settle(q)
        loose = q.evaluate('''() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let t; while ((t = w.nextNode())) { if (!t.data.trim()) continue; const e = t.parentElement; if (!e || e.closest('script,style')) continue;
            if (!e.getClientRects().length) continue; if (!e.closest('header,nav,main,footer,aside,section[aria-label],section[aria-labelledby],[role]')) out.push(t.data.trim()) } return out }''')
        check(f'T-20 F9: no visible text on {n} sits outside a landmark', loose == [], str(loose)[:200])
    check('T-20 F9: the exhibit panel is a div carrying role="tabpanel"', '<div id="xb-panel" role="tabpanel"' in mf and '<article id="xb-panel"' not in mf)

    # F9 tabs: tap and keyboard work exactly as before.
    def tabs_seq(q):
        res = []
        q.click('[role=tab][data-ex="c"]'); q.wait_for_timeout(80)
        res.append([q.inner_text('#xb-title'), q.inner_text('#xb-rows'), q.locator('[role=tab][aria-selected=true]').get_attribute('data-ex')])
        q.focus('[role=tab][data-ex="d"]'); q.keyboard.press('Enter'); q.wait_for_timeout(80)
        res.append([q.inner_text('#xb-title'), q.inner_text('#xb-rows'), q.locator('[role=tab][aria-selected=true]').get_attribute('data-ex')])
        q.focus('[role=tab][data-ex="b"]'); q.keyboard.press('Space'); q.wait_for_timeout(80)
        res.append([q.inner_text('#xb-title'), q.locator('[role=tab][aria-selected=true]').get_attribute('data-ex')])
        q.keyboard.press('ArrowRight'); q.wait_for_timeout(80)
        res.append([q.inner_text('#xb-title'), q.evaluate('document.activeElement.dataset.ex || document.activeElement.tagName')])
        return res
    a, b_ = both19('mainframe', tabs_seq)
    check('T-20 F9: the exhibit tabs work by tap and keyboard exactly as before (F3\'s value aside)',
          _json.dumps(a).replace('Comparing the code, line by line', 'X') == _json.dumps(b_).replace('Comparing the output, not reading the code', 'X'), str(a)[:200] + ' | ' + str(b_)[:200])

    # F9 contrast: the darker text colors are in place.
    q = newpage(1440); q.goto(BASE + 'local.html'); settle(q)
    check('T-20 F9: the orange "Start a Blueprint" button text is #0E1A17', q.evaluate("getComputedStyle([...document.querySelectorAll('a.btn-blaze')].find(a => a.textContent.includes('Start a Blueprint'))).color") == 'rgb(14, 26, 23)')
    q = newpage(1440); q.goto(BASE + 'scaler.html'); settle(q)
    check('T-20 F9: the struck-through "was" amounts are #6F736D', q.evaluate("getComputedStyle(document.querySelector('.was')).color") == 'rgb(111, 115, 109)')
    for n in ('studio', 'studio-birdleague', 'studio-deepcuts'):
        q = newpage(1440); q.goto(BASE + n + '.html'); settle(q)
        check(f'T-20 F9: the dates on {n} are #676D66', q.evaluate("getComputedStyle(document.querySelector('.log time')).color") == 'rgb(103, 109, 102)')

    # No sideways scroll at 320, 390 and 1440 on every page.
    for n in ALL_HTML:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + n); settle(q)
            sw = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-20: {n} has no sideways scroll at {w}', sw <= w, str(sw))
            q.close()

    # F6: the Mainframe layout.
    for w in (320, 390, 640):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q)
        r = q.evaluate('''() => { const L = e => { const b = e.getBoundingClientRect(), s = getComputedStyle(e); return Math.round(b.left + parseFloat(s.paddingLeft)) };
            const stats = [...document.querySelectorAll('.t20-stats > div')], steps = [...document.querySelectorAll('.t20-steps > li')];
            return {lefts: [...stats, ...steps].map(L), rights: [...stats, ...steps].map(e => getComputedStyle(e).borderRightWidth),
                    tops: [...stats.slice(1), ...steps.slice(1)].map(e => getComputedStyle(e).borderTopWidth),
                    widths: [...stats, ...steps].map(e => Math.round(e.getBoundingClientRect().width)), pw: Math.round(stats[0].parentElement.getBoundingClientRect().width),
                    sw: Math.round(steps[0].parentElement.getBoundingClientRect().width)} }''')
        check(f'T-20 F6: at {w} the stats and the four steps share one left edge', len(set(r['lefts'])) == 1, str(r['lefts']))
        check(f'T-20 F6: at {w} no stat or step has a side rule, and each divider runs the full width',
              set(r['rights']) == {'0px'} and set(r['tops']) == {'1px'} and set(r['widths'][:3]) == {r['pw']} and set(r['widths'][3:]) == {r['sw']}, str(r))
        pre = q.evaluate("(() => { const p = document.querySelector('.t20-code'); return [p.scrollWidth, p.clientWidth] })()")
        check(f'T-20 F6: at {w} every Exhibit A code line shows in full', pre[0] <= pre[1], str(pre))
    for w in (320, 390, 768, 1024, 1440):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q)
        hs = q.evaluate("[...document.querySelectorAll('.t20-read button')].map(b => Math.round(b.getBoundingClientRect().height))")
        check(f'T-20 F6: at {w} the two Exhibit A reading buttons are the same height', len(hs) == 2 and hs[0] == hs[1], str(hs))
        sel = q.evaluate("[...document.querySelectorAll('.t20-read button')].map(b => [b.textContent, b.getAttribute('aria-pressed'), getComputedStyle(b).backgroundColor])")
        # T-24 A2, A3: the buttons now read "Stored as 0.035" and "Stored as 3.5" (were "A fraction" and "A percentage").
        check(f'T-20 F6: at {w} "Stored as 3.5" starts selected, filled dark, and "Stored as 0.035" is a plain outline',
              sel == [['Stored as 0.035', 'false', 'rgba(0, 0, 0, 0)'], ['Stored as 3.5', 'true', 'rgb(18, 22, 31)']], str(sel))
    q = newpage(1440); q.goto(BASE + 'mainframe.html'); settle(q)
    tops = q.evaluate("[...document.querySelectorAll('.t20-steps > li > p:last-child')].map(p => Math.round(p.getBoundingClientRect().top))")
    check('T-20 F6: at 1440 step IV\'s divider and price line sit level with I to III', len(tops) == 4 and len(set(tops)) == 1, str(tops))
    v = q.evaluate("(() => { const g = document.querySelector('.t20-voices'); return [Math.round(g.children[0].getBoundingClientRect().top), Math.round(g.children[1].getBoundingClientRect().top)] })()")
    check('T-20 F6: at 1440 the text beside the third section\'s heading sits at its top', abs(v[1] - v[0]) < 24, str(v))
    gap = q.evaluate("(() => { const a = document.getElementById('s4').querySelector(':scope > div'), s5 = document.getElementById('s5'); const last = [...a.children].reduce((m, c) => Math.max(m, c.getBoundingClientRect().bottom), 0); return Math.round(s5.querySelector('h2').getBoundingClientRect().top - last) })()")
    check('T-20 F6: at 1440 the gap above "What this does not prove" is a normal section gap', gap < 200, str(gap))

    # F7: the tools.
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'receipt.html'); settle(q)
        r = q.evaluate('''() => { const used = document.querySelector('.chip.used'), free = document.querySelector('#presets .chip:not(.used)'), s = getComputedStyle(used), f = getComputedStyle(free);
            return {used: [s.opacity, s.backgroundColor, s.color, getComputedStyle(used, '::before').borderBottomWidth, used.getAttribute('aria-disabled')],
                    free: [f.opacity, f.backgroundColor, f.borderTopStyle, free.hasAttribute('aria-disabled')],
                    add: document.getElementById('addown').parentElement === document.getElementById('presets').parentElement && document.getElementById('addown').parentElement.classList.contains('chips'),
                    rate: document.getElementById('addown').parentElement.contains(document.getElementById('rate'))} }''')
        check(f'T-20 F7: at {w} chores on the receipt look chosen (filled, a CSS check mark), never faded',
              r['used'] == ['1', 'rgb(22, 32, 28)', 'rgb(242, 237, 225)', '2px', 'true'], str(r['used']))
        check(f'T-20 F7: at {w} chores not chosen are plain outlines', r['free'] == ['1', 'rgba(0, 0, 0, 0)', 'solid', False], str(r['free']))
        check(f'T-20 F7: at {w} "+ Something else" sits in the chore group, not beside the hourly rate', r['add'] and not r['rate'])
        check(f'T-20 F7: at {w} no receipt note is blue or purple',
              q.evaluate("[...document.querySelectorAll('[class^=t-]')].map(e => getComputedStyle(e).color).filter(c => ['rgb(31, 79, 168)', 'rgb(122, 79, 176)'].includes(c)).length") == 0)
    q = newpage(390); q.goto(BASE + 'receipt.html'); settle(q)
    before_ = q.evaluate("[...document.querySelectorAll('[data-p]')].map(c => c.getAttribute('aria-disabled'))")
    q.evaluate("document.querySelector('[data-p=\"1\"]').click()"); q.wait_for_timeout(80)
    after_ = q.evaluate("[...document.querySelectorAll('[data-p]')].map(c => c.getAttribute('aria-disabled'))")
    check('T-20 F7: tapping a chore marks it chosen as before (aria-disabled), and it lands on the receipt',
          before_[1] is None and after_[1] == 'true' and 'Booking and rescheduling' in q.inner_text('#paper'))
    for w in (390, 1440):
        q = newpage(w, 844); q.goto(BASE + 'captions.html'); settle(q); q.wait_for_timeout(300)
        check(f'T-20 F7: at {w} the sample caption passes on first load', q.inner_text('#verdict').strip() == 'Good to go. It fits, and people can read it in time.'
              and q.input_value('#secs') == '7.5', q.inner_text('#verdict') + ' ' + q.input_value('#secs'))
        lb, vb = q.locator('.a-len').bounding_box(), q.locator('#verdict').bounding_box()
        check(f'T-20 F7: at {w} the clip length sits directly above the verdict', 0 <= vb['y'] - (lb['y'] + lb['height']) <= 32, f'{lb} {vb}')
    q = newpage(390); q.goto(BASE + 'captions.html'); settle(q)
    set_val(q, '#secs', '7'); q.wait_for_timeout(200)
    check('T-20 F7: 7.5 is the shortest choice at which the sample passes (7 fails)', q.inner_text('#verdict').strip().startswith('Too long for this clip.'))
    for w in (320, 390, 560, 561, 1440):
        q = newpage(w); q.goto(BASE + 'scaler.html'); settle(q)
        bots = q.evaluate("[...document.querySelectorAll('.who input')].map(i => Math.round(i.getBoundingClientRect().bottom))")
        check(f'T-20 F7: at {w} the three scaler inputs line up along their bottom edge', len(bots) == 3 and len(set(bots)) == 1, str(bots))
        hd = q.evaluate("Math.round(document.querySelector('thead tr').getBoundingClientRect().height)")
        three = q.evaluate("(() => { const c = document.querySelector('#out tr').children; return c[0].getBoundingClientRect().top === c[1].getBoundingClientRect().top && c[1].getBoundingClientRect().top === c[2].getBoundingClientRect().top })()")
        check(f'T-20 F7: at {w} the column headers show only where the rows show three columns', (hd > 4) == three, f'{hd} {three}')
        butter = q.evaluate("(() => { const r = [...document.querySelectorAll('#out tr')].find(r => r.textContent.includes('butter')); return Math.abs(r.children[0].getBoundingClientRect().top - r.children[1].getBoundingClientRect().top) })()")
        check(f'T-20 F7: at {w} "butter, for the pan" stays beside its amount', butter < 6, str(butter))
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'start.html'); settle(q)
        r = q.evaluate('''() => { const c = [...document.querySelectorAll('.chips[data-key="days"] .chip')], B = e => e.getBoundingClientRect();
            const fri = c.find(e => e.textContent === 'Friday'), mor = c.find(e => e.textContent === 'Mornings'), aft = c.find(e => e.textContent === 'Afternoons');
            return [B(mor).top >= B(fri).bottom, Math.round(B(mor).left) === Math.round(B(c[0]).left), Math.round(B(mor).top) === Math.round(B(aft).top), c.map(e => e.className)] }''')
        check(f'T-20 F7: at {w} Mornings and Afternoons sit on their own row under the weekdays', r[0] and r[1] and r[2] and set(r[3]) == {'chip'}, str(r))
    q = newpage(320); q.goto(BASE + 'start.html'); settle(q)
    pads = q.evaluate('''[...document.querySelectorAll('.chip')].filter(c => c.getBoundingClientRect().height > 56).map(c => { const b = c.getBoundingClientRect(), r = document.createRange(); r.selectNodeContents(c); const t = r.getBoundingClientRect(); return [Math.round(t.top - b.top), Math.round(b.bottom - t.bottom)] })''')
    check('T-20 F7: at 320 two-line start chips grow, with even padding and no text touching a border', all(a_ > 6 and b2 > 6 and abs(a_ - b2) <= 2 for a_, b2 in pads), str(pads))

    # F8: other layout.
    q = newpage(320); q.goto(BASE + 'local.html'); settle(q)
    r = q.evaluate('''() => { const h = document.querySelector('.tear > div'), a = h.children[0].getBoundingClientRect(), b = h.children[1].getBoundingClientRect();
        const lh = parseFloat(getComputedStyle(document.querySelector('#rc-rows span')).lineHeight);
        return {stack: b.top >= a.bottom - 1, one: [a.height, b.height], lh: lh,
                rows: [...document.querySelectorAll('#rc-rows > div')].map(d => Math.round(d.getBoundingClientRect().height - parseFloat(getComputedStyle(d).paddingTop) - parseFloat(getComputedStyle(d).paddingBottom))),
                tabs: [...document.querySelectorAll('[aria-label="Receipts"] > button')].map(t => [Math.round(t.getBoundingClientRect().top), Math.round(t.getBoundingClientRect().width)]),
                tw: Math.round(document.querySelector('[aria-label="Receipts"]').getBoundingClientRect().width)} }''')
    check('T-20 F8: local at 320, the receipt card\'s labels sit above each other, each on one line', r['stack'] and max(r['one']) < 26, str(r['one']))
    # T-22 K4: the hero card has four rows. T-33 R4: still four; they are the card's second block now (no line above them).
    below = q.evaluate("[...document.querySelectorAll('.tear > div:nth-child(2) > div')].map(d => Math.round(d.lastElementChild.getBoundingClientRect().top - d.firstElementChild.getBoundingClientRect().bottom))")
    check('T-20 F8: local at 320, each receipt card label sits above its number', len(below) == 4 and all(x >= -2 for x in below), str(below))
    check('T-20 F8: local at 320, no Results row is taller than three lines', all(h <= 3 * max(r['lh'], 27) + 6 for h in r['rows']), str(r['rows']))
    rows_ = {}
    for top, wdt in r['tabs']:
        rows_[top] = rows_.get(top, 0) + wdt
    check('T-20 F8: local at 320, the tab row wraps evenly (each row fills the width)', all(abs(v - r['tw']) <= 10 + 8 * 2 for v in rows_.values()), str(r['tabs']) + ' ' + str(r['tw']))
    bp = q.evaluate("(() => { const h = document.querySelector('#blueprint h3'), r = document.createRange(); r.selectNodeContents(h); return [r.getClientRects().length, h.scrollWidth <= h.clientWidth + 1] })()")
    check('T-20 F8: local at 320, "$1,500" stays on the line with "THE BLUEPRINT"', bp == [1, True], str(bp))
    q = newpage(320); q.goto(BASE + 'index.html'); settle(q)
    g = q.evaluate("(() => { const bar = document.querySelector('.djm-bar'), logo = bar.children[0], m = bar.querySelector('.djm-btn'); return [Math.round(m.getBoundingClientRect().left - logo.getBoundingClientRect().right), Math.round(m.getBoundingClientRect().top - logo.getBoundingClientRect().top)] })()")
    check('T-20 F8: index at 320, at least 12 px between the logo and Menu, on one row', g[0] >= 12 and abs(g[1]) < 24, str(g))
    c = q.evaluate("(() => { const s = [...document.querySelectorAll('.route span')].find(s => s.textContent.startsWith('Take the Mainframe Route')); return getComputedStyle(s).textAlign })()")
    check('T-20 F8: index, the "Take the Mainframe Route" label is centered when it wraps', c == 'center', c)
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'comp3.html'); settle(q)
        bx = q.evaluate("[...document.querySelectorAll('.bytes .byte')].map(b => [Math.round(b.getBoundingClientRect().left), Math.round(b.getBoundingClientRect().top)])")
        check(f'T-20 F8: comp3 at {w}, the half-byte boxes are 2 by 2', len(bx) == 4 and len({x for x, _ in bx}) == 2 and len({y for _, y in bx}) == 2, str(bx))
    for w in (320, 390, 600, 768, 1024, 1440):
        q = newpage(w); q.goto(BASE + 'case-reels.html'); settle(q)
        r = q.evaluate("(() => { const s = document.querySelector('.stats'), W = s.clientWidth, rows = {}; for (const e of s.children) { const b = e.getBoundingClientRect(); rows[Math.round(b.top)] = (rows[Math.round(b.top)] || 0) + b.width } return [W, Object.values(rows).map(Math.round)] })()")
        check(f'T-20 F8: case-reels at {w}, every stat row is full (no empty cell)', all(abs(v - r[0]) <= 2 for v in r[1]), str(r))
    q = newpage(1440); q.goto(BASE + 'receipt.html'); settle(q)
    r = q.evaluate("(() => { const a = document.querySelector('.a-acts').getBoundingClientRect(), p = document.querySelector('.a-pick').getBoundingClientRect(), r = document.querySelector('.a-paper').getBoundingClientRect(); return [Math.round(a.left - p.left), Math.round(a.top - p.bottom), Math.round(r.bottom - a.bottom)] })()")
    check('T-20 F8: receipt at 1440, the buttons and note sit under the chips, beside the receipt', r[0] == 0 and 0 <= r[1] <= 40, str(r))
    for w in (390,):
        q = newpage(w); q.goto(BASE + 'receipt.html'); settle(q)
        ys = q.evaluate("['.a-pick', '#paper', '#bring', '.a-acts .private'].map(s => Math.round(document.querySelector(s).getBoundingClientRect().top))")
        check(f'T-20 F8: receipt at {w}, the order is still chips, receipt, buttons, note', ys == sorted(ys), str(ys))
    q = newpage(1440); q.goto(BASE + 'studio-birdleague.html'); settle(q)
    r = q.evaluate("(() => { const p = document.querySelector('.top .proof').getBoundingClientRect(), l = document.querySelector('.top #log-h').getBoundingClientRect(), i = document.querySelector('.top img').getBoundingClientRect(); return [Math.round(l.left - p.left), Math.round(l.top - p.bottom), l.right <= i.left] })()")
    check('T-20 F8: Bird League at 1440, its log sits under the proof line, beside the image', r[0] == 0 and 0 < r[1] < 80 and r[2], str(r))
    q = newpage(390); q.goto(BASE + 'studio-birdleague.html'); settle(q)
    ys = q.evaluate("['.top .proof', '.top img', '#log-h', '#join'].map(s => Math.round(document.querySelector(s).getBoundingClientRect().top))")
    check('T-20 F8: Bird League at 390, the order is still proof, image, log, join box', ys == sorted(ys), str(ys))
    q = newpage(1440); q.goto(BASE + 'local.html'); settle(q)
    for sec in ('proof', 'faq'):
        r = q.evaluate(f"(() => {{ const d = document.querySelector('#{sec} > div'), h = d.children[0].getBoundingClientRect(), c = d.children[1].getBoundingClientRect(); return [Math.round(c.top - h.bottom), Math.round(c.left - h.left)] }})()")
        check(f'T-20 F8: local at 1440, the {sec} heading sits above its content, no empty column beside it', 0 <= r[0] <= 48 and r[1] == 0, str(r))

    # Same input, same result as origin/main: two inputs per tool, and every form.
    SHOT20 = SHOT_JS
    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')]):
        def shot20(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT20); r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both19('shotlist', shot20)
        check(f'T-20: shot list gives the same clips, stops, countdown and copy as before for {picks or "the defaults"}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for text, picks, secs in ((None, [], '5'), ('New fall sweaters just landed.', [('size', 'l'), ('pos', 'top'), ('app', 'tiktok')], '2')):
        def cap20(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks); set_val(q, '#secs', secs); q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS); r['copy'] = grab_copy(q, '#copy'); r['verdict'] = q.inner_text('#verdict')
            return r
        a, b_ = both19('captions', cap20)
        check(f'T-20: caption fitter gives the same verdict, checks, preview and copy as before for {(text or "the default")[:24]} at {secs} s', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for args in (([], None, False), ([4, 11], '45', True)):
        a, b_ = both19('receipt', rec_in(*args))
        check(f'T-20: receipt gives the same lines, totals, hand-off and copy as before for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for serves, adults, kids in ((None, None, None), ('6', '10', '0')):
        def sc20(q):
            if serves:
                set_val(q, '#serves', serves); set_val(q, '#adults', adults); set_val(q, '#kids', kids); q.wait_for_timeout(100)
            return [q.inner_text('#fac'), q.inner_text('#facl'), q.inner_text('#warn'), q.evaluate("document.getElementById('out').textContent"), grab_copy(q, '#copy')]
        a, b_ = both19('scaler', sc20)
        check(f'T-20: scaler gives the same amounts and copy as before for {serves or "the defaults"}', a == b_, str(a)[:200] + ' | ' + str(b_)[:200])
    for steps in ([], [('#in', '0350000D'), ('#pic', 'PIC S9(5)V99 COMP-3.')]):
        def dec20(q):
            for sel, val in steps:
                q.fill(sel, val)
            q.wait_for_timeout(150)
            return q.inner_text('#out')
        a, b_ = both19('comp3', dec20)
        a = un24(a)   # T-24 A7: the two result labels read back as T-23's
        check(f'T-20: the decoder gives the same readings as before for {steps or "the opening example"}', a == b_, a[:200] + ' | ' + b_[:200])
    def sent19(base_, name, fill, btn, done):
        q = newpage(1440) if base_ == BASE else t19_page(1440)
        got = []
        def grab(route):
            if route.request.method == 'POST':
                got.append(_json.loads(route.request.post_data or '{}'))
            route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
        q.route('**/dj-intake.stephens-josef.workers.dev/**', grab)
        q.goto(base_ + name + '.html'); settle(q)
        fill(q); q.click(btn); q.wait_for_timeout(700)
        for g in got:
            g.pop('ms', None)
        return got, q.locator(done).is_visible()
    for name, fill, btn, done in (('start', fill_start20, '#bp-send', '#bp-done'), ('call', fill_call, '#cl-send', '#cl-done'), ('briefing', fill_brief, '#br-send', '#br-done')):
        a, b_ = sent19(BASE, name, fill, btn, done), sent19(OLD19, name, fill, btn, done)
        check(f'T-20: {name} still sends, and sends exactly what it sent before', a == b_ and len(a[0]) == 1 and a[1], str(a)[:300] + ' | ' + str(b_)[:300])


# ---------------- T-21: walk fixes 02 (G1 to G6), Nov 16, 2026
@section('T-21')
def s_t_21():
    # Layout and line breaking only. Comparisons are against origin/main before this item
    # (T-20's last commit), read straight from git.
    T20C = '172db8bfed500e4768671108aa28cf546b7df5f9'
    T20_FILES = {}

    def t20_file(path):
        if path not in T20_FILES:
            r = _sp18.run(['git', 'show', f'{T20C}:{path}'], cwd=here, capture_output=True)
            T20_FILES[path] = r.stdout if r.returncode == 0 else None
        return T20_FILES[path]

    def t20_page(w, h=900):
        """A page that can open the T-20 build at BASE + '__t20/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t20/', 1)[1].split('?')[0].split('#')[0]
            body = t20_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t20/**', serve)
        return q
    OLD20 = BASE + '__t20/'
    check('T-21: the T-20 pages can be read from git for comparison', t20_file('index.html') is not None and t20_file('local.html') is not None)

    # T-22 (Nov 16, 2026) changes the words on case-reels, local, work and studio. Where a check below
    # compares words with T-20, those four pages are read as T-21 left them (trip/T-21's last commit,
    # from git), so the check still proves exactly what T-21 changed; the T-22 block checks T-22's lines.
    T22P = ('case-reels.html', 'local.html', 'work.html', 'studio.html')
    T21G = 'a0c77c98a2213a618efd2e2831d03fae424963c4'
    T21G_FILES = {}

    def t21g_file(path):
        if path not in T21G_FILES:
            r = _sp18.run(['git', 'show', f'{T21G}:{path}'], cwd=here, capture_output=True)
            T21G_FILES[path] = r.stdout if r.returncode == 0 else None
        return T21G_FILES[path]

    def t21g_page(w, h=900):
        """A page that can open T-21's own build at BASE + '__t21/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t21/', 1)[1].split('?')[0].split('#')[0]
            body = t21g_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t21/**', serve)
        return q
    NEW21 = BASE + '__t21/'

    def both20(name, fn, w=1440, words=False):
        out_ = []
        cur = (NEW21, lambda: t21g_page(w)) if words and name + '.html' in T22P else (UN30, lambda: newpage(w))   # T-33: its lines out (un30() calls un33())
        for base_, pgf in (cur, (OLD20, lambda: t20_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    SRC21 = {n: un26(un33(un34(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n), n) for n in ALL_HTML}   # git holds LF; T-26: the gallery out (its block checks it); T-33: its lines out
    NW = '<span style="white-space: nowrap">'

    # Every word as it was: each page's text content (after its scripts run), with the new
    # spans out of the way and a no-break space read as a space, matches origin/main.
    for n in ALL_HTML:
        a, b_ = both20(n[:-5], lambda q: q.evaluate(TEXT_JS), words=True)   # T-22: its four pages as T-21 left them
        a = un24(a)   # T-24: A1 to A7 read back as T-23's (the T-24 block checks them)
        if n.startswith('studio'):   # the build-date stamp and the log's day count move with the day the page is built
            a, b_ = (_re.sub(r'\b(?:Nov|Oct|Sep|Aug|Jul) \d{1,2}\b|\b\d+ (?:days?|lines?|things?)\b', '#', x) for x in (a, b_))
        check(f'T-21: {n} reads word for word as on origin/main', a == b_,
              next((f'...{a[max(0, i - 40):i + 40]}... | ...{b_[max(0, i - 40):i + 40]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
    # T-22: case-reels, local, work and studio as T-21 left them, for the checks that compare words with T-20.
    SRC21W = {n: (t21g_file(n).decode('utf-8').replace('\r\n', '\n') if n in T22P else SRC21[n]) for n in ALL_HTML}
    for n in ALL_HTML:
        old = t20_file(n).decode('utf-8').replace('\r\n', '\n')
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'), ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>')):
            a = [_re.sub(r'<span style="white-space: nowrap">([^<]*)</span>', r'\1', x) for x in _re.findall(rx, SRC21W[n], _re.S)]
            check(f'T-21: {n} keeps its {what} (no word changed)', a == _re.findall(rx, old, _re.S), str(a)[:160])
        check(f'T-21: {n} keeps every link address', _re.findall(r'href="([^"]*)"', un23(SRC21[n], n)) ==_re.findall(r'href="([^"]*)"', old))
    for n in ('local.html', 'mainframe.html', 'index.html'):
        rx = r'<script type="application/ld\+json">(.*?)</script>'
        check(f'T-21: {n}\'s structured data is exactly as before', _re.findall(rx, SRC21[n], _re.S) == _re.findall(rx, t20_file(n).decode('utf-8'), _re.S))
    # T-22 K1 redraws og/case-reels.png, so that one card is read as T-21 left it.
    og_same = all((t21g_file('og/' + f) if f == 'case-reels.png' else open(os.path.join(here, '..', 'og', f), 'rb').read()) == t20_file('og/' + f) for f in os.listdir(os.path.join(here, '..', 'og')))
    check('T-21: every share card in og/ is byte for byte as on origin/main', og_same)

    # G1: no hyphen pair splits at its hyphen; the pass leaves code, scripts, links and addresses alone.
    PAIR_SPLIT_JS = r'''(() => {
      const out = [], seen = [];
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {acceptNode(n) {
        const p = n.parentElement; if (!p || p.closest('script,style,code,pre,textarea,svg,[hidden],[aria-hidden="true"]')) return 2;
        return p.getClientRects().length ? 1 : 2; }});
      let n;
      while ((n = w.nextNode())) for (const m of n.data.matchAll(/(?<![\p{L}\p{N}-])[\p{L}\p{N}]+-[\p{L}\p{N}]+(?![\p{L}\p{N}-])/gu)) {
        const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
        const tops = new Set([...r.getClientRects()].filter(x => x.width > 0.5).map(x => Math.round(x.top)));
        seen.push(m[0]); if (tops.size > 1) out.push(m[0]);
      }
      return {split: out, seen};
    })()'''
    # T-22: "cooking-class" left local, work and case-reels with the lines it sat in (K3 to K6); on local
    # and work the pair a visitor now reads in those spots is "40-reel" (K4, K6). case-reels has no listed pair left.
    LISTED = {'captions.html': ['15-minute'], 'checkup.html': ['15-minute'], 'scaler.html': ['15-minute'], 'work.html': ['15-minute', '40-reel'],
              'shotlist.html': ['15-minute'], 'local.html': ['three-month', '40-reel'], 'start.html': ['one-page']}
    for w in (320, 390, 1440):
        for n in ALL_HTML:
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(600)
            r = q.evaluate(PAIR_SPLIT_JS)
            check(f'T-21 G1: at {w}, no hyphen pair on {n} breaks at its hyphen', r['split'] == [], str(r['split']))
            for pair in LISTED.get(n, []):
                if w < 1440:
                    check(f'T-21 G1: at {w}, "{pair}" is on {n} and holds on one line', pair in r['seen'] and pair not in r['split'])
            q.close()
    q = newpage(320); q.goto(BASE + 'work.html'); settle(q)
    # T-22 K6: the reels card's heading is now "A 40-reel series on one engine."
    h = q.evaluate("(() => { const e = [...document.querySelectorAll('#cards h2')].find(x => x.textContent.startsWith('A 40-reel series')); const s = e.querySelector('span'); return [s.textContent, s.getClientRects().length] })()")
    check('T-21 G1: at 320 the work heading "A 40-reel series" keeps "40-reel" on one line', h == ['40-reel', 1], str(h))
    q.close()
    for n, pairs in LISTED.items():
        for pair in pairs:
            check(f'T-21 G1: "{pair}" on {n} sits in a no-wrap span', (NW + pair + '</span>') in SRC21[n])
    check('T-21 G1: the call band button keeps its words and spaces ("Free 15-minute call")',
          all(f'><span>Free {NW}15-minute</span> call</span></a>' in SRC21[n] for n in ('shotlist.html', 'captions.html', 'scaler.html')))
    FLEX_JS = '''(() => [...document.querySelectorAll('span[style="white-space: nowrap"]')].filter(s => /flex|grid/.test(getComputedStyle(s.parentElement).display)).map(s => s.parentElement.textContent.trim()))()'''
    for n in ALL_HTML:
        q = newpage(1440); q.goto(BASE + n); settle(q)
        check(f'T-21 G1: on {n} no no-wrap span sits straight in a flex or grid box (its spaces would vanish)', q.evaluate(FLEX_JS) == [], str(q.evaluate(FLEX_JS))[:200])
        q.close()
    for n in ALL_HTML:
        s = SRC21[n]
        pres = ''.join(_re.findall(r'<(?:pre|code|textarea|title)\b.*?</(?:pre|code|textarea|title)>', s, _re.S))
        check(f'T-21 G1: on {n} nothing inside pre, code, textarea or title got a no-wrap span', NW not in pres)
        # Every attribute value outside scripts and styles (links, labels, alt text, placeholders, data)
        # is as on origin/main; only style and class may differ, and the Studio pages' build-date stamp.
        def attrs21(src):
            src = _re.sub(r'<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->', '', src, flags=_re.S)
            return sorted((a.lower(), v) for t in _re.findall(r'<[a-zA-Z][^<>]*>', src)
                          for a, v in _re.findall(r'''\s([a-zA-Z][\w:-]*)\s*=\s*("[^"]*"|'[^']*')''', t) if a.lower() not in ('style', 'class', 'data-built'))
        check(f'T-21 G1: on {n} every attribute is as on origin/main (the pass never writes inside one)', attrs21(SRC21W[n]) == attrs21(t20_file(n).decode('utf-8')))   # T-22: its four pages as T-21 left them
        long_ = [x for x in _re.findall(NW + r'([^<]*)</span>', _re.sub(r'<script\b.*?</script>', '', un23(un25(s, n), n), flags=_re.S)) if len(x) > 24 or x.count('-') != 1]   # T-23's spans (L1, L4, L5) out: its own block checks them; T-25's too (F1's held phrases, F2's amounts)
        check(f'T-21 G1: on {n} every wrapped pair is letters or digits with one hyphen, at most 24 characters', long_ == [], str(long_))
    check('T-21 G1: three-part runs ("side-by-side", "year-to-date") and addresses are left to break as before (T-23 L1 now wraps the three-part runs: read with its spans out)',
          'side-by-side' in un23(SRC21['mainframe.html'], 'mainframe.html') and NW + 'side-by-side' not in un23(SRC21['mainframe.html'], 'mainframe.html') and 'stephensjosef-cloud' in SRC21['mainframe.html'] and NW + 'stephensjosef' not in SRC21['mainframe.html'])
    # The tools' own scripts use the same span where they write such text.
    q = newpage(390); q.goto(BASE + 'shotlist.html'); settle(q)
    q.evaluate("document.querySelector('.chip[data-k=\"type\"][data-v=\"gym\"]').click()"); q.wait_for_timeout(150)
    check('T-21 G1: the shot list\'s script wraps "mid-cue" when it writes the clips (Gym or class)', (NW + 'mid-cue</span>') in q.inner_html('#edit') and 'mid-cue' in q.inner_text('#edit'))
    q.close()
    q = newpage(390); q.goto(BASE + 'receipt.html'); settle(q)
    check('T-21 G1: the receipt\'s script wraps "follow-ups" on its chore chip', (NW + 'follow-ups</span>') in q.inner_html('#presets'))
    q.close()
    q = newpage(390); q.goto(BASE + 'comp3.html'); settle(q)
    check('T-21 G1: the decoder\'s script wraps "half-byte" in its label', (NW + 'half-byte</span>') in q.inner_html('#out'))
    q.close()

    # G2: in " · " lists no line starts or ends with the dot.
    DOT_JS = r'''(() => {
      const out = [];
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {acceptNode(n) {
        const p = n.parentElement; if (!p || p.closest('script,style,textarea,svg,[hidden],[aria-hidden="true"]')) return 2;
        return p.getClientRects().length ? 1 : 2; }});
      // T-23 L4: a dot clipped out of sight by a box that hides its overflow is not on screen, so it is not counted.
      const shown = (n, x) => { for (let e = n.parentElement; e && e !== document.body; e = e.parentElement) { if (getComputedStyle(e).overflowX === 'visible') continue;
        const c = e.getBoundingClientRect(); if (x.right <= c.left + 0.5 || x.left >= c.right - 0.5) return false; } return true; };
      const box = (n, i) => { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); return [...r.getClientRects()].find(x => x.width > 0.5 && shown(n, x)); };
      const chars = []; let n;
      while ((n = w.nextNode())) for (let i = 0; i < n.data.length; i++) if (/\S/.test(n.data[i]) && n.data[i] !== ' ') chars.push([n, i]);
      chars.forEach(([n, i], k) => {
        if (n.data[i] !== '·') return;
        const d = box(n, i); if (!d) return;
        const prev = chars[k - 1] && box(...chars[k - 1]), next = chars[k + 1] && box(...chars[k + 1]);
        if (prev && prev.top < d.top - 4) out.push('starts a line: ' + n.data.trim().slice(0, 40));
        if (next && next.top > d.top + 4) out.push('ends a line: ' + n.data.trim().slice(0, 40));
      });
      return out;
    })()'''
    for w in (320, 390, 1440):
        for n in ALL_HTML:
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(600)
            r = q.evaluate(DOT_JS)
            check(f'T-21 G2: at {w}, no line on {n} starts or ends with a " · " separator', r == [], str(r)[:200])
            q.close()
    for w in (320, 390):
        q = newpage(w); q.goto(BASE + 'local.html'); settle(q)
        for tab in ('app', 'method'):
            q.evaluate(f"document.querySelector('[data-tab=\"{tab}\"]').click()"); q.wait_for_timeout(200)
            check(f'T-21 G2: at {w}, local\'s {tab} result card has no separator at a line edge', q.evaluate(DOT_JS) == [], str(q.evaluate(DOT_JS)))
        q.close()

    # G3: Mainframe.
    MF_OLD = t20_file('mainframe.html').decode('utf-8')
    code_of = lambda s: _html.unescape(_re.sub(r'<[^>]+>', '', _re.search(r'<pre [^>]*class="t20-code">(.*?)</pre>', s, _re.S).group(1)))
    check('T-21 G3: Exhibit A\'s code is character for character as before', code_of(SRC21['mainframe.html']) == code_of(MF_OLD))
    for w in (320, 360, 390):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q)
        r = q.evaluate('''(() => { const pre = document.querySelector('pre.t20-code');
          const toks = [...pre.querySelectorAll('.t21-tk')];
          return {split: toks.filter(t => new Set([...t.getClientRects()].map(x => Math.round(x.top))).size > 1).map(t => t.textContent),
                  alone: toks.filter(t => /^[=*\\/+-]$/.test(t.textContent.trim())).map(t => t.textContent),
                  words: toks.map(t => t.textContent),
                  fs: parseFloat(getComputedStyle(pre).fontSize), scroll: [pre.scrollWidth, pre.clientWidth], page: document.documentElement.scrollWidth,
                  indent: [...pre.querySelectorAll('.t21-ln')].filter(l => l.getClientRects().length && l.textContent.trim()).map(l => { const rs = [...l.querySelectorAll('.t21-tk')].map(t => t.getBoundingClientRect()); return rs.length > 1 ? Math.round(rs[rs.length - 1].left - rs[0].left) : 0 })} })()''')
        check(f'T-21 G3: at {w} no COBOL name or token in Exhibit A breaks across lines', r['split'] == [], str(r['split']))
        check(f'T-21 G3: at {w} no operator sits alone in Exhibit A', r['alone'] == [] and 'ROUNDED =' in r['words'], str(r['alone']))
        check(f'T-21 G3: at {w} Exhibit A fits its box at {r["fs"]} px (11 px or more) with no sideways scroll, and the page has none', r['fs'] >= 11 and r['scroll'][0] <= r['scroll'][1] and r['page'] <= w, str(r))
        q.close()
    q = newpage(320); q.goto(BASE + 'mainframe.html'); settle(q)
    ind = q.evaluate('''(() => [...document.querySelectorAll('pre.t20-code .t21-ln')].map(l => { const t = [...l.querySelectorAll('.t21-tk')]; const pre = l.closest('pre').getBoundingClientRect(); const cs = getComputedStyle(l.closest('pre'));
        return t.map(x => [x.textContent, Math.round(x.getBoundingClientRect().left - pre.left - parseFloat(cs.paddingLeft)), Math.round(x.getBoundingClientRect().top)]) }))()''')
    ch = q.evaluate("(() => { const s = document.createElement('span'); s.textContent = '0000000000'; document.querySelector('pre.t20-code').appendChild(s); const w = s.getBoundingClientRect().width / 10; s.remove(); return w })()")
    cont = [(t[0], round(t[1] / ch)) for line in ind for k, t in enumerate(line) if k and t[2] > line[0][2] + 4 and t[2] != line[k - 1][2]]
    lead = {line[0][0]: round(line[0][1] / ch) for line in ind if line}
    check('T-21 G3: at 320 a wrapped Exhibit A line continues 2 characters in from where its own line starts',
          bool(cont) and all(c in (2, 6) for _, c in cont) and lead.get('APR-RATE') == 4 and lead.get('COMPUTE') == 0, str(cont) + str(lead))
    q.close()
    for w in (320, 390):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q)
        for tab in ('b', 'c', 'd'):
            q.evaluate(f"document.querySelector('[data-ex=\"{tab}\"]').click()"); q.wait_for_timeout(200)
            r = q.evaluate(r'''(() => [...document.querySelectorAll('#xb-rows > div')].map(row => { const [l, v] = row.children;
                const lines = e => { const r = document.createRange(); r.selectNodeContents(e); return new Set([...r.getClientRects()].filter(x => x.width > .5).map(x => Math.round(x.top))).size };
                const words = e => { const ws = []; const t = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let n; while ((n = t.nextNode())) for (const m of n.data.matchAll(/\S+/g)) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const b = [...r.getClientRects()].filter(x => x.width > .5); ws.push([m[0], b.length, b.length ? Math.round(b[b.length - 1].top) : 0]) } return ws };
                return {label: l.textContent, lw: words(l), vw: words(v)} }))()''')
            alone = [x['label'] for x in r if len({t for _, _, t in x['lw']}) > 1 and sum(1 for _, _, t in x['lw'] if t == max(t2 for _, _, t2 in x['lw'])) == 1]
            split = [wd for x in r for wd, nb, _ in x['vw'] + x['lw'] if nb > 1]
            check(f'T-21 G3: at {w}, Exhibit {tab.upper()}: no label leaves one word alone on its last line', alone == [], str(alone))
            check(f'T-21 G3: at {w}, Exhibit {tab.upper()}: no field name or word splits across lines', split == [], str(split))
        q.close()
    q = newpage(1440); q.goto(BASE + 'mainframe.html'); settle(q)
    tops = q.evaluate("[...document.querySelectorAll('.t20-steps > li')].map(li => Math.round(li.querySelector('p').getBoundingClientRect().top))")
    check('T-21 G3: at 1440 the body text of steps I to IV starts at the same height', len(tops) == 4 and len(set(tops)) == 1, str(tops))
    eyebrows = q.evaluate("[...document.querySelectorAll('.t20-steps > li')].map(li => li.querySelectorAll('span').length)")
    check('T-21 G3: only steps I and IV carry an eyebrow line, as before (no words added)', eyebrows == [2, 1, 1, 2], str(eyebrows))
    v = q.evaluate("[...document.querySelectorAll('section[aria-label=Thesis] > div > p')].map(p => Math.round(p.getBoundingClientRect().top))")
    check('T-21 G3: at 1440 the paragraph beside the band about both readings sits at its top', len(v) == 2 and abs(v[0] - v[1]) <= 2, str(v))
    q.close()
    q = newpage(390); q.goto(BASE + 'mainframe.html'); settle(q)
    tops = q.evaluate("[...document.querySelectorAll('.t20-steps > li')].map(li => li.getBoundingClientRect().height)")
    check('T-21 G3: on phones the steps stay one column with no empty eyebrow row', all(t > 0 for t in tops) and q.evaluate("getComputedStyle(document.querySelector('.t20-steps > li')).display") == 'flex', str(tops))
    q.close()

    # G4: no card grid ends with an empty slot; work in both checkup states.
    LAST_JS = '''((sel) => { const g = document.querySelector(sel); const kids = [...g.children].filter(k => k.getClientRects().length);
        const gb = g.getBoundingClientRect(); const top = Math.max(...kids.map(k => Math.round(k.getBoundingClientRect().top)));
        const last = kids.filter(k => Math.round(k.getBoundingClientRect().top) === top);
        return Math.round(gb.right - Math.max(...last.map(k => k.getBoundingClientRect().right))) })'''
    def grids21(base_, label):
        for w in (320, 390, 768, 1024, 1440):
            q = newpage(w); q.goto(base_ + 'work.html'); settle(q)
            for f in ('all', 'apps', 'video', 'mainframe', 'free'):   # T-33 R11: the tabs (were nonprofit, banking, own)
                q.click(f'.filt[data-f="{f}"]'); q.wait_for_timeout(120)
                gap = q.evaluate(LAST_JS, '#cards')
                check(f'T-21 G4 ({label}): at {w}, the work grid ("{f}") ends with no empty slot', gap <= 2, str(gap))
            q.goto(base_ + 'studio.html'); settle(q)
            check(f'T-21 G4 ({label}): at {w}, the Studio products grid ends with no empty slot', q.evaluate(LAST_JS, '#products') <= 2, str(q.evaluate(LAST_JS, '#products')))
            q.goto(base_ + 'local.html'); settle(q)
            check(f'T-21 G4 ({label}): at {w}, local\'s free tools cards end with no empty slot', q.evaluate(LAST_JS, '#tools > div > div') <= 2, str(q.evaluate(LAST_JS, '#tools > div > div')))
            q.close()
    grids21(BASE, 'checkup not live')
    tmp21 = _tmp.mkdtemp()
    srv = None
    try:
        bd = os.path.join(tmp21, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        fp = os.path.join(bd, 'tools', 'checkup.py')
        open(fp, 'w', encoding='utf-8').write(ck_src.replace("\nvar CHECKUP_URL = '';", "\nvar CHECKUP_URL = 'https://dj-checkup.example.test/';", 1))
        steps = [([sys.executable, t + '.py', '..'], os.path.join(bd, 'tools')) for t in ('shotlist', 'captions', 'receipt', 'scaler', 'checkup', 'studio')]
        steps += [(st, bd) for st in (['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'],
                                      [sys.executable, 'enhance.py', 'out'], [sys.executable, 'plain.py', 'out'], [sys.executable, 'intent.py', 'out'],
                                      [sys.executable, 'voice2.py', 'out'], [sys.executable, 'final.py', 'out'])]
        built = True
        for st, cwd_ in steps:
            r = _sp18.run(st, cwd=cwd_, capture_output=True, text=True)
            if r.returncode:
                built = False
                check('T-21 G4: the temp build with a checkup address runs', False, ' '.join(st[1:2]) + ': ' + (r.stdout + r.stderr)[-300:])
                break
        if built:
            check('T-21 G4: the temp build with a checkup address has the fifth tool card', open(os.path.join(bd, 'out', 'work.html'), encoding='utf-8').read().count('href="checkup.html"') >= 1)
            srv = _sp18.Popen([sys.executable, '-m', 'http.server', str(TEMP_PORT), '--bind', '127.0.0.1'], cwd=os.path.join(bd, 'out'), stdout=_sp18.DEVNULL, stderr=_sp18.DEVNULL)
            import time as _time21
            _time21.sleep(1.5)
            grids21(f'http://127.0.0.1:{TEMP_PORT}/', 'checkup live')
    finally:
        if srv:
            srv.terminate(); srv.wait()
        _shutil.rmtree(tmp21, ignore_errors=True)
    check('T-21 G4: the temp copy is gone, and the real checkup.py still has no address',
          not os.path.exists(tmp21) and "\nvar CHECKUP_URL = '';" in open(os.path.join(here, 'tools', 'checkup.py'), encoding='utf-8').read())

    # G5: Local at 1440.
    q = newpage(1440); q.goto(BASE + 'local.html'); settle(q)
    r = q.evaluate('''(() => { const s = document.querySelector('#proof > div'); const cs = getComputedStyle(s);
        const inner = s.getBoundingClientRect().width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        return [Math.round(document.getElementById('rc-panel').getBoundingClientRect().width), Math.round(inner)] })()''')
    check('T-21 G5: at 1440 the Results card fills the section\'s content width', abs(r[0] - r[1]) <= 1, str(r))
    for w, cols in ((1440, 2), (1200, 2), (1199, 1), (900, 1), (390, 1)):
        q2 = newpage(w); q2.goto(BASE + 'local.html'); settle(q2)
        r = q2.evaluate('''(() => { const items = [...document.querySelectorAll('[data-faq]')].map(b => b.parentElement);
            const lefts = new Set(items.map(i => Math.round(i.getBoundingClientRect().left)));
            const p = document.getElementById('faq-a-0'); const s = document.createElement('span'); s.style.cssText = 'display:inline-block;width:72ch';
            p.appendChild(s); const max = s.getBoundingClientRect().width; s.remove();
            return [lefts.size, Math.round(p.getBoundingClientRect().width), Math.round(max)] })()''')
        check(f'T-21 G5: at {w} the FAQ lays its questions out in {cols} column{"s" if cols > 1 else ""}', r[0] == cols, str(r))
        check(f'T-21 G5: at {w} an FAQ answer is no wider than 72 characters', r[1] <= r[2], str(r))
        q2.close()
    r = q.evaluate('''(() => [document.getElementById('sr-status').getBoundingClientRect().left, document.querySelector('#contact a.btn-blaze').getBoundingClientRect().left].map(Math.round))()''')
    check('T-21 G5: at 1440 "I\'m off the clock..." shares the left edge of the buttons above it', abs(r[0] - r[1]) <= 1, str(r))
    q.close()
    for w in (1440, 390):
        a, b_ = [], []
        for base_, pgf, out_ in ((BASE, lambda: newpage(w), a), (OLD20, lambda: t20_page(w), b_)):
            q = pgf(); q.goto(base_ + 'local.html'); settle(q)
            st = lambda: q.evaluate("[...document.querySelectorAll('[data-faq]')].map(b => b.getAttribute('aria-expanded') + (document.getElementById(b.getAttribute('aria-controls')).hidden ? '-' : '+'))")
            out_.append(st())
            n_ = len(st())
            for i in range(n_):
                q.click(f'[data-faq="{i}"]'); q.wait_for_timeout(250); out_.append(st())
            for i in range(n_):
                q.focus(f'[data-faq="{i}"]'); q.keyboard.press('Enter' if i % 2 else 'Space'); q.wait_for_timeout(250); out_.append(st())
            q.close()
        check(f'T-21 G5: at {w} every FAQ item opens and closes by tap and by keyboard exactly as before', a == b_ and len(a) > 6, str(a[:3]) + ' | ' + str(b_[:3]))

    # G6: the small ones.
    q = newpage(320); q.goto(BASE + 'comp3.html'); settle(q)
    r = q.evaluate(r'''(() => { const s = [...document.querySelectorAll('a.quiet span')].find(x => x.textContent.startsWith('Found a field')); const out = [];
        const t = s.firstChild; for (const m of t.data.matchAll(/\S+/g)) { const r = document.createRange(); r.setStart(t, m.index); r.setEnd(t, m.index + m[0].length); out.push([m[0], Math.round(r.getClientRects()[0].top)]) } return out })()''')
    last = [x for x, t in r if t == r[-1][1]]
    check('T-21 G6: comp3 at 320, "Found a field with two readings?" leaves no word alone on its last line', len(last) >= 2, str(r))
    q.close()
    q = newpage(1440); q.goto(BASE + 'studio-birdleague.html'); settle(q)
    r = q.evaluate('''(() => { const p = document.querySelector('.top > .proof').getBoundingClientRect(); const h = document.getElementById('log-h').getBoundingClientRect();
        const j = document.getElementById('join').getBoundingClientRect(); const top = document.querySelector('.top').getBoundingClientRect();
        return [Math.round(h.top - p.bottom), Math.round(j.top - top.bottom)] })()''')
    check('T-21 G6: Bird League at 1440, "Shipped lately" gets the page\'s normal space under the bold line', abs(r[0] - 48) <= 2, str(r))
    q.close()
    for w in (390, 320):
        q = newpage(w); q.goto(BASE + 'local.html'); settle(q)
        r = q.evaluate('''(() => { const lis = [...document.querySelectorAll('#route ol > li')];
            const dots = lis.map(li => li.querySelector('span[aria-hidden="true"]').getBoundingClientRect());
            const lines = lis.map(li => { const s = getComputedStyle(li, '::before'); return s.content === 'none' ? null : [Math.round(li.getBoundingClientRect().left + parseFloat(s.left) + parseFloat(s.width) / 2), Math.round(li.getBoundingClientRect().top + parseFloat(s.top)), Math.round(li.getBoundingClientRect().bottom - parseFloat(s.bottom))] });
            return {dx: dots.map(d => Math.round(d.left + d.width / 2)), dy: dots.map(d => Math.round(d.top + d.height / 2)), lines, ol: getComputedStyle(document.querySelector('#route ol')).borderTopWidth} })()''')
        joined = all(r['lines'][i] and abs(r['lines'][i][0] - r['dx'][i]) <= 1 and abs(r['lines'][i][1] - r['dy'][i]) <= 2 and abs(r['lines'][i][2] - r['dy'][i + 1]) <= 2 for i in range(len(r['dx']) - 1))
        check(f'T-21 G6: local at {w}, "How it works" reads as one line through all three steps (every dot on it, every step the same)',
              len(set(r['dx'])) == 1 and joined and r['lines'][-1] is None and r['ol'] == '0px', str(r))
        bp = q.evaluate("(() => { const h = document.querySelector('#blueprint h3'); return [h.getClientRects().length, h.scrollWidth <= h.clientWidth + 1] })()")
        check(f'T-21 G6: local at {w}, "THE BLUEPRINT · $1,500" still holds on one line beside the line', bp == [1, True], str(bp))
        q.close()
    for w in (390, 320):
        q = newpage(w); q.goto(BASE + 'local.html'); settle(q)
        r = q.evaluate('''(() => [...document.querySelectorAll('[data-pick]')].map(b => { const c = b.firstElementChild.getBoundingClientRect(), r = b.getBoundingClientRect(), cs = getComputedStyle(b);
            return [Math.round(r.top), Math.round(r.height), Math.round(c.height + parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom) + parseFloat(cs.borderTopWidth) * 2)] }))()''')
        rows_ = {}
        for top, hgt, need in r:
            rows_.setdefault(top, []).append(hgt)
        check(f'T-21 G6: local at {w}, each "Start here" tile is as tall as its words (no tall empty bottom)', all(h_ <= nd + 2 for _, h_, nd in r), str(r))
        check(f'T-21 G6: local at {w}, tiles on one row share a height and every tile is at least 48 px tall', all(len(set(v)) == 1 for v in rows_.values()) and min(h_ for _, h_, _ in r) >= 48, str(r))
        q.close()
    for n in ('captions', 'checkup', 'receipt', 'scaler', 'shotlist'):
        q = newpage(1440); q.goto(BASE + n + '.html'); settle(q)
        r = q.evaluate('''(() => { const s = document.querySelector('section[aria-labelledby="more-h"]'); const cs = getComputedStyle(s); const b = s.getBoundingClientRect();
            const t = s.children[0].getBoundingClientRect(), a = s.querySelector('a').getBoundingClientRect();
            return {right: Math.round(b.right - parseFloat(cs.paddingRight) - a.right), left: Math.round(t.left - b.left - parseFloat(cs.paddingLeft)),
                    mid: Math.round((a.top + a.bottom) / 2 - (t.top + t.bottom) / 2), empty: Math.round(a.left - t.right)} })()''')
        check(f'T-21 G6: {n} at 1440, the call band\'s words and button sit as one group (words from the left edge, button at the right edge, centered on the words)',
              abs(r['right']) <= 1 and abs(r['left']) <= 1 and abs(r['mid']) <= 2, str(r))
        q.close()
    check('T-21 G6: the call band rule is set once, in tools/chrome.py', all(SRC21[n].count(_chrome20.BAND_CSS) == 1 for n in ('captions.html', 'checkup.html', 'receipt.html', 'scaler.html', 'shotlist.html')))
    for n in ALL_HTML:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + n); settle(q)
            sw = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-21: {n} has no sideways scroll at {w}', sw <= w, str(sw))
            q.close()

    # Same input, same result as origin/main: two inputs per tool, and every form.
    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')]):
        def shot21(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT_JS); r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both20('shotlist', shot21)
        check(f'T-21: shot list gives the same clips, stops, countdown and copy as on origin/main for {picks or "the defaults"}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for text, picks, secs in ((None, [], '7.5'), ('New fall sweaters just landed.', [('size', 'l'), ('pos', 'top'), ('app', 'tiktok')], '2')):
        def cap21(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks); set_val(q, '#secs', secs); q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS); r['copy'] = grab_copy(q, '#copy'); r['verdict'] = q.inner_text('#verdict')
            return r
        a, b_ = both20('captions', cap21)
        check(f'T-21: caption fitter gives the same verdict, checks, preview and copy as on origin/main for {(text or "the default")[:24]} at {secs} s', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for args in (([], None, False), ([4, 11], '45', True)):
        a, b_ = both20('receipt', rec_in(*args))
        check(f'T-21: receipt gives the same lines, totals, hand-off and copy as on origin/main for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for serves, adults, kids in ((None, None, None), ('6', '10', '0')):
        def sc21(q):
            if serves:
                set_val(q, '#serves', serves); set_val(q, '#adults', adults); set_val(q, '#kids', kids); q.wait_for_timeout(100)
            return [q.inner_text('#fac'), q.inner_text('#facl'), q.inner_text('#warn'), q.evaluate("document.getElementById('out').textContent"), grab_copy(q, '#copy')]
        a, b_ = both20('scaler', sc21)
        check(f'T-21: scaler gives the same amounts and copy as on origin/main for {serves or "the defaults"}', a == b_, str(a)[:200] + ' | ' + str(b_)[:200])
    for steps in ([], [('#in', '0350000D'), ('#pic', 'PIC S9(5)V99 COMP-3.')]):
        def dec21(q):
            for sel, val in steps:
                q.fill(sel, val)
            q.wait_for_timeout(150)
            return q.evaluate("document.getElementById('out').textContent.replace(/\\s+/g, ' ').trim()")
        a, b_ = both20('comp3', dec21)
        a = un24(a)   # T-24 A7: the two result labels read back as T-23's
        check(f'T-21: the decoder gives the same readings as on origin/main for {steps or "the opening example"}', a == b_, a[:200] + ' | ' + b_[:200])
    for tab in ('b', 'c', 'd'):
        def ex21(q):
            q.evaluate(f"document.querySelector('[data-ex=\"{tab}\"]').click()"); q.wait_for_timeout(150)
            return q.evaluate("document.getElementById('xb-panel').textContent.replace(/\\s+/g, ' ').trim()")
        a, b_ = both20('mainframe', ex21)
        check(f'T-21: Mainframe Exhibit {tab.upper()} reads as on origin/main', a == b_, a[:120] + ' | ' + b_[:120])
    for reading in ('fraction', 'percent'):
        def rd21(q):
            q.evaluate(f"document.querySelector('[data-reading=\"{reading}\"]').click()"); q.wait_for_timeout(150)
            return [q.inner_text('#mf-value'), q.inner_text('#mf-rate'), q.inner_text('#mf-interest'), q.inner_text('#mf-verdict')]
        a, b_ = both20('mainframe', rd21)
        a = [un24(x) for x in a]   # T-24 A4: the fraction verdict reads back as T-23's
        check(f'T-21: Exhibit A\'s "{reading}" reading gives the same numbers as on origin/main', a == b_, str(a) + ' | ' + str(b_))
    sel = both20('mainframe', lambda q: q.evaluate("[...document.querySelectorAll('[data-reading]')].map(b => b.dataset.reading + '=' + b.getAttribute('aria-pressed'))"))
    check('T-21: Exhibit A starts on the same reading as on origin/main', sel[0] == sel[1], str(sel))
    def sent20(base_, name, fill, btn, done):
        q = newpage(1440) if base_ == BASE else t20_page(1440)
        got = []
        def grab(route):
            if route.request.method == 'POST':
                got.append(_json.loads(route.request.post_data or '{}'))
            route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
        q.route('**/dj-intake.stephens-josef.workers.dev/**', grab)
        q.goto(base_ + name + '.html'); settle(q)
        fill(q); q.click(btn); q.wait_for_timeout(700)
        for g in got:
            g.pop('ms', None)
        return got, q.locator(done).is_visible()
    for name, fill, btn, done in (('start', fill_start20, '#bp-send', '#bp-done'), ('call', fill_call, '#cl-send', '#cl-done'), ('briefing', fill_brief, '#br-send', '#br-done')):
        a, b_ = sent20(BASE, name, fill, btn, done), sent20(OLD20, name, fill, btn, done)
        check(f'T-21: {name} still sends, and sends exactly what it sent on origin/main', a == b_ and len(a[0]) == 1 and a[1], str(a)[:300] + ' | ' + str(b_)[:300])
    def join20(base_):
        q = newpage(1440) if base_ == BASE else t20_page(1440)
        got = []
        def grab(route):
            if route.request.method == 'POST':
                got.append(_json.loads(route.request.post_data or '{}'))
            route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
        q.route('**/dj-intake.stephens-josef.workers.dev/**', grab)
        q.goto(base_ + 'studio-birdleague.html'); settle(q)
        q.fill('#join input[type=email]', 'test@example.com'); q.click('#join button[type=submit]'); q.wait_for_timeout(700)
        for g in got:
            g.pop('ms', None)
        return got
    a, b_ = join20(BASE), join20(OLD20)
    check('T-21: the Bird League join list still sends exactly what it sent on origin/main', a == b_ and len(a) == 1, str(a) + ' | ' + str(b_))


# ---------------- T-22 (Nov 16, 2026): Kids Kitchen, process and scale ----------------
@section('T-22')
def s_t_22():
    # Josef's lines K1 to K9, word for word. Comparisons are against T-21's own pages
    # (trip/T-21's last commit, the base this item was cut from), read straight from git.
    T21C = 'a0c77c98a2213a618efd2e2831d03fae424963c4'
    T21_FILES = {}

    def t21_file(path):
        if path not in T21_FILES:
            r = _sp18.run(['git', 'show', f'{T21C}:{path}'], cwd=here, capture_output=True)
            T21_FILES[path] = r.stdout if r.returncode == 0 else None
        return T21_FILES[path]
    check('T-22: the T-21 pages can be read from git for comparison', t21_file('case-reels.html') is not None and t21_file('og/case-reels.png') is not None)
    SRC22 = {n: un23(un24(un25(un26(un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n), n)), n) for n in ALL_HTML}   # T-26: the gallery out first   # T-23: its changes out (its block checks them); T-24: A1 to A7 read back as T-23's; T-25: its layout swaps out   # T-30: local's descriptions back
    OLD22 = {n: t21_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}

    K1_H1 = 'Forty reels, one engine.'
    K1 = ("Every cooking class used to cost the program's creator an evening of editing. "
          "Now her phone clips go through an engine and come back as a finished reel in about four minutes.")
    K1_TITLE = "Case study: forty reels, one engine · Dragoman's Journey"
    K2 = [('An evening', 'Editing each reel, before'), ('~4 min', 'Each reel now'), ('40', 'Reels in the series'), ('0', 'Posted without her yes')]
    K3_H = 'How it works'
    K3 = ("She films the class on her phone. The clips and the recipe card go through the engine. It finds the action, "
          "cuts the dead time and captions every step in her style. Every note she has given becomes a rule it checks on "
          "every reel after. Nothing posts until she says yes.")
    K4_LINE = "A 40-reel series for a children's nonprofit, cut by one engine."
    K4_ROWS = [('Editing each reel, before', 'An evening'), ('Now', '~4 min'), ('Reels in the series', '40'), ('Posted without their yes', '0')]
    K5_TITLE = 'Forty reels, one engine.'
    K5_NOTE = 'Every note she gives becomes a rule the engine checks on every reel after, so nobody catches the same thing twice.'
    K5_SRC_NEW = ['Before the engine, she cut each class by hand. That took an evening.',
                  "The engine's own log for the August 2026 shoot: about four minutes from clips in to finished reel.",
                  'The full series the program has planned.']
    K6 = ('An evening of editing, now about 4 minutes.', 'A 40-reel series on one engine.',
          "A children's nonprofit used to spend an evening editing each class. Now the clips go through an engine and come back as finished, captioned reels. They approve every one.")
    K7 = 'Your staff try every update before any family sees it.'
    K8_HEAD = 'Their recipe cards, now an app.'
    K8 = "The program's own recipes, in an app teachers cook from in class. iPhone, iPad, Android and the web."
    K9 = "The program's own recipes went into the cooking app, ready to print."
    K9_KEPT = "The kids' cooking app runs on Android as well as iPhone and iPad."

    def text22(name, w=1440, before=None):
        q = newpage(w); q.goto((UN29 if name == 'studio.html' else UN30) + name); settle(q)   # T-30: studio's kids' line back (un29() calls un30()); T-33: every page through un30(), which takes T-33's lines out
        if before:
            before(q)
        t = q.evaluate(TEXT_JS); q.close()
        return t

    # T-23: its four lines read as T-22's, and the Studio's closing call (L6) out of the way; the T-23 block checks them.
    drop_box = lambda q: q.evaluate("""document.querySelector('section[aria-labelledby="next-h"]').remove()""")
    TXT22 = {n: back23(text22(n, before=drop_box if n == 'studio.html' else None)) for n in ('case-reels.html', 'local.html', 'work.html', 'studio.html')}
    ONCE = {'case-reels.html': [('K1', K1_H1), ('K1', K1), ('K3', K3_H), ('K3', K3)],
            'local.html': [('K4', K4_LINE), ('K5', K5_TITLE), ('K5', K5_NOTE), ('K7', K7)],
            'work.html': [('K6', K6[0]), ('K6', K6[1]), ('K6', K6[2]), ('K8', K8_HEAD), ('K8', K8)],
            'studio.html': [('K8', K8), ('K9', K9)]}
    for n, lines in ONCE.items():
        for kid, line in lines:
            check(f'T-22 {kid}: "{line[:48]}" is on {n} word for word, exactly once', TXT22[n].count(line) == 1, str(TXT22[n].count(line)))
    check('T-22: no long dash on the four changed pages', not any(d in SRC22[n] for n in TXT22 for d in ('—', '–')))
    check('T-22: the client is never named on the four changed pages (CLIENT_ placeholders all filled)', not any('CLIENT_' in SRC22[n] for n in TXT22))

    # K1: title, descriptions, share card.
    cr = SRC22['case-reels.html']
    meta = lambda s, rx: (_re.search(rx, s) or [None, None])[1]
    check('T-22 K1: case-reels title follows the new h1 in the page\'s title pattern', meta(cr, r'<title>([^<]*)</title>') == K1_TITLE, str(meta(cr, r'<title>([^<]*)</title>')))
    check('T-22 K1: case-reels og:title is the title', _html.unescape(meta(cr, r'<meta property="og:title" content="([^"]*)"') or '') == K1_TITLE)
    check('T-22 K1: case-reels meta description is the new line, both sentences', _html.unescape(meta(cr, r'<meta name="description" content="([^"]*)"') or '') == K1)
    check('T-22 K1: case-reels og:description is the new line, both sentences', _html.unescape(meta(cr, r'<meta property="og:description" content="([^"]*)"') or '') == K1)
    check('T-22 K1: case-reels h1 is the new headline', [_re.sub(r'<[^>]+>', '', x) for x in _re.findall(r'<h1[^>]*>(.*?)</h1>', cr, _re.S)] == [K1_H1])
    check('T-22 K1: case-reels og:image is its own card', meta(cr, r'<meta property="og:image" content="([^"]*)"') == 'https://dragomansjourney.com/og/case-reels.png')
    card = urlopen(BASE + 'og/case-reels.png').read()
    check('T-22 K1: the served case-reels card is the one tools/og.py drew', card == open(os.path.join(here, 'assets', 'og', 'case-reels.png'), 'rb').read())
    check('T-22 K1: the case-reels card is redrawn (not T-21\'s)', card != t21_file('og/case-reels.png'))
    check('T-22 K1: og/case-reels.png at the root is the redrawn card', open(os.path.join(here, '..', 'og', 'case-reels.png'), 'rb').read() == card)
    check('T-22 K1: the redrawn card is 1200 by 630', card[:8] == b'\x89PNG\r\n\x1a\n' and _struct.unpack('>II', card[16:24]) == (1200, 630))
    others = sorted(f for f in os.listdir(os.path.join(here, '..', 'og')) if f != 'case-reels.png')
    check('T-22: every other share card in og/ is byte for byte as at T-21', len(others) == 16 and all(
        open(os.path.join(here, '..', 'og', f), 'rb').read() == t21_file('og/' + f) for f in others), str(len(others)))
    check('T-22: every other share card in _build/assets/og/ is byte for byte as at T-21', all(
        open(os.path.join(here, 'assets', 'og', f), 'rb').read() == _sp18.run(['git', 'show', f'{T21C}:_build/assets/og/{f}'], cwd=here, capture_output=True).stdout for f in others))

    # K2 and K3 on case-reels, read from the page.
    q = newpage(1440); q.goto(BASE + 'case-reels.html'); settle(q)
    stats = q.evaluate("[...document.querySelectorAll('.stats .stat')].map(s => [s.querySelector('b').textContent, s.querySelector('span').textContent])")
    check('T-22 K2: case-reels has these four numbers, in this order, value then label', [tuple(x) for x in stats] == K2, str(stats))
    h2s = q.evaluate("[...document.querySelectorAll('main h2')].map(h => h.textContent.trim())")
    check('T-22 K3: case-reels\' body is one section, then the closing call', h2s == [K3_H, 'Got a phone full of footage?'], str(h2s))
    sec = [back23(x) for x in q.evaluate("[...document.querySelector('section[aria-labelledby=c1] > div').children].map(e => e.tagName + ':' + e.textContent.replace(/\\s+/g, ' ').trim())")]   # T-23 K3b read as K3
    check('T-22 K3: the section holds the one paragraph', sec == ['P:' + K3], str(sec))
    close = q.evaluate("(() => { const s = document.querySelector('section[aria-labelledby=c7]'); return s.outerHTML })()")
    old_close = _re.search(r'<section aria-labelledby="c7".*?</section>', OLD22['case-reels.html'], _re.S).group(0)
    check('T-22 K3: the closing call ("Got a phone full of footage?", its line and its buttons) is as at T-21',
          _re.sub(r'\s+', ' ', close) == _re.sub(r'\s+', ' ', old_close), close[:160])
    q.close()

    # Removed words: off case-reels, local, work and studio, page source and scripts included.
    GONE = ['21:28', '13:33', '81 sec', '81-second', '9 captioned steps', '16 to 20', '29×', '535 automatic checks',
            'kids as young as three', 'garden and science', 'empty pot', 'empty-pot', 'house rules', 'Seven more episodes',
            "The kids' cooking app got its new logo, everywhere in the app.",
            "Step-by-step videos and a full Spanish version went into the kids' cooking app.",
            'One shoot, one finished reel', 'One cooking-class shoot', 'One cooking class, filmed on a phone',
            'refuses broken entries', 'hundreds of automatic checks', 'Those three were uneven caption boxes']
    for n in TXT22:
        flat = un21(SRC22[n])
        hits = [g for g in GONE if g.lower() in flat.lower() or g.lower() in TXT22[n].lower()]
        check(f'T-22: none of the removed words are left on {n}', not hits, str(hits))
        heads = [_re.sub(r'<[^>]+>|\s+', ' ', h).strip() for h in _re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', SRC22[n], _re.S)]
        gone_h = [h for h in heads if h in ('The program', 'The pile', 'What I built', 'The house rules', 'Who signs off', "What's next", 'The gate')]
        check(f'T-22 K3: none of the six section headings are left on {n}', not gone_h, str(gone_h))

    # K4: the hero "Real result" card.
    q = newpage(1440); q.goto(BASE + 'local.html'); settle(q)
    # T-33 R4 replaces this card's title, line, rows and client line: the expected values are R4's (no line, no client line).
    hero = q.evaluate("""(() => { const f = document.querySelector('figure.rise3 .tear'); const head = f.querySelector('div');
      return {head: [...head.children].map(e => e.textContent.trim()), line: (f.querySelector('p') || {textContent: ''}).textContent.replace(/\\s+/g, ' ').trim(),
        rows: [...f.querySelectorAll(':scope > div:nth-of-type(2) > div')].map(r => [r.querySelector('span').textContent, r.querySelector('strong').textContent]),
        foot: [...(f.querySelector(':scope > div:nth-of-type(3)') || {children: []}).children].map(e => e.textContent.trim())} })()""")
    check('T-22 K4: the hero card\'s title stays "KIDS\' COOKING REELS"', hero['head'] == ['REAL RESULTS', 'BUILT WITH AI'], str(hero['head']))   # T-33 R4: REAL RESULTS, BUILT WITH AI
    check('T-22 K4: the hero card\'s line is the new one', hero['line'] == '', hero['line'])   # T-33 R4: no line under the labels
    check('T-22 K4: the hero card has these four rows, in this order, label then value', [tuple(r) for r in hero['rows']] == T33_R4_ROWS, str(hero['rows']))   # T-33 R4's rows
    check('T-22 K4: the hero card\'s client line stays', hero['foot'] == [], str(hero['foot']))   # T-33 R4: no client line

    # K5: Results, Reels tab, as first drawn and after the tabs redraw it.
    def rc22(q):
        return q.evaluate("""(() => ({title: document.getElementById('rc-title').textContent, date: document.getElementById('rc-date').textContent,
          head: document.getElementById('rc-head').textContent.replace(/\\u00a0/g, ' '),
          rows: [...document.querySelectorAll('#rc-rows > div')].map(r => [r.querySelector('span').textContent, (r.querySelector('.src-btn') || r.querySelector('strong')).textContent,
                 !!r.querySelector('.src-btn'), (r.querySelector('.src-note') || {}).textContent || '']),
          note: document.getElementById('rc-note').textContent,
          link: (l => [l.textContent, l.getAttribute('href')])(document.getElementById('rc-link'))}))()""")
    old_src = _re.search(r'reels: \[\s*(.*?)\s*\],', OLD22['local.html'], _re.S).group(1)
    old_src = [_json.loads(x) for x in _re.findall(r'"(?:[^"\\]|\\.)*"', old_src)]
    WANT_SRC = K5_SRC_NEW + old_src[3:5]
    for when, prep in (('as first drawn', None), ('after the tabs switch away and back', lambda q: (q.click('button[data-tab="app"]'), q.wait_for_timeout(200), q.click('button[data-tab="reels"]'), q.wait_for_timeout(300)))):
        if prep:
            prep(q)
        rc = rc22(q)
        check(f'T-22 K5: the Reels tab\'s title is the new one ({when})', rc['title'] == K5_TITLE, rc['title'])
        check(f'T-22 K5: the Reels tab\'s date label stays AUG 2026 ({when})', rc['date'] == 'AUG 2026', rc['date'])
        check(f'T-22 K5: the Reels tab has these five rows, in this order, label then value ({when})', [(r[0], r[1]) for r in rc['rows']] == K5_ROWS, str(rc['rows']))
        check(f'T-22 K5: every orange number in the Reels tab has a tap-to-see source ({when})', len(rc['rows']) == 5 and all(r[2] and r[3].strip() for r in rc['rows']), str(rc['rows']))
        check(f'T-22 K5: the Reels tab\'s sources are the three new ones word for word, then the kept ones for "3 of 3" and "0" ({when})',
              [r[3] for r in rc['rows']] == WANT_SRC, str([r[3] for r in rc['rows']]))
        check(f'T-22 K5: the note under the rows is the new one ({when}; T-23 K5b read as K5)', back23(rc['note']) == K5_NOTE, rc['note'])
        check(f'T-22 K5: the "Open the repo →" link stays ({when})', rc['link'] == ['Open the repo →', 'https://github.com/stephensjosef-cloud/cobol-behavioral-equivalence'], str(rc['link']))
    check('T-22 K5: the kept sources for "3 of 3" and "0" are T-21\'s, word for word',
          old_src[3] == "The client's three notes from the first rounds. The tool now checks for each one automatically."
          and old_src[4] == "Every reel waits for the client's yes before it posts. None has gone out without it.", str(old_src))
    btns = q.locator('#rc-rows .src-btn')
    opened = []
    for i in range(btns.count()):
        btns.nth(i).click(); q.wait_for_timeout(80)
        opened.append(q.evaluate(f"(() => {{ const b = document.querySelectorAll('#rc-rows .src-btn')[{i}]; const n = document.getElementById(b.getAttribute('aria-controls')); return [b.getAttribute('aria-expanded'), !n.hidden, n.textContent] }})()"))
    check('T-22 K5: tapping each orange number shows its source', [o[2] for o in opened] == WANT_SRC and all(o[0] == 'true' and o[1] for o in opened), str(opened)[:300])
    # K7
    how = [back23(x) for x in q.evaluate("[...document.querySelectorAll('dt')].filter(d => d.textContent.trim() === 'HOW YOU KNOW IT WORKS').map(d => d.nextElementSibling.textContent.trim())")]   # T-23 K7b read as K7
    check('T-22 K7: the app offer\'s "HOW YOU KNOW IT WORKS" is the new line', K7 in how and len(how) == 3, str(how))
    q.close()
    # Left alone on local: the FAQ line, the About line and the Reels offer.
    for keep in ("Kids' programs get stricter rules: no child accounts and no child data, ever.",
                 "This year a Sonoma County children's nonprofit became my first client",
                 'Send your clips. Get a month of finished, captioned reels back.',
                 '8 or 12 captioned reels a month in the style you picked, all delivered by the 5th.'):
        check(f'T-22: local keeps "{keep[:40]}..."', TXT22['local.html'].count(keep) == 1, str(TXT22['local.html'].count(keep)))

    # K6 and K8 on work.html: tags, titles and links stay.
    def cards22(src):
        return _re.findall(r'<article class="card" data-k="nonprofit">.*?</article>', src, _re.S)
    new_c, old_c = cards22(un21(SRC22['work.html'])), cards22(un21(OLD22['work.html']))
    part = lambda c, rx: [_re.sub(r'<!--.*?-->', '', x).strip() for x in _re.findall(rx, c, _re.S)]
    check('T-22: work.html still has its two nonprofit cards', len(new_c) == 2 and len(old_c) == 2)
    if len(new_c) == 2 and len(old_c) == 2:
        check('T-22 K6: the reels card\'s headline, title and body are the new ones',
              (part(new_c[0], r'<p class="num">(.*?)</p>'), part(new_c[0], r'<h2>(.*?)</h2>'), part(new_c[0], r'</h2>\s*<p>(.*?)</p>')) == ([K6[0]], [K6[1]], [K6[2]]), new_c[0][:300])
        check('T-22 K8: the app card\'s headline and body are the new ones, its title stays',
              (part(new_c[1], r'<p class="num">(.*?)</p>'), part(new_c[1], r'<h2>(.*?)</h2>'), part(new_c[1], r'</h2>\s*<p>(.*?)</p>')) == ([K8_HEAD], ['A seasonal cooking app for teachers'], [K8]), new_c[1][:300])
        for i, k in ((0, 'K6'), (1, 'K8')):
            check(f'T-22 {k}: the card\'s tags and link stay as at T-21', part(new_c[i], r'<div class="tags">.*?</div>') == part(old_c[i], r'<div class="tags">.*?</div>')
                  and part(new_c[i], r'<a class="go"[^>]*>.*?</a>') == part(old_c[i], r'<a class="go"[^>]*>.*?</a>'), part(new_c[i], r'<a class="go"[^>]*>.*?</a>'))

    # K8 and K9 on the Studio page.
    q = newpage(1440); q.goto(UN29 + 'studio.html'); settle(q)   # T-30: the kids' card with its line, as at T-29 (un29() calls un30())
    kids = q.evaluate("""(() => { const c = [...document.querySelectorAll('.prod')].find(p => p.textContent.includes("A kids' cooking app"));
      return c ? c.outerHTML : '' })()""")
    kids = back23(kids)   # T-23 K8b read as K8
    log = q.evaluate("[...document.querySelectorAll('#log li')].map(li => [li.querySelector('time').getAttribute('datetime'), li.querySelector('.proj').textContent, li.querySelector('.line').textContent])")
    count = q.evaluate("[document.querySelector('#stats strong').textContent, document.getElementById('log-all') ? document.getElementById('log-all').textContent : '']")
    q.close()
    check('T-22 K8: the Studio\'s cooking app card has the new body', K8 in kids, kids[:200])
    old_kids = _re.search(r'<article class="prod[^"]*"[^>]*>(?:(?!</article>).)*A kids\' cooking app.*?</article>', OLD22['studio.html'], _re.S)
    new_kids = _re.search(r'<article class="prod[^"]*"[^>]*>(?:(?!</article>).)*A kids\' cooking app.*?</article>', SRC22['studio.html'], _re.S)
    check('T-22 K8: the Studio card differs from T-21 only by its body (tags, status, links stay)', bool(old_kids and new_kids) and
          new_kids.group(0) == old_kids.group(0).replace("Seasonal recipes a teacher leads the class through, a grocery list that scales to the class, and recipe pages that print like the program's own cards. iPhone, iPad, Android and the web.", K8),
          (new_kids.group(0)[:200] if new_kids else 'no card'))
    kid_log = [l for l in log if l[1] == "A kids' cooking app"]
    check('T-22 K9: the cooking app\'s log is the Oct 27 line, changed, and the Oct 6 line, kept', kid_log == [['2026-10-27', "A kids' cooking app", K9], ['2026-10-06', "A kids' cooking app", K9_KEPT]], str(kid_log))
    old_log = [[a, b_, c] for a, b_, c in _re.findall(r'<time class="mono" datetime="([^"]+)">[^<]*</time><span class="proj">([^<]*)</span><span class="line">([^<]*)</span>', OLD22['studio.html'])]
    old_log = [[a, _html.unescape(b_), _html.unescape(c)] for a, b_, c in old_log]
    want_log = [l for l in old_log if l[0] not in ('2026-11-08', '2026-10-07') or l[1] != "A kids' cooking app"]
    want_log = [[a, b_, K9 if (a, b_) == ('2026-10-27', "A kids' cooking app") else c] for a, b_, c in want_log]
    check('T-22 K9: every other log line is as at T-21', log == want_log, str(log)[:300])
    check('T-22 K9: the Studio\'s count matches the lines that show', count[0] == str(len(log)) and count[1] == f'See all {len(log)}', str(count) + f' / {len(log)} lines')
    sj = _json.loads(open(os.path.join(here, 'shipped.json'), encoding='utf-8').read())
    check('T-22 K9: shipped.json has neither removed line and the new Oct 27 line once',
          [e for e in sj['entries'] if e['project'] == 'kids'] == [{'date': '2026-10-27', 'project': 'kids', 'line': K9}, {'date': '2026-10-06', 'project': 'kids', 'line': K9_KEPT}])
    check('T-22 K8: studio.json carries the new body', any(p.get('id') == 'kids' and back23(what29(p)) == K8 for p in _json.loads(open(os.path.join(here, 'studio.json'), encoding='utf-8').read())['products']))

    # Everything else is as at T-21. Pages this item doesn't touch: byte for byte (the Studio pages' stamp aside).
    # T-24: the Studio's data-built day moves with the day the page is built (T-21's word checks already allow for it).
    stamp = lambda s: _re.sub(r'<!-- studio\.py \d{4}-\d\d-\d\d [0-9a-f]+ -->', '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))
    for n in ALL_HTML:
        if n in TXT22:
            continue
        check(f'T-22: {n} is as at T-21', stamp(SRC22[n]) == stamp(OLD22[n]),
              next((f'...{SRC22[n][max(0, i - 40):i + 40]}...' for i in range(min(len(SRC22[n]), len(OLD22[n]))) if SRC22[n][i] != OLD22[n][i]), ''))

    # The four changed pages: T-21's page with only this item's swaps applied, character for character.
    def swap(s, old, new, n=1):
        if s.count(old) != n:
            raise AssertionError(f'{s.count(old)} x {old[:70]}')
        return s.replace(old, new)
    HR = ('<div style="display: flex; justify-content: space-between; gap: 16px; align-items: baseline"><span style="color: #3E4640">%s</span>'
          '<span style="flex: 1; border-bottom: 1px dotted #A6AAA2; transform: translateY(-4px)"></span><strong style="font-weight: 700; color: #16201C; white-space: nowrap">%s</strong></div>')
    RR = ('<div style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 18px; padding: 12px 0; border-top: 1px solid #2B3D35; align-items: baseline">'
          '<span style="font-size: 14px; color: #B5C2BA; line-height: 1.45">%s</span><strong style="font-size: 18px; font-weight: 700; color: #F07A4E; text-align: right">%s</strong></div>')
    RJ = lambda rows: '"rows": [' + ', '.join('{"k": "%s", "v": "%s"}' % r for r in rows) + ']'
    K5_OLD = [('Clips in a typical cooking-class shoot', '16 to 20'), ('Captioned steps in the finished reel', '9'), ('Machine time for the whole episode', '~4 min'),
              ('Mistakes the client caught in the first three rounds', '3 of 3 fixed'), ('Reels posted without the client approving them', '0')]
    OLD_NOTE = ('Those three were uneven caption boxes, square corners and single words stranded on their own line. '
                'The tool now checks for all three on every reel, so nobody has to catch them twice.')
    try:
        s = un21(OLD22['case-reels.html'])
        s = swap(s, "Case study: one shoot, one finished reel · Dragoman's Journey", K1_TITLE, 2)
        s = swap(s, '<meta name="description" content="How a Sonoma County children\'s nonprofit turns its kids\' cooking-class footage into finished, captioned reels with about four minutes of machine time each.">',
                 '<meta name="description" content="' + K1 + '">')
        s = swap(s, '<meta property="og:description" content="From a phone full of cooking-class clips to a finished, captioned reel.">', '<meta property="og:description" content="' + K1 + '">')
        s = swap(s, '>One shoot, one finished reel</h1>', '>' + K1_H1 + '</h1><!-- T-22 K1 -->')
        s = swap(s, ">How a Sonoma County children's nonprofit turns its kids' cooking-class footage into finished reels, without anyone giving up their evenings to edit.</p>", '>' + K1 + '</p><!-- T-22 K1 -->')
        a_, b2 = s.index('      <div class="stats" style="margin-top:10px">\n'), s.index('      </div>\n', s.index('<div class="stats"'))
        s = s[:a_] + '      <div class="stats" style="margin-top:10px"><!-- T-22 K2 -->\n' + ''.join(f'        <div class="stat"><b>{v}</b><span>{k}</span></div>\n' for v, k in K2) + s[b2:]
        a_, b2 = s.index('  <section class="sec" aria-labelledby="c1">'), s.index('  <section aria-labelledby="c7"')
        s = s[:a_] + ('  <section class="sec" aria-labelledby="c1"><!-- T-22 K3 -->\n    <h2 id="c1">How it works</h2>\n    <div>\n      <p>' + K3 + '</p>\n    </div>\n  </section>\n\n') + s[b2:]
        check('T-22: case-reels is T-21\'s page with only K1 to K3 changed', un21(SRC22['case-reels.html']) == s,
              next((f'...{un21(SRC22["case-reels.html"])[max(0, i - 60):i + 60]}... | ...{s[max(0, i - 60):i + 60]}...' for i in range(min(len(s), len(un21(SRC22["case-reels.html"])))) if s[i] != un21(SRC22['case-reels.html'])[i]), 'length'))
    except AssertionError as e:
        check('T-22: case-reels is T-21\'s page with only K1 to K3 changed', False, str(e))
    try:
        s = un21(OLD22['local.html'])
        s = swap(s, '>One cooking class, filmed on a phone, turned into a finished reel. August 2026.</p>', '>' + K4_LINE + '</p>')
        s = swap(s, ''.join(HR % r for r in [('Clips in a typical class', '16 to 20'), ('Sorts the footage at', '29× real time'), ('Captioned steps', '9'),
                                              ('Feedback notes it now checks for itself', '3 of 3'), ('Computer time, start to finish', '~4 min')]), ''.join(HR % r for r in K4_ROWS))
        s = swap(s, 'The app refuses broken entries, like a recipe with no photo. It runs hundreds of automatic checks every time it changes, and your staff try it before any family does.', K7)
        s = swap(s, '>One shoot, one finished reel</h3>', '>' + K5_TITLE + '</h3>')
        s = swap(s, '"title": "One shoot, one finished reel"', '"title": "' + K5_TITLE + '"')
        s = swap(s, ''.join(RR % r for r in K5_OLD), ''.join(RR % (k, v) for k, v in K5_ROWS))
        s = swap(s, RJ(K5_OLD), RJ(K5_ROWS))
        s = swap(s, '>' + OLD_NOTE + '</p>', '>' + K5_NOTE + '</p>')
        s = swap(s, '"note": "' + OLD_NOTE + '"', '"note": "' + K5_NOTE + '"')
        for o, n_ in zip(old_src[:3], K5_SRC_NEW):
            s = swap(s, '      ' + _json.dumps(o) + ',\n', '      ' + _json.dumps(n_) + ',\n')
        check('T-22: local is T-21\'s page with only K4, K5 and K7 changed', un21(SRC22['local.html']) == s,
              next((f'...{un21(SRC22["local.html"])[max(0, i - 60):i + 60]}... | ...{s[max(0, i - 60):i + 60]}...' for i in range(min(len(s), len(un21(SRC22["local.html"])))) if s[i] != un21(SRC22['local.html'])[i]), 'length'))
    except AssertionError as e:
        check('T-22: local is T-21\'s page with only K4, K5 and K7 changed', False, str(e))
    try:
        s = un21(OLD22['work.html'])
        s = swap(s, '''      <p class="num">An 81-second reel in about 4 minutes</p>
      <h2>One cooking-class shoot, one finished reel</h2>
      <p>Phone clips from a cooking class at a Sonoma County children's nonprofit became a finished, captioned reel with about four minutes of machine time. Every reel waits for the client's yes.</p>''',
                 '      <!-- T-22 K6 -->\n      <p class="num">%s</p>\n      <h2>%s</h2>\n      <p>%s</p>' % K6)
        s = swap(s, '      <p class="num">535 automatic checks</p>\n', '      <!-- T-22 K8 -->\n      <p class="num">' + K8_HEAD + '</p>\n')
        s = swap(s, "<p>Seasonal recipes a teacher leads the class through, a grocery list that scales to the class, and recipe pages that print like the program's own cards. iPhone, iPad, Android and the web.</p>", '<p>' + K8 + '</p>')
        check('T-22: work is T-21\'s page with only K6 and K8 changed', un21(SRC22['work.html']) == s,
              next((f'...{un21(SRC22["work.html"])[max(0, i - 60):i + 60]}... | ...{s[max(0, i - 60):i + 60]}...' for i in range(min(len(s), len(un21(SRC22["work.html"])))) if s[i] != un21(SRC22['work.html'])[i]), 'length'))
    except AssertionError as e:
        check('T-22: work is T-21\'s page with only K6 and K8 changed', False, str(e))
    # studio.html: outside its log and its count, T-21's page with only K8's body changed.
    unlog = lambda x: _re.sub(r'<ol class="log" id="log">.*?</ol>', '', _re.sub(r'<strong>\d+</strong> things finished|See all \d+', '#', stamp(x)), flags=_re.S)
    s = unlog(OLD22['studio.html']).replace("Seasonal recipes a teacher leads the class through, a grocery list that scales to the class, and recipe pages that print like the program's own cards. iPhone, iPad, Android and the web.", K8)
    check('T-22: studio is T-21\'s page with only K8 and K9 changed (log and count checked above)', unlog(SRC22['studio.html']) == s)

    # Same input, same result: the forms and tools on the four changed pages are untouched code.
    for n in TXT22:
        js = lambda x: [_re.sub(r'\s+', ' ', j) for j in _re.findall(r'<script(?![^>]*ld\+json)[^>]*>(.*?)</script>', stamp(x), _re.S)]
        a, b_ = js(un21(SRC22[n])), js(un21(OLD22[n]))
        if n == 'local.html':   # the tap sources (K5) and the tabs' state data (K5) are the only script changes
            a = [_re.sub(r'reels: \[.*?\],', '', _re.sub(r'"rc": \{"head": "RESULT · REELS".*?"linkLabel": ""\}', '', x)) for x in a]
            b_ = [_re.sub(r'reels: \[.*?\],', '', _re.sub(r'"rc": \{"head": "RESULT · REELS".*?"linkLabel": ""\}', '', x)) for x in b_]
        check(f'T-22: {n} runs the same scripts as at T-21 (K5\'s sources and state data aside)', a == b_)

    # The look: no sideways scroll, and every new line inside its box, at 320, 390 and 1440.
    for n in TXT22:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(200)
            sw = q.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
            check(f'T-22: {n} has no sideways scroll at {w}', sw[0] <= sw[1], str(sw))
            q.close()


# ---------------- T-23 (Nov 16, 2026): Kids Kitchen, the person back in, plus layout leftovers ----------------
@section('T-23')
def s_t_23():
    # Josef's lines K3b, K5b, K7b and K8b, word for word, and L1 to L7 (layout only). Comparisons are
    # against T-22's own pages (origin/main at 98eef4f, the base this item was cut from), read from git.
    T22C = '98eef4f93f38a732b8ac1c9b458dd747e8803f4f'
    T22_FILES = {}

    def t22_file(path):
        if path not in T22_FILES:
            r = _sp18.run(['git', 'show', f'{T22C}:{path}'], cwd=here, capture_output=True)
            T22_FILES[path] = r.stdout if r.returncode == 0 else None
        return T22_FILES[path]

    def t22_page(w, h=900):
        """A page that can open T-22's own build at BASE + '__t22/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t22/', 1)[1].split('?')[0].split('#')[0]
            body = t22_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t22/**', serve)
        return q
    OLD23B = BASE + '__t22/'
    check('T-23: the T-22 pages can be read from git for comparison', t22_file('studio.html') is not None and t22_file('og/case-reels.png') is not None)
    SRC23 = {n: un24(un25(un26(un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n), n)) for n in ALL_HTML}   # T-26: the gallery out first   # T-24: A1 to A7 read back as T-23's (its block checks them); T-25: its layout swaps out   # T-30: local's descriptions back
    OLD23 = {n: t22_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    K3_22, K5_22, K7_22, K8_22 = (o for o, _ in T23_LINES)
    K3B, K5B, K7B, K8B = (n_ for _, n_ in T23_LINES)
    # T-24: the Studio's data-built day moves with the day the page is built (T-21's word checks already allow for it).
    stamp23 = lambda s: _re.sub(r'<!-- studio\.py \d{4}-\d\d-\d\d [0-9a-f]+ -->', '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))
    TOOLS23 = ('captions.html', 'checkup.html', 'receipt.html', 'scaler.html', 'shotlist.html')
    CHANGED23 = ['captions.html', 'case-reels.html', 'checkup.html', 'local.html', 'mainframe.html', 'receipt.html', 'scaler.html',
                 'shotlist.html', 'studio-birdleague.html', 'studio-deepcuts.html', 'studio.html', 'work.html']

    # The whole build: T-22's pages with only T-23's changes. un23() takes each change back out,
    # and what is left is T-22's page byte for byte (the Studio pages' build stamp aside).
    for n in ALL_HTML:
        a, b_ = stamp23(un23(SRC23[n], n)), stamp23(OLD23[n])
        check(f'T-23: {n} is T-22\'s page with only T-23\'s changes', a == b_,
              next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
    got23 = sorted(n for n in ALL_HTML if stamp23(SRC23[n]) != stamp23(OLD23[n]))
    check('T-23: the pages that changed are these twelve and no others', got23 == CHANGED23, str(got23))
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>')):
            check(f'T-23: {n} keeps its {what}', _re.findall(rx, SRC23[n], _re.S) == _re.findall(rx, OLD23[n], _re.S))
    ogs = sorted(os.listdir(os.path.join(here, '..', 'og')))
    check('T-23: every share card in og/ is byte for byte as at T-22', len(ogs) == 17 and all(
        open(os.path.join(here, '..', 'og', f), 'rb').read() == t22_file('og/' + f) for f in ogs), str(len(ogs)))
    check('T-23: every share card in _build/assets/og/ is byte for byte as at T-22', all(
        open(os.path.join(here, 'assets', 'og', f), 'rb').read() == t22_file('_build/assets/og/' + f) for f in ogs))
    check('T-23: no em dash on any changed page, and no new en dash (the scaler\'s parser reads "1–2" ranges, as at T-22)',
          not any('—' in SRC23[n] for n in CHANGED23) and all(SRC23[n].count('–') == OLD23[n].count('–') for n in CHANGED23))

    # Words: every page reads as at T-22, apart from the four lines (and the Studio's closing call, L6).
    TXT23 = {}
    BOX23 = None
    for n in ALL_HTML:
        q = newpage(1440); q.goto((UN29 if n == 'studio.html' else UN30) + n); settle(q)   # T-30: local's descriptions back (un30)   # T-29: studio's text as at T-27 (un29): TEXT_JS leaves the gallery out, which now holds the two cards' words
        TXT23[n] = q.evaluate(TEXT_JS)
        if n == 'studio.html':
            BOX23 = q.evaluate("(() => { const s = document.querySelector('section[aria-labelledby=\"next-h\"]'); return s ? s.textContent.replace(/[\\s\\u00a0]+/g, ' ').trim() : '' })()")
        q.close()
        q = t22_page(1440); q.goto(OLD23B + n); settle(q)
        old_t = q.evaluate(TEXT_JS); q.close()
        a = back27(un24(TXT23[n]))   # T-24: A1 to A7 read back as T-23's (the T-24 block checks them); T-27: the ChuckleFits line read back as T-26's
        for o, n_ in T23_LINES:
            a = a.replace(n_, o)
        if n == 'studio.html' and BOX23:
            a = a.replace(' ' + BOX23 + ' ', ' ', 1)
        if n.startswith('studio'):
            a, old_t = (_re.sub(r'\b(?:Nov|Oct|Sep|Aug|Jul) \d{1,2}\b|\b\d+ (?:days?|lines?|things?)\b', '#', x) for x in (a, old_t))
        check(f'T-23: {n} reads word for word as at T-22, apart from K3b, K5b, K7b, K8b and L6\'s closing call', a == old_t,
              next((f'...{a[max(0, i - 40):i + 40]}... | ...{old_t[max(0, i - 40):i + 40]}...' for i in range(min(len(a), len(old_t))) if a[i] != old_t[i]), f'{len(a)} vs {len(old_t)}'))
    for kid, n, line, old in (('K3b', 'case-reels.html', K3B, K3_22), ('K5b', 'local.html', K5B, K5_22), ('K7b', 'local.html', K7B, K7_22),
                              ('K8b', 'work.html', K8B, K8_22), ('K8b', 'studio.html', K8B, K8_22)):
        check(f'T-23 {kid}: "{line[:48]}" is on {n} word for word, exactly once', TXT23[n].count(line) == 1, str(TXT23[n].count(line)))
        check(f'T-23 {kid}: T-22\'s line ("{old[:40]}...") is gone from {n}, text and source', old not in TXT23[n] and old not in un21(SRC23[n]))
    for n in ALL_HTML:
        check(f'T-23: none of T-22\'s four replaced lines is on {n}', not any(o in un21(SRC23[n]) for o, _ in T23_LINES))
    check('T-23 K5b: the note is in the tabs\' state data once, word for word', SRC23['local.html'].count('"note": "' + K5B + '"') == 1)
    q = newpage(390); q.goto(BASE + 'local.html'); settle(q)
    notes = [q.evaluate("document.getElementById('rc-note').textContent")]
    for away in ('app', 'method'):
        q.click(f'button[data-tab="{away}"]'); q.wait_for_timeout(200); q.click('button[data-tab="reels"]'); q.wait_for_timeout(300)
        notes.append(q.evaluate("document.getElementById('rc-note').textContent"))
    rows = q.evaluate("[...document.querySelectorAll('#rc-rows > div')].map(r => [r.querySelector('span').textContent, (r.querySelector('.src-btn') || r.querySelector('strong')).textContent])")
    q.close()
    check('T-23 K5b: the Reels note reads K5b as first drawn and after switching to Apps and to COBOL checking and back', notes == [K5B] * 3, str(notes))
    check('T-23 K5b: the Reels rows stay as T-22 left them', [tuple(r) for r in rows] == K5_ROWS, str(rows))
    # Where each line lives, with its ID.
    rd = lambda f: open(os.path.join(here, f), encoding='utf-8').read()
    check('T-23 K3b: in _build/case-reels.html with its ID', 'T-23 K3b' in rd('case-reels.html') and rd('case-reels.html').count(K3B) == 1)
    check('T-23 K5b and K7b: voice2.py edits with their IDs', rd('voice2.py').count("ref='K5b'") == 2 and rd('voice2.py').count("ref='K7b'") == 1)
    check('T-23 K8b: in _build/work.html with its ID, and the kids product in studio.json', 'T-23 K8b' in rd('work.html') and rd('work.html').count(K8B) == 1
          and any(p.get('id') == 'kids' and what29(p) == K8B for p in _json.loads(rd('studio.json'))['products']))   # T-30: the kids' "what" as at T-29 (null now; the T-30 block checks it)
    check('T-23: the Studio card\'s proof line stays', "535 tests, and every change checked on a real phone before it ships." in TXT23['studio.html'])

    # L1: a two-hyphen word up to 24 characters never breaks, on any page, at 320, 390 and 1440.
    L1_JS = r'''(() => {
      const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {acceptNode(n) {
        const p = n.parentElement; if (!p || p.closest('script,style,code,pre,textarea,svg,[hidden]')) return 2; return p.getClientRects().length ? 1 : 2; }});
      let n; while ((n = w.nextNode())) { for (const m of n.data.matchAll(/(?<![\w-])[A-Za-z0-9]+(?:-[A-Za-z0-9]+){2}(?![\w-])/g)) {
        const tops = new Set(); for (let i = m.index; i < m.index + m[0].length; i++) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
          const b = [...r.getClientRects()].find(x => x.width > 0.5); if (b) tops.add(Math.round(b.top)); }
        out.push([m[0], !!n.parentElement.closest('[style*="white-space: nowrap"]'), tops.size]); } }
      return out; })()'''
    seen23 = set()
    for n in ALL_HTML:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(200)
            r = [x for x in q.evaluate(L1_JS) if len(x[0]) <= 24]; q.close()
            seen23.update(x[0] for x in r)
            check(f'T-23 L1: at {w}, every two-hyphen word on {n} is in a no-wrap span and on one line', all(x[1] and x[2] == 1 for x in r), str([x for x in r if not (x[1] and x[2] == 1)]))
            if n == 'mainframe.html':
                check(f'T-23 L1: "year-to-date" on mainframe is on one line at {w}', any(x[0] == 'year-to-date' and x[2] == 1 for x in r), str(r))
    check('T-23 L1: the two-hyphen words found are year-to-date, side-by-side and DEP-INTEREST-YTD', seen23 == {'year-to-date', 'side-by-side', 'DEP-INTEREST-YTD'}, str(seen23))
    nws = [x for n in ALL_HTML for x in _re.findall(r'<span style="white-space: nowrap">([^<]*)</span>', SRC23[n])]
    check('T-23 L1: no new span holds more than two hyphens or more than 24 characters',
          not [x for x in nws if '-' in x and (x.count('-') > 2 or len(x) > 24) and x not in _re.findall(r'<span style="white-space: nowrap">([^<]*)</span>', ''.join(OLD23.values()))])
    check('T-23 L1: nothing new is wrapped inside script, style, code or pre', all(
        len(_re.findall(r'<(script|style|code|pre)\b[^>]*>(?:(?!</\1>).)*white-space: nowrap', SRC23[n], _re.S)) ==
        len(_re.findall(r'<(script|style|code|pre)\b[^>]*>(?:(?!</\1>).)*white-space: nowrap', OLD23[n], _re.S)) for n in ALL_HTML))
    check('T-23 L1: no address or email holds a new span', not any(_re.search(r'(?:href|src|content)="[^"]*<span', SRC23[n]) for n in ALL_HTML))

    # L2: case-reels' h1 lines don't touch: each line's ink clears the next.
    INK23 = r'''(() => {
      const el = document.querySelector('h1'); const cs = getComputedStyle(el); const cv = document.createElement('canvas').getContext('2d');
      cv.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`; const lines = [];
      const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) for (let i = 0; i < n.data.length; i++) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        const b = [...r.getClientRects()].find(x => x.width > 0.5); if (!b) continue;
        let L = lines.find(l => Math.abs(l.top - b.top) < 4); if (!L) { L = {top: b.top, text: ''}; lines.push(L); } L.text += n.data[i]; }
      return lines.map(l => { const t = cs.textTransform === 'uppercase' ? l.text.toUpperCase() : l.text; const m = cv.measureText(t.trim()); const base = l.top + m.fontBoundingBoxAscent;
        return [t.trim(), base - m.actualBoundingBoxAscent, base + m.actualBoundingBoxDescent]; }); })()'''
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'case-reels.html'); settle(q)
        ln = q.evaluate(INK23); lh = q.evaluate("[getComputedStyle(document.querySelector('h1')).lineHeight, getComputedStyle(document.querySelector('h1')).fontSize]"); q.close()
        gaps = [round(ln[i + 1][1] - ln[i][2], 1) for i in range(len(ln) - 1)]
        check(f'T-23 L2: at {w}, each line of case-reels\' h1 clears the next (ink gaps {gaps})', len(ln) >= 2 and all(g >= 1 for g in gaps), str(ln))
        check(f'T-23 L2: at {w}, case-reels\' h1 line height is its font size', lh[0] == lh[1], str(lh))

    # L3: local's reply-status words share the closing buttons' left edge at every width.
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); settle(q)
        r = q.evaluate('''(() => { const a = document.querySelector('#contact a.btn-blaze').getBoundingClientRect().left; const s = document.getElementById('sr-status');
          const g = document.createRange(); g.selectNodeContents(s); const t = g.getClientRects()[0]; const d = document.getElementById('sr-dot');
          return [a, t ? t.left : null, s.textContent, getComputedStyle(d).display, d.getBoundingClientRect().right]; })()''')
        q.close()
        check(f'T-23 L3: at {w}, the reply-status line starts on the buttons\' left edge', r[1] is not None and abs(r[0] - r[1]) <= 1 and r[2].startswith("I'm "), str(r))
        if w < 700:
            check(f'T-23 L3: at {w}, the dot is not shown (no empty slot in front of the words)', r[3] == 'none', str(r))
        else:
            check(f'T-23 L3: at {w}, the dot shows, hanging left of the words', r[3] != 'none' and r[4] < r[1], str(r))

    # L4: the "More free tools" names never wrap, and no visible dot starts or ends a row.
    MT_JS = r'''(() => { const p = [...document.querySelectorAll('main p')].find(x => x.textContent.includes('More free tools:')); const pb = p.getBoundingClientRect();
      const links = [...p.querySelectorAll('a')].map(a => { const rs = [...a.getClientRects()].filter(x => x.width > 0.5); return [a.textContent, new Set(rs.map(x => Math.round(x.top))).size, Math.round(rs[0].top), rs[0].left, rs[rs.length - 1].right]; });
      const dots = []; const w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const i = n.data.indexOf('·'); if (i < 0) continue; const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getClientRects()[0]; dots.push([Math.round(b.top), b.left >= pb.left && b.right <= pb.right, b.right <= pb.left]); }
      return {links, dots, pl: pb.left, over: p.scrollWidth > p.clientWidth, text: p.textContent.replace(/[\s ]+/g, ' ').trim()}; })()'''
    for t in TOOLS23:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + t); settle(q); q.wait_for_timeout(200)
            r = q.evaluate(MT_JS); q.close()
            L = r['links']
            check(f'T-23 L4: at {w}, no tool name in {t}\'s "More free tools" line wraps', len(L) >= 2 and all(x[1] == 1 for x in L), str(L))   # T-33 R21: two names on three of the pages
            # dot k sits between name k and name k+1
            okd = len(r['dots']) == len(L) - 1
            for k, (top, vis, hid) in enumerate(r['dots'] if okd else []):
                same_row = L[k][2] == L[k + 1][2]
                okd = okd and ((vis and same_row and abs(top - L[k][2]) <= 2) or (hid and not same_row))
            check(f'T-23 L4: at {w}, on {t} a dot shows only between two names on one row, and the dot in front of a name that starts a row is out of sight', okd, str(r['dots']) + ' ' + str(L))
            check(f'T-23 L4: at {w}, a name that starts a row sits on the line\'s left edge with room for its focus ring', all(x[3] - r['pl'] >= 5.5 for x in L), str([x[3] - r['pl'] for x in L]))
            check(f'T-23 L4: at {w}, {t}\'s "More free tools" line has no sideways overflow', not r['over'])
            check(f'T-23 L4: {t}\'s "More free tools" line reads as before', r['text'] == 'More free tools: ' + ' · '.join(x[0] for x in L), r['text'])

    # L5: "4 minutes." on one line, and every number with its unit in a card headline on work, local and case-reels.
    PAIR_JS = r'''([sel, needle]) => [...document.querySelectorAll(sel)].filter(e => e.textContent.includes(needle)).map(el => {
      const k = el.textContent.indexOf(needle); const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n, pos = 0; const tops = new Set();
      while ((n = w.nextNode())) { for (let i = 0; i < n.data.length; i++, pos++) { if (pos < k || pos >= k + needle.length || !n.data[i].trim()) continue;
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const b = [...r.getClientRects()].find(x => x.width > 0.5); if (b) tops.add(Math.round(b.top)); } }
      return tops.size; })'''
    PAIRS23 = [('work.html', 'p.num', '4 minutes.'), ('work.html', 'p.num', '2 AI'), ('local.html', 'figure.rise3 strong', '~4 min'),
               ('local.html', '#rc-rows strong, #rc-rows .src-btn', '~4 min'), ('local.html', '#rc-rows strong, #rc-rows .src-btn', '3 of 3'),
               ('case-reels.html', '.stat b', '~4 min')]
    for w in (320, 390, 1440):
        for n, sel, needle in PAIRS23:
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(200)
            r = q.evaluate(PAIR_JS, [sel, needle]); q.close()
            check(f'T-23 L5: at {w}, "{needle}" on {n} is on one line', len(r) >= 1 and all(x == 1 for x in r), str(r))
    check('T-23 L5: "4 minutes." sits in a no-wrap span on work', SRC23['work.html'].count('about <span style="white-space: nowrap">4 minutes.</span></p>') == 1)

    # L6: the Studio page ends with work's closing call box, the same markup, words and links.
    BOX_WORDS = ['Your pile could be next', 'Two weeks, $1,500, and it comes off the build price. Or start with a free 15-minute call.']
    BOX_LINKS = [['Start a Blueprint →', 'start.html'], ['Free 15-minute call', 'call.html']]
    boxes = {}
    for n in ('work.html', 'studio.html'):
        q = newpage(1440); q.goto(BASE + n); settle(q)
        boxes[n] = q.evaluate('''(() => { const s = [...document.querySelectorAll('section[aria-labelledby="next-h"]')];
          if (s.length !== 1) return {n: s.length}; const x = s[0];
          return {n: 1, html: x.outerHTML, words: [x.querySelector('h2').textContent, x.querySelector('p').textContent],
                  links: [...x.querySelectorAll('a')].map(a => [a.textContent, a.getAttribute('href')]),
                  last: x === document.querySelector('main').lastElementChild, prev: (x.previousElementSibling || {}).id || '',
                  prevGal: !!(x.previousElementSibling && x.previousElementSibling.getAttribute('aria-labelledby') === 'gallery-h'
                              && (x.previousElementSibling.previousElementSibling || {}).id === 'products')}; })()''')
        q.close()
    st, wk = boxes['studio.html'], boxes['work.html']
    check('T-23 L6: studio has one closing call box', st.get('n') == 1, str(st.get('n')))
    check('T-23 L6: studio\'s box is work\'s box, the same markup character for character', st.get('html') == wk.get('html') and bool(st.get('html')))
    check('T-23 L6: the box\'s words are work\'s exactly', st.get('words') == BOX_WORDS and wk.get('words') == BOX_WORDS, str(st.get('words')))
    check('T-23 L6: the box\'s links are "Start a Blueprint →" to start.html and "Free 15-minute call" to call.html', st.get('links') == BOX_LINKS and wk.get('links') == BOX_LINKS, str(st.get('links')))
    check('T-23 L6: on studio the box comes right after the products (T-26: or right after the gallery, which comes right after them) and ends the page\'s main',
          st.get('last') is True and (st.get('prev') == 'products' or st.get('prevGal') is True), str(st.get('prev')))
    check('T-23 L6: built from work\'s source, not a copy (neither studio.py nor its page holds the box; enhance.py lifts it from work.html)',
          'next-h' not in rd('studio.html') and 'next-h' not in rd(os.path.join('tools', 'studio.py')) and 'def add_closing_call' in rd('enhance.py')
          and '(HERE / "work.html")' in rd('enhance.py'))
    from collections import Counter as _C23
    check('T-23 L6: studio\'s links are T-22\'s plus start.html and call.html', _C23(_re.findall(r'href="([^"]*)"', SRC23['studio.html'])) - _C23(_re.findall(r'href="([^"]*)"', OLD23['studio.html'])) == _C23(['start.html', 'call.html'])
          and not (_C23(_re.findall(r'href="([^"]*)"', OLD23['studio.html'])) - _C23(_re.findall(r'href="([^"]*)"', SRC23['studio.html']))))

    # L7: the count sits with "Shipped lately" on wide screens; on phones it stays as at T-22.
    L7_JS = r'''(() => { const h = document.getElementById('log-h'), s = document.querySelector('#stats strong'), st = document.getElementById('stats');
      const probe = el => { const z = document.createElement('span'); z.style.cssText = 'display:inline-block;width:0;height:0'; el.appendChild(z); const y = z.getBoundingClientRect().top; z.remove(); return y; };
      const g = document.createRange(); g.selectNodeContents(h); const hr = g.getClientRects();
      return {hb: probe(h), sb: probe(s), hRight: hr[hr.length - 1].right, sLeft: s.getBoundingClientRect().left, stW: st.getBoundingClientRect().width,
              mainW: document.querySelector('main').clientWidth, st: [st.getBoundingClientRect().top, st.getBoundingClientRect().height], h: [h.getBoundingClientRect().top, h.getBoundingClientRect().height],
              n: s.textContent, lines: document.querySelectorAll('#log li').length, all: (document.getElementById('log-all') || {}).textContent || ''}; })()'''
    for w in (1024, 1440):
        q = newpage(w); q.goto(BASE + 'studio.html'); settle(q)
        r = q.evaluate(L7_JS); q.close()
        check(f'T-23 L7: at {w}, the count sits beside "Shipped lately", on its baseline', abs(r['hb'] - r['sb']) <= 1.5 and r['sLeft'] > r['hRight'], str(r))
        check(f'T-23 L7: at {w}, the count is no longer a full-width band', r['stW'] < r['mainW'] / 2, str(r))
        check(f'T-23 L7: at {w}, the count still equals the log lines that show', r['n'] == str(r['lines']) and r['all'] == f'See all {r["lines"]}', str(r))
    def un25_page(w, h=900):
        """T-25: a page that opens this build at BASE + '__un25/<file>' with T-25's swaps taken out (un25),
        for the positions T-23 L7 compares with T-22 on phones (T-25 F4 moves them on purpose; its block checks F4)."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__un25/', 1)[1].split('?')[0].split('#')[0]
            body = urlopen(BASE + path).read()
            if path.endswith('.html'):
                body = un25(body.decode('utf-8').replace('\r\n', '\n'), path).encode('utf-8')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__un25/**', serve)
        return q
    for w in (320, 390):
        q = un25_page(w); q.goto(BASE + '__un25/studio.html'); settle(q); r = q.evaluate(L7_JS); q.close()   # T-25: read through un25 (F4)
        q = t22_page(w); q.goto(OLD23B + 'studio.html'); settle(q); o = q.evaluate(L7_JS); q.close()
        check(f'T-23 L7: at {w}, the count band and the heading sit where they did at T-22', all(abs(a - b_) <= 1 for a, b_ in zip(r['st'] + r['h'], o['st'] + o['h'])), f'{r["st"] + r["h"]} vs {o["st"] + o["h"]}')
        check(f'T-23 L7: at {w}, the count still equals the log lines that show', r['n'] == str(r['lines']) == o['n'], str(r))

    # No sideways scroll on any changed page.
    for n in CHANGED23:
        for w in (320, 390, 1440):
            q = newpage(w); q.goto(BASE + n); settle(q); q.wait_for_timeout(200)
            sw = q.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); q.close()
            check(f'T-23: {n} has no sideways scroll at {w}', sw[0] <= sw[1], str(sw))


# ---------------- T-24 (Nov 17, 2026): Exhibit A says what is stored ----------------
@section('T-24')
def s_t_24():
    # Josef's lines A1 to A7, word for word (mainframe A1 to A5, comp3 A6 and A7). Comparisons are
    # against T-23's own pages (origin/main at 78bf1e6, the base this item was cut from), read from git.
    T23C = '78bf1e632a752b8ea9ef89536e342bcf9ed90758'
    T23_FILES = {}

    def t23_file(path):
        if path not in T23_FILES:
            r = _sp18.run(['git', 'show', f'{T23C}:{path}'], cwd=here, capture_output=True)
            T23_FILES[path] = r.stdout if r.returncode == 0 else None
        return T23_FILES[path]

    def t23_page(w, h=900):
        """A page that can open T-23's own build at BASE + '__t23/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t23/', 1)[1].split('?')[0].split('#')[0]
            body = t23_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t23/**', serve)
        return q
    OLD24B = BASE + '__t23/'
    check('T-24: the T-23 pages can be read from git for comparison', t23_file('mainframe.html') is not None and t23_file('comp3.html') is not None)
    SRC24 = {n: un26(un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n) for n in ALL_HTML}   # T-26: the gallery out (its block checks it)   # T-30: studio's and local's paragraphs back (the T-30 block checks them)
    OLD24 = {n: t23_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT24 = {n: open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n') for n in ('mainframe.html', 'comp3.html')}
    # The Studio pages carry the day they were built (a comment and data-built); nothing else on them moves.
    stamp24 = lambda s: _re.sub(r'<!-- studio\.py \d{4}-\d\d-\d\d [0-9a-f]+ -->', '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))
    OLD_PHRASES24 = ('A fraction', 'A percentage', 'Read as a fraction', 'Read as a percentage', 'read as a percentage',
                     'as the bank stored it', 'What the bank means', 'field definition allows two readings')

    # The whole build: T-23's pages with only T-24's seven lines. un24() swaps each back, and what is left
    # is T-23's page byte for byte (the Studio pages' build day aside).
    for n in ALL_HTML:
        a, b_ = stamp24(un24(un25(SRC24[n], n))), stamp24(OLD24[n])   # T-25: its layout swaps out first (its block checks them)
        check(f'T-24: {n} is T-23\'s page with only T-24\'s lines', a == b_,
              next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
    got24 = sorted(n for n in ALL_HTML if stamp24(un25(SRC24[n], n)) != stamp24(OLD24[n]))   # T-25's seven pages read with its swaps out
    check('T-24: the pages that changed are comp3.html and mainframe.html and no others', got24 == ['comp3.html', 'mainframe.html'], str(got24))
    check('T-24: the root mainframe.html and comp3.html are the built pages', not t32_root_off(ROOT24))   # T-32: the themed build
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>')):
            check(f'T-24: {n} keeps its {what}', _re.findall(rx, SRC24[n], _re.S) == _re.findall(rx, OLD24[n], _re.S))
    ogs = sorted(os.listdir(os.path.join(here, '..', 'og')))
    check('T-24: every share card in og/ is byte for byte as at T-23', len(ogs) == 17 and all(
        open(os.path.join(here, '..', 'og', f), 'rb').read() == t23_file('og/' + f) for f in ogs), str(len(ogs)))
    check('T-24: every share card in _build/assets/og/ is byte for byte as at T-23', all(
        open(os.path.join(here, 'assets', 'og', f), 'rb').read() == t23_file('_build/assets/og/' + f) for f in ogs))
    check('T-24: no em dash on mainframe or comp3, and no new en dash',
          not any('—' in SRC24[n] for n in ROOT24) and all(SRC24[n].count('–') == OLD24[n].count('–') for n in ROOT24))

    # Each line, word for word, exactly once in its page's source; every old phrase gone.
    for aid, n, old, new in T24_LINES:
        check(f'T-24 {aid}: {n} holds "{new}" exactly once', SRC24[n].count(new) == 1 and ROOT24[n].count(new) == 1, str(SRC24[n].count(new)))
    for n in ROOT24:
        for ph in OLD_PHRASES24:
            check(f'T-24: "{ph}" is gone from {n}', ph not in SRC24[n] and ph not in ROOT24[n])
    check('T-24 A6: the two example buttons keep their data-b and data-p values, in the same order',
          _re.findall(r'<button type="button" class="chip" (data-b="[^"]*" data-p="[^"]*")>', SRC24['comp3.html'])
          == _re.findall(r'<button type="button" class="chip" (data-b="[^"]*" data-p="[^"]*")>', OLD24['comp3.html']))
    check('T-24 A6: "Exhibit A, stored as 3.5" is the 03 50 00 0C button and "Exhibit A, stored as 0.035" the 00 03 50 0C one',
          'data-b="03 50 00 0C" data-p="S9(2)V9(5)">Exhibit A, stored as 3.5</button>' in SRC24['comp3.html']
          and 'data-b="00 03 50 0C" data-p="S9(2)V9(5)">Exhibit A, stored as 0.035</button>' in SRC24['comp3.html'])

    # Where each line lives, with its ID: mainframe's in voice2.py (the canvas isn't touched), comp3's in its template.
    rd = lambda f: open(os.path.join(here, f), encoding='utf-8').read()
    v2 = rd('voice2.py')
    check('T-24: voice2.py writes A1 to A5, each with its ID', all(f"ref='{a}')" in v2 for a in ('A1', 'A2', 'A3', 'A4', 'A5')))
    check('T-24: the Mainframe canvas is as at T-23 (T-34: its <em> to <span> lines out, through un34())',
          un34(open(os.path.join(here, 'canvas', 'Mainframe.dc.html'), encoding='utf-8', newline='').read().replace('\r\n', '\n'), 'canvas/Mainframe.dc.html').encode('utf-8')
          == t23_file('_build/canvas/Mainframe.dc.html').replace(b'\r\n', b'\n'))
    c3 = rd('comp3.html')
    check('T-24: _build/comp3.html carries A6 and A7 with their IDs, and A6 and A7 word for word',
          'T-24 A6' in c3 and 'T-24 A7' in c3 and all(c3.count(new) == 1 for _a, n, _o, new in T24_LINES if n == 'comp3.html'))

    # What a reader sees: each shown line exactly once in the page's text, after its scripts run.
    TXT24_JS = '''(() => { const c = document.body.cloneNode(true); c.querySelectorAll('script, style, section[aria-labelledby="gallery-h"], .shelf').forEach(e => e.remove());
      return c.textContent.replace(/[\\s\\u00a0]+/g, ' ').trim() })()'''
    MF24_JS = r'''(() => { const bs = [...document.querySelectorAll('button[data-reading]')];
      const lines = e => { const g = document.createRange(); g.selectNodeContents(e); return new Set([...g.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size; };
      return {btn: bs.map(b => [b.textContent, b.getAttribute('aria-pressed'), getComputedStyle(b).backgroundColor]),
              h: bs.map(b => Math.round(b.getBoundingClientRect().height * 10) / 10), lines: bs.map(lines),
              w: bs.map(b => Math.round(b.getBoundingClientRect().width)), gw: Math.round(bs[0].parentElement.getBoundingClientRect().width),
              row: new Set(bs.map(b => Math.round(b.getBoundingClientRect().top))).size,
              vals: ['bytes', 'value', 'rate', 'interest'].map(k => document.getElementById('mf-' + k).textContent),
              color: document.getElementById('mf-interest').getAttribute('style'), verdict: document.getElementById('mf-verdict').textContent}; })()'''
    # A number token split across two lines anywhere in the element holding a line (or in the whole page).
    SPLIT24_JS = r'''([sel, toks]) => { const out = []; const roots = sel ? [...document.querySelectorAll(sel)] : [document.body];
      for (const root of roots) { const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let t;
        while ((t = tw.nextNode())) { if (t.parentElement.closest('script, style')) continue;
          for (const k of toks) { let i = t.data.indexOf(k);
            while (i >= 0) { const g = document.createRange(); g.setStart(t, i); g.setEnd(t, i + k.length);
              const tops = new Set([...g.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top)));
              if (tops.size > 1) out.push(k + ' in ' + t.data.slice(0, 60)); i = t.data.indexOf(k, i + 1); } } } }
      return out; }'''
    TOKS24 = ['0.035', '3.5%', '3.5', '0.03500', '3.50000', '$291.67', '$2.92']
    PCT_VERDICT = 'Correct to the code, line for line. 100 times too much interest.'
    A1, A2, A3, A4, A5 = (new for _a, _n, _o, new in T24_LINES[:5])
    A6a, A6b, A7a, A7b = (new for _a, _n, _o, new in T24_LINES[5:])
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q); q.wait_for_timeout(200)
        r = q.evaluate(MF24_JS); t = q.evaluate(TXT24_JS)
        check(f'T-24: at {w} mainframe shows A1, A2, A3 and A5 exactly once each as it loads, and not A4',
              all(t.count(x) == 1 for x in (A1, A2, A3, A5)) and t.count(A4) == 0, str([t.count(x) for x in (A1, A2, A3, A4, A5)]))
        check(f'T-24: at {w} as loaded, "Stored as 3.5" is selected (filled dark) and "Stored as 0.035" is a plain outline',
              r['btn'] == [[A2, 'false', 'rgba(0, 0, 0, 0)'], [A3, 'true', 'rgb(18, 22, 31)']], str(r['btn']))
        check(f'T-24: at {w} as loaded, Exhibit A shows 03 50 00 0C, 3.50000, 0.2916667, $291.67 and the percent verdict',
              r['vals'] == ['03 50 00 0C', '3.50000', '0.2916667', '$291.67'] and r['verdict'] == PCT_VERDICT and '#A93F17' in r['color'], str(r['vals']) + r['verdict'])
        check(f'T-24: at {w} as loaded, the two Exhibit A buttons are the same height and each label is on one line',
              len(set(r['h'])) == 1 and r['lines'] == [1, 1], f"{r['h']} {r['lines']}")
        if w < 400:
            check(f'T-24: at {w} the two buttons are stacked, each the group\'s full width', r['row'] == 2 and set(r['w']) == {r['gw']}, str(r))
        else:
            check(f'T-24: at {w} the two buttons sit side by side', r['row'] == 1, str(r))
        sp = q.evaluate(SPLIT24_JS, [None, TOKS24])
        check(f'T-24: at {w} as loaded, no "0.035", "3.5" or "3.5%" (or Exhibit A figure) splits across lines on mainframe', not sp, str(sp))
        q.click('button[data-reading="fraction"]'); q.wait_for_timeout(500)   # the buttons' fill fades in 160 ms
        r = q.evaluate(MF24_JS); t = q.evaluate(TXT24_JS)
        check(f'T-24: at {w} after tapping "Stored as 0.035", it is selected and "Stored as 3.5" is not',
              r['btn'] == [[A2, 'true', 'rgb(18, 22, 31)'], [A3, 'false', 'rgba(0, 0, 0, 0)']], str(r['btn']))
        check(f'T-24: at {w} after tapping "Stored as 0.035", Exhibit A shows 00 03 50 0C, 0.03500, 0.0029167, $2.92 and A4',
              r['vals'] == ['00 03 50 0C', '0.03500', '0.0029167', '$2.92'] and r['verdict'] == A4 and '#12161F' in r['color'], str(r['vals']) + r['verdict'])
        check(f'T-24: at {w} after the tap, A4 shows exactly once and the percent verdict is gone', t.count(A4) == 1 and t.count(PCT_VERDICT) == 0)
        check(f'T-24: at {w} after the tap, the two buttons are the same height and each label is on one line',
              len(set(r['h'])) == 1 and r['lines'] == [1, 1], f"{r['h']} {r['lines']}")
        sp = q.evaluate(SPLIT24_JS, [None, TOKS24])
        check(f'T-24: at {w} after the tap, no number splits across lines on mainframe', not sp, str(sp))
        q.click('button[data-reading="percent"]'); q.wait_for_timeout(150)
        check(f'T-24: at {w} tapping "Stored as 3.5" brings back the first state', q.evaluate(MF24_JS)['verdict'] == PCT_VERDICT)
        sw = q.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
        check(f'T-24: mainframe has no sideways scroll at {w}', sw[0] <= sw[1], str(sw))
        q.close()

    # comp3: the example buttons and the two result boxes. Same input, same figures as at T-23.
    BOX24_JS = r'''(() => { const o = {}; document.querySelectorAll('#out .label').forEach(l => { const v = l.nextElementSibling;
      if (v && v.classList.contains('mono')) o[l.textContent] = v.textContent; }); return o; })()'''
    CHIP24_JS = r'''(() => [...document.querySelectorAll('button.chip[data-b]')].map(b => { const g = document.createRange(); g.selectNodeContents(b);
      return [b.textContent, new Set([...g.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size, Math.round(b.getBoundingClientRect().height)]; }))()'''
    LAB24_JS = r'''(() => [...document.querySelectorAll('#out .label')].map(l => { const g = document.createRange(); g.selectNodeContents(l);
      return [l.textContent, new Set([...g.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size]; }))()'''
    OUT24_JS = "document.getElementById('out').textContent.replace(/\\s+/g, ' ').trim()"
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'comp3.html'); settle(q); q.wait_for_timeout(200)
        o = t23_page(w); o.goto(OLD24B + 'comp3.html'); settle(o); o.wait_for_timeout(200)
        bx = q.evaluate(BOX24_JS)
        check(f'T-24 A7: at {w} the default input 03 50 00 0C reads $291.67 under "What the code charges" and $2.92 under "If it means a percent"',
              bx == {A7a: '$291.67', A7b: '$2.92'}, str(bx))
        t = q.evaluate(TXT24_JS)
        check(f'T-24: at {w} comp3 shows A6 and A7 exactly once each', all(t.count(x) == 1 for x in (A6a, A6b, A7a, A7b)), str([t.count(x) for x in (A6a, A6b, A7a, A7b)]))
        ch, cho = q.evaluate(CHIP24_JS), o.evaluate(CHIP24_JS)
        check(f'T-24 A6: at {w} the example buttons keep their layout: no button has more lines than at T-23',
              len(ch) == len(cho) == 4 and all(a[1] <= b_[1] for a, b_ in zip(ch, cho)), f'{ch} vs {cho}')
        check(f'T-24 A6: at {w} "Exhibit A, stored as 3.5" and "Exhibit A, stored as 0.035" are each on one line', [c[1] for c in ch[:2]] == [1, 1], str(ch))
        for lbl, want in ((A6a, {A7a: '$291.67', A7b: '$2.92'}), (A6b, None)):
            q.click(f'button.chip:text-is("{lbl}")'); q.wait_for_timeout(150)
            o.click(f'button.chip:text-is("{un24(lbl)}")'); o.wait_for_timeout(150)
            bx = q.evaluate(BOX24_JS)
            if want:
                check(f'T-24: at {w} after tapping "{lbl}", "What the code charges" shows $291.67 and "If it means a percent" shows $2.92', bx == want, str(bx))
            else:
                check(f'T-24: at {w} after tapping "{lbl}", "What the code charges" shows $2.92', bx.get(A7a) == '$2.92', str(bx))
            a, b_ = un24(q.evaluate(OUT24_JS)), o.evaluate(OUT24_JS)
            check(f'T-24: at {w} after tapping "{lbl}", the decoder reads exactly as at T-23 apart from the two labels', a == b_, f'{a[:200]} | {b_[:200]}')
            lb = q.evaluate(LAB24_JS)
            check(f'T-24 A7: at {w} after tapping "{lbl}", each result label is on one line', all(x[1] == 1 for x in lb if x[0] in (A7a, A7b)) and sum(x[0] in (A7a, A7b) for x in lb) == 2, str(lb))
            sp = q.evaluate(SPLIT24_JS, [None, TOKS24])
            check(f'T-24: at {w} after tapping "{lbl}", no number splits across lines on comp3', not sp, str(sp))
        sw = q.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
        check(f'T-24: comp3 has no sideways scroll at {w}', sw[0] <= sw[1], str(sw))
        q.close(); o.close()


# ---------------- T-25 (Nov 17, 2026): layout leftovers, no words change ----------------
@section('T-25')
def s_t_25():
    # F1 to F5 and T1: layout, wrapping and test code only, not one word. Comparisons are against
    # T-24's own pages (origin/main at fd4b14e, the base this item was cut from), read from git.
    T24C = 'fd4b14ec5669aa11d8695f8a2f6d077904a6b8ee'
    T24_FILES = {}

    def t24_file(path):
        if path not in T24_FILES:
            r = _sp18.run(['git', 'show', f'{T24C}:{path}'], cwd=here, capture_output=True)
            T24_FILES[path] = r.stdout if r.returncode == 0 else None
        return T24_FILES[path]

    def t24_page(w, h=900):
        """A page that can open T-24's own build at BASE + '__t24/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t24/', 1)[1].split('?')[0].split('#')[0]
            body = t24_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t24/**', serve)
        return q
    OLD25B = BASE + '__t24/'
    check('T-25: the T-24 pages can be read from git for comparison', t24_file('work.html') is not None and t24_file('og/work.png') is not None)
    SRC25 = {n: un26(un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n) for n in ALL_HTML}   # T-26: the gallery out (its block checks it)   # T-30: studio's and local's paragraphs back (the T-30 block checks them)
    OLD25 = {n: t24_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT25 = {n: un26(un30(open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n'), n), n) for n in ALL_HTML}   # T-26: as SRC25   # T-30: as SRC25
    CHANGED25 = ['captions.html', 'case-reels.html', 'local.html', 'mainframe.html', 'scaler.html', 'studio.html', 'work.html']

    # The whole build: T-24's pages with only T-25's changes. un25() swaps each back, and what is
    # left is T-24's page byte for byte (the Studio pages' build day aside).
    for n in ALL_HTML:
        a, b_ = stamp25(un25(SRC25[n], n)), stamp25(OLD25[n])
        check(f'T-25: {n} is T-24\'s page with only T-25\'s changes', a == b_,
              next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
    got25 = sorted(n for n in ALL_HTML if stamp25(SRC25[n]) != stamp25(OLD25[n]))
    check('T-25: the pages that changed are these seven and no others', got25 == CHANGED25, str(got25))
    check('T-25: every root page is the built page', not t32_root_off(ALL_HTML),   # T-32: the themed build
          str(t32_root_off(ALL_HTML)))
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>'),
                         ('alt texts', r'\balt="[^"]*"'), ('aria-labels', r'\baria-label="[^"]*"'), ('placeholders', r'\bplaceholder="[^"]*"'),
                         ('labels', r'<label\b[^>]*>.*?</label>')):
            check(f'T-25: {n} keeps its {what}', _re.findall(rx, SRC25[n], _re.S) == _re.findall(rx, OLD25[n], _re.S))
    ogs = sorted(os.listdir(os.path.join(here, '..', 'og')))
    check('T-25: every share card in og/ is byte for byte as at T-24', len(ogs) == 17 and all(
        open(os.path.join(here, '..', 'og', f), 'rb').read() == t24_file('og/' + f) for f in ogs), str(len(ogs)))
    check('T-25: every share card in _build/assets/og/ is byte for byte as at T-24', all(
        open(os.path.join(here, 'assets', 'og', f), 'rb').read() == t24_file('_build/assets/og/' + f) for f in ogs))
    check('T-25: no em dash on any changed page, and no new en dash',
          not any('—' in SRC25[n] for n in CHANGED25) and all(SRC25[n].count('–') == OLD25[n].count('–') for n in CHANGED25))

    # Where each fix lives.
    rd = lambda f: open(os.path.join(here, f), encoding='utf-8').read()
    ch25, bp25, sc25, ca25, st25, en25, ts25 = (rd(f) for f in ('tools/chrome.py', 'build.py', 'tools/scaler.py', 'tools/captions.py',
                                                              'tools/studio.py', 'enhance.py', 'test_site.py'))
    check('T-25 T1: tools/chrome.py holds djNb() (NB_JS), and build.py writes it into the local and mainframe scripts and uses it in both tab redraws',
          'NB_JS = ' in ch25 and bp25.count('/*NBJS*/\n') == 2 and bp25.count('\n/*NBJS*/\n(function () {\n') == 1 and '"/*NBJS*/", chrome.NB_JS' in bp25
          and "$('rc-head').innerHTML = djNb(esc(rc.head));" in bp25 and "$('xb-body').innerHTML = djNb(esc(x.body));" in bp25)
    check('T-25 T1 (grown-up): enhance.py writes the tap-to-see notes and their footer on local through djNb(), not as plain text',
          'note.innerHTML = djNb(esc(s));' in en25 and "foot.innerHTML = djNb(esc(FOOT[tab] || ''));" in en25
          and 'note.textContent' not in en25 and 'foot.textContent' not in en25)
    check('T-25 T1: djNb() is on local.html and mainframe.html once each, and on no other page',
          all(SRC25[n].count('function djNb(s)') == (1 if n in ('local.html', 'mainframe.html') else 0) for n in ALL_HTML))
    check('T-25 T1: test_site.py falls back to the live Google Fonts when its font folder is missing, and still counts the css2 requests',
          "if not FONT_FILES:" in ts25 and 'route.continue_()' in ts25 and 'gf_hits.append(u)' in ts25 and "FONT_MODE" in ts25)
    check('T-25 F2: tools/scaler.py writes the hint through keep_amounts() and every result through amtNw()',
          'keep_amounts("One ingredient per line' in sc25 and sc25.count('amtNw(esc(') == 5 and "amtNw('Make it in '" in sc25)
    check('T-25 F3: tools/captions.py sets --k from the text size and the reel\'s caption width, and draws each part with white-space:pre',
          "style.setProperty('--k',String(SIZES[st.size][1]/MAXW))" in ca25 and 'white-space:pre;' in ca25 and 'white-space:pre-line' not in ca25)
    check('T-25 F4: tools/studio.py writes LOG_PHONE_CSS into studio.html only',
          'css=CSS + LOG_PHONE_CSS' in st25 and all(('@media (max-width:799px){.loghead' in SRC25[n]) == (n == 'studio.html') for n in ALL_HTML))
    CALLCSS25 = '<style>@media (min-width:900px){section[aria-labelledby="next-h"],section[aria-labelledby="c7"]{grid-template-columns:minmax(0,1fr) auto!important}}</style>'
    check('T-25 F5: enhance.py writes the closing box rule once into work, studio and case-reels, and nowhere else',
          'CALL_BOX_CSS = ' in en25 and all(SRC25[n].count(CALLCSS25) == (1 if n in ('work.html', 'studio.html', 'case-reels.html') else 0) for n in ALL_HTML))
    check('T-25 F5: the three closing boxes are still built from their sources (work\'s on studio, character for character)',
          _re.findall(r'<section aria-labelledby="next-h".*?</section>', SRC25['studio.html'], _re.S)
          == _re.findall(r'<section aria-labelledby="next-h".*?</section>', SRC25['work.html'], _re.S) != [])

    # Words: every page reads word for word as at T-24, as loaded, at 1440 and 390.
    day25 = lambda s: _re.sub(r'\b(?:Nov|Oct|Sep|Aug|Jul) \d{1,2}\b|\b\d+ (?:days?|lines?|things?)\b', '#', s)
    for w in (1440, 390):
        for n in ALL_HTML:
            q = newpage(w); q.goto((UN29 if n == 'studio.html' else UN30) + n); settle(q); a = q.evaluate(TEXT_JS); q.close()   # T-29: as above (un29); T-30: local's descriptions back (un30)
            o = t24_page(w); o.goto(OLD25B + n); settle(o); b_ = o.evaluate(TEXT_JS); o.close()
            if n.startswith('studio'):   # the log's day count moves with the day the page is built
                a, b_ = day25(back27(a)), day25(b_)   # T-27: the ChuckleFits line read back as T-26's (its block checks it)
            check(f'T-25: {n} reads word for word as at T-24 at {w}', a == b_,
                  next((f'...{a[max(0, i - 40):i + 40]}... | ...{b_[max(0, i - 40):i + 40]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))

    # Shared measuring: the lines a box's words fall on (by the words' own rectangles).
    LINES25_JS = r'''(el) => { if (typeof el === 'string') el = document.querySelector(el); if (!el) return null;
      const words = [], w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const re = /\S+/g; let m; while ((m = re.exec(n.data))) {
        const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
        const rs = [...r.getClientRects()].filter(x => x.width > 0); if (!rs.length) continue;
        words.push({t: m[0], top: rs[0].top, h: rs[0].height}); } }
      const lines = []; words.forEach(x => { let L = lines.find(l => Math.abs(l.mid - (x.top + x.h / 2)) < Math.max(6, x.h / 3));
        if (!L) { L = {mid: x.top + x.h / 2, w: []}; lines.push(L); } L.w.push(x.t); });
      lines.sort((a, b) => a.mid - b.mid); return lines.map(l => l.w.join(' ')); }'''
    CARDH25_JS = r'''() => [...document.querySelectorAll('main h2, main h3, main h4, main .num')]
      .filter(e => e.offsetParent && e.closest('article, .card, [data-card]'))
      .map(e => [e.textContent.replace(/\s+/g, ' ').trim(), (''' + LINES25_JS + r''')(e)])
      .filter(x => x[1].length > 1 && x[1].some(l => l.split(' ').length === 1))'''

    # F1: the reels headline leaves no word alone at 320, 390 and 1440 ("about 4 minutes." whole is wider than the card at 320
    # and 1440, so "of editing," and "now about" are held instead, with T-23's "4 minutes."), and no card headline on work,
    # local or case-reels leaves a word alone that T-24 didn't. Three card headlines can't be held by a span without running
    # past their card (measured in the Receipt); Josef ruled on them (Nov 17, 2026): the balanced wrap, checked after this loop.
    REELS25 = 'An evening of editing, now about 4 minutes.'
    RULED25 = ('2 AI translations of one bank program', 'Your videos, finished every month', 'Busywork, automated', 'Your know-how, in an app',
               'Something else')
    # T-33: R7 renames "Reels from your phone videos"; R8 renames "Your own app", which now leaves a word alone at 320 and
    # so comes under the same ruling (balanced wrap, no smaller type, no span of F1's; "know-how" keeps T-21 G1's pair span);
    # R9's "Something else" leaves each word alone at 320 and comes under it too. Its type size is compared with the
    # heading beside it ("Busywork, automated"), as T-24 had no fourth offer.
    WAS25 = {'Your videos, finished every month': 'Reels from your phone videos', 'Your know-how, in an app': 'Your own app',
             'Something else': 'Busywork, automated'}
    SPANS25 = {'Your know-how, in an app': 1}
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'work.html'); settle(q)
        ln = q.evaluate(LINES25_JS, '.card .num')
        check(f'T-25 F1: at {w} the reels headline ends "now about / 4 minutes.", "4 minutes." on one line',
              ln is not None and (ln[-2:] == ['now about', '4 minutes.'] if w < 1440 else ln == [REELS25]), str(ln))   # T-33 R12: at 1440 the card is alone on its row, one line
        check(f'T-25 F1: at {w} the reels headline leaves no word alone on a line', ln is not None and all(len(l.split(' ')) > 1 for l in ln), str(ln))
        nw = q.evaluate('''() => { const n = document.querySelector('.card .num'), ss = [...n.querySelectorAll('span')];
          return [ss.map(s => [s.textContent, getComputedStyle(s).whiteSpace]), Math.max(...ss.map(s => Math.round(s.getBoundingClientRect().right))), Math.round(n.getBoundingClientRect().right)] }''')
        check(f'T-25 F1: at {w} "of editing,", "now about" and "4 minutes." are no-wrap spans that stay inside the card',
              nw[0] == [['of editing,', 'nowrap'], ['now about', 'nowrap'], ['4 minutes.', 'nowrap']] and nw[1] <= nw[2], str(nw))
        q.close()
        for n in ('work.html', 'local.html', 'case-reels.html'):
            q = newpage(w); q.goto(BASE + n); settle(q); now = q.evaluate(CARDH25_JS); q.close()
            o = t24_page(w); o.goto(OLD25B + n); settle(o); was = o.evaluate(CARDH25_JS); o.close()
            check(f'T-25 F1: at {w} no card headline on {n} leaves a word alone that T-24 didn\'t, and the reels headline none (the three under Josef\'s ruling checked below)',
                  all(x in was for x in now if x[0] not in RULED25) and not any(x[0] == REELS25 for x in now), f'now {now} | T-24 {was}')
            check(f'T-25 F1: at {w} the card headlines on {n} with a word alone are only the three under Josef\'s ruling',
                  all(x[0] in RULED25 for x in now), str(now))

    # Josef's ruling (Nov 17, 2026): the three card headlines that left a word alone get the balanced wrap the site's
    # headings use (text-wrap: balance), with no smaller type, no new words and no span; what still leaves a word alone
    # after that stays as it is ("left as is, Josef's ruling"). Each reads as measured for the Receipt.
    HEAD25_JS = r'''([text, LINES]) => { const e = [...document.querySelectorAll('main h2, main h3, main .num')].find(x => x.textContent.replace(/\s+/g, ' ').trim() === text);
      if (!e) return null; const cs = getComputedStyle(e), b = e.getBoundingClientRect();
      const rs = []; const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const r = document.createRange(); r.selectNodeContents(n); rs.push(...[...r.getClientRects()].filter(x => x.width > 0)); }
      return {wrap: cs.textWrapStyle || cs.textWrap, size: cs.fontSize, spans: e.querySelectorAll('span').length,
              inside: rs.every(r => r.right <= b.right + 0.5 && r.left >= b.left - 0.5), lines: (new Function('return ' + LINES))()(e)}; }'''
    # T-33: R7 and R8's names as measured (Nov 20, 2026); "Busywork, automated" on one line at 1440 (R9's two columns).
    WANT25 = {320: {'2 AI translations of one bank program': ['2 AI', 'translations', 'of one', 'bank program'],
                    'Your videos, finished every month': ['Your videos,', 'finished', 'every month'], 'Busywork, automated': ['Busywork,', 'automated'],
                    'Your know-how, in an app': ['Your', 'know-how ,', 'in an app'], 'Something else': ['Something', 'else']},
              390: {'2 AI translations of one bank program': ['2 AI translations of', 'one bank program'],
                    'Your videos, finished every month': ['Your videos,', 'finished', 'every month'], 'Busywork, automated': ['Busywork,', 'automated'],
                    'Your know-how, in an app': ['Your know-how ,', 'in an app'], 'Something else': ['Something else']},
              1440: {'2 AI translations of one bank program': ['2 AI', 'translations', 'of one bank', 'program'],
                     'Your videos, finished every month': ['Your videos, finished', 'every month'], 'Busywork, automated': ['Busywork, automated'],
                     'Your know-how, in an app': ['Your know-how , in an app'], 'Something else': ['Something else']}}
    for w in (320, 390, 1440):
        for n, text in (('work.html', RULED25[0]), ('local.html', RULED25[1]), ('local.html', RULED25[2]), ('local.html', RULED25[3]), ('local.html', RULED25[4])):
            q = newpage(w); q.goto(BASE + n); settle(q); now = q.evaluate(HEAD25_JS, [text, LINES25_JS]); q.close()
            o = t24_page(w); o.goto(OLD25B + n); settle(o); was = o.evaluate(HEAD25_JS, [WAS25.get(text, text), LINES25_JS]); o.close()   # T-33: T-24's headline in that spot
            check(f'T-25 ruling: at {w} "{text}" on {n} has the balanced wrap, at T-24\'s type size, with no span added',
                  now is not None and was is not None and now['wrap'] == 'balance' and now['size'] == was['size'] and now['spans'] == SPANS25.get(text, 0) and was['spans'] == 0, f'{now} | T-24 {was}')
            check(f'T-25 ruling: at {w} "{text}" on {n} stays inside its card', now is not None and now['inside'], str(now))
            check(f'T-25 ruling: at {w} "{text}" on {n} reads {" / ".join(WANT25[w][text])}', now is not None and now['lines'] == WANT25[w][text], str(now and now['lines']))
    check('T-25 ruling: work.html carries the balance rule for the banking card\'s figure only, and local\'s two headlines already had the headings\' rule',
          SRC25['work.html'].count('.card[data-k="banking"] .num{text-wrap:balance}') == 1 and SRC25['work.html'].count('<article class="card" data-k="banking">') == 1
          and ':is(h1,h2,h3,h4,button,' in SRC25['local.html'] and OLD25['local.html'].count(':is(h1,h2,h3,h4,button,') == SRC25['local.html'].count(':is(h1,h2,h3,h4,button,'))

    # F2: no amount splits from itself or its unit, in the hint and in results after changing the numbers;
    # the scaler gives the same results for the same inputs as at T-24.
    AMT25_JS = r'''() => { const SEL = '#out td, #out .was, #facl, #warn p, .lay .private';
      const RX = /(\d+\s+\d+\/\d+|\d+\s*[¼-¾⅐-⅞]|\d+\/\d+|\d*\.?\d+|[¼-¾⅐-⅞])(\s+(?:(?:large|small|medium|ripe)\s+)?[A-Za-z][A-Za-z.]*)?/g;
      let found = 0; const bad = [];
      document.querySelectorAll(SEL).forEach(el => {
        const nodes = []; let txt = ''; const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
        while ((n = w.nextNode())) { if (n.parentElement.closest(SEL) !== el) continue; nodes.push([n, txt.length]); txt += n.data; }
        const at = i => { for (let k = nodes.length - 1; k >= 0; k--) if (nodes[k][1] <= i) return [nodes[k][0], i - nodes[k][1]]; };
        let m; while ((m = RX.exec(txt))) { if (!/\s/.test(m[0])) continue; found++;
          const r = document.createRange(), s = at(m.index), e = at(m.index + m[0].length - 1); r.setStart(s[0], s[1]); r.setEnd(e[0], e[1] + 1);
          const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top + x.height / 2)));
          if (tops.size > 1) bad.push(m[0]); } });
      return [found, bad]; }'''
    RES25_JS = '''() => ['out', 'fac', 'facl', 'warn'].map(i => document.getElementById(i).textContent.replace(/\\s+/g, ' ').trim())'''
    REC25 = '1½ cups flour\n1 1/2 cups butter, soft\n2 large eggs\n3 Tbsp honey\n200 g oats\n12 pinches of salt'
    SC25 = [('as loaded', None, None, None, False), ('1 grown-up, 7 kids', '1', '7', None, False),
            ('3 grown-ups, 40 kids', '3', '40', None, False), ('3 grown-ups, 40 kids, one batch', '3', '40', None, True),
            ('a typed recipe, 2 grown-ups, 9 kids', '2', '9', REC25, False)]
    for w in (320, 390):
        for label, ad, kd, rec, one in SC25:
            res = []
            for base, opener in ((BASE, newpage), (OLD25B, t24_page)):
                q = opener(w); q.goto(base + 'scaler.html'); settle(q)
                if rec is not None:
                    q.fill('#rec', rec)
                if ad is not None:
                    q.fill('#adults', ad); q.fill('#kids', kd)
                if one:
                    q.click('[data-b="one"]')
                q.wait_for_timeout(150)
                res.append((q.evaluate(RES25_JS), q.evaluate(AMT25_JS) if base == BASE else None))
                if base == BASE and w == 390 and label == 'a typed recipe, 2 grown-ups, 9 kids':
                    q.screenshot(path=f'{SHOTS}/t25-scaler-typed-390.png', full_page=True)
                q.close()
            (r_now, amt), (r_old, _) = res
            check(f'T-25 F2: at {w}, {label}: the scaler\'s results are exactly as at T-24', r_now == r_old, f'{r_now} | {r_old}')
            check(f'T-25 F2: at {w}, {label}: no amount splits from itself or its unit (hint and results)', amt[0] >= 5 and not amt[1], str(amt))

    # F3: the example's part 1 on two lines at every width, drawn at the reel's proportions; the fitter's results unchanged.
    CAP25_JS = r'''() => [...document.querySelectorAll('.cardline .t>span')].map(e => { const r = document.createRange(); r.selectNodeContents(e);
      const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top)));
      return [tops.size, e.textContent.split('\n').length, e.scrollWidth <= e.parentElement.clientWidth + 1, parseFloat(getComputedStyle(e).fontSize)]; })'''
    FIT25_JS = r'''() => [document.getElementById('cards').textContent, document.getElementById('k-sub').textContent,
      document.getElementById('verdicts').textContent, document.getElementById('v-text').textContent]'''
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'captions.html'); settle(q); q.wait_for_timeout(200)
        cp = q.evaluate(CAP25_JS)
        check(f'T-25 F3: at {w} the example\'s part 1 is on two lines, under "Two lines fit on a phone"',
              len(cp) >= 2 and cp[0][0] == 2 and 'Two lines fit on a phone' in q.evaluate("document.getElementById('k-sub').textContent"), str(cp))
        check(f'T-25 F3: at {w} every part shows exactly the fitter\'s lines, none reflowed, none running past its box',
              all(c[0] == c[1] and c[2] for c in cp), str(cp))
        check(f'T-25 F3: at {w} the parts are drawn at 11 px or more and never above 15 px', all(11 <= c[3] <= 15 for c in cp), str(cp))
        q.close()
    CAPS25 = [None, 'Fresh sourdough comes out of the oven at 7 every morning. Come early, because the first batch is always gone by 9.',
              'Our Saturday class is full. The next one opens on the first, and every family on the list hears first. Sign up at the front desk or tap the link.',
              'Short one.']
    for w in (390, 1440):
        for cap in CAPS25:
            for extra in ((), ('[data-k="size"][data-v="l"]',), ('[data-k="app"][data-v="tiktok"]', '[data-k="size"][data-v="s"]')):
                got = []
                for base, opener in ((BASE, newpage), (OLD25B, t24_page)):
                    q = opener(w); q.goto(base + 'captions.html'); settle(q); q.wait_for_timeout(150)
                    if cap is not None:
                        q.fill('#cap', cap); q.wait_for_timeout(300)
                    if extra:
                        q.click('#f-look')
                    for sel in extra:
                        q.click(sel)
                    q.wait_for_timeout(150)
                    got.append(q.evaluate(FIT25_JS)); q.close()
                check(f'T-25 F3: at {w} the fitter gives the same parts, lines and verdicts as at T-24 for {"the default" if cap is None else repr(cap[:24])} {list(extra)}',
                      got[0] == got[1], f'{got[0]} | {got[1]}')

    # F4: around "Shipped lately" no two horizontal rules within 24 px, and the count reads with the heading; the count equals the log lines that show.
    RULES25_JS = r'''() => { const h = document.getElementById('log-h').getBoundingClientRect(), ys = [];
      document.querySelectorAll('body *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width < 120 || !e.offsetParent) return; const s = getComputedStyle(e);
        [[r.top, s.borderTopWidth, s.borderTopStyle], [r.bottom, s.borderBottomWidth, s.borderBottomStyle]].forEach(b => {
          if (parseFloat(b[1]) > 0 && b[2] !== 'none') ys.push(Math.round(b[0])); });
        if (e.tagName === 'HR') ys.push(Math.round(r.top)); });
      const near = [...new Set(ys.filter(y => y > h.top - 240 && y < h.bottom + 160))].sort((a, b) => a - b);
      const gaps = near.slice(1).map((y, i) => y - near[i]).filter(g => g > 1);
      const c = document.querySelector('#stats strong').getBoundingClientRect(), t = document.querySelector('#stats p').getBoundingClientRect();
      const ruleBetween = near.some(y => y > Math.min(h.bottom, t.top) && y < Math.max(h.bottom, t.top));
      return {near, gaps, head: [Math.round(h.top), Math.round(h.bottom)], count: [Math.round(t.top), Math.round(t.bottom)], ruleBetween,
              n: document.querySelector('#stats strong').textContent.trim(), lis: document.querySelectorAll('#log li').length,
              all: (document.getElementById('log-all') || {}).textContent || ''}; }'''
    for w in (320, 390, 1024, 1440):
        q = newpage(w); q.goto(BASE + 'studio.html'); settle(q)
        r = q.evaluate(RULES25_JS)
        if w != 1024:
            check(f'T-25 F4: at {w} no two horizontal rules sit within 24 px of each other around "Shipped lately"', all(g >= 24 for g in r['gaps']), str(r))
        check(f'T-25 F4: at {w} the count reads with "Shipped lately": no rule between them, and it starts within 24 px of the heading',
              not r['ruleBetween'] and (r['count'][0] - r['head'][1] <= 24 if w < 800 else abs(r['count'][1] - r['head'][1]) <= 24), str(r))
        check(f'T-25 F4: at {w} the count ({r["n"]}) equals the log lines that show and "See all"', r['n'] == str(r['lis']) and r['all'] == f'See all {r["lis"]}', str(r))
        if w < 800:
            check(f'T-25 F4: at {w} the heading comes first on screen and the count right under it', r['head'][1] <= r['count'][0] + 2, str(r))
        q.close()
    check('T-25 F4: the count still comes first in the page, before the heading',
          SRC25['studio.html'].index('id="stats"') < SRC25['studio.html'].index('id="log-h"'))

    # F5: the closing box's inner left and right space match within 8 px at 1024 and 1440 on all three pages.
    BOX25_JS = r'''(h) => { const s = document.querySelector('section[aria-labelledby="' + h + '"]'), b = s.getBoundingClientRect();
      const rs = []; s.querySelectorAll('h2, p').forEach(e => { const r = document.createRange(); r.selectNodeContents(e); rs.push(...[...r.getClientRects()].filter(x => x.width > 0)); });
      s.querySelectorAll('a').forEach(a => rs.push(a.getBoundingClientRect()));
      return [Math.round(Math.min(...rs.map(r => r.left)) - b.left), Math.round(b.right - Math.max(...rs.map(r => r.right)))]; }'''
    for w in (1024, 1440):
        for n, h in (('case-reels.html', 'c7'), ('work.html', 'next-h'), ('studio.html', 'next-h')):
            q = newpage(w); q.goto(BASE + n); settle(q); lr = q.evaluate(BOX25_JS, h); q.close()
            o = t24_page(w); o.goto(OLD25B + n); settle(o); lr0 = o.evaluate(BOX25_JS, h); o.close()
            check(f'T-25 F5: at {w} the closing box on {n} has the same space inside on the left and the right, within 8 px (T-24: {lr0})',
                  abs(lr[0] - lr[1]) <= 8, f'{lr} (T-24 {lr0})')

    # T1: a tab round trip gives back the markup the page was built with, so no hyphen pair or held dot is lost.
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); settle(q)
        p0 = q.inner_html('#proof')
        for t in ('app', 'method', 'reels'):
            q.click(f'button[data-tab="{t}"]')
        check(f'T-25 T1: at {w} local\'s Results after Apps, COBOL checking and back to Reels is the built markup, byte for byte', q.inner_html('#proof') == p0)
        check(f'T-25 T1: at {w} local\'s "RESULT · REELS" keeps its dot held after the round trip', '&nbsp;·&nbsp;' in q.inner_html('#rc-head'))
        q.close()
        q = newpage(w); q.goto(BASE + 'mainframe.html'); settle(q)
        s0 = q.inner_html('#s2')
        for t in ('c', 'd', 'b'):
            q.click(f'button[data-ex="{t}"]')
        check(f'T-25 T1: at {w} mainframe\'s Exhibit B after C, D and back is the built markup, byte for byte', q.inner_html('#s2') == s0)
        q.close()
    # Every tab, as redrawn, reads exactly as at T-24, and holds no hyphen pair outside a no-wrap span (two-hyphen words included).
    PAIRS25_JS = r'''(sel) => { const out = [], w = document.createTreeWalker(document.querySelector(sel), NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { if (n.parentElement.closest('[style*="nowrap"], script, style')) continue;
        for (const m of n.data.matchAll(/(?:^|\s)[(“"'‘]*([\p{L}\p{N}]+(?:-[\p{L}\p{N}]+){1,2})(?=$|[\s)”"'’.,;:!?…]|['’]s)/gu)) if (m[1].length <= 24) out.push(m[1]); }
      return out; }'''
    SPLIT25_JS = r'''(sel) => [...document.querySelectorAll(sel + ' span[style*="nowrap"]')].filter(s => /-/.test(s.textContent)).map(s => {
      const r = document.createRange(); r.selectNodeContents(s); return [s.textContent, new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))).size]; })
      .filter(x => x[1] > 1)'''
    for w in (320, 390, 1440):
        for n, sel, btn, tabs in (('local.html', '#proof', 'data-tab', ('app', 'method', 'reels')), ('mainframe.html', '#s2', 'data-ex', ('c', 'd', 'b'))):
            q = newpage(w); q.goto(BASE + n); settle(q)
            o = t24_page(w); o.goto(OLD25B + n); settle(o)
            for t in tabs:
                q.click(f'button[{btn}="{t}"]'); o.click(f'button[{btn}="{t}"]'); q.wait_for_timeout(60)
                tq = q.evaluate(f"document.querySelector('{sel}').textContent.replace(/[\\s\\u00a0]+/g, ' ').trim()")
                to = o.evaluate(f"document.querySelector('{sel}').textContent.replace(/[\\s\\u00a0]+/g, ' ').trim()")
                check(f'T-25 T1: at {w} {n} tab "{t}" reads word for word as at T-24', tq == to, f'{tq[:160]} | {to[:160]}')
                pr = q.evaluate(PAIRS25_JS, sel)
                check(f'T-25 T1: at {w} {n} tab "{t}" has every hyphen pair in a no-wrap span', not pr, str(pr))
                sp = q.evaluate(SPLIT25_JS, sel)
                check(f'T-25 T1: at {w} {n} tab "{t}" splits no hyphen pair across lines', not sp, str(sp))
            q.close(); o.close()

    # T1 (grown-up): the Apps tab's fourth tap-to-see note, written by LOCAL_JS after the tab redraws, keeps
    # "grown-up" in a no-wrap span and on one line once tapped open; its words are T-24's.
    for w in (320, 390, 1440):
        res = []
        for base, opener in ((BASE, newpage), (OLD25B, t24_page)):
            q = opener(w); q.goto(base + 'local.html'); settle(q)
            q.click('button[data-tab="app"]'); q.wait_for_timeout(60)
            q.click('button[aria-controls="src-app-3"]'); q.wait_for_timeout(60)
            res.append(q.evaluate('''() => { const n = document.getElementById('src-app-3'), s = [...n.querySelectorAll('span[style*="nowrap"]')].find(x => x.textContent === 'grown-up');
              const tops = s ? new Set((() => { const r = document.createRange(); r.selectNodeContents(s); return [...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top)); })()).size : 0;
              return [n.hidden, n.textContent, !!s, tops]; }'''))
            q.close()
        (hid, txt, wrapped, tops), (_h, txt0, _w, _t) = res
        check(f'T-25 T1 (grown-up): at {w} the Apps tab\'s fourth note opens on tap with "grown-up" in a no-wrap span, on one line, and reads as at T-24',
              not hid and wrapped and tops == 1 and txt == txt0 and 'the grown-up does.' in txt, str(res))

    # T1: test_site.py runs to the end on this machine, with no hang.
    import tempfile as _tmp25
    try:
        rs = _sp18.run([sys.executable, os.path.join(here, 'test_site.py'), BASE, _tmp25.mkdtemp(prefix='t25site')],
                       cwd=here, capture_output=True, timeout=900)
        so = rs.stdout.decode('utf-8', 'replace')
    except Exception as e:   # a hang shows here as a timeout
        rs, so = None, f'{type(e).__name__}: {e}'
    m25 = _re.search(r'(\d+)/(\d+) passed', so)
    check('T-25 T1: test_site.py runs to the end with no hang, and every check passes',
          rs is not None and rs.returncode == 0 and m25 is not None and m25.group(1) == m25.group(2), so[-400:])
    check('T-25 T1: test_site.py says which fonts it used', so.startswith('fonts: '), so[:80])

    # No sideways scroll on the changed pages.
    for w in (320, 390, 1440):
        for n in CHANGED25:
            q = newpage(w); q.goto(BASE + n); settle(q)
            sw = q.evaluate('[document.documentElement.scrollWidth, window.innerWidth]'); q.close()
            check(f'T-25: {n} has no sideways scroll at {w}', sw[0] <= sw[1], str(sw))


# ---------------- T-26 (Nov 18, 2026): "Inside the apps", a gallery on the Studio page ----------------
@section('T-26')
def s_t_26():
    # One section on studio.html, every word from studio.json's "gallery", 20 images from _build/assets/gallery/.
    # Comparisons are against T-25's own build (origin/main at 00948bb, the base this item was cut from), read from git.
    T25C = '00948bba14a57eb3364caa74fe814a13237e460e'
    T25_FILES = {}

    def t25_file(path):
        if path not in T25_FILES:
            r = _sp18.run(['git', 'show', f'{T25C}:{path}'], cwd=here, capture_output=True)
            T25_FILES[path] = r.stdout if r.returncode == 0 else None
        return T25_FILES[path]
    check('T-26: the T-25 files can be read from git for comparison', t25_file('studio.html') is not None and t25_file('og/work.png') is not None)
    SRC26 = {n: un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: studio's and local's paragraphs back (the T-30 block checks them)
    OLD26 = {n: t25_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT26 = {n: un30(open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: as SRC26
    GAL26 = [it[0] for _a, gs in T26_APPS for _g in gs for it in _g[3]]

    # The whole build: studio.html is T-25's page with only the gallery added; every other page is byte for byte
    # T-25's (the two product pages differ only by studio.py's stamp line: the build day and studio.json's hash).
    check('T-26: un26() takes something out of studio.html (the gallery is there)', un26(SRC26['studio.html'], 'studio.html') != SRC26['studio.html'])
    for n in ALL_HTML:
        if n == 'studio.html':
            a, b_ = stamp25(un26(SRC26[n], n)), stamp25(OLD26[n])
            check('T-26: studio.html is T-25\'s page with only the gallery (its CSS and its section) added, the build day aside', a == b_,
                  next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
        elif n.startswith('studio-'):
            dl = [(x, y) for x, y in zip(SRC26[n].split('\n'), OLD26[n].split('\n')) if x != y]
            check(f'T-26: {n} is T-25\'s page apart from studio.py\'s stamp line', SRC26[n].count('\n') == OLD26[n].count('\n')
                  and all(_re.fullmatch(STAMP26, x) and _re.fullmatch(STAMP26, y) for x, y in dl), str(dl[:2]))
        else:
            check(f'T-26: {n} is byte for byte as at T-25', SRC26[n] == OLD26[n])
    check('T-26: every root page is the built page', not t32_root_off(ALL_HTML), str(t32_root_off(ALL_HTML)))   # T-32: the themed build
    pub25 = [f for f in _sp18.run(['git', 'ls-tree', '-r', '--full-tree', '--name-only', T25C], cwd=here, capture_output=True, text=True).stdout.split('\n')
             if f and not f.startswith('_build/') and not f.endswith('.html')]
    check('T-26: every other public file at the root (sitemap, robots, images, share cards...) is byte for byte as at T-25',
          len(pub25) > 20 and all(rb26(f) == t25_file(f).replace(b'\r\n', b'\n') for f in pub25),
          str([f for f in pub25 if rb26(f) != t25_file(f).replace(b'\r\n', b'\n')][:5]))
    outf = sorted(os.path.relpath(os.path.join(d, f), outd).replace(os.sep, '/') for d, _x, fs in os.walk(outd) for f in fs)
    t25tree = set(_sp18.run(['git', 'ls-tree', '-r', '--full-tree', '--name-only', T25C], cwd=here, capture_output=True, text=True).stdout.split('\n'))
    check('T-26: the build adds only gallery/ (every other file in out/ was at the root at T-25; T-27\'s images/shelf/ aside, its block checks it)',
          sorted(f for f in outf if f not in t25tree and not f.startswith('images/shelf/')) == sorted('gallery/' + g for g in GAL26), str([f for f in outf if f not in t25tree][:25]))
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>'),
                         ('alt texts', r'\balt="[^"]*"'), ('aria-labels', r'\baria-label="[^"]*"'), ('placeholders', r'\bplaceholder="[^"]*"'),
                         ('labels', r'<label\b[^>]*>.*?</label>')):
            check(f'T-26: {n} keeps its {what} (the gallery\'s own aside)',
                  _re.findall(rx, un26(SRC26[n], n), _re.S) == _re.findall(rx, OLD26[n], _re.S))

    # The images: the item's 20, byte for byte, in _build/assets/gallery/, out/gallery/, served, and gallery/ at the root (tracked in git).
    asg = os.path.join(here, 'assets', 'gallery')
    check('T-26: _build/assets/gallery/ holds exactly the item\'s 20 images', sorted(os.listdir(asg)) == sorted(GAL26) and len(GAL26) == 20, str(sorted(os.listdir(asg))))
    rootg = os.path.join(here, '..', 'gallery')
    check('T-26: gallery/ at the root holds exactly the same 20 files', os.path.isdir(rootg) and sorted(os.listdir(rootg)) == sorted(GAL26))
    for g in GAL26:
        src = open(os.path.join(asg, g), 'rb').read()
        check(f'T-26: gallery/{g} at the root, in out/ and as served is byte for byte _build/assets/gallery/{g}',
              os.path.isfile(os.path.join(rootg, g)) and open(os.path.join(rootg, g), 'rb').read() == src
              and open(os.path.join(outd, 'gallery', g), 'rb').read() == src and urlopen(BASE + 'gallery/' + g).read() == src and src[:2] == b'\xff\xd8')
    trk = _sp18.run(['git', 'ls-files', '--', '../gallery', 'assets/gallery'], cwd=here, capture_output=True, text=True).stdout.split()
    check('T-26: gallery/ at the root and _build/assets/gallery/ are tracked in git, 20 files each',
          sorted(trk) == sorted(['../gallery/' + g for g in GAL26] + ['assets/gallery/' + g for g in GAL26]) or
          sorted(trk) == sorted(['gallery/' + g for g in GAL26] + ['_build/assets/gallery/' + g for g in GAL26]), str(trk[:3]) + f' ({len(trk)})')

    # The words: studio.json holds the item's words character for character, and the page prints them from there.
    sj26 = _json26.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
    want26 = {'heading': T26_HEADING, 'apps': [{'name': a, 'groups': [dict({'label': l}, **({'caption': c} if c else {}), **({'numbered': True} if num else {}),
              items=[dict({'file': f}, **({'caption': fc} if fc else {}), alt=alt) for f, fc, alt in its]) for l, c, num, its in gs]} for a, gs in T26_APPS]}
    gal26 = dict(sj26.get('gallery') or {}, apps=[{k: v for k, v in x.items() if k not in ('product', 'id')} for x in (sj26.get('gallery') or {}).get('apps', [])])   # T-29 adds "product" (an id, not a word); its block checks it. T-33 R13 adds "id" (Birdsighted's anchor); the T-33 block checks it
    check('T-26: studio.json\'s "gallery" holds the item\'s words character for character, in order', gal26 == want26)
    check('T-26: studio.json\'s _about says the gallery\'s words live in "gallery" too', 'The gallery\'s words live in "gallery" too' in sj26['_about'])
    gw26 = _json26.dumps(sj26['gallery'], ensure_ascii=False)
    check('T-26: the gallery\'s words have no em dash and only straight apostrophes', '—' not in gw26 and '’' not in gw26 and '‘' not in gw26 and "'" in gw26)
    check('T-26: no em dash on studio.html, and no new en dash', '—' not in SRC26['studio.html'] and SRC26['studio.html'].count('–') == OLD26['studio.html'].count('–'))
    st26, en26 = (open(os.path.join(here, f), encoding='utf-8').read() for f in ('tools/studio.py', 'enhance.py'))
    check('T-26: studio.py holds none of the gallery\'s words (it prints them from studio.json) and writes its CSS into studio.html only',
          'def gallery(studio)' in st26 and 'css=CSS + LOG_PHONE_CSS + GALLERY_CSS' in st26
          and not any(s in st26 for s in [T26_HEADING, 'November 2026', 'One case, start to finish', 'Pick a case', 'A spreadsheet', 'A Figma sketch'])
          and all(('.gal{gap:28px}' in SRC26[n]) == (n == 'studio.html') for n in ALL_HTML))
    check('T-26: enhance.py copies _build/assets/gallery/ to out/gallery/, as it copies bird-league-then-now.jpg',
          '(HERE / "assets" / "gallery").glob("*.jpg")' in en26 and 'shutil.copy(jpg, OUT / "gallery" / jpg.name)' in en26)
    check('T-26: the gallery is one section on studio.html and on no other page',
          SRC26['studio.html'].count('aria-labelledby="gallery-h"') == 1 and not any('gallery-h' in SRC26[n] for n in ALL_HTML if n != 'studio.html'))

    GAL26_JS = r'''() => { const ss = document.querySelectorAll('section[aria-labelledby="gallery-h"]'); if (ss.length !== 1) return null; const sec = ss[0];
      const h2 = sec.querySelector('h2'), tx = [], w = document.createTreeWalker(sec, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const s = n.data.replace(/\s+/g, ' ').trim(); if (s) tx.push(s); }
      return {place: [sec.parentElement.tagName, sec.previousElementSibling && sec.previousElementSibling.id,
                      sec.nextElementSibling && sec.nextElementSibling.getAttribute('aria-labelledby')],
        h2: [h2.id, h2.className, h2.textContent, sec.querySelectorAll('h2').length], text: tx,
        apps: [...sec.querySelectorAll(':scope > .gapp')].map(a => ({h3: [...a.querySelectorAll('h3')].map(h => h.textContent),
          first: a.firstElementChild.tagName,
          groups: [...a.querySelectorAll('.ggroup')].map(g => { const r = g.querySelector('.grow');
            return {label: [...g.querySelectorAll('.ghead .label')].map(e => e.textContent), cap: [...g.querySelectorAll('.ghead .gcap')].map(e => e.textContent),
              row: [r.getAttribute('role'), r.getAttribute('tabindex'), r.getAttribute('aria-label')],
              items: [...r.children].map(f => ({tag: f.tagName, imgs: f.querySelectorAll('img').length, caps: [...f.querySelectorAll('figcaption')].map(c => c.textContent),
                capLast: !f.querySelector('figcaption') || f.lastElementChild.tagName === 'FIGCAPTION',
                src: f.querySelector('img').getAttribute('src'), alt: f.querySelector('img').getAttribute('alt'),
                w: f.querySelector('img').getAttribute('width'), h: f.querySelector('img').getAttribute('height'),
                loading: f.querySelector('img').getAttribute('loading'), decoding: f.querySelector('img').getAttribute('decoding')}))}; })}))}; }'''
    q = newpage(1440); q.goto(UN29 + 'studio.html'); settle(q); G = q.evaluate(GAL26_JS)   # T-29: the section's place and words as at T-27 (un29); the T-29 block checks the new ones
    nat = q.evaluate('''async (srcs) => Promise.all(srcs.map(s => new Promise(r => { const i = new Image(); i.onload = () => r([i.naturalWidth, i.naturalHeight]); i.onerror = () => r(null); i.src = s; })))''',
                     ['gallery/' + g for g in GAL26])
    q.close()
    check('T-26: one gallery section on studio.html', G is not None)
    G = G or {'place': [], 'h2': [], 'text': [], 'apps': []}
    check('T-26: the section sits in <main>, right after the product cards and right before "Your pile could be next"', G['place'] == ['MAIN', 'products', 'next-h'], str(G['place']))
    check('T-26: its heading is one h2#gallery-h.big, "Inside the apps"', G['h2'] == ['gallery-h', 'big', T26_HEADING, 1], str(G['h2']))
    want_text = [T26_HEADING]
    for a, gs in T26_APPS:
        want_text.append(a)
        for l, c, num, its in gs:
            want_text += [l] + ([c] if c else []) + [f'{k}. {fc}' if num else fc for k, (_f, fc, _alt) in enumerate(its, 1) if fc]
    check('T-26: the section\'s words are exactly the item\'s, in order, and nothing else', G['text'] == want_text, f'{G["text"][:8]} vs {want_text[:8]}')
    check('T-26: the three apps in order, each one h3 with its name, first in its block', [x['h3'] for x in G['apps']] == [[a] for a, _g in T26_APPS]
          and all(x['first'] == 'H3' for x in G['apps']), str([x['h3'] for x in G['apps']]))
    nimg = 0
    for (a, gs), ga in zip(T26_APPS, G['apps']):
        check(f'T-26: {a} has its groups in order', [g['label'] for g in ga['groups']] == [[l] for l, *_r in gs], str([g['label'] for g in ga['groups']]))
        for (l, c, num, its), gg in zip(gs, ga['groups']):
            check(f'T-26: {a}, "{l}": its caption on the group is {c!r}', gg['cap'] == ([c] if c else []), str(gg['cap']))
            check(f'T-26: {a}, "{l}": its row is a region, tabindex 0, named "{a}, {l.lower()}"', gg['row'] == ['region', '0', f'{a}, {l.lower()}'], str(gg['row']))
            check(f'T-26: {a}, "{l}": its images in order', [x['src'] for x in gg['items']] == ['gallery/' + f for f, *_r in its], str([x['src'] for x in gg['items']]))
            for (f, fc, alt), it in zip(its, gg['items']):
                nimg += 1
                k = GAL26.index(f)
                check(f'T-26: {f}: a <figure> with one <img>, its alt, its width and height from the file, lazy, async',
                      it['tag'] == 'FIGURE' and it['imgs'] == 1 and it['alt'] == alt and nat[k] is not None
                      and [int(it['w']), int(it['h'])] == nat[k] and it['loading'] == 'lazy' and it['decoding'] == 'async', f'{it} {nat[k]}')
                cap = (f'{its.index((f, fc, alt)) + 1}. {fc}' if num else fc) if fc else None
                check(f'T-26: {f}: a <figcaption> only when it has a caption ({cap!r}), after its image',
                      it['caps'] == ([cap] if cap else []) and it['capLast'], str(it['caps']))
    check('T-26: 20 images in the section', nimg == 20 and sum(len(g['items']) for x in G['apps'] for g in x['groups']) == 20)
    check('T-26: Birdsighted\'s captions read "1. Pick a case" to "5. Earn your rank"',
          [c for g in G['apps'][2]['groups'] for x in g['items'] for c in x['caps']] == ['1. Pick a case', '2. Read the clues', '3. See what you missed', '4. Learn why', '5. Earn your rank']
          if len(G['apps']) == 3 else False)

    # The look, measured with every image loaded, at 320, 390, 1024 and 1440.
    LOAD26_JS = r'''async () => { const imgs = [...document.querySelectorAll('section[aria-labelledby="gallery-h"] img')];
      for (const r of document.querySelectorAll('section[aria-labelledby="gallery-h"] .grow')) { r.scrollLeft = r.scrollWidth; await new Promise(f => setTimeout(f, 120)); r.scrollLeft = 0; }
      imgs.forEach(i => { i.loading = 'eager'; });
      await Promise.all(imgs.map(i => i.complete && i.naturalWidth ? 1 : new Promise(f => { i.onload = f; i.onerror = f; })));
      await Promise.all(imgs.map(i => i.decode().catch(() => 0))); return imgs.filter(i => i.naturalWidth > 0).length; }'''
    LOOK26_JS = r'''() => { const sec = document.querySelector('section[aria-labelledby="gallery-h"]'), sr = sec.getBoundingClientRect();
      const cs = e => getComputedStyle(e), ref = document.querySelector('.prod.feature img'), lab = sec.querySelector('.ghead .label'), lh = document.getElementById('log-h'), gh = document.getElementById('gallery-h');
      const pick = (e, ks) => ks.map(k => cs(e)[k]);
      return {sec: [sr.left, sr.right], vw: innerWidth, page: [document.documentElement.scrollWidth, document.documentElement.clientWidth, scrollX],
        h2: [pick(gh, ['fontFamily', 'fontSize', 'fontWeight', 'textTransform', 'lineHeight']), pick(lh, ['fontFamily', 'fontSize', 'fontWeight', 'textTransform', 'lineHeight'])],
        label: pick(lab, ['fontFamily', 'fontSize', 'letterSpacing', 'textTransform']),
        border: [[...sec.querySelectorAll('img')].map(i => pick(i, ['borderTopWidth', 'borderTopStyle', 'borderTopColor', 'borderTopLeftRadius', 'borderBottomRightRadius']).join(' ')),
                 pick(ref, ['borderTopWidth', 'borderTopStyle', 'borderTopColor', 'borderTopLeftRadius', 'borderBottomRightRadius']).join(' ')],
        rows: [...sec.querySelectorAll('.grow')].map(r => { const rr = r.getBoundingClientRect();
          return {name: r.getAttribute('aria-label'), sw: r.scrollWidth, cw: r.clientWidth, ox: cs(r).overflowX, snap: cs(r).scrollSnapType, wrap: cs(r).flexWrap, right: rr.right,
            figs: [...r.querySelectorAll('figure')].map(f => { const i = f.querySelector('img'), b = i.getBoundingClientRect(), c = f.querySelector('figcaption'), cb = c && c.getBoundingClientRect();
              return {f: i.getAttribute('src'), nw: i.naturalWidth, nh: i.naturalHeight, l: b.left, r: b.right, t: b.top, b: b.bottom, w: b.width, h: b.height,
                      cap: cb && [cb.left, cb.right, cb.top, cb.bottom, c.scrollWidth <= c.clientWidth + 1], snap: cs(f).scrollSnapAlign}; })}; })}; }'''
    for w in (320, 390, 1024, 1440):
        q = newpage(w); q.goto(UN29 + 'studio.html'); settle(q)   # T-29: measured against the Bird League card image, which T-29 takes off the page (un29)
        q.locator('#gallery-h').scroll_into_view_if_needed(); nl = q.evaluate(LOAD26_JS); q.wait_for_timeout(150)
        L = q.evaluate(LOOK26_JS)
        phone = w < 800
        shot = 200 if phone else 220
        check(f'T-26: at {w}, all 20 images load', nl == 20, str(nl))
        check(f'T-26: at {w}, studio.html has no sideways scroll', L['page'][0] <= L['page'][1] and L['page'][2] == 0, str(L['page']))
        check(f'T-26: at {w}, the heading is styled like "Shipped lately" (.big at the section size)', L['h2'][0] == L['h2'][1], str(L['h2']))
        check(f'T-26: at {w}, the group labels are styled like the page\'s .label (JetBrains Mono, 12 px, 0.08em, capitals)',
              'JetBrains Mono' in L['label'][0] and L['label'][1:] == ['12px', '0.96px', 'uppercase'], str(L['label']))
        check(f'T-26: at {w}, every image has the Bird League card image\'s 1.5px #CFC6B2 border and 2px radius',
              all(x == L['border'][1] for x in L['border'][0]) and _re.fullmatch(r'1(?:\.5)?px solid rgb\(207, 198, 178\) 2px 2px', L['border'][1]) is not None
              and 'border:1.5px solid #CFC6B2;border-radius:2px' in SRC26['studio.html'].split('.grow img{', 1)[-1].split('}', 1)[0],
              f"{L['border'][1]} / {L['border'][0][:1]}")
        for r in L['rows']:
            figs = r['figs']
            hs = {round(f['h'], 1) for f in figs}
            ph = [f for f in figs if (f['nw'], f['nh']) == (660, 1349)]
            check(f'T-26: at {w}, "{r["name"]}": every image the same height, and phone shots about {shot} px wide',
                  max(hs) - min(hs) < 0.6 and all(abs(f['w'] - shot) <= 1.5 for f in ph), f'{hs} {[round(f["w"], 1) for f in ph][:3]}')
            check(f'T-26: at {w}, "{r["name"]}": every image keeps its own shape (border aside)',
                  all(abs((f['w'] - 3) / (f['h'] - 3) - f['nw'] / f['nh']) < 0.01 for f in figs), str([(round(f['w'], 1), round(f['h'], 1), f['nw'], f['nh']) for f in figs][:3]))
            check(f'T-26: at {w}, "{r["name"]}": each caption sits under its own image, inside its width, not cut',
                  all(f['cap'] is None or (f['cap'][2] >= f['b'] - 0.5 and f['cap'][0] >= f['l'] - 1 and f['cap'][1] <= f['r'] + 1 and f['cap'][3] - f['b'] < 60 and f['cap'][4]) for f in figs),
                  str([(f['f'], f['cap'], f['l'], f['r'], f['b']) for f in figs if f['cap']][:2]))
            if phone:
                fits = r['name'] == 'Deepcuts, then'
                check(f'T-26: at {w}, "{r["name"]}" is one row that scrolls sideways inside itself (overflow-x auto, scroll-snap)',
                      r['ox'] == 'auto' and r['snap'].startswith('x') and r['wrap'] == 'nowrap' and len({round(f['t']) for f in figs}) == 1
                      and all(f['snap'] == 'start' for f in figs) and ((r['sw'] <= r['cw']) if fits else (r['sw'] > r['cw'])), str(r)[:200])
                if not fits:
                    edge = min(r['right'], L['vw'])
                    check(f'T-26: at {w}, "{r["name"]}" shows there is more: an image runs on past the screen\'s edge', any(f['l'] < edge - 4 < f['r'] or f['l'] < edge < f['r'] for f in figs),
                          str([(round(f['l']), round(f['r'])) for f in figs][:3]) + f' edge {edge}')
                    e = q.evaluate('''(name) => { const r = [...document.querySelectorAll('.grow')].find(x => x.getAttribute('aria-label') === name); r.scrollLeft = r.scrollWidth;
                      return new Promise(f => setTimeout(() => { const im = [...r.querySelectorAll('img')], last = im[im.length - 1].getBoundingClientRect(), s = r.closest('section').getBoundingClientRect();
                        const out = [r.scrollLeft, r.scrollWidth - r.clientWidth, last.left, last.right, s.right, scrollX, document.documentElement.scrollWidth, innerWidth]; r.scrollLeft = 0; f(out); }, 400)); }''', r['name'])
                    check(f'T-26: at {w}, "{r["name"]}" scrolls to its end inside itself, its last image ending inside the section, the page not moving sideways',
                          e[0] == e[1] > 0 and e[3] <= e[4] + 1 and e[3] >= e[4] - 2 and e[2] >= 0 and e[5] == 0 and e[6] <= e[7], str(e))
            else:
                check(f'T-26: at {w}, "{r["name"]}" wraps into rows inside the section, with nothing to scroll',
                      r['wrap'] == 'wrap' and r['sw'] <= r['cw'] and all(f['r'] <= L['sec'][1] + 0.5 and f['l'] >= L['sec'][0] - 0.5 for f in figs), str(r)[:200])
        if w == 1440:
            bs = next(r for r in L['rows'] if r['name'].startswith('Birdsighted'))
            check('T-26: at 1440, Birdsighted\'s five steps sit in one row', len({round(f['t']) for f in bs['figs']}) == 1, str([round(f['t']) for f in bs['figs']]))
            bt = next(r for r in L['rows'] if r['name'] == 'Bird League, then')
            check('T-26: at 1440, the Figma photo sits beside the first build at the same height, unstretched',
                  len({round(f['t']) for f in bt['figs']}) == 1 and abs(bt['figs'][0]['w'] - 3 - (bt['figs'][0]['h'] - 3) * 660 / 762) < 1.5, str(bt['figs'])[:200])
        # Keyboard: from the last link before the gallery, Tab reaches each row in order, with the page's standard focus ring.
        names26 = [f'{a}, {l.lower()}' for a, gs in T26_APPS for l, *_r in gs]
        q.focus('a[href="https://chucklefits.com/?' + T27_TAG + '"]')   # T-27: the shop link now carries the shelf tag
        seen, rings = [], []
        for _k in range(len(names26)):
            q.keyboard.press('Tab')
            seen.append(q.evaluate("document.activeElement.getAttribute('aria-label')"))
            rings.append(q.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset].join(' '); })()"))
        check(f'T-26: at {w}, Tab reaches the five rows in order, right after the last product link', seen == names26, str(seen))
        check(f'T-26: at {w}, a focused row shows the page\'s standard focus ring (3px solid #E8592B, 3px out)',
              all(x == 'solid 3px rgb(232, 89, 43) 3px' for x in rings), str(rings[:2]))
        if phone:
            q.focus('.grow[aria-label="Bird League, now"]'); x0 = q.evaluate("document.querySelector('.grow[aria-label=\"Bird League, now\"]').scrollLeft")
            q.keyboard.press('ArrowRight'); q.wait_for_timeout(600)
            x1 = q.evaluate("[document.querySelector('.grow[aria-label=\"Bird League, now\"]').scrollLeft, scrollX]")
            check(f'T-26: at {w}, a focused row scrolls sideways with the arrow keys, and the page doesn\'t', x0 == 0 and x1[0] > 0 and x1[1] == 0, f'{x0} {x1}')
        q.close()


# ---------------- T-27 (Nov 18, 2026): the ChuckleFits shelf on the Studio page ----------------
@section('T-27')
def s_t_27():
    # Six products from the Nov 18 shop snapshot inside the ChuckleFits card, each one link to its shop page with
    # the shelf tag; "Visit the shop" tagged too; nothing else changed. Comparisons are against T-26's own build
    # (origin/main at 58a8075, the base this item was cut from), read from git.
    import pathlib as _pl27
    T26C = '58a8075efe480ab26b2f58562707a53cd67425f2'
    T26_FILES = {}

    def t26_file(path):
        if path not in T26_FILES:
            r = _sp18.run(['git', 'show', f'{T26C}:{path}'], cwd=here, capture_output=True)
            T26_FILES[path] = r.stdout if r.returncode == 0 else None
        return T26_FILES[path]
    check('T-27: the T-26 files can be read from git for comparison', t26_file('studio.html') is not None and t26_file('gallery/birdsighted-5-rank.jpg') is not None)
    SRC27 = {n: un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: studio's and local's paragraphs back (the T-30 block checks them)
    OLD27 = {n: t26_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT27 = {n: un30(open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: as SRC27
    TAGQ = T27_TAG.replace('&', '&amp;')
    SHOP27 = 'https://chucklefits.com/?' + T27_TAG
    H27 = [h for h, *_r in T27_SHELF]
    sj27 = _json26.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
    cf27 = next(x for x in sj27['products'] if x['id'] == 'chucklefits')
    shelf27 = cf27.get('shelf') or []

    # The whole build: studio.html is T-26's page with only the shelf and the two tagged shop addresses; every other
    # page is byte for byte T-26's (the two product pages differ only by studio.py's stamp line: studio.json's hash).
    check('T-27: un27() takes something out of studio.html (the shelf is there)', un27(SRC27['studio.html'], 'studio.html') != SRC27['studio.html'])
    for n in ALL_HTML:
        if n == 'studio.html':
            a, b_ = stamp27(un27(SRC27[n], n)), stamp27(OLD27[n])
            check('T-27: studio.html is T-26\'s page with only the shelf (its CSS and its block) added and the shop addresses tagged, the build day aside', a == b_,
                  next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
        elif n.startswith('studio-'):
            dl = [(x, y) for x, y in zip(SRC27[n].split('\n'), OLD27[n].split('\n')) if x != y]
            check(f'T-27: {n} is T-26\'s page apart from studio.py\'s stamp line', SRC27[n].count('\n') == OLD27[n].count('\n')
                  and all(_re.fullmatch(STAMP26, x) and _re.fullmatch(STAMP26, y) for x, y in dl), str(dl[:2]))
        else:
            check(f'T-27: {n} is byte for byte as at T-26', SRC27[n] == OLD27[n])
    check('T-27: every root page is the built page', not t32_root_off(ALL_HTML), str(t32_root_off(ALL_HTML)))   # T-32: the themed build
    t26tree = [f for f in _sp18.run(['git', 'ls-tree', '-r', '--full-tree', '--name-only', T26C], cwd=here, capture_output=True, text=True).stdout.split('\n') if f]
    pub26 = [f for f in t26tree if not f.startswith('_build/') and not f.endswith('.html')]
    check('T-27: every other public file at the root (sitemap, robots, images, gallery, share cards...) is byte for byte as at T-26',
          len(pub26) > 40 and all(rb26(f) == t26_file(f).replace(b'\r\n', b'\n') for f in pub26),
          str([f for f in pub26 if rb26(f) != t26_file(f).replace(b'\r\n', b'\n')][:5]))
    outf27 = sorted(os.path.relpath(os.path.join(d, f), outd).replace(os.sep, '/') for d, _x, fs in os.walk(outd) for f in fs)
    check('T-27: the build adds only images/shelf/ with the six photos (every other file in out/ was at the root at T-26)',
          sorted(f for f in outf27 if f not in set(t26tree)) == sorted(f'images/shelf/{h}.jpg' for h in H27), str([f for f in outf27 if f not in set(t26tree)][:10]))
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>'),
                         ('alt texts', r'\balt="[^"]*"'), ('aria-labels', r'\baria-label="[^"]*"'), ('placeholders', r'\bplaceholder="[^"]*"'),
                         ('labels', r'<label\b[^>]*>.*?</label>')):
            check(f'T-27: {n} keeps its {what} (the shelf\'s own aside)',
                  _re.findall(rx, un27(SRC27[n], n), _re.S) == _re.findall(rx, OLD27[n], _re.S))

    # studio.json: the snapshot's six in its order, the tag, and the note in _about.
    check('T-27: studio.json\'s chucklefits product carries the snapshot\'s link_tag', cf27.get('link_tag') == T27_TAG, str(cf27.get('link_tag')))
    check('T-27: studio.json\'s shelf holds the snapshot\'s six, in its order', [x.get('handle') for x in shelf27] == H27, str([x.get('handle') for x in shelf27]))
    for (h, nm, kd, pr), x in zip(T27_SHELF, shelf27):
        check(f'T-27: studio.json shelf {h}: name, kind and price as in the snapshot, the local photo path, an alt, tags',
              x.get('name') == nm and x.get('kind') == kd and 'From $' + x.get('price', '').replace('.00', '') == pr
              and x.get('image') == f'images/shelf/{h}.jpg' and len(x.get('alt', '')) > 40 and isinstance(x.get('tags'), list) and len(x['tags']) > 0, str(x)[:160])
    check('T-27: no shelf product has a tag containing "unhinged"', not any('unhinged' in tg.lower() for x in shelf27 for tg in x.get('tags', [])))
    sw27 = ' '.join(x.get(k, '') for x in shelf27 for k in ('name', 'kind', 'alt'))
    check('T-27: the shelf\'s words have no em dash and only straight apostrophes', '—' not in sw27 and '’' not in sw27 and '‘' not in sw27 and "'" in sw27)
    check('T-27: studio.json\'s _about says the shelf lives there and is refreshed from a new shop snapshot',
          'ChuckleFits shelf lives in' in sj27['_about'] and 'refreshed from a new shop snapshot' in sj27['_about'])

    # The photos: six, 480 px wide, byte for byte in _build/assets/shelf/, out/images/shelf/, served, and images/shelf/ at the root, tracked in git.
    ass27 = os.path.join(here, 'assets', 'shelf')
    rts27 = os.path.join(here, '..', 'images', 'shelf')
    check('T-27: _build/assets/shelf/ holds exactly the six photos', sorted(os.listdir(ass27)) == sorted(h + '.jpg' for h in H27), str(sorted(os.listdir(ass27))))
    check('T-27: images/shelf/ at the root holds exactly the same six', os.path.isdir(rts27) and sorted(os.listdir(rts27)) == sorted(h + '.jpg' for h in H27))
    for h in H27:
        f0 = open(os.path.join(ass27, h + '.jpg'), 'rb').read()
        check(f'T-27: images/shelf/{h}.jpg at the root, in out/ and as served is byte for byte _build/assets/shelf/{h}.jpg',
              f0 == open(os.path.join(rts27, h + '.jpg'), 'rb').read() == open(os.path.join(outd, 'images', 'shelf', h + '.jpg'), 'rb').read()
              == urlopen(BASE + f'images/shelf/{h}.jpg').read())
        wh = _studio.jpeg_size(_pl27.Path(os.path.join(ass27, h + '.jpg')))
        check(f'T-27: {h}.jpg is a JPEG 480 px wide', f0[:2] == b'\xff\xd8' and wh[0] == 480 and wh[1] > 0, str(wh))
    tracked27 = _sp18.run(['git', 'ls-files', '--full-name', '_build/assets/shelf', 'images/shelf'], cwd=os.path.join(here, '..'), capture_output=True, text=True).stdout.split()
    check('T-27: images/shelf/ at the root and _build/assets/shelf/ are tracked in git, six files each',
          sorted(tracked27) == sorted([f'_build/assets/shelf/{h}.jpg' for h in H27] + [f'images/shelf/{h}.jpg' for h in H27]), str(tracked27))
    check('T-27: no page hotlinks the shop\'s images', not any('cdn.shopify.com' in SRC27[n] for n in ALL_HTML))

    # The code: studio.py prints the shelf from studio.json, its CSS on studio.html only; enhance.py copies the photos.
    spy27 = open(os.path.join(here, 'tools', 'studio.py'), encoding='utf-8').read()
    check('T-27: studio.py holds none of the shelf\'s names or alts (it prints them from studio.json)',
          not any(x[k] in spy27 for x in shelf27 for k in ('name', 'alt')))
    check('T-27: the shelf\'s CSS is on studio.html and on no product page', '.shelf{' in SRC27['studio.html']
          and not any('.shelf{' in SRC27[n] for n in ALL_HTML if n != 'studio.html'))
    enh27 = open(os.path.join(here, 'enhance.py'), encoding='utf-8').read()
    check('T-27: enhance.py copies _build/assets/shelf/ to out/images/shelf/', '(HERE / "assets" / "shelf")' in enh27 and 'OUT / "images" / "shelf"' in enh27)

    # The unhinged rule: in a temp copy, a shelf product with such a tag stops studio.py, named, and no page is written.
    tmp27 = _tmp.mkdtemp()
    try:
        bd27 = os.path.join(tmp27, '_build')
        os.makedirs(bd27)
        _shutil.copytree(os.path.join(here, 'tools'), os.path.join(bd27, 'tools'), ignore=_shutil.ignore_patterns('__pycache__'))
        _shutil.copy(os.path.join(here, 'shipped.json'), bd27)
        for dd in ('gallery', 'shelf'):
            _shutil.copytree(os.path.join(here, 'assets', dd), os.path.join(bd27, 'assets', dd))
        for case, tagv, pick in (('as is', None, None), ('tagged "unhinged"', 'unhinged', 3), ('tagged "Unhinged Humor"', 'Unhinged Humor', 0)):
            sjx = _json26.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
            cfx = next(x for x in sjx['products'] if x['id'] == 'chucklefits')
            if tagv:
                cfx['shelf'][pick]['tags'].append(tagv)
            _json26.dump(sjx, open(os.path.join(bd27, 'studio.json'), 'w', encoding='utf-8'))
            for f in _pl27.Path(bd27).glob('studio*.html'):
                f.unlink()
            r = _sp.run([sys.executable, 'studio.py', '..'], cwd=os.path.join(bd27, 'tools'), capture_output=True, text=True)
            made = os.path.exists(os.path.join(bd27, 'studio.html'))
            if tagv is None:
                check('T-27: in a temp copy, studio.py builds the page with the shelf as it is', r.returncode == 0 and made, r.stderr[-200:])
            else:
                h = cfx['shelf'][pick]['handle']
                check(f'T-27: in a temp copy, a shelf product {case} stops studio.py, naming the product, and no page is written',
                      r.returncode != 0 and h in r.stderr and 'unhinged' in r.stderr.lower() and not made, (r.stderr or r.stdout)[-240:])
    finally:
        _shutil.rmtree(tmp27, ignore_errors=True)

    # The words: no discount or offer anywhere; inside the card no sale, bundle or shipping and no "$45"; no ChuckleFits on the Mainframe pages.
    for n in ALL_HTML:
        hit = _re.findall(r'discount|free shipping|% off', SRC27[n], _re.I)
        check(f'T-27: {n} says nothing of a discount, free shipping or "% off"', not hit, str(hit[:3]))
    for n in ('mainframe.html', 'comp3.html', 'briefing.html'):
        check(f'T-27: "ChuckleFits" is nowhere on {n}', 'chucklefits' not in SRC27[n].lower() and 'chucklefits' not in ROOT27[n].lower())
    card27 = _re.search(r'<article class="prod[^"]*" data-id="chucklefits">.*?</article>', SRC27['studio.html'], _re.S)
    card27 = card27.group(0) if card27 else ''
    cardtxt27 = _html.unescape(_re.sub(r'<[^>]+>', ' ', card27)) + ' ' + ' '.join(_html.unescape(x) for x in _re.findall(r'\b(?:alt|aria-label)="([^"]*)"', card27))
    check('T-27: the ChuckleFits card holds none of the whole words "sale", "bundle" or "shipping"', bool(card27) and not _re.search(r'\b(?:sale|bundle|shipping)\b', cardtxt27, _re.I),
          str(_re.findall(r'\b(?:sale|bundle|shipping)\b', cardtxt27, _re.I)))
    check('T-27: no "$45" price stands alone in the ChuckleFits card', bool(card27) and not _re.search(r'\$45\b', card27))
    check('T-27: no em dash on studio.html, and no new en dash', '—' not in SRC27['studio.html'] and SRC27['studio.html'].count('–') == OLD27['studio.html'].count('–'))
    shoplinks = [(n, x) for n in ALL_HTML for x in _re.findall(r'href="(https?://(?:www\.)?chucklefits\.com[^"]*)"', SRC27[n])]
    check('T-27: every shop link on the site carries the tag (seven, all on studio.html)',
          len(shoplinks) == 7 and all(n == 'studio.html' and x.endswith('?' + TAGQ) for n, x in shoplinks), str(shoplinks[:3]))
    check('T-27: the ChuckleFits card\'s line is "My humor shirt shop." (Josef cut "I write every line on every shirt."), in studio.json and on the page',
          cf27['what'] == T27_WHAT[1] and card27.count(f'<p>{T27_WHAT[1]}</p>') == 1 and 'I write every line' not in SRC27['studio.html']
          and all('I write every line' not in SRC27[n] for n in ALL_HTML))
    check('T-27: "Visit the shop" keeps its words and goes to the shop\'s front page with the tag',
          card27.count(f'<a class="go" href="https://chucklefits.com/?{TAGQ}">Visit the shop ↗</a>') == 1)

    # The markup, as the browser reads it: inside the card, between its "what" line and its link row.
    SHELF27_JS = r'''() => { const c = document.querySelector('[data-id="chucklefits"]'); if (!c) return null;
      const sh = c.querySelectorAll('.shelf'); if (sh.length !== 1) return {n: sh.length}; const s = sh[0];
      return {n: 1, order: [...c.children].map(e => e.tagName + (e.className ? '.' + e.className : '')),
        region: [s.getAttribute('role'), s.getAttribute('aria-label'), s.getAttribute('tabindex')],
        lists: [...s.children].map(e => e.tagName), lis: s.querySelectorAll('ul > li').length,
        items: [...s.querySelectorAll('ul > li')].map(li => { const a = li.querySelectorAll('a'), x = a[0], im = x ? x.querySelectorAll('img') : [];
          return {links: a.length, kids: li.children.length, href: x && x.getAttribute('href'), target: x && x.getAttribute('target'),
            parts: x ? [...x.children].map(e => e.tagName + (e.className ? '.' + e.className : '')) : [],
            src: im[0] && im[0].getAttribute('src'), alt: im[0] && im[0].getAttribute('alt'), w: im[0] && im[0].getAttribute('width'), h: im[0] && im[0].getAttribute('height'),
            loading: im[0] && im[0].getAttribute('loading'), decoding: im[0] && im[0].getAttribute('decoding'),
            nw: im[0] && im[0].naturalWidth, nh: im[0] && im[0].naturalHeight,
            name: (x.querySelector('.sn') || {}).textContent, kind: (x.querySelector('.sk') || {}).textContent, price: (x.querySelector('.sp') || {}).textContent}; }),
        text: c.innerText.replace(/\s+/g, ' ').trim()}; }'''
    LOAD27_JS = r'''async () => { const s = document.querySelector('.shelf'); const imgs = [...s.querySelectorAll('img')];
      s.scrollLeft = s.scrollWidth; await new Promise(f => setTimeout(f, 150)); s.scrollLeft = 0;
      imgs.forEach(i => { i.loading = 'eager'; });
      await Promise.all(imgs.map(i => i.complete && i.naturalWidth ? 1 : new Promise(f => { i.onload = f; i.onerror = f; })));
      await Promise.all(imgs.map(i => i.decode().catch(() => 0))); await new Promise(f => setTimeout(f, 300)); return imgs.filter(i => i.naturalWidth > 0).length; }'''
    LOOK27_JS = r'''() => { const c = document.querySelector('[data-id="chucklefits"]'), cs = getComputedStyle(c), cr = c.getBoundingClientRect();
      const s = c.querySelector('.shelf'), ss = getComputedStyle(s), ul = s.querySelector('ul'), ref = document.querySelector('.prod.feature img');
      const st = e => getComputedStyle(e), R = e => { const r = e.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height}; };
      const inner = {l: cr.left + parseFloat(cs.borderLeftWidth), r: cr.right - parseFloat(cs.borderRightWidth)};
      const content = {l: inner.l + parseFloat(cs.paddingLeft), r: inner.r - parseFloat(cs.paddingRight)};
      return {page: [document.documentElement.scrollWidth, innerWidth, scrollX], inner, content, card: R(c),
        shelf: {ox: ss.overflowX, snap: ss.scrollSnapType, sw: s.scrollWidth, cw: s.clientWidth, disp: st(ul).display, r: R(s)},
        items: [...s.querySelectorAll('li')].map(li => { const im = li.querySelector('img'), sn = li.querySelector('.sn'), sk = li.querySelector('.sk'), sp = li.querySelector('.sp');
          return {li: R(li), img: R(im), sn: R(sn), sk: R(sk), sp: R(sp), snOver: sn.scrollWidth > sn.clientWidth + 1,
            snap: st(li).scrollSnapAlign,
            border: [st(im).borderTopWidth, st(im).borderTopStyle, st(im).borderTopColor, st(im).borderTopLeftRadius].join(' '),
            snFont: [st(sn).fontFamily.split(',')[0].replace(/["']/g, ''), st(sn).fontWeight, st(sn).fontSize, st(sn).color].join(' '),
            skFont: [st(sk).fontSize, st(sk).color], spFont: [st(sp).fontSize, st(sp).color]}; }),
        refBorder: [st(ref).borderTopWidth, st(ref).borderTopStyle, st(ref).borderTopColor, st(ref).borderTopLeftRadius].join(' ')}; }'''
    for w in (320, 390, 800, 1024, 1199, 1200, 1440):
        q = newpage(w)
        q.goto(UN29 + 'studio.html', wait_until='networkidle'); q.evaluate('document.fonts.ready')   # T-29: measured against the Bird League card image, now off the page (un29); the T-29 block checks the shelf lays out the same
        q.locator('[data-id="chucklefits"]').scroll_into_view_if_needed()
        M0 = q.evaluate(SHELF27_JS)   # the markup as served, before LOAD27_JS makes the photos eager to measure them
        nl = q.evaluate(LOAD27_JS)
        M = q.evaluate(SHELF27_JS)
        if M and M0 and M.get('items') and M0.get('items'):
            for it, it0 in zip(M['items'], M0['items']):
                it['loading'], it['decoding'] = it0['loading'], it0['decoding']
        L = q.evaluate(LOOK27_JS)
        phone = w < 800
        check(f'T-27: at {w}, the six photos load', nl == 6, str(nl))
        check(f'T-27: at {w}, studio.html has no sideways scroll', L['page'][0] <= L['page'][1] and L['page'][2] == 0, str(L['page']))
        if w in (390, 1440):
            check(f'T-27: at {w}, one shelf, inside the ChuckleFits card, between its "what" line and its link row',
                  bool(M) and M.get('n') == 1 and M['order'] == ['H2', 'DIV.meta', 'P', 'DIV.shelf', 'DIV.acts'], str(M and M.get('order')))
            check(f'T-27: at {w}, the shelf is a region named "ChuckleFits shirts", tabindex 0, holding one list of six items',
                  M['region'] == ['region', 'ChuckleFits shirts', '0'] and M['lists'] == ['UL'] and M['lis'] == 6, str([M['region'], M['lists'], M['lis']]))
            for (h, nm, kd, pr), x, it in zip(T27_SHELF, shelf27, M['items']):
                wh = _studio.jpeg_size(_pl27.Path(os.path.join(ass27, h + '.jpg')))
                check(f'T-27: at {w}, {h}: one link to its shop page with the tag, opening in the same tab',
                      it['links'] == 1 and it['kids'] == 1 and it['href'] == f'https://chucklefits.com/products/{h}?{T27_TAG}' and it['target'] is None, str(it['href']))
                check(f'T-27: at {w}, {h}: the link holds its photo, then its name, kind and price', it['parts'] == ['IMG', 'SPAN.sn', 'SPAN.sk', 'SPAN.sp'], str(it['parts']))
                check(f'T-27: at {w}, {h}: name "{nm}", kind "{kd}", price "{pr}", as in studio.json', [it['name'], it['kind'], it['price']] == [nm, kd, pr]
                      and [it['name'], it['kind']] == [x['name'], x['kind']], str([it['name'], it['kind'], it['price']]))
                check(f'T-27: at {w}, {h}: its photo is local, with studio.json\'s alt, width and height from the file, lazy, async',
                      it['src'] == f'images/shelf/{h}.jpg' and it['alt'] == x['alt'] and [it['w'], it['h']] == [str(wh[0]), str(wh[1])]
                      and [it['nw'], it['nh']] == list(wh) and it['loading'] == 'lazy' and it['decoding'] == 'async', str(it)[:200])
            want27 = ' '.join(['CHUCKLEFITS', 'Live', T27_WHAT[1]] + [f'{nm} {kd} {pr}' for _h, nm, kd, pr in T27_SHELF] + ['Visit the shop ↗'])
            check(f'T-27: at {w}, the card reads its old words (its line cut to "{T27_WHAT[1]}", Josef) plus each product\'s name, kind and price, and nothing else', M['text'] == want27, M['text'][:300])
        its = L['items']
        check(f'T-27: at {w}, every photo has the card images\' 1.5px #CFC6B2 border and 2px radius', all(x['border'] == L['refBorder'] for x in its), str([its[0]['border'], L['refBorder']]))
        check(f'T-27: at {w}, names in Instrument Sans 700, kind and price smaller in #5A635D',
              all(x['snFont'].startswith('Instrument Sans 700 ') for x in its)
              and all(x['skFont'][1] == x['spFont'][1] == 'rgb(90, 99, 93)' and float(x['skFont'][0][:-2]) < float(x['snFont'].split(' ')[3][:-2]) for x in its),
              str([its[0]['snFont'], its[0]['skFont'], its[0]['spFont']]))
        check(f'T-27: at {w}, no name runs past its card, and each name, kind and price sits under its own photo, in order',
              all(not x['snOver'] and x['li']['l'] - 0.5 <= x[k]['l'] and x[k]['r'] <= x['li']['r'] + 0.5 for x in its for k in ('img', 'sn', 'sk', 'sp'))
              and all(x['img']['b'] <= x['sn']['t'] < x['sk']['t'] < x['sp']['t'] for x in its), str(its[0])[:240])
        check(f'T-27: at {w}, every photo is square at the item\'s width', all(abs(x['img']['w'] - x['li']['w']) < 1 and abs(x['img']['w'] - x['img']['h']) < 1 for x in its),
              str([(round(x['img']['w']), round(x['img']['h'])) for x in its][:2]))
        if phone:
            check(f'T-27: at {w}, the six sit in one row that scrolls sideways inside the card (overflow-x auto, scroll-snap)',
                  L['shelf']['ox'] == 'auto' and L['shelf']['snap'].startswith('x mandatory') and L['shelf']['disp'] == 'flex'
                  and len({round(x['li']['t']) for x in its}) == 1 and L['shelf']['sw'] > L['shelf']['cw'] and all(x['snap'] == 'start' for x in its),
                  str([L['shelf'], [round(x['li']['t']) for x in its]]))
            cut = [x for x in its if x['li']['l'] < L['inner']['r'] < x['li']['r']]
            check(f'T-27: at {w}, the next product shows cut at the card\'s edge, so the row reads as more',
                  len(cut) == 1 and 0.25 < (L['inner']['r'] - cut[0]['li']['l']) / cut[0]['li']['w'] < 0.9, str([(round(x['li']['l']), round(x['li']['r'])) for x in its] + [L['inner']]))
            check(f'T-27: at {w}, the row starts on the card\'s content edge', abs(its[0]['li']['l'] - L['content']['l']) < 1, f'{its[0]["li"]["l"]} vs {L["content"]["l"]}')
            q.evaluate("document.querySelector('.shelf').scrollLeft = 1e5"); q.wait_for_timeout(600)
            E = q.evaluate(LOOK27_JS)
            last = E['items'][-1]['li']
            check(f'T-27: at {w}, scrolled to its end, the row\'s last product ends on the card\'s content edge, inside the card, and the page doesn\'t move',
                  abs(last['r'] - E['content']['r']) < 1.5 and last['l'] >= E['inner']['l'] and E['page'][2] == 0 and E['page'][0] <= E['page'][1],
                  f'{last} {E["content"]} {E["page"]}')
            q.evaluate("document.querySelector('.shelf').scrollLeft = 0"); q.wait_for_timeout(300)
        else:
            per = 3 if w < 1200 else 6
            rows = sorted({round(x['li']['t']) for x in its})
            check(f'T-27: at {w}, {per} across ({6 // per} row{"s" if per == 3 else ""}), nothing to scroll',
                  len(rows) == 6 // per and all(sum(1 for x in its if round(x['li']['t']) == t) == per for t in rows) and L['shelf']['sw'] <= L['shelf']['cw'] + 1,
                  str([rows, L['shelf']['sw'], L['shelf']['cw']]))
            ws = [x['li']['w'] for x in its]
            gaps = [round(its[i + 1]['li']['l'] - its[i]['li']['r'], 1) for i in range(per - 1)]
            check(f'T-27: at {w}, the products are one even width with even gaps, inside the card\'s content edges',
                  max(ws) - min(ws) < 1 and max(gaps) - min(gaps) < 1 and min(x['li']['l'] for x in its) >= L['content']['l'] - 0.5
                  and max(x['li']['r'] for x in its) <= L['content']['r'] + 0.5, str([ws[:2], gaps, L['content']]))
        # Keyboard: from the last link before the shelf, Tab reaches the row, then its six links in order, then "Visit the shop".
        q.focus('[data-id="tools"] a.go')
        seen = []
        for _k in range(8):
            q.keyboard.press('Tab')
            seen.append(q.evaluate("(() => { const e = document.activeElement; return e.getAttribute('aria-label') || e.getAttribute('href'); })()"))
        want_tab = ['ChuckleFits shirts'] + [f'https://chucklefits.com/products/{h}?{T27_TAG}' for h in H27] + [SHOP27]
        check(f'T-27: at {w}, Tab reaches the row, then its six links in order, then "Visit the shop"', seen == want_tab, str(seen))
        q.focus('.shelf')
        ring = q.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset].join(' '); })()")
        check(f'T-27: at {w}, the focused row shows the page\'s standard focus ring (3px solid #E8592B, 3px out)', ring == 'solid 3px rgb(232, 89, 43) 3px', ring)
        if phone:
            q.evaluate("document.querySelector('.shelf').scrollLeft = 0"); q.wait_for_timeout(400)   # Tab above scrolled it along
            x0 = q.evaluate("document.querySelector('.shelf').scrollLeft")
            q.keyboard.press('ArrowRight'); q.wait_for_timeout(700)
            x1 = q.evaluate("[document.querySelector('.shelf').scrollLeft, scrollX]")
            check(f'T-27: at {w}, the focused row scrolls sideways with the arrow keys, and the page doesn\'t', x0 == 0 and x1[0] > 0 and x1[1] == 0, f'{x0} {x1}')
            q.locator('.shelf a').last.focus(); q.wait_for_timeout(600)
            x2 = q.evaluate("[document.querySelector('.shelf').scrollLeft, scrollX, (() => { const r = document.activeElement.getBoundingClientRect(), c = document.querySelector('[data-id=chucklefits]').getBoundingClientRect(); return r.right <= c.right && r.left >= c.left; })()]")
            check(f'T-27: at {w}, tabbing to the last product scrolls the row to show it inside the card, and the page doesn\'t move sideways', x2[0] > 0 and x2[1] == 0 and x2[2], str(x2))
        q.close()


# ---------------- T-29 (Nov 18, 2026): one block per app on the Studio page ----------------
@section('T-29')
def s_t_29():
    # Bird League and Deepcuts each show once: their "Inside the apps" block opens with the card's words (pill, what,
    # proof, "More on" link, join form) and the cards are gone; the section sits right after "Shipped lately".
    # Comparisons are against T-27's own build (origin/main at 4a76a78, the base this item was cut from), read from git.
    T27C = '4a76a78'
    T27_FILES = {}

    def t27_file(path):
        if path not in T27_FILES:
            r = _sp18.run(['git', 'show', f'{T27C}:{path}'], cwd=here, capture_output=True)
            T27_FILES[path] = r.stdout if r.returncode == 0 else None
        return T27_FILES[path]
    check('T-29: the T-27 files can be read from git for comparison', t27_file('studio.html') is not None and t27_file('images/shelf/love-your-mother-5-panel-cap.jpg') is not None)
    SRC29 = {n: un30(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: studio's and local's paragraphs back (the T-30 block checks them)
    OLD29 = {n: t27_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT29 = {n: un30(open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n'), n) for n in ALL_HTML}   # T-30: as SRC29
    S29 = SRC29['studio.html']
    sj29 = _json26.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
    P29 = {x['id']: x for x in sj29['products']}
    APPS29 = {'birdleague': 'Bird League', 'deepcuts': 'Deepcuts'}

    # The whole build: studio.html is T-27's page once un29() puts the cards back (stamp line aside); every other page byte for byte.
    check('T-29: un29() changes studio.html (the blocks are there)', un29(S29, 'studio.html') != S29)
    for n in ALL_HTML:
        if n == 'studio.html':
            a, b_ = stamp27(un29(S29, n)), stamp27(OLD29[n])
            check('T-29: studio.html is T-27\'s page with only the cards moved into their blocks, the section moved up, Free tools spanning its row and the new CSS, the stamp line aside', a == b_,
                  next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
        elif n.startswith('studio-'):
            dl = [(x, y) for x, y in zip(SRC29[n].split('\n'), OLD29[n].split('\n')) if x != y]
            check(f'T-29: {n} is T-27\'s page apart from studio.py\'s stamp line (build day and studio.json\'s hash)', SRC29[n].count('\n') == OLD29[n].count('\n')
                  and all(_re.fullmatch(STAMP26, x) and _re.fullmatch(STAMP26, y) for x, y in dl), str(dl[:2]))
            check(f'T-29: {n} still shows the product image as at T-27', SRC29[n].count('<img src="') == OLD29[n].count('<img src="'))
        else:
            check(f'T-29: {n} is byte for byte as at T-27', SRC29[n] == OLD29[n])
    check('T-29: every root page is the built page', not t32_root_off(ALL_HTML), str(t32_root_off(ALL_HTML)))   # T-32: the themed build
    t27tree = [f for f in _sp18.run(['git', 'ls-tree', '-r', '--full-tree', '--name-only', T27C], cwd=here, capture_output=True, text=True).stdout.split('\n') if f]
    pub27 = [f for f in t27tree if not f.startswith('_build/') and not f.endswith('.html')]
    check('T-29: every other public file at the root (sitemap, robots, images, gallery, shelf, share cards) is byte for byte as at T-27',
          len(pub27) >= 52 and all(rb26(f) == t27_file(f).replace(b'\r\n', b'\n') for f in pub27), str([f for f in pub27 if rb26(f) != t27_file(f).replace(b'\r\n', b'\n')][:5]))
    outf29 = sorted(os.path.relpath(os.path.join(d, f), outd).replace(os.sep, '/') for d, _x, fs in os.walk(outd) for f in fs)
    check('T-29: the build adds no file (everything in out/ was at the root at T-27)', [f for f in outf29 if f not in set(t27tree)] == [], str([f for f in outf29 if f not in set(t27tree)][:5]))
    check('T-29: the then/now image is off studio.html, and still on work.html and studio-birdleague.html',
          'bird-league-then-now.jpg' not in S29 and 'bird-league-then-now.jpg' in SRC29['work.html'] and 'bird-league-then-now.jpg' in SRC29['studio-birdleague.html'])
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>'), ('scripts', r'<script>.*?</script>'),
                         ('aria-labels', r'\baria-label="[^"]*"'), ('placeholders', r'\bplaceholder="[^"]*"'), ('labels', r'<label\b[^>]*>.*?</label>')):
            check(f'T-29: {n} keeps its {what}', sorted(_re.findall(rx, SRC29[n], _re.S)) == sorted(_re.findall(rx, OLD29[n], _re.S)))
    alts29, alts27 = _re.findall(r'\balt="([^"]*)"', S29), _re.findall(r'\balt="([^"]*)"', OLD29['studio.html'])
    check('T-29: studio.html\'s alt texts are T-27\'s minus the then/now image\'s, and nothing new',
          sorted(alts27) == sorted(alts29 + [P29['birdleague']['image_alt']]), str(sorted(set(alts27) ^ set(alts29))[:3]))

    # The source: one h3 each, no h2, no card; each block's top in order; the join forms as at T-27.
    for pid, nm in APPS29.items():
        check(f'T-29: studio.html has exactly one h3 "{nm}" and no h2 "{nm}"', S29.count(f'<h3>{nm}</h3>') == 1 and f'<h2>{nm}</h2>' not in S29)
        check(f'T-29: no article with data-id "{pid}" on studio.html', f'data-id="{pid}"' not in S29)
    forms = lambda s: _re.findall(r'<form class="jf".*?</form>', s, _re.S)
    check('T-29: studio.html has the same join forms as at T-27, character for character (data-list, mailto action, honeypot, email label, button words), now Deepcuts\' first',
          sorted(forms(S29)) == sorted(forms(OLD29['studio.html'])) and len(forms(S29)) == 2
          and [_re.search(r'data-list="(\w+)"', x).group(1) for x in forms(S29)] == ['deepcuts', 'birdleague'], str(len(forms(S29))))
    for pid in APPS29:
        f = next((x for x in forms(S29) if f'data-list="{pid}"' in x), '')
        lst = P29[pid]['list']
        check(f'T-29: the {pid} join form posts to its list, opens its mailto with scripts off, keeps the honeypot, the email label and "{lst["button"]}"',
              f'data-list="{lst["id"]}"' in f and f'action="mailto:hello@dragomansjourney.com?subject=List%3A%20{P29[pid]["name"].replace(" ", "%20")}"' in f
              and '<input name="website" tabindex="-1" autocomplete="off">' in f and '<span>Email</span><input name="email" type="email" autocomplete="email" required>' in f
              and f'>{lst["button"]}</button>' in f)
    check('T-29: the join script posts to the intake Worker as at T-27', 'https://dj-intake.stephens-josef.workers.dev/' in S29
          and _re.findall(r'<script>.*?</script>', S29, _re.S) == _re.findall(r'<script>.*?</script>', OLD29['studio.html'], _re.S))
    check('T-29: no em dash on studio.html, and no new en dash', '—' not in S29 and S29.count('–') == OLD29['studio.html'].count('–'))
    check('T-29: the new CSS is on studio.html only', '.gprod{' in S29 and not any('.gprod{' in SRC29[n] or '.gtext' in SRC29[n] for n in ALL_HTML if n != 'studio.html'))

    # studio.json and studio.py: the two apps name their product, Birdsighted none; _about says so; the words come from studio.json.
    gapps29 = {x['name']: x for x in sj29['gallery']['apps']}
    check('T-29: studio.json\'s gallery apps Deepcuts and Bird League name their products, Birdsighted none',
          gapps29['Deepcuts'].get('product') == 'deepcuts' and gapps29['Bird League'].get('product') == 'birdleague' and 'product' not in gapps29['Birdsighted'],
          str({k: v.get('product') for k, v in gapps29.items()}))
    check('T-29: studio.json\'s _about says an app with a product shows its card\'s words inside its gallery block instead of as a card',
          'A gallery app with a "product"' in sj29['_about'] and 'inside its gallery block instead of as a card' in sj29['_about'])
    spy29 = open(os.path.join(here, 'tools', 'studio.py'), encoding='utf-8').read()
    check('T-29: studio.py holds none of the two products\' words (it prints them from studio.json)',
          not any(P29[pid][k] in spy29 for pid in APPS29 for k in ('what', 'proof', 'status') if P29[pid][k]) and 'Get the launch email' not in spy29 and 'Join the beta' not in spy29)
    check('T-29: studio.json\'s two products keep every word they had at T-27',
          all(P29[pid] == next(x for x in _json26.loads(t27_file('_build/studio.json').decode('utf-8'))['products'] if x['id'] == pid) for pid in APPS29))

    # The browser: the page, then T-27's page served through un29() (UN29), for the comparisons.
    MAIN29_JS = r'''() => [...document.querySelector('main').children].map(e => e.tagName === 'SECTION' && e.getAttribute('aria-labelledby') === 'log-h' ? 'log'
      : e.getAttribute('aria-labelledby') === 'gallery-h' ? 'gallery' : e.id === 'products' ? 'products:' + [...e.querySelectorAll(':scope > article')].map(a => a.dataset.id).join(',')
      : e.getAttribute('aria-labelledby') === 'next-h' ? 'box' : e.tagName + '.' + e.className)'''
    LINES29_JS = r'''() => document.querySelector('main').innerText.split('\n').map(x => x.replace(/\s+/g, ' ').trim()).filter(Boolean)'''
    BLOCK29_JS = r'''() => [...document.querySelectorAll('.gapp')].map(g => ({h3: g.querySelector('h3').textContent, h3n: g.querySelectorAll('h3').length,
      kids: [...g.children].map(e => e.tagName + '.' + e.className),
      top: g.querySelector('.gprod') ? [...g.querySelector('.gprod').querySelectorAll('.pill, .gtext > p, .gtext > a, form')].map(e =>
        [e.matches('.pill') ? 'pill' : e.matches('p.proof') ? 'proof' : e.tagName === 'P' ? 'what' : e.tagName === 'A' ? 'link' : 'form',
         e.tagName === 'A' ? e.getAttribute('href') : e.tagName === 'FORM' ? e.dataset.list : e.textContent]) : null,
      groups: [...g.querySelectorAll('.ggroup')].map(x => x.outerHTML), text: g.innerText.split('\n').map(x => x.trim()).filter(Boolean)}))'''
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(UN30 + 'studio.html', wait_until='networkidle'); q.evaluate('document.fonts.ready'); q.wait_for_timeout(300)   # T-30: the two "what" lines back, the 34em rule out (un30)
        o = newpage(w); o.goto(UN29 + 'studio.html', wait_until='networkidle'); o.evaluate('document.fonts.ready'); o.wait_for_timeout(300)
        main29, main27 = q.evaluate(MAIN29_JS), o.evaluate(MAIN29_JS)
        check(f'T-29: at {w}, main reads: the log, "Inside the apps", the products grid (kids, cobol, tools, chucklefits), the closing box',
              main29 == ['log', 'gallery', 'products:kids,cobol,tools,chucklefits', 'box'], str(main29))
        check(f'T-29: at {w}, the page served through un29() is T-27\'s order (the check reads what it should)',
              main27 == ['log', 'products:birdleague,deepcuts,kids,cobol,tools,chucklefits', 'gallery', 'box'], str(main27))
        B, B27 = q.evaluate(BLOCK29_JS), o.evaluate(BLOCK29_JS)
        check(f'T-29: at {w}, the gallery\'s three apps are Deepcuts, Bird League and Birdsighted, one h3 each', [x['h3'] for x in B] == ['Deepcuts', 'Bird League', 'Birdsighted'] and all(x['h3n'] == 1 for x in B))
        for x, x27 in zip(B, B27):
            pid = next((k for k, v in APPS29.items() if v == x['h3']), None)
            if pid:
                p = P29[pid]
                want = [['pill', p['status']], ['what', p['what']]] + ([['proof', p['proof']]] if p.get('proof') else []) + [['link', f'studio-{pid}.html'], ['form', pid]]
                check(f'T-29: at {w}, {x["h3"]}\'s block opens with its name, then the pill, the what line,{" the proof line," if p.get("proof") else ""} the "More on" link and the join form, in order',
                      x['kids'][:2] == ['H3.', 'DIV.gprod'] and x['top'] == want, str([x['kids'][:3], x['top']]))
                check(f'T-29: at {w}, {x["h3"]}\'s link reads "More on {x["h3"]} →"', f'More on {x["h3"]} →' in x['text'])
            else:
                check(f'T-29: at {w}, {x["h3"]}\'s block is as at T-27 (no product, no top)', x['top'] is None and x['kids'] == x27['kids'] and x['text'] == x27['text'])
            check(f'T-29: at {w}, {x["h3"]}\'s groups are exactly as at T-27', x['groups'] == x27['groups'] and x['kids'][-len(x27['kids']) + 1:] == x27['kids'][1:])
        L29, L27 = q.evaluate(LINES29_JS), o.evaluate(LINES29_JS)
        from collections import Counter as _C29
        c29, c27 = _C29(L29), _C29(L27)
        dup = _C29({nm.upper(): 1 for nm in APPS29.values()})   # the card h2s; their h3 twins stay
        check(f'T-29: at {w}, every visible line of T-27\'s page is still there, and nothing new: T-27\'s lines minus the two cards\' second name heading',
              c29 == c27 - dup and (c27 - c29) == dup and not (c29 - c27), str([(c27 - c29) - dup, c29 - c27]))
        for pid, nm in APPS29.items():
            blk = next(x for x in B if x['h3'] == nm)
            cl =o.evaluate(f'''() => document.querySelector('[data-id="{pid}"]').innerText.split('\\n').map(x => x.replace(/\\s+/g, ' ').trim()).filter(Boolean)''')
            check(f'T-29: at {w}, every line of T-27\'s {nm} card is in its block exactly once, and on the page as often as the other app\'s copies allow',
                  len(cl) >= 5 and all(blk['text'].count(l) == 1 for l in cl) and all(c29[l] == c27[l] - (1 if l == nm.upper() else 0) for l in cl), str([cl, blk['text'][:8]]))
        q.close(); o.close()

    # Layout: from 900 px the text left (at most 34em) and the join form right, top-aligned; under 900 stacked, text first.
    TOP29_JS = r'''() => [...document.querySelectorAll('.gprod')].map(p => { const R = e => e.getBoundingClientRect(), t = p.querySelector('.gtext'), f = p.querySelector('form.jf');
      const fs = parseFloat(getComputedStyle(t).fontSize), sec = R(p.closest('.gapp'));
      const parts = [...t.querySelectorAll('.pill, :scope > p, :scope > a')].map(e => [R(e).top, R(e).bottom, R(e).left]);
      const lab = f.querySelector('.jf-e span'), inp = f.querySelector('input[name=email]'), btn = f.querySelector('button');
      return {name: p.closest('.gapp').querySelector('h3').textContent, text: [R(t).left, R(t).top, R(t).right, R(t).bottom, R(t).width / fs], form: [R(f).left, R(f).top, R(f).right, R(f).bottom],
        sec: [sec.left, sec.right], parts, labColor: getComputedStyle(lab).color, inp: [R(inp).width, R(inp).height], btn: [R(btn).left, R(btn).top, R(btn).width, R(btn).height],
        rows: [...p.closest('.gapp').querySelectorAll('.grow')].map(r => [r.getAttribute('aria-label'), getComputedStyle(r).overflowX, r.scrollWidth - r.clientWidth])}; })'''
    for w in (320, 390, 899, 900, 1024, 1440):
        q = newpage(w); q.goto(BASE + 'studio.html', wait_until='networkidle'); q.evaluate('document.fonts.ready'); q.wait_for_timeout(300)
        T = q.evaluate(TOP29_JS)
        sw = q.evaluate('[document.documentElement.scrollWidth, innerWidth]')
        check(f'T-29: at {w}, studio.html has no sideways scroll', sw[0] <= sw[1], str(sw))
        for x in T:
            check(f'T-29: at {w}, {x["name"]}: pill, lines and link read top to bottom, each starting on the text\'s left edge',
                  all(a_[1] <= b2[0] + 0.5 for a_, b2 in zip(x['parts'], x['parts'][1:])) and all(abs(pp[2] - x['text'][0]) < 1 for pp in x['parts']), str(x['parts']))
            check(f'T-29: at {w}, {x["name"]}: the text column is at most 34em wide and inside the block', x['text'][4] <= 34.01 and x['text'][0] >= x['sec'][0] - 0.5 and x['text'][2] <= x['sec'][1] + 0.5, str(x['text']))
            check(f'T-29: at {w}, {x["name"]}: the join form sits inside the block', x['form'][0] >= x['sec'][0] - 0.5 and x['form'][2] <= x['sec'][1] + 0.5, str([x['form'], x['sec']]))
            if w >= 900:
                check(f'T-29: at {w}, {x["name"]}: the join form is beside the text, on the right, top-aligned', x['form'][0] >= x['text'][2] + 24 and abs(x['form'][1] - x['text'][1]) <= 1, str([x['text'], x['form']]))
            else:
                check(f'T-29: at {w}, {x["name"]}: the join form is under the text, on its left edge', x['form'][1] >= x['text'][3] + 8 and abs(x['form'][0] - x['text'][0]) < 1, str([x['text'], x['form']]))
            check(f'T-29: at {w}, {x["name"]}: the email field and button are full size (48 px field, 44 px or taller button)', x['inp'][1] >= 47.5 and x['btn'][3] >= 44 and x['inp'][0] >= 200, str([x['inp'], x['btn']]))
            check(f'T-29: at {w}, {x["name"]}: the email label is the darker grey for cream (#676D66)', x['labColor'] == 'rgb(103, 109, 102)', x['labColor'])
            for nm_, ox, extra in x['rows']:
                if w < 800:
                    check(f'T-29: at {w}, the row "{nm_}" still scrolls inside itself (overflow-x auto)', ox == 'auto' and (extra > 0 or nm_ == 'Deepcuts, then'), str([ox, extra]))
                else:
                    check(f'T-29: at {w}, the row "{nm_}" wraps, nothing to scroll', extra <= 0, str([ox, extra]))
        if w in (320, 390, 1440):
            # Keyboard: from "See all", Tab goes through Deepcuts' link, email, button and rows, then Bird League's, then Birdsighted's row, then the first card.
            q.focus('#log-all')
            seen = []
            for _k in range(12):
                q.keyboard.press('Tab')
                seen.append(q.evaluate("(() => { const e = document.activeElement; return e.getAttribute('aria-label') || e.getAttribute('href') || e.getAttribute('name') || e.textContent.trim(); })()"))
            want29 = ['studio-deepcuts.html', 'email', 'Join the beta', 'Deepcuts, then', 'Deepcuts, now', 'studio-birdleague.html', 'email', 'Get the launch email',
                      'Bird League, then', 'Bird League, now', 'Birdsighted, one case, start to finish', 'work.html']
            check(f'T-29: at {w}, Tab from "See all" goes through each block\'s link, email, button and rows in order, then the first card', seen == want29, str(seen))
        q.close()

    # The remaining cards: same width and inner layout as at T-27, apart from Free tools, which now spans its row (T-21 G4:
    # it's alone on it); the ChuckleFits card and its shelf sit exactly as at T-27, measured relative to the card.
    CARDS29_JS = r'''() => { const R = e => e.getBoundingClientRect();
      return [...document.querySelectorAll('#products > article')].map(a => { const c = R(a);
        return [a.dataset.id, Math.round(c.width), Math.round(c.height), [...a.querySelectorAll('h2, .pill, p, .shelf li, .shelf img, a.go')].map(e => { const r = R(e);
          return [e.tagName, Math.round(r.left - c.left), Math.round(r.top - c.top), Math.round(r.width), Math.round(r.height)]; })]; }); }'''
    for w in (320, 390, 800, 1024, 1200, 1440):
        q = newpage(w); q.goto(UN30 + 'studio.html', wait_until='networkidle'); q.evaluate('document.fonts.ready'); q.wait_for_timeout(300)   # T-30: the 34em rule out (un30); the T-30 block checks the card with it
        o = newpage(w); o.goto(UN29 + 'studio.html', wait_until='networkidle'); o.evaluate('document.fonts.ready'); o.wait_for_timeout(300)
        C29, C27 = {x[0]: x for x in q.evaluate(CARDS29_JS)}, {x[0]: x for x in o.evaluate(CARDS29_JS)}
        q.close(); o.close()
        check(f'T-29: at {w}, the ChuckleFits card and its shelf lay out exactly as at T-27', C29.get('chucklefits') == C27.get('chucklefits'), str([C29.get('chucklefits', [])[:3], C27.get('chucklefits', [])[:3]]))
        for pid in ('kids', 'cobol'):
            check(f'T-29: at {w}, the {pid} card is as wide as at T-27', C29[pid][1] == C27[pid][1], str([C29[pid][1], C27[pid][1]]))
        if w >= 800:
            check(f'T-29: at {w}, Free tools spans the row like ChuckleFits (alone on its row, T-21 G4)', C29['tools'][1] == C29['chucklefits'][1] > C29['kids'][1], str([C29['tools'][1], C29['chucklefits'][1]]))
        else:
            check(f'T-29: at {w}, Free tools is as at T-27 (one column)', C29['tools'] == C27['tools'], str([C29['tools'][:3], C27['tools'][:3]]))

    # The join boxes in their new place work as T-10's checks run them in the cards: success posts the right fields and
    # says so; an error answer or no connection falls back to the box's mailto and leaves the box ready.
    for pid in APPS29:
        x = P29[pid]
        box29 = f'.gapp .gprod .gjoin form.jf[data-list="{pid}"]'
        for w in (390, 1440):
            q = newpage(w); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok); q.add_init_script(CATCH_MAILTO)
            q.goto(BASE + 'studio.html'); q.wait_for_timeout(300)
            f = q.locator(box29)
            check(f'T-29: at {w}, {pid}: one join box in its block, email field required, type email, labeled "Email", honeypot off screen',
                  f.count() == 1 and f.locator('input[name="email"][type="email"][required]').count() == 1 and f.locator('label.jf-e span').inner_text().strip().lower() == 'email'
                  and f.locator('.hp input[name="website"]').count() == 1 and f.locator('.hp').bounding_box()['x'] < -1000)
            n0 = len(posts)
            f.locator('button').click(); q.wait_for_timeout(300)
            check(f'T-29: at {w}, {pid}: an empty email sends nothing', len(posts) == n0 and q.evaluate('window.__mailto.length') == 0)
            f.locator('input[name="email"]').fill('  fan@example.com '); q.wait_for_timeout(2700)
            f.locator('button').click(); q.wait_for_timeout(600)
            sent = posts[-1] if len(posts) == n0 + 1 else {}
            check(f'T-29: at {w}, {pid}: posts form=list with the email and list {x["list"]["id"]}, honeypot and time',
                  sent.get('form') == 'list' and sent.get('fields') == {'email': 'fan@example.com', 'list': x['list']['id']}
                  and sent.get('website') == '' and sent.get('ms', 0) >= 2500, str(sent))
            check(f'T-29: at {w}, {pid}: success says "You\'re on the list", hides the field and the button, opens no mailto',
                  f.locator('.jf-ok').inner_text().strip() == "You're on the list" and not f.locator('input[name="email"]').is_visible()
                  and not f.locator('button').is_visible() and q.evaluate('window.__mailto.length') == 0)
            check(f'T-29: at {w}, {pid}: no sideways scroll after success', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.close()
        for how, mock in (('an error answer', mock_fail), ('no connection', mock_abort)):
            q = newpage(390); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock); q.add_init_script(CATCH_MAILTO)
            q.goto(BASE + 'studio.html'); q.wait_for_timeout(300)
            f = q.locator(box29)
            f.locator('input[name="email"]').fill('fan@example.com'); q.wait_for_timeout(2700)
            f.locator('button').click(); q.wait_for_timeout(600)
            got = q.evaluate('window.__mailto')
            check(f'T-29: {pid}: on {how}, falls back to the mailto "List: {x["name"]}" and the box stays ready to try again',
                  len(got) == 1 and got[0] == f.get_attribute('action') and _unquote(got[0].split('subject=', 1)[1]) == 'List: ' + x['name']
                  and f.locator('input[name="email"]').is_visible() and f.locator('button').is_enabled() and f.locator('button').inner_text() == x['list']['button']
                  and f.locator('.jf-ok').inner_text().strip() == '', str(got))
            q.close()


# ---------------- T-30 (Nov 18, 2026): each paragraph lives on one page ----------------
@section('T-30')
def s_t_30():
    # The kids' app and COBOL cards on studio.html print no "what" line, and the four tool cards on local.html print no
    # description; work.html keeps all six. A studio card that spans its row keeps its description at most 34em wide.
    # Comparisons are against T-29's own build (origin/main at d1117bd, the base this item was cut from), read from git.
    T29C = 'd1117bd'
    T29_FILES = {}

    def t29_file(path):
        if path not in T29_FILES:
            r = _sp18.run(['git', 'show', f'{T29C}:{path}'], cwd=here, capture_output=True)
            T29_FILES[path] = r.stdout if r.returncode == 0 else None
        return T29_FILES[path]
    check('T-30: the T-29 files can be read from git for comparison', t29_file('studio.html') is not None and t29_file('local.html') is not None)
    SRC30 = {n: un33(un34(urlopen(BASE + n).read().decode('utf-8').replace('\r\n', '\n'), n), n) for n in ALL_HTML}   # T-33: its lines out (its block checks them)
    OLD30 = {n: t29_file(n).decode('utf-8').replace('\r\n', '\n') for n in ALL_HTML}
    ROOT30 = {n: open(os.path.join(here, '..', n), encoding='utf-8').read().replace('\r\n', '\n') for n in ALL_HTML}
    S30, L30, W30 = SRC30['studio.html'], SRC30['local.html'], SRC30['work.html']
    sj30 = _json26.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
    # T-33 R13: Birdsighted's gallery block carries an "id" and _about one more sentence; read without them here (the T-33 block checks them).
    sj30['gallery'] = dict(sj30['gallery'], apps=[{k: v for k, v in x.items() if k != 'id'} for x in sj30['gallery']['apps']])
    sj30['_about'] = sj30['_about'].replace(' A gallery app with an "id" carries it on its block, so another page can link to it (T-33: Work\'s Birdsighted card links studio.html#birdsighted).', '', 1)
    sj29 = _json26.loads(t29_file('_build/studio.json').decode('utf-8'))
    P30 = {x['id']: x for x in sj30['products']}
    WHAT30 = {pid: t30_text(para) for pid, para in T30_STUDIO}                        # the two paragraphs' words
    DESC30 = {href: t30_text(inner) for href, inner in T30_LOCAL}                     # the four tools' descriptions' words
    SIX30 = list(WHAT30.values()) + list(DESC30.values())
    stamp30 = lambda s: _re.sub(STAMP26, '', _re.sub(r'data-built="\d{4}-\d\d-\d\d"', 'data-built=""', s))   # the build day aside, as stamp25/stamp27 (Josef, Nov 19)

    # un30() itself, proved against T-29's own files: it puts the six paragraphs back byte for byte and takes the rule out.
    check('T-30: un30() changes studio.html and local.html (the paragraphs are gone)', un30(S30, 'studio.html') != S30 and un30(L30, 'local.html') != L30)
    check('T-30: un30() gives T-29\'s studio.html byte for byte, the stamp line aside', stamp30(un30(S30, 'studio.html')) == stamp30(OLD30['studio.html']))
    check('T-30: un30() gives T-29\'s local.html byte for byte', un30(L30, 'local.html') == OLD30['local.html'])
    check('T-30: un30() leaves T-29\'s own files as they are (it only puts back what is missing)',
          un30(OLD30['studio.html'], 'studio.html') == OLD30['studio.html'] and un30(OLD30['local.html'], 'local.html') == OLD30['local.html'])
    check('T-30: un30() leaves every other page alone', all(un30(SRC30[n], n) == SRC30[n] for n in ALL_HTML if n not in ('studio.html', 'local.html')))
    check('T-30: the six paragraphs in un30() are T-29\'s, word for word: on T-29\'s studio.html, local.html and work.html',
          all(para in OLD30['studio.html'] for _p, para in T30_STUDIO) and all(T30_LOCAL_P + inner + '</p>' in OLD30['local.html'] for _h, inner in T30_LOCAL)
          and all(para in OLD30['work.html'] for _p, para in T30_STUDIO) and all(f'<p>{inner}</p>' in OLD30['work.html'] for _h, inner in T30_LOCAL))

    # The whole build: studio.html and local.html are T-29's minus the paragraphs (studio: plus the rule, stamp aside);
    # the product pages differ only by the stamp line; every other page and public file byte for byte as at T-29.
    for n in ALL_HTML:
        if n == 'studio.html':
            a, b_ = stamp30(un30(S30, n)), stamp30(OLD30[n])
            check('T-30: studio.html is T-29\'s page with only the two "what" lines out and the 34em rule in, the stamp line aside', a == b_,
                  next((f'...{a[max(0, i - 60):i + 60]}... | ...{b_[max(0, i - 60):i + 60]}...' for i in range(min(len(a), len(b_))) if a[i] != b_[i]), f'{len(a)} vs {len(b_)}'))
        elif n == 'local.html':
            check('T-30: local.html is T-29\'s page with only the four tool descriptions out', un30(L30, n) == OLD30[n])
        elif n.startswith('studio-'):
            dl = [(x, y) for x, y in zip(SRC30[n].split('\n'), OLD30[n].split('\n')) if x != y]
            check(f'T-30: {n} is T-29\'s page apart from studio.py\'s stamp line (studio.json\'s hash)', SRC30[n].count('\n') == OLD30[n].count('\n')
                  and all(_re.fullmatch(STAMP26, x) and _re.fullmatch(STAMP26, y) for x, y in dl), str(dl[:2]))
        else:
            check(f'T-30: {n} is byte for byte as at T-29', SRC30[n] == OLD30[n])
    check('T-30: the pages that changed are studio.html and local.html (and the product pages\' stamp line)',
          sorted(n for n in ALL_HTML if SRC30[n] != OLD30[n] and not n.startswith('studio-')) == ['local.html', 'studio.html'])
    check('T-30: every root page is the built page', not t32_root_off(ALL_HTML), str(t32_root_off(ALL_HTML)))   # T-32: the themed build
    t29tree = [f for f in _sp18.run(['git', 'ls-tree', '-r', '--full-tree', '--name-only', T29C], cwd=here, capture_output=True, text=True).stdout.split('\n') if f]
    pub29 = [f for f in t29tree if not f.startswith('_build/') and not f.endswith('.html')]
    check('T-30: every other public file at the root (sitemap, robots, images, gallery, shelf, share cards) is byte for byte as at T-29',
          len(pub29) >= 52 and all(rb26(f) == t29_file(f).replace(b'\r\n', b'\n') for f in pub29), str([f for f in pub29 if rb26(f) != t29_file(f).replace(b'\r\n', b'\n')][:5]))
    outf30 = sorted(os.path.relpath(os.path.join(d, f), outd).replace(os.sep, '/') for d, _x, fs in os.walk(outd) for f in fs)
    check('T-30: the build adds no file (everything in out/ was at the root at T-29)', len(outf30) >= 60 and [f for f in outf30 if f not in set(t29tree)] == [],
          str([f for f in outf30 if f not in set(t29tree)][:5]))
    for n in ALL_HTML:
        for what, rx in (('title', r'<title>.*?</title>'), ('meta description', r'<meta name="description"[^>]*>'),
                         ('share card tags', r'<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>'), ('h1', r'<h1[^>]*>.*?</h1>'),
                         ('structured data', r'<script type="application/ld\+json">.*?</script>'), ('scripts', r'<script>.*?</script>'),
                         ('alt texts', r'\balt="[^"]*"'), ('aria-labels', r'\baria-label="[^"]*"'), ('labels', r'<label\b[^>]*>.*?</label>')):
            check(f'T-30: {n} keeps its {what}', sorted(_re.findall(rx, SRC30[n], _re.S)) == sorted(_re.findall(rx, OLD30[n], _re.S)))
    check('T-30: no em dash on studio.html, local.html or work.html, and no new en dash',
          all('—' not in SRC30[n] and SRC30[n].count('–') == OLD30[n].count('–') for n in ('studio.html', 'local.html', 'work.html')))

    # Where each paragraph lives now: work.html once, studio.html and local.html never (source and markup).
    for pid, para in T30_STUDIO:
        check(f'T-30: the {pid} paragraph is on work.html exactly once and on studio.html zero times',
              W30.count(para) == 1 and WHAT30[pid] not in S30 and WHAT30[pid] not in _html.unescape(S30), str([W30.count(para), S30.count(WHAT30[pid])]))
    for href, inner in T30_LOCAL:
        check(f'T-30: the {href} description is on work.html exactly once and on local.html zero times',
              W30.count(f'<p>{inner}</p>') == 1 and inner not in L30 and DESC30[href] not in _re.sub(r'<[^>]+>', '', L30), str([W30.count(f'<p>{inner}</p>'), L30.count(inner)]))
    for pid, nm in (('kids', "A kids' cooking app"), ('cobol', 'COBOL, checked in public')):
        card = _re.search(r'<article class="prod[^"]*" data-id="' + pid + r'">.*?</article>', S30, _re.S).group(0)
        sents = [x.strip() for x in _re.split(r'(?<=\.)\s+', WHAT30[pid]) if x.strip()]
        check(f'T-30: the {pid} card holds none of its "what" sentences', len(sents) >= 2 and not any(x in card for x in sents), str(sents))
        want = ([f'<h2>{nm}</h2>', f'<div class="meta"><span class="pill">{P30[pid]["status"]}</span></div>']
                + ([f'<p class="proof"><strong>{P30[pid]["proof"]}</strong></p>'] if P30[pid].get('proof') else [])
                + ['<div class="acts">'])
        kids_ = _re.findall(r'\n        (<[^\n]*)', card)
        check(f'T-30: the {pid} card reads name, pill,{" proof," if P30[pid].get("proof") else ""} link, in that order, and nothing else',
              [k if not k.startswith('<div class="acts">') else '<div class="acts">' for k in kids_] == want and card.count('<p') == (1 if P30[pid].get('proof') else 0), str(kids_))
    check('T-30: the kids\' card keeps "Built for a client", its bold proof line and "See the work →"',
          '<span class="pill">Built for a client</span>' in S30 and '<p class="proof"><strong>535 tests, and every change checked on a real phone before it ships.</strong></p>' in S30
          and '<a class="go" href="work.html">See the work →</a>' in S30)
    check('T-30: the COBOL card keeps "Public" and "Open the repo ↗"', '<span class="pill">Public</span>' in S30
          and '<a class="go" href="https://github.com/stephensjosef-cloud/cobol-behavioral-equivalence">Open the repo ↗</a>' in S30)
    TOOLS30_RX = r'<article style="[^"]*">\s*<h3 style="[^"]*">([^<]*)</h3>\s*(<p [^>]*>.*?</p>\s*)?<a href="([^"]*)" style="[^"]*">([^<]*)</a>\s*</article>'
    sec30 = lambda s: _re.search(r'<section id="tools".*?</section>', s, _re.S).group(0)
    t30, t29_ = _re.findall(TOOLS30_RX, sec30(L30), _re.S), _re.findall(TOOLS30_RX, sec30(OLD30['local.html']), _re.S)
    check('T-30: local\'s tools section holds the same tools in the same order, with the same names, hrefs and link words as at T-29',
          [(h, a_, g) for h, _p, a_, g in t30] == [(h, a_, g) for h, _p, a_, g in t29_] and len(t30) == 4
          and [g for _h, _p, _a, g in t30] == ['Plan your reel →', 'Fit a caption →', 'Ring it up →', 'Scale a recipe →'], str([t30, t29_]))
    check('T-30: local\'s tool cards have no description paragraph (each card is its name and its link)',
          all(_p == '' for _h, _p, _a, _g in t30) and '<p' not in sec30(L30) and sec30(L30).count('<article') == 4)
    WCARDS30 = {m[1]: (m[0], m[2]) for m in _re.findall(r'<h2>([^<]*)</h2>\s*<p>.*?</p>\s*<a class="go" href="([^"]*)">([^<]*)</a>', W30, _re.S)}
    check('T-30: each tool\'s name and link words on local.html are the work page card\'s (read from it)',
          all(WCARDS30.get(a_) == (h, g) for h, _p, a_, g in t30), str([(h, a_, g, WCARDS30.get(a_)) for h, _p, a_, g in t30]))
    check('T-30: the work page\'s free-tool cards are as at T-29, descriptions and all',
          _re.findall(r'<article class="card" data-k="free[^"]*">.*?</article>', W30, _re.S) == _re.findall(r'<article class="card" data-k="free[^"]*">.*?</article>', OLD30['work.html'], _re.S))

    # studio.json, studio.py, enhance.py: the two "what" lines are null, _about says what that means, nothing else changed.
    check('T-30: what29() gives kids\' and COBOL\'s "what" exactly as in T-29\'s studio.json, and every other product\'s as it is',
          all(what29(P30[x['id']]) == x['what'] for x in sj29['products']) and what29(dict(id='kids', what='x')) == 'x')
    check('T-30: studio.json\'s kids and cobol products have "what": null', P30['kids'].get('what', 0) is None and P30['cobol'].get('what', 0) is None)
    check('T-30: studio.json is T-29\'s apart from those two "what" lines and one sentence in _about',
          {k: v for k, v in sj30.items() if k != 'products' and k != '_about'} == {k: v for k, v in sj29.items() if k != 'products' and k != '_about'}
          and [dict(x, what=None) if x['id'] in ('kids', 'cobol') else x for x in sj29['products']] == sj30['products']
          and sj30['_about'] == sj29['_about'] + ' A product whose "what" is null shows no description line, because its description lives on the Work page.')
    import importlib.util as _ilu30
    _spec30 = _ilu30.spec_from_file_location('studio30', os.path.join(here, 'tools', 'studio.py'))
    _st30 = _ilu30.module_from_spec(_spec30); _spec30.loader.exec_module(_st30)
    _card30 = _st30.product_card(dict(P30['kids']))
    check('T-30: studio.py\'s product_card() prints no line for a null "what" and still prints one when it is set',
          '<p>' not in _card30.replace('<p class="proof">', '') and '<p>Some words.</p>' in _st30.product_card(dict(P30['kids'], what='Some words.')), _card30)
    spy30 = open(os.path.join(here, 'tools', 'studio.py'), encoding='utf-8').read()
    check('T-30: the 34em rule is in studio.py\'s WIDE_CSS, on studio.html only', '.prod.wide>p:not(.proof){max-width:34em}' in getattr(_st30, 'WIDE_CSS', '')
          and S30.count('.prod.wide>p:not(.proof){max-width:34em}') == 1 and not any('max-width:34em}' in SRC30[n] and '.prod.wide>p' in SRC30[n] for n in ALL_HTML if n != 'studio.html'))
    enh30 = open(os.path.join(here, 'enhance.py'), encoding='utf-8').read()
    tc30 = enh30[enh30.index('def tool_cards():'):enh30.index('def add_free_tools():')]
    check('T-30: enhance.py\'s tool_cards() still reads each name and link from work.html and prints no paragraph',
          '(OUT / "work.html")' in tc30 and '<p ' not in tc30.split('cards.append', 1)[1] and 'h, go = m[0].groups()' in tc30)
    check('T-30: neither studio.py nor enhance.py holds any of the six paragraphs\' words', not any(x[:40] in spy30 or x[:40] in enh30 for x in SIX30))

    # The browser: T-29's own pages are served from git at BASE + '__t29/', next to this build.
    T29URL = BASE + '__t29/'

    def serve_t29(route):
        path = route.request.url.split('/__t29/', 1)[1].split('?')[0].split('#')[0]
        body = t29_file(path)
        if body is None:
            return route.fulfill(status=404, body=b'')
        ct = ('text/html; charset=utf-8' if path.endswith('.html') else 'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg')
              else 'image/png' if path.endswith('.png') else 'application/octet-stream')
        route.fulfill(status=200, body=body, content_type=ct)

    def page30(url, w):
        q = newpage(w); q.route('**/__t29/**', serve_t29)
        q.goto(url, wait_until='networkidle'); q.evaluate('document.fonts.ready.then(() => 1)'); q.wait_for_timeout(300)
        return q
    LINES30_JS = r'''() => document.querySelector('main').innerText.split('\n').map(x => x.replace(/\s+/g, ' ').trim()).filter(Boolean)'''
    PS30_JS = r'''() => [...document.querySelectorAll('main p')].map(p => p.innerText.replace(/\s+/g, ' ').trim())'''
    from collections import Counter as _C30
    for n in ('studio.html', 'local.html'):
        for w in (390, 1440):
            q, o = page30(UN33 + n, w), page30(T29URL + n, w)   # T-33: its lines out (__un33/)
            L, L29 = q.evaluate(LINES30_JS), o.evaluate(LINES30_JS)
            Pn, P29_ = q.evaluate(PS30_JS), o.evaluate(PS30_JS)
            q.close(); o.close()
            gone = _C30(x for x in SIX30 if x in P29_)
            want_gone = _C30(WHAT30.values()) if n == 'studio.html' else _C30(DESC30.values())
            check(f'T-30: at {w}, {n} as served from git at T-29 shows its paragraphs (the check reads what it should)', gone == want_gone, str(gone))
            check(f'T-30: at {w}, {n}\'s visible text is T-29\'s minus exactly those paragraphs: nothing else gone, nothing new',
                  _C30(L) == _C30(L29) - want_gone and (_C30(L29) - _C30(L)) == want_gone and not (_C30(L) - _C30(L29)),
                  str([(_C30(L29) - _C30(L)) - want_gone, _C30(L) - _C30(L29)]))
            check(f'T-30: at {w}, {n}\'s paragraphs are T-29\'s minus those, in the same order', Pn == [x for x in P29_ if x not in want_gone], str(len(Pn)))

    # Layout at 320, 390 and 1440: no sideways scroll; the two cards read name, pill, (proof), link; Free tools' paragraph at
    # most 34em; the tool cards are name then link, with 44 px links; at 1440 kids and COBOL side by side, links level.
    GRID30_JS = r'''() => { const R = e => e.getBoundingClientRect();
      const card = id => { const a = document.querySelector(`#products > article[data-id="${id}"]`), c = R(a);
        return {box: [c.left, c.top, c.width, c.height], kids: [...a.children].map(e => e.tagName + (e.className ? '.' + e.className : '')),
          link: (l => [R(l).left, R(l).top, R(l).bottom, R(l).height])(a.querySelector('a.go')),
          ps: [...a.querySelectorAll(':scope > p')].map(p => { const g = document.createRange(); g.selectNodeContents(p); const t = g.getBoundingClientRect();
            return [p.className, R(p).width / parseFloat(getComputedStyle(p).fontSize), Math.round(R(p).top - c.top), Math.round(R(p).height), Math.round(t.width), Math.round(t.left - c.left)]; }),
          shelf: [...a.querySelectorAll('.shelf li, .shelf img, a.go')].map(e => [e.tagName, Math.round(R(e).left - c.left), Math.round(R(e).top - c.top), Math.round(R(e).width), Math.round(R(e).height)])}; };
      return {kids: card('kids'), cobol: card('cobol'), tools: card('tools'), chucklefits: card('chucklefits'),
        sw: [document.documentElement.scrollWidth, innerWidth]}; }'''
    TOOLSEC30_JS = r'''() => { const R = e => e.getBoundingClientRect(), s = document.getElementById('tools');
      return {cards: [...s.querySelectorAll('article')].map(a => ({kids: [...a.children].map(e => e.tagName), name: a.querySelector('h3').textContent,
        link: (l => [l.getAttribute('href'), l.textContent, R(l).height, R(l).top, R(l).bottom])(a.querySelector('a')), h3: (h => [R(h).top, R(h).bottom])(a.querySelector('h3')),
        box: [R(a).left, R(a).top, R(a).right, R(a).bottom]})), sw: [document.documentElement.scrollWidth, innerWidth]}; }'''
    for w in (320, 390, 1440):
        q, o = page30(BASE + 'studio.html', w), page30(T29URL + 'studio.html', w)
        G, G29 = q.evaluate(GRID30_JS), o.evaluate(GRID30_JS)
        q.locator('#products').screenshot(path=f'{SHOTS}/t30-studio-products-{w}.png')
        o.close()
        check(f'T-30: at {w}, studio.html has no sideways scroll', G['sw'][0] <= G['sw'][1], str(G['sw']))
        check(f'T-30: at {w}, the kids\' card reads name, pill, proof line, link', G['kids']['kids'] == ['H2', 'DIV.meta', 'P.proof', 'DIV.acts'], str(G['kids']['kids']))
        check(f'T-30: at {w}, the COBOL card reads name, pill, link', G['cobol']['kids'] == ['H2', 'DIV.meta', 'DIV.acts'], str(G['cobol']['kids']))
        for pid in ('kids', 'cobol'):
            check(f'T-30: at {w}, the {pid} card\'s link keeps its 44 px tap height', G[pid]['link'][3] >= 44, str(G[pid]['link']))
            check(f'T-30: at {w}, the {pid} card is as wide as at T-29', abs(G[pid]['box'][2] - G29[pid]['box'][2]) < 0.5, str([G[pid]['box'], G29[pid]['box']]))
        tp = G['tools']['ps']
        check(f'T-30: at {w}, Free tools\' paragraph is at most 34em wide', len(tp) == 1 and tp[0][1] <= 34.01, str(tp))
        check(f'T-30: at {w}, Free tools spans the same width as at T-29', abs(G['tools']['box'][2] - G29['tools']['box'][2]) < 0.5, str([G['tools']['box'], G29['tools']['box']]))
        cf, cf29 = G['chucklefits'], G29['chucklefits']
        check(f'T-30: at {w}, the ChuckleFits card, its line (where its words sit) and its shelf lay out as at T-29',
              cf['box'][2:] == cf29['box'][2:] and [x[2:] for x in cf['ps']] == [x[2:] for x in cf29['ps']] and cf['shelf'] == cf29['shelf'] and len(cf['shelf']) >= 13,
              str([cf['box'], cf29['box'], cf['ps'], cf29['ps']]))
        for pid in ('kids', 'cobol'):
            check(f'T-30: at {w}, the {pid} card holds no paragraph but its proof line', [x[0] for x in G[pid]['ps']] == (['proof'] if pid == 'kids' else []), str(G[pid]['ps']))
        if w == 1440:
            check('T-30: at 1440, Free tools\' paragraph is narrower than at T-29 (it was one long line) and wraps at its 34em measure',
                  G29['tools']['ps'][0][1] > 34.01 and abs(tp[0][1] - 34) < 0.5, str([tp, G29['tools']['ps']]))
            k, c = G['kids'], G['cobol']
            check('T-30: at 1440, the kids\' and COBOL cards sit side by side, same top, same height', abs(k['box'][1] - c['box'][1]) < 0.5 and c['box'][0] > k['box'][0] + k['box'][2] - 1
                  and abs(k['box'][3] - c['box'][3]) < 0.5, str([k['box'], c['box']]))
            check('T-30: at 1440, their links line up at the bottom', abs(k['link'][2] - c['link'][2]) < 0.5, str([k['link'], c['link']]))
        q.close()
        q = page30(UN33 + 'local.html', w)   # T-33: its lines out (__un33/): R20 and R21 change these cards; the T-33 block checks them
        T = q.evaluate(TOOLSEC30_JS)
        q.locator('#tools').screenshot(path=f'{SHOTS}/t30-local-tools-{w}.png')
        q.close()
        check(f'T-30: at {w}, local.html has no sideways scroll', T['sw'][0] <= T['sw'][1], str(T['sw']))
        check(f'T-30: at {w}, each tool card is its name, then its link', len(T['cards']) == 4 and all(x['kids'] == ['H3', 'A'] and x['link'][3] >= x['h3'][1] for x in T['cards']), str([x['kids'] for x in T['cards']]))
        check(f'T-30: at {w}, each tool card\'s link keeps its 44 px tap height and sits inside its card', all(x['link'][2] >= 44 and x['link'][4] <= x['box'][3] + 0.5 for x in T['cards']),
              str([x['link'] for x in T['cards']]))
        check(f'T-30: at {w}, the tool cards\' names and links read as at T-29', [(x['name'], x['link'][0], x['link'][1]) for x in T['cards']]
              == [(h, a_, g) for h, _p, a_, g in t29_], str([(x['name'], x['link'][0]) for x in T['cards']]))


# ---------------- T-32 (Nov 20, 2026): the chart style, a themed copy of every page in out-themed/ ----------------
# theme.py (step 6c) writes _build/out-themed/ from out/; the root is copied from there. Every older section keeps
# testing out/. This one serves out-themed/ on its own free port and checks that only styles differ, that every color
# is the new palette's, the type, the ring, the route, the dark footer and call box, no sideways scroll, and axe.
T32_INK = 'rgb(23, 33, 43)'
T32_ACCENT = ('rgb(232, 89, 43)', 'rgb(28, 95, 168)')   # the orange (kept, Josef Nov 19) and the Mainframe pages' blue
T32_MF = ('mainframe.html', 'comp3.html', 'briefing.html')
# The ring: page -> the words of the one element it sits around (T-32's Receipt lists the same).
T32_RINGS = {'local.html': 'Start a Blueprint', 'checkup.html': 'Free 15-minute call'}
# The route: page -> the element each dashed line is drawn on.
T32_ROUTES = {'local.html': ['#route ol', '.t32-rt'], 'mainframe.html': ['.t20-steps'], 'start.html': ['.t32-rt', '.t32-rl']}
T32_AXE_VER = '4.10.3'
T32_AXE_URL = f'https://cdnjs.cloudflare.com/ajax/libs/axe-core/{T32_AXE_VER}/axe.min.js'
# Every color a themed page may hold: the table's new values (the orange accent kept), DESIGN.md's, white and black,
# the role picks and kept status colors listed in T-32's Receipt, and the contour browns.
T32_HEX = {'#17212B', '#2E3A47', '#4F5A63', '#E4ECD8', '#F7F9F3', '#EDF2E6', '#B9C3CC', '#9BAA90', '#3A4654',
           '#A21C8A', '#E58FD3', '#1C5FA8', '#8FB8E8', '#E8592B', '#A93F17', '#F07A4E', '#FFFFFF', '#000000',
           # kept as they are, by role (the Receipt): status signals and the shot list's role tags
           '#2E7D4F', '#D9A520', '#7BD389', '#F9EEDA', '#F8E3DA', '#8A6A12', '#F6C9B5', '#D9E4D2', '#F2DEA8', '#E6DCF0', '#CFE0EE'}
T32_RGBA = {(168, 139, 92, .30), (168, 139, 92, .55), (168, 139, 92, .38), (168, 139, 92, .6), (23, 33, 43, .08), (23, 33, 43, .18),
            (23, 33, 43, .35), (232, 89, 43, .45), (0, 0, 0, .45), (0, 0, 0, .2)}
T32_COLOR = _re.compile(r'(?<![&\w#])#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f\w])|rgba?\([^)]*\)|(?<![\w-])(?:white|black)(?![\w-])', _re.I)


def t32_norm(c):
    c = c.strip()
    if c.lower().startswith('rgb'):
        v = [float(x) for x in _re.findall(r'[\d.]+', c)]
        return tuple(v[:3] + [v[3] if len(v) > 3 else 1.0])
    if c.startswith('#'):
        h = c[1:].upper()
        return '#' + (''.join(ch * 2 for ch in h) if len(h) == 3 else h)
    return {'WHITE': '#FFFFFF', 'BLACK': '#000000'}[c.upper()]


def t32_colors(src):
    """Every color in a style attribute, a <style> element or an SVG paint attribute, as (where, token)."""
    out = []
    bodies = [('style attribute', m.group(1)) for m in _re.finditer(r'\sstyle="([^"]*)"', src)]
    bodies += [('<style>', m.group(1)) for m in _re.finditer(r'<style\b[^>]*>(.*?)</style>', src, _re.S)]
    for where, body in bodies:
        for d in _re.finditer(r'([A-Za-z-]+)\s*:\s*([^;{}]*)', _re.sub(r'url\([^)]*\)', '', body)):
            out += [(f'{where} {d.group(1)}', c.group(0)) for c in T32_COLOR.finditer(d.group(2))]
    for m in _re.finditer(r'\s(fill|stroke|stop-color)="([^"]*)"', src):
        out += [(f'svg {m.group(1)}', c.group(0)) for c in T32_COLOR.finditer(m.group(2))]
    return out


def t32_allowed(c):
    v = t32_norm(c)
    if isinstance(v, tuple):
        return v[3] == 1.0 and '#%02X%02X%02X' % tuple(int(x) for x in v[:3]) in T32_ALLOWED_HEX() or \
            any(all(abs(a - b) < 1e-6 for a, b in zip(v, r)) for r in T32_RGBA)
    return v in T32_ALLOWED_HEX()


_T32_HEX_ALL = []


def T32_ALLOWED_HEX():
    if not _T32_HEX_ALL:
        design = open(os.path.join(here, 'DESIGN.md'), encoding='utf-8').read()
        _T32_HEX_ALL.append(T32_HEX | {h.upper() for h in _re.findall(r'#[0-9A-Fa-f]{6}\b', design)})
    return _T32_HEX_ALL[0]


def t32_axe():
    """axe-core, pinned, fetched once from cdnjs into the system temp folder (outside the repo) and read from there."""
    path = os.path.join(tempfile.gettempdir(), 'dj-test-axe', f'axe-{T32_AXE_VER}.min.js')
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = urlopen(T32_AXE_URL, timeout=60).read()
        with open(path + '.tmp', 'wb') as f:
            f.write(body)
        os.replace(path + '.tmp', path)
    return open(path, encoding='utf-8').read()


T32_DOM_JS = r'''() => {
  const sp = s => (s || '').replace(/\s+/g, ' ').trim();
  const words = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {acceptNode: n =>
    n.parentElement.closest('script,style,noscript') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  while (tw.nextNode()) { const t = sp(tw.currentNode.nodeValue); if (t) words.push(t); }
  return {text: words.join(' '),
          links: [...document.querySelectorAll('a')].map(a => [a.getAttribute('href'), sp(a.textContent)]),
          imgs: [...document.querySelectorAll('img')].map(i => [i.getAttribute('src'), i.getAttribute('alt')]),
          title: document.title,
          desc: (document.querySelector('meta[name="description"]') || {}).content || null,
          ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => s.textContent)};
}'''

T32_LOOK_JS = r'''([acc]) => {
  const W = innerWidth, H = innerHeight, sp = s => (s || '').replace(/\s+/g, ' ').trim();
  const box = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const vis = e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility != 'hidden'; };
  const TAP = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[tabindex]:not([tabindex="-1"])';
  let first = null;
  for (const e of document.querySelectorAll('a,button,input[type=submit]')) {
    if (!vis(e) || !acc.includes(getComputedStyle(e).backgroundColor)) continue;
    const [l, t, r, b] = box(e);
    if (l >= 0 && t >= 0 && r <= W && b <= H) { first = sp(e.textContent); break; }
  }
  const rings = [...document.querySelectorAll('.t32-ring')].map(g => {
    const host = g.parentElement, [l, t, r, b] = box(g), ov = [];
    for (const e of document.querySelectorAll(TAP)) {
      if (e === host || host.contains(e) || e.contains(host) || !vis(e)) continue;
      const [l2, t2, r2, b2] = box(e);
      if (Math.min(r, r2) - Math.max(l, l2) > 0.5 && Math.min(b, b2) - Math.max(t, t2) > 0.5) ov.push(sp(e.textContent).slice(0, 40) || e.tagName);
    }
    return {host: sp(host.textContent), hidden: g.getAttribute('aria-hidden'), pe: getComputedStyle(g).pointerEvents,
            box: [l + scrollX, t + scrollY, r + scrollX, b + scrollY], over: ov, stroke: getComputedStyle(g.querySelector('path')).stroke,
            sw: g.querySelector('path').getAttribute('stroke-width')};
  });
  const bg = e => getComputedStyle(e).backgroundColor;
  const routes = {};
  for (const sel of %ROUTES%) {
    routes[sel] = [...document.querySelectorAll(sel)].map(e => {
      const b4 = getComputedStyle(e, '::before');
      return {img: b4.backgroundImage, disp: b4.display, w: b4.width, h: b4.height, bt: getComputedStyle(e).borderTopColor};
    });
  }
  return {sw: [document.documentElement.scrollWidth, W], first, rings, routes,
          footers: [...document.querySelectorAll('footer')].map(bg),
          calls: [...document.querySelectorAll('section[aria-labelledby="next-h"],section[aria-labelledby="c7"]')].map(bg),
          pills: [...document.querySelectorAll('.pill,.hero-pill')].map(bg)};
}'''


def t32_dark(c):
    v = [float(x) for x in _re.findall(r'[\d.]+', c)]
    if len(v) < 3 or (len(v) > 3 and v[3] == 0):
        return False
    return (0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]) < 80


@section('T-32')
def s_t_32():
    port = free_port()
    srv = _sp.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', T32_DIR], cwd=here,
                    stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    TB = f'http://127.0.0.1:{port}/'
    try:
        for _i in range(100):
            try:
                urlopen(TB + 'index.html', timeout=2).read()
                break
            except OSError:
                time.sleep(0.1)
        _t32_checks(TB)
    finally:
        srv.kill()
        srv.wait()


def _t32_checks(TB):
    names = sorted(ALL_HTML)
    check('T-32: out-themed/ holds every page out/ holds', all(os.path.exists(os.path.join(T32_DIR, n)) for n in names))
    OUT = {n: t32_read(outd, n) for n in names}
    TH = {n: t32_read(T32_DIR, n) for n in names}

    # The files themselves: every color is the new palette's, the type is Barlow, nothing is uppercased.
    for n in names:
        bad_ = [f'{w}: {c}' for w, c in t32_colors(TH[n]) if not t32_allowed(c)]
        check(f'T-32: {n}: every color in its styles and SVG paint is in the palette', not bad_, str(sorted(set(bad_))[:8]))
        check(f'T-32: {n}: no Big Shoulders Display or Instrument Sans is left', 'Big Shoulders' not in TH[n] and 'Instrument Sans' not in TH[n]
              and 'Big+Shoulders' not in TH[n] and 'Instrument+Sans' not in TH[n])
        links = _re.findall(r'href="(https://fonts\.googleapis\.com/css2\?[^"]*)"', TH[n])
        check(f'T-32: {n}: its font link asks for Barlow and Barlow Semi Condensed', links and all(
            'family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400' in u and 'family=Barlow+Semi+Condensed:wght@600;700;800;900' in u for u in links), str(links))
        check(f'T-32: {n}: no text-transform: uppercase is left', not _re.search(r'text-transform\s*:\s*uppercase', TH[n]))
        check(f'T-32: {n}: at most one ring, aria-hidden, with no pointer events', TH[n].count('class="t32-ring"') <= 1
              and TH[n].count('class="t32-ring"') == TH[n].count('class="t32-ring" aria-hidden="true"'))
        check(f'T-32: {n}: has the ring exactly when the Receipt lists one', (TH[n].count('class="t32-ring"') == 1) == (n in T32_RINGS))
    favicon = open(os.path.join(T32_DIR, 'favicon.svg'), 'rb').read()
    check('T-32: favicon.svg keeps the orange (the accent stays orange)', favicon == open(os.path.join(outd, 'favicon.svg'), 'rb').read() and b'E8592B' in favicon.upper())
    others = sorted(os.path.relpath(os.path.join(d, f), T32_DIR).replace(os.sep, '/') for d, _x, fs in os.walk(T32_DIR) for f in fs if not f.endswith('.html'))
    check('T-32: every other file in out-themed/ is out/\'s, byte for byte', len(others) >= 40 and all(
        open(os.path.join(T32_DIR, f), 'rb').read() == open(os.path.join(outd, f), 'rb').read() for f in others))
    outf32 = sorted(os.path.relpath(os.path.join(d, f), outd).replace(os.sep, '/') for d, _x, fs in os.walk(outd) for f in fs)
    themf32 = sorted(os.path.relpath(os.path.join(d, f), T32_DIR).replace(os.sep, '/') for d, _x, fs in os.walk(T32_DIR) for f in fs)
    check('T-32: out-themed/ holds exactly out/\'s files', outf32 == themf32)

    # The root is the themed build.
    check('T-32: every root page is the themed page', not t32_root_off(names), str(t32_root_off(names)))
    check('T-32: every other file in out-themed/ is at the root, byte for byte', all(rb26(f) == open(os.path.join(T32_DIR, f), 'rb').read().replace(b'\r\n', b'\n') for f in others),
          str([f for f in others if rb26(f) != open(os.path.join(T32_DIR, f), 'rb').read().replace(b'\r\n', b'\n')][:5]))
    check('T-32: _build/DESIGN.md is the vault\'s DESIGN.md (its colors are read here)', '#A21C8A' in open(os.path.join(here, 'DESIGN.md'), encoding='utf-8').read())

    # Only styles differ: the words, links, images, title, description and structured data, as the browser sees them.
    for n in names:
        q = newpage(1440)
        q.goto(BASE + n, wait_until='load')
        a = q.evaluate(T32_DOM_JS)
        q.goto(TB + n, wait_until='load')
        t = q.evaluate(T32_DOM_JS)
        q.close()
        for k, what in (('text', 'visible text'), ('links', 'links (href and words)'), ('imgs', 'images and alts'), ('title', 'title'),
                        ('desc', 'meta description'), ('ld', 'structured data')):
            check(f'T-32: {n}: its {what} is out/\'s', a[k] == t[k],
                  next((f'...{a[k][max(0, i - 50):i + 50]}... | ...{t[k][max(0, i - 50):i + 50]}...' for i in range(min(len(a[k]), len(t[k]))) if a[k][i] != t[k][i]), f'{len(a[k])} vs {len(t[k])}')
                  if isinstance(a[k], str) else str([x for x in zip(a[k] or [], t[k] or []) if x[0] != x[1]][:3]))

    # Looked at in the browser: ring, route, the dark footer and call box, pills, no sideways scroll; axe at 390 and 1440.
    axe = t32_axe()
    darks32 = [0]
    js = T32_LOOK_JS.replace('%ROUTES%', _json.dumps(sorted({s for v in T32_ROUTES.values() for s in v})))
    for n in names:
        q = newpage(1440)
        q.goto(BASE + n, wait_until='load')
        old = q.evaluate(js, [list(T32_ACCENT)])
        q.close()
        darks32[0] += sum(t32_dark(x) for x in old['footers'] + old['calls'])
        for w, h in ((320, 700), (390, 844), (1440, 900)):
            q = newpage(w, h)
            q.goto(TB + n, wait_until='load')
            q.evaluate('document.fonts.ready.then(() => 1)')
            q.wait_for_timeout(300)
            L = q.evaluate(js, [list(T32_ACCENT)])
            check(f'T-32: at {w}, {n} has no sideways scroll', L['sw'][0] <= L['sw'][1], str(L['sw']))
            want = T32_RINGS.get(n)
            if want:
                r = L['rings'][0] if len(L['rings']) == 1 else None
                check(f'T-32: at {w}, {n}: one ring, around "{want}"', r and r['host'] == want, str(L['rings']))
                if r:
                    check(f'T-32: at {w}, {n}: the ring is aria-hidden, takes no taps, 3px, in the accent',
                          r['hidden'] == 'true' and r['pe'] == 'none' and r['sw'] == '3' and r['stroke'] == (T32_ACCENT[1] if n in T32_MF else T32_ACCENT[0]), str(r))
                    check(f'T-32: at {w}, {n}: the ring covers no other tap target', not r['over'], str(r['over']))
                    check(f'T-32: at {w}, {n}: the ring stays inside the page', r['box'][0] >= 0 and r['box'][2] <= w, str(r['box']))
            else:
                check(f'T-32: at {w}, {n}: no ring', not L['rings'], str(L['rings']))
            if h == 844:   # the rule, on a phone's first screen: the first accent-filled button fully in view gets the ring
                check(f'T-32: {n}: the ringed element is its first accent-filled button in its first screen at 390 (none: no ring)', L['first'] == want, str([L['first'], want]))
            check(f'T-32: at {w}, {n}: every footer and closing call box that was dark is ink, and status pills are ink',
                  all(nw == T32_INK for ow, nw in zip(old['footers'] + old['calls'], L['footers'] + L['calls']) if t32_dark(ow))
                  and all(p == T32_INK for p in L['pills']) and len(L['footers']) == len(old['footers']) and len(L['calls']) == len(old['calls']),
                  str([old['footers'], L['footers'], old['calls'], L['calls'], L['pills']]))
            for sel in T32_ROUTES.get(n, []):
                rs = L['routes'][sel]
                dashed = [x for x in rs if x['disp'] != 'none' and 'repeating-linear-gradient' in x['img']]
                check(f'T-32: at {w}, {n}: {sel} carries the dashed route line', rs and (dashed or (n == 'local.html' and sel == '#route ol' and w < 700)), str(rs)[:300])
            if n in T32_ROUTES and '#route ol' in T32_ROUTES[n] or n == 'mainframe.html':
                sel = '#route ol' if n == 'local.html' else '.t20-steps'
                check(f'T-32: at {w}, {n}: the route replaces {sel}\'s solid top border', all(x['bt'] == 'rgba(0, 0, 0, 0)' for x in L['routes'][sel]), str(L['routes'][sel])[:200])
            if w in (390, 1440):
                q.add_script_tag(content=axe)
                # A 1:1 pair (text the color of its background) is "incomplete" (equalRatio) in axe, not a violation: count it too.
                res = q.evaluate('() => axe.run(document, {resultTypes: ["violations", "incomplete"]}).then(r => r.violations.map(v => [v.id, v.nodes.length, v.nodes.slice(0, 3).map(x => x.target.join(" "))])'
                                 '.concat(r.incomplete.filter(v => v.id == "color-contrast").map(v => [v.id + " 1:1", v.nodes.filter(x => (x.any || []).some(c => c.data && c.data.messageKey == "equalRatio")).map(x => x.target.join(" "))]).filter(v => v[1].length)))')
                check(f'T-32: at {w}, {n}: axe-core {T32_AXE_VER}, color contrast included: 0 violations', not res, str(res)[:600])
            q.screenshot(path=f'{SHOTS}/t32-{n[:-5]}-{w}.png', full_page=True)
            q.close()
    check('T-32: the old build had dark footers and call boxes to keep (the check above has something to check)', darks32[0] > 0, str(darks32))


# ---------------- T-33 (Nov 20, 2026): the site says what I do (R2 to R23) ----------------
# Josef's lines, word for word. Served from out-themed/ (the root's build) on its own free port, with origin/main's root
# pages (git, T33_MAIN) served beside it under __m33/, so "nothing else changed" is checked against the live build.
T33_MAIN = '95230a7'   # origin/main when T-33 was cut (T-32 DONE)
T33_PAGES = ('index.html', 'local.html', 'work.html', 'start.html', 'shotlist.html', 'captions.html', 'receipt.html',
             'scaler.html', 'checkup.html', 'studio.html')
T33_TOOL_PAGES = ('shotlist.html', 'captions.html', 'receipt.html', 'scaler.html', 'checkup.html')
T33_R2_OLD = ("For shops and nonprofits around Sonoma County. Maybe it's a phone full of videos you'll never edit. Maybe it's a binder of "
              "lessons, or the one chore that eats every Thursday. Hand it over. You get back finished reels, an app with your name on it, "
              "or a chore that does itself, and you watch it work before you decide to go ahead.")
T33_R2 = ("For shops and nonprofits around Sonoma County. Whatever keeps sliding to the bottom of the list, hand it over. Videos nobody "
          "edits, follow-ups nobody sends, the spreadsheet everyone avoids, the app you keep meaning to make. I build the AI tool that "
          "does it, and you watch it work before you decide to go ahead.")
T33_R3_OLD = ("I'm Josef. Hand me the work you never get to, like the phone videos nobody has time to edit or the lessons sitting in a "
              "binder. I'll build the AI tool that handles it and walk you through it in plain English. Nothing reaches your customers "
              "until a person has checked it.")
T33_R3 = ("I'm Josef. Hand me the work you never get to. If someone on your team does it by hand every week, I can usually build an "
          "AI tool that does it instead, and I'll walk you through it in plain English. Nothing reaches your customers until a person "
          "has checked it.")
T33_R4_ROWS = [('A 40-reel series for a nonprofit', '~4 min a reel'), ('A teaching app, iPhone, iPad, Android and web', '535 tests'),
               ('A birding league with real players', 'zero lines of code to start'),
               ('A banking COBOL program, checked in public', '2 AIs compared')]
T33_R4_OLD = ("REAL RESULT KIDS' COOKING REELS A 40-reel series for a children's nonprofit, cut by one engine. Editing each reel, before "
              "An evening Now ~4 min Reels in the series 40 Posted without their yes 0 Client: a Sonoma County children's nonprofit")
T33_R4 = 'REAL RESULTS BUILT WITH AI ' + ' '.join(k + ' ' + v for k, v in T33_R4_ROWS)
T33_R5_OLD = ['Phone videos nobody has time to edit', 'Lessons, recipes or a curriculum', 'A weekly task that eats hours',
              'Not sure yet. Point me somewhere.']
T33_R5 = ['Videos or photos nobody has time to edit', "Know-how stuck in binders, docs or one person's head", 'A weekly task that eats hours',
          'An app or tool you keep wishing existed', 'Not sure yet. Point me somewhere.']
T33_R5_NEWVAL = 'An app or tool you keep wishing existed'   # what the new fourth choice sends
T33_R6 = ('Three ready to go', "These three already run on real projects, so they're quick, and you don't pay me to start from scratch. "
          "If yours is something else, that starts with a Blueprint too.")
T33_R6_OLD = ('Three things I make', "Each one is already built and working on real projects, so you get finished work quickly and you "
              "don't pay me to start from scratch.")
T33_R7, T33_R7_OLD = 'Your videos, finished every month', 'Reels from your phone videos'
T33_R8 = ('Your know-how, in an app', 'What you teach or sell, in an app with your name on it.',
          'What you already teach or sell: lessons, recipes, guides, a product list, a resource library.')
T33_R8_OLD = ('Your own app', 'Your lessons or recipes, in an app with your name on it.',
              'The content you already teach: lessons, recipes, activities, a resource library.')
T33_R9 = ('Something else', 'Not on this list? Tell me anyway. The Blueprint works the same for any job: I watch how it gets done, build '
          'a sample from your material, and give you a fixed price before any building starts.', 'Priced in the Blueprint')
T33_R10, T33_R10_OLD = 'You care more about what it brings in than how it looks in a demo.', 'You care more about inquiries than about views.'
T33_R11_TABS = ['All', 'Apps', 'Video', 'Mainframe', 'Free tools']
T33_R11_OLD_TABS = ['All', 'Nonprofits', 'Banking', 'My own builds', 'Free tools']
# Work's cards by their headings, in R12's order, with their tags.
T33_CARDS = [('A 40-reel series on one engine.', ['Client', 'Reels']),
             ('Bird League', ['My own build', 'App']),
             ('A seasonal cooking app for teachers', ['Client', 'App', 'In progress']),
             ('Birdsighted', ['My own build', 'Game']),
             ('A banking program, checked in public', ['My own build', 'COBOL', 'Public']),
             ('Busywork receipt', ['Free tool', 'Busywork']),
             ('COBOL field decoder', ['Free tool', 'COBOL']),
             ('Reel shot list', ['Free tool', 'Reels']),
             ('Caption fitter', ['Free tool', 'Reels'])]
T33_TABS_SHOW = {'All': [c for c, _t in T33_CARDS],
                 'Apps': ['Bird League', 'A seasonal cooking app for teachers', 'Birdsighted'],
                 'Video': ['A 40-reel series on one engine.'],
                 'Mainframe': ['A banking program, checked in public', 'COBOL field decoder'],
                 'Free tools': ['Busywork receipt', 'COBOL field decoder', 'Reel shot list', 'Caption fitter']}
T33_R13 = ('Birdsighted', 'A detective game for birders. Twelve cases, each one a bird you work out from the clues.', 'See it on Studio →',
           'studio.html#birdsighted')
T33_R14_KEEP = ("I taught myself to build software with AI. Bird League, a competitive birding app, went from zero lines of code to real "
                "users and an App Store submission.")
T33_R14 = "This year a Sonoma County children's nonprofit became my first client. On my own time I've built a birding league, an indie game matchmaker and a detective game for birders."
T33_R14_OLD = "This year a Sonoma County children's nonprofit became my first client, and the tools I built for them are the ones on this page."
T33_GROUP = ('From my reel engine', 'The same rules my reel engine runs on.')
T33_LOCAL_TOOLS = ['Busywork receipt', 'Reel shot list', 'Caption fitter']               # R20, local.html
T33_WORK_TOOLS = ['Busywork receipt', 'COBOL field decoder', 'Reel shot list', 'Caption fitter']   # R20, work.html
T33_ROW_ORDER = ['Busywork receipt', 'Reel shot list', 'Caption fitter']   # R20, each tool page's "More free tools:" row
T33_ROW_OLD = ['Reel shot list', 'Caption fitter', 'Busywork receipt', 'Recipe scaler']
T33_TOOL_NAME = {'shotlist.html': 'Reel shot list', 'captions.html': 'Caption fitter', 'receipt.html': 'Busywork receipt',
                 'scaler.html': 'Recipe scaler', 'checkup.html': 'Website checkup'}
T33_R21 = ('Try its recipe scaler →', 'scaler.html')
T33_R23 = 'A sentence or two is plenty. Something like "every Friday someone spends three hours copying orders into a spreadsheet."'
T33_R23_OLD = 'A sentence or two is plenty. Something like "we film every class and post maybe one clip a month."'
# Old words that must be gone from every page's visible text (whitespace aside). A regex where a new line holds the old one.
T33_GONE = [T33_R2_OLD, T33_R3_OLD, "KIDS' COOKING REELS", 'Client: a Sonoma County', "A 40-reel series for a children's nonprofit, cut by one engine.",
            'Posted without their yes', T33_R5_OLD[0], T33_R5_OLD[1], *T33_R6_OLD, T33_R7_OLD, *T33_R8_OLD, T33_R10_OLD, 'My own builds',
            T33_R14_OLD, 'the tools I built for them', T33_R23_OLD, 'we film every class', 'Scale a recipe →']
T33_GONE_RX = [r'REALRESULT(?!S)']
T33_NORM = r'''(e) => (e.textContent || '').replace(/[\s ]+/g, ' ').trim()'''
T33_LOOK_JS = r'''() => {
  const n = e => (e.textContent || '').replace(/[\s ]+/g, ' ').trim(), box = e => e.getBoundingClientRect();
  const vis = e => { const r = box(e); return r.width > 0 && r.height > 0; };
  const out = {sw: [document.documentElement.scrollWidth, innerWidth]};
  const tear = document.querySelector('.tear');
  if (tear) {
    const kids = [...tear.children], rows = kids[1] ? [...kids[1].children] : [], tb = box(tear);
    out.card = {kids: kids.length, head: kids[0] ? [...kids[0].children].map(e => [n(e), Math.round(box(e).left), Math.round(box(e).top)]) : [],
      rows: rows.filter(r => r.querySelector('span') && r.querySelector('strong')).map(r => { const s = r.querySelector('span'), g = r.querySelector('strong'), gb = box(g);
        return [n(s), n(g), getComputedStyle(s).fontSize, getComputedStyle(g).fontSize, gb.right <= tb.right - 20 + 0.5 && gb.left >= tb.left + 20 - 0.5,
                g.scrollWidth <= g.clientWidth + 1, getComputedStyle(g).whiteSpace]; }),
      size: [Math.round(tb.width)], p: tear.querySelectorAll('p').length};
    const offers = [...document.querySelectorAll('#engines article')];
    out.offers = offers.map(a => ({h: n(a.querySelector('h3')), card: a.getAttribute('data-card'), cls: a.className, style: a.getAttribute('style'),
      ps: [...a.querySelectorAll(':scope > p')].map(n), dl: a.querySelectorAll('dl').length,
      x: Math.round(box(a).left), y: Math.round(box(a).top), w: Math.round(box(a).width), h3y: Math.round(box(a.querySelector('h3')).top - box(a).top),
      price: (() => { const p = [...a.querySelectorAll(':scope > p')].pop(); const c = getComputedStyle(p);
        return [c.fontFamily, c.fontSize, c.borderTopStyle, c.borderTopWidth, c.paddingTop, getComputedStyle(p.querySelector('strong') || p).fontWeight]; })()}));
    const t = document.getElementById('tools');
    out.tools = t ? {h3: [...t.querySelectorAll('article h3')].map(n), links: [...t.querySelectorAll('article a')].map(a => [a.getAttribute('href'), n(a)]),
      group: [...t.querySelectorAll('[role=group]')].map(g => ({label: n(document.getElementById(g.getAttribute('aria-labelledby'))),
        ps: [...g.querySelectorAll(':scope > p')].map(n), h3: [...g.querySelectorAll('article h3')].map(n)})),
      boxes: [...t.querySelectorAll('article')].map(a => [Math.round(box(a).left), Math.round(box(a).bottom), Math.round(box(a).right)])} : null;
  }
  const more = [...document.querySelectorAll('p.noprint')].find(p => n(p).startsWith('More free tools:'));
  if (more) out.more = {text: n(more), links: [...more.querySelectorAll('a')].map(a => [a.getAttribute('href'), n(a)])};
  return out;
}'''
T33_WORK_JS = r'''() => {
  const n = e => (e.textContent || '').replace(/[\s ]+/g, ' ').trim();
  const card = c => ({h: n(c.querySelector('h2')), tags: [...c.querySelectorAll('.tag')].map(n), hidden: c.hidden || !!c.closest('[hidden]'),
    links: [...c.querySelectorAll('a')].map(a => [a.getAttribute('href'), n(a)]), text: n(c)});
  const cl = document.body.cloneNode(true); cl.querySelectorAll('script, style, #cards').forEach(e => e.remove());
  return {tabs: [...document.querySelectorAll('.filt')].map(b => [n(b), b.getAttribute('data-f')]),
    cards: [...document.querySelectorAll('#cards .card')].map(card),
    groups: [...document.querySelectorAll('#cards .cardgroup')].map(g => ({hidden: g.hidden, label: n(g.querySelector('.glabel')), line: n(g.querySelector('.gline')),
      cards: [...g.querySelectorAll('.card h2')].map(n), labelled: g.getAttribute('aria-labelledby')})),
    outside: n(cl), sw: [document.documentElement.scrollWidth, innerWidth]};
}'''


from urllib.parse import quote as _quote33


def t33_ws(s):
    return _re.sub(r'\s+', '', s)


def t33_main(name):
    """A root file as origin/main has it (T33_MAIN), read from git."""
    return _sp.run(['git', 'show', f'{T33_MAIN}:{name}'], cwd=os.path.join(here, '..'), capture_output=True, check=True).stdout


def t33_more(page, order):
    names = [x for x in order if x != T33_TOOL_NAME[page]]
    return 'More free tools: ' + ' · '.join(names)


@section('T-33')
def s_t_33():
    port = free_port()
    srv = _sp.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', T32_DIR], cwd=here,
                    stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    TB = f'http://127.0.0.1:{port}/'
    try:
        for _i in range(100):
            try:
                urlopen(TB + 'index.html', timeout=2).read()
                break
            except OSError:
                time.sleep(0.1)
        _t33_checks(TB)
    finally:
        srv.kill()
        srv.wait()


def _t33_checks(TB):
    MB = TB + '__m33/'
    mains = {}

    def serve_main(route):
        path = route.request.url.split('/__m33/', 1)[1].split('?')[0].split('#')[0]
        if path.endswith('.html'):
            if path not in mains:
                mains[path] = t33_main(path)
            return route.fulfill(status=200, body=mains[path], content_type='text/html; charset=utf-8')
        return route.continue_(url=TB + path)

    def page33(w, h=900):
        q = newpage(w, h)
        q.route('**/__m33/**', serve_main)
        q.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
        return q

    def load(q, url):
        q.goto(url, wait_until='load')
        q.evaluate('document.fonts.ready.then(() => 1)')
        q.wait_for_timeout(150)

    # ---- The files: the root is this build.
    names = sorted(ALL_HTML)
    check('T-33: every root page is the themed page (this build)', not t32_root_off(names), str(t32_root_off(names)))
    # un33() (the older checks read pages through it): each page of out/ through un33(), themed by theme.py, is
    # origin/main's root page byte for byte (the studio pages' build day and studio.json's hash aside, as stamp27()).
    import theme as _theme33
    for n in names:
        new = un34(t32_read(outd, n), n)   # T-34: T-33's own page (the T-34 block checks un34())
        u = un33(new, n)
        check(f'T-33: un33() takes T-33 out of {n}: through theme.py it is origin/main\'s root page byte for byte',
              stamp27(_theme33.theme_page(u, n)) == stamp27(t33_main(n).decode('utf-8').replace('\r\n', '\n')))
        check(f'T-33: un33() changes {n} exactly when T-33 changed it, and a second pass changes nothing',
              (u != new) == (n in T33_UNDO) and un33(u, n) == u)
    TH = {n: t32_read(T32_DIR, n) for n in names}
    for n in names:
        old = t33_main(n).decode('utf-8')
        check(f'T-33: {n}: no em dash added', TH[n].count('—') <= old.count('—'), f'{old.count(chr(0x2014))} -> {TH[n].count(chr(0x2014))}')
    for line in [T33_R2, T33_R3, T33_R4, *T33_R5, *T33_R6, T33_R7, *T33_R8, *T33_R9, T33_R10, *T33_R11_TABS, *T33_R13, T33_R14,
                 *T33_GROUP, T33_R21[0], T33_R23]:
        check(f'T-33: no em dash in the line "{line[:40]}"', '—' not in line)
    check('T-33 R21: scaler.html is still in the sitemap', '<loc>https://dragomansjourney.com/scaler.html</loc>' in t32_read(T32_DIR, 'sitemap.xml'))
    check('T-33 R5: the intake Worker takes the pile as free text, with no list of values (unchanged)',
          '["pile", "Their pile"]' in wk and t33_main('_build/worker/intake.js').decode('utf-8').replace('\r\n', '\n') == wk.replace('\r\n', '\n'))

    # ---- Every page's visible text, title, description and structured data: origin/main's with only the listed lines changed.
    D = {}
    for n in names:
        q = page33(1440)
        load(q, MB + n)
        a = q.evaluate(T32_DOM_JS)
        load(q, TB + n)
        t = q.evaluate(T32_DOM_JS)
        q.close()
        D[n] = (a, t)
    swaps = {'index.html': [(T33_R2_OLD, T33_R2), (T34_H1_OLD + ' ' + T34_LINE_OLD, T34_H1 + ' ' + T34_LINE)],   # T-34: the home opening
             'local.html': [(T33_R3_OLD, T33_R3), (T33_R4_OLD, T33_R4), (' '.join(T33_R5_OLD), ' '.join(T33_R5)),
                            (T33_R6_OLD[0], T33_R6[0]), (T33_R6_OLD[1], T33_R6[1]), (T33_R7_OLD, T33_R7),
                            *zip(T33_R8_OLD, T33_R8),
                            ('Build from $3,000 · support from $750/month', 'Build from $3,000 · support from $750/month ' + ' '.join(T33_R9)),
                            (T33_R10_OLD, T33_R10), (T33_R14_OLD, T33_R14),
                            ('Free tools for your pile Reel shot list Plan your reel → Caption fitter Fit a caption → Busywork receipt Ring it up → '
                             'Recipe scaler Scale a recipe →',
                             'Free tools for your pile Busywork receipt Ring it up → ' + ' '.join(T33_GROUP) + ' Reel shot list Plan your reel → '
                             'Caption fitter Fit a caption →')],
             'start.html': [(' '.join(T33_R5_OLD), ' '.join(T33_R5)), (T33_R23_OLD, T33_R23)]}
    for p in T33_TOOL_PAGES:
        swaps[p] = [(t33_more(p, T33_ROW_OLD), t33_more(p, T33_ROW_ORDER))]
    for n in names:
        if n == 'work.html':
            continue
        a, t = D[n]
        want = t33_ws(a['text'])
        for o, nw in swaps.get(n, []):
            k = want.count(t33_ws(o))
            check(f'T-33: {n}: origin/main reads "{o[:50]}" exactly once (the line this item changes)', k == 1, str(k))
            want = want.replace(t33_ws(o), t33_ws(nw))
        got = t33_ws(t['text'])
        check(f'T-33: {n}: its visible text is origin/main\'s with only the listed lines changed', got == want,
              next((f'...{want[max(0, i - 60):i + 60]}... | ...{got[max(0, i - 60):i + 60]}...' for i in range(min(len(want), len(got))) if want[i] != got[i]), f'{len(want)} vs {len(got)}'))
        check(f'T-33: {n}: title and meta description are origin/main\'s', (a['title'], a['desc']) == (t['title'], t['desc']))
        ld = [x.replace(f'"{T33_R7_OLD}"', f'"{T33_R7}"').replace(f'"{T33_R8_OLD[0]}"', f'"{T33_R8[0]}"') for x in a['ld']]
        check(f'T-33: {n}: structured data is origin/main\'s (on local.html, with the two offer names R7 and R8 changed)', ld == t['ld'],
              str([x for x in zip(ld, t['ld']) if x[0] != x[1]])[:300])
    # The offer names in local.html's structured data are the new ones (final.py reads them from the page).
    ldl = ' '.join(D['local.html'][1]['ld'])
    check('T-33 R7, R8: local.html\'s structured data names the offers by their new names', f'"{T33_R7}"' in ldl and f'"{T33_R8[0]}"' in ldl
          and T33_R7_OLD not in ldl and T33_R8_OLD[0] not in ldl)
    check('T-33 R9: "Something else" is not a priced offer in the structured data', 'Something else' not in ldl)

    # ---- Old words: gone from every page's visible text. R14's Bird League sentence stays, word for word.
    for n in names:
        txt = t33_ws(D[n][1]['text'])
        left = [o for o in T33_GONE if t33_ws(o) in txt] + [r for r in T33_GONE_RX if _re.search(r, txt)]
        check(f'T-33: {n}: none of the old lines is on it', not left, str(left))
    check('T-33 R7, R8: the old offer names are nowhere in local.html, structured data included',
          T33_R7_OLD not in TH['local.html'] and f'>{T33_R8_OLD[0]}<' not in TH['local.html'] and f'"{T33_R8_OLD[0]}"' not in TH['local.html'])
    check('T-33 R14: the Bird League sentence reads exactly as before, on local.html',
          t33_ws(T33_R14_KEEP + ' ' + T33_R14) in t33_ws(D['local.html'][1]['text']) and t33_ws(T33_R14_KEEP) in t33_ws(D['local.html'][0]['text']))

    # ---- Each new line where it belongs (the element's whole text).
    places = [('index.html', 'span', T33_R2, 'R2'), ('local.html', 'p', T33_R3, 'R3'),
              ('local.html', '#engines-h', T33_R6[0], 'R6'), ('local.html', '#engines-h + p', T33_R6[1], 'R6'),
              ('local.html', '[data-card="reels"] h3', T33_R7, 'R7'), ('local.html', '[data-card="app"] h3', T33_R8[0], 'R8'),
              ('local.html', '[data-card="app"] > p', T33_R8[1], 'R8'), ('local.html', '[data-card="app"] dd', T33_R8[2], 'R8'),
              ('local.html', 'li', T33_R10, 'R10'), ('local.html', 'p', T33_R14_KEEP + ' ' + T33_R14, 'R14'),
              ('start.html', 'p.hint', T33_R23, 'R23')]
    for n, sel, want, rid in places:
        q = page33(1440)
        load(q, TB + n)
        k = q.evaluate(f'''([s, w]) => [...document.querySelectorAll(s)].filter(e => ({T33_NORM})(e) === w).length''', [sel, want])
        q.close()
        check(f'T-33 {rid}: {n}: "{want[:50]}" is the whole text of one {sel}', k == 1, str(k))
    # R7 and R8 keep everything under their names.
    q = page33(1440)
    load(q, MB + 'local.html')
    ob = q.evaluate('() => [...document.querySelectorAll("#engines article")].map(a => [...a.querySelectorAll("dl, :scope > p:last-of-type")].map(e => e.textContent.replace(/[\\s\\u00a0]+/g, " ").trim()))')
    load(q, TB + 'local.html')
    nb = q.evaluate('() => [...document.querySelectorAll("#engines article")].map(a => [...a.querySelectorAll("dl, :scope > p:last-of-type")].map(e => e.textContent.replace(/[\\s\\u00a0]+/g, " ").trim()))')
    q.close()
    check('T-33 R7, R8: the three offers keep every row and price line (the app offer\'s YOU SEND aside)',
          len(ob) == 3 and nb[:3] == [ob[0], [ob[1][0].replace(T33_R8_OLD[2], T33_R8[2]), ob[1][1]], ob[2]], str(nb[:3])[:300])
    check('T-33 R8: "It won\'t take a broken entry, like a recipe with no photo," is still in the app offer',
          "It won't take a broken entry, like a recipe with no photo," in nb[1][0])
    check('T-33: "Forty reels, one engine." is still on local.html', 'Forty reels, one engine.' in D['local.html'][1]['text'])

    # ---- R4 (the proof card), R9 (four offers), R20 (local's tools), at 320, 390, 1024 and 1440.
    for w in (320, 390, 1024, 1440):
        q = page33(w, 844)
        load(q, MB + 'local.html')
        ML = q.evaluate(T33_LOOK_JS)
        load(q, TB + 'local.html')
        L = q.evaluate(T33_LOOK_JS)
        q.close()
        c = L['card']
        check(f'T-33 R4: at {w}, the card holds its labels and its rows only (no line under the labels, no client line)',
              c['kids'] == 2 and c['p'] == 0, str(c)[:200])
        check(f'T-33 R4: at {w}, the labels are REAL RESULTS and BUILT WITH AI', [h[0] for h in c['head']] == ['REAL RESULTS', 'BUILT WITH AI'], str(c['head']))
        if w == 1440:
            check('T-33 R4: at 1440, REAL RESULTS on the left and BUILT WITH AI on the right, on one line',
                  c['head'][0][1] < c['head'][1][1] and abs(c['head'][0][2] - c['head'][1][2]) <= 3, str(c['head']))
        check(f'T-33 R4: at {w}, four rows with the listed labels and values', [r[:2] for r in c['rows']] == [list(r) for r in T33_R4_ROWS], str(c['rows']))
        check(f'T-33 R4: at {w}, every row keeps 13px type and whole values inside the card', all(r[2] == '13px' and r[3] == '13px' and r[4] and r[5]
              and r[6] == 'nowrap' for r in c['rows']), str(c['rows']))
        check(f'T-33 R4: at {w}, the card keeps its width', c['size'] == ML['card']['size'], str([ML['card']['size'], c['size']]))
        o = L['offers']
        check(f'T-33 R9: at {w}, four offer blocks', len(o) == 4 and [x['h'] for x in o] == [T33_R7, T33_R8[0], 'Busywork, automated', T33_R9[0]], str([x['h'] for x in o]))
        if len(o) == 4:
            s = o[3]
            check(f'T-33 R9: at {w}, the fourth block: its name, its line, its price line, and no rows',
                  s['ps'] == [T33_R9[1], T33_R9[2]] and s['dl'] == 0 and s['card'] is None, str(s)[:300])
            check(f'T-33 R9: at {w}, the fourth block is the same card as the other three', s['cls'] == o[2]['cls']
                  and _re.sub(r'(border|box-shadow)[^;]*;', '', s['style']) == _re.sub(r'(border|box-shadow)[^;]*;', '', o[2]['style'])
                  and 'border: 2px solid' in s['style'] and s['price'] == o[2]['price'] and s['h3y'] == o[2]['h3y'], str([s['price'], o[2]['price'], s['h3y'], o[2]['h3y'], s['cls'], o[2]['cls'], s['style'] == o[2]['style']]))
            xs, ys, ws = sorted({x['x'] for x in o}), sorted({x['y'] for x in o}), {x['w'] for x in o}
            cols = 1 if w < 700 else 2
            check(f'T-33 R9: at {w}, the four sit evenly, {cols} across', len(xs) == cols and len(ys) == 4 // cols and len(ws) == 1, str([xs, ys, ws]))
        tl = L['tools']
        check(f'T-33 R20: at {w}, local.html\'s tools in order: Busywork receipt, then the reel engine pair', tl['h3'] == T33_LOCAL_TOOLS, str(tl['h3']))
        check(f'T-33 R20: at {w}, the reel engine pair sits under its label and line',
              len(tl['group']) == 1 and tl['group'][0] == {'label': T33_GROUP[0], 'ps': list(T33_GROUP), 'h3': T33_LOCAL_TOOLS[1:]}, str(tl['group']))
        check(f'T-33 R21: at {w}, no recipe scaler in local.html\'s tools', all('scaler' not in h for h, _x in tl['links']) and 'Recipe scaler' not in tl['h3'])
        check(f'T-33 R20: at {w}, each tool keeps its own name and link', tl['links'] == [['receipt.html', 'Ring it up →'], ['shotlist.html', 'Plan your reel →'],
              ['captions.html', 'Fit a caption →']], str(tl['links']))
        bx = tl['boxes']
        if w >= 1024:
            check(f'T-33 R20: at {w}, the three tool cards sit level in one row', len({b_[1] for b_ in bx}) == 1 and bx[0][2] < bx[1][0] < bx[2][0], str(bx))
        else:
            check(f'T-33 R20: at {w}, the tool cards stack, one under another', len({b_[0] for b_ in bx}) == 1 and bx[0][1] < bx[1][1] < bx[2][1], str(bx))
        check(f'T-33: at {w}, local.html has no sideways scroll', L['sw'][0] <= L['sw'][1], str(L['sw']))

    # ---- R5: five choices in order on local.html and start.html; the old four send what they sent on origin/main.
    q = page33(1440)
    load(q, TB + 'local.html')
    picks = q.evaluate(f'() => [...document.querySelectorAll("button[data-pick]")].map(b => [b.getAttribute("data-pick"), ({T33_NORM})(b), b.getAttribute("data-value")])')
    q.close()
    check('T-33 R5: local.html, five choices in the listed order', [p_[1] for p_ in picks] == T33_R5, str(picks))
    q = page33(1440)
    load(q, MB + 'local.html')
    mpicks = q.evaluate(f'() => [...document.querySelectorAll("button[data-pick]")].map(b => [b.getAttribute("data-pick"), ({T33_NORM})(b)])')
    q.close()
    check('T-33 R5: origin/main\'s local.html had the four old choices', [p_[1] for p_ in mpicks] == T33_R5_OLD, str(mpicks))

    def sent_local(base, pid):
        """Pick a choice on local.html, answer the three questions, press send: the pile in the address it opens."""
        q = page33(1440)
        q.route('**/start.html*', lambda route: route.fulfill(status=200, body='<!doctype html><title>s</title>', content_type='text/html'))
        load(q, base + 'local.html')
        q.click(f'button[data-pick="{pid}"]')
        st = q.evaluate('() => [document.getElementById("intake").hidden, document.getElementById("pick-msg").hidden, '
                        '[...document.querySelectorAll("[data-match]")].filter(e => !e.hidden).length]')
        for g in ('q1', 'q2', 'q3'):
            q.click(f'button.iq[data-q="{g}"] >> nth=0')
        with q.expect_navigation():
            q.click('#iq-send')
        u = q.url
        q.close()
        frag = u.split('#', 1)[1]
        kv = dict(x.split('=', 1) for x in frag.split('&') if '=' in x)
        return _unquote(kv.get('pile', '')), st

    for (pid, _m_label), old_label in zip(mpicks, T33_R5_OLD):
        was, _st = sent_local(MB, pid)
        now, st = sent_local(TB, pid)
        check(f'T-33 R5: local.html, choice "{pid}" sends what it sent on origin/main ("{was}")', now == was and was == old_label, str([was, now]))
        check(f'T-33 R5: local.html, choice "{pid}" still opens the three questions', st[0] is False, str(st))
    now, st = sent_local(TB, 'tool')
    check('T-33 R5: local.html, the new fourth choice sends its own value', now == T33_R5_NEWVAL, now)
    check('T-33 R5: local.html, the new fourth choice opens the three questions, shows no message box and marks no offer',
          st == [False, True, 0], str(st))
    q = page33(1440)
    load(q, TB + 'local.html')
    q.click('button[data-pick="tool"]')
    pressed = q.evaluate('() => [...document.querySelectorAll("button[data-pick]")].map(b => b.getAttribute("aria-pressed"))')
    q.close()
    check('T-33 R5: local.html, the new fourth choice shows as the pressed one', pressed == ['false', 'false', 'false', 'true', 'false'], str(pressed))

    q = page33(1440)
    load(q, TB + 'start.html')
    chips = q.evaluate(f'() => [...document.querySelectorAll(".chips[data-key=pile] .chip")].map(c => ({T33_NORM})(c))')
    q.close()
    check('T-33 R5: start.html step 01, five choices in the listed order', chips == T33_R5, str(chips))

    def sent_start(base, i):
        q = page33(1440)
        load(q, base + 'start.html')
        q.click(f'.chips[data-key="pile"] .chip >> nth={i}')
        q.fill('#name', 'Pat Test'); q.fill('#email', 'pat@example.com')
        n0 = len(posts)
        q.click('#bp-send'); q.wait_for_timeout(500)
        q.close()
        return posts[-1]['fields'].get('pile') if len(posts) == n0 + 1 else None

    def preselected(base, value):
        q = page33(1440)
        load(q, base + 'start.html#pile=' + _quote33(value, safe=''))
        on = q.evaluate(f'() => [...document.querySelectorAll(".chips[data-key=pile] .chip[aria-pressed=true]")].map(c => ({T33_NORM})(c))')
        q.close()
        return on

    new_index = {0: 0, 1: 1, 2: 2, 3: 4}   # the old four's places among the five
    for i, old_label in enumerate(T33_R5_OLD):
        was, now = sent_start(MB, i), sent_start(TB, new_index[i])
        check(f'T-33 R5: start.html, "{T33_R5[new_index[i]]}" sends what "{old_label}" sent on origin/main', was == old_label and now == was, str([was, now]))
        check(f'T-33 R5: start.html, arriving with #pile={old_label} selects "{T33_R5[new_index[i]]}"', preselected(TB, old_label) == [T33_R5[new_index[i]]])
    check('T-33 R5: start.html, the new fourth choice sends its own value', sent_start(TB, 3) == T33_R5_NEWVAL)
    check('T-33 R5: start.html, arriving with the new value selects the new fourth choice', preselected(TB, T33_R5_NEWVAL) == [T33_R5[3]])
    check('T-33 R5: the receipt tool\'s "#pile=A weekly task that eats hours" link still selects that choice',
          "start.html#pile='+encodeURIComponent('A weekly task that eats hours')" in TH['receipt.html'] and preselected(TB, T33_R5[2]) == [T33_R5[2]])

    # ---- R11, R12, R13, R21 and R20 on work.html.
    q = page33(1440)
    load(q, MB + 'work.html')
    MW = q.evaluate(T33_WORK_JS)
    load(q, TB + 'work.html')
    W = q.evaluate(T33_WORK_JS)
    check('T-33 R11: work.html, the five tabs in order', [t_[0] for t_ in W['tabs']] == T33_R11_TABS, str(W['tabs']))
    check('T-33 R11: origin/main had the old tabs', [t_[0] for t_ in MW['tabs']] == T33_R11_OLD_TABS, str(MW['tabs']))
    check('T-33 R11: "Free tools" keeps its key, so work.html#free still opens it', W['tabs'][-1] == ['Free tools', 'free'])
    check('T-33 R12: work.html, the cards in the listed order', [c_['h'] for c_ in W['cards']] == [h for h, _t in T33_CARDS], str([c_['h'] for c_ in W['cards']]))
    check('T-33 R11: work.html, every card\'s tags', [c_['tags'] for c_ in W['cards']] == [t_ for _h, t_ in T33_CARDS], str([c_['tags'] for c_ in W['cards']]))
    old_cards = {c_['h']: c_ for c_ in MW['cards']}
    for c_ in W['cards']:
        o = old_cards.get(c_['h'])
        if c_['h'] == 'Birdsighted':
            check('T-33 R13: the Birdsighted card is new', o is None)
            continue
        if o is None:
            check(f'T-33: work.html card "{c_["h"]}" was on origin/main', False)
            continue
        swap = {'Nonprofit': 'Client', 'Banking': 'My own build'}
        check(f'T-33 R11: work.html "{c_["h"]}" keeps every other tag', c_['tags'] == [swap.get(x, x) for x in o['tags']], str([o['tags'], c_['tags']]))
        want = t33_ws(o['text'])
        got = t33_ws(c_['text'])
        exp = t33_ws(' '.join(swap.get(x, x) for x in o['tags'])) + want[len(t33_ws(' '.join(o['tags']))):]
        if c_['h'] == 'A seasonal cooking app for teachers':
            exp += t33_ws(T33_R21[0])
        check(f'T-33: work.html "{c_["h"]}" reads as on origin/main, its tags aside (and R21\'s link on the kids\' app card)', got == exp, str([exp, got])[:400])
    check('T-33 R21: work.html, the recipe scaler card is gone', 'Recipe scaler' in old_cards and 'Recipe scaler' not in [c_['h'] for c_ in W['cards']]
          and 'Kitchens' not in sum((c_['tags'] for c_ in W['cards']), []))
    kid = next((c_ for c_ in W['cards'] if c_['h'] == 'A seasonal cooking app for teachers'), {'links': []})
    check('T-33 R21: the kids\' app card links its recipe scaler, under "About custom apps →"',
          kid['links'] == [['local.html#engines', 'About custom apps →'], [T33_R21[1], T33_R21[0]]], str(kid['links']))
    bs = next((c_ for c_ in W['cards'] if c_['h'] == 'Birdsighted'), None)
    check('T-33 R13: the Birdsighted card: tags, heading, line and link, no number and no picture',
          bs and bs['tags'] == ['My own build', 'Game'] and bs['links'] == [[T33_R13[3], T33_R13[2]]]
          and t33_ws(bs['text']) == t33_ws('My own build Game ' + ' '.join(T33_R13[:3])), str(bs))
    n_img = q.evaluate('() => { const c = [...document.querySelectorAll("#cards .card")].find(c => c.querySelector("h2").textContent.trim() == "Birdsighted"); '
                       'return [c.querySelectorAll("img").length, c.querySelectorAll(".num").length, c.className] }')
    check('T-33 R13: the Birdsighted card has no picture and no number, and is a card like Bird League\'s', n_img[:2] == [0, 0] and 'card' in n_img[2].split(), str(n_img))
    check('T-33 R20: work.html, the reel engine pair sits under its label and line',
          W['groups'] == [{'hidden': False, 'label': T33_GROUP[0], 'line': T33_GROUP[1], 'cards': ['Reel shot list', 'Caption fitter'], 'labelled': 'reel-tools'}], str(W['groups']))
    check('T-33 R11: work.html reads as on origin/main outside the cards, the tabs aside',
          t33_ws(W['outside']) == t33_ws(MW['outside']).replace(t33_ws(' '.join(T33_R11_OLD_TABS)), t33_ws(' '.join(T33_R11_TABS))), str([MW['outside'][:300], W['outside'][:300]]))
    for tab in T33_R11_TABS:
        q.click(f'.filt:text-is("{tab}")')
        q.wait_for_timeout(60)
        S = q.evaluate(T33_WORK_JS)
        shown = [c_['h'] for c_ in S['cards'] if not c_['hidden']]
        check(f'T-33 R11: work.html, "{tab}" shows exactly its cards', shown == T33_TABS_SHOW[tab], str(shown))
        grp_on = not S['groups'][0]['hidden']
        check(f'T-33 R20: work.html, under "{tab}" the reel engine label shows only with its cards',
              grp_on == ('Reel shot list' in shown), str([tab, grp_on]))
        if tab == 'Free tools':
            check('T-33 R20: work.html\'s free tools in order: Busywork receipt, COBOL field decoder, then the reel engine pair', shown == T33_WORK_TOOLS, str(shown))
    q.close()
    q = page33(1440)
    load(q, TB + 'work.html#free')
    q.wait_for_timeout(200)
    S = q.evaluate(T33_WORK_JS)
    q.close()
    check('T-33 R11: work.html#free still opens on the free tools', [c_['h'] for c_ in S['cards'] if not c_['hidden']] == T33_WORK_TOOLS)
    q = page33(1440)
    load(q, TB + 'studio.html')
    sid = q.evaluate('() => { const e = document.getElementById("birdsighted"); return e ? [e.className, e.querySelector("h3").textContent.trim()] : null }')
    q.close()
    check('T-33 R13: studio.html#birdsighted is the Birdsighted block', sid == ['gapp', 'Birdsighted'], str(sid))
    import theme as _theme33r
    st33 = _theme33r.theme_page(un34(t32_read(outd, 'studio.html'), 'studio.html'), 'studio.html')   # T-34: the themed page as T-33 built it
    check('T-33 R13: the id is the only change to studio.html\'s Birdsighted block',
          st33.count('<div class="gapp" id="birdsighted">') == 1 and stamp27(st33).replace(' id="birdsighted"', '', 1)
          == stamp27(t33_main('studio.html').decode('utf-8').replace('\r\n', '\n')))

    # ---- R20, R21: each tool page's "More free tools:" row.
    for p in T33_TOOL_PAGES:
        q = page33(1440)
        load(q, TB + p)
        L = q.evaluate(T33_LOOK_JS)
        q.close()
        want = [x for x in T33_ROW_ORDER if x != T33_TOOL_NAME[p]]
        hrefs = {v: k for k, v in T33_TOOL_NAME.items()}
        check(f'T-33 R20: {p}: "More free tools:" lists the others in order, with no group label',
              L.get('more') and L['more']['links'] == [[hrefs[x], x] for x in want] and L['more']['text'] == t33_more(p, T33_ROW_ORDER), str(L.get('more')))
        check(f'T-33 R21: {p}: no recipe scaler in its row', L.get('more') and 'scaler.html' not in str(L['more']['links']))

    # ---- At 320, 390 and 1440: no sideways scroll; axe at 390 and 1440 (color contrast in, a 1:1 pair counted).
    axe = t32_axe()
    for n in T33_PAGES:
        for w, h in ((320, 700), (390, 844), (1440, 900)):
            q = page33(w, h)
            load(q, TB + n)
            sw = q.evaluate('[document.documentElement.scrollWidth, innerWidth]')
            check(f'T-33: at {w}, {n} has no sideways scroll', sw[0] <= sw[1], str(sw))
            if w in (390, 1440):
                q.add_script_tag(content=axe)
                res = q.evaluate('() => axe.run(document, {resultTypes: ["violations", "incomplete"]}).then(r => r.violations.map(v => [v.id, v.nodes.length, v.nodes.slice(0, 3).map(x => x.target.join(" "))])'
                                 '.concat(r.incomplete.filter(v => v.id == "color-contrast").map(v => [v.id + " 1:1", v.nodes.filter(x => (x.any || []).some(c => c.data && c.data.messageKey == "equalRatio")).map(x => x.target.join(" "))]).filter(v => v[1].length)))')
                check(f'T-33: at {w}, {n}: axe-core {T32_AXE_VER}, color contrast included: 0 violations', not res, str(res)[:600])
            q.screenshot(path=f'{SHOTS}/t33-{n[:-5]}-{w}.png', full_page=True)
            q.close()


# ---------------- T-34 (Nov 20, 2026): the home opening, no italic switches, bigger Then and Now
# Josef picked direction A: the home h1 in Barlow Semi Condensed 900 with the pen underline under "easy.", the line under
# it reworded; every headline that switched to italic partway through keeps its marked words upright in their color, the
# pen underline under three words or fewer; Then and Now on Studio as section-size labels. Run on the themed root.
T34_MAIN = '61adbc7'   # origin/main when T-34 was cut (T-33 DONE)
T34_PAGES = ['index.html', '404.html', 'briefing.html', 'comp3.html', 'mainframe.html', 'studio.html']
T34_BLUE = 'rgb(28, 95, 168)'
# (page, the marked words, the color they keep: None = the color they had on origin/main, the pen's stroke or None)
T34_MARKS = [
    ('index.html', 'easy.', T32_INK, 'E8592B'),          # item 1: no color change on the word, the underline is the mark
    ('index.html', '(n.)', None, 'F07A4E'),               # on the dark band
    ('index.html', 'does what the old one did.', None, None),
    ('404.html', "doesn't go anywhere", None, 'E8592B'),
    ('briefing.html', 'system', None, '1C5FA8'),
    ('briefing.html', "I'll take it from here.", None, None),
    ('comp3.html', 'decoder', None, '1C5FA8'),
    ('comp3.html', 'It never tells you what the number means.', None, None),
    ('mainframe.html', 'The interest came out 100 times too high.', None, None),
    ('mainframe.html', 'Only the real data your business stores can tell you which one is right.', None, None),
    ('mainframe.html', 'The real data settles it.', None, None),
    ('mainframe.html', "and see what I'd look at first", None, None),
]
T34_PEN = ("background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 20' "
           "preserveAspectRatio='none'%3E%3Cpath d='M3 13 C 60 6, 120 16, 180 9 S 270 7, 297 11' fill='none' stroke='%23{}' "
           "stroke-width='5' stroke-linecap='round'/%3E%3C/svg%3E\");background-repeat:no-repeat;background-size:100% 0.2em;"
           "background-position:0 100%;padding-bottom:0.12em;box-decoration-break:clone;-webkit-box-decoration-break:clone")

# A marked phrase: the element whose whole text it is, inside a headline line (its block holds more words).
T34_MARK_JS = r"""(t) => { const sp = s => (s || '').replace(/[\s\u00a0]+/g, ' ').trim(), cs = e => getComputedStyle(e);
  const els = [...document.querySelectorAll('body span, body em, body i')].filter(e => sp(e.textContent) === t && sp(e.parentElement.textContent) !== t);
  return els.map(e => { const c = cs(e), pc = cs(e.parentElement);
    return {tag: e.tagName, cls: e.className, style: c.fontStyle, fam: c.fontFamily, wt: c.fontWeight, size: c.fontSize, color: c.color, ws: c.whiteSpace,
            pfam: pc.fontFamily, pwt: pc.fontWeight, psize: pc.fontSize, pstyle: pc.fontStyle, pcolor: pc.color,
            bg: c.backgroundImage, tap: !!e.closest('a,button,label,input,select,textarea,summary'), pe: c.pointerEvents,
            aria: [...e.attributes].map(a => a.name).filter(n => n.startsWith('aria-') || n === 'role')}; }); }"""
# The italic sweep: every h1 to h3, and every line set at 28px or more that holds words of its own.
T34_ITALIC_JS = r"""() => { const cs = e => getComputedStyle(e), sp = s => (s || '').replace(/\s+/g, ' ').trim(), bad = [];
  const own = e => [...e.childNodes].some(n => n.nodeType === 3 && n.data.trim());
  const heads = new Set([...document.querySelectorAll('h1,h2,h3')]);
  for (const e of document.querySelectorAll('body *')) if (!e.closest('script,style,svg') && own(e) && parseFloat(cs(e).fontSize) >= 28) heads.add(e);
  for (const h of heads) {
    const st = cs(h).fontStyle, tw = document.createTreeWalker(h, NodeFilter.SHOW_TEXT); let n, sw = [];
    while ((n = tw.nextNode())) if (n.data.trim() && cs(n.parentElement).fontStyle !== st) sw.push(sp(n.data));
    const tags = h.querySelectorAll('em,i').length;
    if (tags || sw.length || (/^H[123]$/.test(h.tagName) && st !== 'normal')) bad.push([h.tagName, sp(h.textContent).slice(0, 60), tags, st, sw]); }
  return bad; }"""
T34_PEN_JS = r"""() => { const ctx = document.createElement('canvas').getContext('2d');
  const blockOf = el => { let e = el.parentElement; while (e && getComputedStyle(e).display === 'inline') e = e.parentElement; return e; };
  const glyphs = root => { const out = []; if (!root) return out;
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let t = tw.nextNode(); t; t = tw.nextNode()) { const cs = getComputedStyle(t.parentElement);
      ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      for (let i = 0; i < t.length; i++) { if (/\s/.test(t.data[i])) continue;
        const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1); const rc = r.getBoundingClientRect(); if (!rc.width) continue;
        const m = ctx.measureText(t.data[i]), base = rc.top + m.fontBoundingBoxAscent + (rc.height - m.fontBoundingBoxAscent - m.fontBoundingBoxDescent) / 2;
        out.push({ch: t.data[i], l: rc.left, r: rc.right, top: base - m.actualBoundingBoxAscent, bot: base + m.actualBoundingBoxDescent}); } }
    return out; };
  return [...document.querySelectorAll('.pen')].map(el => { const fs = parseFloat(getComputedStyle(el).fontSize), blk = blockOf(el);
    const near = [...glyphs(blk), ...glyphs(blk.previousElementSibling), ...glyphs(blk.nextElementSibling)], hits = [];
    const frags = [...el.getClientRects()];
    for (const f of frags) { const b0 = f.bottom - 0.2 * fs, b1 = f.bottom;
      for (const g of near) { if (g.r <= f.left || g.l >= f.right) continue;
        if (Math.abs((g.top + g.bot) / 2 - (f.top + f.bottom) / 2) < fs * 0.5) continue;   // a glyph on the pen's own line
        if (g.bot > b0 && g.top < b1) hits.push(`"${g.ch}" ink ${Math.round(g.top)}-${Math.round(g.bot)} vs line ${Math.round(b0)}-${Math.round(b1)}`); } }
    return [el.textContent, frags.length, hits.slice(0, 4)]; }); }"""
T34_GAL_JS = r"""() => [...document.querySelectorAll('.ghead')].map(g => { const l = g.querySelector('.label'), c = g.querySelector('.gcap'), cs = getComputedStyle(l);
  let b = l, bg = 'rgba(0, 0, 0, 0)'; while (b && (bg = getComputedStyle(b).backgroundColor) === 'rgba(0, 0, 0, 0)') b = b.parentElement;
  const cc = c && getComputedStyle(c);
  return {t: l.textContent, cls: l.className, fam: cs.fontFamily, wt: cs.fontWeight, size: parseFloat(cs.fontSize), color: cs.color, bg,
          cap: c && [c.textContent, cc.fontFamily, cc.fontSize, cc.color]}; })"""


def t34_lum(c):
    v = [float(x) / 255 for x in _re.findall(r'[\d.]+', c)[:3]]
    v = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def t34_ratio(a, b_):
    la, lb = sorted((t34_lum(a), t34_lum(b_)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def t34_main(name):
    return _sp.run(['git', 'show', f'{T34_MAIN}:{name}'], cwd=os.path.join(here, '..'), capture_output=True, check=True).stdout


@section('T-34')
def s_t_34():
    port = free_port()
    srv = _sp.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', T32_DIR], cwd=here,
                    stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    TB = f'http://127.0.0.1:{port}/'
    try:
        for _i in range(100):
            try:
                urlopen(TB + 'index.html', timeout=2).read()
                break
            except OSError:
                time.sleep(0.1)
        _t34_checks(TB)
    finally:
        srv.kill()
        srv.wait()


def _t34_checks(TB):
    MB = TB + '__m34/'
    mains = {}

    def serve_main(route):
        path = route.request.url.split('/__m34/', 1)[1].split('?')[0].split('#')[0]
        if path.endswith('.html'):
            if path not in mains:
                mains[path] = t34_main(path)
            return route.fulfill(status=200, body=mains[path], content_type='text/html; charset=utf-8')
        return route.continue_(url=TB + path)

    def page34(w, h=900):
        q = newpage(w, h)
        q.route('**/__m34/**', serve_main)
        q.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
        return q

    def load(q, url):
        q.goto(url, wait_until='load')
        q.evaluate('document.fonts.ready.then(() => 1)')
        q.wait_for_timeout(150)

    names = sorted(ALL_HTML)
    TH = {n: t32_read(T32_DIR, n) for n in names}

    # ---- The files: the root is this build, and un34() gives back origin/main exactly.
    check('T-34: every root page is the themed page (this build)', not t32_root_off(names), str(t32_root_off(names)))
    import theme as _theme34
    for n in names:
        new = t32_read(outd, n)
        u = un34(new, n)
        check(f'T-34: un34() takes T-34 out of {n}: through theme.py it is origin/main\'s root page byte for byte',
              stamp27(_theme34.theme_page(u, n)) == stamp27(t34_main(n).decode('utf-8').replace('\r\n', '\n')))
        check(f'T-34: un34() changes {n} exactly when T-34 changed it, and a second pass changes nothing',
              (u != new) == (n in T34_PAGES) and un34(u, n) == u)
    check('T-34: T-34 changes exactly the six pages (and, in the sources un34() reads, the Mainframe canvas)',
          sorted(T34_UNDO) == sorted(T34_PAGES + ['canvas/Mainframe.dc.html']), str(sorted(T34_UNDO)))
    cv = open(os.path.join(here, 'canvas', 'Mainframe.dc.html'), encoding='utf-8', newline='').read().replace('\r\n', '\n')
    check('T-34: un34() gives back origin/main\'s Mainframe canvas byte for byte',
          un34(cv, 'canvas/Mainframe.dc.html') == t34_main('_build/canvas/Mainframe.dc.html').decode('utf-8').replace('\r\n', '\n'))
    for n in names:
        old = t34_main(n).decode('utf-8')
        check(f'T-34: {n}: no em dash added', TH[n].count('—') <= old.count('—'), f'{old.count(chr(0x2014))} -> {TH[n].count(chr(0x2014))}')
    check('T-34: no em dash in the two new lines', '—' not in T34_H1 + T34_LINE)
    # The pen underline: one definition, the item's, in the stroke for each side and band.
    for n in names:
        has = 'class="pen' in TH[n]
        mf = n in T32_MF
        want = [T34_PEN.format('1C5FA8' if mf else 'E8592B')]
        if 'pen-ink' in TH[n]:
            want.append("stroke='%23" + ('8FB8E8' if mf else 'F07A4E') + "'")
        check(f'T-34: {n}: the pen underline\'s definition is on the page exactly when the page uses it, as the item writes it',
              (all(x in TH[n] for x in want) if has else 'M3 13 C 60 6' not in TH[n]), str(has))
    check('T-34: the pen underline is in DESIGN.md\'s components, beside the ring and the route',
          '- **The pen underline:**' in open(os.path.join(here, 'DESIGN.md'), encoding='utf-8').read())
    for n in names:
        heads = _re.findall(r'<(h[1-3])\b[^>]*>(.*?)</\1>', TH[n], _re.S)
        check(f'T-34: {n}: no <em> or <i> inside an h1 to h3 (source)', not [h for h in heads if _re.search(r'<(em|i)\b', h[1])])

    # ---- Every page's visible text, title, description, links and images: origin/main's with only the two lines changed.
    D = {}
    for n in names:
        q = page34(1440)
        load(q, MB + n)
        a = q.evaluate(T32_DOM_JS)
        load(q, TB + n)
        t = q.evaluate(T32_DOM_JS)
        italic = q.evaluate(T34_ITALIC_JS)
        q.close()
        D[n] = (a, t)
        want = t33_ws(a['text'])
        if n == 'index.html':
            o, nw = T34_H1_OLD + ' ' + T34_LINE_OLD, T34_H1 + ' ' + T34_LINE
            check('T-34: index.html: origin/main reads the old opening exactly once', want.count(t33_ws(o)) == 1, str(want.count(t33_ws(o))))
            want = want.replace(t33_ws(o), t33_ws(nw))
        got = t33_ws(t['text'])
        check(f'T-34: {n}: its visible text is origin/main\'s with only the two listed lines changed', got == want,
              next((f'...{want[max(0, i - 60):i + 60]}... | ...{got[max(0, i - 60):i + 60]}...' for i in range(min(len(want), len(got))) if want[i] != got[i]), f'{len(want)} vs {len(got)}'))
        check(f'T-34: {n}: title, description, links, images and structured data are origin/main\'s',
              all(a[k] == t[k] for k in ('title', 'desc', 'links', 'imgs', 'ld')), str([k for k in ('title', 'desc', 'links', 'imgs', 'ld') if a[k] != t[k]]))
        check(f'T-34: {n}: no h1 to h3 or headline line holds <em> or <i> or switches to italic', not italic, str(italic)[:400])

    # ---- Item 1: the home opening.
    for w in (320, 390, 1440):
        q = page34(w)
        load(q, TB + 'index.html')
        H = q.evaluate(r"""() => { const h = document.querySelector('main h1'), p = h.nextElementSibling, c = getComputedStyle(h), sp = s => s.replace(/[\s\u00a0]+/g, ' ').trim();
          const pen = h.querySelector('.pen'), pc = pen && getComputedStyle(pen), pp = getComputedStyle(p);
          return {n: document.querySelectorAll('h1').length, text: sp(h.textContent), fam: c.fontFamily, wt: c.fontWeight, size: c.fontSize, lh: c.lineHeight, ls: c.letterSpacing,
                  color: c.color, style: c.fontStyle, mw: c.maxWidth, ta: c.textAlign, wrap: c.textWrapStyle || c.textWrap, ch: (() => { const s = document.createElement('span');
                  s.style.cssText = 'position:absolute;visibility:hidden;font:inherit;letter-spacing:inherit'; s.textContent = '0'; h.appendChild(s); const x = s.getBoundingClientRect().width; s.remove(); return x; })(),
                  width: h.getBoundingClientRect().width, center: [h.getBoundingClientRect().left + h.getBoundingClientRect().width / 2, innerWidth / 2],
                  pen: pen && [sp(pen.textContent), pc.whiteSpace, pc.color, pc.fontStyle, pc.backgroundImage],
                  ptag: p.tagName, ptext: sp(p.textContent), pstyle: [pp.fontSize, pp.color, pp.maxWidth, pp.margin]}; }""")
        q.close()
        size = min(120, max(56, w * 0.08))
        check(f'T-34 item 1: at {w}, the home h1 reads "{T34_H1}"', H['n'] == 1 and H['text'] == T34_H1, H['text'])
        check(f'T-34 item 1: at {w}, the h1 is Barlow Semi Condensed 900, upright, #17212B',
              H['fam'].startswith('"Barlow Semi Condensed", Impact') and H['wt'] == '900' and H['style'] == 'normal' and H['color'] == T32_INK, str(H)[:300])
        check(f'T-34 item 1: at {w}, the h1 is {size:g}px (clamp(56px, 8vw, 120px)), line-height 0.9, letter-spacing -0.01em, balanced, centered',
              abs(float(H['size'][:-2]) - size) < 0.05 and abs(float(H['lh'][:-2]) - 0.9 * size) < 0.1 and abs(float(H['ls'][:-2]) + 0.01 * size) < 0.02
              and 'balance' in (H['wrap'] or '') and H['ta'] == 'center' and abs(H['center'][0] - H['center'][1]) < 1, str([H['size'], H['lh'], H['ls'], H['wrap'], H['ta'], H['center']]))
        check(f'T-34 item 1: at {w}, the h1 is at most 16ch wide', H['mw'] != 'none' and H['width'] <= 16 * H['ch'] + 0.5, str([H['mw'], H['width'], H['ch']]))
        check(f'T-34 item 1: at {w}, "easy." carries the orange pen underline, keeps together, upright, in the h1\'s ink',
              H['pen'] and H['pen'][0] == 'easy.' and H['pen'][1] == 'nowrap' and H['pen'][2] == T32_INK and H['pen'][3] == 'normal'
              and '%23E8592B' in H['pen'][4], str(H['pen'])[:200])
        check(f'T-34 item 1: at {w}, the line under it reads Josef\'s new words', H['ptag'] == 'P' and H['ptext'] == T34_LINE, H['ptext'])
    q = page34(1440)
    load(q, MB + 'index.html')
    oldp = q.evaluate("(() => { const p = document.querySelector('main h1').nextElementSibling, c = getComputedStyle(p); return [c.fontSize, c.color, c.maxWidth, c.margin]; })()")
    q.close()
    check('T-34 item 1: the line under the h1 keeps its paragraph style (at 1440)', oldp == H['pstyle'], str([oldp, H['pstyle']]))
    check('T-34 item 1: the old line is gone from every page', not [n for n in names if T34_LINE_OLD in TH[n] or T34_LINE_OLD.replace("'", '&#39;') in TH[n]])

    # ---- Item 2: each marked phrase upright, in its font, weight and size, keeping its color; the pen exactly where it belongs.
    pens = {}
    for n in names:
        q = page34(1440)
        load(q, TB + n)
        pens[n] = q.evaluate("[...document.querySelectorAll('.pen')].map(e => e.textContent)")
        q.close()
    want_pens = {n: [m[1] for m in T34_MARKS if m[0] == n and m[3]] for n in names}
    check('T-34 item 2: the pen underline sits exactly on the five short phrases and "easy." (no other page or phrase)',
          all(sorted(pens[n]) == sorted(want_pens[n]) for n in names), str({n: v for n, v in pens.items() if v}))
    for n, t, color, stroke in T34_MARKS:
        q = page34(1440)
        load(q, TB + n)
        M = q.evaluate(T34_MARK_JS, t)
        load(q, MB + n)
        O = q.evaluate(T34_MARK_JS, 'easy' if t == 'easy.' else t)
        q.close()
        short = len(t.split()) <= 3
        ok = len(M) == 1 and len(O) == 1
        check(f'T-34 item 2: {n}: "{t}" is marked once, as it was on origin/main', ok, f'{len(M)} {len(O)}')
        if not ok:
            continue
        m, o = M[0], O[0]
        check(f'T-34 item 2: {n}: "{t}" is upright, a plain span, in its line\'s font, weight and size',
              m['tag'] == 'SPAN' and m['style'] == 'normal' and m['pstyle'] == 'normal' and (m['fam'], m['wt'], m['size']) == (m['pfam'], m['pwt'], m['psize']), str(m)[:300])
        check(f'T-34 item 2: {n}: "{t}"\'s line keeps origin/main\'s font (only the home h1 moves to Barlow)',
              (m['pfam'] == o['pfam'] and m['psize'] == o['psize'] and m['pwt'] == o['pwt']) or t == 'easy.', str([m['pfam'], o['pfam'], m['pwt'], o['pwt']]))
        keep = color or o['color']
        check(f'T-34 item 2: {n}: "{t}" keeps its color ({keep})', m['color'] == keep, f'{m["color"]} (origin/main {o["color"]})')
        if n in T32_MF:
            check(f'T-34 item 2: {n}: "{t}" is the Mainframe blue', m['color'] == T34_BLUE, m['color'])
        if stroke:
            check(f'T-34 item 2: {n}: "{t}" ({len(t.split())} words) has the pen underline, stroke #{stroke}',
                  short or t == 'easy.', str(len(t.split())))
            check(f'T-34 item 2: {n}: "{t}"\'s pen draws in #{stroke}, as decoration only (no aria, no role, not on a tap target)',
                  'pen' in m['cls'].split() and f'%23{stroke}' in m['bg'] and not m['aria'] and not m['tap'], str([m['cls'], m['bg'][:60], m['aria'], m['tap']]))
        else:
            check(f'T-34 item 2: {n}: "{t}" ({len(t.split())} words) has color only, no underline',
                  not short and 'pen' not in m['cls'].split() and m['bg'] == 'none', str([m['cls'], m['bg'][:60]]))

    # ---- The underlines don't reach the line above or below, at 320, 390 and 1440.
    for n in [x for x in names if want_pens.get(x)]:
        for w in (320, 390, 1440):
            q = page34(w)
            load(q, TB + n)
            P = q.evaluate(T34_PEN_JS)
            q.close()
            for txt, frags, hits in P:
                check(f'T-34 item 3: at {w}, {n}: the pen under "{txt}" ({frags} line{"s" if frags > 1 else ""}) overlaps no line above or below it',
                      not hits, '; '.join(hits))

    # ---- Item 4: Then and Now.
    q = page34(1440)
    load(q, MB + 'studio.html')
    G0 = q.evaluate(T34_GAL_JS)
    q.close()
    for w in (320, 390, 1440):
        q = page34(w)
        load(q, TB + 'studio.html')
        G = q.evaluate(T34_GAL_JS)
        q.close()
        check(f'T-34 item 4: at {w}, the gallery labels and captions are origin/main\'s words', [(g['t'], g['cap'] and g['cap'][0]) for g in G] == [(g['t'], g['cap'] and g['cap'][0]) for g in G0],
              str([g['t'] for g in G]))
        tn = [g for g in G if g['t'] in ('Then', 'Now')]
        check(f'T-34 item 4: at {w}, four Then and Now labels', [g['t'] for g in tn] == ['Then', 'Now', 'Then', 'Now'], str([g['t'] for g in tn]))
        want_size = min(48, max(34, w * 0.036))
        for g in tn:
            check(f'T-34 item 4: at {w}, "{g["t"]}" is Barlow Semi Condensed 900 at {want_size:g}px (34px or more)',
                  g['fam'].startswith('"Barlow Semi Condensed", Impact') and g['wt'] == '900' and g['size'] >= 34 and abs(g['size'] - want_size) < 0.05, str(g))
            now = g['t'] == 'Now'
            check(f'T-34 item 4: at {w}, "{g["t"]}" is {"#A93F17, with the class now" if now else "ink"}',
                  (g['color'] == 'rgb(169, 63, 23)' and 'now' in g['cls'].split()) if now else (g['color'] == T32_INK and 'now' not in g['cls'].split()), str(g))
            r = t34_ratio(g['color'], g['bg'])
            check(f'T-34 item 4: at {w}, "{g["t"]}" has contrast 4.5:1 or more on its background ({r:.2f}:1 on {g["bg"]})', r >= 4.5, f'{r:.2f}')
            if now:
                check(f'T-34 item 4: at {w}, "November 2026" beside Now is JetBrains Mono 13px, #4F5A63',
                      g['cap'] and g['cap'][0] == 'November 2026' and g['cap'][1].startswith('"JetBrains Mono"') and g['cap'][2] == '13px' and g['cap'][3] == 'rgb(79, 90, 99)', str(g['cap']))

    # ---- At 320, 390 and 1440: no sideways scroll on any page; axe on the six pages at 390 and 1440 (a 1:1 pair counted).
    axe = t32_axe()
    for n in names:
        for w, h in ((320, 700), (390, 844), (1440, 900)):
            q = page34(w, h)
            load(q, TB + n)
            sw = q.evaluate('[document.documentElement.scrollWidth, innerWidth]')
            check(f'T-34: at {w}, {n} has no sideways scroll', sw[0] <= sw[1], str(sw))
            if w in (390, 1440) and n in T34_PAGES:
                q.add_script_tag(content=axe)
                res = q.evaluate('() => axe.run(document, {resultTypes: ["violations", "incomplete"]}).then(r => r.violations.map(v => [v.id, v.nodes.length, v.nodes.slice(0, 3).map(x => x.target.join(" "))])'
                                 '.concat(r.incomplete.filter(v => v.id == "color-contrast").map(v => [v.id + " 1:1", v.nodes.filter(x => (x.any || []).some(c => c.data && c.data.messageKey == "equalRatio")).map(x => x.target.join(" "))]).filter(v => v[1].length)))')
                check(f'T-34: at {w}, {n}: axe-core {T32_AXE_VER}, color contrast included: 0 violations', not res, str(res)[:600])
                q.screenshot(path=f'{SHOTS}/t34-{n[:-5]}-{w}.png', full_page=True)
            q.close()


# ================================================================ running the sections (T-31)
_ARGS = sys.argv[3:]
_WORKER = '--worker' in _ARGS
_RESULTS = []      # every check as {section, name, passed, detail}, in the order made
_CUR = [None]      # the id of the section running


def _send(t, **kw):
    """The worker's side of run_tests.py: one marked JSON line per event on stdout."""
    sys.stdout.write('\x1eDJ ' + json.dumps(dict(kw, t=t)) + '\n')
    sys.stdout.flush()


def _report(name, cond, detail):
    rec = {'section': _CUR[0], 'name': name, 'passed': bool(cond), 'detail': '' if cond else str(detail)}
    _RESULTS.append(rec)
    if _WORKER:
        _send('check', **rec)
    elif not cond:
        print(f'FAIL {name}  {detail}')


def section_line(sid, n, failed, secs):
    return f'{sid:<22} {n:>5} checks {failed:>4} failed {secs:>7.1f} s'


def run_section(sid, fn):
    """Runs one section; a section that stops on an error counts as one failed check that names it."""
    _CUR[0] = sid
    n0, t0 = len(_RESULTS), time.time()
    try:
        fn()
    except Exception:
        check(f'{sid}: the section runs to the end', False, traceback.format_exc()[-1500:])
    _CUR[0] = None
    mine = _RESULTS[n0:]
    return len(mine), sum(not r['passed'] for r in mine), time.time() - t0


def _arg(flag):
    return _ARGS[_ARGS.index(flag) + 1] if flag in _ARGS and _ARGS.index(flag) + 1 < len(_ARGS) else None


def _main():
    global b
    ids = [sid for sid, _f in SECTIONS]
    fns = dict(SECTIONS)
    only = _arg('--only')
    if only:
        want = [x.strip().lower() for x in only.split(',') if x.strip()]
        unknown = [x for x in want if x not in [i.lower() for i in ids]]
        if unknown:
            sys.exit(f'unknown section id(s): {", ".join(unknown)}. The ids: {", ".join(ids)}')
        ids = [i for i in ids if i.lower() in want]
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        if _WORKER:
            _send('hello', fonts=font_status(), pid=os.getpid())
            while True:
                sid = sys.stdin.readline().strip()
                if not sid or sid == 'END':
                    break
                n, failed, secs = run_section(sid, fns[sid])
                _send('done', section=sid, checks=n, failed=failed, seconds=round(secs, 2), line=section_line(sid, n, failed, secs))
            _send('end', errors=errors)
            b.close()
            return
        print(font_status())
        for sid in ids:
            n, failed, secs = run_section(sid, fns[sid])
            print(section_line(sid, n, failed, secs))
        check('no page errors', not errors, '; '.join(errors[:3]))
        b.close()
    secs = time.time() - t0
    print(f'{len(ok)}/{len(ok) + len(bad)} passed in {int(secs // 60)} min {int(secs % 60)} s')
    for x in bad:
        print('FAIL', x)
    if _arg('--results'):
        json.dump({'base': BASE, 'workers': 1, 'seconds': round(secs, 1), 'passed': len(ok), 'total': len(ok) + len(bad),
                   'checks': _RESULTS}, open(_arg('--results'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    _main()
