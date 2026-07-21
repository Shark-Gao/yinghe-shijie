from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
GEN = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f7dba-0286-7aa1-a3ad-89418425bfd6")

SPECS = [
    {"slug": "golden-dome-missile-defense", "base": "exec-d5acc593-ea87-40c0-aa06-5fc75c2c11b5.png", "base_name": "base-golden-dome.png", "title": ("金穹系统", "怎么拦导弹"), "subtitle": "导弹防御工程拆解", "accent": (83, 171, 255), "focus_x": 0.70},
    {"slug": "ai-gpu-vs-cpu", "base": "exec-c5b6a84a-1fc4-4229-9cfd-f7af722b2dcd.png", "base_name": "base-ai-gpu.png", "title": ("AI 为什么", "要靠 GPU"), "subtitle": "芯片与并行计算", "accent": (255, 174, 55), "focus_x": 0.70},
    {"slug": "ocean-shipping-works", "base": "exec-71babddd-35db-40da-95f4-abd0b52426ad.png", "base_name": "base-ocean-shipping.png", "title": ("一艘船", "卡住全球"), "subtitle": "航运网络怎样运转", "accent": (77, 184, 222), "focus_x": 0.70},
    {"slug": "manage-big-feelings-together", "base": "exec-fd16cf50-02c4-4de0-9b87-0bdbc084bf50.png", "base_name": "base-big-feelings.png", "title": ("孩子情绪", "上来了怎么办"), "subtitle": "先回应，再引导", "accent": (244, 122, 70), "focus_x": 0.68},
    {"slug": "stay-calm-under-pressure", "base": "exec-5de94a96-df5c-42f0-a48e-3a4eed5c9fb9.png", "base_name": "base-stay-calm.png", "title": ("压力上来", "怎样冷静"), "subtitle": "3步找回节奏", "accent": (105, 187, 235), "focus_x": 0.70},
    {"slug": "how-miscommunication-happens", "base": "exec-c3c4a3c5-d0a7-4f25-98c5-72796b554489.png", "base_name": "base-miscommunication.png", "title": ("话没说错", "为何还是吵"), "subtitle": "沟通误解原理", "accent": (245, 180, 63), "focus_x": 0.69},
]


def crop(image: Image.Image, size: tuple[int, int], focus_x: float) -> Image.Image:
    tw, th = size
    sw, sh = image.size
    ratio = tw / th
    if sw / sh > ratio:
        nw = int(sh * ratio)
        left = max(0, min(int(focus_x * sw - nw / 2), sw - nw))
        image = image.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / ratio)
        top = max(0, min((sh - nh) // 2, sh - nh))
        image = image.crop((0, top, sw, top + nh))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def draw_cover(base: Image.Image, size: tuple[int, int], spec: dict, vertical: bool) -> Image.Image:
    image = crop(base, size, spec["focus_x"])
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if vertical:
        panel = (int(w * .045), int(h * .035), int(w * .955), int(h * .33))
        x, y, title_size, sub_size = int(w * .10), int(h * .075), int(w * .105), int(w * .043)
    elif w / h < 1.5:
        panel = (int(w * .025), int(h * .06), int(w * .57), int(h * .78))
        x, y, title_size, sub_size = int(w * .06), int(h * .22), int(h * .091), int(h * .043)
    else:
        panel = (int(w * .025), int(h * .06), int(w * .50), int(h * .72))
        x, y, title_size, sub_size = int(w * .06), int(h * .22), int(h * .091), int(h * .043)
    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=(2, 10, 20, 196))
    ghost = ImageFont.truetype(str(FONT_BOLD), int(title_size * .66))
    draw.text((x, int(y - title_size * 1.12)), "HARDCORE", font=ghost, fill=(255, 255, 255, 30))
    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    sub_font = ImageFont.truetype(str(FONT_REGULAR), sub_size)
    stroke = max(3, int(title_size * .05))
    for line in spec["title"]:
        draw.text((x, y), line, font=title_font, fill=(255, 249, 235), stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(title_size * 1.14)
    bar_y = y + int(title_size * .06)
    draw.rounded_rectangle((x, bar_y, x + int(w * .22), bar_y + max(8, int(h * .011))), radius=5, fill=spec["accent"])
    draw.text((x, bar_y + int(h * .043)), spec["subtitle"], font=sub_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, overlay).convert("RGB")


for spec in SPECS:
    out = ROOT / "covers" / spec["slug"]
    out.mkdir(parents=True, exist_ok=True)
    base = Image.open(GEN / spec["base"]).convert("RGB")
    base.save(out / spec["base_name"])
    draw_cover(base, (1146, 860), spec, False).save(out / f"{spec['slug']}-cover-4x3.png")
    draw_cover(base, (1920, 1080), spec, False).save(out / f"{spec['slug']}-cover-16x9.png")
    draw_cover(base, (1080, 1920), spec, True).save(out / f"{spec['slug']}-cover-9x16.png")
