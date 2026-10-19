import os, sys, re, glob
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1]
SHOTS = sys.argv[2]
os.makedirs(SHOTS, exist_ok=True)

exe = None
for cand in glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome'):
    exe = cand
results = []
fails = []


def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    if not cond:
        fails.append(f'{name} {detail}')


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    # Test-only: this sandbox blocks Google Fonts, so serve the same families from local fontsource files.
    FONT_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts-test.css')).read()
    FONT_DIR = '/tmp/claude-0/-home-claude/16ca1681-18c1-58d3-954a-5698233dc3a8/scratchpad/fonts'
    FONT_FILES = {os.path.basename(f): f for f in glob.glob(FONT_DIR + '/*/package/files/*.woff2')}
    gf_hits = []
    def gf(route):
        u = route.request.url
        if 'fonts.googleapis.com/css2' in u:
            gf_hits.append(u)
            route.fulfill(status=200, content_type='text/css', body=FONT_CSS, headers={'access-control-allow-origin': '*'})
        elif '/testfont/' in u:
            route.fulfill(status=200, path=FONT_FILES[u.rsplit('/', 1)[1]], content_type='font/woff2', headers={'access-control-allow-origin': '*'})
        else:
            route.abort()
    _new_context = browser.new_context
    def new_context(**kw):
        c = _new_context(**kw)
        c.route(re.compile(r'https://fonts\.(googleapis|gstatic)\.com/.*'), gf)
        return c
    browser.new_context = new_context

    # ---------- per page, per viewport: console errors, overflow, screenshots
    for page_name in ['index.html', 'local.html', 'mainframe.html', '404.html']:
        for (w, h) in [(1440, 900), (390, 844)]:
            ctx = browser.new_context(viewport={'width': w, 'height': h})
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.on('pageerror', lambda e: errs.append(str(e)))
            url = BASE + ('nope/missing-page' if page_name == '404.html' else page_name)
            if page_name == '404.html':
                url = BASE + '404.html'
            pg.goto(url, wait_until='networkidle')
            pg.wait_for_timeout(2600)  # let entrance and draw animations finish
            sw = pg.evaluate('document.documentElement.scrollWidth')
            iw = pg.evaluate('window.innerWidth')
            check(f'{page_name}@{w} no console errors', not errs, str(errs))
            check(f'{page_name}@{w} no horizontal scroll ({sw}<={iw})', sw <= iw)
            pg.screenshot(path=f'{SHOTS}/{page_name.replace(".html", "")}-{w}.png', full_page=True)
            ctx.close()

    # ---------- no-JS default state
    ctx = browser.new_context(java_script_enabled=False, viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    pg.goto(BASE + 'local.html')
    check('local noJS: picker message hidden', not pg.is_visible('#pick-msg'))
    check('local noJS: reels tab selected', pg.get_attribute('button[data-tab="reels"]', 'aria-selected') == 'true')
    check('local noJS: 6 receipt rows', pg.locator('#rc-rows > div').count() == 6)
    check('local noJS: first FAQ open only', pg.is_visible('#faq-a-0') and not pg.is_visible('#faq-a-1'))
    check('local noJS: no YOUR MATCH', pg.locator('[data-match]:visible').count() == 0)
    check('local noJS: clock text', "It's afternoon in Santa Rosa." in pg.inner_text('#contact'))
    pg.goto(BASE + 'mainframe.html')
    check('mf noJS: percentage selected', pg.get_attribute('button[data-reading="percent"]', 'aria-pressed') == 'true')
    check('mf noJS: $291.67', pg.inner_text('#mf-interest') == '$291.67')
    check('mf noJS: exhibit B', pg.inner_text('#xb-code') == 'EXHIBIT B')
    check('mf noJS: first dossier open', pg.is_visible('#toc-b-0') and not pg.is_visible('#toc-b-1'))
    pg.goto(BASE + 'index.html')
    check('index noJS: no route pressed', pg.locator('button[aria-pressed="true"]').count() == 0)
    ctx.close()

    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))

    # ---------- index interactions
    pg.goto(BASE + 'index.html')
    table0 = pg.inner_html('#lineup')
    pills0 = pg.inner_html('[role="group"]')
    pg.click('button[data-route="local"]')
    check('index: local pressed', pg.get_attribute('button[data-route="local"]', 'aria-pressed') == 'true')
    st = pg.get_attribute('#lineup tbody tr:first-child td[data-col="local"]', 'style')
    check('index: local column highlighted', 'box-shadow' in st and 'font-weight: 600' in st)
    check('index: main column dimmed', '#8A8F98' in pg.get_attribute('#lineup tbody tr:first-child td[data-col="main"]', 'style'))
    check('index: local head orange', '#A93F17' in pg.get_attribute('th[data-col="local"]', 'style'))
    pg.click('button[data-route="main"]')
    check('index: main pressed, local unpressed', pg.get_attribute('button[data-route="main"]', 'aria-pressed') == 'true' and pg.get_attribute('button[data-route="local"]', 'aria-pressed') == 'false')
    check('index: main column highlighted', 'box-shadow' in pg.get_attribute('#lineup tbody tr:nth-child(3) td[data-col="main"]', 'style'))
    pg.screenshot(path=f'{SHOTS}/index-1440-main-highlight.png', full_page=True)
    pg.click('button[data-route="main"]')
    check('index: toggle off restores default markup', pg.inner_html('#lineup') == table0 and pg.inner_html('[role="group"]') == pills0)

    # ---------- local interactions
    pg.goto(BASE + 'local.html')
    rc0 = pg.inner_html('#proof')
    faq0 = pg.inner_html('#faq')
    expect = {'reels': ('See Engine A', '#engines', 0), 'app': ('See Engine B', '#engines', 1), 'flow': ('See Engine C', '#engines', 2), 'unsure': ('See the Blueprint', '#blueprint', None)}
    names = ['reels', 'app', 'flow']
    for k, (cta, href, idx) in expect.items():
        pg.click(f'button[data-pick="{k}"]')
        check(f'local pick {k}: pressed', pg.get_attribute(f'button[data-pick="{k}"]', 'aria-pressed') == 'true')
        check(f'local pick {k}: only one pressed', pg.locator('button[data-pick][aria-pressed="true"]').count() == 1)
        check(f'local pick {k}: message shown', pg.is_visible('#pick-msg') and len(pg.inner_text('#pick-text')) > 10)
        check(f'local pick {k}: link', pg.get_attribute('#pick-link', 'href') == href and pg.inner_text('#pick-link') == cta + ' →')
        vis = [pg.is_visible(f'[data-match="{n}"]') for n in names]
        check(f'local pick {k}: YOUR MATCH', vis == [i == idx for i in range(3)], str(vis))
        if idx is not None:
            check(f'local pick {k}: card ring', 'border: 3px solid #E8592B' in pg.get_attribute(f'[data-card="{names[idx]}"]', 'style'))
        if k == 'app':
            pg.screenshot(path=f'{SHOTS}/local-1440-pick-app.png', full_page=True)
    for k, rows, title in [('app', 6, 'A cooking-program app, in build'), ('method', 4, 'Checking an AI’s work, in public')]:
        pg.click(f'button[data-tab="{k}"]')
        check(f'local tab {k}: selected', pg.get_attribute(f'button[data-tab="{k}"]', 'aria-selected') == 'true' and pg.locator('button[data-tab][aria-selected="true"]').count() == 1)
        check(f'local tab {k}: rows', pg.locator('#rc-rows > div').count() == rows)
        check(f'local tab {k}: title', pg.inner_text('#rc-title').lower() == title.lower())
        check(f'local tab {k}: link visibility', pg.is_visible('#rc-link') == (k == 'method'))
    check('local tab method: repo link', pg.get_attribute('#rc-link', 'href') == 'https://github.com/stephensjosef-cloud/cobol-behavioral-equivalence')
    pg.click('button[data-tab="reels"]')
    check('local tabs: back to reels restores default markup', pg.inner_html('#proof') == rc0)
    pg.click('button[data-faq="2"]')
    check('local faq: item 2 open, others closed', pg.is_visible('#faq-a-2') and not pg.is_visible('#faq-a-0') and pg.get_attribute('button[data-faq="2"]', 'aria-expanded') == 'true' and pg.get_attribute('button[data-faq="0"]', 'aria-expanded') == 'false')
    pg.click('button[data-faq="2"]')
    check('local faq: toggle closes all', pg.locator('[id^="faq-a-"]:visible').count() == 0)
    pg.click('button[data-faq="0"]')
    check('local faq: reopen first restores default markup', pg.inner_html('#faq') == faq0)
    clock = pg.inner_text('#sr-clock')
    status = pg.inner_text('#sr-status')
    check('local clock: live time', re.match(r'^\d{1,2}:\d{2}\s?[AP]M$', clock) is not None, clock)
    check('local clock: status line', status in ("I'm in a work block, so you'll likely hear back today.", "I'm off the clock. Expect a reply the next weekday afternoon."), status)
    # Working-hours logic: Wed 2 PM Pacific vs Sat 2 PM Pacific
    for iso, want in [('2026-10-14T21:00:00Z', 'work block'), ('2026-10-17T21:00:00Z', 'off the clock'), ('2026-10-14T19:30:00Z', 'off the clock')]:
        c2 = browser.new_context()
        p2 = c2.new_page()
        p2.clock.install(time=iso)
        p2.goto(BASE + 'local.html')
        check(f'local clock at {iso}: {want}', want in p2.inner_text('#sr-status'), p2.inner_text('#sr-status') + ' ' + p2.inner_text('#sr-clock'))
        c2.close()

    # ---------- mainframe interactions
    pg.goto(BASE + 'mainframe.html')
    exa0 = pg.inner_html('figure')
    s2_0 = pg.inner_html('#s2')
    s4_0 = pg.inner_html('#s4')
    pg.click('button[data-reading="fraction"]')
    check('mf fraction: pressed', pg.get_attribute('button[data-reading="fraction"]', 'aria-pressed') == 'true' and pg.get_attribute('button[data-reading="percent"]', 'aria-pressed') == 'false')
    check('mf fraction: values', [pg.inner_text(f'#mf-{k}') for k in ['bytes', 'value', 'rate', 'interest']] == ['00 03 50 0C', '0.03500', '0.0029167', '$2.92'])
    check('mf fraction: color', '#12161F' in pg.get_attribute('#mf-interest', 'style'))
    check('mf fraction: verdict', pg.inner_text('#mf-verdict') == 'What the bank means: 3.5% a year, stored as a fraction.')
    pg.click('button[data-reading="percent"]')
    check('mf percent: restores default markup', pg.inner_html('figure') == exa0)
    for k, rows in [('c', 4), ('d', 4)]:
        pg.click(f'button[data-ex="{k}"]')
        check(f'mf exhibit {k}: selected', pg.get_attribute(f'button[data-ex="{k}"]', 'aria-selected') == 'true' and pg.locator('button[data-ex][aria-selected="true"]').count() == 1)
        check(f'mf exhibit {k}: code + rows', pg.inner_text('#xb-code') == f'EXHIBIT {k.upper()}' and pg.locator('#xb-rows > div').count() == rows)
    pg.click('button[data-ex="b"]')
    check('mf exhibit b: restores default markup', pg.inner_html('#s2') == s2_0)
    pg.click('button[data-toc="4"]')
    check('mf toc: item 4 open only', pg.is_visible('#toc-b-4') and not pg.is_visible('#toc-b-0') and pg.get_attribute('button[data-toc="4"]', 'aria-expanded') == 'true')
    pg.click('button[data-toc="4"]')
    check('mf toc: toggle closes all', pg.locator('[id^="toc-b-"]:visible').count() == 0)
    pg.click('button[data-toc="0"]')
    check('mf toc: reopen first restores default markup', pg.inner_html('#s4') == s4_0)
    check('no page errors during interactions', not errs, str(errs))

    # ---------- links
    import urllib.request
    for page_name in ['index.html', 'local.html', 'mainframe.html', '404.html']:
        pg.goto(BASE + page_name)
        hrefs = pg.eval_on_selector_all('a[href]', 'els => els.map(e => e.getAttribute("href"))')
        ids = set(pg.eval_on_selector_all('[id]', 'els => els.map(e => e.id)'))
        for h in hrefs:
            if h.startswith('#'):
                check(f'{page_name} anchor {h}', h[1:] in ids)
            elif h.startswith(('mailto:', 'http://', 'https://')) or h.startswith('['):
                continue
            else:
                u = urljoin(BASE + page_name, h)
                try:
                    code = urllib.request.urlopen(u).status
                except Exception as e:
                    code = str(e)
                check(f'{page_name} link {h} -> {code}', code == 200)
    # head assets
    for a in ['favicon.svg', 'robots.txt', 'sitemap.xml', 'CNAME']:
        check(f'asset {a}', urllib.request.urlopen(BASE + a).status == 200)
    check('Google Fonts link requested on every page', len(gf_hits) >= 4)
    browser.close()

for n, ok in results:
    if not ok:
        print('FAIL', n)
print(f'{sum(ok for _, ok in results)}/{len(results)} passed')
for f in fails:
    print('  ', f)
