from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
OUT = ROOT / "covers" / "still-face-experiment"
HORIZONTAL = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f72f3-af28-7732-a9dc-3b94fc7a649b\exec-3417b91d-0270-4732-9f3d-dae6e708992c.png")
VERTICAL = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f72f3-af28-7732-a9dc-3b94fc7a649b\exec-02585a4a-6eeb-4449-b3e1-179f61f1c3a9.png")
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def crop_to(image: Image.Image, size: tuple[int, int], x_bias: float = 0.5) -> Image.Image:
    w, h = image.size
    tw, th = size
    if w / h > tw / th:
        cw = int(h * tw / th)
        left = int((w - cw) * x_bias)
        image = image.crop((left, 0, left + cw, h))
    else:
        ch = int(w * th / tw)
        top = int((h - ch) * 0.5)
        image = image.crop((0, top, w, top + ch))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def landscape(size: tuple[int, int]) -> Image.Image:
    image = crop_to(Image.open(HORIZONTAL), size, x_bias=0.5)
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    panel = Image.new("RGBA", size, (0, 0, 0, 0))
    p = ImageDraw.Draw(panel)
    p.rounded_rectangle((int(w * .47), int(h * .09), int(w * .96), int(h * .91)), radius=int(h * .035), fill=(25, 19, 15, 190))
    overlay.alpha_composite(panel.filter(ImageFilter.GaussianBlur(3)))
    title = ImageFont.truetype(FONT_BOLD, int(h * .09))
    subtitle = ImageFont.truetype(FONT_BOLD, int(h * .043))
    x, y = int(w * .53), int(h * .29)
    for line in ("先稳住自己", "再回应孩子"):
        draw.text((x, y), line, font=title, fill=(255, 246, 226), stroke_width=max(3, int(h * .005)), stroke_fill=(40, 25, 16))
        y += int(h * .125)
    draw.rounded_rectangle((x, y + int(h * .02), x + int(w * .17), y + int(h * .033)), radius=int(h * .008), fill=(238, 177, 79))
    draw.text((x, y + int(h * .09)), "育儿，其实也是育己", font=subtitle, fill=(255, 255, 255), stroke_width=2, stroke_fill=(40, 25, 16))
    return Image.alpha_composite(image, overlay).convert("RGB")


def portrait() -> Image.Image:
    size = (1080, 1920)
    image = crop_to(Image.open(VERTICAL), size)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    p = ImageDraw.Draw(overlay)
    p.rounded_rectangle((75, 82, 1005, 650), radius=40, fill=(35, 25, 18, 145))
    draw = ImageDraw.Draw(overlay)
    title = ImageFont.truetype(FONT_BOLD, 112)
    subtitle = ImageFont.truetype(FONT_BOLD, 47)
    for text, y in (("先稳住自己", 180), ("再回应孩子", 325)):
        draw.text((125, y), text, font=title, fill=(255, 246, 226), stroke_width=7, stroke_fill=(45, 27, 15))
    draw.rounded_rectangle((125, 490, 470, 510), radius=10, fill=(238, 177, 79))
    draw.text((125, 550), "育儿，其实也是育己", font=subtitle, fill=(255, 255, 255), stroke_width=3, stroke_fill=(45, 27, 15))
    return Image.alpha_composite(image, overlay).convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    Image.open(HORIZONTAL).save(OUT / "base-parent-child-reconnection.png")
    Image.open(VERTICAL).save(OUT / "base-parent-child-reconnection-vertical.png")
    landscape((1146, 860)).save(OUT / "still-face-experiment-cover-4x3.png", quality=95)
    landscape((1920, 1080)).save(OUT / "still-face-experiment-cover-16x9.png", quality=95)
    portrait().save(OUT / "still-face-experiment-cover-9x16.png", quality=95)


if __name__ == "__main__":
    main()
