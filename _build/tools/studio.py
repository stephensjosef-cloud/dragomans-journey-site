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
- The hero names the album only while the album card shows: "lede" then,
  "lede_album_gated" while the album has a gate.
- A join list opens a mailto with the subject "List: <product name>" until the
  real join lists (T-10) are live. Its count shows only at 10 or more.

Product pages (T-09): each open product with a join list also gets
studio-<id>.html: its name, status, what, proof, image, all of its log lines
that show, and one join box with the line from its list ("line"). Its card
links there ("See it move"). A page whose
product is gated or loses its list is deleted here. og.py, build.py (sitemap)
and enhance.py all take the page list from product_pages().

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
MOVE = "See it move"                     # a card's link to its product page (T-09)


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


def album_shown(studio):
    return any(p["id"] == "album" and p.get("gate") is None for p in studio["products"])


def hero_lede(studio):
    """The hero names the album only while the album card shows (approved Nov 11, 2026)."""
    hero = studio["hero"]
    return hero["lede"] if album_shown(studio) else hero["lede_album_gated"]


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


def log_item(r, today, more=False, label=True):
    return (f'\n      <li{" hidden data-more" if more else ""}>'
            f'<time class="mono" datetime="{r["date"]}">{short_date(r["day"], today)}</time>'
            + (f'<span class="proj">{t(r["label"])}</span>' if label else '')
            + f'<span class="line">{t(r["line"])}</span></li>')


def page_slug(p):
    """Each open product with a join list gets its own page (T-09). None for the rest."""
    return f'studio-{p["id"]}.html' if p.get("gate") is None and p.get("list") else None


def product_pages(studio):
    return [(page_slug(p), p) for p in studio["products"] if page_slug(p)]


def join_button(p):
    lst = p["list"]
    subject = quote(f'List: {p["name"]}', safe="")
    out = [f'<a class="btn hot" data-list="{a(lst["id"])}" href="mailto:{EMAIL}?subject={subject}">{t(lst["button"])}</a>']
    if lst.get("count", 0) >= COUNT_FROM:
        out.append(f'<span class="count">{lst["count"]} people on the list</span>')
    return out


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
    if page_slug(p):
        acts.append(f'<a class="go" data-page href="{page_slug(p)}">{MOVE} →</a>')
    if p.get("list"):
        acts += join_button(p)
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


PAGE_CSS = r"""
.kick a{display:inline-flex;align-items:center;min-height:44px;color:inherit;text-decoration:underline;text-underline-offset:3px}
.kick a:hover{color:#E9EEE9}
.hero-pill{align-self:flex-start;display:inline-flex;align-items:center;min-height:30px;padding:0 14px;border-radius:999px;background:#E9EEE9;color:#0E1B17;font-size:14px;font-weight:700}
.top{display:grid;grid-template-columns:minmax(0,1fr);gap:24px 40px;align-items:start}
.top .proof{margin:0;font-size:clamp(20px,2vw,24px);line-height:1.4}
.top img{width:100%;max-width:560px;height:auto;display:block;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
@media (min-width:800px){.top.has-img{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
.log.solo li{grid-template-columns:5.5em minmax(0,1fr)}
@media (max-width:760px){.log.solo li{grid-template-columns:4.2em minmax(0,1fr);gap:4px 12px}.log.solo .line{grid-column:auto}}
.join{display:flex;flex-direction:column;align-items:flex-start;gap:12px;margin-top:24px;max-width:560px}
.join .acts{display:flex;flex-wrap:wrap;align-items:center;gap:10px 20px}
"""


def product_page(p, rows, today, stamp):
    """One product's page (T-09): name, status, what, proof, image, its own log, one join box."""
    parts = [stamp]
    proof = f'<p class="proof"><strong>{t(p["proof"])}</strong></p>' if p.get("proof") else ""
    img = (f'<img src="{a(p["image"])}" width="1200" height="1331" alt="{a(p["image_alt"] or "")}">'
           if p.get("image") else "")
    if proof or img:
        parts.append(f'\n  <div class="top{" has-img" if img else ""}">'
                     + (f'\n    {proof}' if proof else "") + (f'\n    {img}' if img else "") + '\n  </div>')
    mine = [r for r in rows if r["project"] == p["id"]]
    if mine:
        items = "".join(log_item(r, today, label=False) for r in mine)
        parts.append(f'\n  <section class="sec" aria-labelledby="log-h">'
                     f'\n    <h2 id="log-h" class="big">Shipped lately</h2>'
                     f'\n    <ol class="log solo" id="log">{items}\n    </ol>'
                     '\n  </section>')
    parts.append(f'\n  <section class="join panel" id="join">'
                 f'\n    <div class="acts">{"".join(join_button(p))}</div>'
                 f'\n    <p class="private">{t(p["list"]["line"])}</p>'
                 '\n  </section>\n')
    return "".join(parts)


def main(out_dir):
    studio, shipped = load()
    today = la_today()
    hero = studio["hero"]
    body = build(studio, shipped, today)
    kicker = hero["kicker"]
    lede = hero_lede(studio)
    stamp = f'<!-- studio.py {today.isoformat()} {fingerprint()} -->'
    from chrome import write
    write(out_dir, "studio.html",
          title=kicker.split(" · ")[0],                       # "The studio", from the kicker
          description=lede.replace('"', "&quot;"),
          kicker=t(kicker), h1=hero["h1"], lede=t(lede),
          css=CSS, body=stamp + body, script=SCRIPT, more="")
    # One page per open product with a join list (T-09). A page whose product
    # closed or lost its list is removed, so it can't be copied into the site.
    rows = visible(studio, shipped, today)
    keep = set()
    for slug, p in product_pages(studio):
        keep.add(slug)
        write(out_dir, slug,
              title=t(p["name"]),
              description=a(p["what"]),
              kicker=f'<a href="studio.html">{t(kicker.split(" · ")[0])}</a> · {t(p["kind"])}',
              h1=t(p["name"]),
              badge=f'\n      <span class="hero-pill">{t(p["status"])}</span>',
              lede=t(p["what"]),
              css=CSS + PAGE_CSS, body=product_page(p, rows, today, stamp), more="")
    for old in pathlib.Path(out_dir).glob("studio-*.html"):
        if old.name not in keep:
            old.unlink()
            print("removed", old)


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
