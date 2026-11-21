"""Shared page chrome for the Dragoman's Journey free tools.
Each tool supplies: slug, title, description, kicker, h1 (may contain <br>), lede, css, body, script.
Output is a standalone page written into _build/ (the pipeline copies it to the site)."""
import pathlib, re, sys

# No word alone on a line (T-20 F5, Nov 15, 2026): headings, buttons, chips and form
# labels balance their lines; paragraphs and list items avoid a last word alone.
# One copy for every page: tools/chrome.py puts it in each page it writes, and
# enhance.py puts it in each pipeline page, once.
WRAP_CSS = ("p,li,dd,dt,td,th,span,strong,figcaption{text-wrap:pretty}"
            ":is(h1,h2,h3,h4,button,.btn,.chip,.iq,.filt,label,.label,.lab,.mono,span[style*=\"JetBrains Mono\"]),"
            ":is(h1,h2,h3,h4,button,.btn,.chip,.iq,.filt,label,.label,.lab) :is(span,strong){text-wrap:balance}")

# Line breaking only, no word changes (T-21, Nov 16, 2026).
# G1: a hyphenated pair a visitor reads ("15-minute", "three-month") never breaks at
# its hyphen. The body font has no non-breaking hyphen glyph, so the pair sits in a
# no-wrap span (T-20's pattern for the call link). Only letters or digits joined by
# one or two hyphens (T-23 L1: "year-to-date", "side-by-side"), at most 24 characters;
# longer runs break as before. djNw() below stays at one hyphen: no text a tool script
# writes holds a two-hyphen word.
# G2: in a list joined by " · ", a line never starts or ends with the dot: the dot is
# held to the words on both sides by no-break spaces, so lines break inside an item.
# final.py runs nobreak() last over every finished page; the tool scripts use it (and
# djNw() in the page script) where they write such text themselves.
NOWRAP = '<span style="white-space: nowrap">'
MAX_PAIR = 24
_OPEN = r'(?:[(\["\'“‘]|&(?:quot|#x27|#39|ldquo|lsquo);)*'
_CLOSE = r'(?:[)\]"\'”’.,;:!?…]|&(?:quot|#x27|#39|rdquo|rsquo|hellip);)*'
_POSS = r'(?:(?:[\'’]|&#x27;|&#39;|&rsquo;)s)?'
PAIR_TOKEN = re.compile(r'(?P<pre>' + _OPEN + r')(?P<core>[^\W_]+(?:-[^\W_]+){1,2})(?P<post>' + _POSS + _CLOSE + ')')
DOT_GAP = re.compile(r'[ \t\r\n]+·[ \t\r\n]+')


def keep_pairs(text):
    """Escaped visible text, no tags: each hyphen pair in a no-wrap span."""
    out = []
    for part in re.split(r'(\s+|&nbsp;|&#160;)', text):
        m = PAIR_TOKEN.fullmatch(part) if "-" in part else None
        if m and len(m["core"]) <= MAX_PAIR:
            part = m["pre"] + NOWRAP + m["core"] + "</span>" + m["post"]
        out.append(part)
    return "".join(out)


def keep_dots(text):
    """Escaped visible text, no tags: " · " held to its neighbours."""
    return DOT_GAP.sub("&nbsp;·&nbsp;", text)


def nobreak(text):
    return keep_dots(keep_pairs(text))


# The same rule for text a page script writes (innerHTML only, never the clipboard).
NW_JS = (r"""function djNw(s){return String(s).replace(/(^|[\s(“"'‘])([A-Za-z0-9]+-[A-Za-z0-9]+)(?=$|[\s).,;:!?…”"'’])/g,"""
         r"""function(m,a,b){return b.length>24?m:a+'<span style="white-space: nowrap">'+b+'</span>'})}""")

