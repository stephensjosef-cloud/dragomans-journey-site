#!/usr/bin/env python3
"""Build the static Dragoman's Journey site from the three .dc.html canvas pages.

Copy and styles come from the source files and from vals.json, which is the
output of the sources' own renderVals() (see dump.js). Nothing is retyped.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
VALS = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)

ACCENT = "#E8592B"
SITE = "https://dragomansjourney.com/"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b(v):
    return "true" if v in (True, "true") else "false"


def tidy_path(d):
    # JS float noise like 3.6000000000000014 -> 3.6
    return re.sub(r"-?\d+\.\d{4,}", lambda m: ("%.2f" % float(m.group(0))).rstrip("0").rstrip("."), d)


def rep(text, old, new, count=1):
    n = text.count(old)
    assert n == count, f"expected {count} of {old[:80]!r}, found {n}"
    return text.replace(old, new)


def rep_re(text, pattern, new, count=1):
    rx = re.compile(pattern, re.S)
    n = len(rx.findall(text))
    assert n == count, f"expected {count} of /{pattern[:60]}/, found {n}"
    return rx.sub(lambda m: new, text)


def split_source(name):
    raw = (SRC / name).read_text(encoding="utf-8")
    helmet = re.search(r"<helmet>(.*?)</helmet>", raw, re.S).group(1).strip()
    body = re.search(r"</helmet>(.*?)</x-dc>", raw, re.S).group(1).strip()
    return helmet, body


def fix_links(body):
    body = body.replace('href="Fork.dc.html"', 'href="index.html"')
    body = body.replace('href="Main.dc.html"', 'href="local.html"')
    body = body.replace('href="Mainframe.dc.html"', 'href="mainframe.html"')
    assert ".dc.html" not in body
    return body


EXTRA_CSS = "<style>[hidden]{display:none!important}</style>"


def page(path, title, desc, canonical, helmet, body, script, jsonld=None):
    head = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{canonical}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        "<meta property=\"og:site_name\" content=\"Dragoman's Journey\">",
        '<meta property="og:type" content="website">',
        f'<meta property="og:url" content="{canonical}">',
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
        helmet,
        EXTRA_CSS,
    ]
    if jsonld:
        head.append('<script type="application/ld+json">\n' + json.dumps(jsonld, ensure_ascii=False, indent=1) + "\n</script>")
    head.append("</head>")
    html = "\n".join(head) + "\n<body>\n" + body + "\n<script>\n" + script.strip() + "\n</script>\n</body>\n</html>\n"
    assert "{{" not in html and "sc-for" not in html and "sc-if" not in html, path
    assert "—" not in html, "em dash in " + path
    (OUT / path).write_text(html, encoding="utf-8")


def js(template, data):
    return template.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------- Fork / index
def build_index():
    helmet, body = split_source("Fork.dc.html")
    V = VALS["fork"]
    ids = ["local", "main"]
    v0 = V["none"]

    pills = "".join(
        f'<button type="button" aria-pressed="{p["on"]}" data-route="{ids[i]}" style="{p["style"]}">{esc(p["label"])}</button>'
        for i, p in enumerate(v0["pills"])
    )
    body = rep_re(body, r'<sc-for list="\{\{pills\}\}".*?</sc-for>', pills)
    body = rep(body, '<th scope="col" style="{{colLocalHead}}">', f'<th scope="col" data-col="local" style="{v0["colLocalHead"]}">')
    body = rep(body, '<th scope="col" style="{{colMainHead}}">', f'<th scope="col" data-col="main" style="{v0["colMainHead"]}">')
    body = rep(body, '<table style="width: 100%; min-width: 720px;', '<table id="lineup" style="width: 100%; min-width: 720px;')
    rows = "".join(
        '<tr><th scope="row" style="text-align: left; padding: 16px 16px 16px 0; border-top: 1px solid #CFC8B8; font-weight: 600">'
        f'{esc(r["piece"])}</th><td data-col="local" style="{r["lStyle"]}">{esc(r["local"])}</td>'
        f'<td data-col="main" style="{r["mStyle"]}">{esc(r["main"])}</td></tr>'
        for r in v0["rows"]
    )
    body = rep_re(body, r'<sc-for list="\{\{rows\}\}".*?</sc-for>', rows)
    body = fix_links(body)

    data = {}
    for k in ("none", "local", "main"):
        v = V[k]
        data[k] = {
            "pills": [{"on": p["on"], "style": p["style"]} for p in v["pills"]],
            "heads": [v["colLocalHead"], v["colMainHead"]],
            "cells": [[r["lStyle"], r["mStyle"]] for r in v["rows"]],
        }
    script = js(r"""
