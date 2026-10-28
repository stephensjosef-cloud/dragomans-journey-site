#!/usr/bin/env python3
"""Intent pass, Oct 28 2026.

Josef: "People don't go out of their way to type and place something unless it
really means something and is INTENTIONAL. Humans don't just throw words around
wherever on the off chance it will help whoever's looking. THAT instinct is very AI."

Applies the audit in the vault: Claude outputs/2026-10-28-intent-audit-dragomans-journey.md
Each edit carries the audit's line ID (L1 to L61, F1 to F4).

Runs last, after plain.py, on the built output:  python3 intent.py out
Every edit must hit exactly as many times as it says, or the build fails.
"""
import re
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
pages = {p.name: p.read_text(encoding='utf-8') for p in sorted(OUT.glob('*.html'))}
problems = []


def sub(page, pattern, repl, n=1, ref=''):
    """Regex replace in one page; must match exactly n times."""
    new, k = re.subn(pattern, repl, pages[page], flags=re.S)
    if k != n:
        problems.append('%s %s: %d matches, expected %d  (%s)' % (ref, page, k, n, pattern[:80]))
        return
    pages[page] = new


def text(page, old, new, n=1, ref=''):
    sub(page, re.escape(old), new.replace('\\', r'\\'), n, ref)


# ---------------- Home (index.html) ----------------
sub('index.html', r'\s*<p style="[^"]*">Where are you coming from\?</p>', '', ref='L1')
sub('index.html', r'\s*<!-- elevation profile -->\s*<div aria-hidden="true".*?COBOL · BANKS, INSURERS, AGENCIES</span>\s*</div>\s*</div>', '', ref='L2')
text('index.html', '>ROUTE 01 · THE LOCAL ROUTE<', '>THE LOCAL ROUTE<', ref='L3')
text('index.html', '>ROUTE 02 · THE MAINFRAME ROUTE<', '>THE MAINFRAME ROUTE<', ref='L3')
text('index.html', 'The Survey · one group of programs · fixed fee · counts toward the next step',
     'The Survey · one group of programs · from $8,000 · counts toward the next step', ref='L4/F4')
sub('index.html', r'\s*<!-- same method, different altitude -->\s*<section aria-labelledby="alt-h".*?</section>', '', ref='L5')
sub('index.html', r'<script>\s*\(function \(\) \{\s*var V = .*?</script>\s*', '', ref='L5 script')
sub('index.html', r'<span style="[^"]*">(?:i|ii|iii|iv)\.</span>', '', n=4, ref='L6')

# ---------------- Local (local.html) ----------------
for anchor in ('#engines">What I build', '#proof">Results', '#route">How it works', '#josef">About', '#faq">Questions'):
    sub('local.html', r'\s*<a href="' + re.escape(anchor) + r'</a>', '', ref='L9')
sub('local.html', r'\s*<p class="rise"[^>]*>Santa Rosa, CA · AI help for small businesses and nonprofits</p>', '', ref='L10')
sub('local.html', r'\s*<span[^>]*>Vertical, ready to post</span>', '', ref='L11')
sub('local.html', r'\s*<div[^>]*>APPROVED BY A PERSON</div>', '', ref='L11')
sub('local.html', r'\s*<div[^>]*>\s*<div[^>]*>\s*<span[^>]*>32%</span>.*?</div>\s*</div>\s*<p[^>]*>Source: <a[^>]*>Bluehost survey[^<]*</a></p>', '', ref='L13')
sub('local.html', r'\s*<span[^>]*>Tap one and I\'ll show you where to start\.</span>', '', ref='L14')
sub('local.html', r'(<button type="button" aria-pressed="false" data-pick="[a-z]+"[^>]*>)<span[^>]*>0[1-4]</span>', r'\1', n=4, ref='L14')
sub('local.html', r'<span[^>]*>NO\. [123]</span>\s*', '', n=3, ref='L16')
text('local.html', '>Real results, not promises<', '>Results<', ref='L17')
text('local.html', "Every number here comes from real work I can show you. If I can't show it, it isn't here. <a", '<a', ref='L17')
sub('local.html', r'\s*<p[^>]*>Three steps, with dates we agree on up front, so you always know what\'s next\.</p>', '', ref='L18')
sub('local.html', r'\s*<figure[^>]*>\s*<div[^>]*><strong[^>]*>MONTHLY REPORT · \[MONTH\]</strong>.*?</figure>', '', ref='L19')
sub('local.html', r'<section aria-labelledby="compare-h"([^>]*)>(\s*<div[^>]*>)\s*<h2 id="compare-h"[^>]*>How this compares</h2>\s*<div[^>]*>\s*<table.*?</table>\s*</div>',
    r'<section aria-label="Who this is for"\1>\2', ref='L20')
