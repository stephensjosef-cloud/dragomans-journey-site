"""The chart style (T-32, Nov 19, 2026), step 6c: python3 theme.py out out-themed

Runs last, after final.py. It reads every finished page in out/ and writes a themed copy of the whole folder to
out-themed/; out/ is left exactly as it is, so the older checks keep testing what they always tested. The repo root
is copied from out-themed/.

What it changes, and nothing else (no word, link, image or structured data moves):
1. Colors. Every color in a style attribute, a <style> element, an SVG paint attribute, and the style strings the
   pages' scripts apply on a tap, is rewritten by its role: the property it sits in (background, text, line) and the
   zone it sits on (light, an accent fill, or something that stays dark: the footer, the closing call box, pills and
   dark buttons). Dark bands go light (chart). The canvas paint in the caption tool is the picture of a visitor's reel,
   not the page, so it is left alone. A color this file doesn't know stops the build and names it.
2. Type. 'Big Shoulders Display' becomes 'Barlow Semi Condensed', 'Instrument Sans' becomes 'Barlow', and
   text-transform: uppercase becomes none, so headings read in sentence case.
3. The ring: one hand-drawn ellipse around each page's one next step (RINGS below).
4. The route: a dashed line, 3px, 10 on and 8 off, along each ordered list of steps (ROUTE_CSS below).
5. The pen underline (T-34, Nov 20, 2026): a hand-drawn line under the few words a headline marks (class="pen" in
   the sources), in place of the italic switch Josef found "tacky" (PEN below).

The accent is today's orange (Josef, Nov 19, 2026, after Stephanie found DESIGN.md's magenta "too Barney"). The
Mainframe pages (MF) use blue in its place.
"""
import os, re, shutil, sys

MF = {'mainframe.html', 'comp3.html', 'briefing.html'}

# ---------------------------------------------------------------- the palette
INK, INK2, MUTED = '#17212B', '#2E3A47', '#4F5A63'
CHART, CARD, TINT = '#E4ECD8', '#F7F9F3', '#EDF2E6'
ON_INK, ON_INK_MUTED = '#F7F9F3', '#B9C3CC'
LINE, LINE_DARK = '#9BAA90', '#3A4654'
ORANGE, ORANGE_TEXT, ORANGE_ON_INK = '#E8592B', '#A93F17', '#F07A4E'   # the accent: fill, text on light, on ink
BLUE, BLUE_ON_INK = '#1C5FA8', '#8FB8E8'                               # the Mainframe pages' accent

# ---------------------------------------------------------------- the old colors, by what they were
KEEP_DARK = {'#16201C', '#12161F', '#0E1A17', '#0E1B17', '#2C3341'}    # dark: bands, or (small) buttons and pills
SURFACE = {'#1E2C26', '#1A2822', '#15261F', '#0A1411'}                 # raised surfaces on dark bands
LIGHT_BG = {'#F2EDE1', '#F4F1EA'}
CARDS = {'#FBF8F1', '#FBF9F4', '#F6F2E8', '#FFFDF7'}                    # #FFFDF7: the receipt paper (role pick)
TINTS = {'#F4EFE6', '#EAE3D3', '#EBE6DA', '#E8E1D1', '#EFEBE1'}         # #EFEBE1: checkup's info note (role pick)
INK_TEXT = {'#16201C', '#12161F', '#0E1A17', '#2C3341', '#0E1B17'}
INK2_TEXT = {'#3B4540', '#3E4640', '#3A4252', '#2E3833'}               # #2E3833: the case study's prose (role pick)
MUTED_TEXT = {'#676D66', '#5A635D', '#5C625C', '#6B716A', '#4A534D', '#5D6576', '#6F736D', '#8A8F87', '#9AA0AC'}
BRIGHT = {'#E9EEE9', '#F2EDE1', '#F4F1EA', '#E6E2D8', '#FFFFFF', 'WHITE'}
BRIGHT_MUTED = {'#C9D2CB', '#93A39A', '#B5C2BA', '#C9CED8', '#9AA3B5', '#B7BDC9'}
ACCENT_TEXT = {'#A93F17', '#C2461B', '#F07A4E'}
LIGHT_LINES = {'#CFC8B8', '#CFC6B2', '#B9B2A2', '#C9C1AE', '#B9B09C', '#A6AAA2', '#9AA097', '#DDD5C3', '#999999'}
BAND_LINES = {'#3A4D44', '#4C5F56', '#2B3D35', '#33463D', '#2A3140', '#3A4252'}   # #3A4252: Mainframe's band lines (role pick)
# Colors kept as they are, by role (listed in T-32's Receipt): status signals and the shot list's role tags.
KEPT = {'#2E7D4F', '#D9A520', '#7BD389', '#F9EEDA', '#F8E3DA', '#8A6A12',
        '#F6C9B5', '#D9E4D2', '#F2DEA8', '#E6DCF0', '#CFE0EE', '#000000', 'BLACK'}
