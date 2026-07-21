from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
GEN = Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f822f-ed25-7cb2-a2af-addd8efae387")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")

SPECS = [
    {
        "slug": "fusion-power-explained",
        "base": "exec-4f60298f-9ecb-4a0b-bd77-93892bbabad9.png",
        "base_name": "base-fusion-tokamak.png",
        "title": ("可控核聚变", "离我们多远"),
        "subtitle": "托卡马克如何困住太阳",
        "accent": (75, 207, 255),
        "focus_x": 0.58,
        "female": False,
    },
    {
        "slug": "robots-learn-to-be-robots",
        "base": "exec-fcec19fe-0cee-457d-ae82-ce704cdd0d40.png",
        "base_name": "base-robot-simulation.png",
        "title": ("机器人", "怎么练成的"),
        "subtitle": "仿真到现实的训练链",
        "accent": (90, 196, 255),
        "focus_x": 0.62,
        "female": False,
    },
    {
        "slug": "patriot-missile-system",
        "base": "exec-356a9f8a-780b-43e4-a323-4bef7a9b4a32.png",
        "base_name": "base-patriot-air-defense.png",
        "title": ("爱国者系统", "怎样拦导弹"),
        "subtitle": "雷达、指挥、拦截三步协同",
        "accent": (119, 225, 234),
        "focus_x": 0.72,
        "female": False,
    },
    {
        "slug": "manage-emotions-ted-ed",
        "base": "exec-94e3b30d-d060-4b2f-b398-a96c389d3b97.png",
        "base_name": "base-emotion-focus.png",
        "title": ("情绪上来时", "先做什么"),
        "subtitle": "把注意力拉回当下",
        "accent": (118, 229, 193),
        "focus_x": 0.48,
        "female": True,
    },
    {
        "slug": "child-thrive-by-five",
        "base": "exec-2c54b0e1-dac8-4ee9-9230-e15c3aeb4a32.png",
        "base_name": "base-parent-child-connection.png",
        "title": ("每天几分钟", "连上孩子"),
        "subtitle": "互动怎样支持早期成长",
        "accent": (118, 229, 193),
        "focus_x": 0.46,
        "female": True,
        "vertical_base": "exec-aec9bb83-6775-4da2-934a-9a2ec214c862.png",
    },
    {
        "slug": "talk-to-a-partner-listen",
        "base": "exec-bc098c61-aa90-49c9-83b0-3bb506d8097f.png",
        "base_name": "base-partner-conversation.png",
        "title": ("让对方愿意", "听你说话"),
        "subtitle": "关系沟通的一个起点",
        "accent": (118, 229, 193),
        "focus_x": 0.48,
        "female": True,
        "vertical_base": "exec-922aebce-d836-413a-98d9-4bb3e6ec0cae.png",
    },
]


def crop(image: Image.Image, size: tuple[int, int], focus_x: float) -> Image.Image:
    tw, th = size
    sw, sh = image.size
    target_ratio = tw / th
    if sw / sh > target_ratio:
        nw = int(sh * target_ratio)
        left = max(0, min(int(focus_x * sw - nw / 2), sw - nw))
        image = image.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / target_ratio)
        top = max(0, min((sh - nh) // 2, sh - nh))
        image = image.crop((0, top, sw, top + nh))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def draw_cover(base: Image.Image, size: tuple[int, int], spec: dict, vertical: bool) -> Image.Image:
    image = crop(base, size, spec["focus_x"])
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if vertical:
        panel = (int(w * .045), int(h * .035), int(w * .955), int(h * .34))
        x, y, title_size, sub_size = int(w * .10), int(h * .075), int(w * .10), int(w * .042)
    elif w / h < 1.5:
        panel = (int(w * .025), int(h * .06), int(w * .57), int(h * .80))
        x, y, title_size, sub_size = int(w * .06), int(h * .21), int(h * .09), int(h * .041)
    else:
        panel = (int(w * .025), int(h * .06), int(w * .52), int(h * .74))
        x, y, title_size, sub_size = int(w * .06), int(h * .21), int(h * .09), int(h * .041)
    panel_color = (3, 22, 42, 204) if spec["female"] else (2, 10, 20, 202)
    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=panel_color)
    label = "TA 成长笔记" if spec["female"] else "硬核视界"
    label_font = ImageFont.truetype(str(FONT_BOLD), int(title_size * .34))
    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    sub_font = ImageFont.truetype(str(FONT_REGULAR), sub_size)
    draw.text((x, int(y - title_size * .78)), label, font=label_font, fill=(255, 255, 255, 130))
    stroke = max(3, int(title_size * .047))
    for line in spec["title"]:
        draw.text((x, y), line, font=title_font, fill=(255, 249, 235), stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(title_size * 1.13)
    bar_y = y + int(title_size * .04)
    draw.rounded_rectangle((x, bar_y, x + int(w * .22), bar_y + max(8, int(h * .011))), radius=5, fill=spec["accent"])
    draw.text((x, bar_y + int(h * .043)), spec["subtitle"], font=sub_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, overlay).convert("RGB")


def main() -> None:
    for spec in SPECS:
        out = ROOT / "covers" / spec["slug"]
        out.mkdir(parents=True, exist_ok=True)
        base = Image.open(GEN / spec["base"]).convert("RGB")
        base.save(out / spec["base_name"])
        draw_cover(base, (1146, 860), spec, False).save(out / f"{spec['slug']}-cover-4x3.png", quality=95)
        draw_cover(base, (1920, 1080), spec, False).save(out / f"{spec['slug']}-cover-16x9.png", quality=95)
        vertical_base = Image.open(GEN / spec["vertical_base"]).convert("RGB") if "vertical_base" in spec else base
        draw_cover(vertical_base, (1080, 1920), spec, True).save(out / f"{spec['slug']}-cover-9x16.png", quality=95)


if __name__ == "__main__":
    main()