# T-25 T1: nobreak() itself, for the tabs on local.html and mainframe.html that redraw their
# text (build.py). Without it a tab round trip dropped final.py's spans and held dots, so
# "year-to-date", "DEP-INTEREST-YTD" and "RESULT · REELS" could split again after a switch.
# Same rule, piece for piece: escaped text, split at spaces, one or two hyphens, at most 24
# characters, then " · " held to both neighbours. The page's text is never changed.
NB_JS = (r"""function djNb(s){return String(s).split(/(\s+|&nbsp;|&#160;)/).map(function(p){"""
         r"""if(p.indexOf('-')<0)return p;"""
         r"""var m=p.match(/^((?:[(\["'“‘]|&(?:quot|#x27|#39|ldquo|lsquo);)*)([\p{L}\p{N}]+(?:-[\p{L}\p{N}]+){1,2})((?:(?:['’]|&#x27;|&#39;|&rsquo;)s)?(?:[)\]"'”’.,;:!?…]|&(?:quot|#x27|#39|rdquo|rsquo|hellip);)*)$/u);"""
         r"""return m&&m[2].length<=""" + str(MAX_PAIR) + r"""?m[1]+'<span style="white-space: nowrap">'+m[2]+'</span>'+m[3]:p;"""
         r"""}).join('').replace(/[ \t\r\n]+·[ \t\r\n]+/g,'&nbsp;·&nbsp;')}""")