sub('local.html', r'\s*<p[^>]*>Josef Stephens · Santa Rosa, California · raised in Alaska</p>', '', ref='L22')
text('local.html', ' If your Blueprint says you don\'t need me, that is what it will say.', '', ref='L27')
text('local.html', ' That\'s why a build costs less than starting from scratch.', '', ref='L15')
text('local.html', "Kids' programs get stricter rules: no accounts and no child data, ever.",
     "Kids' programs get stricter rules: no child accounts and no child data, ever.", ref='F3')
sub('local.html', r'Twenty minutes of my full attention, somewhere in Santa Rosa with good coffee\. (Sign up and you\'ll hear the date first\.)', r'\1', ref='L28')
sub('local.html', r'<span([^>]*)>It\'s <span id="sr-clock">([^<]*)</span> in Santa Rosa\. <span id="sr-status"></span></span>',
    r'<span\1><span id="sr-clock" hidden>\2</span><span id="sr-status"></span></span>', ref='L29')
sub('local.html', r'\s*<section aria-labelledby="other-route".*?</section>', '', ref='L30')
sub('local.html', r'\s*<span[^>]*>Dragoman \(n\.\): a guide and interpreter for travelers crossing country where they didn\'t speak the language\.</span>', '', ref='L31')
sub('local.html', r'\s*<span[^>]*>Made by Josef Stephens in Santa Rosa, California</span>', '', ref='L31')
text('local.html', '{"k": "Automatic checks on the latest version", "v": "324"}',
     '{"k": "Automatic checks on the latest version", "v": "535"}', ref='F1')
text('local.html', '"The app\'s automatic checks on the latest version, Oct 7, 2026."',
     '"The app\'s automatic checks on the latest version, Oct 27, 2026."', ref='F1')
text('local.html', '{"k": "Accounts or child data collected", "v": "None"}',
     '{"k": "Child accounts or child data collected", "v": "None"}', ref='F3')


def drop_faq(page, drop_questions, ref):
    """Remove FAQ items by question and renumber the rest (the script pairs button i with faq-a-i)."""
    s = pages[page]
    items = list(re.finditer(r'<div[^>]*><button type="button" aria-expanded="(?:true|false)" aria-controls="faq-a-\d+" data-faq="\d+".*?</p></div>', s, re.S))
    if len(items) != 8:
        problems.append('%s %s: %d FAQ items, expected 8' % (ref, page, len(items)))
        return
    kept, dropped = [], 0
    for m in items:
        if any(q in m.group(0) for q in drop_questions):
            dropped += 1
            continue
        kept.append(m.group(0))
    if dropped != len(drop_questions):
        problems.append('%s %s: dropped %d FAQ items, expected %d' % (ref, page, dropped, len(drop_questions)))
        return
    renum = []
    for i, block in enumerate(kept):
        block = re.sub(r'aria-controls="faq-a-\d+" data-faq="\d+"', 'aria-controls="faq-a-%d" data-faq="%d"' % (i, i), block)
        block = re.sub(r'<p id="faq-a-\d+"', '<p id="faq-a-%d"' % i, block)
        renum.append(block)
    pages[page] = s[:items[0].start()] + ''.join(renum) + s[items[-1].end():]


drop_faq('local.html', ['What happens when it breaks?', 'Can you fix the AI thing someone else built for us?'], 'L24/L26')

# ---------------- Mainframe (mainframe.html) ----------------
# L32 cut all six jump links; the second pass (D3) puts back the three an evaluator scans for.
sub('mainframe.html', r'(<div class="mnav"[^>]*>).*?(</div>)',
    r'\1\n      <a href="#s2">Exhibits</a>\n      <a href="#s3">Steps and prices</a>\n      <a href="#s4">The report</a>\n    \2', ref='L32/D3')
sub('mainframe.html', r'\s*<p class="fade"[^>]*>Moving off COBOL with AI · with proof nothing changed</p>', '', ref='L33')
for n in range(1, 5):
    sub('mainframe.html', r'(<section id="s%d"(?:(?!</section>).)*?)\s*<span[^>]*>0%d</span>' % (n, n), r'\1', ref='L35')
