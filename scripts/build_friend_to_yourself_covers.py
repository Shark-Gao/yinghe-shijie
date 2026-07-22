from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
OUT = ROOT / "covers" / "friend-to-yourself"
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")


def crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target = size[0] / size[1]
    source = image.width / image.height
    if source > target:
        width = round(image.height * target)
        image = image.crop((0, 0, width, image.height))
    elif source < target:
        height = round(image.width / target)
        image = image.crop((0, 0, image.width, height))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def draw_cover(base: Image.Image, size: tuple[int, int], vertical: bool) -> Image.Image:
    image = crop(base, size)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    w, h = size
    if vertical:
        panel = (int(w * .05), int(h * .04), int(w * .95), int(h * .31))
        x, y, title_size = int(w * .10), int(h * .075), int(w * .105)
        sub_y, sub_size = int(h * .242), int(w * .043)
        title_lines = ("学会像朋友一样", "对待自己")
    elif w / h < 1.5:
        panel = (int(w * .54), int(h * .07), int(w * .96), int(h * .75))
        x, y, title_size = int(w * .59), int(h * .19), int(h * .088)
        sub_y, sub_size = int(h * .52), int(h * .032)
        title_lines = ("像朋友一样", "对待自己")
    else:
        panel = (int(w * .54), int(h * .07), int(w * .96), int(h * .75))
        x, y, title_size = int(w * .59), int(h * .19), int(h * .093)
        sub_y, sub_size = int(h * .52), int(h * .039)
        title_lines = ("学会像朋友一样", "对待自己")
    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=(3, 22, 42, 207))
    label_font = ImageFont.truetype(str(FONT_BOLD), int(title_size * .33))
    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    sub_font = ImageFont.truetype(str(FONT_REGULAR), sub_size)
    draw.text((x, y - int(title_size * .73)), "TA 成长笔记", font=label_font, fill=(255, 255, 255, 150))
    for index, line in enumerate(title_lines):
        draw.text((x, y + index * int(title_size * 1.12)), line, font=title_font,
                  fill=(255, 249, 235), stroke_width=max(3, int(title_size * .045)), stroke_fill=(0, 0, 0))
    draw.rounded_rectangle((x, sub_y - int(h * .022), x + int(w * .25), sub_y - int(h * .012)), radius=5, fill=(118, 229, 193))
    draw.text((x, sub_y), "把自我责备换成更温柔的对话", font=sub_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, layer).convert("RGB")


def main() -> None:
    landscape = Image.open(OUT / "base-friend-to-yourself-landscape.png").convert("RGB")
    portrait = Image.open(OUT / "base-friend-to-yourself-portrait.png").convert("RGB")
    draw_cover(landscape, (1146, 860), False).save(OUT / "friend-to-yourself-cover-4x3.png", quality=95)
    draw_cover(landscape, (1920, 1080), False).save(OUT / "friend-to-yourself-cover-16x9.png", quality=95)
    draw_cover(portrait, (1080, 1920), True).save(OUT / "friend-to-yourself-cover-9x16.png", quality=95)


if __name__ == "__main__":
    main()