(function () {
  var V = /*DATA*/null;
  var route = 'none';
  var pills = document.querySelectorAll('button[data-route]');
  var heads = [document.querySelector('th[data-col="local"]'), document.querySelector('th[data-col="main"]')];
  var rows = document.querySelectorAll('#lineup tbody tr');
  function apply() {
    var v = V[route];
    pills.forEach(function (btn, i) {
      btn.setAttribute('aria-pressed', v.pills[i].on);
      btn.setAttribute('style', v.pills[i].style);
    });
    heads[0].setAttribute('style', v.heads[0]);
    heads[1].setAttribute('style', v.heads[1]);
    rows.forEach(function (tr, i) {
      var tds = tr.querySelectorAll('td');
      tds[0].setAttribute('style', v.cells[i][0]);
      tds[1].setAttribute('style', v.cells[i][1]);
    });
  }
  pills.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-route');
      route = route === id ? 'none' : id;
      apply();
    });
  });
})();
""", data)

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "Dragoman's Journey",
                "alternateName": "Dragoman's Journey · Josef Stephens",
                "url": SITE,
            },
            {
                "@type": "Person",
                "name": "Josef Stephens",
                "jobTitle": "Founder, Dragoman's Journey",
                "address": {"@type": "PostalAddress", "addressLocality": "Santa Rosa", "addressRegion": "CA"},
                "sameAs": ["https://github.com/stephensjosef-cloud"],
            },
        ],
    }
    page(
        "index.html",
        "Dragoman's Journey · Josef Stephens",
        "Two routes, one guide: AI productions for Sonoma County small businesses and nonprofits, and proof of behavioral equivalence for COBOL migrations.",
        SITE,
        helmet, body, script, jsonld,
    )
    return helmet


# ---------------------------------------------------------------- Main / local
RC_ROW = ('<div style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 18px; padding: 12px 0; border-top: 1px solid #2B3D35; align-items: baseline">'
          '<span style="font-size: 14px; color: #B5C2BA; line-height: 1.45">{k}</span>'
          '<strong style="font-size: 18px; font-weight: 700; color: #F07A4E; text-align: right">{v}</strong></div>')


def build_local():
    helmet, body = split_source("Main.dc.html")
    V = VALS["main"]
    v0 = V["none"]
    assert v0["accent"] == ACCENT

    topo = "".join(f'<path d="{tidy_path(p["d"])}" fill="none" stroke="{p["stroke"]}" stroke-width="1.1"></path>' for p in v0["topo"])
    body = rep_re(body, r'<sc-for list="\{\{topo\}\}".*?</sc-for>', topo, count=2)
    body = rep(body, "{{accent}}", ACCENT, count=4)

    hero = "".join(
        '<div style="display: flex; justify-content: space-between; gap: 16px; align-items: baseline">'
        f'<span style="color: #3E4640">{esc(r["k"])}</span>'
        '<span style="flex: 1; border-bottom: 1px dotted #A6AAA2; transform: translateY(-4px)"></span>'
        f'<strong style="font-weight: 700; color: #16201C; white-space: nowrap">{esc(r["v"])}</strong></div>'
        for r in v0["heroRows"]
    )
    body = rep_re(body, r'<sc-for list="\{\{heroRows\}\}".*?</sc-for>', hero)

    pick_ids = ["reels", "app", "flow", "unsure"]
    opts = "".join(
        f'<button type="button" aria-pressed="{o["on"]}" data-pick="{pick_ids[i]}" style="{o["style"]}">'
        f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 12px; letter-spacing: 0.1em; opacity: 0.8">{esc(o["num"])}</span>'
        f'<span style="font-size: 19px; font-weight: 600; line-height: 1.3">{esc(o["label"])}</span></button>'
        for i, o in enumerate(v0["options"])
    )
    body = rep_re(body, r'<sc-for list="\{\{options\}\}".*?</sc-for>', opts)
    msg = ('<div id="pick-msg" role="status" style="display: flex; flex-wrap: wrap; align-items: center; gap: 16px; padding: 18px 22px; border: 1.5px solid #F07A4E; border-radius: 2px" hidden="">'
           '<span id="pick-text" style="font-size: 18px; color: #E9EEE9"></span>'
           '<a id="pick-link" href="#engines" style="color: #F07A4E; font-weight: 700; text-decoration: none"> →</a></div>')
    body = rep_re(body, r'<sc-if value="\{\{hasPick\}\}".*?</sc-if>', msg)

    for key, card in (("reels", "cardReels"), ("app", "cardApp"), ("flow", "cardFlow")):
        body = rep(body, f'<article class="card-lift" style="{{{{{card}}}}}">', f'<article class="card-lift" data-card="{key}" style="{v0[card]}">')
    for key, flag in (("reels", "isReels"), ("app", "isApp"), ("flow", "isFlow")):
        body = rep_re(
            body,
            r'<sc-if value="\{\{' + flag + r'\}\}"[^>]*>(.*?)</sc-if>',
            f'<span data-match="{key}" style="font-family: \'JetBrains Mono\', monospace; font-size: 12px; font-weight: 700; color: #A93F17" hidden="">YOUR MATCH</span>',
        )

    tab_ids = ["reels", "app", "method"]
    tabs = "".join(
        f'<button type="button" role="tab" aria-selected="{t["on"]}" aria-controls="rc-panel" data-tab="{tab_ids[i]}" style="{t["style"]}">{esc(t["label"])}</button>'
        for i, t in enumerate(v0["tabs"])
    )
    body = rep_re(body, r'<sc-for list="\{\{tabs\}\}".*?</sc-for>', tabs)
    rc = v0["rc"]
    body = rep(body, '<div style="background: #15261F; border: 1px solid #2B3D35;', '<div id="rc-panel" role="tabpanel" aria-label="Receipt" style="background: #15261F; border: 1px solid #2B3D35;')
    body = rep(body, "<span>{{rc.head}}</span>", f'<span id="rc-head">{esc(rc["head"])}</span>')
    body = rep(body, "<span>{{rc.date}}</span>", f'<span id="rc-date">{esc(rc["date"])}</span>')
    body = rep(body, '<h3 style="margin: 0; font-family: \'Big Shoulders Display\', Impact, sans-serif; font-weight: 800; text-transform: uppercase; font-size: 34px; line-height: 1; color: #E9EEE9">{{rc.title}}</h3>',
               f'<h3 id="rc-title" style="margin: 0; font-family: \'Big Shoulders Display\', Impact, sans-serif; font-weight: 800; text-transform: uppercase; font-size: 34px; line-height: 1; color: #E9EEE9">{esc(rc["title"])}</h3>')
    rows = "".join(RC_ROW.format(k=esc(r["k"]), v=esc(r["v"])) for r in rc["rows"])
    body = rep_re(body, r'<div style="display: flex; flex-direction: column">\s*<sc-for list="\{\{rc.rows\}\}".*?</sc-for>\s*</div>',
                  f'<div id="rc-rows" style="display: flex; flex-direction: column">{rows}</div>')
    body = rep(body, 'color: #C9D2CB">{{rc.note}}</p>', f'color: #C9D2CB" id="rc-note">{esc(rc["note"])}</p>')
    method = V["tab_method"]["rc"]
    body = rep_re(body, r'<sc-if value="\{\{rc.hasLink\}\}".*?</sc-if>',
                  f'<a id="rc-link" href="{method["link"]}" style="color: #F07A4E; font-size: 14px; text-decoration: none" hidden="">{esc(method["linkLabel"])} →</a>')

    faqs = ""
    for i, f in enumerate(v0["faqs"]):
        hid = "" if f["open"] else ' hidden=""'
        faqs += ('<div style="border-bottom: 1px solid #C9C1AE">'
                 f'<button type="button" aria-expanded="{b(f["open"])}" aria-controls="faq-a-{i}" data-faq="{i}" style="width: 100%; min-height: 64px; display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 16px 0; background: none; border: 0; text-align: left; color: #16201C; font-size: 19px; font-weight: 600">'
                 f'<span>{esc(f["q"])}</span><span aria-hidden="true" style="{f["iconStyle"]}">+</span></button>'
                 f'<p id="faq-a-{i}" style="margin: 0 0 22px; max-width: 62ch; font-size: 17px; color: #3B4540"{hid}>{esc(f["a"])}</p></div>')
    body = rep_re(body, r'<sc-for list="\{\{faqs\}\}".*?</sc-for>', faqs)

    body = rep(body, '<span aria-hidden="true" class="blink" style="width: 9px; height: 9px; border-radius: 50%; background: {{dot}}"></span>',
               f'<span aria-hidden="true" class="blink" id="sr-dot" style="width: 9px; height: 9px; border-radius: 50%; background: {v0["dot"]}"></span>')
    body = rep(body, "<span>It's {{clock}} in Santa Rosa. {{status}}</span>",
               f'<span>It\'s <span id="sr-clock">{esc(v0["clock"])}</span> in Santa Rosa. <span id="sr-status">{esc(v0["status"])}</span></span>')
    body = fix_links(body)

    data = {
        "picks": {},
        "tabs": {},
        "faqIcon": {"open": v0["faqs"][0]["iconStyle"], "closed": V["closed"]["faqs"][0]["iconStyle"]},
        "row": RC_ROW,
    }
    for k in pick_ids:
        v = V[k]
        data["picks"][k] = {
            "options": [{"on": o["on"], "style": o["style"]} for o in v["options"]],
            "msg": v["pickMsg"], "href": v["pickHref"], "cta": v["pickCta"],
            "cards": [v["cardReels"], v["cardApp"], v["cardFlow"]],
            "match": [v["isReels"], v["isApp"], v["isFlow"]],
        }
    for k, sk in (("reels", "none"), ("app", "tab_app"), ("method", "tab_method")):
        v = V[sk]
        data["tabs"][k] = {"tabs": [{"on": t["on"], "style": t["style"]} for t in v["tabs"]], "rc": v["rc"]}

    script = js(r"""
