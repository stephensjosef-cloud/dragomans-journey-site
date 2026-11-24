#!/usr/bin/env python3
"""Voice pass, Nov 12 2026.

Josef: the site has to sound like him, warm, safe and compelling.
These are his own words, approved line by line. Use them character for
character: no improving, shortening or adding.
The record is in the vault: Claude outputs/dragomans-journey/voice-pass-2026-11-12.md

Runs after intent.py and before final.py, on the built output:
    python3 voice2.py out
Each edit carries its ID (V1, V2, ...) and must match exactly once, or
nothing is written and the build stops naming the edit that missed.
Later pages add their edits to this same file, under their own heading.
"""
import re
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
pages = {p.name: p.read_text(encoding='utf-8') for p in sorted(OUT.glob('*.html'))}
problems = []


def text(page, old, new, ref):
    """Plain text replace in one page; must match exactly once."""
    k = pages[page].count(old)
    if k != 1:
        problems.append('%s %s: %d matches, expected 1  (%s)' % (ref, page, k, old[:80]))
        return
    pages[page] = pages[page].replace(old, new)


def item(page, old_bold, old_line, new_bold, new_line, ref):
    """One "How I work" item: the bold first line and the line under it, as a pair."""
    pat = r'(<strong[^>]*>)' + re.escape(old_bold) + r'(</strong><span[^>]*>)' + re.escape(old_line) + r'(</span>)'
    found = re.findall(pat, pages[page])
    if len(found) != 1:
        problems.append('%s %s: %d matches, expected 1  (%s / %s)' % (ref, page, len(found), old_bold, old_line[:60]))
        return
    pages[page] = re.sub(pat, lambda m: m.group(1) + new_bold + m.group(2) + new_line + m.group(3), pages[page])


# ---------------- Home (index.html), T-17 ----------------
text('index.html',
     "I'm Josef. I build AI tools that take real work off your plate, and I explain every one of them in plain English. Pick the one that sounds like you, and I'll take it from here.",
     "Hey, I'm Josef, your dragoman. That's the old word for the guide travelers trusted in a strange land. Out there, AI is loud and confusing. In here, I'll walk you through it one plain step at a time.",   # T-34 (Nov 20, 2026); T-45 (Nov 23, 2026)
     ref='V1')
text('index.html',
     "For small businesses and nonprofits in Sonoma County. Hand me the videos you never get to, the lessons in a binder or the chore that eats your week. I'll turn it into reels, an app with your name on it, or a chore that runs itself, and show you that it works.",
     "For shops and nonprofits around Sonoma County. Maybe it's a phone full of videos you'll never edit. Maybe it's a binder of lessons, or the one chore that eats every Thursday. Hand it over. You get back finished reels, an app with your name on it, or a chore that does itself, and you watch it work before you decide on the build.",
     ref='V2')
item('index.html',
     "A person checks everything first.",
     "Nothing reaches your customers or your live systems until a real person has looked at it.",
     "Nothing goes out until a person has looked at it.",
     "First me, then you.",
     ref='V3')
item('index.html',
     "You can check my work without me.",
     "The tests stay with you, so you can rerun them any time you like.",
     "You never have to take my word for it.",
     "The checks stay with you, and you can run them again any time.",
     ref='V4')
item('index.html',
     "The first step is small and the price is fixed.",
     "If the honest answer is that you don't need me, that's the answer you get.",
     "The first step is small and the price is fixed.",
     "And if you don't need me, I'll tell you. I sold insurance for years and learned to give the honest answer even when it cost me the sale.",
     ref='V5')
item('index.html',
     "What's yours stays yours.",
     "Your data stays in your own accounts, and the contract says so.",
     "What's yours stays yours.",
     "Your accounts, your data, and it's in the contract.",
     ref='V6')

# ---------------- Harness lines 01, T-19 (Nov 13, 2026) ----------------
# Each new line won a blind reader test against the line it replaces.
# Only lines that a pass before this one writes live here; lines that sit
# in a template or a tools/*.py file are changed there.
text('index.html',
     "The Blueprint · $1,500 · two weeks · counts toward the build",
     "The Blueprint: two weeks, $1,500, fixed. If you go ahead, the $1,500 comes off the price.",
     ref='W1')
