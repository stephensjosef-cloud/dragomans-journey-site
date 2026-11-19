#!/usr/bin/env python3
"""The Studio page and the public build log (trip item T-08, Nov 11, 2026).

    cd _build/tools && python3 studio.py ..

Writes _build/studio.html from _build/studio.json (the products) and
_build/shipped.json (the dated build log, newest first), with the shared
header and footer from chrome.py. Every word on the page comes from those two
files; this script adds only numbers, dates and arrows.

Rules:
- A product with a non-null "gate" does not render, and neither do its log lines.
- A product whose "what" is null prints no description line on its card (T-30): its
  description lives on work.html, and the card keeps its name, pill, proof and links.
- Log lines older than 120 days (America/Los_Angeles) drop off at build time.
  The count over the log ("<n> things finished since <date>") counts the lines
  that are left, so it always agrees with the list under it.
- "Shipped lately" shows the 8 newest; "See all <N>" reveals the rest in place.
- Each log line carries a small label: its project's product name, or the
  site's own address for project "site".
- The hero shows only "intro" (T-16). The meta description names the album
  only while the album card shows: "lede" then, "lede_album_gated" while the
  album has a gate. The kicker and each product's "kind" stay in the JSON but
  aren't printed (T-16); the page title is the kicker's first part.
- A join list is a small form (T-10): an email field and the list's button.
  It posts {form: "list", fields: {email, list}} to the intake Worker the same
  way start.html does (honeypot, time since load), says "You're on the list"
  when the Worker answers ok, and otherwise opens the mailto it used before,
  subject "List: <product name>". That mailto is also the form's action, so
  the box still works with scripts off. Its count shows only at 10 or more.

Product pages (T-09): each open product with a join list also gets
studio-<id>.html: its name, status, what, proof, image, all of its log lines
that show, and one join box with the line from its list ("line"). Its card
links there ("More on <name>", T-16) and the page links back ("← The Studio"). A page whose product is gated or loses its list is deleted here. og.py, build.py (sitemap)
and enhance.py all take the page list from product_pages().

Gallery (T-26): one section on studio.html, from studio.json's "gallery" and the
images in _build/assets/gallery/ (see gallery()). T-29: it comes right after the
build log, before the product cards. A gallery app with a "product" carries that
product's card words at the top of its block (app_intro()), and the product gets no
card on studio.html; its own page (studio-<id>.html) is unchanged.

Shelf (T-27): the ChuckleFits card's products, from that product's "shelf" in
studio.json and the photos in _build/assets/shelf/ (see shelf()).

enhance.py copies studio.html into the site, and refuses to if either JSON
file changed since this script last ran.
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
FIRST = 8
COUNT_FROM = 10
SITE_LABEL = "dragomansjourney.com"      # label for project "site": the site's own address
MORE = "More on {name}"                  # a card's link to its product page (T-09, words T-16)
BACK = "← The Studio"                    # a product page's link back to the Studio (T-16)
ENDPOINT = "https://dj-intake.stephens-josef.workers.dev/"   # the intake Worker, same as start.html (T-10)
JOINED = "You're on the list"            # a join box after the Worker says ok (T-10)


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


def numbers(rows):
    return len(rows), min(r["day"] for r in rows)


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
    """The join box (T-10): email field and the list's button, posted by JOIN_SCRIPT."""
    lst = p["list"]
    subject = quote(f'List: {p["name"]}', safe="")
    out = [f'<form class="jf" data-list="{a(lst["id"])}" action="mailto:{EMAIL}?subject={subject}" method="post" enctype="text/plain">'
           '<div class="hp" aria-hidden="true"><label>Website <input name="website" tabindex="-1" autocomplete="off"></label></div>'
           '<label class="jf-e"><span>Email</span><input name="email" type="email" autocomplete="email" required></label>'
           f'<button type="submit" class="btn hot">{t(lst["button"])}</button>'
           '<div class="jf-ok" role="status"></div></form>']
    if lst.get("count", 0) >= COUNT_FROM:
        out.append(f'<span class="count">{lst["count"]} people on the list</span>')
    return out