# T-42 (Nov 22, 2026): blue as a data mark (DESIGN.md: "and data marks"), on any page: the Studio build log's
# Bird League and Birdsighted dots. Written in the new palette by tools/studio.py and kept as it is. No source used
# this color before (it would have stopped the build), so no other page changes.
DATA_MARKS = {BLUE}
RGBA = {
    'rgba(147,163,154,0.35)': 'rgba(168,139,92,0.30)',    # Local's contour lines (the table)
    'rgba(240,122,78,0.55)': 'rgba(168,139,92,0.55)',     # Local's orange contour lines (the table)
    'rgba(147,163,154,.45)': 'rgba(168,139,92,0.38)',     # start.html's contour lines (role pick)
    'rgba(240,122,78,.6)': 'rgba(168,139,92,0.6)',        # start.html's orange contour line (role pick)
    'rgba(18,22,31,0.07)': 'rgba(168,139,92,0.30)',       # Mainframe's contour lines (role pick)
    'rgba(230,226,216,0.06)': 'rgba(168,139,92,0.30)',    # Mainframe's contour lines on its dark band (role pick)
    'rgba(18,22,31,0.08)': 'rgba(23,33,43,0.08)',         # ink shadows and hairlines, now in ink
    'rgba(22,32,28,.18)': 'rgba(23,33,43,.18)', 'rgba(22,32,28,.08)': 'rgba(23,33,43,.08)',
    'rgba(22,32,28,.35)': 'rgba(23,33,43,.35)',
    'rgba(232,89,43,.45)': 'rgba(232,89,43,.45)',         # the caption tool's safe-zone legend: the accent, kept
    'rgba(0,0,0,0.45)': 'rgba(0,0,0,0.45)', 'rgba(0,0,0,0.2)': 'rgba(0,0,0,0.2)',
}