text('index.html',
     "you watch it work before you decide on the build",
     "you watch it work before you decide to go ahead",
     ref='W2')
text('local.html',
     "Two weeks · fixed price · the $1,500 comes off your build",
     "Two weeks · fixed price · the $1,500 comes off the price if you go ahead",
     ref='W3')
# W5 retired by T-22 K8: the cooking app card's headline is now in _build/work.html.
# W25 retired by T-22 K3: its section ("What I built") is off case-reels.
text('mainframe.html',
     "The code never divides by 100. The field definition allows two readings. Pick one:",
     "The code never divides by 100. The field definition allows two readings. See each one:",
     ref='W29')
text('mainframe.html',
     "Every record tells a different story. <span",   # T-34: a span, not <em>
     "The code, the layouts, the job setup and the data each tell a different story. <span",
     ref='W30')
text('mainframe.html',
     '>Send one program <span style="color: #A93F17">and see what I find</span>',   # T-34: a span, not <em>
     '>Tell me about one program <span style="color: #A93F17">and see what I\'d look at first</span>',
     ref='W31')
text('briefing.html',
     '<span class="label">Which programs</span>',
     '<span class="label">Which programs (a rough description is enough)</span>',
     ref='W33')

# ---------------- T-20 (Nov 15, 2026): walk fixes, three word changes ----------------
# F3: Exhibit B's "Caught by" agrees with the Limits note (the output comparison hasn't
# been done yet). The value is in the exhibit as first drawn and in the tabs' state data,
# so both change and every state of the tabs carries it.
text('mainframe.html',
     '>Caught by</span><strong style="text-align: right">Comparing the output, not reading the code</strong>',
     '>Caught by</span><strong style="text-align: right">Comparing the code, line by line</strong>',
     ref='F3')
text('mainframe.html',
     '"Caught by", "v": "Comparing the output, not reading the code"',
     '"Caught by", "v": "Comparing the code, line by line"',
     ref='F3')
# F4: the hero button. Where it points does not change.
text('mainframe.html',
     '>Send one program</a>',
     '>Tell me about one program</a>',
     ref='F4')

# ---------------- T-22 (Nov 16, 2026): Kids Kitchen, process and scale ----------------
# Josef's lines, word for word. local.html's words come from the canvas through plain.py
# and intent.py, so they change here, the same way T-19 and T-20 did it; the canvas file
# isn't touched. case-reels and work change in their templates, Studio in studio.json and
# shipped.json.
HERO_ROW = ('<div style="display: flex; justify-content: space-between; gap: 16px; align-items: baseline">'
            '<span style="color: #3E4640">%s</span><span style="flex: 1; border-bottom: 1px dotted #A6AAA2; '
            'transform: translateY(-4px)"></span><strong style="font-weight: 700; color: #16201C; white-space: nowrap">%s</strong></div>')
RC_ROW = ('<div style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 18px; padding: 12px 0; '
          'border-top: 1px solid #2B3D35; align-items: baseline"><span style="font-size: 14px; color: #B5C2BA; '
          'line-height: 1.45">%s</span><strong style="font-size: 18px; font-weight: 700; color: #F07A4E; text-align: right">%s</strong></div>')


def rc_json(rows):
    return '"rows": [' + ', '.join('{"k": "%s", "v": "%s"}' % r for r in rows) + ']'


# K4: the hero "Real result" card. Title and client line stay.
text('local.html',
     '>One cooking class, filmed on a phone, turned into a finished reel. August 2026.</p>',
     ">A 40-reel series for a children's nonprofit, cut by one engine.</p>",
     ref='K4')
K4_OLD = [('Clips in a typical class', '16 to 20'), ('Sorts the footage at', '29× real time'), ('Captioned steps', '9'),
          ('Feedback notes it now checks for itself', '3 of 3'), ('Computer time, start to finish', '~4 min')]
K4_NEW = [('Editing each reel, before', 'An evening'), ('Now', '~4 min'), ('Reels in the series', '40'),
          ('Posted without their yes', '0')]
text('local.html', ''.join(HERO_ROW % r for r in K4_OLD), ''.join(HERO_ROW % r for r in K4_NEW), ref='K4')