sub('mainframe.html', r'\s*<div[^>]*>\s*<span[^>]*>&gt;70%</span>.*?</div>', '', ref='L36')
sub('mainframe.html', r'\s*<li[^>]*>Gartner forecast, Jun 18, 2026\..*?</li>', '', ref='L36')
for old, new in (('5', '4'), ('6', '5'), ('7', '6')):
    sub('mainframe.html', r'(<sup[^>]*>)' + old + r'(</sup>)', r'\g<1>' + new + r'\2', ref='L36 note %s' % old)
sub('mainframe.html', r'\s*<span[^>]*>BUILT FOR YOUR SYSTEMS</span>', '', ref='L38')
sub('mainframe.html', r'\s*<span[^>]*>TRANSLATION WITH A CHECKPOINT</span>', '', ref='L38')
sub('mainframe.html', r'<div[^>]*><button type="button" aria-expanded="false" aria-controls="toc-b-6" data-toc="6"[^>]*>(?:(?!</div>).)*?What this does not prove.*?</p></div>', '', ref='L40')
sub('mainframe.html', r'aria-controls="toc-b-7" data-toc="7"([^>]*>)(<span[^>]*>)08(</span>)', r'aria-controls="toc-b-6" data-toc="6"\1\g<2>07\3', ref='L40 renumber')
sub('mainframe.html', r'<p id="toc-b-7"', '<p id="toc-b-6"', ref='L40 renumber')
sub('mainframe.html', r'\s*<!-- ======= THE OTHER ROUTE ======= -->\s*<section aria-labelledby="other-h".*?</section>', '', ref='L43')
sub('mainframe.html', r'\s*<span[^>]*>Correspondence</span>', '', ref='L44')
sub('mainframe.html', r'\s*<span[^>]*>Set in Newsreader, Instrument Sans and JetBrains Mono\.</span>', '', ref='L46')
sub('mainframe.html', r'\s*<span[^>]*>Dragoman \(n\.\): an interpreter and guide for travelers crossing country where they didn\'t speak the language\.</span>', '', ref='L47')

# ---------------- second pass: say it directly (Oct 28, 1:45 PM) ----------------
text('index.html', "I'll turn it into something that runs on its own, and show you that it works.",
     "I'll turn it into reels, an app with your name on it, or a chore that runs itself, and show you that it works.", ref='D1')
text('mainframe.html', 'Start with the Survey · fixed fee', 'Start with the Survey · from $8,000', ref='D2')

# ---------------- Start, briefing, work, case study, decoder, 404 ----------------
text('start.html', " You don't pay anything today.", '', ref='L48')
sub('briefing.html', r'\s*<span class="label"[^>]*>Correspondence</span>', '', ref='L50')
text('briefing.html', ">The programs you're least sure about<", '>Which programs<', ref='L51')
sub('work.html', r'\s*<span class="mono"[^>]*>THE WORK</span>', '', ref='L54')
sub('work.html', r'\s*<p[^>]*>Every number here comes from real work I can show you\. Tap a card to see the details\.</p>', '', ref='L55')
sub('work.html', r'\s*<span class="mono"[^>]*>SHOW</span>', '', ref='L56')
text('work.html', '<p class="num">324 tests</p>', '<p class="num">535 tests</p>', ref='F1')
text('work.html', '<h2>A seasonal cooking app for teachers and families</h2>', '<h2>A seasonal cooking app for teachers</h2>', ref='F2')
text('work.html', "<p>What's in season, a grocery list that scales to however many people are cooking, and pictures and read-aloud for the youngest cooks. iPhone, iPad and Android.</p>",
     '<p>Seasonal recipes a teacher leads the class through, a grocery list that scales to the class, and recipe pages that print like the program\'s own cards. iPhone, iPad and Android.</p>', ref='F2')
text('case-reels.html', 'a seasonal cooking app for teachers and families, on iPhone, iPad and Android.',
     'a seasonal cooking app for teachers, on iPhone, iPad and Android.', ref='F2')
sub('comp3.html', r'\s*<span class="label"[^>]*>Why this exists</span>', '', ref='L59')
sub('404.html', r'\s*<span style="[^"]*">Josef Stephens · Santa Rosa, California</span>', '', ref='L61')
sub('404.html', r'\s*<p style="[^"]*">404 · Off the map</p>', '', ref='L61')

# ---------------- write ----------------
if problems:
    print('INTENT: %d problem(s), nothing written:' % len(problems))
    for p in problems:
        print('  ' + p)
    sys.exit(1)
for name, s in pages.items():
    (OUT / name).write_text(s, encoding='utf-8')
print('intent: applied to %d pages' % len(pages))
