from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"G:\workspace\yinghe-shijie")
OUT = ROOT / "covers" / "neural-network-deep-learning-chapter-1"
HORIZONTAL_BASE = OUT / "base-neural-network.png"
VERTICAL_BASE = OUT / "base-neural-network-vertical.png"
FONT = Path(r"C:\Windows\Fonts\msyhbd.ttc")


def crop_to(image: Image.Image, size: tuple[int, int], anchor: str) -> Image.Image:
    target_w, target_h = size
    source_w, source_h = image.size
    source_ratio = source_w / source_h
    target_ratio = target_w / target_h
    if source_ratio > target_ratio:
        crop_w = int(source_h * target_ratio)
        left = 0 if anchor == "left" else (source_w - crop_w) // 2
        box = (left, 0, left + crop_w, source_h)
    else:
        crop_h = int(source_w / target_ratio)
        top = 0 if anchor == "top" else (source_h - crop_h) // 2
        box = (0, top, source_w, top + crop_h)
    return image.crop(box).resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def text(draw: ImageDraw.ImageDraw, pos: tuple[int, int], value: str, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int], stroke: int) -> None:
    draw.text(pos, value, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 235))


def horizontal(size: tuple[int, int]) -> Image.Image:
    image = crop_to(Image.open(HORIZONTAL_BASE), size, "left")
    width, height = image.size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    left = int(width * 0.51)
    draw.rounded_rectangle((left, int(height * 0.07), int(width * 0.97), int(height * 0.93)), radius=int(height * 0.035), fill=(2, 10, 26, 203))
    # The narrower 4:3 text panel needs a smaller six-character second line.
    title_size = int(height * (0.085 if width < 1600 else 0.105))
    title_font = ImageFont.truetype(str(FONT), title_size)
    sub_font = ImageFont.truetype(str(FONT), int(height * 0.045))
    ghost_font = ImageFont.truetype(str(FONT), int(height * 0.13))
    x, y = left + int(width * 0.035), int(height * 0.22)
    draw.text((x, int(height * 0.09)), "AI  HARDCORE", font=ghost_font, fill=(255, 255, 255, 35))
    text(draw, (x, y), "神经网络", title_font, (245, 250, 255, 255), max(3, height // 160))
    text(draw, (x, y + int(height * 0.13)), "到底在算什么", title_font, (245, 250, 255, 255), max(3, height // 160))
    line_y = y + int(height * 0.30)
    draw.rounded_rectangle((x, line_y, x + int(width * 0.20), line_y + int(height * 0.014)), radius=5, fill=(25, 212, 255, 255))
    text(draw, (x, line_y + int(height * 0.055)), "AI 看图的底层逻辑", sub_font, (199, 239, 255, 255), 2)
    return Image.alpha_composite(image, overlay).convert("RGB")


def vertical() -> Image.Image:
    image = crop_to(Image.open(VERTICAL_BASE), (1080, 1920), "top")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((64, 80, 1016, 610), radius=34, fill=(2, 10, 26, 156))
    title_font = ImageFont.truetype(str(FONT), 110)
    sub_font = ImageFont.truetype(str(FONT), 45)
    text(draw, (116, 180), "神经网络", title_font, (245, 250, 255, 255), 7)
    text(draw, (116, 315), "到底在算什么", title_font, (245, 250, 255, 255), 7)
    draw.rounded_rectangle((120, 470, 410, 490), radius=8, fill=(25, 212, 255, 255))
    text(draw, (120, 520), "AI 看图的底层逻辑", sub_font, (199, 239, 255, 255), 3)
    return Image.alpha_composite(image, overlay).convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    horizontal((1146, 860)).save(OUT / "neural-network-deep-learning-chapter-1-cover-4x3.png", quality=95)
    horizontal((1920, 1080)).save(OUT / "neural-network-deep-learning-chapter-1-cover-16x9.png", quality=95)
    vertical().save(OUT / "neural-network-deep-learning-chapter-1-cover-9x16.png", quality=95)


if __name__ == "__main__":
    main()
