#!/usr/bin/env python3
"""Final pass, Nov 11 2026 (T-11): facts a machine can read.

Runs last, after intent.py, on the built output:  python3 final.py out

It reads the finished pages, so every word it puts in the structured data is
what the page says after the plain and intent passes. Nothing here is typed by
hand that a page states: names, prices, the description and the FAQ are all
read from the page. If a price can't be found, the build fails and says which.

Adds one <script type="application/ld+json"> just before </head> on:
  local.html      ProfessionalService (with its offers) and FAQPage
  mainframe.html  Service "The Mainframe Route" (with one offer per priced step)
index.html keeps its own block as it is.

T-12 (Nov 11 2026), the visit counter: CF_BEACON_TOKEN below. While it is
empty, nothing is added anywhere. When it holds the token from Cloudflare's Web
Analytics snippet, two things happen:
  1. The local.html FAQ answer "What do you do with our data?" gets one more
     sentence, before the structured data is built, so the FAQPage carries it.
  2. Cloudflare's beacon, in the form its docs give, goes just before </body>
     on every .html page in the output, except comp3.html: that page keeps
     pasted bytes in its own address (its share link), so it gets no beacon.
Cloudflare's docs say the beacon sets no cookies and uses no storage
(developers.cloudflare.com/speed/observatory/rum-beacon/, "Data processing";
cloudflare.com/web-analytics/). They don't say whether the part of the address
after # is sent, so start.html clears its own # before the beacon runs.

This is not in enhance.py on purpose: intent.py needs each edit to match an
exact number of times, and a second copy of a page's words inside a script
tag would break that.
"""
import html
import json
import re
import sys
from pathlib import Path

# The site token from Cloudflare's Web Analytics snippet (the part inside
# data-cf-beacon='{"token": "..."}'). Public by design: it sits in every page.
CF_BEACON_TOKEN = ""

OUT = Path(sys.argv[1])
SITE = 'https://dragomansjourney.com/'
NAME = "Dragoman's Journey"
FOUNDER = {'@type': 'Person', 'name': 'Josef Stephens'}
problems = []
pages = {f.name: f.read_text(encoding='utf-8') for f in sorted(OUT.glob('*.html'))}
before = dict(pages)

# The Web Analytics snippet, in the form Cloudflare's docs give it
# (developers.cloudflare.com/web-analytics/faq/, with type="module" as they say).
BEACON = ('<script\n\ttype="module"\n\tsrc="https://static.cloudflareinsights.com/beacon.min.js"\n'
          '\tdata-cf-beacon=\'{"token": "%s"}\'\n></script>\n')
NO_BEACON = ('comp3.html',)  # keeps pasted bytes in its own address on purpose
DATA_Q = 'What do you do with our data?'
COUNTER_LINE = 'This site counts page visits with Cloudflare Web Analytics, which uses no cookies.'


def plain(fragment):
    """Visible words of an HTML fragment: tags out, entities decoded, spaces collapsed."""
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def one(page, pattern, what):
    m = re.findall(pattern, pages[page], flags=re.S)
    if len(m) != 1:
        problems.append('%s: found %d %s, expected 1' % (page, len(m), what))
        return ''
    return m[0]


def meta_description(page):
    return html.unescape(one(page, r'<meta name="description" content="([^"]*)">', 'meta description'))


AMOUNT = re.compile(r'\$([\d,]+(?:\.\d+)?)(/month)?')


