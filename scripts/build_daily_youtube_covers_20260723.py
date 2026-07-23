from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
GEN = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f8c7e-155e-75e1-8655-10a3666dba1b")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")

SPECS = [
    {"slug": "transistors-build-cpu", "base": "exec-0c5602ee-c68b-47de-80a0-359403f9aca1.png", "topic": "transistor-cpu", "title": ("几十亿晶体管", "怎样拼成 CPU"), "subtitle": "3D 拆开芯片底层结构", "accent": (76, 212, 255), "female": False, "focus": 0.50},
    {"slug": "apollo-spacecraft-works", "base": "exec-0f737d7a-3570-46a5-b65d-3f2cfc458dd2.png", "topic": "apollo-spacecraft", "title": ("阿波罗飞船", "里面装了什么"), "subtitle": "登月飞船 3D 剖面", "accent": (118, 203, 255), "female": False, "focus": 0.54},
    {"slug": "aegis-combat-system", "base": "exec-29007993-fe96-4618-a53b-5807d5f41abd.png", "topic": "aegis-air-defense", "title": ("宙斯盾系统", "怎样同时拦截"), "subtitle": "雷达、垂发、导弹协同", "accent": (73, 224, 210), "female": False, "focus": 0.42},
    {"slug": "managing-emotions-story-kids", "base": "exec-9d4e4356-6874-4bbf-a1fe-a8e457ee9b36.png", "topic": "parent-child-emotions", "title": ("孩子有情绪", "先别急着劝"), "subtitle": "先帮他把感受说出来", "accent": (118, 229, 193), "female": True, "focus": 0.42},
    {"slug": "being-a-good-listener", "base": "exec-5f629e29-cd27-429e-82fc-9e66e1c23d0c.png", "topic": "relationship-listening", "title": ("让人愿意说", "先学会倾听"), "subtitle": "关系沟通的一个起点", "accent": (118, 229, 193), "female": True, "focus": 0.50},
    {"slug": "practice-self-compassion", "base": "exec-dbc95128-97d3-48fd-b85e-2c7186dd6a67.png", "topic": "self-compassion", "title": ("别急着责怪", "先接住自己"), "subtitle": "练习更友善的内心对话", "accent": (118, 229, 193), "female": True, "focus": 0.36},
]


def crop(image: Image.Image, size: tuple[int, int], focus: float) -> Image.Image:
    tw, th = size
    sw, sh = image.size
    ratio = tw / th
    if sw / sh > ratio:
        nw = int(sh * ratio)
        left = max(0, min(int(sw * focus - nw / 2), sw - nw))
        image = image.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / ratio)
        top = max(0, min((sh - nh) // 2, sh - nh))
        image = image.crop((0, top, sw, top + nh))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def render(base: Image.Image, size: tuple[int, int], spec: dict, vertical: bool) -> Image.Image:
    image = crop(base, size, spec["focus"])
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if vertical:
        panel = (int(w * .045), int(h * .035), int(w * .955), int(h * .35))
        x, y, ts, ss = int(w * .10), int(h * .075), int(w * .10), int(w * .042)
    elif w / h < 1.5:
        panel = (int(w * .025), int(h * .06), int(w * .57), int(h * .80))
        x, y, ts, ss = int(w * .06), int(h * .21), int(h * .09), int(h * .041)
    else:
        panel = (int(w * .025), int(h * .06), int(w * .52), int(h * .74))
        x, y, ts, ss = int(w * .06), int(h * .21), int(h * .09), int(h * .041)
    panel_color = (3, 22, 42, 210) if spec["female"] else (2, 10, 20, 205)
    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=panel_color)
    label = "TA 成长笔记" if spec["female"] else "硬核视界"
    draw.text((x, int(y - ts * .78)), label, font=ImageFont.truetype(str(FONT_BOLD), int(ts * .34)), fill=(255, 255, 255, 145))
    title_font = ImageFont.truetype(str(FONT_BOLD), ts)
    sub_font = ImageFont.truetype(str(FONT_REGULAR), ss)
    for line in spec["title"]:
        draw.text((x, y), line, font=title_font, fill=(255, 249, 235), stroke_width=max(3, int(ts * .047)), stroke_fill=(0, 0, 0))
        y += int(ts * 1.13)
    bar_y = y + int(ts * .04)
    draw.rounded_rectangle((x, bar_y, x + int(w * .22), bar_y + max(8, int(h * .011))), radius=5, fill=spec["accent"])
    draw.text((x, bar_y + int(h * .043)), spec["subtitle"], font=sub_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, overlay).convert("RGB")


for spec in SPECS:
    out = ROOT / "covers" / spec["slug"]
    out.mkdir(parents=True, exist_ok=True)
    base = Image.open(GEN / spec["base"]).convert("RGB")
    base.save(out / f"base-{spec['topic']}.png")
    render(base, (1146, 860), spec, False).save(out / f"{spec['slug']}-cover-4x3.png", quality=95)
    render(base, (1920, 1080), spec, False).save(out / f"{spec['slug']}-cover-16x9.png", quality=95)
    render(base, (1080, 1920), spec, True).save(out / f"{spec['slug']}-cover-9x16.png", quality=95)
