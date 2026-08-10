from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(r"L:\workspace\yinghe-shijie")
FRAME_DIR = ROOT / "tmp" / "cover-frames" / "stills"
OUT_DIR = ROOT / "covers"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_LATIN = r"C:\Windows\Fonts\Dengb.ttf"


def fit_crop(image: Image.Image, size, center_y):
    width, height = size
    source = image.convert("RGB")
    source_ratio = source.width / source.height
    target_ratio = width / height

    if source_ratio > target_ratio:
        crop_width = int(source.height * target_ratio)
        left = (source.width - crop_width) // 2
        box = (left, 0, left + crop_width, source.height)
    else:
        crop_height = int(source.width / target_ratio)
        top = max(0, min(source.height - crop_height, int(center_y - crop_height / 2)))
        box = (0, top, source.width, top + crop_height)

    return source.crop(box).resize(size, Image.Resampling.LANCZOS)


def add_gradient_panel(image: Image.Image, start_ratio=0.64):
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(height * start_ratio)
    for y in range(start, height):
        progress = (y - start) / max(1, height - start - 1)
        alpha = int(20 + progress * 225)
        for x in range(width):
            pixels[x, y] = (0, 0, 0, alpha)
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def draw_centered_text(draw, canvas_width, text, y, font, fill, stroke_width, stroke_fill):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = (canvas_width - (bbox[2] - bbox[0])) // 2
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def make_cover(source_path, output_name, size, center_y):
    base = Image.open(source_path)
    cover = fit_crop(base, size, center_y)
    cover = add_gradient_panel(cover)
    draw = ImageDraw.Draw(cover)
    width, height = cover.size

    main_size = max(64, int(height * 0.105))
    sub_size = max(28, int(height * 0.035))
    main_font = ImageFont.truetype(FONT_BOLD, main_size)
    sub_font = ImageFont.truetype(FONT_LATIN, sub_size)

    main_y = int(height * 0.735)
    sub_y = int(height * 0.865)
    draw_centered_text(
        draw,
        width,
        "柴火 烤肉",
        main_y,
        main_font,
        (255, 216, 70, 255),
        max(3, int(height * 0.004)),
        (25, 20, 12, 255),
    )
    draw_centered_text(
        draw,
        width,
        "WOOD-FIRED TRAY KEBAB",
        sub_y,
        sub_font,
        (255, 244, 188, 255),
        max(1, int(height * 0.0015)),
        (22, 18, 10, 255),
    )

    output_path = OUT_DIR / output_name
    cover.convert("RGB").save(output_path, quality=95, subsampling=0)
    return output_path


make_cover(
    FRAME_DIR / "frame-90.jpg",
    "木柴火烤盘式烤肉_16x9.jpg",
    (1920, 1080),
    center_y=1300,
)
make_cover(
    FRAME_DIR / "frame-90.jpg",
    "木柴火烤盘式烤肉_4x3.jpg",
    (1440, 1080),
    center_y=1280,
)
make_cover(
    FRAME_DIR / "frame-85.jpg",
    "木柴火烤盘式烤肉_3x4.jpg",
    (1080, 1440),
    center_y=1120,
)
