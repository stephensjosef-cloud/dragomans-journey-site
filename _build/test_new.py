"""Checks for the Oct 18 additions: decoder, sources, timeline, intake, drop-in."""
import glob, os, sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1]
SHOTS = sys.argv[2]
os.makedirs(SHOTS, exist_ok=True)
exe = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0]
FONT_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts-test.css')).read()
FONT_DIR = '/tmp/claude-0/-home-claude/16ca1681-18c1-58d3-954a-5698233dc3a8/scratchpad/fonts'
FONT_FILES = {os.path.basename(f): f for f in glob.glob(FONT_DIR + '/*/package/files/*.woff2')}
ok, bad = [], []


def check(name, cond, detail=''):
    (ok if cond else bad).append(name + ('' if cond else f'  {detail}'))


def route_fonts(page):
    def gf(route):
        u = route.request.url
        if 'fonts.googleapis.com' in u:
            return route.fulfill(status=200, content_type='text/css', body=FONT_CSS)
        name = os.path.basename(u.split('?')[0])
        if name in FONT_FILES:
            return route.fulfill(status=200, content_type='font/woff2', body=open(FONT_FILES[name], 'rb').read())
        return route.abort()
    page.route('**/fonts.googleapis.com/**', gf)
    page.route('**/fonts.gstatic.com/**', gf)
    page.route('**/__fonts/**', gf)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    errors = []

    def newpage(w, h=900):
        pg = b.new_page(viewport={'width': w, 'height': h})
        route_fonts(pg)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        return pg

    # ---------------- decoder
    pg = newpage(1440)
    pg.goto(BASE + 'comp3.html'); pg.wait_for_timeout(300)
    out = lambda: pg.inner_text('#out')
    check('decoder default value 3.50000', '3.50000' in out(), out()[:200])
    check('decoder default fraction reading $291.67', '$291.67' in out())
    check('decoder default percentage reading $2.92', '$2.92' in out())
    pg.click('text=Exhibit A, as the bank stored it'); pg.wait_for_timeout(100)
    check('bank-stored value 0.03500', '0.03500' in out(), out()[:200])
    check('bank-stored fraction reading $2.92', '$2.92' in out())
    pg.click('text=A negative balance'); pg.wait_for_timeout(100)
    check('negative balance -12345.67', '-12345.67' in out(), out()[:200])
    check('no rate block for a balance', 'ANNUAL RATE' not in out().upper())
    pg.click('text=A damaged field'); pg.wait_for_timeout(100)
    check('damaged field warns S0C7', 'S0C7' in out(), out()[:300])
    pg.fill('#in', '0350000C'); pg.fill('#pic', 'PIC S9(2)V9(5) COMP-3.'); pg.wait_for_timeout(100)
    check('full PIC clause parsed', '3.50000' in out(), out()[:200])
    pg.fill('#pic', '9(5)'); pg.fill('#in', '12345F'); pg.wait_for_timeout(100)
    check('unsigned 9(5) value 12345 clean', '12345' in out() and 'Clean field' in out(), out()[:300])
    pg.fill('#in', '01 23 4C'); pg.fill('#pic', 'S9(6)'); pg.wait_for_timeout(100)
    check('length mismatch flagged', 'packs into 3 bytes' in out() or 'You pasted' in out(), out()[:300])
    pg.click('#mode-enc'); pg.wait_for_timeout(100)
    pg.fill('#pic', 'S9(7)V99'); pg.fill('#in', '-12345.67'); pg.wait_for_timeout(100)
    check('encode -12345.67 -> 00 12 34 56 7D', '00 12 34 56 7D' in out(), out()[:200])
    pg.fill('#pic', 'S9(2)V9(5)'); pg.fill('#in', '0.035'); pg.wait_for_timeout(100)
    check('encode 0.035 -> 00 03 50 0C', '00 03 50 0C' in out(), out()[:200])
    pg.fill('#in', '123.5'); pg.wait_for_timeout(100)
    check('encode overflow warns', 'Too many digits' in out(), out()[:200])
    # shared link
    pg2 = newpage(1440)
    pg2.goto(BASE + 'comp3.html#m=dec&v=00%2003%2050%200C&p=S9(2)V9(5)'); pg2.wait_for_timeout(300)
    check('shared link restores field', '0.03500' in pg2.inner_text('#out'))
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'comp3.html'); q.wait_for_timeout(400)
        check(f'decoder no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/comp3-{w}.png', full_page=True)

    # ---------------- local page
    pg = newpage(1440)
    pg.goto(BASE + 'local.html'); pg.wait_for_timeout(500)
    btns = pg.locator('#rc-rows .src-btn')
    check('reels receipt has 5 source buttons', btns.count() == 5, str(btns.count()))
    btns.nth(0).click(); pg.wait_for_timeout(100)
    check('first source note opens', pg.locator('#src-reels-0').is_visible())
    check('reels foot text', 'stay private' in pg.inner_text('#rc-src-foot'))
    pg.click('button[data-tab="app"]'); pg.wait_for_timeout(150)
    check('app receipt decorated after tab switch', pg.locator('#rc-rows .src-btn').count() == 6, str(pg.locator('#rc-rows .src-btn').count()))
    check('app foot text', 'share my screen' in pg.inner_text('#rc-src-foot'))
    pg.click('button[data-tab="method"]'); pg.wait_for_timeout(150)
    check('method receipt has 4 source buttons', pg.locator('#rc-rows .src-btn').count() == 4)
    check('method link visible', pg.locator('#rc-link').is_visible())
    pg.click('button[data-tab="reels"]'); pg.wait_for_timeout(150)
    check('back to reels, 5 buttons', pg.locator('#rc-rows .src-btn').count() == 5)


    check('intake hidden before pick', not pg.locator('#intake').is_visible())
    pg.click('button[data-pick="reels"]'); pg.wait_for_timeout(100)
    check('intake shown after pick', pg.locator('#intake').is_visible())
    check('send disabled until answered', pg.locator('#iq-send').is_disabled())
    pg.click('button.iq[data-q="q1"]:has-text("A nonprofit")')
    pg.click('button.iq[data-q="q2"]:has-text("I do")')
    check('send still disabled with 2 of 3', pg.locator('#iq-send').is_disabled())
    pg.click('button.iq[data-q="q3"]:has-text("This month")')
    check('send enabled with 3 of 3', not pg.locator('#iq-send').is_disabled())
    pg2 = newpage(1440)
    pg2.goto(BASE + 'local.html'); pg2.wait_for_timeout(400)
    pg2.click('button[data-pick="app"]')
    for q, txt in (('q1', 'A small business'), ('q2', 'A board or committee'), ('q3', 'Just looking for now')):
        pg2.click(f'button.iq[data-q="{q}"]:has-text("{txt}")')
    pg2.fill('#iq-name', 'Test Kitchen')
    pg2.click('#iq-send'); pg2.wait_for_timeout(600)
    # T-12: start.html reads its # and then clears it, so the typed business name isn't left in the address.
    check('quiz hands off to start page, # cleared after load', pg2.url.endswith('/start.html'), pg2.url)
    check('start page preselects pile', pg2.locator('.chips[data-key="pile"] .chip[aria-pressed="true"]').inner_text() == 'Lessons, recipes or a curriculum')
    check('start page preselects run/yes/when', pg2.locator('.chip[aria-pressed="true"]').count() == 4, str(pg2.locator('.chip[aria-pressed="true"]').count()))
    check('start page carries org name', pg2.input_value('#org') == 'Test Kitchen')

    check('drop-in section present', pg.locator('#dropin').count() == 1)
    check('no bracket placeholders visible', '[' not in pg.inner_text('body').replace('[n]', '').replace('[MONTH]', ''), '')
    for w in (390, 768, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(500)
        q.click('button[data-pick="flow"]'); q.wait_for_timeout(100)
        check(f'local no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.locator('#proof').screenshot(path=f'{SHOTS}/proof-{w}.png')
        q.locator('section[aria-labelledby="start"]').screenshot(path=f'{SHOTS}/start-{w}.png')
        q.locator('#dropin').screenshot(path=f'{SHOTS}/dropin-{w}.png')
        q.locator('#josef').screenshot(path=f'{SHOTS}/josef-{w}.png')

    # ---------------- start, briefing, drop-in (endpoint mocked)
    import json as _json
    posts = []
    def mock_ok(route):
        if route.request.method == 'POST':
            posts.append(_json.loads(route.request.post_data or '{}'))
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
    def mock_fail(route):
        return route.fulfill(status=502, content_type='application/json', body='{"ok":false}', headers={'Access-Control-Allow-Origin': '*'})

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'local.html'); pg.wait_for_timeout(300)
    check('all Blueprint buttons go to start.html', pg.locator('a[href="start.html"]').count() == 3, str(pg.locator('a[href="start.html"]').count()))
    check('no gmail anywhere on local', 'stephens.josef@gmail.com' not in pg.content())
    pg.fill('#dl-email', 'list@example.com'); pg.wait_for_timeout(2700); pg.click('#dl-send'); pg.wait_for_timeout(400)
    check('drop-in posts form=dropin', posts and posts[-1].get('form') == 'dropin' and posts[-1]['fields']['email'] == 'list@example.com', str(posts[-1:]))
    check('drop-in confirms', "on the list" in pg.inner_text('#dl-msg'))

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'start.html'); pg.wait_for_timeout(300)
    check('start success panel hidden on load', not pg.locator('#bp-done').is_visible())
    pg.click('#bp-send'); pg.wait_for_timeout(200)
    check('start validates empty form', pg.locator('#bp-err').is_visible() and 'step 1' in pg.inner_text('#bp-err'))
    pg.click('.chips[data-key="pile"] .chip >> nth=0')
    pg.click('.chips[data-key="days"] .chip >> nth=1'); pg.click('.chips[data-key="days"] .chip >> nth=3')
    pg.fill('#name', 'Pat Test'); pg.fill('#email', 'pat@example.com'); pg.fill('#never', 'We film and never post.')
    n0 = len(posts)
    pg.click('#bp-send'); pg.wait_for_timeout(500)
    check('start posts form=blueprint', len(posts) == n0 + 1 and posts[-1]['form'] == 'blueprint', str(posts[-1:]))
    check('start sends multi-select days', posts[-1]['fields'].get('days') == 'Tuesday, Thursday', str(posts[-1]['fields']))
    check('start shows success', pg.locator('#bp-done').is_visible() and not pg.locator('#bp').is_visible())

    pg = newpage(390); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_fail)
    pg.goto(BASE + 'start.html'); pg.wait_for_timeout(300)
    pg.click('.chips[data-key="pile"] .chip >> nth=2'); pg.fill('#name', 'Pat'); pg.fill('#email', 'pat@example.com')
    pg.click('#bp-send'); pg.wait_for_timeout(500)
    check('start failure keeps form and offers email', pg.locator('#bp').is_visible() and pg.locator('#bp-err a[href^="mailto:hello@dragomansjourney.com"]').count() == 1)
    check('start no overflow at 390', pg.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
    pg.screenshot(path=f'{SHOTS}/start-390.png', full_page=True)
    q = newpage(1440); q.goto(BASE + 'start.html'); q.wait_for_timeout(400); q.screenshot(path=f'{SHOTS}/start-1440.png', full_page=True)

    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'briefing.html#ask=survey'); pg.wait_for_timeout(300)
    check('briefing success panel hidden on load', not pg.locator('#br-done').is_visible())
    check('briefing preselects survey', pg.locator('.chips[data-key="ask"] .chip[aria-pressed="true"]').inner_text() == 'A quote for the Survey')
    pg.fill('#name', 'Dana Test'); pg.fill('#email', 'dana@bank.example'); pg.fill('#org', 'Example Credit Union')
    pg.click('.chips[data-key="stage"] .chip >> nth=2')
    n0 = len(posts)
    pg.click('#br-send'); pg.wait_for_timeout(500)
    check('briefing posts form=briefing', len(posts) == n0 + 1 and posts[-1]['form'] == 'briefing' and posts[-1]['fields'].get('ask') == 'A quote for the Survey', str(posts[-1:]))
    check('briefing shows success', pg.locator('#br-done').is_visible())
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'briefing.html'); q.wait_for_timeout(400)
        check(f'briefing no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/briefing-{w}.png', full_page=True)

    # ---------------- work, case study, free call
    pg = newpage(1440)
    pg.goto(BASE + 'work.html'); pg.wait_for_timeout(300)
    check('work has 10 cards (T-04 adds the Website checkup)', pg.locator('#cards .card').count() == 10)
    pg.click('.filt[data-f="banking"]'); pg.wait_for_timeout(100)
    check('banking filter shows 2', pg.locator('#cards .card:visible').count() == 2, str(pg.locator('#cards .card:visible').count()))
    pg.click('.filt[data-f="nonprofit"]'); pg.wait_for_timeout(100)
    check('nonprofit filter shows 3 (two jobs + the recipe scaler)', pg.locator('#cards .card:visible').count() == 3)
    pg.click('.filt[data-f="free"]'); pg.wait_for_timeout(100)
    check('free tools filter shows 6', pg.locator('#cards .card:visible').count() == 6)
    q = newpage(1440); q.goto(BASE + 'work.html#free'); q.wait_for_timeout(300)
    check('work.html#free opens on free tools', q.locator('#cards .card:visible').count() == 6)
    check('no CLIENT_ token left on work', 'CLIENT_' not in pg.content())
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'work.html'); q.wait_for_timeout(400)
        check(f'work no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/work-{w}.png', full_page=True)
        q = newpage(w); q.goto(BASE + 'case-reels.html'); q.wait_for_timeout(400)
        check(f'case no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'case client filled at {w}', 'CLIENT_' not in q.content() and "children's nonprofit" in q.inner_text('main'))
        q.screenshot(path=f'{SHOTS}/case-{w}.png', full_page=True)

    calls = []
    def mock_old_worker(route):
        body = _json.loads(route.request.post_data or '{}'); calls.append(body)
        if body.get('form') == 'call':
            return route.fulfill(status=400, content_type='application/json', body='{"ok":false,"error":"form"}', headers={'Access-Control-Allow-Origin': '*'})
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
    pg = newpage(1440); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_old_worker)
    pg.goto(BASE + 'call.html'); pg.wait_for_timeout(300)
    check('call success hidden on load', not pg.locator('#cl-done').is_visible())
    pg.click('.chips[data-key="topic"] .chip >> nth=0'); pg.click('.chips[data-key="days"] .chip >> nth=5')
    pg.fill('#name', 'Sam Test'); pg.fill('#email', 'sam@example.com'); pg.fill('#note', 'Hi')
    pg.wait_for_timeout(2600); pg.click('#cl-send'); pg.wait_for_timeout(700)
    check('call tries call form first', calls and calls[0]['form'] == 'call', str(calls[:1]))
    check('call falls back to labeled blueprint', len(calls) == 2 and calls[1]['form'] == 'blueprint' and 'CALL REQUEST' in calls[1]['fields'].get('heard', ''), str(calls))
    check('call shows success', pg.locator('#cl-done').is_visible())
    calls.clear()
    pg = newpage(390); pg.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok)
    pg.goto(BASE + 'call.html'); pg.wait_for_timeout(300)
    pg.fill('#name', 'Sam'); pg.fill('#email', 'sam@example.com'); pg.click('#cl-send'); pg.wait_for_timeout(500)
    check('call posts natively when worker knows it', posts and posts[-1]['form'] == 'call', str(posts[-1:]))
    check('call no overflow at 390', pg.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
    pg.screenshot(path=f'{SHOTS}/call-390.png', full_page=True)

    pg = newpage(1440); pg.goto(BASE + 'index.html'); pg.wait_for_timeout(300)
    check('front door links work + call', pg.locator('a[href="work.html"]').count() >= 1 and pg.locator('a[href="call.html"]').count() >= 1)
    pg = newpage(1440); pg.goto(BASE + 'local.html'); pg.wait_for_timeout(300)
    check('local links work + call', pg.locator('a[href="work.html"]').count() >= 2 and pg.locator('#contact a[href="call.html"]').count() == 1)
    check('local results link, no slogan (intent L17)', pg.locator('#proof a[href="work.html"]').count() == 1 and "If I can't show it" not in pg.inner_text('#proof'))

    # ---------------- mainframe
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); q.wait_for_timeout(500)
        check(f'mainframe no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'mainframe decoder links at {w}', q.locator('a[href="comp3.html"]').count() == 2)
        check(f'mainframe no placeholders at {w}', '[' not in q.inner_text('#s7'))
        q.locator('#s7').screenshot(path=f'{SHOTS}/mf-s7-{w}.png')

    # ---------------- free tools (Nov 8, 2026)
    for w in (390, 1440):
        for t in ('shotlist', 'captions', 'receipt', 'scaler', 'checkup'):
            q = newpage(w); q.goto(BASE + t + '.html'); q.wait_for_timeout(500)
            check(f'{t} no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.screenshot(path=f'{SHOTS}/{t}-{w}.png', full_page=True)
    q = newpage(1440); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    check('shot list has 10 clips', q.locator('#edit .clip').count() == 10)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 30', abs(secs - 30) < 0.01, str(secs))
    q.click('#f-details'); q.click('#f-cut')   # T-18: "How long?" and the edit sit under two folds now
    q.click('.chip[data-v="15"]'); q.wait_for_timeout(100)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 15', abs(secs - 15) < 0.01, str(secs))
    check('shoot order covers all 10 clips', q.locator('#shoot li').count() == 10)
    q = newpage(1440); q.goto(BASE + 'captions.html'); q.wait_for_timeout(400)
    check('captions split into screens', q.locator('#cards .cardline').count() >= 2)
    q.fill('#cap', 'New fall sweaters just landed.'); q.wait_for_timeout(300)
    check('short caption is one screen', q.locator('#cards .cardline').count() == 1)
    q = newpage(1440); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    check('receipt starts with 3 lines', q.locator('#rows .row2').count() == 3)   # T-18: the lines sit on the receipt
    check('receipt default total $9,750', '$9,750' in q.inner_text('#paper'), q.inner_text('#paper')[:300])
    q.click('[data-p="11"]'); q.wait_for_timeout(100)
    check('keep-human chore adds nothing to come back', '$6,225' in q.inner_text('#paper'))
    href = q.get_attribute('#bring', 'href')
    check('receipt hands off to start with never=', href.startswith('start.html#pile=') and '&never=' in href, href[:80])
    q.goto(BASE + href); q.wait_for_timeout(300)
    check('start form takes the receipt', 'busywork receipt' in q.input_value('#never'))
    check('start clears the receipt text from the address after load', q.url.endswith('/start.html') and '#' not in q.url, q.url[:120])
    check('start keeps the receipt pick after clearing the address',
          q.locator('.chips[data-key="pile"] .chip[aria-pressed="true"]').count() == 1)
    q = newpage(1440); q.goto(BASE + 'scaler.html'); q.wait_for_timeout(300)
    out = q.inner_text('#out')
    check('scaler default x3', q.inner_text('#fac').strip() == '\u00d73', q.inner_text('#fac'))
    check('scaler 1/2 cup milk x3 = 1 1/2 cups', '1 1/2 cups' in out, out[:300])
    check('scaler 1 1/2 tbsp x3 = 4 1/2 tbsp', '4 1/2 tbsp' in out, out[:300])
    q.fill('#kids', '40'); q.wait_for_timeout(100)
    check('scaler warns about batches past x3', 'batches' in q.inner_text('#warn'))

    # ---------------- share cards (T-01, Nov 9, 2026)
    import re as _re, struct as _struct
    from urllib.request import urlopen
    SHARED = ('index', 'local', 'mainframe', 'work', 'comp3', 'shotlist', 'captions', 'receipt',
              'scaler', 'start', 'call', 'case-reels', 'briefing', 'studio', 'checkup')
    # Plus a page per open Studio product with a join list (T-09).
    SHARED += tuple('studio-' + x['id'] for x in _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'studio.json'), encoding='utf-8'))['products']
                    if x.get('gate') is None and x.get('list'))
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        imgs = _re.findall(r'<meta property="og:image" content="([^"]*)">', src)
        check(f'{name} has exactly one og:image', len(imgs) == 1, str(imgs))
        if len(imgs) != 1:
            continue
        check(f'{name} og:image is its own absolute card', imgs[0] == f'https://dragomansjourney.com/og/{name}.png', imgs[0])
        check(f'{name} card size tags and large twitter card',
              '<meta property="og:image:width" content="1200">' in src and '<meta property="og:image:height" content="630">' in src
              and src.count('<meta name="twitter:card" content="summary_large_image">') == 1)
        try:
            png = urlopen(BASE + 'og/' + imgs[0].rsplit('/', 1)[1]).read()
            size = _struct.unpack('>II', png[16:24]) if png[:8] == b'\x89PNG\r\n\x1a\n' else None
        except Exception as e:
            size = str(e)
        check(f'{name} card file exists in out/og at 1200x630', size == (1200, 630), str(size))
    check('404 page carries no share card', 'og:image' not in urlopen(BASE + '404.html').read().decode('utf-8'))

    # ---------------- free tools, findable (T-02, Nov 10, 2026)
    TOOLS = {'shotlist.html': 'Reel shot list', 'captions.html': 'Caption fitter',
             'receipt.html': 'Busywork receipt', 'scaler.html': 'Recipe scaler', 'checkup.html': 'Website checkup'}
    # T-16: every header except the three Mainframe pages, which carry neither Studio nor Free tools.
    MAINFRAME_PAGES = ('mainframe', 'briefing', 'comp3')
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        # The header nav: <nav> where the page has one, else its <header>, else the home page's letterhead bar.
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="work\.html#free"[^>]*>([^<]*)</a>', top)
        if name in MAINFRAME_PAGES:
            check(f'{name} header has no Free tools link (T-16)', bool(top) and links == [] and 'Free tools' not in top, str(links))
            continue
        check(f'{name} nav links Free tools to work.html#free', links == ['Free tools'], str(links))
        if 'Free 15-min call' in top:
            check(f'{name} Free tools sits before the free call', -1 < top.find('work.html#free') < top.index('Free 15-min call'))
    q = newpage(1440); q.goto(BASE + 'work.html#free'); q.wait_for_timeout(300)
    check('work.html#free opens on the free tools', q.get_attribute('.filt[data-f="free"]', 'aria-pressed') == 'true'
          and q.locator('#cards .card:visible').count() == q.locator('#cards .card[data-k~="free"]').count())
    src = urlopen(BASE + 'local.html').read().decode('utf-8')
    sec = _re.search(r'<section id="tools".*?</section>', src, _re.S)
    sec = sec.group(0) if sec else ''
    check('local free tools section sits right before contact', bool(sec) and bool(_re.search(_re.escape(sec) + r'\s*<section id="contact"', src)))
    check('local free tools heading', '>Free tools for your pile</h2>' in sec)
    check('local free tools section links the 5 tools', sorted(_re.findall(r'href="([a-z]+\.html)"', sec)) == sorted(TOOLS), sec[:200])
    work = urlopen(BASE + 'work.html').read().decode('utf-8')
    for href, title in TOOLS.items():
        para = _re.search(r'<h2>' + title + r'</h2>\s*<p>([^<]*)</p>\s*<a class="go" href="' + href, work)
        check(f'local card for {href} matches the work page', bool(para) and f'>{title}</h3>' in sec and f'>{para.group(1)}</p>' in sec)
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(300)
        xs = q.eval_on_selector_all('#tools article', 'e => e.map(a => Math.round(a.getBoundingClientRect().left))')
        check(f'local free tools: {"one column" if w == 390 else "one row of five"} at {w}',
              len(xs) == 5 and (len(set(xs)) == 1 if w == 390 else len(set(xs)) == 5), str(xs))
    for href in TOOLS:
        q = newpage(1440); q.goto(BASE + href); q.wait_for_timeout(300)
        line = q.locator('main > p', has_text='More free tools:')
        got = line.locator('a').evaluate_all('e => e.map(a => [a.getAttribute("href"), a.textContent])') if line.count() == 1 else []
        check(f'{href} links the other tools by name', sorted(got) == sorted([k, v] for k, v in TOOLS.items() if k != href), str(got))
        if line.count() == 1:
            check(f'{href} more-tools line sits above the dark panel',
                  line.bounding_box()['y'] < q.locator('#more-h').bounding_box()['y'])
        # T-16 N14: the dark panel keeps its own button and no longer has "More free tools".
        panel = q.locator('section[aria-labelledby="more-h"]')
        check(f'{href} dark panel: one button, its own, no "More free tools" (T-16)', panel.locator('a').count() == 1
              and panel.locator('a').get_attribute('href') == ('start.html' if href == 'receipt.html' else 'call.html')
              and 'More free tools' not in panel.inner_text(),
              str(panel.locator('a').all_inner_texts()))
        # T-16 N13: the line over the title is just "Free tool".
        check(f'{href} kicker reads "Free tool" (T-16)', q.locator('header .kick').count() == 1
              and q.locator('header .kick').text_content().strip() == 'Free tool', q.locator('header .kick').text_content())
    for name in SHARED:
        q = newpage(390); q.goto(BASE + name + '.html'); q.wait_for_timeout(300)
        sw = q.evaluate('document.documentElement.scrollWidth')
        check(f'{name} has no sideways scroll at 390', sw <= 390, str(sw))
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(150)
            q.screenshot(path=f'{SHOTS}/t02-{name}-{w}.png', full_page=True)

    # ---------------- facts a machine can read (T-11, Nov 11, 2026)
    import json as _json, html as _html

    def ld_blocks(src):
        return _re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, _re.S)

    def page_text(src):
        # The page's words with the tags stripped: scripts and styles out first, so the block can't vouch for itself.
        src = _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S)
        return _re.sub(r'\s+', ' ', _html.unescape(_re.sub(r'<[^>]+>', ' ', src)))

    def walk(node):
        yield node
        for v in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()):
            yield from walk(v)

    def dollars(n):
        return '$' + f'{n:,}'

    LD = {}
    for name in ('local', 'mainframe'):
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        blocks = ld_blocks(src)
        check(f'{name} has exactly one ld+json block', len(blocks) == 1, str(len(blocks)))
        check(f'{name} ld+json sits just before </head>', _re.search(r'</script>\s*</head>', src) is not None
              and src.index('application/ld+json') < src.index('</head>'))
        try:
            data = _json.loads(blocks[0]) if blocks else None
        except ValueError as e:
            data = None
            check(f'{name} ld+json parses as JSON', False, str(e))
        else:
            check(f'{name} ld+json parses as JSON', data is not None)
        LD[name] = data
        if data is None:
            continue
        text = page_text(src)
        nodes = list(walk(data))
        prices = [n.get('price', n.get('minPrice')) for n in nodes if isinstance(n, dict) and n.get('@type') in ('Offer', 'PriceSpecification', 'UnitPriceSpecification')]
        prices = [p for p in prices if p is not None]
        check(f'{name} ld+json carries prices', len(prices) >= 3, str(prices))
        for pr in prices:
            check(f'{name} price {dollars(pr)} is in the page text', dollars(pr) in text)
        for n in nodes:
            if isinstance(n, dict) and n.get('unitText') == 'month':
                check(f'{name} monthly price {dollars(n["minPrice"])}/month is in the page text', dollars(n['minPrice']) + '/month' in text)
        for s in (n for n in nodes if isinstance(n, str)):
            for amt in _re.findall(r'\$[\d,]+', s):
                check(f'{name} amount {amt} in the block is in the page text', amt in text)
        for n in nodes:
            if isinstance(n, dict) and n.get('@type') == 'Offer':
                check(f'{name} offer "{n["name"]}" is named on the page', n['name'] in text)
                if 'description' in n:
                    check(f'{name} offer "{n["name"]}" description is word for word', n['description'] in text, n['description'])
                cur = [n.get('priceCurrency')] + [n['priceSpecification'].get('priceCurrency')] if 'priceSpecification' in n else [n.get('priceCurrency')]
                check(f'{name} offer "{n["name"]}" is in USD', set(cur) == {'USD'}, str(cur))
        check(f'{name} ld+json has no long dash', '—' not in blocks[0] and '–' not in blocks[0])
        flat = _json.dumps(data)
        for word in ('aggregateRating', 'review', 'openingHours', 'telephone', 'streetAddress', 'postalCode'):
            check(f'{name} ld+json has no {word}', f'"{word}' not in flat)
        desc = _re.search(r'<meta name="description" content="([^"]*)">', src).group(1)
        top = data['@graph'][0] if '@graph' in data else data
        check(f'{name} ld+json description is the meta description', top.get('description') == _html.unescape(desc))

    if LD.get('local'):
        src = urlopen(BASE + 'local.html').read().decode('utf-8')
        biz = next((n for n in LD['local'].get('@graph', []) if n.get('@type') == 'ProfessionalService'), {})
        faq = next((n for n in LD['local'].get('@graph', []) if n.get('@type') == 'FAQPage'), {})
        check('local business facts', biz.get('name') == "Dragoman's Journey" and biz.get('url') == 'https://dragomansjourney.com/local.html'
              and biz.get('email') == 'hello@dragomansjourney.com' and biz.get('founder') == {'@type': 'Person', 'name': 'Josef Stephens'}
              and biz.get('areaServed') == 'Sonoma County, California'
              and biz.get('address') == {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa', 'addressRegion': 'CA', 'addressCountry': 'US'}, str(biz)[:300])
        check('local email is on the page', 'hello@dragomansjourney.com' in src)
        index_ld = _json.loads(ld_blocks(urlopen(BASE + 'index.html').read().decode('utf-8'))[0])
        gh = [u for n in index_ld['@graph'] for u in n.get('sameAs', [])]
        check('local sameAs is the GitHub link index uses', biz.get('sameAs') == gh, str(biz.get('sameAs')))
        offers = biz.get('makesOffer', [])
        check('local has the Blueprint and the three cards as offers', [o.get('name') for o in offers][:1] == ['The Blueprint'] and len(offers) == 4
              and [o.get('name') for o in offers][1:] == [_html.unescape(_re.sub(r'<[^>]+>', '', h)) for h in
                                                         _re.findall(r'data-card="[^"]+".*?<h3[^>]*>(.*?)</h3>', src, _re.S)], str([o.get('name') for o in offers]))
        check('local Blueprint is a fixed $1,500 as the page says', offers and offers[0].get('price') == 1500 and '>The Blueprint · $1,500</h3>' in src, str(offers[:1]))
        qs = faq.get('mainEntity', [])
        nbtn = len(_re.findall(r'<button[^>]*data-faq="', src))
        check('local FAQ count equals the data-faq buttons', len(qs) == nbtn and nbtn > 0, f'{len(qs)} vs {nbtn}')
        text = page_text(src)
        check('local FAQ questions and answers are the page\'s own words',
              all(q['name'] in text and q['acceptedAnswer']['text'] in text for q in qs) and all('<' not in q['acceptedAnswer']['text'] for q in qs))
    if LD.get('mainframe'):
        svc = LD['mainframe']
        src = urlopen(BASE + 'mainframe.html').read().decode('utf-8')
        check('mainframe service facts', svc.get('@type') == 'Service' and svc.get('name') == 'The Mainframe Route'
              and svc.get('provider', {}).get('name') == "Dragoman's Journey"
              and svc.get('provider', {}).get('founder') == {'@type': 'Person', 'name': 'Josef Stephens'}, str(svc)[:300])
        steps = _re.search(r'id="s3-h".*?<ol.*?</ol>', src, _re.S).group(0)
        priced = [_re.sub(r'<[^>]+>', '', _re.search(r'<h3[^>]*>(.*?)</h3>', li, _re.S).group(1)) for li in _re.findall(r'<li.*?</li>', steps, _re.S)
                  if '$' in _re.findall(r'<p[^>]*>(.*?)</p>', li, _re.S)[-1]]
        check('mainframe has one offer per step that prints a price', [o.get('name') for o in svc.get('offers', [])] == priced, str(priced))
    idx = ld_blocks(urlopen(BASE + 'index.html').read().decode('utf-8'))
    check('index ld+json block is unchanged', len(idx) == 1 and _json.loads(idx[0]) == {
        '@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', 'name': "Dragoman's Journey", 'alternateName': "Dragoman's Journey · Josef Stephens", 'url': 'https://dragomansjourney.com/'},
            {'@type': 'Person', 'name': 'Josef Stephens', 'jobTitle': "Founder, Dragoman's Journey",
             'address': {'@type': 'PostalAddress', 'addressLocality': 'Santa Rosa', 'addressRegion': 'CA'},
             'sameAs': ['https://github.com/stephensjosef-cloud']}]})
    for name in ('local', 'mainframe'):
        for w in (390, 1440):
            q = newpage(w); q.goto(BASE + name + '.html'); q.wait_for_timeout(300)
            q.screenshot(path=f'{SHOTS}/t11-{name}-{w}.png')

    # ---------------- visit counter (T-12, Nov 11, 2026)
    import shutil as _shutil, subprocess as _sp, tempfile as _tmp
    COUNTER_LINE = 'This site counts page visits with Cloudflare Web Analytics, which uses no cookies.'
    ALL_HTML = [n + '.html' for n in SHARED] + ['404.html']
    for name in ALL_HTML:
        src = urlopen(BASE + name).read().decode('utf-8')
        check(f'{name} has no beacon while the token is empty', 'cloudflareinsights' not in src)
        check(f'{name} has no counter sentence while the token is empty', COUNTER_LINE not in src)
    # A temp copy of the pipeline with a made-up token: build it all, then count.
    here = os.path.dirname(os.path.abspath(__file__))
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        fp = os.path.join(bd, 'final.py')
        fsrc = open(fp, encoding='utf-8').read()
        check('final.py starts with the token empty', fsrc.count('\nCF_BEACON_TOKEN = ""\n') == 1)
        open(fp, 'w', encoding='utf-8').write(fsrc.replace('\nCF_BEACON_TOKEN = ""\n', '\nCF_BEACON_TOKEN = "0123456789abcdef0123456789abcdef"\n', 1))
        steps = [['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'],
                 [sys.executable, 'enhance.py', 'out'], [sys.executable, 'plain.py', 'out'],
                 [sys.executable, 'intent.py', 'out'], [sys.executable, 'final.py', 'out']]
        built = True
        for st in steps:
            r = _sp.run(st, cwd=bd, capture_output=True, text=True)
            if r.returncode:
                built = False
                check('temp build with a made-up token runs', False, ' '.join(st[1:2]) + ': ' + (r.stdout + r.stderr)[-300:])
                break
        if built:
            out = os.path.join(bd, 'out')
            names = sorted(f for f in os.listdir(out) if f.endswith('.html'))
            check('temp build has every page', sorted(ALL_HTML) == names, str(names))
            for name in names:
                src = open(os.path.join(out, name), encoding='utf-8').read()
                n = src.count('https://static.cloudflareinsights.com/beacon.min.js')
                if name == 'comp3.html':
                    check('comp3.html gets no beacon with a token set', n == 0 and 'cloudflareinsights' not in src, str(n))
                else:
                    check(f'{name} has exactly one beacon with a token set', n == 1, str(n))
                    check(f'{name} beacon is the docs\' form, just before </body>',
                          _re.search(r'<script\n\ttype="module"\n\tsrc="https://static\.cloudflareinsights\.com/beacon\.min\.js"\n'
                                     r'\tdata-cf-beacon=\'\{"token": "0123456789abcdef0123456789abcdef"\}\'\n></script>\n</body>', src) is not None)
            loc = open(os.path.join(out, 'local.html'), encoding='utf-8').read()
            check('local.html has the counter sentence once on the page', page_text(loc).count(COUNTER_LINE) == 1)
            a = _re.search(r'<p id="faq-a-3"[^>]*>(.*?)</p>', loc, _re.S)
            check('counter sentence ends the "What do you do with our data?" answer',
                  'What do you do with our data?</span>' in loc and a is not None and a.group(1).endswith(' ' + COUNTER_LINE))
            ld = _json.loads(ld_blocks(loc)[0])
            faq = next(n for n in ld['@graph'] if n.get('@type') == 'FAQPage')['mainEntity']
            data_a = [x['acceptedAnswer']['text'] for x in faq if x['name'] == 'What do you do with our data?']
            check('FAQPage data carries the counter sentence too', len(data_a) == 1 and data_a[0].endswith(' ' + COUNTER_LINE), str(data_a)[:200])
            others = [n for n in names if n != 'local.html']
            check('no other page has the counter sentence', not any(COUNTER_LINE in open(os.path.join(out, n), encoding='utf-8').read() for n in others))
            check('the counter adds no long dash', '—' not in COUNTER_LINE and '–' not in COUNTER_LINE)
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)

    # ---------------- the Studio page and the public build log (T-08, Nov 11, 2026)
    import datetime as _dt
    from urllib.parse import unquote as _unquote
    STUDIO_J = _json.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
    SHIPPED_J = _json.load(open(os.path.join(here, 'shipped.json'), encoding='utf-8'))
    open_p = [x for x in STUDIO_J['products'] if x.get('gate') is None]
    gated_p = [x for x in STUDIO_J['products'] if x.get('gate') is not None]
    label_of = dict({x['id']: x['name'] for x in open_p}, site='dragomansjourney.com')

    def short(d, today):
        s = d.strftime('%b') + ' ' + str(d.day)
        return s if d.year == today.year else f'{s}, {d.year}'

    src = urlopen(BASE + 'studio.html').read().decode('utf-8')
    check('sitemap lists studio.html', 'https://dragomansjourney.com/studio.html' in urlopen(BASE + 'sitemap.xml').read().decode('utf-8'))
    check('studio has no long dash', '—' not in src and '–' not in src)
    built = _re.search(r'id="stats" data-built="(\d{4}-\d\d-\d\d)"', src)
    check('studio numbers strip says its build date', bool(built))
    today = _dt.date.fromisoformat(built.group(1)) if built else _dt.date.today()
    # The log lines that should show: not from a gated product, not older than 120 days, newest first.
    hide = {x['id'] for x in gated_p}
    rows = [e for e in SHIPPED_J['entries'] if e['project'] not in hide
            and _dt.date.fromisoformat(e['date']) >= today - _dt.timedelta(days=120)]
    rows.sort(key=lambda e: e['date'], reverse=True)
    N = len(rows)
    oldest = min(_dt.date.fromisoformat(e['date']) for e in rows)

    q = newpage(1440); q.goto(BASE + 'studio.html'); q.wait_for_timeout(400)
    stats = [s.strip() for s in q.locator('#stats p').all_inner_texts()]
    stats = [_re.sub(r'\s+', ' ', s) for s in stats]
    # T-16 N4: one count, still from the log; "in the last 30 days" and "projects" are gone.
    # T-19 W28: "shipped" became "finished".
    check('studio count matches shipped.json, and is the only one', stats == [f'{N} things finished since {short(oldest, today)}'], str(stats))
    check('studio count is one block, not a three-column box (T-16)', q.eval_on_selector('#stats', 'e => getComputedStyle(e).display') == 'block'
          and abs(q.locator('#stats p').bounding_box()['width'] - q.locator('#stats').bounding_box()['width']) <= 1)
    # T-16 N2: no line over the title.
    check('studio shows the h1 from studio.json and no kicker (T-16)', q.inner_text('h1').replace('\n', ' ').upper() == _re.sub(r'<br\s*/?>', ' ', STUDIO_J['hero']['h1']).upper()
          and q.locator('header .kick').count() == 0 and 'updated as things ship' not in src)
    check('studio title unchanged', '<title>The studio · Dragoman\'s Journey</title>' in src)
    # T-16 N3: the hero keeps only its first sentence; the meta description stays as it was, and
    # still names the album only while the album card shows (fix approved Nov 11, 2026).
    INTRO = "Everything I'm building right now, and the date each piece was finished."   # T-19 W27
    HIDDEN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools and shirts, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    SHOWN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools, shirts and an album, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    album_hidden = any(x['id'] == 'album' for x in gated_p)
    hero_p = q.locator('header p').last.inner_text().strip()
    check('studio hero is the intro\'s first sentence only (T-16)', hero_p == INTRO and 'Get on a list' not in q.inner_text('header'), hero_p)
    check('studio meta description unchanged, names the album only when its card shows',
          _html.unescape(_re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) == (HIDDEN_LEDE if album_hidden else SHOWN_LEDE))
    if album_hidden:
        check('studio says no "album" while the album is hidden', 'album' not in q.inner_text('body').lower() and 'album' not in src.split('<style>')[0].lower())
    # Both states, from studio.py in a temp copy: the album hidden, then shown.
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        os.makedirs(bd)
        _shutil.copytree(os.path.join(here, 'tools'), os.path.join(bd, 'tools'), ignore=_shutil.ignore_patterns('__pycache__'))
        _shutil.copy(os.path.join(here, 'shipped.json'), bd)
        for state in ('hidden', 'shown'):
            sj = _json.load(open(os.path.join(here, 'studio.json'), encoding='utf-8'))
            for x in sj['products']:
                if x['id'] == 'album':
                    x['gate'] = 'test gate' if state == 'hidden' else None
            _json.dump(sj, open(os.path.join(bd, 'studio.json'), 'w', encoding='utf-8'))
            r = _sp.run([sys.executable, 'studio.py', '..'], cwd=os.path.join(bd, 'tools'), capture_output=True, text=True)
            page_src = open(os.path.join(bd, 'studio.html'), encoding='utf-8').read() if r.returncode == 0 else ''
            hero_txt = _re.search(r'<p style="margin:0;max-width:56ch[^"]*">([^<]*)</p>', page_src)
            hero_txt = _html.unescape(hero_txt.group(1)) if hero_txt else ''
            meta = _re.search(r'<meta name="description" content="([^"]*)"', page_src)
            want_lede = HIDDEN_LEDE if state == 'hidden' else SHOWN_LEDE
            check(f'album {state}: hero is the first sentence only (T-16)', hero_txt == INTRO, (r.stderr or hero_txt)[-200:])
            check(f'album {state}: meta description reads as approved', bool(meta) and _html.unescape(meta.group(1)) == want_lede)
            check(f'album {state}: album card ' + ('absent' if state == 'hidden' else 'present'),
                  ('data-id="album"' in page_src) == (state == 'shown'))
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)
    check('studio "Shipped lately" heading', q.locator('#log-h').inner_text().strip().lower() == 'shipped lately')
    lis = q.locator('#log li')
    check('studio log holds every line that should show', lis.count() == N, f'{lis.count()} vs {N}')
    check('studio log shows the 8 newest first', q.locator('#log li:visible').count() == min(8, N), str(q.locator('#log li:visible').count()))
    got = [[lis.nth(i).locator('time').get_attribute('datetime'), lis.nth(i).locator('time').inner_text(),
            lis.nth(i).locator('.proj').inner_text(), lis.nth(i).locator('.line').inner_text()] for i in range(lis.count())]
    want = [[e['date'], short(_dt.date.fromisoformat(e['date']), today), label_of[e['project']], e['line']] for e in rows]
    check('studio log lines, dates and labels match shipped.json, newest first', got == want, str(got[:2]))
    check('studio log leaves out gated products', not any(e['project'] in hide and e['line'] in src for e in SHIPPED_J['entries']))
    btn = q.locator('#log-all')
    check('studio "See all" names the count', btn.count() == 1 and btn.inner_text().strip() == f'See all {N}', btn.inner_text() if btn.count() else 'none')
    if btn.count():
        btn.click(); q.wait_for_timeout(150)
        check('studio "See all" reveals the rest in place', q.locator('#log li:visible').count() == N and not btn.is_visible() and q.url.endswith('studio.html'))
    arts = q.locator('#products article')
    check('studio renders every open product, in order', arts.evaluate_all('e => e.map(a => a.dataset.id)') == [x['id'] for x in open_p],
          str(arts.evaluate_all('e => e.map(a => a.dataset.id)')))
    for x in gated_p:
        check(f'studio leaves out gated product {x["id"]}', f'data-id="{x["id"]}"' not in src and x['name'] not in src and x['what'] not in src)
    for x in open_p:
        card = q.locator(f'#products article[data-id="{x["id"]}"]')
        txt = card.inner_text()
        check(f'studio card {x["id"]}: name, status and what from the JSON',
              card.locator('h2').inner_text().upper() == x['name'].upper() and card.locator('.pill').inner_text() == x['status']
              and x['what'] in txt)
        # T-16 N6: the kind stays in the JSON but isn't printed on the card.
        check(f'studio card {x["id"]}: no kind label (T-16)', card.locator('.kind').count() == 0
              and x['kind'].upper() not in card.locator('.meta').inner_text().upper(), card.locator('.meta').inner_text())
        if x.get('proof'):
            check(f'studio card {x["id"]}: proof line in bold', card.locator('strong', has_text=x['proof']).count() == 1)
        if x.get('image'):
            check(f'studio card {x["id"]}: image', card.locator(f'img[src="{x["image"]}"]').get_attribute('alt') == x['image_alt'])
        if x.get('link'):
            lk = card.locator(f'a[href="{x["link"]["href"]}"]')
            check(f'studio card {x["id"]}: link', lk.count() == 1 and lk.inner_text().startswith(x['link']['label']))
        if x.get('list'):
            # T-10: the join button sits in a small form; its mailto is the form's action and the fallback.
            jf = card.locator('form.jf[data-list]')
            href = jf.get_attribute('action') if jf.count() == 1 else ''
            check(f'studio card {x["id"]}: join box for list {x["list"]["id"]}, mailto "List: {x["name"]}" as its fallback',
                  jf.count() == 1 and jf.get_attribute('data-list') == x['list']['id'] and jf.locator('button').inner_text() == x['list']['button']
                  and href.startswith('mailto:hello@dragomansjourney.com?subject=')
                  and _unquote(href.split('subject=', 1)[1]) == 'List: ' + x['name'], href)
            check(f'studio card {x["id"]}: list count shows only at 10 or more',
                  ('people on the list' in txt) == (x['list'].get('count', 0) >= 10))
    # The count rule, on a made-up count either side of 10.
    sys.path.insert(0, os.path.join(here, 'tools'))
    import studio as _studio
    p41 = dict(open_p[0], list=dict(open_p[0].get('list') or {'id': 'x', 'button': 'b'}, count=41))
    p9 = dict(p41, list=dict(p41['list'], count=9))
    check('a list of 41 says "41 people on the list"', '>41 people on the list<' in _studio.product_card(p41))
    check('a list of 9 shows no count', 'on the list' not in _studio.product_card(p9))
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'studio.html'); q.wait_for_timeout(400)
        check(f'studio no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        boxes = q.locator('#products article').evaluate_all('e => e.map(a => [a.dataset.id, Math.round(a.getBoundingClientRect().left), Math.round(a.getBoundingClientRect().width)])')
        grid_w = round(q.locator('#products').bounding_box()['width'])
        full = [b_[0] for b_ in boxes if abs(b_[2] - grid_w) <= 2]
        if w == 390:
            check('studio products in one column at 390', len({b_[1] for b_ in boxes}) == 1 and len(full) == len(boxes), str(boxes))
        else:
            check('studio products in two columns at 1440', len({b_[1] for b_ in boxes}) == 2, str(boxes))
            check('Bird League spans the full width at 1440', full == ['birdleague'], str(full))
        q.screenshot(path=f'{SHOTS}/t08-studio-{w}.png', full_page=True)

    # T-16 N1: the home page's "Shipped lately" strip is gone; the header's Studio link stays.
    src = urlopen(BASE + 'index.html').read().decode('utf-8')
    check('home has no "Shipped lately" strip (T-16)', 'id="shipped"' not in src and 'Shipped lately' not in src
          and "See everything I'm building" not in _html.unescape(src) and not any(e['line'] in _html.unescape(src) for e in SHIPPED_J['entries']))
    check('home hero runs straight into the two routes (T-16)', _re.search(r'</header>\s*<!-- the two routes -->', src) is not None)
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(300)
        check(f'home no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'home header keeps its Studio link at {w}', q.locator('a[href="studio.html"]').count() == 1)
        q.screenshot(path=f'{SHOTS}/t16-home-top-{w}.png')

    # Studio in every header, before Free tools, except the three Mainframe pages (T-16).
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="studio\.html"[^>]*>([^<]*)</a>', top)
        if name in MAINFRAME_PAGES:
            check(f'{name} header has no Studio link (T-16)', bool(top) and links == [] and '>Studio<' not in top, str(links))
            continue
        check(f'{name} nav links Studio', links == ['Studio'], str(links))
        check(f'{name} Studio sits before Free tools', -1 < top.find('href="studio.html"') < top.find('work.html#free'))

    # enhance.py refuses a studio.html that is older than its JSON.
    tmp = _tmp.mkdtemp()
    try:
        bd = os.path.join(tmp, '_build')
        _shutil.copytree(here, bd, ignore=_shutil.ignore_patterns('out', 'vals.json', '__pycache__', 'trip', 'worker'))
        with open(os.path.join(bd, 'shipped.json'), 'a', encoding='utf-8') as f:
            f.write('\n')
        r = None
        for st in ([['node', 'dump.js', 'canvas', 'vals.json'], [sys.executable, 'build.py', 'canvas', 'out', 'vals.json'], [sys.executable, 'enhance.py', 'out']]):
            r = _sp.run(st, cwd=bd, capture_output=True, text=True)
            if r.returncode:
                break
        check('enhance.py stops when studio.html is older than shipped.json', r.returncode != 0 and 'studio.html is older' in r.stdout + r.stderr, (r.stdout + r.stderr)[-200:])
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)

    # ---------------- a page per Studio product (T-09, Nov 11, 2026)
    page_p = [x for x in open_p if x.get('list')]
    check('one page per open product with a join list', [x['id'] for x in page_p] == ['birdleague', 'deepcuts'], str([x['id'] for x in page_p]))
    sitemap = urlopen(BASE + 'sitemap.xml').read().decode('utf-8')
    for x in STUDIO_J['products']:
        slug = f'studio-{x["id"]}.html'
        if x in page_p:
            continue
        try:
            urlopen(BASE + slug); served = True
        except Exception:
            served = False
        check(f'no page for {x["id"]} ({"gated" if x.get("gate") else "no join list"})', not served and slug not in sitemap)
    q = newpage(1440); q.goto(BASE + 'studio.html'); q.wait_for_timeout(300)
    for x in open_p:
        mv = q.locator(f'#products article[data-id="{x["id"]}"] a[data-page]')
        if x in page_p:
            check(f'studio card {x["id"]} links "More on {x["name"]} →" to its page (T-16)',
                  mv.count() == 1 and mv.inner_text().strip() == f'More on {x["name"]} →' and mv.get_attribute('href') == f'studio-{x["id"]}.html')
        else:
            check(f'studio card {x["id"]} has no page link', mv.count() == 0)
    for x in page_p:
        slug = f'studio-{x["id"]}.html'
        src = urlopen(BASE + slug).read().decode('utf-8')
        check(f'{slug} in the sitemap', f'https://dragomansjourney.com/{slug}' in sitemap)
        check(f'{slug} has no long dash', '—' not in src and '–' not in src)
        check(f'{slug} title and meta description from the JSON',
              f'<title>{_html.escape(x["name"], quote=False)} · Dragoman\'s Journey</title>' in src
              and _html.unescape(_re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) == x['what'])
        q = newpage(1440); q.goto(BASE + slug); q.wait_for_timeout(300)
        hd = q.locator('header')
        check(f'{slug}: the name big', q.locator('h1').count() == 1 and q.inner_text('h1').strip().upper() == x['name'].upper())
        check(f'{slug}: status pill under the name', hd.locator('.hero-pill').inner_text() == x['status']
              and hd.locator('.hero-pill').bounding_box()['y'] > q.locator('h1').bounding_box()['y'])
        check(f'{slug}: what, from the JSON', x['what'] in hd.inner_text())
        # T-16 N8: the line over the title is one link back, "← The Studio", and nothing else.
        check(f'{slug}: the line over the title is one link, "← The Studio", to studio.html (T-16)',
              hd.locator('.kick a').count() == 1 and hd.locator('.kick a').get_attribute('href') == 'studio.html'
              and hd.locator('.kick').text_content().strip() == '← The Studio' and hd.locator('.kick a').text_content() == '← The Studio',
              hd.locator('.kick').text_content())
        main_ = q.locator('main')
        if x.get('proof'):
            check(f'{slug}: proof line in bold', main_.locator('strong', has_text=x['proof']).count() == 1)
        else:
            check(f'{slug}: no proof line when the JSON has none', main_.locator('.proof').count() == 0)
        if x.get('image'):
            check(f'{slug}: image', main_.locator(f'img[src="{x["image"]}"]').get_attribute('alt') == x['image_alt'])
        else:
            check(f'{slug}: no image when the JSON has none', main_.locator('img').count() == 0)
        mine = [e for e in rows if e['project'] == x['id']]
        lis = q.locator('#log li')
        got = [[lis.nth(i).locator('time').get_attribute('datetime'), lis.nth(i).locator('time').inner_text(),
                lis.nth(i).locator('.line').inner_text()] for i in range(lis.count())]
        want = [[e['date'], short(_dt.date.fromisoformat(e['date']), today), e['line']] for e in mine]
        check(f'{slug}: log matches shipped.json for {x["id"]}, newest first, with dates', got == want and len(want) > 0, str(got[:2]))
        check(f'{slug}: every log line shows', q.locator('#log li:visible').count() == len(mine) and q.locator('#log-all').count() == 0)
        check(f'{slug}: "Shipped lately" heading', q.locator('#log-h').inner_text().strip().lower() == 'shipped lately')
        check(f'{slug}: no other project\'s lines', not any(e['line'] in src for e in SHIPPED_J['entries'] if e['project'] != x['id']))
        jf = q.locator('#join form.jf[data-list]')
        href = jf.get_attribute('action') if jf.count() == 1 else ''
        check(f'{slug}: one join box, mailto "List: {x["name"]}" as its fallback', q.locator('#join').count() == 1 and q.locator('form.jf').count() == 1
              and jf.get_attribute('data-list') == x['list']['id']
              and jf.locator('button').inner_text() == x['list']['button'] and href.startswith('mailto:hello@dragomansjourney.com?subject=')
              and _unquote(href.split('subject=', 1)[1]) == 'List: ' + x['name'], href)
        check(f'{slug}: the line under the join box', q.locator('#join p').inner_text().strip() == x['list']['line'])
        check(f'{slug}: join box comes last, after the log', q.locator('#join').bounding_box()['y'] > q.locator('#log').bounding_box()['y'])
        check(f'{slug}: list count shows only at 10 or more', ('people on the list' in q.inner_text('#join')) == (x['list'].get('count', 0) >= 10))
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            check(f'{slug}: no sideways scroll at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.screenshot(path=f'{SHOTS}/t09-{x["id"]}-{w}.png', full_page=True)
    # The page list follows the JSON: a product that loses its gate and has a list gets a page.
    sj = _json.loads(_json.dumps(STUDIO_J))
    for x in sj['products']:
        x['gate'] = None
    check('a product gets a page once its gate clears', [s for s, _ in _studio.product_pages(sj)] == ['studio-birdleague.html', 'studio-deepcuts.html', 'studio-album.html'])

    # ---------------- real join lists (T-10, Nov 11, 2026)
    # The Worker, with no network: intake.js and intake.deployed.js agree, the list form works, the old forms don't change.
    r = _sp.run(['node', 'test_intake.mjs'], cwd=os.path.join(here, 'worker'), capture_output=True, text=True)
    check('worker: node test_intake.mjs passes', r.returncode == 0 and ' passed' in r.stdout, (r.stdout + r.stderr)[-400:])
    wk = open(os.path.join(here, 'worker', 'intake.js'), encoding='utf-8').read()
    check('worker: the four lists, as the item names them', 'const LISTS = ["birdleague", "deepcuts", "album", "spots-feb"];' in wk)
    check('worker: every Studio join list is one the Worker takes',
          all(x['list']['id'] in ('birdleague', 'deepcuts', 'album', 'spots-feb') for x in STUDIO_J['products'] if x.get('list')))
    start_ep = _re.search(r"var ENDPOINT = '([^']+)'", open(os.path.join(here, 'start.html'), encoding='utf-8').read()).group(1)
    check('join boxes post to the same Worker as start.html', _studio.ENDPOINT == start_ep, _studio.ENDPOINT)
    # Catch the fallback mailto instead of letting the browser open a mail app.
    CATCH_MAILTO = ("window.__mailto = []; document.addEventListener('click', function (e) {"
                    " var a = e.target.closest && e.target.closest('a[href^=\"mailto:\"]');"
                    " if (a && a.hidden) { window.__mailto.push(a.getAttribute('href')); e.preventDefault(); } }, true);")

    def mock_abort(route):
        return route.abort()
    join_pages = [('studio.html', x) for x in open_p if x.get('list')] + [(f'studio-{x["id"]}.html', x) for x in page_p]
    for slug, x in join_pages:
        box = (f'#products article[data-id="{x["id"]}"] ' if slug == 'studio.html' else '#join ') + 'form.jf'
        tag = f'{slug} ({x["id"]})' if slug == 'studio.html' else slug
        shoot = slug != 'studio.html' or x['id'] == 'deepcuts'
        # Success: the right fields go to the Worker, and the box says so.
        q = newpage(1440); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock_ok); q.add_init_script(CATCH_MAILTO)
        q.goto(BASE + slug); q.wait_for_timeout(300)
        f = q.locator(box)
        check(f'{tag}: email field is required, type email, labeled "Email"',
              f.locator('input[name="email"][type="email"][required]').count() == 1 and f.locator('label.jf-e span').inner_text().strip().lower() == 'email')
        check(f'{tag}: honeypot is there and off screen', f.locator('.hp input[name="website"]').count() == 1
              and f.locator('.hp').bounding_box()['x'] < -1000)
        n0 = len(posts)
        f.locator('button').click(); q.wait_for_timeout(300)
        check(f'{tag}: an empty email sends nothing', len(posts) == n0 and q.evaluate('window.__mailto.length') == 0)
        f.locator('input[name="email"]').fill('  fan@example.com '); q.wait_for_timeout(2700)
        f.locator('button').click(); q.wait_for_timeout(600)
        sent = posts[-1] if len(posts) == n0 + 1 else {}
        check(f'{tag}: posts form=list with the email and list {x["list"]["id"]}, honeypot and time',
              sent.get('form') == 'list' and sent.get('fields') == {'email': 'fan@example.com', 'list': x['list']['id']}
              and sent.get('website') == '' and sent.get('ms', 0) >= 2500, str(sent))
        check(f'{tag}: success says "You\'re on the list"', f.locator('.jf-ok').inner_text().strip() == "You're on the list"
              and f.locator('.jf-ok').get_attribute('role') == 'status')
        check(f'{tag}: success hides the field and the button', not f.locator('input[name="email"]').is_visible() and not f.locator('button').is_visible())
        check(f'{tag}: success opens no mailto', q.evaluate('window.__mailto.length') == 0)
        for w in (390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            check(f'{tag}: no sideways scroll after success at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            if shoot:
                f.scroll_into_view_if_needed(); q.screenshot(path=f'{SHOTS}/t10-{slug[:-5]}-ok-{w}.png')
        # Failure (the Worker says no, or can't be reached): the mailto opens, the box stays as it was.
        for how, mock in (('an error answer', mock_fail), ('no connection', mock_abort)):
            q = newpage(390); q.route('**/dj-intake.stephens-josef.workers.dev/**', mock); q.add_init_script(CATCH_MAILTO)
            q.goto(BASE + slug); q.wait_for_timeout(300)
            f = q.locator(box)
            f.locator('input[name="email"]').fill('fan@example.com'); q.wait_for_timeout(2700)
            f.locator('button').click(); q.wait_for_timeout(600)
            got = q.evaluate('window.__mailto')
            check(f'{tag}: on {how}, falls back to the mailto "List: {x["name"]}"', len(got) == 1 and got[0] == f.get_attribute('action')
                  and _unquote(got[0].split('subject=', 1)[1]) == 'List: ' + x['name'], str(got))
            check(f'{tag}: on {how}, the box stays ready to try again', f.locator('input[name="email"]').is_visible()
                  and f.locator('button').is_enabled() and f.locator('button').inner_text() == x['list']['button']
                  and f.locator('.jf-ok').inner_text().strip() == '')
            if how == 'an error answer' and shoot:
                f.scroll_into_view_if_needed(); q.screenshot(path=f'{SHOTS}/t10-{slug[:-5]}-fail-390.png')
    check('join boxes: no long dash in the join script', '—' not in _studio.JOIN_SCRIPT and '–' not in _studio.JOIN_SCRIPT)

    # ---------------- website checkup (T-04, Nov 12, 2026)
    # The Worker, with no network: safety rules, link classifier, 8a to 8e, and local.html through 8b (step 12).
    import tempfile as _tf
    lp = os.path.join(_tf.mkdtemp(), 'local.html')
    open(lp, 'w', encoding='utf-8').write(urlopen(BASE + 'local.html').read().decode('utf-8'))
    r = _sp.run(['node', 'test_checkup.mjs', lp], cwd=os.path.join(here, 'worker'), capture_output=True, text=True)
    check('checkup worker: node test_checkup.mjs passes (with local.html from the build)', r.returncode == 0 and ' passed' in r.stdout, (r.stdout + r.stderr)[-600:])
    check('checkup worker: local.html ran through the 8b check', 'FAIL local.html' not in r.stdout and r.stdout.strip().split('/')[0] == r.stdout.strip().split('/')[1].split()[0])
    ck = open(os.path.join(here, 'worker', 'checkup.js'), encoding='utf-8').read()
    check('checkup worker: separate from intake (no email, no intake code)', 'cloudflare:email' not in ck and 'SEB' not in ck)
    check('checkup worker: CORS for the same origins as intake', _re.search(r'const ORIGINS = \[[^\]]*\];', ck).group(0) == _re.search(r'const ORIGINS = \[[^\]]*\];', wk).group(0))
    check('checkup worker: no long dash', '—' not in ck and '–' not in ck)
    SAMPLE = _json.loads(_sp.run(['node', 'test_checkup.mjs', '--sample'], cwd=os.path.join(here, 'worker'), capture_output=True, text=True).stdout)

    src = urlopen(BASE + 'checkup.html').read().decode('utf-8')
    check('checkup: sitemap lists it', 'https://dragomansjourney.com/checkup.html' in urlopen(BASE + 'sitemap.xml').read().decode('utf-8'))
    check('checkup: CHECKUP_URL is one empty constant at the top of the script', src.count("var CHECKUP_URL = '';") == 1
          and _re.search(r"<script>\s*function djToast[\s\S]*?\n\s*var CHECKUP_URL = '';", src) is not None)
    check('checkup: the line under the box', "This checks your public page the way a visitor's phone would. Nothing is stored." in src)
    check('checkup: no long dash', '—' not in src and '–' not in src)
    work = urlopen(BASE + 'work.html').read().decode('utf-8')
    card = _re.search(r'<article class="card" data-k="([^"]*)">((?:(?!</article>).)*href="checkup\.html"(?:(?!</article>).)*)</article>', work, _re.S)
    # T-16 N10: the card keeps its place but no longer carries the "25 links" figure.
    check('checkup: a fifth tool card on the work page, data-k free, "Website checkup", no figure', bool(card) and card.group(1) == 'free'
          and 'class="num"' not in card.group(2) and '25 links' not in card.group(2) and '<h2>Website checkup</h2>' in card.group(2))

    # Until the Worker is live: "Coming this week", no box, nothing sent.
    sent = []
    for w in (390, 1440):
        q = newpage(w); q.on('request', lambda rq: sent.append(rq.url) if 'checkup' in rq.url and not rq.url.startswith(BASE) else None)
        q.goto(BASE + 'checkup.html'); q.wait_for_timeout(400)
        check(f'checkup: says "Coming this week" at {w}', q.locator('#soon').is_visible() and q.inner_text('#soon').strip().upper() == 'COMING THIS WEEK')
        check(f'checkup: no box while CHECKUP_URL is empty at {w}', not q.locator('#ask').is_visible() and not q.locator('#site').is_visible() and not q.locator('#go').is_visible())
        check(f'checkup: no report cards before a check at {w}', not q.locator('#rep1').is_visible() and not q.locator('#rep2').is_visible() and not q.locator('#stat').is_visible())
        check(f'checkup: no sideways scroll, coming soon, at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.screenshot(path=f'{SHOTS}/t04-soon-{w}.png', full_page=True)
    check('checkup: nothing sent while it says coming this week', not sent, str(sent))

    # With a Worker address set (in the browser only, the file is untouched) and the Worker answering the sample.
    def live_page(w, answer):
        q = newpage(w, 1000)
        calls = []
        def page_route(route):
            body = route.fetch().text().replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1)
            route.fulfill(status=200, content_type='text/html', body=body)
        def worker(route):
            calls.append(route.request.url)
            route.fulfill(status=200 if answer.get('ok') else 400, content_type='application/json', body=_json.dumps(answer), headers={'Access-Control-Allow-Origin': '*'})
        q.route(BASE + 'checkup.html', page_route)
        q.route('https://dj-checkup.test/**', worker)
        q.goto(BASE + 'checkup.html'); q.wait_for_timeout(400)
        return q, calls
    q, calls = live_page(1440, SAMPLE)
    check('checkup live: the box shows, coming soon hides', q.locator('#site').is_visible() and q.inner_text('#go') == 'Check it' and not q.locator('#soon').is_visible())
    check('checkup live: nothing sent before the button', calls == [])
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: one GET with the address', len(calls) == 1 and calls[0] == 'https://dj-checkup.test/?url=crumb.example', str(calls))
    heads = q.locator('#finds1 .find h3').all_inner_texts()
    levels = q.eval_on_selector_all('#finds1 .find', 'e => e.map(x => x.classList.contains("bad") ? 0 : x.classList.contains("warn") ? 1 : 2)')
    check('checkup live: the worst finding first', heads[:1] == ['Your "Book Now" button leads to an error page'], str(heads))
    check('checkup live: worst to mildest, all the way down', levels == sorted(levels), str(levels))
    first = q.locator('#finds1 .find').first.inner_text()
    check('checkup live: a finding says what it costs and how hard it is to fix', "People who tap it can't book." in first and 'A five-minute fix in your site builder' in first, first)
    check('checkup live: the "#" Donate button goes nowhere', 'Your "Donate" button goes nowhere' in heads)
    check('checkup live: no phone layout, no tap-to-call, no description, http not sent on', all(h in heads for h in (
        "Your page isn't set up for phones", "Your phone number can't be tapped to call", 'Your page has no description',
        "The plain http address doesn't send people on to https")), str(heads))
    check('checkup live: what works is listed', '1 button works: "Order online".' in q.inner_text('#oks1'), q.inner_text('#oks1'))
    rep1 = q.locator('#rep1')
    check('checkup live: ends with "Want me to fix it?" to call.html', rep1.locator('a').last.get_attribute('href') == 'call.html'
          and rep1.locator('a').last.inner_text().startswith('Want me to fix it?')
          and q.evaluate("document.querySelector('#rep1').lastElementChild.getAttribute('href')") == 'call.html')
    st = q.locator('#stat')
    check('checkup live: the BrightLocal line sits above the second card, with its year and source', st.is_visible()
          and '45%' in st.inner_text() and '2026' in st.inner_text() and 'BrightLocal' in st.inner_text()
          and st.locator('a').get_attribute('href') == 'https://www.brightlocal.com/research/local-consumer-review-survey/'
          and st.bounding_box()['y'] < q.locator('#rep2').bounding_box()['y'] and q.locator('#rep1').bounding_box()['y'] < st.bounding_box()['y'])
    check('checkup live: second card heading', q.inner_text('#rep2-h') == 'Can AI find you?')
    check('checkup live: its first line, exactly', q.locator('#rep2 > p').first.inner_text() ==
          "This doesn't tell you what ChatGPT says about you. It checks whether a computer can find the basic facts about your business on your page.")   # T-19 W22
    heads2 = q.locator('#finds2 .find h3').all_inner_texts()
    levels2 = q.eval_on_selector_all('#finds2 .find', 'e => e.map(x => x.classList.contains("bad") ? 0 : x.classList.contains("warn") ? 1 : 2)')
    check('checkup live: blocking a search crawler turns AI readers away, worst first', heads2[:1] == ['Your site turns AI readers away']
          and 'OAI-SearchBot' in q.locator('#finds2 .find').first.inner_text() and levels2 == sorted(levels2), str(heads2))
    check('checkup live: blocking only training is a choice, in one plain line',
          'Your robots.txt keeps GPTBot from collecting your pages for AI training. That\'s a choice, not a fault.' in heads2
          and not any('GPTBot' in h for h in heads2[:1]), str(heads2))
    check('checkup live: two phone numbers are flagged', 'Your page gives two different phone numbers' in heads2)
    check('checkup live: hours not found, said as "I couldn\'t find"', "I couldn't find your opening hours in your page text" in heads2)
    check('checkup live: never says "missing"', 'missing' not in q.inner_text('#rep2').lower() and 'missing' not in q.inner_text('#rep1').lower())
    facts = dict(zip(q.locator('#facts dt').all_text_contents(), q.locator('#facts dd').all_text_contents()))
    check('checkup live: the facts card, as found', q.inner_text('#rep2 .facts h3') == 'What a computer can read off your page'   # T-19 W23
          and list(facts) == ['Name', 'Phone', 'Address', 'Hours'] and facts['Name'] == 'Crumb Bakery' and facts['Phone'] == '(707) 555-0134'
          and facts['Address'] == '12 Main St, Santa Rosa, CA' and facts['Hours'] == "I couldn't find it", str(facts))
    check('checkup live: the facts card ends with the profile line', q.locator('#rep2 .facts p').last.inner_text() ==
          "Compare these with your Google listing. They should match exactly. I can't see your listing from here.")   # T-19 W24
    for w in (390, 1440):
        q.set_viewport_size({'width': w, 'height': 1000}); q.wait_for_timeout(200)
        check(f'checkup live: no sideways scroll with both reports at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.evaluate('scrollTo(0, 0)'); q.wait_for_timeout(100)
        q.screenshot(path=f'{SHOTS}/t04-report-{w}.png', full_page=True)
    # 8d's exact sentence, on a page with almost no readable text.
    thin = _json.loads(_json.dumps(SAMPLE)); thin['facts']['textLength'] = 120
    q, calls = live_page(390, thin)
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: almost no readable text, in the item\'s words', "Your page holds almost no text a machine can read without running scripts or reading images." in q.locator('#finds2 .find h3').all_inner_texts())
    thin['cut'] = True
    q, calls = live_page(390, thin)
    q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
    check('checkup live: no text warning when the page was cut at 1.5 MB', not any('almost no text' in h for h in q.locator('#finds2 .find h3').all_inner_texts()))
    # A refused address: a plain answer, no report.
    q, calls = live_page(390, {'ok': False, 'error': 'private-name'})
    q.fill('#site', 'printer.local'); q.click('#go'); q.wait_for_timeout(600)
    check('checkup live: a refused address gets a plain answer and no report', 'inside a home or office network' in q.inner_text('#msg')
          and not q.locator('#rep1').is_visible() and q.inner_text('#go') == 'Check it')
    q.screenshot(path=f'{SHOTS}/t04-refused-390.png', full_page=True)

    # ---------------- intent pass 2 (T-16, Nov 12, 2026)
    def text_of(src):
        return _html.unescape(_re.sub(r'<[^>]+>', ' ', _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S)))
    T16_PAGES = ('index', 'studio', 'studio-birdleague', 'studio-deepcuts', 'work', 'shotlist', 'captions', 'receipt',
                 'scaler', 'checkup', 'local', 'mainframe', 'briefing', 'comp3')
    site = {n: urlopen(BASE + n + '.html').read().decode('utf-8') for n in SHARED + ('index',)}

    # N5: four log lines gone everywhere, one shortened, the stranger rule written down.
    GONE = ["Bird League build 50 runs on Apple's newest tools.", 'Deepcuts build 4 works end to end on iPhone.',
            "Build 2 of the kids' cooking app, checked screen by screen on a real phone.",
            "Every word on dragomansjourney.com rechecked: if it isn't there for a reader, it's gone.",
            'Deepcuts got its new look, built and walked through on iPhone.']
    check('N5: the removed log lines are on no page', not any(g in text_of(s) for g in GONE for s in site.values()))
    check('N5: shipped.json no longer holds them', not any(g == e['line'] for g in GONE for e in SHIPPED_J['entries']) and len(SHIPPED_J['entries']) == 14)
    check('N5: the Deepcuts line reads "Deepcuts got its new look."', any(e['line'] == 'Deepcuts got its new look.' and e['date'] == '2026-11-04' for e in SHIPPED_J['entries'])
          and 'Deepcuts got its new look.' in text_of(site['studio']) and 'Deepcuts got its new look.' in text_of(site['studio-deepcuts']))
    RULE = 'A line stays only if a stranger can picture what changed: no build number without what a person can now do.'
    check('N5: the stranger rule ends shipped.json\'s _about and is in the README\'s "To log a ship" line',
          SHIPPED_J['_about'].endswith(RULE) and any(l.startswith('   To log a ship:') and RULE in l for l in open(os.path.join(here, 'README.md'), encoding='utf-8')))
    # N9: each product page's log is the JSON's, already checked above; and none of the removed lines.
    for slug in ('studio-birdleague', 'studio-deepcuts'):
        check(f'N9: {slug} log follows shipped.json, without the removed lines', not any(g in text_of(site[slug]) for g in GONE))

    # N10 to N12: the work page.
    q = newpage(1440); q.goto(BASE + 'work.html'); q.wait_for_timeout(400)
    figs = dict(q.locator('#cards .card').evaluate_all('e => e.map(c => [c.querySelector("h2").textContent, c.querySelector(".num") ? c.querySelector(".num").textContent : null])'))
    # T-19 W4 to W6: the three figures now say what they count.
    KEEP = {'One cooking-class shoot, one finished reel': 'An 81-second reel in about 4 minutes', 'A seasonal cooking app for teachers': '535 automatic checks',
            'A banking program, checked in public': '2 AI translations of one bank program'}
    check('N10: only the three cards with a real result keep their figure', {k: v for k, v in figs.items() if v} == KEEP and len(figs) == 10, str(figs))
    for gone in ('0 → real users', 'Free</p>', '10 clips', '0 stranded words', '1 year, rung up', '×3, measurable', '25 links'):
        check(f'N10: figure "{gone.replace("</p>", "")}" is gone', f'<p class="num">{gone}' not in site['work'])

    def lined_up(pg, label):
        # Cards in one row share their top and height, and their links sit on one line.
        cards = pg.locator('#cards .card:visible:not(.feature)').evaluate_all(
            'e => e.map(c => { const r = c.getBoundingClientRect(), g = c.querySelector("a.go").getBoundingClientRect();'
            ' return [Math.round(r.top), Math.round(r.height), Math.round(g.bottom - r.top), !!c.querySelector(".num")]; })')
        rows_ = {}
        for c in cards:
            rows_.setdefault(c[0], []).append(c)
        mixed = [r for r in rows_.values() if len({c[3] for c in r}) == 2]
        ok_ = all(len({c[1] for c in r}) == 1 and max(c[2] for c in r) - min(c[2] for c in r) <= 1 for r in rows_.values())
        check(f'N10: cards line up, with and without a figure ({label})', ok_ and len(cards) > 0, str(rows_))
        return mixed
    lined_up(q, 'all cards at 1440')
    for f_ in ('nonprofit', 'banking'):
        q.click(f'.filt[data-f="{f_}"]'); q.wait_for_timeout(150)
        mixed = lined_up(q, f'{f_} filter at 1440')
        check(f'N10: the {f_} filter puts cards with and without a figure in one row', len(mixed) == 1, str(mixed))
        q.screenshot(path=f'{SHOTS}/t16-work-{f_}-1440.png', full_page=True)
    bl = q.locator('#cards .card.feature a.go')
    check('N11: the Bird League card links "See Bird League →" to studio-birdleague.html', bl.count() == 1 and bl.inner_text().strip() == 'See Bird League →'
          and bl.get_attribute('href') == 'studio-birdleague.html')
    check('N11: "More about how I work" is gone', 'More about how I work' not in site['work'])
    check('N12: the cooking app card says "iPhone, iPad, Android and the web."', 'iPhone, iPad, Android and the web.</p>' in site['work']
          and 'iPhone, iPad and Android.</p>' not in site['work'])

    # N15: the scaler intro.
    # T-18 S25 replaced the intro; it still leaves "Kids count as half a portion." out.
    check('N15: the scaler intro drops "Kids count as half a portion."', 'Kids count as half a portion.' not in site['scaler']
          and "Paste a recipe and say who's eating. You get amounts you can actually measure." in _html.unescape(site['scaler']))
    check('N15: the line under the boxes still says it', 'A kid counts as half a portion.' in site['scaler'])

    # N16: the shot list countdown shows from 42 days out to the day itself, and not before.
    def shot_at(when, nonprofit=False):
        pg = newpage(390); pg.clock.set_fixed_time(when); pg.goto(BASE + 'shotlist.html'); pg.wait_for_timeout(300)
        if nonprofit:
            pg.click('.chip[data-k="type"][data-v="nonprofit"]'); pg.wait_for_timeout(100)
        return pg
    for when, np_, want in (('2026-10-17T12:00:00', False, '42 days'), ('2026-10-16T12:00:00', False, None),
                            ('2026-10-20T12:00:00', True, '42 days'), ('2026-10-19T12:00:00', True, None),
                            ('2026-11-28T09:00:00', False, 'Today'), ('2026-11-12T12:00:00', False, '16 days')):
        pg = shot_at(when, np_)
        who = 'Giving Tuesday' if np_ else 'Small Business Saturday'
        if want:
            check(f'N16: {when[:10]}, {who}: countdown shows "{want}"', pg.locator('#when').is_visible() and pg.inner_text('#days').strip() == want
                  and who in pg.inner_text('#dayslabel'), pg.inner_text('#days'))
        else:
            # T-18 S9: the countdown is its own box now, so with no countdown the whole box is gone.
            check(f'N16: {when[:10]}, {who}: 43 days out, no countdown and no empty box', not pg.locator('#when').is_visible()
                  and pg.locator('#when').bounding_box() is None and who not in pg.inner_text('main'))
        if when.startswith('2026-10-1') and not np_:
            pg.locator('main').screenshot(path=f'{SHOTS}/t16-shotlist-countdown-{when[:10]}-390.png')

    # N17, N18: local.html.
    lt = text_of(site['local'])
    check('N17: "Recently finished" and its four lines are gone', 'Recently finished' not in lt and 'id="log-h"' not in site['local']
          and 'Export to eBird goes live' not in lt and 'First run on a real shoot' not in lt and 'SHIPPED LOG' not in site['local'])
    q = newpage(390); q.goto(BASE + 'local.html'); q.wait_for_timeout(300)
    card = q.locator('#dropin form#dl').locator('xpath=..')
    ct = card.inner_text()
    check('N18: no date set, the drop-in box says it in one line', "No date set yet. Leave your email and you'll get it first." in ct
          and 'NEXT DROP-IN' not in ct.upper() and 'Get the next date' not in ct and "Sign up and you'll hear the date first." not in ct, ct[:200])
    check('N18: the form and its button stay', q.locator('#dl-email').count() == 1 and q.locator('#dl-name').count() == 1
          and q.inner_text('#dl-send').strip() == 'Put me on the list →')
    q.locator('#dropin').screenshot(path=f'{SHOTS}/t16-dropin-390.png')

    # N22: the BrightLocal line.
    check('N22: the line above the second card names who was asked',
          '45% of US adults surveyed now use ChatGPT and other AI tools for local recommendations, up from 6% a year before (BrightLocal, 2026). <a href="https://www.brightlocal.com/research/local-consumer-review-survey/" target="_blank" rel="noopener">See the source</a>' in site['checkup']
          and '45% of people now' not in site['checkup'])

    # N24: the lone 05 and 06 are gone; the audit report's 01 to 07 stay.
    q = newpage(1440); q.goto(BASE + 'mainframe.html'); q.wait_for_timeout(300)
    toc = q.locator('[data-toc] span').evaluate_all('e => e.map(s => s.textContent.trim()).filter(t => /^0[0-9]$/.test(t))')
    check('N24: the audit report still lists 01 to 07', toc == ['01', '02', '03', '04', '05', '06', '07'], str(toc))
    lone = q.evaluate('[...document.querySelectorAll("span")].filter(s => /^0[0-9]$/.test(s.textContent.trim()) && !s.closest("[data-toc]")).length')
    check('N24: no lone section number left on the page', lone == 0, str(lone))
    check('N24: no empty column left where 05 was', q.eval_on_selector('#s5 > div', 'e => e.children.length === 1 && !!e.firstElementChild.querySelector("#s6-h")'))
    check('N24: the section about Josef keeps its photo column', q.locator('#s7 > div > div').first.locator('img, [role="img"]').count() == 1
          and q.locator('#s7 > div > div').first.inner_text().strip() == '')

    # Look rule: every changed page at 320, 390 and 1440, no sideways scroll on phones.
    for n in T16_PAGES:
        q = newpage(320); q.goto(BASE + n + '.html'); q.wait_for_timeout(400)
        for w in (320, 390, 1440):
            q.set_viewport_size({'width': w, 'height': 900}); q.wait_for_timeout(200)
            if w < 1440:
                sw = q.evaluate('document.documentElement.scrollWidth')
                check(f'T-16: {n} has no sideways scroll at {w}', sw <= w, str(sw))
            q.screenshot(path=f'{SHOTS}/t16-{n}-{w}.png', full_page=True)

    # ---------------- T-17: voice pass, home (voice2.py V1 to V6)
    src = _html.unescape(urlopen(BASE + 'index.html').read().decode('utf-8'))
    V_NEW = {
        'V1': "Hey, I'm Josef. Take a deep breath. AI is a set of power tools, and I already know how to run them. Tell me the job that never gets done, and I'll take it from here.",
        'V2': "For shops and nonprofits around Sonoma County. Maybe it's a phone full of videos you'll never edit. Maybe it's a binder of lessons, or the one chore that eats every Thursday. Hand it over. You get back finished reels, an app with your name on it, or a chore that does itself, and you watch it work before you decide to go ahead.",   # T-19 W2
        'V3 bold': "Nothing goes out until a person has looked at it.",
        'V3 line': "First me, then you.",
        'V4 bold': "You never have to take my word for it.",
        'V4 line': "The checks stay with you, and you can run them again any time.",
        'V5 bold': "The first step is small and the price is fixed.",
        'V5 line': "And if you don't need me, I'll tell you. I sold insurance for years and learned to give the honest answer even when it cost me the sale.",
        'V6 bold': "What's yours stays yours.",
        'V6 line': "Your accounts, your data, and it's in the contract.",
    }
    V_OLD = {
        'V1': "I'm Josef. I build AI tools that take real work off your plate, and I explain every one of them in plain English. Pick the one that sounds like you, and I'll take it from here.",
        'V2': "For small businesses and nonprofits in Sonoma County. Hand me the videos you never get to, the lessons in a binder or the chore that eats your week. I'll turn it into reels, an app with your name on it, or a chore that runs itself, and show you that it works.",
        'V3 bold': "A person checks everything first.",
        'V3 line': "Nothing reaches your customers or your live systems until a real person has looked at it.",
        'V4 bold': "You can check my work without me.",
        'V4 line': "The tests stay with you, so you can rerun them any time you like.",
        'V5 line': "If the honest answer is that you don't need me, that's the answer you get.",
        'V6 line': "Your data stays in your own accounts, and the contract says so.",
    }
    for k, v in V_NEW.items():
        check(f'T-17 {k}: new line on the home page exactly once', src.count(v) == 1, str(src.count(v)))
    for k, v in V_OLD.items():
        check(f'T-17 {k}: old line gone from the home page', v not in src)
    check('T-17: no em dash on the home page', '—' not in src)
    pairs = _re.findall(r'<li[^>]*><strong[^>]*>([^<]*)</strong><span[^>]*>([^<]*)</span></li>', src)
    check('T-17: "How I work" is four items, each a bold line over its second line, in order',
          pairs == [(V_NEW[f'V{i} bold'], V_NEW[f'V{i} line']) for i in (3, 4, 5, 6)], str(pairs))
    for keep in ('AI that works the first day', 'Proof your new system', 'The Blueprint: two weeks, $1,500, fixed. If you go ahead, the $1,500 comes off the price.',   # T-19 W1
                 'The Survey · one group of programs · from $8,000 · counts toward the next step', 'Take the Local Route →',
                 'Take the Mainframe Route →', 'How I work, on either side',
                 'For banks, insurers and agencies moving off COBOL with AI.'):
        check(f'T-17: home keeps "{keep[:40]}"', src.count(keep) == 1)
    for w in (320, 390, 1440):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(400)
        sw = q.evaluate('document.documentElement.scrollWidth')
        check(f'T-17: home has no sideways scroll at {w}', sw <= w, str(sw))
        cards = q.locator('a.route').evaluate_all('e => e.map(a => { const r = a.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.height), a.scrollHeight - a.clientHeight, a.scrollWidth - a.clientWidth] })')
        check(f'T-17: neither route card spills at {w}', len(cards) == 2 and all(c[3] <= 0 and c[4] <= 0 for c in cards), str(cards))
        lis = q.locator('#rules-h + ol > li').evaluate_all('e => e.map(l => { const r = l.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.height), l.scrollWidth - l.clientWidth] })')
        check(f'T-17: four "How I work" items, none spilling sideways, at {w}', len(lis) == 4 and all(l[3] <= 0 for l in lis), str(lis))
        if w == 1440:
            check('T-17: the two route cards sit side by side, same top and height, at 1440',
                  cards[0][1] == cards[1][1] and cards[0][2] == cards[1][2] and cards[0][0] < cards[1][0], str(cards))
            check('T-17: the four "How I work" items sit in one row, same top and height, at 1440',
                  len({l[1] for l in lis}) == 1 and len({l[2] for l in lis}) == 1, str(lis))
            begins = q.locator('a.route').evaluate_all('e => e.map(a => Math.round([...a.querySelectorAll("span")].find(s => s.textContent.trim() === "BEGINS WITH").getBoundingClientRect().y))')
            # The Mainframe card has a 1 px border and the Local card has none, so allow 1 px.
            check('T-17: both "Begins with" lines sit at the same height at 1440 (within the 1 px border)', len(begins) == 2 and abs(begins[0] - begins[1]) <= 1, str(begins))
        else:
            check(f'T-17: route cards stack in one column at {w}', cards[0][0] == cards[1][0] and cards[0][1] < cards[1][1], str(cards))
        q.screenshot(path=f'{SHOTS}/t17-home-{w}.png', full_page=True)
        q.locator('section[aria-label="Routes"]').screenshot(path=f'{SHOTS}/t17-home-routes-{w}.png')
        q.locator('section[aria-labelledby="rules-h"]').screenshot(path=f'{SHOTS}/t17-home-rules-{w}.png')
        q.locator('header:has(h1)').screenshot(path=f'{SHOTS}/t17-home-hero-{w}.png')

    # ---------------- T-18: simple pass, the six tools and the phone header (Nov 13, 2026)
    import subprocess as _sp18
    T17 = 'd0a24616f56f85eb6a252d3a4f98ad2449d1ca04'   # trip/T-17: the pages as they were before this item
    T17_FILES = {}

    def t17_file(path):
        if path not in T17_FILES:
            r = _sp18.run(['git', 'show', f'{T17}:{path}'], cwd=here, capture_output=True)
            T17_FILES[path] = r.stdout if r.returncode == 0 else None
        return T17_FILES[path]

    def old_page(w, h=900):
        """A page that can open the T-17 build at BASE + '__t17/<file>', straight from git."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t17/', 1)[1].split('?')[0].split('#')[0]
            body = t17_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'application/octet-stream')
        q.route('**/__t17/**', serve)
        return q
    OLD = BASE + '__t17/'
    check('T-18: the T-17 pages can be read from git for comparison', t17_file('shotlist.html') is not None and t17_file('comp3.html') is not None)
    TOOLS6 = ('shotlist', 'captions', 'receipt', 'scaler', 'checkup', 'comp3')
    MENU = ('index', 'work', 'call', 'case-reels', 'start', 'shotlist', 'captions', 'receipt', 'scaler', 'checkup',
            'studio', 'studio-birdleague', 'studio-deepcuts')
    # Built on Windows the pages end lines with CRLF and git holds LF, so compare without CR.
    new_src = {n: urlopen(BASE + n + '.html').read().decode('utf-8').replace('\r', '') for n in TOOLS6 + MENU}
    old_src = {n: t17_file(n + '.html').decode('utf-8').replace('\r', '') for n in TOOLS6 + MENU}

    def settle(q):
        q.wait_for_load_state('networkidle'); q.evaluate('document.fonts.ready.then(() => 1)'); q.wait_for_timeout(100)
    U = lambda s: _html.unescape(s)

    # Left as they are: title tags, meta descriptions, share cards, the dark panels and the "More free tools" lines.
    for n in TOOLS6 + ('index',):
        for rx in (r'<title>.*?</title>', r'<meta name="description"[^>]*>', r'<meta property="og:[^"]*"[^>]*>', r'<meta name="twitter:card"[^>]*>'):
            check(f'T-18: {n} keeps its {rx[1:12]}... as at T-17', _re.findall(rx, new_src[n], _re.S) == _re.findall(rx, old_src[n], _re.S))
    for n in TOOLS6[:5]:
        for rx in (r'<p class="noprint"[^>]*>More free tools:.*?</p>', r'<section aria-labelledby="more-h".*?</section>'):
            a, b_ = _re.findall(rx, new_src[n], _re.S), _re.findall(rx, old_src[n], _re.S)
            if n == 'receipt' and 'more-h' in rx:   # T-19 W21 changed the panel's line; the rest stays as at T-17
                b_ = [x.replace('Day 1 of a Blueprint is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the build price.',
                                'The first step is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the price if you go ahead.') for x in b_]
            check(f'T-18: {n} keeps its {"More free tools line" if "More" in rx else "dark panel"} as at T-17', a == b_ and len(a) == 1)

    # The words, exactly once where they are in the page itself, and the old ones gone.
    NEW_LINES = {
        'shotlist': ["Tell me what you run. You get 10 clips to film, in the order you walk your shop.", "What do you run?",
                     "Change the details", "Your 10 clips. Film them in this order.", "Start at the top of the list and film as you go. You never walk back.",   # T-19 W13, W14
                     "How it gets cut together"],
        'captions': ["Type the words that go on your video. See them on a phone, and find out if people can read them before they're gone.", "Change how it looks",   # T-19 W17
                     "Which app?", "How long is your clip?", "Try it on your own video", "Add a screenshot from your video. It stays on your phone.",
                     "Your caption, split up", "Save this caption as an image", "Save all of them", "Copy the text",
                     "This picture is see-through except for your words. Lay it over your video in CapCut or the Instagram editor and the words land right where you see them here."],   # T-19 W19
        'receipt': ["Tap the chores that eat your week. See what a year of them costs you.", "Guess. Close is good enough."],
        'scaler': ["Paste a recipe and say who's eating. You get amounts you can actually measure."],
        'checkup': ["Paste your website's address. You get a plain list of what's broken, worst first, and whether AI tools can find your business."],
        'comp3': ["One stored number. Two ways to read it. On a $1,000 balance, one reading charges $2.92 of interest a month and the other charges $291.67. The code can't tell you which is right. Paste your own below. Nothing you paste leaves this page.",
                  "The line in the program that says how the number is stored. Paste it however it appears: PIC S9(7)V99 COMP-3. works."],
    }
    OLD_LINES = {
        'shotlist': ["Ten clips.", "Tell it four things", "The shoot: one lap, no backtracking",
                     "Film by where you're standing, not by the edit order. Numbers match the edit.",
                     "Pick what you run and what the reel should do.", "'Payoff'", "'Where'", "'Hook'"],
        'captions': ["Type it once.", "Upper third", "Lower third", "Check against", "This clip is on screen for", "Try it on your own frame",
                     "A screenshot from your video. It stays on your device.", "The checkup", ">Screens<", "Download this screen as a PNG",
                     "Download every screen", "Copy the line breaks", "The PNG is see-through", "Two lines fit comfortably", "Fits on one screen. Tap it to preview."],
        'receipt': ["How long, how often", "Change any name to match how you'd say it.", "COULD COME BACK", "Could come back:",
                    "Tap a chore above to start your receipt.", "You get a receipt for a year of them", "tag2"],
        'scaler': ["Paste any ingredient list and say who's eating."],
        'checkup': ["Paste your site's address. You get a plain report"],
        'comp3': ["A free tool · runs in your browser", "Paste the raw bytes of a COMP-3", "Paste the bytes of a COMP-3 field and its picture clause. You get"],
    }
    def visible_text(src):
        return U(_re.sub(r'\s+', ' ', _re.sub(r'<[^>]+>', ' ', _re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=_re.S))))
    for n, lines in NEW_LINES.items():
        page_text = visible_text(new_src[n]) + ' ' + U(new_src[n])   # words in the markup, or in the script that writes them
        flat = U(_re.sub(r'<[^>]+>', '', new_src[n]))
        for s in lines:
            c = flat.count(s) + (flat.count(s.replace("'", "\\'")) if "'" in s else 0)
            check(f'T-18: {n} has "{s[:50]}" exactly once', c == 1, str(c))
    for n, lines in OLD_LINES.items():
        for s in lines:
            check(f'T-18: {n} no longer has "{s[:50]}"', s not in U(new_src[n]) and s.replace("'", "\\'") not in U(new_src[n]))

    # Every page that gains the phone menu, and the folds: at 390, 48 px or taller, closed on load.
    def fold_ok(q, btn, target, label):
        b_ = q.locator(btn)
        t_ = q.locator(target)
        h_ = b_.bounding_box()['height'] if b_.is_visible() else 0
        tag = b_.evaluate('e => e.tagName')
        check(f'T-18: {label}: a real button, closed on load, 48 px or taller at 390', tag == 'BUTTON' and b_.get_attribute('aria-expanded') == 'false'
              and not t_.is_visible() and h_ >= 48 and b_.get_attribute('aria-controls') == t_.get_attribute('id'), f'{tag} {h_}')
        b_.click(); q.wait_for_timeout(60)
        o1 = b_.get_attribute('aria-expanded') == 'true' and t_.is_visible()
        b_.click(); q.wait_for_timeout(60)
        c1 = b_.get_attribute('aria-expanded') == 'false' and not t_.is_visible()
        check(f'T-18: {label}: opens and closes by click, aria-expanded follows', o1 and c1)
        b_.focus(); q.keyboard.press('Enter'); q.wait_for_timeout(60)
        o2 = b_.get_attribute('aria-expanded') == 'true' and t_.is_visible()
        q.keyboard.press('Space'); q.wait_for_timeout(60)
        c2 = b_.get_attribute('aria-expanded') == 'false' and not t_.is_visible()
        check(f'T-18: {label}: opens with Enter and closes with Space from the keyboard', o2 and c2)
        q.keyboard.press('Shift+Tab'); q.keyboard.press('Tab')
        check(f'T-18: {label}: reachable with Tab', q.evaluate('document.activeElement') is not None and b_.evaluate('e => e === document.activeElement'))

    q = newpage(390, 844); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    fold_ok(q, '#f-details', '#details', 'shot list "Change the details"')
    fold_ok(q, '#f-cut', '#cut', 'shot list "How it gets cut together"')
    q = newpage(390, 844); q.goto(BASE + 'captions.html'); q.wait_for_timeout(300)
    fold_ok(q, '#f-look', '#look', 'caption fitter "Change how it looks"')
    q = newpage(390, 844); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    for i in range(3):
        fold_ok(q, f'#rows .row2:nth-child({i + 1}) .fold', f'#rows .row2:nth-child({i + 1}) .ed', f'receipt line {i + 1} "Change"')

    # The answer first: where each tool's answer starts at 390 wide (one phone screen is 844 px).
    ANSWER = {'shotlist': "document.querySelector('section[aria-labelledby=shoot-h]')", 'captions': "document.querySelector('.phone')",
              'receipt': "document.getElementById('paper')", 'scaler': "document.getElementById('out').closest('table')",
              'checkup': "document.getElementById('soon')",
              'comp3': "[...document.querySelectorAll('#out .label')].find(e => e.textContent === 'If this field is an annual rate').parentElement"}
    for n, js in ANSWER.items():
        tops = []
        for base_, pgf in ((BASE, lambda: newpage(390, 844)), (OLD, lambda: old_page(390, 844))):
            q = pgf(); q.goto(base_ + n + '.html'); settle(q)
            tops.append(q.evaluate('(() => Math.round(' + js + '.getBoundingClientRect().top + scrollY))()'))
        check(f'T-18: {n}: the answer starts on the first or second phone screen at 390 (was {tops[1]} px, now {tops[0]} px)',
              tops[0] < 2 * 844 and tops[0] <= tops[1], str(tops))

    # Same choices, same results: three inputs per tool, against the page as it was at T-17.
    def click_chips(q, picks):
        for k, v in picks:
            q.evaluate(f"document.querySelector('.chip[data-k=\"{k}\"][data-v=\"{v}\"]').click()")
    def set_val(q, sel, v):
        q.evaluate("([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})) }", [sel, v])
    def grab_copy(q, btn):
        q.evaluate('window.djCopy = t => { window.__copied = t }')
        q.evaluate(f"document.querySelector('{btn}').click()")
        return q.evaluate('window.__copied')
    def both(name, fn, w=1440):
        out_ = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD, lambda: old_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    SHOT_JS = '''(() => ({
      edit: [...document.querySelectorAll('#edit .clip')].map(c => [c.querySelector('.no').textContent, c.querySelector('.role').className, c.querySelector('.sec').textContent, c.querySelector('p').textContent, (c.querySelector('.cap') || {}).textContent || '']),
      shoot: [...document.querySelectorAll('#shoot .spot')].map(s => [s.querySelector('h3').textContent, [...s.querySelectorAll('li')].map(l => l.textContent)]),
      strip: [...document.querySelectorAll('#strip span')].map(s => [s.className, s.style.flex, s.textContent]), striplabel: document.getElementById('striplabel').textContent,
      rules: [...document.querySelectorAll('#rules li')].map(l => l.textContent),
      days: document.getElementById('days').textContent, dayslabel: document.getElementById('dayslabel').textContent, when: document.getElementById('when').hidden,
      offer: document.getElementById('offer').innerHTML,
      pressed: [...document.querySelectorAll('.chip[aria-pressed=true]')].map(c => c.dataset.k + '=' + c.dataset.v)}))()'''
    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')], [('type', 'nonprofit'), ('len', '45'), ('light', 'mid')]):
        def shot(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT_JS)
            r['copy'] = _re.sub(r'(?m)^(\d+)\. [^(\n]+ \(', r'\1. (', grab_copy(q, '#copy'))   # S8 renames the clip labels
            return r
        a, b_ = both('shotlist', shot)
        check(f'T-18: shot list gives the same clips, seconds, stops, rules, countdown, offer and copy as T-17 for {picks or "the defaults"}', a == b_,
              str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    q.click('#f-cut'); q.wait_for_timeout(60)
    check('T-18 S8: the ten clip labels in the order people see them', q.locator('#edit .role').all_text_contents() ==
          ['Opening', 'Your place', 'Hands', "How it's made", 'Close-up', 'You', 'A customer', 'The best part', 'Your sign', 'The ask'],
          str(q.locator('#edit .role').all_text_contents()))
    qo = old_page(390); qo.goto(OLD + 'shotlist.html'); qo.wait_for_timeout(300)
    st_js = 'e => { const s = getComputedStyle(e); return [e.className, s.fontFamily, s.fontSize, s.textTransform, s.backgroundColor, s.color, s.padding] }'
    check('T-18 S8: the labels keep their styling', q.locator('#edit .role').evaluate_all(f'es => es.map({st_js})') == qo.locator('#edit .role').evaluate_all(f'es => es.map({st_js})'))
    q.click('#f-cut')
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-18: printed, the shot list shows both lists, the edit fold open', q.locator('#cut').is_visible() and q.locator('#edit .clip').count() == 10
          and q.locator('#shoot li').count() == 10 and not q.locator('#f-cut').is_visible())
    q.emulate_media(media='screen')

    CAP_JS = '''(() => { const d = document.getElementById('cv').toDataURL(); let h = 0; for (let i = 0; i < d.length; i++) h = (h * 31 + d.charCodeAt(i)) | 0;
      return {verdicts: [...document.querySelectorAll('#verdicts li')].map(l => [l.querySelector('.dot').className, l.textContent]),
              cards: [...document.querySelectorAll('#cards .cardline')].map(c => c.textContent), canvas: h,
              pressed: [...document.querySelectorAll('.chip[aria-pressed=true]')].map(c => c.dataset.k + '=' + c.dataset.v)} })()'''
    CAP_IN = ((None, [], None), ('New fall sweaters just landed.', [('size', 'l'), ('pos', 'top'), ('app', 'tiktok')], '2'),
              ('Supercalifragilisticexpialidocious bakery opens at nine tomorrow morning on Fourth Street', [('size', 's'), ('box', 'none'), ('app', 'shorts'), ('pos', 'mid')], '20'))
    for text, picks, secs in CAP_IN:
        def cap(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks)
            if secs:
                set_val(q, '#secs', secs)
            q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS)
            r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both('captions', cap)
        check(f'T-18: caption fitter gives the same screens, checks, preview and copy as T-17 for {(text or "the default")[:24]} {picks}', a == b_,
              str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390, 844); q.goto(BASE + 'captions.html'); q.wait_for_timeout(500)
    v = q.locator('#verdict')
    check('T-18 S11: the verdict line has role="status"', v.get_attribute('role') == 'status')
    check('T-18 S11: too long, with today\'s numbers', v.inner_text().strip() == 'Too long for this clip. People need about 7.5 seconds and your clip is 5.', v.inner_text())
    set_val(q, '#secs', '10'); q.wait_for_timeout(100)
    check('T-18 S11: good to go when it fits and there is time', v.inner_text().strip() == 'Good to go. It fits, and people can read it in time.', v.inner_text())
    set_val(q, '#cap', 'Supercalifragilisticexpialidocious'); click_chips(q, [('size', 'l')]); set_val(q, '#secs', '1'); q.wait_for_timeout(300)
    check('T-18 S11: covered comes first, before too long', v.inner_text().strip() == "The app's buttons cover part of it. Move it up."
          and 'cover screen' in q.inner_text('#verdicts'), v.inner_text())
    set_val(q, '#cap', 'New fall sweaters just landed.'); set_val(q, '#secs', '5'); click_chips(q, [('size', 'm')]); q.wait_for_timeout(300)
    before_ = v.inner_text().strip()
    q.locator('#cap').click(); q.keyboard.press('Control+A')
    q.keyboard.type('Fresh sourdough comes out of the oven at 7 every morning. Come early, because the first batch is always gone by 9.'); q.wait_for_timeout(400)
    check('T-18 S11: the line updates as the visitor types', before_.startswith('Good to go.') and v.inner_text().strip().startswith('Too long for this clip.'), before_ + ' / ' + v.inner_text())
    st_ = q.locator('.stage').bounding_box(); vb = v.bounding_box(); fb = q.locator('#f-look').bounding_box(); cb = q.locator('.a-in').bounding_box()
    check('T-18 S11: at 390, the caption box, then the phone, then the verdict, then "Change how it looks"',
          cb['y'] < st_['y'] < vb['y'] < fb['y'] and vb['y'] - (st_['y'] + st_['height']) < 40, f'{cb} {st_} {vb} {fb}')
    check('T-18 S13: where on screen is Top / Middle / Bottom, Bottom chosen as before', q.locator('#c-pos .chip').all_text_contents() == ['Top', 'Middle', 'Bottom']
          and q.locator('#c-pos .chip[aria-pressed=true]').inner_text() == 'Bottom')
    check('T-18 S16: the checkup list is headed "Why" and sits under the verdict and the settings link', q.inner_text('#v-h') == 'Why'
          and q.locator('#v-h').bounding_box()['y'] > fb['y'])
    check('T-18 S17: the note counts the parts', q.inner_text('#k-sub') == 'Two lines fit on a phone, so this caption shows in 3 parts. Tap one to see it.', q.inner_text('#k-sub'))
    set_val(q, '#cap', 'New fall sweaters just landed.'); q.wait_for_timeout(300)
    check('T-18 S17: one part, no note', not q.locator('#k-sub').is_visible() and q.locator('#cards .cardline').count() == 1)
    with q.expect_download() as dl:
        q.click('#png')
    check('T-18 S18: "Save this caption as an image" still saves the PNG', dl.value.suggested_filename == 'caption-1.png', dl.value.suggested_filename)

    def rec_in(presets, rate, edit):
        def rec(q):
            for i in presets:
                q.evaluate(f"document.querySelector('[data-p=\"{i}\"]').click()")
            if rate:
                set_val(q, '#rate', rate)
            if edit:
                set_val(q, '[data-f=min]', '60'); set_val(q, '[data-f=per]', 'week')
                q.evaluate("document.getElementById('addown').click()"); q.wait_for_timeout(60)
                set_val(q, 'input[data-f=name]', 'Renamed chore')
                q.evaluate("document.querySelector('[data-del=\"1\"]').click()")
            q.wait_for_timeout(100)
            paper = q.evaluate("(() => { const c = document.getElementById('paper').cloneNode(true); c.querySelectorAll('.ed, .fold').forEach(e => e.remove()); return c.textContent.replace(/\\s+/g, ' ').trim() })()")
            paper = paper.replace('You could get back', 'BACK').replace('COULD COME BACK', 'BACK')
            return {'paper': paper, 'bring': q.get_attribute('#bring', 'href'),
                    'copy': grab_copy(q, '#copy').replace('You could get back:', 'BACK:').replace('Could come back:', 'BACK:'),
                    'chips': q.evaluate("[...document.querySelectorAll('#presets .chip')].map(c => [c.textContent, c.className, c.getAttribute('aria-disabled')])")}
        return rec
    for args in (([], None, False), ([4, 11], '45', False), ([1, 9], None, True)):
        a, b_ = both('receipt', rec_in(*args))
        check(f'T-18: receipt gives the same lines, totals, hand-off and copy as T-17 for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]) + ' ' + str(a)[:300])
    q = newpage(390, 844); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    y = lambda s: q.locator(s).bounding_box()['y']
    check('T-18 S21/S22: at 390, the chips, then "+ Something else" and the hourly rate, then the receipt',
          y('#presets') < y('#addown') < y('#paper') and y('#rate') < y('#paper'))
    n0 = q.locator('#rows .row2').count()
    q.click('[data-p="4"]')
    check('T-18 S21: the receipt changes the moment a chore is tapped', q.locator('#rows .row2').count() == n0 + 1 and 'Editing videos or photos' in q.inner_text('#paper'))
    check('T-18 S22: "How long, how often" is gone as a block', q.locator('#lines').count() == 0 and 'How long, how often' not in q.inner_text('main'))
    check('T-18 S22: every receipt line has its own "Change"', q.locator('#rows .row2 > .fold').all_text_contents() == ['Change'] * (n0 + 1))
    q.click('#rows .row2:nth-child(1) .fold'); q.wait_for_timeout(60)
    ed = q.locator('#rows .row2:nth-child(1) .ed')
    check('T-18 S22: "Change" opens that chore\'s name, minutes, how often and remove, with "Guess. Close is good enough."',
          ed.locator('input[data-f=name]').input_value() == 'Answering the same questions' and ed.locator('input[data-f=min]').input_value() == '30'
          and ed.locator('select[data-f=per]').input_value() == 'day' and ed.locator('[data-del]').count() == 1
          and ed.locator('p').inner_text() == 'Guess. Close is good enough.')
    check('T-18 S23: the small tag is not repeated in the fields', 'AI drafts it, you approve' not in ed.inner_text()
          and 'AI drafts it, you approve' in q.locator('#rows .row2:nth-child(1) .rs').inner_text())
    ed.locator('input[data-f=min]').fill('60'); q.wait_for_timeout(60)
    check('T-18 S22: changing minutes keeps the field and its focus while the receipt updates', '$7,500' in q.inner_text('#rows .row2:nth-child(1)')
          and ed.locator('input[data-f=min]').evaluate('e => e === document.activeElement'))
    check('T-18: the fields are 48 px or taller at 390', all(h >= 48 for h in ed.locator('input, select, button').evaluate_all('es => es.map(e => e.getBoundingClientRect().height)')))
    q.click('#addown'); q.wait_for_timeout(60)
    last = q.locator('#rows .row2').last
    check('T-18 S22: "+ Something else" opens its own line with its name selected and "What fixes it?" kept',
          last.locator('.ed').is_visible() and last.locator('input[data-f=name]').evaluate('e => e === document.activeElement')
          and last.locator('select[data-f=v]').count() == 1)
    check('T-18 S24: "You could get back" on the receipt', 'You could get back' in q.inner_text('#paper') and 'COULD COME BACK' not in q.inner_text('#paper').upper())
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-18: printed, the receipt has no "Change" and no fields', q.locator('#paper .fold:visible').count() == 0 and q.locator('#paper .ed:visible').count() == 0)
    q.emulate_media(media='screen')

    for k, v_ in (([], None), ([('#kids', '40')], None), ([('#serves', '6'), ('#adults', '10'), ('#kids', '0')], None)):
        def sc(q):
            for s, val in k:
                set_val(q, s, val)
            q.wait_for_timeout(100)
            return [q.inner_text('#fac'), q.inner_text('#facl'), q.inner_text('#warn'), q.inner_text('#out')]
        a, b_ = both('scaler', sc)
        check(f'T-18: scaler gives the same amounts as T-17 for {k or "the defaults"}', a == b_)

    thin = _json.loads(_json.dumps(SAMPLE)); thin['facts']['textLength'] = 120
    for ans in (SAMPLE, thin, {'ok': False, 'error': 'private-name'}):
        res = []
        for base_, pgf in ((BASE, lambda: newpage(1440)), (OLD, lambda: old_page(1440))):
            q = pgf()
            def page_route(route, request=None, base_=base_):   # T-19: Playwright hands a second argument (the request) to a two-argument handler
                body = route.fetch().text() if base_ == BASE else t17_file('checkup.html').decode('utf-8')
                route.fulfill(status=200, content_type='text/html', body=body.replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1))
            q.route(base_ + 'checkup.html', page_route)
            def worker_(a_):
                return lambda route: route.fulfill(status=200 if a_.get('ok') else 400, content_type='application/json',
                                                   body=_json.dumps(a_), headers={'Access-Control-Allow-Origin': '*'})
            q.route('https://dj-checkup.test/**', worker_(ans))
            q.goto(base_ + 'checkup.html'); q.wait_for_timeout(400)
            q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            res.append([q.inner_text('#msg')] + [q.inner_text(s) if q.locator(s).is_visible() else '' for s in ('#rep1', '#stat', '#rep2')])
            if base_ == BASE:   # T-19 W22 to W24 changed three lines of the second card; the rest stays as at T-17
                for new_, old_ in (("It checks whether a computer can find the basic facts about your business on your page.", "It checks whether a machine can read the facts it would need."),
                                   ('What a computer can read off your page', 'The facts a machine reads off your page'),
                                   ("Compare these with your Google listing. They should match exactly.", "Check these against your Google Business Profile, letter for letter.")):
                    res[-1][3] = res[-1][3].replace(new_, old_, 1)
        check(f'T-18: checkup gives the same report as T-17 for {"a refusal" if not ans.get("ok") else "a thin page" if ans is thin else "the sample"}', res[0] == res[1] and any(res[0]))

    def dec(q, steps):
        for s in steps:
            if s[0] == 'chip':
                q.click(f'text={s[1]}')
            elif s[0] == 'mode':
                q.click(s[1])
            else:
                q.fill(s[0], s[1])
        q.wait_for_timeout(100)
        return [sorted(l for l in q.inner_text('#out').split('\n') if l.strip()), _re.sub(r'.*#', '#', q.url)]
    for steps in ([], [('chip', 'A damaged field')], [('chip', 'A negative balance')], [('mode', '#mode-enc'), ('#in', '-12.345'), ('#pic', 'S9(5)V99')]):
        a, b_ = both('comp3', lambda q: dec(q, steps))
        check(f'T-18: decoder shows the same readouts and share link as T-17 for {steps or "the opening example"}', a == b_)
    q = newpage(390, 844); q.goto(BASE + 'comp3.html'); q.wait_for_timeout(300)
    check('T-18 S27: "Free tool" over the title', q.locator('h1').evaluate('e => e.previousElementSibling.textContent') == 'Free tool')
    out_t = q.inner_text('#out')
    check('T-18 S28: the intro\'s figures are what the tool computes on load', '$2.92' in out_t and '$291.67' in out_t
          and q.locator('#out > div').first.inner_text().upper().startswith('IF THIS FIELD IS AN ANNUAL RATE'), out_t[:200])
    order = q.evaluate('''(() => { const k = [...document.querySelectorAll('#out > *')]; const f = p => k.findIndex(p);
      return [f(e => e.classList.contains('ok')), f(e => e.textContent.startsWith('If this field is an annual rate')), f(e => e.tagName === 'DL'), f(e => e.textContent.startsWith('Every half-byte'))] })()''')
    check('T-18 S29: clean message, then the dollar readings and their sentence, then value, digits, sign and length, then the half-byte boxes', order == [0, 1, 2, 3], str(order))
    gap = q.evaluate("document.querySelector('#out > .ok').getBoundingClientRect().top - [...document.querySelectorAll('.chip[data-b]')].pop().getBoundingClientRect().bottom")
    check('T-18 S29: the clean-or-damaged message sits right under the examples at 390', 0 < gap <= 64, str(gap))
    q.click('text=A damaged field'); q.wait_for_timeout(100)
    check('T-18 S29: a damaged field still leads with its warning', q.locator('#out > *').first.evaluate('e => e.className') == 'warn')

    # S1: the phone header.
    def header_links(q):
        return q.evaluate('''(() => { const L = document.querySelector('a[href="work.html#free"]').parentElement;
          return [...L.querySelectorAll('a')].map(a => [a.getAttribute('href'), a.textContent.trim()]) })()''')
    for n in MENU:
        q = old_page(390); q.goto(OLD + n + '.html'); q.wait_for_timeout(200)
        want = header_links(q)
        for w in (320, 390):
            q = newpage(w, 844); q.goto(BASE + n + '.html'); q.wait_for_timeout(300)
            btn = q.locator('.djm-btn')
            links = q.locator('#djm-links')
            logo = q.locator('.djm > a, .djm > span').first.bounding_box()
            bb = btn.bounding_box() if btn.is_visible() else None
            check(f'T-18 S1: {n} at {w}: one row, the site name and "Menu", links closed', bb is not None and btn.inner_text() == 'Menu'
                  and btn.get_attribute('aria-expanded') == 'false' and not links.is_visible() and bb['height'] >= 48
                  and abs((bb['y'] + bb['height'] / 2) - (logo['y'] + logo['height'] / 2)) <= 6 and bb['x'] > logo['x'] + logo['width'], f'{bb} {logo}')
            btn.click(); q.wait_for_timeout(80)
            items = links.locator('a').evaluate_all('es => es.map(a => { const r = a.getBoundingClientRect(); return [a.getAttribute("href"), a.textContent.trim(), Math.round(r.top), r.height] })')
            check(f'T-18 S1: {n} at {w}: "Menu" opens the same links and call button, in the same order, under the header row',
                  btn.get_attribute('aria-expanded') == 'true' and [i[:2] for i in items] == want and all(i[3] >= 48 for i in items)
                  and [i[2] for i in items] == sorted(i[2] for i in items) and items[0][2] >= bb['y'] + bb['height'], f'{items} {want}')
            sw = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-18 S1: {n} at {w}: no sideways scroll with the menu open', sw <= w, str(sw))
            if w == 390 and n in ('index', 'captions'):
                q.screenshot(path=f'{SHOTS}/t18-menu-{n}-390.png')
            btn.click(); q.wait_for_timeout(60)
            check(f'T-18 S1: {n} at {w}: pressing again closes it', btn.get_attribute('aria-expanded') == 'false' and not links.is_visible())
            btn.focus(); q.keyboard.press('Enter'); q.wait_for_timeout(60)
            o = links.is_visible()
            q.keyboard.press('Escape'); q.wait_for_timeout(60)
            check(f'T-18 S1: {n} at {w}: opens from the keyboard, Escape closes it and leaves focus on "Menu"', o and not links.is_visible()
                  and btn.evaluate('e => e === document.activeElement'))
        # 700 px and wider: the header as it was at T-17, to the pixel.
        HJS = '''(() => { const L = document.querySelector('a[href="work.html#free"]').parentElement.parentElement;
          const r = e => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] };
          return [r(L), [...L.querySelectorAll('*')].filter(e => e.getBoundingClientRect().width > 0).map(e => [e.tagName, e.tagName === 'svg' ? '' : e.textContent.trim().slice(0, 30), r(e)]),
                  Math.round(document.querySelector('h1').getBoundingClientRect().top)] })()'''
        for w in (700, 1024, 1440):
            got = []
            for base_, pgf in ((BASE, lambda: newpage(w)), (OLD, lambda: old_page(w))):
                q = pgf(); q.goto(base_ + n + '.html'); settle(q)
                got.append(q.evaluate(HJS))
            check(f'T-18 S1: {n} at {w}: the header matches T-17 (no Menu button, every link where it was)', got[0] == got[1], str(got[0])[:200] + ' | ' + str(got[1])[:200])
    for n in ('local', 'mainframe', 'briefing', 'comp3', '404'):
        src_ = urlopen(BASE + n + '.html').read().decode('utf-8')
        check(f'T-18 S1: {n} keeps its header, no Menu button', 'djm-btn' not in src_)

    # S31: "How I work" on phones; 700 px and up as at T-17.
    LI = 'es => es.map(l => { const r = l.getBoundingClientRect(), s = getComputedStyle(l); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), s.paddingLeft, s.paddingRight, s.borderRightWidth] })'
    for w in (320, 390, 600, 699):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(300)
        lis = q.locator('#rules-h + ol > li').evaluate_all(LI)
        check(f'T-18 S31: at {w}, the four "How I work" items share one left edge, no line at the right', len(lis) == 4 and len({l[0] for l in lis}) == 1
              and all(l[3] == '0px' and l[5] == '0px' for l in lis) and [l[1] for l in lis] == sorted(l[1] for l in lis), str(lis))
        if w in (320, 390):
            q.locator('section[aria-labelledby="rules-h"]').screenshot(path=f'{SHOTS}/t18-home-rules-{w}.png')
    for w in (700, 1024, 1440):
        got = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD, lambda: old_page(w))):
            q = pgf(); q.goto(base_ + 'index.html'); settle(q)
            got.append(q.locator('#rules-h + ol > li').evaluate_all(LI))
        check(f'T-18 S31: at {w}, "How I work" is as it was at T-17', got[0] == got[1], str(got))

    # No sideways scroll at 320 and 390 on every changed page, folds closed and open.
    for n in MENU + ('comp3',):
        for w in (320, 390):
            q = newpage(w); q.goto(BASE + n + '.html'); q.wait_for_timeout(300)
            a = q.evaluate('document.documentElement.scrollWidth')
            q.evaluate("document.querySelectorAll('.fold[aria-expanded=false]').forEach(b => b.click())"); q.wait_for_timeout(100)
            b2 = q.evaluate('document.documentElement.scrollWidth')
            check(f'T-18: {n} has no sideways scroll at {w}, folds closed and open', a <= w and b2 <= w, f'{a} {b2}')

    # ---------------- T-19: harness lines 01, 33 word changes (W1 to W33), Nov 13, 2026
    # Every check here is against the pages as they were at T-18, read straight from git.
    T18 = '5ab14f363bc9ae99bf2a7e110871b097ac01d4e6'   # origin/main after T-18
    T18_FILES = {}

    def t18_file(path):
        if path not in T18_FILES:
            r = _sp18.run(['git', 'show', f'{T18}:{path}'], cwd=here, capture_output=True)
            T18_FILES[path] = r.stdout if r.returncode == 0 else None
        return T18_FILES[path]

    def t18_page(w, h=900):
        """A page that can open the T-18 build at BASE + '__t18/<file>'."""
        q = newpage(w, h)
        def serve(route):
            path = route.request.url.split('/__t18/', 1)[1].split('?')[0].split('#')[0]
            body = t18_file(path)
            if body is None:
                return route.fulfill(status=404, body='')
            route.fulfill(status=200, body=body, content_type='text/html' if path.endswith('.html') else
                          'image/svg+xml' if path.endswith('.svg') else 'image/jpeg' if path.endswith('.jpg') else 'application/octet-stream')
        q.route('**/__t18/**', serve)
        return q
    OLD18 = BASE + '__t18/'
    check('T-19: the T-18 pages can be read from git for comparison', t18_file('index.html') is not None and t18_file('briefing.html') is not None)

    def both18(name, fn, w=1440):
        out_ = []
        for base_, pgf in ((BASE, lambda: newpage(w)), (OLD18, lambda: t18_page(w))):
            q = pgf(); q.goto(base_ + name + '.html'); settle(q); q.wait_for_timeout(300)
            out_.append(fn(q))
        return out_

    # (ID, page, old words, new words, old in the markup, new in the markup); None: the markup is the words.
    W19 = [
        ('W1', 'index', "The Blueprint · $1,500 · two weeks · counts toward the build", "The Blueprint: two weeks, $1,500, fixed. If you go ahead, the $1,500 comes off the price.", None, None),
        ('W2', 'index', "you watch it work before you decide on the build", "you watch it work before you decide to go ahead", None, None),
        ('W3', 'local', "Two weeks · fixed price · the $1,500 comes off your build", "Two weeks · fixed price · the $1,500 comes off the price if you go ahead", None, None),
        ('W4', 'work', "~4 min", "An 81-second reel in about 4 minutes", '<p class="num">~4 min</p>', '<p class="num">An 81-second reel in about 4 minutes</p>'),
        ('W5', 'work', "535 tests", "535 automatic checks", '<p class="num">535 tests</p>', '<p class="num">535 automatic checks</p>'),
        ('W6', 'work', "2 AI translations", "2 AI translations of one bank program", '<p class="num">2 AI translations</p>', '<p class="num">2 AI translations of one bank program</p>'),
        ('W7', 'work', "A competitive birding app I built from zero lines of code. Its first sound screen ran on mock data. Build 49 names birds from a photo or a song, has real players, and sends sightings to eBird in one tap.",
                       "A competitive birding app I built from zero lines of code. It names birds from a photo or a song, has real players, and sends sightings to eBird in one tap.", None, None),
        ('W8', 'start', "Who says yes, and when?", "Who says yes to spending money, and when?", None, None),
        ('W9', 'start', "Good days for Day 1", "Good days for my first visit", '<h2 id="s5">Good days for Day 1</h2>', '<h2 id="s5">Good days for my first visit</h2>'),
        ('W10', 'start', "Start my Blueprint →", "Send my answers →", 'id="bp-send">Start my Blueprint →<', 'id="bp-send">Send my answers →<'),
        ('W11', 'start', "You get the one-page Blueprint agreement and an invoice for $1,500.", "You get a one-page agreement and an invoice for $1,500.", None, None),
        ('W12', 'call', "Tell me what you run and when you're free.", "Fifteen minutes, free. Tell me what you run and when you're free.",
                        '">Tell me what you run and when you\'re free. I\'ll call you', '">Fifteen minutes, free. Tell me what you run and when you\'re free. I\'ll call you'),
        ('W13', 'shotlist', "Your 10 clips, in walking order", "Your 10 clips. Film them in this order.", None, None),
        ('W14', 'shotlist', "Start at stop 1 and film as you go. You never walk back.", "Start at the top of the list and film as you go. You never walk back.", None, None),
        ('W15', 'shotlist', "Seconds are what each clip gets in the finished reel. Film every one for about five seconds anyway; the edit trims.",
                            "Film each one for about five seconds. The number beside it is how long it stays in the finished video.", None, None),
        ('W16', 'captions', "Will your caption survive the phone?", "Can people read the words on your video?", "Will your caption<br>survive the phone?", "Can people read the words on your video?"),
        ('W17', 'captions', "Type your caption. See it on a phone, and find out if people can read it in time.",
                            "Type the words that go on your video. See them on a phone, and find out if people can read them before they're gone.", None, None),
        ('W18', 'captions', "Box", "Box behind the words", 'id="l-box">Box</p>', 'id="l-box">Box behind the words</p>'),
        ('W19', 'captions', "The image is clear except for the caption. Drop it over your clip in CapCut or the Instagram editor and it lands right where you see it here.",
                            "This picture is see-through except for your words. Lay it over your video in CapCut or the Instagram editor and the words land right where you see them here.", None, None),
        ('W20', 'receipt', 'The "can come back" numbers are a rough rule of thumb for each kind of chore, not a promise. Day 1 of a Blueprint is where the real numbers come from.',
                           "The hours you could get back are a rough rule of thumb for each kind of chore, not a promise. The real numbers come from me watching how the work actually gets done.", None, None),
        ('W21', 'receipt', "Day 1 of a Blueprint is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the build price.",
                           "The first step is me watching how the work actually gets done. Two weeks, $1,500, and it comes off the price if you go ahead.", None, None),
        ('W22', 'checkup', "This doesn't tell you what ChatGPT says about you. It checks whether a machine can read the facts it would need.",
                           "This doesn't tell you what ChatGPT says about you. It checks whether a computer can find the basic facts about your business on your page.", None, None),
        ('W23', 'checkup', "The facts a machine reads off your page", "What a computer can read off your page", None, None),
        ('W24', 'checkup', "Check these against your Google Business Profile, letter for letter. I can't see your listing from here.",
                           "Compare these with your Google listing. They should match exactly. I can't see your listing from here.", None, None),
        ('W25', 'case-reels', "and the tool puts together a finished vertical reel with the program's own title art.",
                              "and the tool puts together a finished reel, upright for phones, with the program's own title card.", None, None),
        ('W26', 'studio', "Built in the open", "Follow along while I piece it together", "Built in<br>the open", "Follow along<br>while I piece it together"),
        ('W27', 'studio', "Everything I'm building right now, and the date each piece shipped.", "Everything I'm building right now, and the date each piece was finished.",
                          ">Everything I'm building right now, and the date each piece shipped.</p>", ">Everything I'm building right now, and the date each piece was finished.</p>"),
        ('W28', 'studio', "things shipped since", "things finished since", None, None),
        ('W29', 'mainframe', "The code never divides by 100. The field definition allows two readings. Pick one:",
                             "The code never divides by 100. The field definition allows two readings. See each one:", None, None),
        ('W30', 'mainframe', "Every record tells a different story. The real data settles it.",
                             "The code, the layouts, the job setup and the data each tell a different story. The real data settles it.",
                             "Every record tells a different story. <em", "The code, the layouts, the job setup and the data each tell a different story. <em"),
        ('W31', 'mainframe', "Send one program and see what I find", "Tell me about one program and see what I'd look at first",
                             '>Send one program <em style="color: #A93F17">and see what I find</em>', '>Tell me about one program <em style="color: #A93F17">and see what I\'d look at first</em>'),
        ('W32', 'briefing', "Request a briefing", "Ask me about your system",
                            '>Request a <em style="color:#A93F17">briefing</em></h1>', '>Ask me about your <em style="color:#A93F17">system</em></h1>'),
        ('W33', 'briefing', "Which programs", "Which programs (a rough description is enough)",
                            '<span class="label">Which programs</span>', '<span class="label">Which programs (a rough description is enough)</span>'),
    ]
    # Words set again by script: the start button's label after a send that didn't go through.
    W19_SCRIPT = [('W10 script', 'start', None, None, "btn.textContent = 'Start my Blueprint →';", "btn.textContent = 'Send my answers →';")]
    check('T-19: 33 lines', len(W19) == 33 and [w[0] for w in W19] == [f'W{i}' for i in range(1, 34)])

    def words19(src):
        """What a visitor reads: the body, scripts and styles out, a line break read as a space."""
        b_ = src[src.index('<body'):]
        b_ = _re.sub(r'<(script|style)\b.*?</\1>', ' ', b_, flags=_re.S)
        b_ = _re.sub(r'<br\s*/?>', ' ', b_)
        return _re.sub(r'\s+', ' ', U(_re.sub(r'<[^>]+>', '', b_)))
    P19 = ['index', 'local', 'work', 'start', 'call', 'shotlist', 'captions', 'receipt', 'checkup', 'case-reels', 'studio', 'mainframe', 'briefing']
    check('T-19: the 13 pages named in the item', sorted(P19) == sorted({w[1] for w in W19}))
    src19 = {n: urlopen(BASE + n + '.html').read().decode('utf-8').replace('\r', '') for n in P19}
    for wid, n, old, new, _o, _n in W19:
        t = words19(src19[n])
        check(f'T-19 {wid}: {n} has the new line exactly once', t.count(new) == 1, str(t.count(new)))
        if old in new:
            check(f'T-19 {wid}: on {n} the old words are only inside the new line', t.count(old) == 1, str(t.count(old)))
        else:
            check(f'T-19 {wid}: the old line is gone from {n}', t.count(old) == 0, str(t.count(old)))
    check('T-19 W10: the script puts back the new label after a send that fails', "btn.textContent = 'Send my answers →';" in src19['start']
          and 'Start my Blueprint' not in src19['start'])
    for n in P19:
        check(f'T-19: no em dash on {n}', '—' not in src19[n])

    # Nothing else changed: the T-18 page with only these lines swapped is the new page, byte for byte
    # (the Studio build stamp aside: it is a hash of studio.json, which holds W26 and W27).
    STAMP = lambda s: _re.sub(r'<!-- studio\.py [^>]* -->', '<!-- studio.py -->', s)
    for n in P19:
        was = t18_file(n + '.html').decode('utf-8').replace('\r', '')
        miss = []
        for wid, n_, old, new, o_raw, n_raw in W19 + W19_SCRIPT:
            if n_ != n:
                continue
            o, nw = o_raw or old, n_raw or new
            if was.count(o) != 1:
                miss.append(f'{wid}: {was.count(o)} matches')
                continue
            was = was.replace(o, nw)
        a, b_ = STAMP(was), STAMP(src19[n])
        i = next((k for k in range(min(len(a), len(b_))) if a[k] != b_[k]), min(len(a), len(b_)))
        check(f'T-19: {n} differs from T-18 only by its lines in this item', not miss and a == b_, str(miss) + ' first difference: ' + repr(b_[max(0, i - 60):i + 60]))
    for f in ('scaler.html', 'comp3.html', '404.html', 'studio-birdleague.html', 'studio-deepcuts.html', 'sitemap.xml', 'robots.txt'):
        now_ = urlopen(BASE + f).read().decode('utf-8').replace('\r', '')
        check(f'T-19: {f} is as it was at T-18 (the Studio build stamp aside)', STAMP(now_) == STAMP(t18_file(f).decode('utf-8').replace('\r', '')))

    # Accessible names follow the new words; names that point at the old ones are gone.
    q = newpage(1440); q.goto(BASE + 'start.html'); q.wait_for_timeout(300)
    check('T-19 W8: step 4 is named by its new heading', q.get_by_role('region', name='Who says yes to spending money, and when?', exact=True).count() == 1)
    check('T-19 W9: the day choices are named by the new heading', q.get_by_role('group', name='Good days for my first visit', exact=True).count() == 1)
    check('T-19 W10: the send button is named "Send my answers →"', q.get_by_role('button', name='Send my answers →', exact=True).count() == 1)
    q.route('**/dj-intake.stephens-josef.workers.dev/**', lambda r: r.fulfill(status=502, content_type='application/json', body='{"ok":false}', headers={'Access-Control-Allow-Origin': '*'}))
    q.locator('.chips[data-key="pile"] .chip').first.click()
    q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com')
    q.click('#bp-send'); q.wait_for_timeout(600)
    check('T-19 W10: after a send that fails, the button says "Send my answers →" again', q.inner_text('#bp-send').strip() == 'Send my answers →'
          and q.locator('#bp-err').is_visible(), q.inner_text('#bp-send'))
    q = newpage(1440); q.goto(BASE + 'captions.html'); q.wait_for_timeout(300)
    check('T-19 W18: the box choices are named "Box behind the words", with the same three choices',
          q.get_by_role('group', name='Box behind the words', exact=True, include_hidden=True).count() == 1
          and q.locator('#c-box .chip').all_text_contents() == ['Dark box', 'Light box', 'No box'])
    q = newpage(1440); q.goto(BASE + 'briefing.html'); q.wait_for_timeout(300)
    check('T-19 W33: the programs field is named by its new label', q.get_by_role('textbox', name='Which programs (a rough description is enough)', exact=True).evaluate('e => e.id') == 'family')
    check('T-19 W33: "Which programs" still finds the same field', q.get_by_label('Which programs').evaluate('e => e.id') == 'family')
    check('T-19 W32: the briefing form\'s own send button is untouched', q.inner_text('#br-send').strip() == 'Send the request →')

    # Every form still sends exactly what it sent at T-18 (the Worker intercepted, nothing leaves).
    def sent18(base_, name, fill, btn, done):
        q = newpage(1440) if base_ == BASE else t18_page(1440)
        got = []
        def grab(route):
            if route.request.method == 'POST':
                got.append(_json.loads(route.request.post_data or '{}'))
            route.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'})
        q.route('**/dj-intake.stephens-josef.workers.dev/**', grab)
        q.goto(base_ + name + '.html'); settle(q)
        fill(q); q.click(btn); q.wait_for_timeout(700)
        for g in got:
            g.pop('ms', None)
        return got, q.locator(done).is_visible()
    def fill_start(q):
        q.locator('.chips[data-key="pile"] .chip').nth(1).click()
        q.locator('.chips[data-key="days"] .chip').first.click()
        q.fill('#org', 'Test Bakery'); q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com')
    def fill_call(q):
        q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com'); q.fill('#org', 'Test Bakery')
    def fill_brief(q):
        q.fill('#name', 'Test Person'); q.fill('#email', 'test@example.com'); q.fill('#family', 'Month-end batch'); q.fill('#role', 'Lead')
    for name, fill, btn, done in (('start', fill_start, '#bp-send', '#bp-done'), ('call', fill_call, '#cl-send', '#cl-done'), ('briefing', fill_brief, '#br-send', '#br-done')):
        a, b_ = sent18(BASE, name, fill, btn, done), sent18(OLD18, name, fill, btn, done)
        check(f'T-19: {name} still sends, and sends exactly what it sent at T-18', a == b_ and len(a[0]) == 1 and a[1], str(a)[:300] + ' | ' + str(b_)[:300])

    # Same input, same result, against T-18: two inputs per changed tool.
    for picks in ([], [('type', 'cafe'), ('goal', 'how'), ('len', '15'), ('light', 'pm')]):
        def shot18(q):
            click_chips(q, picks); q.wait_for_timeout(80)
            r = q.evaluate(SHOT_JS); r['copy'] = grab_copy(q, '#copy')
            return r
        a, b_ = both18('shotlist', shot18)
        check(f'T-19: shot list gives the same clips, stops, countdown, offer and copy as T-18 for {picks or "the defaults"}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    q = newpage(390); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    cp = grab_copy(q, '#copy')
    check('T-19 W13 to W15: the copied shot list repeats none of the old lines', not any(w[2] in cp for w in W19 if w[1] == 'shotlist'))
    q.emulate_media(media='print'); q.wait_for_timeout(60)
    check('T-19 W13 to W15: printed, the shot list shows the new lines', all(q.get_by_text(w[3], exact=True).is_visible() for w in W19 if w[1] == 'shotlist'))
    q.emulate_media(media='screen')
    for text, picks, secs in CAP_IN[:2]:
        def cap18(q):
            if text is not None:
                set_val(q, '#cap', text)
            click_chips(q, picks)
            if secs:
                set_val(q, '#secs', secs)
            q.wait_for_timeout(400)
            r = q.evaluate(CAP_JS); r['copy'] = grab_copy(q, '#copy'); r['verdict'] = q.inner_text('#verdict')
            return r
        a, b_ = both18('captions', cap18)
        check(f'T-19: caption fitter gives the same verdict, checks, preview and copy as T-18 for {(text or "the default")[:24]} {picks}', a == b_, str([k for k in a if a[k] != b_.get(k)]))
    for args in (([], None, False), ([4, 11], '45', False)):
        a, b_ = both18('receipt', rec_in(*args))
        check(f'T-19: receipt gives the same lines, totals, hand-off and copy as T-18 for {args}', a == b_, str([k for k in a if a[k] != b_.get(k)]))

    def checkup_live(q, base_):
        def page_route(route, request=None, base_=base_):   # T-19: Playwright hands a second argument (the request) to a two-argument handler
            body = route.fetch().text() if base_ == BASE else t18_file('checkup.html').decode('utf-8')
            route.fulfill(status=200, content_type='text/html', body=body.replace("var CHECKUP_URL = '';", "var CHECKUP_URL = 'https://dj-checkup.test/';", 1))
        q.route(base_ + 'checkup.html', page_route)
    W22_24 = [(w[3], w[2]) for w in W19 if w[0] in ('W22', 'W23', 'W24')]
    for ans in (SAMPLE, thin):
        res = []
        for base_, pgf in ((BASE, lambda: newpage(1440)), (OLD18, lambda: t18_page(1440))):
            q = pgf(); checkup_live(q, base_)
            q.route('https://dj-checkup.test/**', worker_(ans))
            q.goto(base_ + 'checkup.html'); q.wait_for_timeout(400)
            q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            r2 = q.inner_text('#rep2')
            if base_ == BASE:
                for new, old in W22_24:   # the three lines of this item read back as they were; everything else must match
                    r2 = r2.replace(new, old, 1)
            res.append([q.inner_text('#msg'), q.inner_text('#rep1'), q.inner_text('#stat'), r2])
        check(f'T-19: checkup gives the same report as T-18 for {"a thin page" if ans is thin else "the sample"}, only the three lines changed', res[0] == res[1] and any(res[0]))

    # The look: each new line sits inside its own box at 320, 390 and 1440, nothing spills, no sideways scroll.
    # (Titles and labels set in capitals read back in capitals, so the match ignores case. W11 is in the
    # panel that shows after a send, so the start form is sent, to an intercepted Worker, before W11.)
    FIT_JS = '''(line) => {
      const norm = s => s.replace(/\\s+/g, ' ').trim();
      const els = [...document.querySelectorAll('body *')].filter(e => {
        const d = getComputedStyle(e).display; const r = e.getBoundingClientRect();
        return d !== 'inline' && d !== 'contents' && r.width > 0 && r.height > 0 && norm(e.innerText || '').toLowerCase().includes(line.toLowerCase()); });
      if (!els.length) return null;
      els.sort((a, b) => a.innerText.length - b.innerText.length);
      const e = els[0], r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
      const kids = [...e.querySelectorAll('*')].map(k => k.getBoundingClientRect()).filter(k => k.width > 0);
      return {spill: e.scrollWidth - e.clientWidth, inParent: r.left >= p.left - 1 && r.right <= p.right + 1,
              kidsIn: kids.every(k => k.left >= r.left - 1 && k.right <= r.right + 1), w: Math.round(r.width), h: Math.round(r.height)};
    }'''
    for n in P19:
        for w in (320, 390, 1440):
            q = newpage(w)
            if n == 'checkup':
                checkup_live(q, BASE)
                q.route('https://dj-checkup.test/**', lambda route: route.fulfill(status=200, content_type='application/json', body=_json.dumps(SAMPLE), headers={'Access-Control-Allow-Origin': '*'}))
            if n == 'start':
                q.route('**/dj-intake.stephens-josef.workers.dev/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{"ok":true}', headers={'Access-Control-Allow-Origin': '*'}))
            q.goto(BASE + n + '.html'); settle(q)
            if n == 'checkup':
                q.fill('#site', 'crumb.example'); q.click('#go'); q.wait_for_timeout(700)
            q.evaluate("document.querySelectorAll('.fold[aria-expanded=false]').forEach(b => b.click())"); q.wait_for_timeout(150)
            for wid, n_, old, new, _o, _n in W19:
                if n_ != n:
                    continue
                if wid == 'W11':
                    fill_start(q); q.click('#bp-send'); q.wait_for_timeout(700)
                f_ = q.evaluate(FIT_JS, new)
                check(f'T-19 {wid}: on {n} at {w} the new line sits inside its box', f_ is not None and f_['spill'] <= 0 and f_['inParent'] and f_['kidsIn'], str(f_))
            if w < 1440:
                sw = q.evaluate('document.documentElement.scrollWidth')
                check(f'T-19: {n} has no sideways scroll at {w}', sw <= w, str(sw))

    check('no page errors', not errors, '; '.join(errors[:3]))
    b.close()

print(f'{len(ok)}/{len(ok) + len(bad)} passed')
for x in bad:
    print('FAIL', x)
