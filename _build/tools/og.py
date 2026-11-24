#!/usr/bin/env python3
"""Share cards (og:image) for every public page. Added Nov 9, 2026 (trip item T-01).
Redrawn in the chart style Nov 22, 2026 (T-40): same words, the live page's look.

    cd _build && python3 tools/og.py out

Reads the finished pages in out/ (after plain.py and intent.py, so the words
match the live page) and writes one 1200 by 630 PNG per page into
_build/assets/og/. enhance.py copies them to out/og/. Rerun this whenever a
page's <h1> or meta description changes, then rebuild from step 4.

The look (T-40): a small poster of the page's top. Chart paper (#E4ECD8), the
brand row as the live header draws it (the mountain mark in ink, its dot in the
accent, "Dragoman's Journey" in Newsreader), the headline in ink in the face and
weight the page's own <h1> uses (Barlow Semi Condensed 800 or 900, or Newsreader
300 on the Mainframe pages), the subhead in Barlow, and an accent bar along the
bottom. The accent is orange, blue on the Mainframe pages (theme.py's MF set).
Words the live <h1> colors keep that color, and words it marks class="pen" get
theme.py's pen underline in the accent. Free tools get an ink "Free tool" pill.
The colors and marks are read from the repo-root copy of each page (the themed,
live one); its <h1> words must match out/'s.

Headline: the page's <h1>, tags stripped, <br> as a space, as the page writes
it (sentence case). Lines are balanced; when the page's own <br> breaks give
the same number of lines and fit, those breaks are used.
Subhead: the page's meta description, cut at the last sentence end under 110
characters. If no sentence ends that early, the page's og:description is tried
the same way. If that fails too, the meta description is cut at the last comma,
colon or semicolon under 110 and ends with a period. A first sentence that just
repeats the headline is skipped.
Free tool tag: every page linked from a card tagged "free" on work.html.
Every text color pair is checked against WCAG AA at the smallest size it is
drawn (4.5:1 under 24px, 3:1 at 24px and up); the run stops if one falls short.
"""
import html
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent          # _build/
ROOT = HERE.parent                                     # the repo root: the themed, live pages
FONTS = HERE / "assets" / "fonts"
DEST = HERE / "assets" / "og"

PAGES = ["index", "local", "mainframe", "work", "comp3", "shotlist", "captions",
         "receipt", "scaler", "start", "call", "case-reels", "briefing", "studio", "checkup", "voicecheck", "sample-blueprint", "sample-report"]   # T-47   # T-35: the voice checker
# Plus one card per Studio product page (T-09), the same list studio.py writes.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio  # noqa: E402
PAGES += [slug[:-len(".html")] for slug, _ in studio.product_pages(studio.load()[0])]

# The chart style's palette, Mainframe set and pen stroke come from theme.py (step 6c).
sys.path.insert(0, str(HERE))
import theme  # noqa: E402

W, H = 1200, 630
S = 2                      # draw at 2x, then scale down for clean edges
M = 64                     # margin on every side
CHART, INK, INK2, ON_INK = theme.CHART, theme.INK, theme.INK2, theme.ON_INK
ORANGE, BLUE = theme.ORANGE, theme.BLUE
MF = {p[:-len(".html")] for p in theme.MF}
BAR = 14                   # accent bar along the bottom
SUB_MAX = 110

BARLOW_SC = {800: "BarlowSemiCondensed-ExtraBold.ttf", 900: "BarlowSemiCondensed-Black.ttf"}
TAG_FONT = "BarlowSemiCondensed-SemiBold.ttf"
SANS = "Barlow-Regular.ttf"
SERIF = "Newsreader-Variable.ttf"      # variable: weight and optical size set per use, as a browser would


def font(name, px, wght=None):
    f = ImageFont.truetype(str(FONTS / name), px * S)
    if wght is not None:
        vals = []
        for a in f.get_variation_axes():
            n = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
            vals.append(wght if n == "Weight" else max(a["minimum"], min(a["maximum"], px)))
        f.set_variation_by_axes(vals)
    return f