# K5: Results, Reels tab. Drawn once in the page and once in the tabs' state data, so both change.
# The date (AUG 2026) and the "Open the repo" link stay.
K5_OLD = [('Clips in a typical cooking-class shoot', '16 to 20'), ('Captioned steps in the finished reel', '9'),
          ('Machine time for the whole episode', '~4 min'), ('Mistakes the client caught in the first three rounds', '3 of 3 fixed'),
          ('Reels posted without the client approving them', '0')]
K5_NEW = [('Editing each reel, before', 'An evening'), ('Engine time each reel', '~4 min'), ('Reels in the series', '40'),
          ('Her notes it now checks on every reel', '3 of 3'), ('Posted without her yes', '0')]
K5_NOTE_OLD = ('Those three were uneven caption boxes, square corners and single words stranded on their own line. '
               'The tool now checks for all three on every reel, so nobody has to catch them twice.')
K5_NOTE = 'Every note she gives becomes a rule the engine checks on every reel after, so nobody catches the same thing twice.'
text('local.html', '>One shoot, one finished reel</h3>', '>Forty reels, one engine.</h3>', ref='K5')
text('local.html', '"title": "One shoot, one finished reel"', '"title": "Forty reels, one engine."', ref='K5')
text('local.html', ''.join(RC_ROW % r for r in K5_OLD), ''.join(RC_ROW % r for r in K5_NEW), ref='K5')
text('local.html', rc_json(K5_OLD), rc_json(K5_NEW), ref='K5')
text('local.html', '>' + K5_NOTE_OLD + '</p>', '>' + K5_NOTE + '</p>', ref='K5')
text('local.html', '"note": "' + K5_NOTE_OLD + '"', '"note": "' + K5_NOTE + '"', ref='K5')
# K5: a tap-to-see source per orange number, in row order. "3 of 3" and "0" keep theirs.
text('local.html',
     '''    reels: [
      "Each class gives 16 to 20 clips, from ten seconds to a couple of minutes each.",
      "One caption for each recipe step in the finished reel.",
      "Computer time from the log, from the first scan to the finished file. Time people spend reviewing comes on top of this.",
      "The client's three notes from the first rounds. The tool now checks for each one automatically.",
      "Every reel waits for the client's yes before it posts. None has gone out without it."
    ],''',
     '''    reels: [
      "Before the engine, she cut each class by hand. That took an evening.",
      "The engine's own log for the August 2026 shoot: about four minutes from clips in to finished reel.",
      "The full series the program has planned.",
      "The client's three notes from the first rounds. The tool now checks for each one automatically.",
      "Every reel waits for the client's yes before it posts. None has gone out without it."
    ],''',
     ref='K5')

# K7: the app offer, "HOW YOU KNOW IT WORKS".
text('local.html',
     'The app refuses broken entries, like a recipe with no photo. It runs hundreds of automatic checks every time it changes, and your staff try it before any family does.',
     'Your staff try every update before any family sees it.',
     ref='K7')

# ---------------- T-23 (Nov 16, 2026): Kids Kitchen, the person back in ----------------
# Josef's lines, word for word. Each replaces the T-22 line just written above, so the
# T-22 edits still have to hit first. case-reels (K3b) and work (K8b) change in their
# templates, Studio (K8b) in studio.json.
# K5b: the note under the Reels tab's rows, drawn once in the page and once in the tabs'
# state data, so it reads the same after the tabs switch away and back. Rows and sources stay.
K5B_NOTE = ('She caught three things in the first rounds: uneven caption boxes, square corners and words left '
            'alone on a line. The engine now checks for all three on every reel.')
text('local.html', '>' + K5_NOTE + '</p>', '>' + K5B_NOTE + '</p>', ref='K5b')
text('local.html', '"note": "' + K5_NOTE + '"', '"note": "' + K5B_NOTE + '"', ref='K5b')
# K7b: the app offer, "HOW YOU KNOW IT WORKS".
text('local.html',
     '>Your staff try every update before any family sees it.<',
     ">It won't take a broken entry, like a recipe with no photo, and your staff try every update before any family sees it.<",
     ref='K7b')