def product_card(p, wide=False):
    feature = bool(p.get("image"))
    parts = [f'<h2>{t(p["name"])}</h2>',
             f'<div class="meta"><span class="pill">{t(p["status"])}</span></div>']
    # T-30: a product whose "what" is null prints no line here; its description lives on work.html.
    if p.get("what"):
        parts.append(f'<p>{t(p["what"])}</p>')
    if p.get("proof"):
        parts.append(f'<p class="proof"><strong>{t(p["proof"])}</strong></p>')
    if p.get("shelf"):
        parts.append(shelf(p))
    acts = []
    if p.get("link"):
        href = p["link"]["href"]
        if p.get("link_tag"):                          # T-27: the shop link carries the tag
            href = href.rstrip("/") + "/?" + p["link_tag"]
        arrow = "↗" if href.startswith("http") else "→"
        acts.append(f'<a class="go" href="{a(href)}">{t(p["link"]["label"])} {arrow}</a>')
    if page_slug(p):
        acts.append(f'<a class="go" data-page href="{page_slug(p)}">{t(MORE.format(name=p["name"]))} →</a>')
    if p.get("list"):
        acts += join_button(p)
    if acts:
        parts.append('<div class="acts">' + "".join(acts) + '</div>')
    body = "\n        ".join(parts)
    if not feature:
        cls = "prod wide" if wide else "prod"
        return f'\n    <article class="{cls}" data-id="{a(p["id"])}">\n        {body}\n    </article>'
    img = (f'<img src="{a(p["image"])}" width="1200" height="1331" loading="lazy" alt="{a(p["image_alt"] or "")}">')
    return (f'\n    <article class="prod feature" data-id="{a(p["id"])}">\n      <div class="fb">\n        {body}\n      </div>\n      {img}\n    </article>')


CSS = r"""
.stats{border-top:2px solid #16201C;border-bottom:1px solid #CFC6B2}
.stats p{margin:0;padding:18px 0;font-size:17px;color:#3B4540}
.stats strong{display:block;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;font-size:clamp(48px,5.4vw,68px);line-height:.9;color:#C2461B}
@media (max-width:760px){.stats p{padding:14px 0}}
.sec{display:flex;flex-direction:column;gap:18px;margin-top:24px}
.sec h2.big{font-size:clamp(38px,4.6vw,60px)}
.logsec{margin-top:0}
.loghead{display:flex;flex-direction:column;gap:48px}
@media (min-width:800px){.loghead{flex-direction:row-reverse;flex-wrap:wrap-reverse;justify-content:flex-end;align-items:baseline;gap:8px clamp(24px,3vw,40px)}
.loghead .stats{border:0}.loghead .stats p{padding:0}
.loghead .stats strong{display:inline;font-size:clamp(38px,4.6vw,60px);margin-right:.18em}}
.log{list-style:none;margin:0;padding:0;border-top:1px solid #16201C}
.log li{display:grid;grid-template-columns:5.5em 13em minmax(0,1fr);gap:4px 18px;align-items:baseline;padding:14px 0;border-bottom:1px solid #DDD5C3}
.log time{font-size:14px;color:#676D66;white-space:nowrap}
.log .proj{justify-self:start;font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.04em;padding:3px 9px;background:#EAE3D3;color:#3B4540;border-radius:2px}
.log .line{font-size:17px}
@media (max-width:760px){.log li{grid-template-columns:auto minmax(0,1fr)}.log .line{grid-column:1/-1}}
#log-all{align-self:flex-start}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.jf{flex:1 1 100%;display:flex;flex-wrap:wrap;align-items:flex-end;gap:10px 12px}
.jf-e{flex:1 1 220px;max-width:340px;display:flex;flex-direction:column;gap:6px}
.jf-e span{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#6B716A}
.jf-e input{min-height:48px}
.jf-ok{flex:1 1 100%;font-weight:700;color:#16201C}
.jf-ok:empty{display:none}
.jf.done .jf-e,.jf.done button{display:none}
.prods{display:grid;grid-template-columns:minmax(0,1fr);gap:18px}
@media (min-width:800px){.prods{grid-template-columns:repeat(2,minmax(0,1fr))}}
.prod{display:flex;flex-direction:column;gap:12px;padding:clamp(22px,2.6vw,30px);background:#FBF8F1;border:1.5px solid #CFC6B2;border-radius:2px}
.prod h2{margin:0;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(34px,3.4vw,44px);line-height:.95}
.prod p{margin:0;font-size:16px;color:#3B4540}
.prod .proof strong{color:#16201C}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px}
.pill{display:inline-flex;align-items:center;min-height:28px;padding:0 12px;border-radius:999px;background:#16201C;color:#F2EDE1;font-size:13px;font-weight:600}
.acts{margin-top:auto;padding-top:8px;display:flex;flex-wrap:wrap;align-items:center;gap:10px 20px}
.prod a.go{display:inline-flex;align-items:center;min-height:44px;font-weight:700;text-decoration:none;color:#16201C}
.prod a.go:hover{color:#A93F17}
.count{font-size:14px;color:#5A635D}
.prod.wide{grid-column:1/-1}
.prod.feature{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);gap:20px 36px;align-items:center}
.prod.feature .fb{display:flex;flex-direction:column;gap:12px}
.prod.feature .acts{margin-top:8px}
.prod.feature img{width:100%;height:auto;display:block;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
@media (min-width:800px){.prod.feature{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}}
"""

