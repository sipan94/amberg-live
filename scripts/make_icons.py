"""Generate PWA icons, favicon and the default Open Graph image into app/static/img/.

Run once (or after changing colors):  python scripts/make_icons.py
The outputs are committed, so the server never needs to run this.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "img"
# Amberg city colors (Stadtfahne: Schwarz – Gold – Schwarz)
AMBER = (245, 196, 0)       # heraldic gold, tailwind gold-400
AMBER_DARK = (179, 134, 0)  # gold-600
STONE = (13, 12, 11)        # flag black
CREAM = (250, 250, 249)


def logo_mark(size: int, padding: float, background=STONE, rounded=True) -> Image.Image:
    """The site's logo: an amber dot with a soft ring, on a dark tile."""
    scale = 4  # draw big, then shrink = smooth edges
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if rounded:
        draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.22), fill=background)
    else:
        draw.rectangle((0, 0, s, s), fill=background)
    center = s / 2
    ring = s * (0.5 - padding)
    dot = ring * 0.62
    # Semi-transparent ring on its own layer, then blended onto the tile
    # (drawing it directly would replace the black pixels instead of mixing with them).
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((center - ring, center - ring, center + ring, center + ring), fill=(*AMBER, 90))
    img = Image.alpha_composite(img, layer)
    ImageDraw.Draw(img).ellipse((center - dot, center - dot, center + dot, center + dot), fill=AMBER)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def og_image() -> Image.Image:
    """Like the city flag: black – gold – black, with the name on the gold band."""
    w, h = 1200, 630
    band = 150  # height of each black band
    img = Image.new("RGB", (w, h), STONE)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, band, w, h - band), fill=AMBER)
    mark = logo_mark(200, 0.12)
    img.paste(mark, (90, (h - 200) // 2), mark)
    title = ImageFont.load_default(size=104)
    sub = ImageFont.load_default(size=46)
    draw.text((330, 205), "Amberg Live", font=title, fill=STONE)
    draw.text((334, 330), "Was ist los in Amberg?", font=sub, fill=(46, 33, 2))
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logo_mark(192, 0.16).save(OUT / "icon-192.png")
    logo_mark(512, 0.16).save(OUT / "icon-512.png")
    # Maskable: full-bleed background, logo inside the 80 % safe zone.
    logo_mark(512, 0.28, rounded=False).save(OUT / "icon-maskable-512.png")
    logo_mark(180, 0.16, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png")
    logo_mark(48, 0.1).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    og_image().save(OUT / "og-default.png", optimize=True)
    for f in sorted(OUT.iterdir()):
        print(f"{f.name:28} {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