# ---------------- T-24 (Nov 17, 2026): Exhibit A says what is stored ----------------
# Josef's lines, word for word. Every label names what the field stores, and the bank
# comes out (the public run is a synthetic example). The old words come from the canvas
# through plain.py and W29; the canvas file isn't touched. comp3 (A6, A7) changes in
# _build/comp3.html. Exhibit A's numbers and its starting state stay as they are.
# A1: the line above the two buttons, chained after W29 (which still has to hit).
text('mainframe.html',
     "The code never divides by 100. The field definition allows two readings. See each one:",
     "The code never divides by 100, and the field fits 3.5% stored either way. See each one:",
     ref='A1')
# A2, A3: the two buttons. Their data-reading values, styles and starting state stay.
text('mainframe.html', '>A fraction</button>', '>Stored as 0.035</button>', ref='A2')
text('mainframe.html', '>A percentage</button>', '>Stored as 3.5</button>', ref='A3')
# A4: the verdict for the fraction state. It is drawn only from the page's state data
# (D.readings.fraction.ex.verdict); the percent verdict stays as plain.py wrote it.
text('mainframe.html',
     '"verdict": "What the bank means: 3.5% a year, stored as a fraction."',
     '"verdict": "Same code, right answer: 3.5% a year."',
     ref='A4')
# A5: the "4 · THE REAL DATA" card, the caption under 00 03 50 0C (plain.py writes the old line).
text('mainframe.html',
     ">The only one that can't be wrong about what your business actually stored.</p>",
     ">Reads 0.035: a fraction. The only one that can't be wrong about what your business actually stored.</p>",
     ref='A5')

# ---------------- T-33 (Nov 20, 2026): the site says what I do ----------------
# Josef's lines, word for word ("yes all, dont change bird league line"). Only the lines
# this pass already writes change here (R2 after W2, R4's rows and line after K4), plus
# R9's new block; the others change where they are written (plain.py, the canvas, the
# templates, tools/chrome.py, studio.json). Each still has to hit exactly once.
# R2: the Local Route card on the home page, the whole paragraph (V2, then W2).
text('index.html',
     "For shops and nonprofits around Sonoma County. Maybe it's a phone full of videos you'll never edit. Maybe it's a binder of lessons, or the one chore that eats every Thursday. Hand it over. You get back finished reels, an app with your name on it, or a chore that does itself, and you watch it work before you decide to go ahead.",
     "For shops and nonprofits around Sonoma County. Whatever keeps sliding to the bottom of the list, hand it over. Videos nobody edits, follow-ups nobody sends, the spreadsheet everyone avoids, the app you keep meaning to make. I build the AI tool that does it, and you watch it work before you decide to go ahead.",
     ref='R2')
# R4: the proof card beside the Local headline. Its labels are plain.py's (REAL RESULTS,
# BUILT WITH AI). No line under them, four rows, no client line. The rows are the card's
# own dotted rows (HERO_ROW): on wide screens a label wraps beside its value, and at 420px
# and under enhance.py's phone rule (T-20 F8) puts the label on its own line with the
# leader and value under it, so no type shrinks and no word is cut. That rule finds the
# rows as the card's second block now (enhance.py, T-33), and above 420px keeps each dotted
# leader at least 24px wide, as these longer labels wrap beside their values there. The rows
# take the 14px the line under the labels used to leave.
R4_ROWS = [('A 40-reel series for a nonprofit', '~4 min a reel'),
           ('A teaching app, iPhone, iPad, Android and web', 'Over 700 tests'),   # T-43 (Nov 23, 2026): was '535 tests'
           ('A birding league app, with real players in testing', 'zero lines of code to start'),   # T-46 (Nov 23, 2026): was 'A birding league with real players'
           ('A banking COBOL program, checked in public', '2 AIs compared')]
R4_ROW = HERO_ROW
text('local.html',
     "\n          <p style=\"margin: 12px 0 14px; color: #3E4640\">A 40-reel series for a children's nonprofit, cut by one engine.</p>",
     '', ref='R4')
