"""Shared page chrome for the Dragoman's Journey free tools.
Each tool supplies: slug, title, description, kicker, h1 (may contain <br>), lede, css, body, script.
Output is a standalone page written into _build/ (the pipeline copies it to the site)."""
import pathlib, sys

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
{css}
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
      <span class="kick">{kicker}</span>
      <h1 class="big" style="font-size:clamp(52px,7.4vw,104px)">{h1}</h1>
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
{script}
</script>
</body>
</html>
"""

# The four tools, by the names the work page gives them (T-02). Each tool page links the other three.
TOOLS = (("shotlist.html", "Reel shot list"), ("captions.html", "Caption fitter"),
         ("receipt.html", "Busywork receipt"), ("scaler.html", "Recipe scaler"))


def more_tools(slug):
    return " · ".join(f'<a href="{href}">{name}</a>' for href, name in TOOLS if href != slug)


# Under the tool: the line to the other tools and the dark panel. A page without
# cta_h (the Studio page, T-08) gets neither.
TAIL = """  <p class="noprint" style="margin:8px 0 0;font-size:15px;line-height:2;color:#5A635D">More free tools: {more}</p>
  <section aria-labelledby="more-h" class="noprint" style="margin-top:16px;background:#16201C;color:#E9EEE9;padding:clamp(26px,4vw,44px);display:grid;grid-template-columns:repeat(auto-fit,minmax(min(380px,100%),1fr));gap:20px 48px;align-items:center;border-radius:2px">
    <div style="display:flex;flex-direction:column;gap:10px">
      <h2 id="more-h" class="big" style="font-size:clamp(34px,4.4vw,56px)">{cta_h}</h2>
      <p style="margin:0;font-size:18px;color:#C9D2CB">{cta_p}</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:12px">
      <a href="{cta_href}" style="display:inline-flex;align-items:center;min-height:56px;padding:0 24px;background:#E8592B;color:#0E1B17;text-decoration:none;font-weight:700;border-radius:2px">{cta_btn}</a>
      <a href="work.html#free" style="display:inline-flex;align-items:center;min-height:56px;padding:0 22px;border:1.5px solid #4C5F56;color:#E9EEE9;text-decoration:none;font-weight:600;border-radius:2px">More free tools</a>
    </div>
  </section>
"""


def page(**k):
    for key in ("css", "script"):
        k.setdefault(key, "")
    k["tail"] = TAIL.format(**k) if k.get("cta_h") else ""
    k["studio_cur"] = ' aria-current="page"' if k.get("slug") == "studio.html" else ""
    return HEAD.format(**k)

def write(out_dir, slug, **k):
    k.setdefault("more", more_tools(slug))
    html = page(slug=slug, og=slug[:-len(".html")], **k)   # share card from tools/og.py
    assert "—" not in html, "em dash in " + slug
    p = pathlib.Path(out_dir) / slug
    p.write_text(html, encoding="utf-8")
    print("wrote", p, len(html))
