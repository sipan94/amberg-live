"""Generate the iPhone/Android app icons and splash images into mobile/assets/.

Same logo mark as the website (scripts/make_icons.py): a small Amberg flag, dark – gold – dark,
on the warm cream background. Run after changing colours:  python scripts/make_app_icons.py

Store rules this follows:
- iOS icon: 1024×1024, square, NO transparency (Apple rounds the corners itself).
- Android adaptive icon: 1024×1024 foreground with the mark inside the central safe zone
  (the launcher may cut the outer third as a circle, squircle, …), plus a background layer and
  a one-colour "monochrome" layer for themed icons on Android 13+.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "mobile" / "assets"

SLATE = (42, 37, 32, 255)      # flag  #2a2520
HONEY = (227, 169, 43, 255)    # gold-400  #e3a92b
CREAM = (246, 245, 242, 255)   # stone-50  #f6f5f2
EDGE = (120, 112, 101, 255)    # light edge so dark bands stay visible on dark backgrounds
SIZE = 1024
SCALE = 4  # draw big, shrink for smooth edges


def _flag(draw: ImageDraw.ImageDraw, cx: float, cy: float, width: float, *, edge: bool = False,
          mono: bool = False) -> None:
    h = width * 0.72
    x0, y0, x1, y1 = cx - width / 2, cy - h / 2, cx + width / 2, cy + h / 2
    r = width * 0.14
    band = h / 3
    if mono:
        # One colour only: the two dark bands solid, the gold band left open.
        draw.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=(255, 255, 255, 255))
        draw.rectangle((x0, y0 + band, x1, y0 + 2 * band), fill=(0, 0, 0, 0))
        return
    draw.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=SLATE)
    draw.rectangle((x0, y0 + band, x1, y0 + 2 * band), fill=HONEY)
    if edge:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=r, outline=EDGE, width=int(width * 0.025))


def _canvas(background=None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), background or (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _save(img: Image.Image, name: str, size: int = SIZE, rgb: bool = False) -> None:
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    if rgb:
        out = out.convert("RGB")  # App Store rejects icons with an alpha channel
    out.save(OUT / name, optimize=True)
    print("wrote", OUT / name)


def main() -> None:
    s = SIZE * SCALE
    c = s / 2

    img, d = _canvas(CREAM)  # iOS + generic icon
    _flag(d, c, c, s * 0.56)
    _save(img, "icon.png", rgb=True)

    img, d = _canvas()  # Android adaptive: mark within the central ~60 %
    _flag(d, c, c, s * 0.40)
    _save(img, "android-icon-foreground.png")

    img, _ = _canvas(CREAM)
    _save(img, "android-icon-background.png")

    img, d = _canvas()
    _flag(d, c, c, s * 0.40, mono=True)
    _save(img, "android-icon-monochrome.png")

    img, d = _canvas()  # splash, light mode (cream background comes from app.json)
    _flag(d, c, c, s * 0.62)
    _save(img, "splash-icon.png")

    img, d = _canvas()  # splash, dark mode: light edge so the dark bands don't vanish
    _flag(d, c, c, s * 0.62, edge=True)
    _save(img, "splash-icon-dark.png")

    img, d = _canvas(CREAM)  # web favicon (Expo web preview only)
    _flag(d, c, c, s * 0.70)
    _save(img, "favicon.png", size=48)


if __name__ == "__main__":
    main()