SMALL = {'a', 'button', 'span', 'strong', 'b', 'em', 'i', 'small', 'label', 'code', 'kbd', 'mark', 'time', 'abbr'}
FIELDS = {'input', 'textarea', 'select'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
# CSS rules whose own dark background is a small dark element (a button, a chip when pressed, a pill, a toast).
KEEP_DARK_SEL = re.compile(r'\.(btn|chip|filt|seg|nib|toast|pill|hero-pill|r-call|send|quiet|seal|used)\b|::selection')
ACCENT_SEL = re.compile(r'btn-blaze|\.hot\b|\.iq\[aria-pressed')

COLOR = re.compile(r'(?<![&\w#])#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f\w])|rgba?\([^)]*\)|\b(?:white|black)\b', re.I)


class Unknown(Exception):
    pass


def norm(c):
    c = c.strip()
    if c.lower().startswith('rgb'):
        return c.replace(' ', '')
    if c.startswith('#'):
        h = c[1:].upper()
        return '#' + (''.join(ch * 2 for ch in h) if len(h) == 3 else h)
    return c.upper()


def accents(mf):
    return (BLUE, BLUE, BLUE_ON_INK) if mf else (ORANGE, ORANGE_TEXT, ORANGE_ON_INK)


def on_accent(mf):
    return ON_INK if mf else INK   # ink on orange is 4.6:1; blue needs light text


def map_color(role, tok, zone, mf, tag=''):
    """One color token, by its role (bg, text, line, svgfill) and the zone it sits on (light, dark, accent)."""
    c = norm(tok)
    fill, acc_text, acc_ink = accents(mf)
    if c.startswith('RGB'):
        c = tok.replace(' ', '')
    if c.startswith('rgb'):
        if c in RGBA:
            return RGBA[c]
        raise Unknown(c)
    if c in KEPT or c in DATA_MARKS:
        return tok
    if role == 'bg':
        if c in ('#FFFFFF', 'WHITE'):
            return tok                                   # white stays
        if c in KEEP_DARK or c in SURFACE:
            if zone == 'dark':
                return INK
            return CARD if tag in FIELDS else CHART      # a dark band goes light; a dark form field becomes a card field
        if c in LIGHT_BG:
            return CHART
        if c in CARDS:
            return CARD
        if c in TINTS:
            return TINT
        if c == ORANGE:
            return fill
        if c in ('#E9EEE9',):                            # the product pages' hero pill: a status pill, so ink
            return INK
        if c == '#93A39A':                               # Local's office-hours dot, closed
            return MUTED
        if c == '#3B4540':                               # the caption tool's phone screen
            return INK2
        if c == '#2A3040':                               # the briefing button's hover
            return INK2
        if c == '#C2461B':                               # the caption tool's "too long" mark
            return acc_text
        raise Unknown(c)
    if role in ('text', 'svgfill'):
        if role == 'svgfill' and c == ORANGE:
            return acc_ink if (mf and zone == 'dark') else fill   # the logo's sun
        if zone == 'accent':
            if c in INK_TEXT or c in BRIGHT:
                return on_accent(mf)
        if c in INK_TEXT:
            return ON_INK if zone == 'dark' else INK      # dark text on a light pill that is now ink: light
        if c in INK2_TEXT:
            return ON_INK_MUTED if zone == 'dark' else INK2
        if c in MUTED_TEXT:
            return ON_INK_MUTED if zone == 'dark' else MUTED
        if c in BRIGHT:
            return ON_INK if zone == 'dark' else INK
        if c in BRIGHT_MUTED:
            return ON_INK_MUTED if zone == 'dark' else MUTED
        if c in ACCENT_TEXT or c == ORANGE:
            return acc_ink if zone == 'dark' else acc_text
        raise Unknown(c)
    if role == 'line':
        if c in LIGHT_LINES or c in BAND_LINES:
            return LINE_DARK if zone == 'dark' else LINE
        if c in KEEP_DARK:
            return INK
        if c in BRIGHT:
            return ON_INK if zone == 'dark' else INK
        if c == ORANGE:
            return acc_ink if zone == 'dark' else fill
        if c in ACCENT_TEXT:
            return acc_ink if zone == 'dark' else acc_text
        if c in MUTED_TEXT:
            return MUTED
        raise Unknown(c)
    raise Unknown(f'{role}:{c}')


def role_of(prop):
    p = prop.strip().lower()
    if p in ('-webkit-mask', 'mask', 'mask-image', '-webkit-mask-image'):
        return None
    if p.startswith('background'):
        return 'bg'
    if p in ('color', 'caret-color', '-webkit-text-fill-color', 'text-decoration', 'text-decoration-color', 'fill'):
        return 'text'
    if p.startswith('border') or p.startswith('outline') or p in ('box-shadow', 'text-shadow', 'stroke', 'column-rule'):
        return 'line'
    return 'other'


DECL = re.compile(r'([A-Za-z-]+)(\s*:\s*)([^;{}]*)')


def bg_of(style):
    for m in DECL.finditer(style):
        if role_of(m.group(1)) == 'bg':
            c = COLOR.search(m.group(3))
            if c:
                return norm(c.group(0))
    return None


def theme_decls(style, zone, mf, where, tag=''):
    """Rewrite each color in a declaration list, by the declaration's property."""
    def rep(m):
        prop, sep, val = m.group(1), m.group(2), m.group(3)
        role = role_of(prop)
        if role is None:
            return m.group(0)
        def one(cm):
            if role == 'other':
                raise Unknown(f'{where}: a color in {prop}: {cm.group(0)}')
            try:
                return map_color(role, cm.group(0), zone, mf, tag)
            except Unknown as e:
                raise Unknown(f'{where}: {prop}: {e} (zone {zone})')
        return prop + sep + COLOR.sub(one, val)
    return DECL.sub(rep, style)


def css_zone(sel, body):
    bg = bg_of(body)
    if bg == ORANGE:
        return 'accent'
    if bg in KEEP_DARK or bg == '#E9EEE9' or bg == '#2A3040':
        return 'dark' if KEEP_DARK_SEL.search(sel) else 'light'
    if ACCENT_SEL.search(sel):
        return 'accent'
    if KEEP_DARK_SEL.search(sel) and re.search(r'\.(btn|seal|send)\b(?!\.(hot|ghost))', sel) and 'ghost' not in sel and 'hot' not in sel \
            and not re.search(r'\.btn-', sel):
        return 'dark'
    return 'light'


def theme_css(css, mf, where):
    out, i = [], 0
    for m in re.finditer(r'([^{}]*)\{([^{}]*)\}', css):
        sel, body = m.group(1), m.group(2)
        out.append(css[i:m.start()])
        out.append(sel + '{' + theme_decls(body, css_zone(sel, body), mf, f'{where} <style> {sel.strip()[:60]}') + '}')
        i = m.end()
    out.append(css[i:])
    return ''.join(out)


def elem_zone(tag, attrs, style, parent, page):
    bg = bg_of(style) if style else None
    cls = (attrs.get('class') or '').split()
    if tag == 'footer' and bg in (KEEP_DARK | SURFACE):
        return 'dark'
    if tag == 'section' and attrs.get('aria-labelledby') in ('next-h', 'c7') and bg in KEEP_DARK:
        return 'dark'                                             # the closing call box
    if bg:
        if bg == ORANGE:
            return 'accent'
        if bg in KEEP_DARK:
            if parent == 'dark' or (tag in SMALL and 'route' not in cls):
                return 'dark'
            return 'light'
        if bg in SURFACE:
            return 'dark' if parent == 'dark' else 'light'
        if bg in LIGHT_BG | CARDS | TINTS | {'#FFFFFF', 'WHITE'}:
            return 'light'
    if 'btn-blaze' in cls or ('btn' in cls and 'hot' in cls) or ('send' in cls and page in ('call.html', 'start.html')):
        return 'accent'
    if ('btn' in cls and 'ghost' not in cls) or 'pill' in cls or 'hero-pill' in cls or ('send' in cls and page == 'briefing.html'):
        return 'dark'
    return parent


ATTR = re.compile(r'''([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?''')


def parse_attrs(s):
    return {m.group(1).lower(): (m.group(2) if m.group(2) is not None else m.group(3) if m.group(3) is not None else m.group(4) or '')
            for m in ATTR.finditer(s)}


SCRIPT_STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'')
STYLE_IN_STR = re.compile(r'style=(\\?)"(.*?)\1"')


