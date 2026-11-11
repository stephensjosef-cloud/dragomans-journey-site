#!/usr/bin/env python3
"""Share cards (og:image) for every public page. Added Nov 9, 2026 (trip item T-01).

    cd _build && python3 tools/og.py out

Reads the finished pages in out/ (after plain.py and intent.py, so the words
match the live page) and writes one 1200 by 630 PNG per page into
_build/assets/og/. enhance.py copies them to out/og/. Rerun this whenever a
page's <h1> or meta description changes, then rebuild from step 4.

Headline: the page's <h1>, tags stripped, <br> as a space, uppercase. Lines
are balanced; when the page's own <br> breaks give the same number of lines
and fit, those breaks are used.
Subhead: the page's meta description, cut at the last sentence end under 110
characters. If no sentence ends that early, the page's og:description is tried
the same way. If that fails too, the meta description is cut at the last comma,
colon or semicolon under 110 and ends with a period. A first sentence that just
repeats the headline is skipped.
Free tool tag: every page linked from a card tagged "free" on work.html.
"""
import html
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent          # _build/
FONTS = HERE / "assets" / "fonts"
DEST = HERE / "assets" / "og"

PAGES = ["index", "local", "mainframe", "work", "comp3", "shotlist", "captions",
         "receipt", "scaler", "start", "call", "case-reels", "briefing", "studio"]
# Plus one card per Studio product page (T-09), the same list studio.py writes.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio  # noqa: E402
PAGES += [slug[:-len(".html")] for slug, _ in studio.product_pages(studio.load()[0])]

W, H = 1200, 630
S = 2                      # draw at 2x, then scale down for clean edges
M = 64                     # margin on every side
BG = "#0E1B17"
INK = "#E9EEE9"
SOFT = "#C9D2CB"
BLAZE = "#E8592B"
BAR = 14                   # orange bar along the bottom
SUB_MAX = 110


def font(name, px):
    return ImageFont.truetype(str(FONTS / name), px * S)


BIG = "BigShouldersDisplay-ExtraBold.ttf"
SANS = "InstrumentSans-Regular.ttf"
SANS_BOLD = "InstrumentSans-Bold.ttf"
MONO = "JetBrainsMono-Bold.ttf"


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


def mark(draw, x, y, size):
    # The site's mountain mark, from the 34 by 34 header SVG.
    k = size / 34
    pts = [(4, 28), (13, 10), (19, 20), (23, 14), (30, 28)]
    pts = [(x + px * k, y + py * k) for px, py in pts]
    draw.line(pts + [pts[0]], fill=INK, width=max(2, round(1.8 * k)), joint="curve")
    r = 2.4 * k
    cx, cy = x + 23 * k, y + 7 * k
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLAZE)


def card(headline, sub, free, breaks=None):
    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)
    left, right, width = M * S, (W - M) * S, (W - 2 * M) * S

    # Brand row.
    size = 44 * S
    top = M * S
    mark(d, left, top, size)
    bf = font(SANS_BOLD, 28)
    bx = left + size + 14 * S
    asc, desc = bf.getmetrics()
    d.text((bx, top + size / 2), "Dragoman's Journey", font=bf, fill=INK, anchor="lm")

    if free:
        tf = font(MONO, 18)
        label = "FREE TOOL"
        tw = d.textlength(label, font=tf)
        padx, h = 14 * S, 38 * S
        x1 = right - 2 * S          # outline stays inside the margin
        x0 = x1 - tw - 2 * padx
        y0 = top + (size - h) / 2
        d.rectangle([x0, y0, x1, y0 + h], outline=BLAZE, width=2 * S)
        d.text(((x0 + x1) / 2, y0 + h / 2), label, font=tf, fill=BLAZE, anchor="mm")

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
        d.text((left, sub_top + i * slh), l, font=sf, fill=SOFT, anchor="la")

    # Headline: as big as it can be, shrinking until it fits the space left.
    head_top = top + size + 40 * S
    head_bottom = sub_top - 30 * S
    room = head_bottom - head_top
    text = headline.upper()
    hp = 150
    while True:
        hf = font(BIG, hp)
        hlines = balanced(d, text, hf, width)
        if breaks and len(breaks) == len(hlines) and fits(d, [b.upper() for b in breaks], hf, width):
            hlines = [b.upper() for b in breaks]   # the page's own <br> breaks
        lh = round(hp * 0.92) * S
        cap = hf.getbbox("H", anchor="ls")
        cap_h = cap[3] - cap[1]
        block = lh * (len(hlines) - 1) + cap_h
        if fits(d, hlines, hf, width) and block <= room and len(hlines) <= 4:
            break
        hp -= 2
        assert hp > 40, "headline will not fit: " + headline
    base = head_bottom - lh * (len(hlines) - 1)
    for i, l in enumerate(hlines):
        d.text((left, base + i * lh), l, font=hf, fill=INK, anchor="ls")

    d.rectangle([0, (H - BAR) * S, W * S, H * S], fill=BLAZE)
    return img.resize((W, H), Image.LANCZOS), hp, sp


def main(out):
    out = Path(out)
    DEST.mkdir(parents=True, exist_ok=True)
    free = free_pages(out)
    assert len(free) >= 5, free
    for name in PAGES:
        t = (out / f"{name}.html").read_text(encoding="utf-8")
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        assert len(h1s) == 1, name
        headline = plain(h1s[0])
        breaks = [plain(x) for x in re.split(r"<br\s*/?>", h1s[0])]
        desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', t).group(1))
        og_desc = html.unescape(re.search(r'<meta property="og:description" content="([^"]*)"', t).group(1))
        sub = subhead(desc, og_desc, headline)
        assert "—" not in headline + sub, "em dash in card " + name
        img, hp, sp = card(headline, sub, name in free, breaks)
        img.save(DEST / f"{name}.png", optimize=True)
        print(f"{name}.png  {hp}px  {'FREE ' if name in free else ''}{headline!r} / {sub!r} ({len(sub)})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "out")