def offer(page, name, price_part, line):
    """An Offer from a price line. price_part holds the price ("From $800/month");
    line is the whole price line, and what's left of it once the price part is
    taken out goes in the description, word for word."""
    m = AMOUNT.search(price_part)
    if not m:
        problems.append('%s: no price found for "%s"' % (page, name))
        return None
    amount = float(m.group(1).replace(',', ''))
    amount = int(amount) if amount.is_integer() else amount
    o = {'@type': 'Offer', 'name': name, 'priceCurrency': 'USD'}
    if re.search(r'\bfrom\s*$', price_part[:m.start()], flags=re.I):
        spec = {'@type': 'PriceSpecification', 'minPrice': amount, 'priceCurrency': 'USD'}
        if m.group(2):
            # unitText belongs to UnitPriceSpecification, the PriceSpecification for a price per unit.
            spec['@type'] = 'UnitPriceSpecification'
            spec['unitText'] = 'month'
        o['priceSpecification'] = spec
    else:
        if m.group(2):
            problems.append('%s: "%s" is a monthly price without "from"; no rule for that' % (page, name))
        o['price'] = amount
    rest = line.replace(price_part, '', 1).strip(' ·')
    if rest:
        o['description'] = rest
    return o


def github():
    """The GitHub link index.html's own block uses."""
    block = one('index.html', r'<script type="application/ld\+json">(.*?)</script>', 'ld+json block')
    try:
        links = [u for node in json.loads(block)['@graph'] for u in node.get('sameAs', []) if 'github.com' in u]
    except (ValueError, KeyError, TypeError):
        links = []
    if len(links) != 1:
        problems.append('index.html: found %d GitHub links in its ld+json, expected 1' % len(links))
        return []
    return links


# ---------------- local.html ----------------
def local():
    page = 'local.html'
    s = pages[page]
    offers = []
    bp = one(page, r'<li id="blueprint".*?</li>', 'Blueprint step')
    h3 = plain(one(page, r'<li id="blueprint".*?<h3[^>]*>(.*?)</h3>', 'Blueprint heading')) if bp else ''
    if h3:
        name, _, price = h3.partition(' · ')
        offers.append(offer(page, name.strip(), price, price))
    cards = re.findall(r'<article[^>]* data-card="[^"]+".*?</article>', s, flags=re.S)
    if len(cards) != 3:
        problems.append('%s: found %d offer cards, expected 3' % (page, len(cards)))
    for card in cards:
        name = plain((re.search(r'<h3[^>]*>(.*?)</h3>', card, flags=re.S) or [None, ''])[1])
        line = re.findall(r'<p[^>]*>(.*?)</p>', card, flags=re.S)
        line = line[-1] if line else ''
        strong = re.search(r'<strong>(.*?)</strong>', line, flags=re.S)
        if not name or not strong:
            problems.append('%s: no price found for "%s"' % (page, name or 'a card with no heading'))
            continue
        offers.append(offer(page, name, plain(strong.group(1)), plain(line)))

    qs = re.findall(r'<button[^>]*aria-controls="faq-a-(\d+)"[^>]*data-faq="\1"[^>]*>(.*?)</button>', s, flags=re.S)
    if len(qs) != len(re.findall(r'data-faq="', s)) or not qs:
        problems.append('%s: could not read every data-faq button' % page)
    faq = []
    for i, q in qs:
        a = re.search(r'<p id="faq-a-%s"[^>]*>(.*?)</p>' % i, s, flags=re.S)
        if not a:
            problems.append('%s: no answer faq-a-%s' % (page, i))
            continue
        q = re.match(r'\s*<span>(.*?)</span>', q, flags=re.S)  # the question; the next span is the + icon
        if not q:
            problems.append('%s: no question text on data-faq %s' % (page, i))
            continue
        faq.append({'@type': 'Question', 'name': plain(q.group(1)),
                    'acceptedAnswer': {'@type': 'Answer', 'text': plain(a.group(1))}})

    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'ProfessionalService', 'name': NAME, 'url': SITE + 'local.html',
         'email': 'hello@dragomansjourney.com', 'founder': FOUNDER,
         'address': {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa',
                     'addressRegion': 'CA', 'addressCountry': 'US'},
         'areaServed': 'Sonoma County, California',
         'description': meta_description(page), 'sameAs': github(),
         'makesOffer': [o for o in offers if o]},
        {'@type': 'FAQPage', 'mainEntity': faq},
    ]}