text('local.html',
     '<div style="display: flex; flex-direction: column; gap: 7px">\n            ' + ''.join(HERO_ROW % r for r in K4_NEW),
     '<div style="display: flex; flex-direction: column; gap: 7px; margin-top: 14px">\n            ' + ''.join(R4_ROW % r for r in R4_ROWS),
     ref='R4')
text('local.html',
     '\n          <div style="margin-top: 16px; padding-top: 12px; border-top: 1.5px dashed #9AA097; display: flex; justify-content: space-between; gap: 12px; color: #5C625C; font-size: 12px">'
     "\n            <span>Client: a Sonoma County children's nonprofit</span>\n          </div>",
     '', ref='R4')
# R9: a fourth block after "Busywork, automated", the same card, no rows and no data-card
# (it isn't a pick's match, and final.py lists only the three priced offers). The empty
# first row stands where the other three keep their hidden "YOUR MATCH", so the four
# headings sit level. The grid holds two columns at most, so four sit two by two from
# 700px and one under another below that.
text('local.html',
     '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(340px, 100%), 1fr)); gap: 20px; align-items: stretch">\n\n      <article class="card-lift" data-card="reels"',
     '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, max(340px, calc(50% - 11px))), 1fr)); gap: 20px; align-items: stretch">\n\n      <article class="card-lift" data-card="reels"',
     ref='R9')
text('local.html',
     '<strong>Build from $3,000</strong> · support from $750/month</p>\n      </article>\n',
     '<strong>Build from $3,000</strong> · support from $750/month</p>\n      </article>\n'
     '\n      <article class="card-lift" style="display: flex; flex-direction: column; gap: 18px; padding: 30px 28px; background: #FBF8F1; border-radius: 2px; border: 2px solid #16201C; box-shadow: 6px 6px 0 #16201C;">'
     '\n        <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px"></div>'
     "\n        <h3 style=\"margin: 0; font-family: 'Big Shoulders Display', Impact, sans-serif; font-weight: 800; text-transform: uppercase; font-size: 40px; line-height: 0.95\">Something else</h3>"
     '\n        <p style="margin: 0; font-size: 19px; font-weight: 600; line-height: 1.35">Not on this list? Tell me anyway. The Blueprint works the same for any job: I watch how it gets done, build a sample from your material, and give you a fixed price before any building starts.</p>'
     "\n        <p style=\"margin: auto 0 0; padding-top: 16px; border-top: 1.5px solid #16201C; font-family: 'JetBrains Mono', monospace; font-size: 14px\"><strong>Priced in the Blueprint</strong></p>"
     '\n      </article>\n',
     ref='R9')

# ---------------- T-46 (Nov 23, 2026): the launch fixes, Josef's four calls ----------------
# Josef's words, exactly as approved (old, then new). Only lines a pass before this one writes
# (the canvas through plain.py and intent.py) change here; call.html, start.html, work.html and
# tools/receipt.py change in their own files, the local status line in build.py, and the R4 row
# above in R4_ROWS. Each still has to hit exactly once.
# 2a: the headline. The home card's title, then Local's h1 (the orange part stays the span).
text('index.html', '>AI that works the first day<', '>See it working in a week<', ref='T46-2a')
text('local.html',
     '>AI that works the first day <span style="color: #F07A4E">and keeps working</span></h1>',
     '>See it working in a week, <span style="color: #F07A4E">and keep it working.</span></h1>',
     ref='T46-2a')
# 2b: split payment, in the Blueprint block.
text('local.html', "If you don't, the plan is still yours.",
     "If you don't, the plan is still yours. Half is due up front and half after the Day 7 sample. Stop at Day 7 and you owe nothing more.",
     ref='T46-2b')
# 2d: ownership, the FAQ "Who owns what?" (final.py reads the FAQ data from here).
text('local.html', 'The tool underneath is mine, and you can keep using it for as long as you like.',
     'The tool underneath is mine, and you can keep using it for good, with or without support. Support pays for fixes, and for me to watch it when something it depends on changes.',
     ref='T46-2d')
