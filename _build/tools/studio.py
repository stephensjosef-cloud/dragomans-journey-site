#!/usr/bin/env python3
"""The Studio page and the public build log (trip item T-08, Nov 11, 2026).

    cd _build/tools && python3 studio.py ..

Writes _build/studio.html from _build/studio.json (the products) and
_build/shipped.json (the dated build log, newest first), with the shared
header and footer from chrome.py. Every word on the page comes from those two
files; this script adds only numbers, dates and arrows.

Rules:
- A product with a non-null "gate" does not render, and neither do its log lines.
- Log lines older than 120 days (America/Los_Angeles) drop off at build time.
  The numbers strip counts the lines that are left, so it always agrees with
  the list under it.
- "Shipped lately" shows the 8 newest; "See all <N>" reveals the rest in place.
- Each log line carries a small label: its project's product name, or the
  site's own address for project "site".
- A join list opens a mailto with the subject "List: <product name>" until the
  real join lists (T-10) are live. Its count shows only at 10 or more.

enhance.py copies studio.html into the site, and refuses to if either JSON
file changed since this script last ran. enhance.py also uses visible() and
LABELS here for the band on the home page.
"""
import datetime
import hashlib
import html
import json
import pathlib
import sys
from urllib.parse import quote

HERE = pathlib.Path(__file__).resolve().parent.parent      # _build/
STUDIO = HERE / "studio.json"
SHIPPED = HERE / "shipped.json"
EMAIL = "hello@dragomansjourney.com"
KEEP_DAYS = 120
RECENT_DAYS = 30
FIRST = 8
COUNT_FROM = 10
SITE_LABEL = "dragomansjourney.com"      # label for project "site": the site's own address


