from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
SOURCE = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f72bd-23bc-7841-ae2e-5d02010d8ba9")

SPECS = [
    {
        "slug": "cities-at-sea-aircraft-carriers",
        "topic": "aircraft-carrier-cutaway",
        "landscape": SOURCE / "exec-3dd88483-f9f3-47a2-9d54-e3af2aeaaedf.png",
        "portrait": SOURCE / "exec-094bfa6e-03fa-4d36-8d90-767db8d1c752.png",
        "title": ("航母如何", "变成海上城市"),
        "subtitle": "剖面看懂起降与动力",
        "accent": (255, 91, 63),
    },
    {
        "slug": "liquid-cooling-ai-data-center",
        "topic": "ai-data-center-liquid-cooling",
        "landscape": SOURCE / "exec-aca1c89c-b878-489a-813a-2ed2af89caba.png",
        "portrait": SOURCE / "exec-3c7c9ae8-23a8-44dd-a9a8-253b6b5b0acb.png",
        "title": ("AI算力", "为何用水冷"),
        "subtitle": "液冷系统硬核拆解",
        "accent": (38, 207, 255),
    },
    {
        "slug": "tunnel-boring-machine-3d",
        "topic": "tunnel-boring-machine-cutaway",
        "landscape": SOURCE / "exec-4234a303-5f46-4118-bab6-75c4c7938271.png",
        "portrait": SOURCE / "exec-c4bfe647-9046-4fd2-8a31-fd3b0502b727.png",
        "title": ("巨型盾构机", "怎么掘穿岩层"),
        "subtitle": "3D剖面看懂建隧道",
        "accent": (255, 169, 63),
    },
]


def fit_crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    sw, sh = image.size
    ratio = tw / th
    if sw / sh > ratio:
        nw = int(sh * ratio)
        # Preserve the left-side title-safe area used by all landscape bases.
        left = max(0, min(int((sw - nw) * 0.20), sw - nw))
        image = image.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / ratio)
        top = max(0, (sh - nh) // 2)
        image = image.crop((0, top, sw, top + nh))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def draw_cover(base: Image.Image, size: tuple[int, int], title: tuple[str, str], subtitle: str, accent: tuple[int, int, int], vertical: bool) -> Image.Image:
    image = fit_crop(base, size)
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if vertical:
        panel = (int(w * .055), int(h * .035), int(w * .945), int(h * .335))
        x, y = int(w * .105), int(h * .085)
        title_size, sub_size = int(w * .112), int(w * .045)
    else:
        panel = (int(w * .025), int(h * .055), int(w * .47), int(h * .68))
        x, y = int(w * .065), int(h * .23)
        title_size, sub_size = int(h * .090), int(h * .042)

    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=(2, 9, 18, 198))
    ghost_font = ImageFont.truetype(str(FONT_BOLD), int(title_size * .70))
    draw.text((x, int(y - title_size * 1.13)), "HARDCORE", font=ghost_font, fill=(255, 255, 255, 30))

    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    subtitle_font = ImageFont.truetype(str(FONT_REGULAR), sub_size)
    stroke = max(3, int(title_size * .05))
    for line in title:
        draw.text((x, y), line, font=title_font, fill=(255, 247, 231), stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(title_size * 1.14)
    bar_y = y + int(title_size * .06)
    draw.rounded_rectangle((x, bar_y, x + int(w * .22), bar_y + max(8, int(h * .011))), radius=5, fill=accent)
    draw.text((x, bar_y + int(h * .043)), subtitle, font=subtitle_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, overlay).convert("RGB")


for spec in SPECS:
    out = ROOT / "covers" / spec["slug"]
    out.mkdir(parents=True, exist_ok=True)
    Image.open(spec["landscape"]).save(out / f"base-{spec['topic']}.png")
    Image.open(spec["portrait"]).save(out / f"base-{spec['topic']}-portrait.png")
    draw_cover(Image.open(spec["landscape"]), (1146, 860), spec["title"], spec["subtitle"], spec["accent"], False).save(out / f"{spec['slug']}-cover-4x3.png")
    draw_cover(Image.open(spec["landscape"]), (1920, 1080), spec["title"], spec["subtitle"], spec["accent"], False).save(out / f"{spec['slug']}-cover-16x9.png")
    draw_cover(Image.open(spec["portrait"]), (1080, 1920), spec["title"], spec["subtitle"], spec["accent"], True).save(out / f"{spec['slug']}-cover-9x16.png")
