#!/usr/bin/env python3
"""Two sample pages (T-47, PROOF-1, Nov 24, 2026).

    cd _build/tools && python3 samples.py ..

Writes _build/sample-blueprint.html and _build/sample-report.html with the shared
header and footer from chrome.py. One made-up bakery carried through the real
Blueprint (Day 1, Day 7, Day 14) and its first monthly report. Every page says it
is a sample and that the bakery and its numbers are made up. Linked from Local's
"How it works" (voice2.py, P1-a and P1-b) and from each other. Not free tools:
no "More free tools" line, not in chrome.TOOLS.
"""
import html
import pathlib
import sys

from chrome import page

CSS = """.smp{display:grid;gap:20px}
.smp h2{font-family:'Big Shoulders Display',Impact,sans-serif;font-weight:800;text-transform:uppercase;line-height:.95;margin:0 0 12px;font-size:clamp(28px,3.4vw,40px)}
.smp h3{margin:18px 0 6px;font-size:18px;line-height:1.3}
.smp p{margin:0 0 10px;max-width:64ch}
.smp p:last-child{margin-bottom:0}
.day{font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.08em;color:#A93F17;margin:0 0 6px}
.rows{list-style:none;margin:6px 0 0;padding:0;max-width:640px}
.rows li{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 24px;padding:10px 0;border-top:1px solid #CFC6B2}
.rows li:last-child{border-bottom:1px solid #CFC6B2}
.rows b{font-family:'JetBrains Mono',monospace;font-weight:700;white-space:nowrap}
.next{font-weight:700}
"""

def esc(s):
    return html.escape(s, quote=False).replace("'", "&#x27;")

def p(*lines):
    return "".join(f"<p>{esc(x)}</p>" for x in lines)

def rows(pairs):
    return '<ul class="rows">' + "".join(f"<li><span>{esc(k)}</span><b>{esc(v)}</b></li>" for k, v in pairs) + "</ul>"

def panel(day, h, inner):
    d = f'<p class="day">{esc(day)}</p>' if day else ""
    return f'<section class="panel">{d}<h2>{esc(h)}</h2>{inner}</section>'

CTA = dict(cta_h="Want a plan like this of your own?",
           cta_p="Two weeks, $1,500. Half after the Day 7 sample, and it comes off the price if you go ahead.",
           cta_href="start.html", cta_btn="Start a Blueprint →")

BLUEPRINT = "".join([
    panel("DAY 1", "What I saw", p(
        "The owner takes wholesale orders from 11 cafes. They come in by text, email and voicemail.",
        "Every Sunday night she types them all into a spreadsheet, then copies the totals onto a bake sheet for the morning crew. It takes her about four hours.",
        "Last month two orders slipped through, and one cafe opened without its croissants.")),
    panel("DAY 7", "The sample", p(
        "I built a working sample from four weeks of her real orders. It reads each order, adds it to the week and writes the bake sheet.",
        "She checked it against her own sheets, and they matched except for one order that came in as a photo of a handwritten note. The sample set that one aside for her to read.")),
    panel("DAY 14", "The plan",
        "<h3>What I'll build</h3>" + p(
            "One place for every order. By 6 PM each Sunday, the week's order list and Monday's bake sheet are ready.",
            "Anything it can't read goes to her first. Invoices are drafted for her, and none go out until she says yes.")
        + "<h3>What stays the same</h3>" + p("The cafes order the way they always have, by text, email or voicemail.")
        + "<h3>The price</h3>" + rows([("The Build, fixed", "$3,600"), ("Less the Blueprint", "−$1,500"),
                                       ("Left to pay for the build", "$2,100"), ("Support, if she wants it", "$750 a month")])
        + "<h3>Launch date</h3>" + p("The second Monday after she says go.")
        + "<h3>What it should save</h3>" + p("Most of her four hours on Sunday nights. The monthly report will show the real number.")
        + "<h3>If the answer had been no</h3>" + p("With five cafes or fewer, I'd have told her a free shared order form would do the job.")),
    '<p class="next"><a href="sample-report.html">See the sample report from its first month →</a></p>',
])

REPORT = "".join([
    panel("THE ORDER TOOL · FIRST MONTH", "What it did", rows([
        ("Orders read", "212"), ("Sundays the bake sheet was ready by 6 PM", "4 of 4"),
        ("Invoices drafted", "44"), ("Invoices sent without her yes", "0"),
        ("Missed orders (2 the month before)", "0"),
    ])),
    panel("", "Held for her", p(
        "9 orders. Six were photos of handwritten notes, two asked for an item that isn't on the list yet, and one cafe wanted to change its standing order.",
        "Most took her a minute or two.")),
    panel("", "What it saved", p("Sunday nights went from about four hours of typing to about 25 minutes of checking.")),
    panel("", "What broke, and how I fixed it", p(
        "On the 9th, one cafe started ordering from a new email address. Its order landed with the held ones instead of on the week's list.",
        "She saw it there, and I added the new address that afternoon. Nothing was missed.")),
    panel("", "Next month", p("Two new cafes start on the 1st. They're set up already.")),
    '<p class="next"><a href="sample-blueprint.html">See the plan this tool came from →</a></p>',
])

PAGES = {
    "sample-blueprint.html": dict(
        title="Sample Blueprint",
        description="A sample of the plan you get on Day 14 of a Blueprint, for a made-up bakery.",
        kicker="Sample · a made-up bakery",
        h1="A sample Blueprint",
        lede="This is what you'd hold on Day 14. The bakery is made up, and so are its numbers. The days and the steps are the real ones.",
        body=BLUEPRINT),
    "sample-report.html": dict(
        title="Sample monthly report",
        description="A sample of the one-page monthly report, for a made-up bakery's order tool.",
        kicker="Sample · a made-up bakery",
        h1="A sample monthly report",
        lede="One page on the 1st of every month. This one is for the bakery's order tool after its first month. The bakery and its numbers are made up.",
        body=REPORT),
}

def build(out_dir):
    for slug, k in PAGES.items():
        k = dict(k, body='<div class="smp">' + k["body"] + "</div>", css=CSS, more="", **CTA)
        t = page(slug=slug, og=slug[:-len(".html")], **k)
        empty = t[t.index('  <p class="noprint" style="margin:4px 0 -4px'):]
        empty = empty[:empty.index("</p>\n") + 5]
        assert ">" + "</p>" in empty and empty.count("<p") == 1, "the empty more line"
        t = t.replace(empty, "", 1)
        assert "—" not in t, "em dash in " + slug
        out = pathlib.Path(out_dir) / slug
        out.write_text(t, encoding="utf-8")
        print("wrote", out, len(t))

if __name__ == "__main__":
    build(sys.argv[1])
