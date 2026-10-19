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
    check('reels receipt has 6 source buttons', btns.count() == 6, str(btns.count()))
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
    check('back to reels, 6 buttons', pg.locator('#rc-rows .src-btn').count() == 6)

    pg.locator('#tl').scroll_into_view_if_needed(); pg.wait_for_timeout(1400)
    check('timeline animates on', 'on' in (pg.get_attribute('#tl', 'class') or ''))
    widths = pg.evaluate("Array.from(document.querySelectorAll('.tl-bar')).map(e => e.getBoundingClientRect().width / e.parentElement.getBoundingClientRect().width)")
    check('timeline bars to scale', abs(widths[0] - 1) < 0.02 and abs(widths[1] - 0.631) < 0.02 and abs(widths[2] - 0.063) < 0.02, str(widths))

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
    pg2.click('#iq-send'); pg2.wait_for_timeout(200)
    url = pg2.get_attribute('#iq-send', 'data-mailto') or ''
    from urllib.parse import unquote
    check('mailto built', url.startswith('mailto:stephens.josef@gmail.com?subject=Blueprint%20question%3A%20Test%20Kitchen'), url[:120])
    check('mailto body has answers', 'Lessons, recipes or a curriculum' in unquote(url) and 'A board or committee' in unquote(url), unquote(url)[:300])

    check('drop-in section present', pg.locator('#dropin').count() == 1)
    check('contact links to drop-in', pg.locator('#contact a[href="#dropin"]').count() == 1)
    check('no bracket placeholders visible', '[' not in pg.inner_text('body').replace('[n]', '').replace('[MONTH]', ''), '')
    for w in (390, 768, 1440):
        q = newpage(w); q.goto(BASE + 'local.html'); q.wait_for_timeout(500)
        q.click('button[data-pick="flow"]'); q.wait_for_timeout(100)
        check(f'local no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        q.locator('#proof').screenshot(path=f'{SHOTS}/proof-{w}.png')
        q.locator('section[aria-labelledby="start"]').screenshot(path=f'{SHOTS}/start-{w}.png')
        q.locator('#dropin').screenshot(path=f'{SHOTS}/dropin-{w}.png')
        q.locator('#josef').screenshot(path=f'{SHOTS}/josef-{w}.png')

    # ---------------- mainframe
    for w in (390, 1440):
        q = newpage(w); q.goto(BASE + 'mainframe.html'); q.wait_for_timeout(500)
        check(f'mainframe no overflow at {w}', q.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0)
        check(f'mainframe decoder links at {w}', q.locator('a[href="comp3.html"]').count() == 2)
        check(f'mainframe no placeholders at {w}', '[' not in q.inner_text('#s7'))
        q.locator('#s7').screenshot(path=f'{SHOTS}/mf-s7-{w}.png')

    check('no page errors', not errors, '; '.join(errors[:3]))
    b.close()

print(f'{len(ok)}/{len(ok) + len(bad)} passed')
for x in bad:
    print('FAIL', x)