# The join boxes (T-10): post to the intake Worker the way start.html does, with
# its honeypot and its time since load; on any failure, open the box's mailto.
JOIN_SCRIPT = r"""
(function(){
var ENDPOINT='%s';
var loaded=Date.now();
document.querySelectorAll('form.jf').forEach(function(f){
  f.addEventListener('submit',function(ev){
    ev.preventDefault();
    var em=f.querySelector('input[name="email"]');
    em.value=em.value.trim();
    if(!f.reportValidity())return;
    var btn=f.querySelector('button');
    var label=btn.textContent;
    btn.disabled=true;
    btn.textContent='Sending…';
    fetch(ENDPOINT,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({form:'list',fields:{email:em.value,list:f.getAttribute('data-list')},website:f.querySelector('input[name="website"]').value,ms:Date.now()-loaded})
    }).then(function(r){return r.json().then(function(j){return{ok:r.ok&&j.ok};});})
      .catch(function(){return{ok:false};})
      .then(function(res){
        btn.disabled=false;
        btn.textContent=label;
        if(res.ok){f.classList.add('done');f.querySelector('.jf-ok').textContent=%s;return;}
        var m=document.createElement('a');
        m.href=f.getAttribute('action');
        m.hidden=true;
        document.body.appendChild(m);
        m.click();
        m.remove();
      });
  });
});
})();
""" % (ENDPOINT, json.dumps(JOINED))

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
""" + JOIN_SCRIPT


def build(studio, shipped, today):
    rows = visible(studio, shipped, today)
    assert rows, "shipped.json: nothing to show in the last 120 days"
    n, oldest = numbers(rows)
    strip = (f'\n  <div class="stats" id="stats" data-built="{today.isoformat()}">'
             f'\n    <p><strong>{n}</strong> {"thing" if n == 1 else "things"} finished since {short_date(oldest, today)}</p>'
             '\n  </div>')
    items = "".join(log_item(r, today, i >= FIRST) for i, r in enumerate(rows))
    toggle = (f'\n    <button type="button" id="log-all" class="btn ghost" aria-controls="log" aria-expanded="false">See all {n}</button>'
              if n > FIRST else "")
    # T-23 L7: the count sits with "Shipped lately" in one head row. Phones: the band above
    # the heading, as before. From 800 px: beside the heading, on its baseline. The count
    # still comes first in the page, so a screen reader hears it in the same order as before.
    log = (f'\n  <section class="sec logsec" aria-labelledby="log-h">'
           f'\n    <div class="loghead">{strip.replace(chr(10) + "  ", chr(10) + "      ")}'
           f'\n      <h2 id="log-h" class="big">Shipped lately</h2>'
           '\n    </div>'
           f'\n    <ol class="log" id="log">{items}\n    </ol>{toggle}'
           '\n  </section>')
    # T-29: a product named by a gallery app shows inside that app's gallery block, not as a card.
    inside = set(gallery_products(studio))
    shown = [p for p in studio["products"] if p.get("gate") is None and p["id"] not in inside]
    # Two columns from 800 px (T-21 G4): a card alone on its row spans the whole row, so
    # the grid never ends a row with an empty cell. A feature card always spans the row, and
    # so does a card with a shelf (T-29: it spanned it at T-27, its shelf laid out for that).
    wide, run = set(), []
    for p in shown + [None]:
        if p is None or p.get("image") or p.get("shelf"):
            if len(run) % 2:
                wide.add(run[-1]["id"])
            run = []
            if p is not None and p.get("shelf"):
                wide.add(p["id"])
        else:
            run.append(p)
    cards = "".join(product_card(p, p["id"] in wide) for p in shown)
    prods = f'\n  <div class="sec prods" id="products">{cards}\n  </div>'
    # T-29: the gallery right after the build log, then the remaining cards.
    return log + gallery(studio) + prods + "\n"


# T-26 (Nov 18, 2026): the gallery section, after the product cards and before the closing
# call box (enhance.py adds that last in <main>). Every word is in studio.json's "gallery";
# this adds only the step numbers of a group marked "numbered" ("1. ", "2. ", ...). The
# images are _build/assets/gallery/ (enhance.py copies them to gallery/), each <img> with its
# width and height read from the file. On phones each group is one row that scrolls sideways
# inside the page (a focusable region named "<app>, <group>"); from 800 px it wraps into rows.
GALLERY_DIR = HERE / "assets" / "gallery"
SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_size(path):
    """(width, height) from a JPEG's frame header, no image library needed."""
    b = path.read_bytes()
    assert b[:2] == b"\xff\xd8", f"{path.name}: not a JPEG"
    i = 2
    while i + 4 <= len(b):
        assert b[i] == 0xFF, f"{path.name}: bad JPEG marker at {i}"
        m = b[i + 1]
        if m == 0xFF:                       # fill byte
            i += 1
            continue
        i += 2
        if m == 0x01 or 0xD0 <= m <= 0xD7:   # markers with no length
            continue
        if m in SOF:
            return int.from_bytes(b[i + 5:i + 7], "big"), int.from_bytes(b[i + 3:i + 5], "big")
        i += int.from_bytes(b[i:i + 2], "big")
    raise AssertionError(f"{path.name}: no JPEG frame header")


