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
     "Hey, I'm Josef. Take a deep breath. AI is a set of power tools, and I already know how to run them. Tell me the job that never gets done, and I'll take it from here.",
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

# ---------------- write ----------------
if problems:
    print('VOICE: %d edit(s) missed, nothing written:' % len(problems))
    for p in problems:
        print('  ' + p)
    sys.exit(1)
for name, s in pages.items():
    (OUT / name).write_text(s, encoding='utf-8')
print('voice2: applied to %d pages' % len(pages))
