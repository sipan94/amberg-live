"""Generate PWA icons, favicon and the default Open Graph image into app/static/img/.

Run once (or after changing colors):  python scripts/make_icons.py
The outputs are committed, so the server never needs to run this.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "img"

# Amberg city colours, softened (see tailwind.config.js)
SLATE = (42, 37, 32)        # flag  #2a2520
HONEY = (227, 169, 43)      # gold-400  #e3a92b
HONEY_LIGHT = (236, 194, 94)  # gold-300
CREAM = (246, 245, 242)     # stone-50  #f6f5f2
MUTED = (203, 198, 189)     # stone-300


def flag(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], radius: float) -> None:
    """The logo mark: a small Amberg flag, dark – gold – dark."""
    x0, y0, x1, y1 = box
    h = (y1 - y0) / 3
    draw.rounded_rectangle(box, radius=radius, fill=SLATE)
    draw.rectangle((x0, y0 + h, x1, y0 + 2 * h), fill=HONEY)


def app_icon(size: int, flag_width: float, rounded: bool = True) -> Image.Image:
    scale = 4  # draw big, shrink for smooth edges
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if rounded:
        draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=CREAM)
    else:
        draw.rectangle((0, 0, s, s), fill=CREAM)
    w = s * flag_width
    h = w * 0.72
    x0, y0 = (s - w) / 2, (s - h) / 2
    flag(draw, (x0, y0, x0 + w, y0 + h), radius=w * 0.14)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def og_image() -> Image.Image:
    """Warm slate card with the flag mark – same mood as the home page hero."""
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), SLATE)
    draw = ImageDraw.Draw(img)
    box = (96, 228, 96 + 168, 228 + 121)
    flag(draw, box, radius=22)
    # Fine outline so the dark flag bands stay visible on the dark card
    draw.rounded_rectangle(box, radius=22, outline=(98, 91, 82), width=3)
    title = ImageFont.load_default(size=100)
    sub = ImageFont.load_default(size=44)
    draw.text((310, 212), "Amberg Live", font=title, fill=CREAM)
    draw.text((314, 330), "Was ist los in Amberg?", font=sub, fill=MUTED)
    for x in range(w):  # slim honey band at the bottom, slightly lighter in the middle
        t = 1 - abs(x / w - 0.5) * 2
        color = tuple(int(HONEY[i] + (HONEY_LIGHT[i] - HONEY[i]) * t) for i in range(3))
        draw.line([(x, h - 12), (x, h)], fill=color)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app_icon(192, 0.62).save(OUT / "icon-192.png")
    app_icon(512, 0.62).save(OUT / "icon-512.png")
    # Maskable: full-bleed background, flag well inside the 80 % safe zone.
    app_icon(512, 0.50, rounded=False).save(OUT / "icon-maskable-512.png")
    app_icon(180, 0.62, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png")
    # Favicon: just the flag, larger, so it stays readable at 16 px.
    app_icon(48, 0.86).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    og_image().save(OUT / "og-default.png", optimize=True)
    for f in sorted(OUT.iterdir()):
        print(f"{f.name:28} {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