def gallery_products(studio):
    """T-29: {product id: product} for each open product a gallery app names with "product"."""
    by_id = {p["id"]: p for p in studio["products"]}
    out = {}
    for app in (studio.get("gallery") or {}).get("apps", []):
        pid = app.get("product")
        if pid is None:
            continue
        assert pid in by_id, f'studio.json gallery: {app["name"]} names product "{pid}", which isn\'t in "products"'
        if by_id[pid].get("gate") is None:              # a gated product's words stay off the page
            out[pid] = by_id[pid]
    return out


def app_intro(p):
    """T-29: the card's words, inside the app's gallery block, after its h3: the status pill,
    the "what" line, the "proof" line (if any), the "More on <name>" link, then the join box,
    each exactly as the card wrote it (same markup, same join form)."""
    text = [f'<div class="meta"><span class="pill">{t(p["status"])}</span></div>',
            f'<p>{t(p["what"])}</p>']
    if p.get("proof"):
        text.append(f'<p class="proof"><strong>{t(p["proof"])}</strong></p>')
    if page_slug(p):
        text.append(f'<a class="go" data-page href="{page_slug(p)}">{t(MORE.format(name=p["name"]))} →</a>')
    out = ('\n      <div class="gprod">\n        <div class="gtext">\n          '
           + "\n          ".join(text) + '\n        </div>')
    if p.get("list"):
        out += '\n        <div class="gjoin">' + "".join(join_button(p)) + '</div>'
    return out + '\n      </div>'