(function () {
  var D = /*DATA*/null;
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function $(id) { return document.getElementById(id); }

  // Picker: four options, message, link, matching engine card.
  var opts = document.querySelectorAll('button[data-pick]');
  var cards = [document.querySelector('[data-card="reels"]'), document.querySelector('[data-card="app"]'), document.querySelector('[data-card="flow"]')];
  var matches = [document.querySelector('[data-match="reels"]'), document.querySelector('[data-match="app"]'), document.querySelector('[data-match="flow"]')];
  function pick(id) {
    var v = D.picks[id];
    opts.forEach(function (btn, i) {
      btn.setAttribute('aria-pressed', v.options[i].on);
      btn.setAttribute('style', v.options[i].style);
    });
    $('pick-text').textContent = v.msg;
    $('pick-link').setAttribute('href', v.href);
    $('pick-link').textContent = v.cta + ' →';
    $('pick-msg').hidden = false;
    cards.forEach(function (c, i) { c.setAttribute('style', v.cards[i]); matches[i].hidden = !v.match[i]; });
  }
  opts.forEach(function (btn) { btn.addEventListener('click', function () { pick(btn.getAttribute('data-pick')); }); });

  // Receipts tabs.
  var tabs = document.querySelectorAll('button[data-tab]');
  function tab(id) {
    var v = D.tabs[id], rc = v.rc;
    tabs.forEach(function (btn, i) {
      btn.setAttribute('aria-selected', v.tabs[i].on);
      btn.setAttribute('style', v.tabs[i].style);
    });
    $('rc-head').textContent = rc.head;
    $('rc-date').textContent = rc.date;
    $('rc-title').textContent = rc.title;
    $('rc-rows').innerHTML = rc.rows.map(function (r) { return D.row.replace('{k}', esc(r.k)).replace('{v}', esc(r.v)); }).join('');
    $('rc-note').textContent = rc.note;
    var link = $('rc-link');
    if (rc.hasLink) { link.setAttribute('href', rc.link); link.textContent = rc.linkLabel + ' →'; }
    link.hidden = !rc.hasLink;
  }
  tabs.forEach(function (btn) { btn.addEventListener('click', function () { tab(btn.getAttribute('data-tab')); }); });

  // FAQ: one open at a time.
  var faqBtns = document.querySelectorAll('button[data-faq]');
  var open = 0;
  function setFaq(n) {
    open = n;
    faqBtns.forEach(function (btn, i) {
      var on = i === open;
      btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      btn.lastElementChild.setAttribute('style', on ? D.faqIcon.open : D.faqIcon.closed);
      $('faq-a-' + i).hidden = !on;
    });
  }
  faqBtns.forEach(function (btn, i) { btn.addEventListener('click', function () { setFaq(open === i ? -1 : i); }); });

  // Santa Rosa clock and status.
  function tick() {
    try {
      var now = new Date();
      var clock = now.toLocaleTimeString('en-US', { timeZone: 'America/Los_Angeles', hour: 'numeric', minute: '2-digit' });
      var parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', weekday: 'short', hour: 'numeric', hour12: false }).formatToParts(now);
      var wd = '', hr = 0;
      parts.forEach(function (p) { if (p.type === 'weekday') wd = p.value; if (p.type === 'hour') hr = parseInt(p.value, 10); });
      var working = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].indexOf(wd) !== -1 && hr >= 13 && hr < 18;
      $('sr-clock').textContent = clock;
      $('sr-status').textContent = working ? "I'm in a work block, so you'll likely hear back today." : "I'm off the clock. Expect a reply the next weekday afternoon.";
      $('sr-dot').style.background = working ? '#7BD389' : '#93A39A';
    } catch (e) { /* the clock is decoration only */ }
  }
  tick();
  setInterval(tick, 30000);
})();
""", data)

    page(
        "local.html",
        "The Local Route · Dragoman's Journey",
        "Reels, apps and workflows for Sonoma County small businesses and nonprofits, made from what you already have and checked by a person before anything reaches your customers.",
        SITE + "local.html",
        helmet, body, script,
    )


# ------------------------------------------------------- Mainframe / mainframe
XB_ROW = ('<div style="display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; padding: 11px 16px; border-bottom: 1px dotted #B9B2A2">'
          '<span style="color: #5D6576">{k}</span><strong style="text-align: right">{v}</strong></div>')


def build_mainframe():
    helmet, body = split_source("Mainframe.dc.html")
    V = VALS["mainframe"]
    v0 = V["none"]

    lines = v0["lines"]
    body = rep_re(body, r'<sc-for list="\{\{lines\}\}" as="p" hint-placeholder-count="18">\s*<path d="\{\{p.d\}\}" fill="none" stroke="rgba\(18,22,31,0.07\)" stroke-width="0.8"></path>\s*</sc-for>',
                  "".join(f'<path d="{tidy_path(p["d"])}" fill="none" stroke="rgba(18,22,31,0.07)" stroke-width="0.8"></path>' for p in lines))
    body = rep_re(body, r'<sc-for list="\{\{lines\}\}" as="p" hint-placeholder-count="18">\s*<path d="\{\{p.d\}\}" fill="none" stroke="rgba\(230,226,216,0.06\)" stroke-width="0.8"></path>\s*</sc-for>',
                  "".join(f'<path d="{tidy_path(p["d"])}" fill="none" stroke="rgba(230,226,216,0.06)" stroke-width="0.8"></path>' for p in lines))

    rd_ids = ["fraction", "percent"]
    rds = "".join(
        f'<button type="button" aria-pressed="{r["on"]}" data-reading="{rd_ids[i]}" style="{r["style"]}">{esc(r["label"])}</button>'
        for i, r in enumerate(v0["readings"])
    )
    body = rep_re(body, r'<sc-for list="\{\{readings\}\}".*?</sc-for>', rds)
    ex = v0["ex"]
    body = rep(body, "<strong>{{ex.bytes}}</strong>", f'<strong id="mf-bytes">{esc(ex["bytes"])}</strong>')
    body = rep(body, "<strong>{{ex.value}}</strong>", f'<strong id="mf-value">{esc(ex["value"])}</strong>')
    body = rep(body, "<strong>{{ex.rate}}</strong>", f'<strong id="mf-rate">{esc(ex["rate"])}</strong>')
    body = rep(body, '<strong style="font-size: 20px; color: {{ex.color}}">{{ex.interest}}</strong>',
               f'<strong id="mf-interest" style="font-size: 20px; color: {ex["color"]}">{esc(ex["interest"])}</strong>')
    body = rep(body, 'line-height: 1.4">{{ex.verdict}}</p>', f'line-height: 1.4" id="mf-verdict" aria-live="polite">{esc(ex["verdict"])}</p>')

    ex_ids = ["b", "c", "d"]
    tabs = "".join(
        f'<button type="button" role="tab" aria-selected="{t["on"]}" aria-controls="xb-panel" data-ex="{ex_ids[i]}" style="{t["style"]}">{esc(t["label"])}</button>'
        for i, t in enumerate(v0["exTabs"])
    )
    body = rep_re(body, r'<sc-for list="\{\{exTabs\}\}".*?</sc-for>', tabs)
    xb = v0["xb"]
    body = rep(body, '<article style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); gap: 28px 48px; align-items: start">',
               '<article id="xb-panel" role="tabpanel" aria-label="Exhibit" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); gap: 28px 48px; align-items: start">')
    body = rep(body, 'line-height: 1.1">{{xb.title}}</h3>', f'line-height: 1.1" id="xb-title">{esc(xb["title"])}</h3>')
    body = rep(body, 'color: #2C3341">{{xb.body}}</p>', f'color: #2C3341" id="xb-body">{esc(xb["body"])}</p>')
    body = rep(body, 'line-height: 1.45">{{xb.lesson}}</p>', f'line-height: 1.45" id="xb-lesson">{esc(xb["lesson"])}</p>')
    body = rep(body, "<strong>{{xb.code}}</strong>", f'<strong id="xb-code">{esc(xb["code"])}</strong>')
    rows = "".join(XB_ROW.format(k=esc(r["k"]), v=esc(r["v"])) for r in xb["rows"])
    body = rep_re(body, r'<sc-for list="\{\{xb.rows\}\}".*?</sc-for>', f'<div id="xb-rows">{rows}</div>')

    toc = ""
    for i, c in enumerate(v0["toc"]):
        hid = "" if c["open"] else ' hidden=""'
        toc += ('<div style="border-bottom: 1px solid #CFC8B8">'
                f'<button type="button" aria-expanded="{b(c["open"])}" aria-controls="toc-b-{i}" data-toc="{i}" style="width: 100%; min-height: 56px; display: grid; grid-template-columns: 44px minmax(0, 1fr) 24px; gap: 12px; align-items: center; padding: 12px 0; background: none; border: 0; text-align: left; color: #12161F">'
                f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 13px; color: #A93F17">{esc(c["num"])}</span>'
                f'<span style="font-family: \'Newsreader\', Georgia, serif; font-size: 21px; line-height: 1.25">{esc(c["title"])}</span>'
                f'<span aria-hidden="true" style="{c["mark"]}">+</span></button>'
                f'<p id="toc-b-{i}" style="margin: 0 0 18px 56px; font-size: 16px; color: #3A4252"{hid}>{esc(c["body"])}</p></div>')
    body = rep_re(body, r'<sc-for list="\{\{toc\}\}".*?</sc-for>', toc)
    body = fix_links(body)

    data = {
        "readings": {},
        "ex": {},
        "mark": {"open": v0["toc"][0]["mark"], "closed": V["closed"]["toc"][0]["mark"]},
        "row": XB_ROW,
    }
    for k, sk in (("percent", "none"), ("fraction", "fraction")):
        v = V[sk]
        data["readings"][k] = {"buttons": [{"on": r["on"], "style": r["style"]} for r in v["readings"]], "ex": v["ex"]}
    for k, sk in (("b", "none"), ("c", "ex_c"), ("d", "ex_d")):
        v = V[sk]
        x = v["xb"]
        data["ex"][k] = {"tabs": [{"on": t["on"], "style": t["style"]} for t in v["exTabs"]],
                         "xb": {"code": x["code"], "title": x["title"], "body": x["body"], "lesson": x["lesson"], "rows": x["rows"]}}

    script = js(r"""
