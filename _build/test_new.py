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
    check('quiz hands off to start page', 'start.html#' in pg2.url, pg2.url)
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
              'scaler', 'start', 'call', 'case-reels', 'briefing')
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

    check('no page errors', not errors, '; '.join(errors[:3]))
    b.close()

print(f'{len(ok)}/{len(ok) + len(bad)} passed')
for x in bad:
    print('FAIL', x)