def la_today():
    """Today in America/Los_Angeles, with or without a time zone database."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:
        # US Pacific: UTC-7 from the second Sunday in March, 2 AM, to the first Sunday in November, 2 AM.
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        y = now.year
        mar = datetime.datetime(y, 3, 8 + (6 - datetime.date(y, 3, 8).weekday()) % 7, 10)   # 2 AM PST in UTC
        nov = datetime.datetime(y, 11, 1 + (6 - datetime.date(y, 11, 1).weekday()) % 7, 9)  # 2 AM PDT in UTC
        return (now - datetime.timedelta(hours=7 if mar <= now < nov else 8)).date()


def load():
    return (json.loads(STUDIO.read_text(encoding="utf-8")),
            json.loads(SHIPPED.read_text(encoding="utf-8")))


def fingerprint():
    # Line endings don't count, so a Windows checkout and a Linux one agree.
    data = "\0".join(f.read_text(encoding="utf-8").replace("\r\n", "\n") for f in (STUDIO, SHIPPED))
    h = hashlib.sha256(data.encode("utf-8"))
    return h.hexdigest()[:16]


def labels(studio):
    out = {p["id"]: p["name"] for p in studio["products"] if p.get("gate") is None}
    out["site"] = SITE_LABEL
    return out


def gated(studio):
    return {p["id"] for p in studio["products"] if p.get("gate") is not None}


def visible(studio, shipped, today):
    """Log lines that show: not from a gated product, not older than 120 days. Newest first."""
    cut = today - datetime.timedelta(days=KEEP_DAYS)
    hide = gated(studio)
    names = labels(studio)
    rows = []
    for e in shipped["entries"]:
        d = datetime.date.fromisoformat(e["date"])
        if e["project"] in hide or d < cut:
            continue
        assert e["project"] in names, f'shipped.json: no product or label for project "{e["project"]}"'
        assert "—" not in e["line"], "em dash in shipped.json: " + e["line"]
        rows.append(dict(e, day=d, label=names[e["project"]]))
    rows.sort(key=lambda r: r["day"], reverse=True)          # stable: file order kept within a day
    return rows


def short_date(d, today):
    s = f"{d.strftime('%b')} {d.day}"
    return s if d.year == today.year else f"{s}, {d.year}"


def numbers(rows, today):
    since = today - datetime.timedelta(days=RECENT_DAYS)
    n = len(rows)
    m = sum(1 for r in rows if r["day"] > since)
    k = len({r["project"] for r in rows})
    oldest = min(r["day"] for r in rows)
    return n, m, k, oldest


def t(s):
    return html.escape(s, quote=False)


def a(s):
    return html.escape(s, quote=False).replace('"', "&quot;")


def log_item(r, today, more=False):
    return (f'\n      <li{" hidden data-more" if more else ""}>'
            f'<time class="mono" datetime="{r["date"]}">{short_date(r["day"], today)}</time>'
            f'<span class="proj">{t(r["label"])}</span>'
            f'<span class="line">{t(r["line"])}</span></li>')


def product_card(p):
    feature = bool(p.get("image"))
    parts = [f'<h2>{t(p["name"])}</h2>',
             f'<div class="meta"><span class="pill">{t(p["status"])}</span><span class="kind mono">{t(p["kind"])}</span></div>',
             f'<p>{t(p["what"])}</p>']
    if p.get("proof"):
        parts.append(f'<p class="proof"><strong>{t(p["proof"])}</strong></p>')
    acts = []
    if p.get("link"):
        href = p["link"]["href"]
        arrow = "↗" if href.startswith("http") else "→"
        acts.append(f'<a class="go" href="{a(href)}">{t(p["link"]["label"])} {arrow}</a>')
    lst = p.get("list")
    if lst:
        subject = quote(f'List: {p["name"]}', safe="")
        acts.append(f'<a class="btn hot" data-list="{a(lst["id"])}" href="mailto:{EMAIL}?subject={subject}">{t(lst["button"])}</a>')
        if lst.get("count", 0) >= COUNT_FROM:
            acts.append(f'<span class="count">{lst["count"]} people on the list</span>')
    if acts:
        parts.append('<div class="acts">' + "".join(acts) + '</div>')
    body = "\n        ".join(parts)
    if not feature:
        return f'\n    <article class="prod" data-id="{a(p["id"])}">\n        {body}\n    </article>'
    img = (f'<img src="{a(p["image"])}" width="1200" height="1331" loading="lazy" alt="{a(p["image_alt"] or "")}">')
    return (f'\n    <article class="prod feature" data-id="{a(p["id"])}">\n      <div class="fb">\n        {body}\n      </div>\n      {img}\n    </article>')


CSS = r"""
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-top:2px solid #16201C;border-bottom:1px solid #CFC6B2}
.stats p{margin:0;padding:18px 20px 18px 0;font-size:17px;color:#3B4540}
.stats p+p{border-left:1px solid #CFC6B2;padding-left:20px}
.stats strong{display:block;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:clamp(48px,5.4vw,68px);line-height:.9;color:#C2461B}
@media (max-width:760px){.stats p{padding:14px 10px 14px 0;font-size:14px;line-height:1.35}.stats p+p{padding-left:10px}}
.sec{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.sec h2.big{font-size:clamp(38px,4.6vw,60px)}
.log{list-style:none;margin:0;padding:0;border-top:1px solid #16201C}
.log li{display:grid;grid-template-columns:5.5em 13em minmax(0,1fr);gap:4px 18px;align-items:baseline;padding:14px 0;border-bottom:1px solid #DDD5C3}
.log time{font-size:14px;color:#6B716A;white-space:nowrap}
.log .proj{justify-self:start;font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.04em;padding:3px 9px;background:#EAE3D3;color:#3B4540;border-radius:2px}
.log .line{font-size:17px}
@media (max-width:760px){.log li{grid-template-columns:auto minmax(0,1fr)}.log .line{grid-column:1/-1}}
#log-all{align-self:flex-start}
.prods{display:grid;grid-template-columns:minmax(0,1fr);gap:18px}
@media (min-width:800px){.prods{grid-template-columns:repeat(2,minmax(0,1fr))}}
.prod{display:flex;flex-direction:column;gap:12px;padding:clamp(22px,2.6vw,30px);background:#FBF8F1;border:1.5px solid #CFC6B2;border-radius:2px}
.prod h2{margin:0;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(34px,3.4vw,44px);line-height:.95}
.prod p{margin:0;font-size:16px;color:#3B4540}
.prod .proof strong{color:#16201C}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px}
.pill{display:inline-flex;align-items:center;min-height:28px;padding:0 12px;border-radius:999px;background:#16201C;color:#F2EDE1;font-size:13px;font-weight:600}
.kind{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#6B716A}
.acts{margin-top:auto;padding-top:8px;display:flex;flex-wrap:wrap;align-items:center;gap:10px 20px}
.prod a.go{display:inline-flex;align-items:center;min-height:44px;font-weight:700;text-decoration:none;color:#16201C}
.prod a.go:hover{color:#A93F17}
.count{font-size:14px;color:#5A635D}
.prod.feature{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);gap:20px 36px;align-items:center}
.prod.feature .fb{display:flex;flex-direction:column;gap:12px}
.prod.feature .acts{margin-top:8px}
.prod.feature img{width:100%;height:auto;display:block;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
@media (min-width:800px){.prod.feature{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}}
"""

SCRIPT = r"""
(function(){
var b=document.getElementById('log-all');
if(!b)return;
b.addEventListener('click',function(){
  document.querySelectorAll('#log li[data-more]').forEach(function(li){li.hidden=false});
  b.setAttribute('aria-expanded','true');
  b.hidden=true;
});
})();
"""


def build(studio, shipped, today):
    rows = visible(studio, shipped, today)
    assert rows, "shipped.json: nothing to show in the last 120 days"
    n, m, k, oldest = numbers(rows, today)
    strip = (f'\n  <div class="stats" id="stats" data-built="{today.isoformat()}">'
             f'\n    <p><strong>{n}</strong> {"thing" if n == 1 else "things"} shipped since {short_date(oldest, today)}</p>'
             f'\n    <p><strong>{m}</strong> in the last {RECENT_DAYS} days</p>'
             f'\n    <p><strong>{k}</strong> {"project" if k == 1 else "projects"}</p>'
             '\n  </div>')
    items = "".join(log_item(r, today, i >= FIRST) for i, r in enumerate(rows))
    toggle = (f'\n    <button type="button" id="log-all" class="btn ghost" aria-controls="log" aria-expanded="false">See all {n}</button>'
              if n > FIRST else "")
    log = (f'\n  <section class="sec" aria-labelledby="log-h">'
           f'\n    <h2 id="log-h" class="big">Shipped lately</h2>'
           f'\n    <ol class="log" id="log">{items}\n    </ol>{toggle}'
           '\n  </section>')
    cards = "".join(product_card(p) for p in studio["products"] if p.get("gate") is None)
    prods = f'\n  <div class="sec prods" id="products">{cards}\n  </div>'
    return strip + log + prods + "\n"


def main(out_dir):
    studio, shipped = load()
    today = la_today()
    hero = studio["hero"]
    body = build(studio, shipped, today)
    kicker = hero["kicker"]
    body = f'<!-- studio.py {today.isoformat()} {fingerprint()} -->' + body
    from chrome import write
    write(out_dir, "studio.html",
          title=kicker.split(" · ")[0],                       # "The studio", from the kicker
          description=hero["lede"].replace('"', "&quot;"),
          kicker=t(kicker), h1=hero["h1"], lede=t(hero["lede"]),
          css=CSS, body=body, script=SCRIPT, more="")


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