# 4a, 4b, 4c, 4d: accuracy on local.html. 4b: the About section's "Hey, I'm Josef." heading goes,
# so it starts "I grew up in Alaska"; the hero keeps its "I'm Josef.".
text('local.html', 'until MS took that work from him', 'until multiple sclerosis took that work from him', ref='T46-4a')
text('local.html', '<section id="josef" aria-labelledby="josef-h" ', '<section id="josef" ', ref='T46-4b')
text('local.html',
     "\n      <h2 id=\"josef-h\" style=\"margin: 0; font-family: 'Big Shoulders Display', Impact, sans-serif; font-weight: 800; "
     "text-transform: uppercase; font-size: clamp(44px, 5.2vw, 72px); line-height: 0.9\">Hey, I'm Josef.</h2>",
     '', ref='T46-4b')
text('local.html', '>Most AI projects quietly break by month two<', ">Most AI tools I've seen quietly break by month two<", ref='T46-4c')
text('local.html', 'went from zero lines of code to real users and an App Store submission',
     'went from zero lines of code to real players in testing and an App Store submission', ref='T46-4d')
# 4f: mainframe.html. Exhibit D is drawn from the tabs' state data only.
# T-47 (Nov 24, 2026, PROOF-1): Local links to the two sample pages, from the Day 14 line and the monthly report.
text('local.html', "Or a straight answer that you don't need me.</span>",
     "Or a straight answer that you don't need me. <a href=\"sample-blueprint.html\" style=\"color: #A93F17; font-weight: 600; white-space: nowrap\">See a sample plan →</a></span>",
     ref='P1-a')
text('local.html', "anything that broke and how I fixed it.</p>",
     "anything that broke and how I fixed it. <a href=\"sample-report.html\" style=\"color: #A93F17; font-weight: 600; white-space: nowrap\">See a sample report →</a></p>",
     ref='P1-b')
# T-47 (Nov 24, 2026, Josef: "we call it \"your pile\" way too often, that is not a common phrase"): "pile" off Local's headings.
text('local.html', '>Start here. What do you have a pile of?</h2>', '>Start here. What would you hand me?</h2>', ref='P1-c')
text('local.html', '>Bring your pile</h2>', '>Bring the work</h2>', ref='P1-d')
text('local.html', '>Free tools for your pile</h2>', '>Free tools</h2>', ref='P1-e')
text('mainframe.html', '{"k": "Lines changed", "v": "1"}', '{"k": "Lines changed", "v": "2"}', ref='T46-4f')
text('mainframe.html', 'Fixing that one line took both from unusable to mostly correct.',
     "Fixing that line, along with a second change I didn't control for, took both from unusable to mostly correct.",
     ref='T46-4f')
text('mainframe.html', 'THE FILE SETUP (JCL)', 'THE FILE SETUP (PROGRAM)', ref='T46-4f')
text('mainframe.html', 'THE REAL DATA', 'THE STORED DATA', ref='T46-4f')
text('mainframe.html', '>Four steps, each with a fixed scope and a fixed price<',
     '>Four steps, each with a fixed scope and a price agreed before it starts<', ref='T46-4f')
# 3m: the Limits line reads at the page's body size and color, in the same place. No word changes.
text('mainframe.html', '<p style="margin: 0; font-size: 14px; color: #5D6576; max-width: 72ch">Limits, plainly:',
     '<p style="margin: 0; max-width: 72ch">Limits, plainly:', ref='T46-3m')

# ---------------- T-48 (Nov 24, 2026, FIX-R2): two sides, support optional, three lines, R-02 fixes ----------------
# Josef's words, exactly as approved (old, then new). Only lines a pass before this one writes (the canvas through
# plain.py and intent.py, and the edits above) change here; the descriptions change in plain.py (home) and build.py
# (Local), the tools in tools/*.py, start, work and case-reels in their templates. Each edit first checks that its new
# words aren't already on the page, then has to hit exactly once.
def t48(page, old, new, ref):
    if new in pages[page]:
        problems.append('%s %s: already applied  (%s)' % (ref, page, new[:80]))
        return
    text(page, old, new, ref)


# R2-1 (A1): the home intro, after the dragoman line.
t48('index.html', "Out there, AI is loud and confusing. In here, I'll walk you through it one plain step at a time.",
    "There's a lot of hype around AI. I'll show you, in plain words, what it can do for your business.", ref='R2-1')