def plain(fragment):
    t = re.sub(r"<br\s*/?>", " ", fragment)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def squash(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def sentences_of(desc, headline):
    found = re.findall(r".+?[.?!](?=\s|$)|.+$", desc)
    found = [s.strip() for s in found if s.strip()]
    if len(found) > 1 and squash(found[0]) == squash(headline):
        found = found[1:]
    return found


def sentence_cut(desc, headline):
    found, best = sentences_of(desc, headline), ""
    for i in range(1, len(found) + 1):
        cut = " ".join(found[:i])
        if len(cut) < SUB_MAX:
            best = cut
    return best


def subhead(desc, og_desc, headline):
    best = sentence_cut(desc, headline) or sentence_cut(og_desc, headline)
    if best:
        return best
    text = " ".join(sentences_of(desc, headline))
    # No sentence ends under the limit: cut at the last clause mark instead.
    marks = [m.start() for m in re.finditer(r"[,:;]", text) if m.start() < SUB_MAX - 1]
    assert marks, "no place to cut: " + text
    return text[:marks[-1]].rstrip() + "."


def free_pages(out):
    t = (out / "work.html").read_text(encoding="utf-8")
    found = set()
    for card in re.findall(r'<article class="card[^"]*" data-k="([^"]*)">(.*?)</article>', t, re.S):
        if "free" in card[0].split():
            found.update(re.findall(r'href="([a-z0-9-]+)\.html', card[1]))
    return found


def wrap(draw, text, f, width):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=f) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    lines.append(line)
    return lines


def balanced(draw, text, f, width):
    # Same number of lines as a plain wrap, but as even as possible: no widows.
    lines = wrap(draw, text, f, width)
    lo, hi = 1, width
    while lo < hi:
        mid = (lo + hi) // 2
        if len(wrap(draw, text, f, mid)) <= len(lines) and fits(draw, wrap(draw, text, f, mid), f, mid):
            hi = mid
        else:
            lo = mid + 1
    return wrap(draw, text, f, lo)


def fits(draw, lines, f, width):
    return all(draw.textlength(l, font=f) <= width for l in lines)


# ---------------------------------------------------------------- the live <h1>: face, colors, marks
def h1_face(page_html, tag):
    """(font file, weight, line height) for the face the page's <h1> is drawn in."""
    style = (re.search(r'style="([^"]*)"', tag) or [None, ""])[1]
    cls = (re.search(r'class="([^"]*)"', tag) or [None, ""])[1].split()
    weight = re.search(r"font-weight:\s*(\d+)", style)
    if "Newsreader" in style or "serif" in cls:
        assert weight, "no weight on a Newsreader <h1>"
        return SERIF, int(weight.group(1)), 1.0
    if not weight and "big" in cls:
        weight = re.search(r"\.big\{[^}]*font-weight:(\d+)", page_html)
    assert weight and int(weight.group(1)) in BARLOW_SC, "unknown <h1> weight: " + tag
    return BARLOW_SC[int(weight.group(1))], int(weight.group(1)), 0.9


def h1_styles(inner):
    """One (color, pen) per character of plain(inner): the color the live page gives each word, and its pen mark."""
    chars, stack = [], [(INK, False)]
    for tok in re.findall(r"<[^>]+>|[^<]+", inner):
        if tok.startswith("<"):
            if re.match(r"<br\s*/?>", tok):
                chars.append((" ", stack[-1]))
            elif tok.startswith("</"):
                stack.pop()
            else:
                color, pen = stack[-1]
                c = re.search(r"color:\s*(#[0-9A-Fa-f]{6})", tok)
                cls = (re.search(r'class="([^"]*)"', tok) or [None, ""])[1].split()
                stack.append((c.group(1).upper() if c else color, pen or "pen" in cls))
        else:
            chars += [(ch, stack[-1]) for ch in html.unescape(tok)]
    out = []                                   # collapse whitespace the way plain() does
    for ch, st in chars:
        if ch.isspace():
            if out and out[-1][0] != " ":
                out.append((" ", st))
        else:
            out.append((ch, st))
    while out and out[-1][0] == " ":
        out.pop()
    while out and out[0][0] == " ":
        out.pop(0)
    return "".join(c for c, _ in out), [st for _, st in out]


# ---------------------------------------------------------------- drawing
def mark(draw, x, y, size, accent):
    # The site's mountain mark, from the 34 by 34 header SVG: ink stroke, accent dot.
    k = size / 34
    pts = [(4, 28), (13, 10), (19, 20), (23, 14), (30, 28)]
    pts = [(x + px * k, y + py * k) for px, py in pts]
    draw.line(pts + [pts[0], pts[1]], fill=INK, width=max(2, round(1.8 * k)), joint="curve")
    r = 2.4 * k
    cx, cy = x + 23 * k, y + 7 * k
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)


def bezier(p0, p1, p2, p3, n=24):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                  for a, b, c, d in zip(p0, p1, p2, p3)) for t in (i / n for i in range(n + 1))]


