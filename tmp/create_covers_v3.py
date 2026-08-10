from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

ROOT = Path(r"L:\workspace\yinghe-shijie")
FRAME = ROOT / "tmp" / "cover-frames" / "best" / "frame-84.jpg"
OUT = ROOT / "covers"

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_LATIN = r"C:\Windows\Fonts\Dengb.ttf"


def crop_and_enhance(size, center_y):
    source = Image.open(FRAME).convert("RGB")
    width, height = size
    target_ratio = width / height
    crop_height = int(source.width / target_ratio)
    top = max(0, min(source.height - crop_height, int(center_y - crop_height / 2)))
    image = source.crop((0, top, source.width, top + crop_height)).resize(size, Image.Resampling.LANCZOS)
    image = ImageEnhance.Color(image).enhance(1.34)
    image = ImageEnhance.Contrast(image).enhance(1.18)
    image = ImageEnhance.Brightness(image).enhance(1.04)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    return image.convert("RGBA")


def add_gradient(image):
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(height * 0.58)
    for y in range(start, height):
        p = (y - start) / max(1, height - start - 1)
        alpha = int(12 + 238 * p)
        for x in range(width):
            pixels[x, y] = (10, 5, 2, alpha)
    return Image.alpha_composite(image, overlay)


def center_text(draw, width, text, y, font, fill, stroke_width=0, stroke_fill=(0, 0, 0, 255)):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = (width - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def render(filename, size, center_y):
    image = add_gradient(crop_and_enhance(size, center_y))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    title_font = ImageFont.truetype(FONT_BOLD, max(72, int(height * 0.14)))
    sub_font = ImageFont.truetype(FONT_REGULAR, max(26, int(height * 0.038)))
    latin_font = ImageFont.truetype(FONT_LATIN, max(22, int(height * 0.025)))

    center_text(
        draw,
        width,
        "溪边现烤",
        int(height * 0.68),
        title_font,
        (255, 218, 55, 255),
        stroke_width=max(4, int(height * 0.006)),
        stroke_fill=(25, 9, 2, 255),
    )
    center_text(
        draw,
        width,
        "柴火烤肉 · WOOD-FIRED KEBAB",
        int(height * 0.84),
        sub_font,
        (255, 245, 207, 255),
        stroke_width=2,
        stroke_fill=(18, 8, 2, 255),
    )
    center_text(
        draw,
        width,
        "COOKED IN THE WILD",
        int(height * 0.915),
        latin_font,
        (255, 179, 46, 255),
        stroke_width=1,
        stroke_fill=(18, 8, 2, 255),
    )

    image.convert("RGB").save(OUT / filename, quality=96, subsampling=0)


render("木柴火烤盘式烤肉_v3_16x9.jpg", (1920, 1080), 1120)
render("木柴火烤盘式烤肉_v3_4x3.jpg", (1440, 1080), 1120)
render("木柴火烤盘式烤肉_v3_3x4.jpg", (1080, 1440), 1120)