def theme_script(js, mf, where):
    """The style strings a script applies: JSON state styles, HTML templates' style="...", and Mainframe's
    "color" value. Bare colors (the caption tool's canvas paint) are left alone."""
    js = re.sub(r'("color":\s*")(#[0-9A-Fa-f]{6})(")', lambda m: m.group(1) + map_color('text', m.group(2), 'light', mf) + m.group(3), js)
    js = js.replace("? '#7BD389' : '#93A39A'", "? '#7BD389' : '" + MUTED + "'")   # Local's office-hours dot

    def lit(m):
        q = '"' if m.group(1) is not None else "'"
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if not COLOR.search(s) or ':' not in s:
            return m.group(0)
        if STYLE_IN_STR.search(s):          # an HTML template: each style="..." on its own
            s2 = STYLE_IN_STR.sub(lambda t: 'style=' + t.group(1) + '"' + theme_decls(
                t.group(2), script_zone(t.group(2)), mf, where) + t.group(1) + '"', s)
            return q + s2 + q
        if re.match(r'\s*[a-z-]+\s*:\s*[^:]', s) and ';' in s or re.match(r'\s*[a-z-]+\s*:.*#', s):
            return q + theme_decls(s, script_zone(s), mf, where) + q
        return m.group(0)
    return SCRIPT_STR.sub(lit, js)