def pen_points():
    # theme.PEN_PATH in its 300 by 20 box: M p0 C a b p1 S c p2 (S mirrors b about p1).
    nums = [float(v) for v in re.findall(r"-?[\d.]+", theme.PEN_PATH)]
    assert len(nums) == 12 and re.fullmatch(r"M[\d ]+C[\d ,]+S[\d ,]+", theme.PEN_PATH.replace(".", "")), theme.PEN_PATH
    p0, a, b, p1, c, p2 = [tuple(nums[i:i + 2]) for i in range(0, 12, 2)]
    m = (2 * p1[0] - b[0], 2 * p1[1] - b[1])
    return bezier(p0, a, b, p1) + bezier(p1, m, c, p2)[1:]


PEN = pen_points()


def pen(draw, x0, x1, top, height, color):
    # As the page draws it: the 300 by 20 stroke stretched to the words' width and 0.2em tall, stroke 5 of 20.
    pts = [(x0 + px / 300 * (x1 - x0), top + py / 20 * height) for px, py in PEN]
    w = max(2 * S, round(height * 5 / 20))
    draw.line(pts, fill=color, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        draw.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=color)


def headline_layout(d, headline, styles, face, breaks, width, room):
    """Size, lines and baselines of the biggest headline that fits: at most 4 lines, balanced."""
    file, weight, lh_em = face
    hp = 150
    while True:
        hf = font(file, hp, weight if file == SERIF else None)
        em = hp * S
        lines = balanced(d, headline, hf, width)
        if breaks and len(breaks) == len(lines) and fits(d, breaks, hf, width):
            lines = list(breaks)                   # the page's own <br> breaks
        asc, desc = hf.getmetrics()
        starts, at = [], 0
        for l in lines:
            assert headline[at:at + len(l)] == l, (headline, lines)
            starts.append(at)
            at += len(l) + 1
        # Pen band per line, as the page draws it: the span's bottom edge (descent + 0.12em) up 0.2em.
        pen_bottom = desc + 0.12 * em
        has_pen = [any(st[1] for st in styles[s:s + len(l)]) for s, l in zip(starts, lines)]
        base, y = [], 0
        for i, l in enumerate(lines):
            if i:
                y += round(hp * lh_em) * S
                if has_pen[i - 1]:                   # a pen underline never touches the next line
                    top = d.textbbox((0, 0), l, font=hf, anchor="ls")[1]
                    y = max(y, base[-1] + pen_bottom + 0.06 * em - top)
            base.append(y)
        top = d.textbbox((0, 0), lines[0], font=hf, anchor="ls")[1]
        # Room for a descender even when the last line has none, so the gap to the subhead is the same on every card.
        low = max(d.textbbox((0, 0), lines[-1], font=hf, anchor="ls")[3], 0.2 * em)
        if has_pen[-1]:
            low = max(low, pen_bottom)
        block = base[-1] + low - top
        if fits(d, lines, hf, width) and block <= room and len(lines) <= 4:
            return hp, hf, lines, starts, base, low, em, desc
        hp -= 2
        assert hp > 40, "headline will not fit: " + headline