(function () {
  var D = /*DATA*/null;
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function $(id) { return document.getElementById(id); }

  // Exhibit A: fraction or percentage reading.
  var rds = document.querySelectorAll('button[data-reading]');
  function reading(id) {
    var v = D.readings[id], ex = v.ex;
    rds.forEach(function (btn, i) {
      btn.setAttribute('aria-pressed', v.buttons[i].on);
      btn.setAttribute('style', v.buttons[i].style);
    });
    $('mf-bytes').textContent = ex.bytes;
    $('mf-value').textContent = ex.value;
    $('mf-rate').textContent = ex.rate;
    $('mf-interest').textContent = ex.interest;
    $('mf-interest').setAttribute('style', 'font-size: 20px; color: ' + ex.color);
    $('mf-verdict').textContent = ex.verdict;
  }
  rds.forEach(function (btn) { btn.addEventListener('click', function () { reading(btn.getAttribute('data-reading')); }); });

  // Exhibit tabs B, C, D.
  var tabs = document.querySelectorAll('button[data-ex]');
  function exhibit(id) {
    var v = D.ex[id], x = v.xb;
    tabs.forEach(function (btn, i) {
      btn.setAttribute('aria-selected', v.tabs[i].on);
      btn.setAttribute('style', v.tabs[i].style);
    });
    $('xb-code').textContent = x.code;
    $('xb-title').textContent = x.title;
    $('xb-body').textContent = x.body;
    $('xb-lesson').textContent = x.lesson;
    $('xb-rows').innerHTML = x.rows.map(function (r) { return D.row.replace('{k}', esc(r.k)).replace('{v}', esc(r.v)); }).join('');
  }
  tabs.forEach(function (btn) { btn.addEventListener('click', function () { exhibit(btn.getAttribute('data-ex')); }); });

  // Dossier table of contents: one open at a time.
  var toc = document.querySelectorAll('button[data-toc]');
  var open = 0;
  function setToc(n) {
    open = n;
    toc.forEach(function (btn, i) {
      var on = i === open;
      btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      btn.lastElementChild.setAttribute('style', on ? D.mark.open : D.mark.closed);
      $('toc-b-' + i).hidden = !on;
    });
  }
  toc.forEach(function (btn, i) { btn.addEventListener('click', function () { setToc(open === i ? -1 : i); }); });
})();
""", data)

    page(
        "mainframe.html",
        "The Mainframe Route · Dragoman's Journey",
        "An equivalence harness that runs the original and the migrated COBOL system over the same files and compares every byte they write, with evidence your auditors can rerun.",
        SITE + "mainframe.html",
        helmet, body, script,
    )


# ------------------------------------------------------------- small files
def build_extras(fork_helmet):
    (OUT / "CNAME").write_text("dragomansjourney.com", encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: https://dragomansjourney.com/sitemap.xml\n", encoding="utf-8")
    urls = [SITE, SITE + "local.html", SITE + "mainframe.html", SITE + "comp3.html", SITE + "start.html", SITE + "briefing.html"]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 34 34">'
        '<path d="M4 28 L13 10 L19 20 L23 14 L30 28 Z" fill="none" stroke="#12161F" stroke-width="1.8" stroke-linejoin="round"/>'
        '<circle cx="23" cy="7" r="2.4" fill="#E8592B"/></svg>\n', encoding="utf-8")

    # 404 uses root-relative URLs because GitHub Pages serves it at any path.
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found · Dragoman's Journey</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{fork_helmet}
</head>
<body>
<div class="fk" style="font-family: 'Instrument Sans', 'Helvetica Neue', system-ui, sans-serif; color: #12161F; background: #F4F1EA; font-size: 17px; line-height: 1.6; -webkit-font-smoothing: antialiased; min-height: 100vh; display: flex; flex-direction: column">
  <div style="width: 100%; max-width: 1240px; margin: 0 auto; padding: 24px clamp(16px, 4vw, 48px); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px 24px; border-bottom: 1px solid #CFC8B8">
    <a href="/" style="display: flex; align-items: center; gap: 12px; color: #12161F; text-decoration: none">
      <svg aria-hidden="true" width="30" height="30" viewBox="0 0 34 34"><path d="M4 28 L13 10 L19 20 L23 14 L30 28 Z" fill="none" stroke="#12161F" stroke-width="1.8" stroke-linejoin="round"></path><circle cx="23" cy="7" r="2.4" fill="#E8592B"></circle></svg>
      <span style="font-family: 'Newsreader', Georgia, serif; font-size: 21px">Dragoman's Journey</span>
    </a>
    <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: #5D6576">Josef Stephens · Santa Rosa, California</span>
  </div>
  <main style="flex: 1; width: 100%; max-width: 1240px; margin: 0 auto; padding: clamp(56px, 8vw, 104px) clamp(16px, 4vw, 48px); display: flex; flex-direction: column; gap: 22px; align-items: center; text-align: center">
    <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: #A93F17">404 · Off the map</p>
    <h1 style="margin: 0; max-width: 18ch; font-family: 'Newsreader', Georgia, serif; font-weight: 300; font-size: clamp(48px, 7vw, 104px); line-height: 0.98; letter-spacing: -0.03em; text-wrap: balance">This trail <em style="color: #A93F17">doesn't go anywhere</em></h1>
    <p style="margin: 0; max-width: 46ch; font-size: clamp(18px, 1.6vw, 21px); color: #3A4252">The page you asked for isn't here. Head back to the front door and pick a route.</p>
    <a href="/" class="route" style="display: inline-flex; align-items: center; min-height: 52px; padding: 0 22px; background: #12161F; color: #F4F1EA; text-decoration: none; font-weight: 600">Back to the front door →</a>
  </main>
</div>
</body>
</html>
"""
    assert "—" not in html
    (OUT / "404.html").write_text(html, encoding="utf-8")


fork_helmet = build_index()
build_local()
build_mainframe()
build_extras(fork_helmet)
print("built", sorted(p.name for p in OUT.iterdir()))