def script_zone(style):
    bg = bg_of(style)
    if bg == ORANGE:
        return 'accent'
    if bg in KEEP_DARK:
        return 'dark'                       # in a script, a dark fill is a pressed chip or a button
    return 'light'


FONT_LINK = re.compile(r'(https://fonts\.googleapis\.com/css2\?)([^"]*)')


def fonts(html):
    html = html.replace("'Big Shoulders Display'", "'Barlow Semi Condensed'").replace('Big Shoulders Display', 'Barlow Semi Condensed')
    html = html.replace("'Instrument Sans'", "'Barlow'").replace('Instrument Sans', 'Barlow')

    def link(m):
        fams = m.group(2).split('&amp;')
        keep = [f for f in fams if not f.startswith(('family=Big+Shoulders+Display', 'family=Instrument+Sans'))]
        had = len(keep) != len(fams)
        if not had:
            return m.group(0)
        new = ['family=Barlow+Semi+Condensed:wght@600;700;800;900', 'family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400']
        at = next(i for i, f in enumerate(fams) if f.startswith(('family=Big+Shoulders+Display', 'family=Instrument+Sans')))
        disp = [f for f in keep if f.startswith('display=')]
        keep = [f for f in keep if not f.startswith('display=')]
        at = min(at, len(keep))
        return m.group(1) + '&amp;'.join(keep[:at] + new + keep[at:] + disp)
    html = FONT_LINK.sub(link, html)
    return re.sub(r'text-transform(\s*:\s*)uppercase', r'text-transform\1none', html)


# ---------------------------------------------------------------- the ring
# Each page's one next step: its first accent-filled button in its first screen (fully inside the first 390 x 844 or
# 1440 x 900 view). Measured on the themed pages; the T-32 test checks each one against that rule.
# page -> the exact start tag of the ringed element (it must occur exactly once).
RINGS = {
    'local.html': '<a href="start.html" class="btn-blaze" style="display: inline-flex; align-items: center; min-height: 44px;',   # the header's
    # In the first screen at 390 (its bottom at 802 of 844); below the fold at 1440. The page's only accent button.
    'checkup.html': '<a href="call.html" style="display:inline-flex;align-items:center;min-height:56px;padding:0 24px;background:#E8592B;',
}
RING_PATH = 'M20 5 C45 2 90 2 108 6 C117 8 118 18 117 26 C116 38 110 44 92 45 C65 46.5 35 46 16 43 C5 41 2 33 3 23 C4 12 9 6 26 4.5 C40 3.5 52 3.8 62 4.4'


def ring_svg(mf):
    return ('<svg class="t32-ring" aria-hidden="true" focusable="false" viewBox="0 0 120 48" preserveAspectRatio="none">'
            f'<path d="{RING_PATH}" fill="none" stroke="{BLUE if mf else ORANGE}" stroke-width="3" stroke-linecap="round" '
            'vector-effect="non-scaling-stroke"/></svg>')


RING_CSS = ('.t32-ring{position:absolute;left:-15px;top:-12px;width:calc(100% + 30px);height:calc(100% + 24px);'
            'overflow:visible;pointer-events:none;transform:rotate(-1.5deg)}')


def add_ring(html, page, mf):
    start = RINGS.get(page)
    if not start:
        return html
    n = html.count(start)
    if n != 1:
        raise SystemExit(f'theme.py: {page}: the ringed element ({start[:60]}...) is on the page {n} times, not once')
    i = html.index(start)
    j = html.index('>', i)
    tag = html[i:j]
    if 'position:' not in tag.replace(' ', ''):
        tag = re.sub(r'style="', 'style="position: relative; ', tag, count=1) if '; ' in tag else re.sub(r'style="', 'style="position:relative;', tag, count=1)
    return html[:i] + tag + '>' + ring_svg(mf) + html[j + 1:]


# ---------------------------------------------------------------- the route
def dash(color, way):
    return f'repeating-linear-gradient(to {way},{color} 0 10px,transparent 10px 18px)'