# ---------------- mainframe.html ----------------
def mainframe():
    page = 'mainframe.html'
    steps_ol = one(page, r'id="s3-h".*?(<ol.*?</ol>)', 'steps list')
    offers = []
    for li in re.findall(r'<li.*?</li>', steps_ol, flags=re.S):
        name = plain((re.search(r'<h3[^>]*>(.*?)</h3>', li, flags=re.S) or [None, ''])[1])
        ps = re.findall(r'<p[^>]*>(.*?)</p>', li, flags=re.S)
        line = plain(ps[-1]) if ps else ''
        m = re.search(r'(?:\bfrom\s+)?\$[\d,]+(?:\.\d+)?(?:/month)?', line, flags=re.I)
        if not m:
            continue  # a step that prints no price gets no offer
        offers.append(offer(page, name, m.group(0), line))
    if not offers:
        problems.append('%s: no priced steps found' % page)
    return {'@context': 'https://schema.org', '@type': 'Service', 'name': 'The Mainframe Route',
            'url': SITE + 'mainframe.html',
            'provider': {'@type': 'Organization', 'name': NAME, 'founder': FOUNDER},
            'description': meta_description(page),
            'offers': [o for o in offers if o]}


def add(page, data):
    if 'application/ld+json' in pages[page]:
        problems.append('%s: already has an ld+json block' % page)
        return
    if pages[page].count('</head>') != 1:
        problems.append('%s: expected one </head>' % page)
        return
    body = json.dumps(data, indent=1, ensure_ascii=False).replace('</', '<\\/')
    pages[page] = pages[page].replace('</head>', '<script type="application/ld+json">\n%s\n</script>\n</head>' % body)


def counter_line():
    """T-12 step 4: one sentence at the end of the local.html data answer."""
    page = 'local.html'
    s = pages[page]
    i = one(page, r'aria-controls="faq-a-(\d+)"[^>]*><span>' + re.escape(DATA_Q) + '</span>', 'FAQ "%s"' % DATA_Q)
    if not i:
        return
    pat = r'(<p id="faq-a-%s"[^>]*>)(.*?)(</p>)' % i
    m = re.findall(pat, s, flags=re.S)
    if len(m) != 1:
        problems.append('%s: found %d answers faq-a-%s, expected 1' % (page, len(m), i))
        return
    if COUNTER_LINE in s:
        problems.append('%s: already says "%s"' % (page, COUNTER_LINE))
        return
    pages[page] = re.sub(pat, lambda m: m.group(1) + m.group(2).rstrip() + ' ' + COUNTER_LINE + m.group(3), s, flags=re.S)


def beacon(token):
    """T-12 step 2: the visit counter, just before </body>, on every page but comp3.html."""
    if not re.fullmatch(r'[A-Za-z0-9]+', token):
        problems.append('CF_BEACON_TOKEN must be the token only (letters and digits), not the whole snippet')
        return
    for name in pages:
        if name in NO_BEACON:
            continue
        if 'cloudflareinsights.com' in pages[name]:
            problems.append('%s: already has a beacon' % name)
        elif pages[name].count('</body>') != 1:
            problems.append('%s: expected one </body>' % name)
        else:
            pages[name] = pages[name].replace('</body>', BEACON % token + '</body>')


if CF_BEACON_TOKEN:
    counter_line()
add('local.html', local())
add('mainframe.html', mainframe())
if CF_BEACON_TOKEN:
    beacon(CF_BEACON_TOKEN)

# ---------------- write ----------------
if problems:
    print('FINAL: %d problem(s), nothing written:' % len(problems))
    for p in problems:
        print('  ' + p)
    sys.exit(1)
for name in pages:
    if pages[name] != before[name]:
        (OUT / name).write_text(pages[name], encoding='utf-8')
print('final: structured data on local.html and mainframe.html')
if CF_BEACON_TOKEN:
    print('final: visit counter on %d pages (not %s)' % (len(pages) - len(NO_BEACON), ', '.join(NO_BEACON)))
else:
    print('final: no visit counter (CF_BEACON_TOKEN is empty)')
