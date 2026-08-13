from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(r"L:\workspace\yinghe-shijie\covers\tavuklu-guvec-kapama")
SOURCE = ROOT / "frame-video-00-01-27-25.png"
FONT = Path(r"C:\Windows\Fonts\msyhbd.ttc")
TEXT = "荒野 美食"


def crop_to_ratio(image: Image.Image, ratio: float, focus_y: float) -> Image.Image:
    src_w, src_h = image.size
    crop_w = src_w
    crop_h = int(round(src_w / ratio))
    if crop_h > src_h:
        crop_h = src_h
        crop_w = int(round(src_h * ratio))

    center_y = int(round(src_h * focus_y))
    top = center_y - crop_h // 2
    top = max(0, min(top, src_h - crop_h))
    left = max(0, (src_w - crop_w) // 2)
    return image.crop((left, top, left + crop_w, top + crop_h))


def fit_font(text: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > 40:
        font = ImageFont.truetype(str(FONT), size=size)
        box = font.getbbox(text, stroke_width=0)
        if box[2] - box[0] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(str(FONT), size=40)


def add_title(image: Image.Image, title_size: int, banner_top: int, banner_bottom: int) -> Image.Image:
    canvas = image.convert("RGBA")
    width, height = canvas.size
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # A soft black title plate keeps the yellow lettering readable without hiding the scene.
    radius = max(12, int(height * 0.018))
    draw.rounded_rectangle(
        (int(width * 0.055), banner_top, int(width * 0.945), banner_bottom),
        radius=radius,
        fill=(0, 0, 0, 148),
        outline=(255, 202, 58, 45),
        width=max(2, int(height * 0.003)),
    )
    canvas = Image.alpha_composite(canvas, overlay)

    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    font = fit_font(TEXT, int(width * 0.82), title_size)
    bbox = text_draw.textbbox((0, 0), TEXT, font=font, stroke_width=0)
    x = width // 2
    y = (banner_top + banner_bottom) // 2

    # Layered strokes reproduce the warm gold / brown / black thumbnail style.
    text_draw.text(
        (x + int(height * 0.008), y + int(height * 0.012)),
        TEXT,
        anchor="mm",
        font=font,
        fill=(0, 0, 0, 170),
        stroke_width=max(10, int(height * 0.014)),
        stroke_fill=(0, 0, 0, 170),
    )
    text_draw.text(
        (x, y),
        TEXT,
        anchor="mm",
        font=font,
        fill=(255, 212, 72, 255),
        stroke_width=max(12, int(height * 0.015)),
        stroke_fill=(48, 19, 5, 255),
    )
    text_draw.text(
        (x, y - max(1, int(height * 0.002))),
        TEXT,
        anchor="mm",
        font=font,
        fill=(255, 217, 82, 255),
        stroke_width=max(4, int(height * 0.006)),
        stroke_fill=(177, 91, 11, 255),
    )
    return Image.alpha_composite(canvas, text_layer).convert("RGB")


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    specs = [
        ("cover-16x9.png", 1920, 1080, 16 / 9, 0.72, 190, 55, 305),
        ("cover-4x3.png", 1600, 1200, 4 / 3, 0.68, 205, 55, 330),
        ("cover-3x4.png", 1350, 1800, 3 / 4, 0.53, 255, 75, 425),
    ]
    for filename, width, height, ratio, focus_y, title_size, banner_top, banner_bottom in specs:
        cropped = crop_to_ratio(source, ratio, focus_y)
        cover = cropped.resize((width, height), Image.Resampling.LANCZOS)
        cover = add_title(cover, title_size, banner_top, banner_bottom)
        cover.save(ROOT / filename, quality=95, optimize=True)
        print(ROOT / filename)


if __name__ == "__main__":
    main()