def gallery(studio):
    g = studio.get("gallery")
    if not g:
        return ""
    inside = gallery_products(studio)
    out = ['\n  <section class="sec gal" aria-labelledby="gallery-h">',
           f'\n    <h2 id="gallery-h" class="big">{t(g["heading"])}</h2>']
    for app in g["apps"]:
        out.append(f'\n    <div class="gapp">\n      <h3>{t(app["name"])}</h3>')
        if app.get("product") in inside:
            out.append(app_intro(inside[app["product"]]))
        for grp in app["groups"]:
            cap = f'<p class="gcap">{t(grp["caption"])}</p>' if grp.get("caption") else ""
            name = f'{app["name"]}, {grp["label"].lower()}'
            out.append(f'\n      <div class="ggroup">'
                       f'\n        <div class="ghead"><p class="label">{t(grp["label"])}</p>{cap}</div>'
                       f'\n        <div class="grow" role="region" tabindex="0" aria-label="{a(name)}">')
            for n, it in enumerate(grp["items"], 1):
                f = GALLERY_DIR / it["file"]
                assert f.is_file(), f"studio.json gallery: {it['file']} is not in assets/gallery"
                w, h = jpeg_size(f)
                for s in (it["alt"], it.get("caption") or ""):
                    assert "—" not in s, "em dash in studio.json gallery: " + s
                fc = ""
                if it.get("caption"):
                    fc = f'<figcaption>{f"{n}. " if grp.get("numbered") else ""}{t(it["caption"])}</figcaption>'
                out.append(f'\n          <figure><img src="gallery/{a(it["file"])}" width="{w}" height="{h}" '
                           f'loading="lazy" decoding="async" alt="{a(it["alt"])}">{fc}</figure>')
            out.append('\n        </div>\n      </div>')
        out.append('\n    </div>')
    out.append('\n  </section>')
    return "".join(out)


# Phone shots are 660 by 1349: 200 px wide on phones and 220 px from 800 px, their 1.5 px
# border included (so five fit across at 1440 with a 10 px gap). Every
# image in a row gets that same height and keeps its own shape (the spreadsheet and the
# Figma photo come out wider). Border and radius as the Bird League card's image. The
# row's focus ring is the page's standard one (chrome.py), since it's a tab stop too.
# Under 800 px a row runs on to the screen's right edge, the page gutter (chrome.py's .wrap)
# becoming padding inside it, so the next image shows at the edge and the last one still ends
# on the section's edge when the row is scrolled to its end.
GALLERY_CSS = r"""
.gal{gap:28px}
.gapp{display:flex;flex-direction:column;gap:16px}
.gapp h3{margin:0;font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(30px,3vw,40px);line-height:.95}
.ggroup{display:flex;flex-direction:column;gap:10px;min-width:0}
.ghead{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 12px}
.ghead .label{margin:0;color:#676D66}
.ghead .gcap{margin:0;font-size:14px;color:#5A635D}
.grow{--h:calc(197px * 1349 / 660 + 3px);display:flex;align-items:flex-start;gap:12px;overflow-x:auto;overscroll-behavior-x:contain;scroll-snap-type:x mandatory;padding-bottom:8px;scrollbar-width:thin}
.grow figure{flex:none;margin:0;display:flex;flex-direction:column;gap:8px;scroll-snap-align:start}
.grow img{display:block;height:var(--h);width:auto;max-width:none;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
.grow figcaption{contain:inline-size;font-size:14px;line-height:1.4;color:#3B4540}
.dj .grow:focus-visible{outline:3px solid #E8592B;outline-offset:3px}
@media (max-width:799px){.grow{margin-right:calc(-1 * clamp(16px,4vw,48px));padding-right:clamp(16px,4vw,48px)}}
@media (min-width:800px){.grow{--h:calc(217px * 1349 / 660 + 3px);flex-wrap:wrap;overflow:visible;gap:18px 10px;padding-bottom:0}}
"""

