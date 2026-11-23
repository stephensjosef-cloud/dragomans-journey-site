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
index.html keeps its own block (WebSite and Person); T-39 adds the business to its @graph.

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

# T-42: tools/board.py imports this file for nobreak_page() and the beacon; the run itself
# (reading out/, the edits, writing) happens only as a script.
OUT = Path(sys.argv[1]) if __name__ == '__main__' else None
SITE = 'https://dragomansjourney.com/'
NAME = "Dragoman's Journey"
FOUNDER = {'@type': 'Person', 'name': 'Josef Stephens'}
EMAIL = 'hello@dragomansjourney.com'
PHONE = '+1-707-394-8719'   # the business line, Google Voice (T-39, Nov 21, 2026)
ADDRESS = {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa', 'addressRegion': 'CA', 'addressCountry': 'US'}
AREA = 'Sonoma County, California'   # a service-area business: no street address, no opening hours


def business(url):
    """The facts about the business that local.html and index.html both state."""
    return {'@type': 'ProfessionalService', 'name': NAME, 'url': url, 'email': EMAIL, 'telephone': PHONE,
            'founder': FOUNDER, 'address': ADDRESS, 'areaServed': AREA}


problems = []
pages = {f.name: f.read_text(encoding='utf-8') for f in sorted(OUT.glob('*.html'))} if OUT else {}
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
        dict(business(SITE + 'local.html'),
             description=meta_description(page), sameAs=github(),
             makesOffer=[o for o in offers if o]),
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


def index_business():
    """T-39: index.html keeps its own block (build.py writes it); this adds one node to its
    @graph, the business, built from the same facts local.html states. The block is written
    back the way build.py wrote it, so the WebSite and Person nodes come out as they were."""
    page = 'index.html'
    pat = r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)'
    if len(re.findall(pat, pages[page], flags=re.S)) != 1:
        problems.append('%s: expected one ld+json block' % page)
        return
    m = re.search(pat, pages[page], flags=re.S)
    try:
        data = json.loads(m.group(2))
        graph = data['@graph']
    except (ValueError, KeyError, TypeError):
        problems.append('%s: could not read the @graph in its ld+json' % page)
        return
    if [n.get('@type') for n in graph] != ['WebSite', 'Person']:
        problems.append('%s: expected a WebSite and a Person in its @graph, found %s' % (page, [n.get('@type') for n in graph]))
        return
    graph.append(business(SITE))
    body = json.dumps(data, indent=1, ensure_ascii=False).replace('</', '<\\/')
    pages[page] = pages[page][:m.start(2)] + body + pages[page][m.end(2):]


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


if __name__ == '__main__':
    if CF_BEACON_TOKEN:
        counter_line()
    add('local.html', local())
    add('mainframe.html', mainframe())
    index_business()
    if CF_BEACON_TOKEN:
        beacon(CF_BEACON_TOKEN)


# ---------------- line breaking (T-21, Nov 16, 2026) ----------------
# The last thing done to every page, after the structured data above (which reads the
# FAQ's <span> markup) and after every exact-match pass (plain, intent, voice2), so no
# exact match can miss. Visible text only: nothing inside script, style, code, pre,
# title, textarea, svg or an element that is already no-wrap, and never an attribute.
# The rules (a hyphen pair in a no-wrap span; " · " held to both neighbours) live in
# tools/chrome.py as nobreak(), which the tool scripts use too. No word changes: the
# visible text before and after must match, with a no-break space read as a space.
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
import chrome  # noqa: E402

RAW = ('script', 'style', 'textarea', 'title')                 # contents are not markup
SKIP = RAW + ('code', 'pre', 'svg', 'head', 'option', 'select', 'template', 'noscript')
VOID = ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr')
TAG = re.compile(r"""<!--.*?-->|<![^>]*>|</?[A-Za-z][^\s/>]*(?:[^"'>]|"[^"]*"|'[^']*')*>""", re.S)
NOWRAP_STYLE = re.compile(r"""\bstyle\s*=\s*(["'])[^"']*white-space:\s*nowrap""", re.I)


def visible(page):
    """The page's text as a reader gets it: tags out, entities decoded, spaces collapsed."""
    t = re.sub(r'<(script|style|title|textarea)\b.*?</\1\s*>', ' ', page, flags=re.S | re.I)
    return re.sub(r'[\s ]+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip()


FLEX_STYLE = re.compile(r"""\bstyle\s*=\s*(["'])[^"']*display:\s*(?:inline-)?(?:flex|grid)""", re.I)


def nobreak_text(text, parent):
    """One run of text. In a flex or grid box (the call buttons) each piece of text
    becomes its own flex item and the spaces around a new span vanish, so there the
    whole run goes in one plain <span>, as T-20 did for the call link."""
    done = chrome.nobreak(text)
    if done != text and '<span' in done and parent and FLEX_STYLE.search(parent):
        core = done.strip()
        lead, trail = done[:len(done) - len(done.lstrip())], done[len(done.rstrip()):]
        done = lead + '<span>' + core + '</span>' + trail
    return done


def nobreak_page(page):
    out, pos, skip = [], 0, None        # skip: [tag name, nesting depth] while inside
    prev = ''                           # the tag just before this run of text
    for m in TAG.finditer(page):
        if m.start() < pos:
            continue
        text = page[pos:m.start()]
        out.append(text if skip else nobreak_text(text, prev if not prev.startswith('</') else ''))
        tag = m.group(0)
        prev = tag
        out.append(tag)
        pos = m.end()
        tm = re.match(r'<(/?)([A-Za-z][^\s/>]*)', tag)
        if not tm:
            continue
        closing, name = tm.group(1) == '/', tm.group(2).lower()
        if name in RAW and not closing:          # copy a raw element whole, up to its end tag
            end = re.compile(r'</%s\s*>' % name, re.I).search(page, pos)
            stop = end.end() if end else len(page)
            out.append(page[pos:stop])
            pos = stop
            continue
        if name in VOID or tag.endswith('/>'):
            continue
        if skip:
            if name == skip[0]:
                skip[1] += -1 if closing else 1
                if skip[1] == 0:
                    skip = None
        elif not closing and (name in SKIP or NOWRAP_STYLE.search(tag)):
            skip = [name, 1]
    out.append(page[pos:] if skip else chrome.nobreak(page[pos:]))
    return ''.join(out)



def nobreak_checked(name, page):
    """One page through the line-breaking pass, or (page, the problem) if it fails a check."""
    done = nobreak_page(page)
    if visible(done) != visible(page):
        return page, '%s: the line-breaking pass changed the visible text' % name
    if nobreak_page(done) != done:
        return page, '%s: the line-breaking pass is not stable on a second run' % name
    return done, None


if __name__ == '__main__':
    for name in pages:
        pages[name], problem = nobreak_checked(name, pages[name])
        if problem:
            problems.append(problem)

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
