from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter


ROOT = Path(r"L:\workspace\yinghe-shijie")
FRAME_DIR = ROOT / "tmp" / "cover-frames" / "best"
OUT_DIR = ROOT / "covers"

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_LATIN = r"C:\Windows\Fonts\Dengb.ttf"


def crop_cover(source_path, size, center_y):
    source = Image.open(source_path).convert("RGB")
    width, height = size
    target_ratio = width / height
    crop_height = int(source.width / target_ratio)
    top = max(0, min(source.height - crop_height, int(center_y - crop_height / 2)))
    crop = source.crop((0, top, source.width, top + crop_height))
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    crop = ImageEnhance.Color(crop).enhance(1.28)
    crop = ImageEnhance.Contrast(crop).enhance(1.16)
    crop = ImageEnhance.Brightness(crop).enhance(1.04)
    crop = ImageEnhance.Sharpness(crop).enhance(1.45)
    return crop.convert("RGBA")


def add_bottom_gradient(image, start_ratio=0.54):
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(height * start_ratio)
    for y in range(start, height):
        progress = (y - start) / max(1, height - start - 1)
        alpha = int(12 + 232 * progress)
        for x in range(width):
            pixels[x, y] = (8, 5, 3, alpha)
    return Image.alpha_composite(image, overlay)


def centered(draw, canvas_width, text, y, font, fill, stroke_width=0, stroke_fill=(0, 0, 0, 255)):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = (canvas_width - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def make_cover(source_name, output_name, size, center_y):
    image = crop_cover(FRAME_DIR / source_name, size, center_y)
    image = add_bottom_gradient(image)
    draw = ImageDraw.Draw(image)
    width, height = image.size

    badge_font = ImageFont.truetype(FONT_BOLD, max(34, int(height * 0.045)))
    title_font = ImageFont.truetype(FONT_BOLD, max(70, int(height * 0.125)))
    sub_font = ImageFont.truetype(FONT_REGULAR, max(25, int(height * 0.035)))
    latin_font = ImageFont.truetype(FONT_LATIN, max(24, int(height * 0.027)))

    badge = "野外现烤"
    badge_box = draw.textbbox((0, 0), badge, font=badge_font)
    badge_w = badge_box[2] - badge_box[0] + int(height * 0.055)
    badge_h = badge_box[3] - badge_box[1] + int(height * 0.025)
    badge_x = int(width * 0.055)
    badge_y = int(height * 0.065)
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=max(8, int(height * 0.012)),
        fill=(218, 48, 24, 245),
        outline=(255, 204, 75, 255),
        width=max(2, int(height * 0.003)),
    )
    draw.text(
        (badge_x + int(height * 0.027), badge_y + int(height * 0.008)),
        badge,
        font=badge_font,
        fill=(255, 248, 220, 255),
    )

    title_y = int(height * 0.68)
    centered(
        draw,
        width,
        "柴火烤肉",
        title_y,
        title_font,
        (255, 218, 60, 255),
        stroke_width=max(4, int(height * 0.006)),
        stroke_fill=(25, 10, 3, 255),
    )
    subtitle = "森林溪流边 · WOOD-FIRED KEBAB"
    centered(draw, width, subtitle, int(height * 0.845), sub_font, (255, 245, 207, 255), 2, (20, 10, 4, 255))
    centered(draw, width, "WILDERNESS CUISINE", int(height * 0.91), latin_font, (255, 181, 56, 255), 1, (20, 10, 4, 255))

    output_path = OUT_DIR / output_name
    image.convert("RGB").save(output_path, quality=96, subsampling=0)


make_cover("frame-82.jpg", "木柴火烤盘式烤肉_v2_16x9.jpg", (1920, 1080), 1060)
make_cover("frame-82.jpg", "木柴火烤盘式烤肉_v2_4x3.jpg", (1440, 1080), 1060)
make_cover("frame-82.jpg", "木柴火烤盘式烤肉_v2_3x4.jpg", (1080, 1440), 1080)