def route_css(page, mf):
    c = BLUE if mf else ORANGE
    if page == 'local.html':
        return ('#route ol{position:relative;border-top-color:transparent!important}'
                f'#route ol::before{{content:"";position:absolute;left:0;right:0;top:-3px;height:3px;background:{dash(c, "right")};pointer-events:none}}'
                '@media (max-width:699px){#route ol::before{display:none}'
                f'#route ol>li:not(:last-child)::before{{background:{dash(c, "bottom")}!important}}}}'
                '.t32-rt{position:relative}'
                f'.t32-rt::before{{content:"";position:absolute;left:52px;top:0;bottom:-10px;width:3px;background:{dash(c, "bottom")};pointer-events:none}}'
                '.t32-rt-end::before{bottom:0}')
    if page == 'mainframe.html':
        return ('.t20-steps{position:relative;border-top-color:transparent!important}'
                f'.t20-steps::before{{content:"";position:absolute;left:0;right:0;top:-2px;height:3px;background:{dash(c, "right")};pointer-events:none}}'
                '@media (max-width:640px){.t20-steps::before{left:-11px;right:auto;top:28px;bottom:30px;width:3px;height:auto;'
                f'background:{dash(c, "bottom")}}}}}')
    if page == 'start.html':
        return ('.t32-rt{position:relative}'
                f'.t32-rt::before{{content:"";position:absolute;left:58px;top:0;bottom:-12px;width:3px;background:{dash(c, "bottom")};pointer-events:none}}'
                '.t32-rt-end::before{bottom:0}'
                '.t32-rl{position:relative}'
                f'.t32-rl::before{{content:"";position:absolute;left:-12px;top:.35em;bottom:.35em;width:3px;background:{dash(c, "bottom")};pointer-events:none}}')
    return ''


# The rows each vertical route runs beside: (page, the row's exact start tag, how many, the class for the last one).
ROUTE_ROWS = [
    ('local.html', '<div style="display: grid; grid-template-columns: 64px minmax(0, 1fr); gap: 10px">', 3),
    ('start.html', '<div style="display:grid;grid-template-columns:72px minmax(0,1fr);gap:10px;font-size:16px;color:#17212B">', 3),   # after the color pass
]
ROUTE_LISTS = [('start.html', '<ol style="margin:0;padding-left:22px;display:flex;flex-direction:column;gap:8px;font-size:18px;color:#17212B">')]   # after the color pass


def mark_routes(html, page):
    for p, start, n in ROUTE_ROWS:
        if p != page:
            continue
        if html.count(start) != n:
            raise SystemExit(f'theme.py: {page}: expected {n} route rows, found {html.count(start)}')
        k = 0

        def cls(_m):
            nonlocal k
            k += 1
            return start.replace('<div style=', f'<div class="t32-rt{" t32-rt-end" if k == n else ""}" style=', 1)
        html = re.sub(re.escape(start), cls, html)
    for p, start in ROUTE_LISTS:
        if p == page:
            if html.count(start) != 1:
                raise SystemExit(f'theme.py: {page}: the route list is not on the page once')
            html = html.replace(start, start.replace('<ol style=', '<ol class="t32-rl" style=', 1))
    return html


# ---------------------------------------------------------------- the pen underline
# T-34 (Nov 20, 2026): a headline's marked words stay upright in their color; three words or fewer also get this line
# under them (class="pen", written by the source that writes the headline). A background image, so it wraps with the
# words, sits behind them and takes no taps. Orange on the Local side, blue on the Mainframe pages; on something that
# stays dark the lighter one, by the element's zone (pen-ink, added here).
PEN_PATH = 'M3 13 C 60 6, 120 16, 180 9 S 270 7, 297 11'
PEN_ON = re.compile(r'class="pen[" ]')


def pen_img(color):
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 20' preserveAspectRatio='none'%3E"
            f"%3Cpath d='{PEN_PATH}' fill='none' stroke='%23{color[1:]}' stroke-width='5' stroke-linecap='round'/%3E%3C/svg%3E\")")


def pen_css(mf):
    return ('.pen{background-image:' + pen_img(BLUE if mf else ORANGE) + ';background-repeat:no-repeat;'
            'background-size:100% 0.2em;background-position:0 100%;padding-bottom:0.12em;'
            'box-decoration-break:clone;-webkit-box-decoration-break:clone}'
            '.pen.pen-ink{background-image:' + pen_img(BLUE_ON_INK if mf else ORANGE_ON_INK) + '}')