# T-29 (Nov 18, 2026): the top of an app block that carries its product's card words
# (app_intro()). The pill, the join box (.jf, .jf-e, .btn.hot) and the link (.go) keep the
# card's classes; these rules give the lines, the proof and the link outside a card what
# .prod gave them inside one. Under 900 px the text, then the join box under it; from
# 900 px the text on the left (at most 34em) and the join box on the right, top-aligned.
# The block sits on the page's cream, not the card's paper, so the email label takes the
# darker grey the gallery's labels use there (#676D66, T-20 F9: #6B716A fails on cream).
APP_CSS = r"""
.gprod{display:flex;flex-direction:column;gap:20px;margin-bottom:8px}
.gtext{display:flex;flex-direction:column;gap:12px;max-width:34em}
.gtext p{margin:0;font-size:16px;color:#3B4540}
.gtext .proof strong{color:#16201C}
.gtext a.go{align-self:flex-start;display:inline-flex;align-items:center;min-height:44px;font-weight:700;text-decoration:none;color:#16201C}
.gtext a.go:hover{color:#A93F17}
.gjoin .jf-e span{color:#676D66}
@media (min-width:900px){.gprod{flex-direction:row;align-items:flex-start;gap:48px}
.gtext{flex:0 1 34em}
.gjoin{flex:1 1 0;min-width:0}}
"""

# T-30 (Nov 18, 2026): a card that spans its whole row (.prod.wide; today Free tools and
# ChuckleFits from 800 px) keeps its description line at most 34em wide, the measure of the
# app blocks above it (.gtext), so it doesn't run as one long line across the page.
# studio.html only (the product pages use CSS, not this); half-width cards, the proof line
# and the ChuckleFits shelf are untouched.
WIDE_CSS = r"""
.prod.wide>p:not(.proof){max-width:34em}
"""


# T-27 (Nov 18, 2026): the ChuckleFits shelf, inside that product's card, between its "what"
# line and its link row. Every word is in studio.json's "shelf" (name, kind, alt); this adds
# only the price as "From $<price>" (no cents when they're .00). Each product is one link to
# its shop page, the tag from "link_tag" on the address, opening in the same tab like the
# card's own shop link. Photos: _build/assets/shelf/<handle>.jpg (480 px wide; enhance.py
# copies them to images/shelf/), width and height read from the file. A product whose tags
# contain "unhinged" stops the build, named, so it can never reach the page.
SHELF_DIR = HERE / "assets" / "shelf"
SHOP = "https://chucklefits.com"


def shelf_price(s):
    whole, _, cents = s.partition(".")
    assert whole.isdigit() and (cents == "" or (cents.isdigit() and len(cents) == 2)), f"shelf price {s!r}"
    return f'From ${whole}' if cents in ("", "00") else f'From ${whole}.{cents}'