def card(headline, styles, face, sub, free, accent, breaks=None):
    img = Image.new("RGB", (W * S, H * S), CHART)
    d = ImageDraw.Draw(img)
    left, right, width = M * S, (W - M) * S, (W - 2 * M) * S

    # Brand row, as the live header: the mark, then the name in Newsreader.
    size = 46 * S
    top = M * S
    mark(d, left, top, size, accent)
    bf = font(SERIF, BRAND_PX, 400)
    d.text((left + size + 16 * S, top + size / 2), "Dragoman's Journey", font=bf, fill=INK, anchor="lm")

    if free:
        tf = font(TAG_FONT, TAG_PX)
        label = "Free tool"
        tw = d.textlength(label, font=tf)
        padx, h = 20 * S, 44 * S
        x1 = right
        x0 = x1 - tw - 2 * padx
        y0 = top + (size - h) / 2
        d.rounded_rectangle([x0, y0, x1, y0 + h], radius=h / 2, fill=INK)
        d.text(((x0 + x1) / 2, y0 + h / 2), label, font=tf, fill=ON_INK, anchor="mm")

    # Subhead, anchored to the bottom margin above the bar.
    bottom = (H - BAR - M + 14) * S
    sp = 30
    while True:
        sf = font(SANS, sp)
        slines = balanced(d, sub, sf, width)
        if len(slines) <= 2 and fits(d, slines, sf, width):
            break
        sp -= 1
    slh = round(sp * 1.3) * S
    sub_top = bottom - slh * len(slines)
    for i, l in enumerate(slines):
        d.text((left, sub_top + i * slh), l, font=sf, fill=INK2, anchor="la")

    # Headline: as big as it can be, its lowest mark 28px above the subhead.
    head_top = top + size + 40 * S
    head_bottom = sub_top - 28 * S
    hp, hf, lines, starts, base, low, em, desc = headline_layout(
        d, headline, styles, face, breaks, width, head_bottom - head_top)
    shift = head_bottom - low - base[-1]
    pens, runs = [], []
    for l, s, b in zip(lines, starts, base):
        y = b + shift
        i = 0
        while i < len(l):
            j = i
            while j < len(l) and styles[s + j] == styles[s + i]:
                j += 1
            color, marked = styles[s + i]
            x0 = left + d.textlength(l[:i], font=hf)
            x1 = left + d.textlength(l[:j], font=hf)
            runs.append((x0, y, l[i:j], color))
            if marked and l[i:j].strip():
                lead = d.textlength(l[i:j], font=hf) - d.textlength(l[i:j].lstrip(), font=hf)
                trail = d.textlength(l[i:j], font=hf) - d.textlength(l[i:j].rstrip(), font=hf)
                pens.append((x0 + lead, x1 - trail, y + desc + 0.12 * em - 0.2 * em))
            i = j
    for x0, x1, ptop in pens:                       # behind the words, as on the page
        pen(d, x0, x1, ptop, 0.2 * em, accent)
    for x, y, t, color in runs:
        d.text((x, y), t, font=hf, fill=color, anchor="ls")

    d.rectangle([0, (H - BAR) * S, W * S, H * S], fill=accent)
    return img.resize((W, H), Image.LANCZOS), hp, sp, lines


BRAND_PX = 32
TAG_PX = 22


# ---------------------------------------------------------------- WCAG AA, worked out from the colors
def luminance(hex_color):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def contrast_report(pairs):
    """pairs: {(what, fg, bg): smallest px drawn}. Prints each pair's ratio and floor; stops on a miss."""
    bad = []
    for (what, fg, bg), px in sorted(pairs.items()):
        r = ratio(fg, bg)
        floor = 3.0 if px >= 24 else 4.5
        ok = r >= floor
        print(f"contrast: {what} {fg} on {bg}, {px}px and up: {r:.2f}:1 (floor {floor}:1) {'ok' if ok else 'FAIL'}")
        if not ok:
            bad.append(what)
    assert not bad, "contrast below AA: " + ", ".join(bad)


def main(out):
    out = Path(out)
    DEST.mkdir(parents=True, exist_ok=True)
    free = free_pages(out)
    assert len(free) >= 5, free
    pairs = {}

    def need(what, fg, bg, px):
        key = (what, fg.upper(), bg.upper())
        pairs[key] = min(px, pairs.get(key, px))

    for name in PAGES:
        t = (out / f"{name}.html").read_text(encoding="utf-8")
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        assert len(h1s) == 1, name
        headline = plain(h1s[0])
        breaks = [plain(x) for x in re.split(r"<br\s*/?>", h1s[0])]
        if len(breaks) > 1:
            assert " ".join(breaks) == headline, name
        desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', t).group(1))
        og_desc = html.unescape(re.search(r'<meta property="og:description" content="([^"]*)"', t).group(1))
        sub = subhead(desc, og_desc, headline)
        assert "—" not in headline + sub, "em dash in card " + name
        # The look comes from the live page: the repo-root copy, themed.
        live = (ROOT / f"{name}.html").read_text(encoding="utf-8")
        tags = re.findall(r"(<h1[^>]*>)(.*?)</h1>", live, re.S)
        assert len(tags) == 1, name
        words, styles = h1_styles(tags[0][1])
        assert words == headline, f"{name}: live <h1> {words!r} is not out/'s {headline!r}"
        face = h1_face(live, tags[0][0])
        accent = BLUE if name in MF else ORANGE
        img, hp, sp, lines = card(headline, styles, face, sub, name in free, accent,
                                  breaks if len(breaks) > 1 else None)
        img.save(DEST / f"{name}.png", optimize=True)
        for color in {st[0] for st in styles}:
            need("headline", color, CHART, hp)
        need("subhead", INK2, CHART, sp)
        need("site name", INK, CHART, BRAND_PX)
        if name in free:
            need("free tool tag", ON_INK, INK, TAG_PX)
        print(f"{name}.png  {hp}px  {'FREE ' if name in free else ''}{headline!r} / {sub!r} ({len(sub)})")
    contrast_report(pairs)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "out")