# ---------------------------------------------------------------- one page
TAG = re.compile(r'<!--.*?-->|<(script|style)\b([^>]*)>(.*?)</\1\s*>|<(/?)([A-Za-z][\w:-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>', re.S)
SVG_PAINT = re.compile(r'(\s(?:fill|stroke|stop-color)=")([^"]*)(")')


def theme_page(html, page):
    mf = page in MF
    out, i, stack = [], 0, [('#root', 'light')]
    for m in TAG.finditer(html):
        out.append(html[i:m.start()])
        i = m.end()
        tok = m.group(0)
        if tok.startswith('<!--'):
            out.append(tok)
            continue
        if m.group(1):                                   # <script> or <style>
            kind, attrs, body = m.group(1).lower(), m.group(2), m.group(3)
            if kind == 'style':
                body = theme_css(body, mf, page)
            elif 'ld+json' not in attrs:
                body = theme_script(body, mf, page)
            out.append(f'<{m.group(1)}{attrs}>{body}</{m.group(1)}>')
            continue
        close, tag, rest = m.group(4), m.group(5).lower(), m.group(6)
        if close:
            while len(stack) > 1:
                t, _z = stack.pop()
                if t == tag:
                    break
            out.append(tok)
            continue
        attrs = parse_attrs(rest)
        style = attrs.get('style')
        parent = stack[-1][1]
        zone = elem_zone(tag, attrs, style or '', parent, page)
        if zone == 'dark' and 'pen' in (attrs.get('class') or '').split():
            rest = rest.replace('class="pen', 'class="pen pen-ink', 1)
        if style is not None:
            new = theme_decls(style, zone, mf, f'{page} <{tag} style>', tag)
            rest = rest.replace(f'style="{style}"', f'style="{new}"', 1)
        if any(a in attrs for a in ('fill', 'stroke', 'stop-color')):
            role = 'text' if tag in ('text', 'tspan') else 'svgfill'

            def paint(pm):
                v = pm.group(2)
                if not COLOR.search(v):
                    return pm.group(0)
                r = 'line' if pm.group(1).strip().startswith('stroke') else role
                try:
                    return pm.group(1) + COLOR.sub(lambda c: map_color(r, c.group(0), zone, mf), v) + pm.group(3)
                except Unknown as e:
                    raise Unknown(f'{page} <{tag} {pm.group(1).strip()}>: {e}')
            rest = SVG_PAINT.sub(paint, rest)
        out.append(f'<{m.group(5)}{rest}>')
        if tag not in VOID and not rest.rstrip().endswith('/'):
            stack.append((tag, zone))
    out.append(html[i:])
    html = fonts(''.join(out))
    html = mark_routes(html, page)
    html = add_ring(html, page, mf)
    css = (RING_CSS if RINGS.get(page) else '') + route_css(page, mf) + (pen_css(mf) if PEN_ON.search(html) else '')
    if css:
        if html.count('</head>') != 1:
            raise SystemExit(f'theme.py: {page}: no single </head>')
        html = html.replace('</head>', f'<style data-t32>{css}</style>\n</head>', 1)
    return html


def main(src, dst):
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if os.path.basename(dst) != 'out-themed' or os.path.dirname(dst) != os.path.dirname(os.path.abspath(__file__)):
        raise SystemExit('theme.py writes only _build/out-themed/')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    bad = []
    for name in sorted(os.listdir(src)):
        if not name.endswith('.html'):
            continue
        with open(os.path.join(src, name), encoding='utf-8', newline='') as f:
            html = f.read()
        try:
            new = theme_page(html, name)
        except Unknown as e:
            bad.append(str(e))
            continue
        with open(os.path.join(dst, name), 'w', encoding='utf-8', newline='') as f:
            f.write(new)
    if bad:
        raise SystemExit('theme.py: colors it does not know (add each to a role, and to the Receipt):\n  ' + '\n  '.join(bad))
    print(f'theme.py: {sum(n.endswith(".html") for n in os.listdir(dst))} pages themed into {dst}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out', sys.argv[2] if len(sys.argv) > 2 else 'out-themed')