def shelf(p):
    tag = p.get("link_tag")
    assert tag, f'studio.json: {p["id"]} has a shelf but no link_tag'
    items = []
    for it in p["shelf"]:
        for tg in it.get("tags", []):
            if "unhinged" in tg.lower():
                raise SystemExit(f'studio.json shelf: "{it["handle"]}" ({it["name"]}) has the tag '
                                 f'"{tg}"; a product tagged unhinged can\'t be on the site. Take it off the shelf.')
        for s in (it["name"], it["kind"], it["alt"]):
            assert "—" not in s, "em dash in studio.json shelf: " + s
        assert it["image"] == f'images/shelf/{it["handle"]}.jpg', f'shelf image path for {it["handle"]}'
        f = SHELF_DIR / f'{it["handle"]}.jpg'
        assert f.is_file(), f'studio.json shelf: {f.name} is not in assets/shelf'
        w, h = jpeg_size(f)
        href = f'{SHOP}/products/{quote(it["handle"], safe="-")}?{tag}'
        items.append(f'\n            <li><a href="{a(href)}"><img src="{a(it["image"])}" width="{w}" height="{h}" '
                     f'loading="lazy" decoding="async" alt="{a(it["alt"])}">'
                     f'<span class="sn">{t(it["name"])}</span><span class="sk">{t(it["kind"])}</span>'
                     f'<span class="sp">{shelf_price(it["price"])}</span></a></li>')
    return (f'<div class="shelf" role="region" aria-label="{a(p["name"])} shirts" tabindex="0">'
            f'\n          <ul>{"".join(items)}\n          </ul>\n        </div>')


# Phones (under 800 px): one row that scrolls sideways inside the card, snapping at each
# product's start, and running on into the card's right padding so the next product shows at
# the edge; scrolled to its end, the last one ends on the card's content edge. Each product is
# sized from the screen width so about 1.6 show under 480 px and 2.6 from 480 px: the next one
# is always cut partway, never hidden and never almost whole. 6 px of room
# round the list keeps the links' focus rings in view. From 800 px three across, from 1200 px
# six. Photo border and radius as the card images; name in the page's sans at 700, kind and
# price smaller in #5A635D. The row is a tab stop with the page's standard focus ring.
SHELF_CSS = r"""
.shelf{margin:-6px calc(-1 * clamp(22px,2.6vw,30px)) 0 -6px;overflow-x:auto;overscroll-behavior-x:contain;scroll-snap-type:x mandatory;scroll-padding-left:6px;scrollbar-width:thin}
.shelf ul{list-style:none;margin:0;display:flex;gap:12px;width:max-content;padding:6px clamp(22px,2.6vw,30px) 10px 6px}
.shelf li{flex:none;width:calc((100vw - 2 * clamp(16px,4vw,48px) - 37px) / 1.6);margin:0;scroll-snap-align:start}
@media (min-width:480px){.shelf li{width:calc((100vw - 2 * clamp(16px,4vw,48px) - 49px) / 2.6)}}
.shelf a{display:flex;flex-direction:column;gap:2px;text-decoration:none;color:#16201C}
.shelf img{display:block;width:100%;height:auto;margin-bottom:8px;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
.shelf .sn{font-family:'Instrument Sans','Helvetica Neue',system-ui,sans-serif;font-weight:700;font-size:16px;line-height:1.25;overflow-wrap:break-word}
.shelf .sk,.shelf .sp{font-size:14px;line-height:1.35;color:#5A635D}
.shelf a:hover .sn{color:#A93F17}
.dj .shelf:focus-visible{outline:3px solid #E8592B;outline-offset:3px}
@media (min-width:800px){.shelf{margin:-6px -6px 0;overflow:visible}
.shelf ul{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px 18px;width:auto;padding:6px}
.shelf li{width:auto}}
@media (min-width:1200px){.shelf ul{grid-template-columns:repeat(6,minmax(0,1fr))}}
"""