# The closing call band under each tool (G6): on wide screens the words and the button
# sit as one group, the button on the right, the words filling the rest.
BAND_CSS = ("@media (min-width:800px){section[aria-labelledby=\"more-h\"]{grid-template-columns:minmax(0,1fr) auto!important;column-gap:clamp(48px,6vw,96px)!important}"
            "section[aria-labelledby=\"more-h\"]>div:first-child{max-width:62ch}}")

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Dragoman's Journey</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://dragomansjourney.com/{slug}">
<meta property="og:title" content="{title} · Dragoman's Journey">
<meta property="og:description" content="{description}">
<meta property="og:site_name" content="Dragoman's Journey">
<meta property="og:type" content="website">
<meta property="og:url" content="https://dragomansjourney.com/{slug}">
<meta property="og:image" content="https://dragomansjourney.com/og/{og}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800;900&amp;family=Instrument+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&amp;family=JetBrains+Mono:wght@400;500;700&amp;display=swap">
<style>
body{{margin:0;background:#F2EDE1}}
*{{box-sizing:border-box}}
[hidden]{{display:none!important}}
a{{color:#A93F17}}a:hover{{color:#16201C}}
::selection{{background:#E8592B;color:#0E1B17}}
.dj{{font-family:'Instrument Sans','Helvetica Neue',system-ui,sans-serif;color:#16201C;font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}}
.dj a:focus-visible,.dj button:focus-visible,.dj input:focus-visible,.dj textarea:focus-visible,.dj select:focus-visible{{outline:3px solid #E8592B;outline-offset:3px}}
.wrap{{max-width:1240px;margin:0 auto;padding-left:clamp(16px,4vw,48px);padding-right:clamp(16px,4vw,48px)}}
.big{{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;line-height:.9;margin:0}}
.mono{{font-family:'JetBrains Mono',ui-monospace,monospace}}
.kick{{font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.1em;color:#F07A4E;text-transform:uppercase}}
.panel{{background:#FBF8F1;border:1.5px solid #CFC6B2;border-radius:2px;padding:clamp(18px,2.4vw,28px)}}
.label{{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#6B716A;margin:0 0 10px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{font:inherit;cursor:pointer;min-height:44px;padding:0 16px;border-radius:999px;border:1.5px solid #B9B09C;background:transparent;color:#16201C;font-size:15px;font-weight:600}}
.chip:hover{{border-color:#16201C}}
.chip[aria-pressed="true"]{{background:#16201C;border-color:#16201C;color:#F2EDE1}}
.btn{{font:inherit;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 20px;border-radius:2px;border:1.5px solid #16201C;background:#16201C;color:#F2EDE1;font-weight:700;font-size:16px;text-decoration:none}}
.btn:hover{{background:#0E1B17;color:#F2EDE1}}
.btn.hot{{background:#E8592B;border-color:#E8592B;color:#0E1B17}}
.btn.ghost{{background:transparent;color:#16201C}}
.btn.ghost:hover{{background:#EAE3D3;color:#16201C}}
input,textarea,select{{font:inherit;color:#16201C;background:#fff;border:1.5px solid #B9B09C;border-radius:2px;padding:10px 12px;min-height:46px;width:100%}}
textarea{{min-height:140px;resize:vertical;line-height:1.5}}
.private{{font-size:14px;color:#5A635D;margin:0}}
.toast{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#16201C;color:#F2EDE1;padding:10px 18px;border-radius:2px;font-weight:700;opacity:0;transition:opacity .2s;pointer-events:none;z-index:20}}
.toast.on{{opacity:1}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;animation:none!important}}}}
{wrap_css}
{band_css}
{fold_css}{css}
</style>
</head>
<body>
<div class="dj">

<header style="background:#0E1B17;color:#E9EEE9" class="noprint">
  <div class="wrap">
    <nav aria-label="Main" style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px;padding:26px 0">
      <a href="index.html" style="display:inline-flex;align-items:center;gap:10px;min-height:44px;color:#E9EEE9;text-decoration:none">
        <svg width="28" height="28" viewBox="0 0 34 34" aria-hidden="true"><path d="M4 28 L13 10 L19 20 L23 14 L30 28 Z" fill="none" stroke="#E9EEE9" stroke-width="1.8" stroke-linejoin="round"/><circle cx="23" cy="7" r="2.4" fill="#E8592B"/></svg>
        <span style="font-weight:700;font-size:18px">Dragoman's Journey</span>
      </a>
      <div style="display:flex;flex-wrap:wrap;align-items:center;gap:18px;font-size:15px">
        <a href="work.html" style="color:#C9D2CB;text-decoration:none">The work</a>
        <a href="local.html" style="color:#C9D2CB;text-decoration:none">Local Route</a>
        <a href="studio.html" style="color:#C9D2CB;text-decoration:none"{studio_cur}>Studio</a>
        <a href="work.html#free" style="color:#C9D2CB;text-decoration:none">Free tools</a>
        <a href="call.html" style="display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border:1.5px solid #4C5F56;color:#E9EEE9;text-decoration:none;font-weight:600;border-radius:2px">Free 15-min call</a>
      </div>
    </nav>
    <div style="padding:clamp(24px,4vw,52px) 0 clamp(36px,5vw,64px);display:flex;flex-direction:column;gap:16px;max-width:880px">
      {kick}<h1 class="big" style="font-size:clamp(52px,7.4vw,104px)">{h1}</h1>{badge}
      <p style="margin:0;max-width:56ch;font-size:clamp(18px,1.6vw,21px);color:#C9D2CB">{lede}</p>
    </div>
  </div>
</header>

<main class="wrap" style="padding-top:clamp(32px,4.5vw,56px);padding-bottom:clamp(64px,8vw,112px);display:flex;flex-direction:column;gap:24px">
{body}
{tail}</main>

<footer class="wrap noprint" style="padding-top:28px;padding-bottom:40px;border-top:1px solid #C9C1AE;display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;font-size:14px;color:#5A635D">
  <span>Dragoman's Journey · Santa Rosa, California</span>
  <a href="mailto:hello@dragomansjourney.com" style="color:#3B4540">hello@dragomansjourney.com</a>
</footer>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
function djToast(t){{var e=document.getElementById('toast');e.textContent=t;e.classList.add('on');clearTimeout(djToast.t);djToast.t=setTimeout(function(){{e.classList.remove('on')}},1600)}}
function djCopy(text,label){{
  var done=function(){{djToast((label||'Text')+' copied')}};
  if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(text).then(done,fallback)}}else fallback();
  function fallback(){{var ta=document.createElement('textarea');ta.value=text;document.body.appendChild(ta);ta.select();try{{document.execCommand('copy');done()}}catch(e){{djToast('Select it and copy by hand')}}ta.remove()}}
}}
{nw_js}
{fold_js}{script}
</script>
</body>
</html>
"""

# The tools, by the names the work page gives them (T-02). Each tool page links the others.
# Website checkup added Nov 12, 2026 (T-04).
# T-33 R20, R21 (Nov 20, 2026): the Busywork receipt first, then the reel engine's two tools;
# the recipe scaler is off the lists (it lives in the kids' app story on the work page, and
# scaler.html stays as it is). This order is the "More free tools" row on every tool page and
# the order of the tools on local.html, which groups the reel engine's pair as work.html does.
# T-35 (Nov 21, 2026, R17): the voice checker joins, linked from day one. The order is R16's:
# the website checkup (still hidden while CHECKUP_URL is empty), the voice checker, the
# Busywork receipt, then the reel engine's pair.
TOOLS = (("checkup.html", "Website checkup"), ("voicecheck.html", "Voice checker"),
         ("receipt.html", "Busywork receipt"), ("shotlist.html", "Reel shot list"),
         ("captions.html", "Caption fitter"))


# The website checkup is linked only once it is live (T-20 F2, Nov 15, 2026). The one
# switch is CHECKUP_URL at the top of checkup.py's script: while it is empty, no page
# links to checkup.html or lists it, and the sitemap leaves it out. Every build script
# reads it from there through checkup_url(); nothing else holds a copy.
def checkup_url():
    src = (pathlib.Path(__file__).resolve().parent / "checkup.py").read_text(encoding="utf-8")
    found = re.findall(r"""^var CHECKUP_URL = (['"])(.*?)\1;""", src, re.M)
    assert len(found) == 1, "checkup.py: expected one CHECKUP_URL line, found " + str(len(found))
    return found[0][1].strip()


def checkup_live():
    return bool(checkup_url())


def linked_tools():
    return tuple(t for t in TOOLS if t[0] != "checkup.html" or checkup_live())


# T-23 L4: each tool's name holds one line (G1's no-wrap span), so the line can break only
# between names, and G2 still holds: no line starts or ends with " · ". Each name after the
# first carries its separator in front of it, in a box MT_SEP wide; the list sits MT_SEP
# left of the text column (its first line indented back), inside a box that clips there, so
# the separator in front of a name that starts a new row is outside the box and never shows.
# The label stays with the first name. Same words, same dots, same no-break spaces.
MT_SEP = 20     # px: wider than "&nbsp;·&nbsp;" at 15 px
MT_PAD = 6      # px of room left of the column for a link's focus ring (3 px + 3 px offset)


def more_tools(slug):
    names = [f'<a href="{href}">{NOWRAP}{name}</span></a>' for href, name in linked_tools() if href != slug]
    sep = (f'<span style="display:inline-block;width:{MT_SEP}px;text-align:center;text-indent:0">'
           '&nbsp;·&nbsp;</span>')
    return (f'<span style="display:block;margin-left:-{MT_SEP}px;text-indent:{MT_SEP}px">'
            f'{NOWRAP}More free tools: {names[0]}</span>'
            + "".join(f'<wbr>{NOWRAP}{sep}{n}</span>' for n in names[1:]) + '</span>')


# Under the tool: the line to the other tools and the dark panel. A page without
# cta_h (the Studio page, T-08) gets neither. A page with more_line and no cta_h (the voice
# checker, T-35, which ends on its own closing line) gets the line only.
MORE_LINE = """  <p class="noprint" style="margin:4px 0 -4px -{mt_pad}px;padding:4px 0 4px {mt_pad}px;overflow:hidden;font-size:15px;line-height:2;color:#5A635D">{more}</p>
"""
TAIL = MORE_LINE + """  <section aria-labelledby="more-h" class="noprint" style="margin-top:16px;background:#16201C;color:#E9EEE9;padding:clamp(26px,4vw,44px);display:grid;grid-template-columns:repeat(auto-fit,minmax(min(380px,100%),1fr));gap:20px 48px;align-items:center;border-radius:2px">
    <div style="display:flex;flex-direction:column;gap:10px">
      <h2 id="more-h" class="big" style="font-size:clamp(34px,4.4vw,56px)">{cta_h}</h2>
      <p style="margin:0;font-size:18px;color:#C9D2CB">{cta_p}</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:12px">
      <a href="{cta_href}" style="display:inline-flex;align-items:center;min-height:56px;padding:0 24px;background:#E8592B;color:#0E1B17;text-decoration:none;font-weight:700;border-radius:2px">{cta_btn}</a>
    </div>
  </section>
"""


# A folded section (T-18, Nov 13, 2026): a real button with aria-expanded that
# opens and closes the block it controls, closed on load, 48 px tall. A block
# with class "printopen" holds part of the answer, so it prints open.
FOLD_CSS = """.fold{font:inherit;cursor:pointer;display:inline-flex;align-items:center;gap:12px;min-height:48px;padding:0;margin:0;background:none;border:0;color:#A93F17;font-size:16px;font-weight:700;text-align:left;text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:5px}
.fold:hover{color:#16201C}
.fold::after{content:'';flex:none;width:8px;height:8px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:translateY(-3px) rotate(45deg)}
.fold[aria-expanded="true"]::after{transform:translateY(2px) rotate(-135deg)}
@media print{.fold{display:none!important}.printopen[hidden]{display:block!important}}
"""
FOLD_JS = """document.addEventListener('click',function(e){var b=e.target.closest('.fold[aria-controls]');if(!b)return;var o=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(o));document.getElementById(b.getAttribute('aria-controls')).hidden=!o});
"""


def page(**k):
    for key in ("css", "script", "badge"):          # badge: right under the h1 (a Studio product's status, T-09)
        k.setdefault(key, "")
    folds = k.pop("folds", False)
    k["fold_css"] = FOLD_CSS if folds else ""
    k["fold_js"] = FOLD_JS if folds else ""
    k["wrap_css"] = WRAP_CSS
    k["band_css"] = BAND_CSS if k.get("cta_h") else ""
    k["nw_js"] = NW_JS
    for key in ("cta_h", "cta_p", "cta_btn"):   # T-21 G1, G2
        if k.get(key):
            k[key] = nobreak(k[key])
    if "<span" in k.get("cta_btn", ""):
        k["cta_btn"] = "<span>" + k["cta_btn"] + "</span>"   # the button is a flex box: one item
    if k.get("more"):
        k["more"] = keep_dots(k["more"])
    k["mt_pad"] = MT_PAD
    k["tail"] = (TAIL.format(**k) if k.get("cta_h")
                 else MORE_LINE.format(**k) if k.pop("more_line", False) else "")
    k["studio_cur"] = ' aria-current="page"' if k.get("slug") == "studio.html" else ""
    # The small line over the title; a page without one (the Studio, T-16) gets no empty span.
    k["kick"] = f'<span class="kick">{k["kicker"]}</span>\n      ' if k.get("kicker") else ""
    return HEAD.format(**k)

def write(out_dir, slug, **k):
    k.setdefault("more", more_tools(slug))
    html = page(slug=slug, og=slug[:-len(".html")], **k)   # share card from tools/og.py
    assert "—" not in html, "em dash in " + slug
    p = pathlib.Path(out_dir) / slug
    p.write_text(html, encoding="utf-8")
    print("wrote", p, len(html))
