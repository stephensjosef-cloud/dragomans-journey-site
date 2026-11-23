#!/usr/bin/env python3
"""Bird League's Then and Now picture (T-43, Nov 23, 2026).

    python3 tools/then_now.py <out.jpg>

Run from _build/. Both sides do the same job, so the change is easy to see: the first
build's sound screen (naming birds by sound, with mock data) beside today's Log screen
(type a bird's name or identify it by sound or photo, then log it). Same look as the
picture it replaced (Nov 9, 2026): 1200 by 1331, warm paper, two phone frames with
rounded corners and a soft shadow, a bold label over a gray line above each.
The labels are Arial (Windows' own, the closest here to the old picture's face); the
picture is pixels, so no font file ships. Needs Pillow.
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent.parent      # _build/
GALLERY = HERE / "assets" / "gallery"
THEN_IMG = GALLERY / "birdleague-then-firstbuild.jpg"       # 501 by 1014, drawn 1:1 as before
NOW_IMG = GALLERY / "birdleague-now-log.jpg"                # 660 by 1349, scaled to the frame's width

W, H = 1200, 1331
PAPER = (243, 239, 230)                                     # #F3EFE6
INK = (26, 27, 45)                                          # the bold label
GRAY = (98, 94, 85)                                         # the line under it
FRAME_W, FRAME_H, TOP, RADIUS = 501, 1014, 222, 28
LEFT_X, RIGHT_X = 67, 633
TEXT_DX = 2                                                 # the old labels sat 2 px in from the frame
CAP_BIG, CAP_SMALL = 91, 139                                # where each label's capitals start
SHADOW_DY, SHADOW_BLUR, SHADOW_ALPHA = 10, 14, 54                # fitted to the old picture
LABELS = (("THEN", "The first build"), ("NOW", "November 2026"))   # T-43, approved Nov 23, 2026


def font(name, size):
    for root in (pathlib.Path("C:/Windows/Fonts"), pathlib.Path("/usr/share/fonts/truetype/msttcorefonts")):
        if (root / name).exists():
            return ImageFont.truetype(str(root / name), size)
    raise SystemExit(f"then_now.py: no {name}")


def screen(path):
    im = Image.open(path).convert("RGB")
    if im.width != FRAME_W:
        im = im.resize((FRAME_W, round(im.height * FRAME_W / im.width)), Image.LANCZOS)
    assert im.height >= FRAME_H, (path, im.size)
    return im.crop((0, 0, FRAME_W, FRAME_H))               # from the bottom only


def rounded(size):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), RADIUS, fill=255)
    return m


def main(out):
    pic = Image.new("RGB", (W, H), PAPER)
    shadow = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shadow)
    for x in (LEFT_X, RIGHT_X):
        sd.rounded_rectangle((x, TOP + SHADOW_DY, x + FRAME_W - 1, TOP + FRAME_H - 1 + SHADOW_DY), RADIUS, fill=SHADOW_ALPHA)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    pic.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow)
    mask = rounded((FRAME_W, FRAME_H))
    for x, path in ((LEFT_X, THEN_IMG), (RIGHT_X, NOW_IMG)):
        pic.paste(screen(path), (x, TOP), mask)
    d = ImageDraw.Draw(pic)
    big, small = font("arialbd.ttf", 37), font("arial.ttf", 26)
    for x, (head, line) in zip((LEFT_X, RIGHT_X), LABELS):
        d.text((x + TEXT_DX, CAP_BIG - big.getbbox("H")[1]), head, font=big, fill=INK)
        d.text((x + TEXT_DX, CAP_SMALL - small.getbbox("H")[1]), line, font=small, fill=GRAY)
    pic.save(out, "JPEG", quality=86, optimize=True, progressive=True)
    print("wrote", out, pathlib.Path(out).stat().st_size, "bytes")


if __name__ == "__main__":
    main(sys.argv[1])