# T-25 F4: on phones the count was its own band (a dark rule over "11", a thin one under
# it, then the heading and the log's rule), so it read apart from "Shipped lately". Under
# 800 px it now sits the way T-23 L7 set it from 800 px: the heading, then the count on
# the next line, no band rules, the log's rule under both. studio.html only (the product
# pages have no count); the count and its words are untouched.
LOG_PHONE_CSS = r"""
@media (max-width:799px){.loghead{flex-direction:row-reverse;flex-wrap:wrap-reverse;justify-content:flex-end;align-items:baseline;gap:8px 24px}
.loghead .stats{border:0}.loghead .stats p{padding:0}
.loghead .stats strong{display:inline;font-size:clamp(38px,4.6vw,60px);margin-right:.18em}}
"""

PAGE_CSS = r"""
.kick a{display:inline-flex;align-items:center;min-height:44px;color:inherit;text-decoration:underline;text-underline-offset:3px}
.kick a:hover{color:#E9EEE9}
.hero-pill{align-self:flex-start;display:inline-flex;align-items:center;min-height:30px;padding:0 14px;border-radius:999px;background:#E9EEE9;color:#0E1B17;font-size:14px;font-weight:700}
.top{display:grid;grid-template-columns:minmax(0,1fr);gap:24px 40px;align-items:start}
.top .proof{margin:0;font-size:clamp(20px,2vw,24px);line-height:1.4}
.top img{width:100%;max-width:560px;height:auto;display:block;border:1.5px solid #CFC6B2;border-radius:2px;background:#F4EFE6}
@media (min-width:800px){.top.has-img{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.top.has-log{grid-template-areas:'proof img' 'log img';grid-template-rows:auto 1fr}.top.has-log>.proof{grid-area:proof}.top.has-log>img{grid-area:img}.top.has-log>.sec{grid-area:log}}
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
    mine = [r for r in rows if r["project"] == p["id"]]
    log = ""
    if mine:
        items = "".join(log_item(r, today, label=False) for r in mine)
        log = (f'\n  <section class="sec" aria-labelledby="log-h">'
               f'\n    <h2 id="log-h" class="big">Shipped lately</h2>'
               f'\n    <ol class="log solo" id="log">{items}\n    </ol>'
               '\n  </section>')
    # With an image and a proof line, the log joins them (T-20 F8), so on wide screens it
    # fills the column under the proof line, beside the image.
    beside = bool(proof and img and log)
    if proof or img:
        parts.append(f'\n  <div class="top{" has-img" if img else ""}{" has-log" if beside else ""}">'
                     + (f'\n    {proof}' if proof else "") + (f'\n    {img}' if img else "")
                     + (log.replace("\n  ", "\n    ") if beside else "") + '\n  </div>')
    if log and not beside:
        parts.append(log)
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
    title = hero["kicker"].split(" · ")[0]          # "The studio"; the kicker itself isn't printed (T-16)
    lede = hero_lede(studio)                         # the meta description, as before T-16
    stamp = f'<!-- studio.py {today.isoformat()} {fingerprint()} -->'
    from chrome import write
    write(out_dir, "studio.html",
          title=title,
          description=lede.replace('"', "&quot;"),
          kicker="", h1=hero["h1"], lede=t(hero["intro"]),
          css=CSS + LOG_PHONE_CSS + GALLERY_CSS + APP_CSS + WIDE_CSS + SHELF_CSS, body=stamp + body, script=SCRIPT, more="")
    # One page per open product with a join list (T-09). A page whose product
    # closed or lost its list is removed, so it can't be copied into the site.
    rows = visible(studio, shipped, today)
    keep = set()
    for slug, p in product_pages(studio):
        keep.add(slug)
        write(out_dir, slug,
              title=t(p["name"]),
              description=a(p["what"]),
              kicker=f'<a href="studio.html">{t(BACK)}</a>',
              h1=t(p["name"]),
              badge=f'\n      <span class="hero-pill">{t(p["status"])}</span>',
              lede=t(p["what"]),
              css=CSS + PAGE_CSS, body=product_page(p, rows, today, stamp), script=JOIN_SCRIPT, more="")
    for old in pathlib.Path(out_dir).glob("studio-*.html"):
        if old.name not in keep:
            old.unlink()
            print("removed", old)


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