# R2-2 (D1): the Local Route card on the home page (R2 above wrote it).
t48('index.html', '>For shops and nonprofits around Sonoma County. ', '>For small businesses around Sonoma County. ', ref='R2-2')
# R2-3 (A2) and R2-4 (A3): Local, after the month-two story. "one-page" keeps the no-break span final.py gives it.
t48('local.html', 'I build for month two from the start.',
    "So I build it and test it on your real work, the way you'll use it every day. Everything I build is intended to keep working long after the demo.",
    ref='R2-3')
t48('local.html', 'Every month you get a one-page report you can read in a minute.',
    'With support, every month you get a one-page report you can read in a minute.', ref='R2-4')
# R2-5 (A4): About, the last paragraph's last sentence.
t48('local.html', 'That system is why the work comes out right.',
    'It catches mistakes, including mine, before you see the work.', ref='R2-5')
# R2-6 (B1): the busywork card's price line (R9 above wrote it). final.py reads the offer's description from this line.
t48('local.html', '<strong>Build from $3,000</strong> · support from $750/month</p>',
    '<strong>Build from $3,000</strong> · optional support from $750/month</p>', ref='R2-6')
# R2-7 (C1) and R2-8 (D4): "We're a good fit if".
t48('local.html', '<li>One person on your side can say yes.</li>',
    '<li>Someone on your side can say yes within two weeks.</li>', ref='R2-7')
t48('local.html', '<li>Small businesses and nonprofits in Sonoma County and the North Bay. Remote works too.</li>',
    '<li>Small businesses in Sonoma County and the North Bay. Remote works too.</li>', ref='R2-8')
# R2-9 (D5): the monthly report step. The sentence keeps its period; P1-b's sample link stays after the paragraph.
t48('local.html', 'One page you can read in a minute and send to your board. It shows',
    'One page you can read in a minute. It shows', ref='R2-9')
# R2-10 (D7): Nonprofits, a short section after the fit and not-a-fit cards, before About, inside the same band.
# Its heading is set like "We're a good fit if" (h3, same face, weight and size); the text is the page's own body text.
# No new colors. Not in the header or the Menu.
t48('local.html',
    '    </div>\n  </div>\n</section>\n\n<!-- ============ LETTER ============ -->',
    '    </div>\n'
    '\n    <div style="display: flex; flex-direction: column; gap: 12px; max-width: 64ch">'
    "\n      <h3 id=\"nonprofits\" style=\"margin: 0; font-family: 'Big Shoulders Display', Impact, sans-serif; font-weight: 800; text-transform: uppercase; font-size: 30px\">Nonprofits</h3>"
    '\n      <p style="margin: 0">I do the same work for nonprofits at a steep discount. I like building for people who do good work. Most of these jobs come by word of mouth, so if someone sent you, tell me on the call.</p>'
    '\n    </div>\n'
    '  </div>\n</section>\n\n<!-- ============ LETTER ============ -->',
    ref='R2-10')
# R2-11 (E2): each quiz pick's link goes to its own card in "Three ready to go", not the top of the section.
# The cards get ids; the picks' links (in the page's state data) point at them. "Not sure" keeps #blueprint.
for k, cta in (('reels', 'See reels'), ('app', 'See custom apps'), ('flow', 'See automation')):
    t48('local.html', '<article class="card-lift" data-card="%s"' % k,
        '<article id="engine-%s" class="card-lift" data-card="%s"' % (k, k), ref='R2-11')
    t48('local.html', '"href": "#engines", "cta": "%s"' % cta, '"href": "#engine-%s", "cta": "%s"' % (k, cta), ref='R2-11')
# R2-12 (E9): Day 1.
t48('local.html', 'I come to you, anywhere in Sonoma County, and watch',
    'I come to you, anywhere in Sonoma County, or we meet on a video call, and watch', ref='R2-12')

# ---------------- write ----------------
if problems:
    print('VOICE: %d edit(s) missed, nothing written:' % len(problems))
    for p in problems:
        print('  ' + p)
    sys.exit(1)
for name, s in pages.items():
    (OUT / name).write_text(s, encoding='utf-8')
print('voice2: applied to %d pages' % len(pages))
