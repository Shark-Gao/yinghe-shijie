from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"L:\workspace\yinghe-shijie")
BASE = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f8757-8405-7951-9875-c754eb31d1d1")
FONT = r"C:\Windows\Fonts\msyhbd.ttc"

ITEMS = [
    ("exec-3796be4c-3e08-4b09-8cff-5e9ec7144634.png", "submarine-missile-launch", "潜艇如何\n水下发射导弹？", "3D 看懂冷发射"),
    ("exec-5d7da1e0-03e8-4205-b3fb-dbd4bf71dc88.png", "ai-data-center-power", "AI 数据中心\n为什么更耗电？", "电力 + 液冷拆解"),
    ("exec-390bf9c1-4c76-4ee7-bdec-914dac529b9c.png", "container-port-logistics", "一艘船进港\n背后有多复杂？", "港口物流一眼看懂"),
    ("exec-3b0f5f90-210c-4387-b543-819a148bf82e.png", "kids-coping-skills", "孩子情绪上来\n先做这几步", "陪他把感受说出来"),
    ("exec-991a1375-35dc-42cd-badb-a035c0c21040.png", "healthy-personal-boundaries", "关系里\n如何设好边界", "不内耗的表达方法"),
    ("exec-160f1230-7e71-4d50-a29b-ef637fcadf27.png", "stop-overthinking-strategies", "别急着压住念头", "6 个方法减少反刍"),
]

def cover_resize(image, size):
    w, h = size
    scale = max(w / image.width, h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - w) // 2)
    top = max(0, (resized.height - h) // 2)
    return resized.crop((left, top, left + w, top + h)).convert("RGBA")

def font(sz):
    return ImageFont.truetype(FONT, sz)

def draw_headline(canvas, title, subtitle, vertical=False):
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size
    if vertical:
        panel = (65, 120, w - 65, 785)
        draw.rounded_rectangle(panel, radius=42, fill=(4, 20, 44, 222))
        f = font(92)
        sf = font(42)
        x, y = 110, 225
        spacing = 12
    else:
        panel = (w * 0.52, 0, w, h)
        draw.rectangle(panel, fill=(4, 18, 39, 190))
        f = font(int(h * 0.105))
        sf = font(int(h * 0.040))
        x, y = int(w * 0.57), int(h * 0.28)
        spacing = 8
    draw.multiline_text((x, y), title, font=f, fill=(250, 252, 255), spacing=spacing,
                        stroke_width=max(2, int(f.size * .025)), stroke_fill=(0, 10, 25))
    bbox = draw.multiline_textbbox((x, y), title, font=f, spacing=spacing)
    sy = bbox[3] + (45 if vertical else 32)
    draw.text((x, sy), subtitle, font=sf, fill=(114, 240, 210),
              stroke_width=1, stroke_fill=(0, 12, 30))

def horizontal(base, size, title, subtitle):
    img = cover_resize(base, size)
    draw_headline(img, title, subtitle, vertical=False)
    return img.convert("RGB")

def vertical(base, title, subtitle):
    # Purpose-built vertical composition: a blurred full-frame color field carries the
    # text while the complete source scene is preserved as a crisp lower visual card.
    bg = cover_resize(base, (1080, 1920)).filter(ImageFilter.GaussianBlur(24))
    veil = Image.new("RGBA", bg.size, (2, 14, 35, 150))
    canvas = Image.alpha_composite(bg, veil)
    card = base.convert("RGBA")
    card.thumbnail((970, 730), Image.Resampling.LANCZOS)
    x = (1080 - card.width) // 2
    y = 990
    shadow = Image.new("RGBA", (card.width + 38, card.height + 38), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((12, 12, shadow.width - 12, shadow.height - 12), 34, fill=(0, 0, 0, 125))
    canvas.alpha_composite(shadow, (x - 19, y - 19))
    canvas.alpha_composite(card, (x, y))
    draw_headline(canvas, title, subtitle, vertical=True)
    return canvas.convert("RGB")

for src, slug, title, subtitle in ITEMS:
    out = ROOT / "covers" / slug
    out.mkdir(parents=True, exist_ok=True)
    base = Image.open(BASE / src)
    base.copy().save(out / f"base-{slug}.png")
    horizontal(base, (1146, 860), title, subtitle).save(out / f"{slug}-cover-4x3.png", quality=95)
    horizontal(base, (1920, 1080), title, subtitle).save(out / f"{slug}-cover-16x9.png", quality=95)
    vertical(base, title, subtitle).save(out / f"{slug}-cover-9x16.png", quality=95)
    print(slug)

# Compact QA sheets make every final cover legible in one visual inspection.
for suffix, label in [("4x3", "4x3"), ("16x9", "16x9"), ("9x16", "9x16")]:
    thumb_size = (382, 286) if suffix == "4x3" else ((426, 240) if suffix == "16x9" else (180, 320))
    cols = 3
    rows = 2
    sheet = Image.new("RGB", (cols * thumb_size[0], rows * thumb_size[1]), (8, 18, 36))
    for i, (_, slug, _, _) in enumerate(ITEMS):
        img = Image.open(ROOT / "covers" / slug / f"{slug}-cover-{suffix}.png").convert("RGB")
        img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        x = (i % cols) * thumb_size[0] + (thumb_size[0] - img.width) // 2
        y = (i // cols) * thumb_size[1] + (thumb_size[1] - img.height) // 2
        sheet.paste(img, (x, y))
    sheet.save(ROOT / "tmp" / f"daily-cover-qa-{label}.jpg", quality=92)
