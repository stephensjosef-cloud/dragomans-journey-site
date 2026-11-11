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
    check('work has 9 cards', pg.locator('#cards .card').count() == 9)
    pg.click('.filt[data-f="banking"]'); pg.wait_for_timeout(100)
    check('banking filter shows 2', pg.locator('#cards .card:visible').count() == 2, str(pg.locator('#cards .card:visible').count()))
    pg.click('.filt[data-f="nonprofit"]'); pg.wait_for_timeout(100)
    check('nonprofit filter shows 3 (two jobs + the recipe scaler)', pg.locator('#cards .card:visible').count() == 3)
    pg.click('.filt[data-f="free"]'); pg.wait_for_timeout(100)
    check('free tools filter shows 5', pg.locator('#cards .card:visible').count() == 5)
    q = newpage(1440); q.goto(BASE + 'work.html#free'); q.wait_for_timeout(300)
    check('work.html#free opens on free tools', q.locator('#cards .card:visible').count() == 5)
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
        for t in ('shotlist', 'captions', 'receipt', 'scaler'):
            q = newpage(w); q.goto(BASE + t + '.html'); q.wait_for_timeout(500)
            check(f'{t} no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
            q.screenshot(path=f'{SHOTS}/{t}-{w}.png', full_page=True)
    q = newpage(1440); q.goto(BASE + 'shotlist.html'); q.wait_for_timeout(300)
    check('shot list has 10 clips', q.locator('#edit .clip').count() == 10)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 30', abs(secs - 30) < 0.01, str(secs))
    q.click('.chip[data-v="15"]'); q.wait_for_timeout(100)
    secs = q.eval_on_selector_all('#edit .sec', 'e => e.reduce((a, x) => a + parseFloat(x.textContent), 0)')
    check('shot list seconds add up to 15', abs(secs - 15) < 0.01, str(secs))
    check('shoot order covers all 10 clips', q.locator('#shoot li').count() == 10)
    q = newpage(1440); q.goto(BASE + 'captions.html'); q.wait_for_timeout(400)
    check('captions split into screens', q.locator('#cards .cardline').count() >= 2)
    q.fill('#cap', 'New fall sweaters just landed.'); q.wait_for_timeout(300)
    check('short caption is one screen', q.locator('#cards .cardline').count() == 1)
    q = newpage(1440); q.goto(BASE + 'receipt.html'); q.wait_for_timeout(300)
    check('receipt starts with 3 lines', q.locator('#lines .line').count() == 3)
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
              'scaler', 'start', 'call', 'case-reels', 'briefing', 'studio')
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
             'receipt.html': 'Busywork receipt', 'scaler.html': 'Recipe scaler'}
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        # The header nav: <nav> where the page has one, else its <header>, else the home page's letterhead bar.
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="work\.html#free"[^>]*>([^<]*)</a>', top)
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
    check('local free tools section links the 4 tools', sorted(_re.findall(r'href="([a-z]+\.html)"', sec)) == sorted(TOOLS), sec[:200])
    work = urlopen(BASE + 'work.html').read().decode('utf-8')
    for href, title in TOOLS.items():
        para = _re.search(r'<h2>' + title + r'</h2>\s*<p>([^<]*)</p>\s*<a class="go" href="' + href, work)
        check(f'local card for {href} matches the work page', bool(para) and f'>{title}</h3>' in sec and f'>{para.group(1)}</p>' in sec)
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(300)
        xs = q.eval_on_selector_all('#tools article', 'e => e.map(a => Math.round(a.getBoundingClientRect().left))')
        check(f'local free tools: {"one column" if w == 390 else "one row of four"} at {w}',
              len(xs) == 4 and (len(set(xs)) == 1 if w == 390 else len(set(xs)) == 4), str(xs))
    for href in TOOLS:
        q = newpage(1440); q.goto(BASE + href); q.wait_for_timeout(300)
        line = q.locator('main > p', has_text='More free tools:')
        got = line.locator('a').evaluate_all('e => e.map(a => [a.getAttribute("href"), a.textContent])') if line.count() == 1 else []
        check(f'{href} links the other three tools by name', sorted(got) == sorted([k, v] for k, v in TOOLS.items() if k != href), str(got))
        if line.count() == 1:
            check(f'{href} more-tools line sits above the dark panel',
                  line.bounding_box()['y'] < q.locator('#more-h').bounding_box()['y'])
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
    M = sum(1 for e in rows if _dt.date.fromisoformat(e['date']) > today - _dt.timedelta(days=30))
    K = len({e['project'] for e in rows})
    oldest = min(_dt.date.fromisoformat(e['date']) for e in rows)

    q = newpage(1440); q.goto(BASE + 'studio.html'); q.wait_for_timeout(400)
    stats = [s.strip() for s in q.locator('#stats p').all_inner_texts()]
    stats = [_re.sub(r'\s+', ' ', s) for s in stats]
    check('studio strip matches shipped.json', stats == [f'{N} things shipped since {short(oldest, today)}', f'{M} in the last 30 days', f'{K} projects'], str(stats))
    check('studio shows the hero from studio.json', q.inner_text('h1').replace('\n', ' ').upper() == _re.sub(r'<br\s*/?>', ' ', STUDIO_J['hero']['h1']).upper()
          and q.locator('header .kick').inner_text().upper() == STUDIO_J['hero']['kicker'].upper())
    # The hero names the album only while the album card shows (fix approved Nov 11, 2026).
    HIDDEN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools and shirts, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    SHOWN_LEDE = "Everything I'm building right now, and the date each piece shipped. Apps, free tools, shirts and an album, made with AI and a lot of real-phone testing. Get on a list and you hear first."
    album_hidden = any(x['id'] == 'album' for x in gated_p)
    hero_p = q.locator('header p').last.inner_text().strip()
    check('studio hero names the album only when its card shows', hero_p == (HIDDEN_LEDE if album_hidden else SHOWN_LEDE), hero_p)
    check('studio meta description matches the hero', _html.unescape(_re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) == hero_p)
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
            check(f'album {state}: hero reads as approved', hero_txt == want_lede, (r.stderr or hero_txt)[-200:])
            check(f'album {state}: meta description matches', bool(meta) and _html.unescape(meta.group(1)) == want_lede)
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
        check(f'studio card {x["id"]}: name, status, kind and what from the JSON',
              card.locator('h2').inner_text().upper() == x['name'].upper() and card.locator('.pill').inner_text() == x['status']
              and card.locator('.kind').inner_text().upper() == x['kind'].upper() and x['what'] in txt)
        if x.get('proof'):
            check(f'studio card {x["id"]}: proof line in bold', card.locator('strong', has_text=x['proof']).count() == 1)
        if x.get('image'):
            check(f'studio card {x["id"]}: image', card.locator(f'img[src="{x["image"]}"]').get_attribute('alt') == x['image_alt'])
        if x.get('link'):
            lk = card.locator(f'a[href="{x["link"]["href"]}"]')
            check(f'studio card {x["id"]}: link', lk.count() == 1 and lk.inner_text().startswith(x['link']['label']))
        if x.get('list'):
            jb = card.locator('a[data-list]')
            href = jb.get_attribute('href') if jb.count() == 1 else ''
            check(f'studio card {x["id"]}: join button mails "List: {x["name"]}"',
                  jb.count() == 1 and jb.inner_text() == x['list']['button'] and href.startswith('mailto:hello@dragomansjourney.com?subject=')
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

    # Home band: the newest 3 lines and the way in.
    src = urlopen(BASE + 'index.html').read().decode('utf-8')
    band = _re.search(r'<section id="shipped".*?</section>', src, _re.S)
    band = band.group(0) if band else ''
    check('home band sits between the hero and the routes', bool(band) and src.index('<!-- hero -->') < src.index(band) < src.index('<!-- the two routes -->'))
    lines = [_html.unescape(x) for x in _re.findall(r'<span style="flex-basis: 100%[^"]*">([^<]*)</span>', band)]
    check('home band shows the newest 3 log lines', lines == [e['line'] for e in rows[:3]], str(lines))
    check('home band dates and labels', _re.findall(r'<time datetime="([^"]+)"', band) == [e['date'] for e in rows[:3]]
          and [_html.unescape(x) for x in _re.findall(r'padding: 2px 8px[^"]*">([^<]*)</span>', band)] == [label_of[e['project']] for e in rows[:3]])
    check('home band links to the studio', '<a href="studio.html"' in band and "See everything I'm building →" in _html.unescape(band))
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'index.html'); q.wait_for_timeout(300)
        check(f'home no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.locator('#shipped').screenshot(path=f'{SHOTS}/t08-home-band-{w}.png')

    # Studio in every header, before Free tools.
    for name in SHARED:
        src = urlopen(BASE + name + '.html').read().decode('utf-8')
        top = (_re.search(r'<nav aria-label="Main".*?</nav>', src, _re.S) or _re.search(r'<!-- letterhead -->.*?<!-- hero -->', src, _re.S)
               or _re.search(r'<header.*?</header>', src, _re.S))
        top = top.group(0) if top else ''
        links = _re.findall(r'<a href="studio\.html"[^>]*>([^<]*)</a>', top)
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
            check(f'studio card {x["id"]} links "See it move →" to its page',
                  mv.count() == 1 and mv.inner_text().strip() == 'See it move →' and mv.get_attribute('href') == f'studio-{x["id"]}.html')
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
        check(f'{slug}: kicker links back to the studio', hd.locator('.kick a[href="studio.html"]').count() == 1
              and x['kind'].upper() in hd.locator('.kick').inner_text().upper())
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
        jb = q.locator('#join a[data-list]')
        href = jb.get_attribute('href') if jb.count() == 1 else ''
        check(f'{slug}: one join box, mailing "List: {x["name"]}"', q.locator('#join').count() == 1 and q.locator('a[data-list]').count() == 1
              and jb.inner_text() == x['list']['button'] and href.startswith('mailto:hello@dragomansjourney.com?subject=')
              and _unquote(href.split('subject=', 1)[1]) == 'List: ' + x['name'], href)
        check(f'{slug}: the line under the join box', q.locator('#join p').inner_text().strip() == "One email when it's out. No newsletter.")
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

    check('no page errors', not errors, '; '.join(errors[:3]))
    b.close()

print(f'{len(ok)}/{len(ok) + len(bad)} passed')
for x in bad:
    print('FAIL', x)
