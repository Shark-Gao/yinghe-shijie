from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"L:\workspace\yinghe-shijie")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")

SPECS = [
    {
        "slug": "lockheed-sr71-blackbird",
        "topic": "sr71-blackbird-cutaway",
        "landscape": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-274dad3f-f31e-4cb9-82be-0251e66f6960.png"),
        "portrait": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-ca54b325-dbd9-4ca8-bfbd-0b3ab42df1ef.png"),
        "title": ("SR-71 为何", "快到发烫"),
        "subtitle": "黑鸟侦察机 3D拆解",
        "accent": (255, 117, 55),
    },
    {
        "slug": "atlas-goes-hands-on",
        "topic": "humanoid-robot-factory",
        "landscape": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-b71cb157-3d5e-4e03-9635-0e33e1a3ea3d.png"),
        "portrait": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-82ea40d0-4ecf-4c16-bf3d-1993b455c873.png"),
        "title": ("人形机器人", "上岗了"),
        "subtitle": "工厂搬运实拍演示",
        "accent": (53, 193, 255),
    },
    {
        "slug": "panama-canal-works",
        "topic": "panama-canal-locks",
        "landscape": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-2e5bda2c-7e28-493d-a9fb-932ccbc8f4f0.png"),
        "portrait": Path(r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f6d97-4a19-7901-9ba0-60e3e0ee3f68\exec-b51620e6-6b4c-413c-a15e-e1b3beb49eed.png"),
        "title": ("一条运河", "改写航线"),
        "subtitle": "全球贸易的咽喉",
        "accent": (58, 221, 180),
    },
]


def crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    sw, sh = image.size
    ratio = tw / th
    if sw / sh > ratio:
        nw = int(sh * ratio)
        left = (sw - nw) // 2
        image = image.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / ratio)
        top = (sh - nh) // 2
        image = image.crop((0, top, sw, top + nh))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def cover(base: Image.Image, size: tuple[int, int], title: tuple[str, str], subtitle: str, accent: tuple[int, int, int], vertical: bool) -> Image.Image:
    image = crop(base, size)
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if vertical:
        panel = (int(w * .06), int(h * .04), int(w * .94), int(h * .35))
        x, y = int(w * .11), int(h * .08)
        title_size, sub_size = int(w * .115), int(w * .048)
    else:
        panel = (int(w * .52), int(h * .06), int(w * .97), int(h * .92))
        x, y = int(w * .56), int(h * .25)
        title_size, sub_size = int(h * .105), int(h * .047)
    draw.rounded_rectangle(panel, radius=int(min(w, h) * .025), fill=(2, 10, 20, 192))
    draw.text((x, int(y - title_size * 1.15)), "HARDCORE", font=ImageFont.truetype(str(FONT_BOLD), int(title_size * .74)), fill=(255, 255, 255, 30))
    title_font = ImageFont.truetype(str(FONT_BOLD), title_size)
    subtitle_font = ImageFont.truetype(str(FONT_REGULAR), sub_size)
    stroke = max(3, int(title_size * .05))
    for line in title:
        draw.text((x, y), line, font=title_font, fill=(255, 247, 231), stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(title_size * 1.14)
    bar_y = y + int(title_size * .08)
    draw.rounded_rectangle((x, bar_y, x + int(w * .23), bar_y + max(8, int(h * .011))), radius=5, fill=accent)
    draw.text((x, bar_y + int(h * .045)), subtitle, font=subtitle_font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return Image.alpha_composite(image, layer).convert("RGB")


for spec in SPECS:
    out = ROOT / "covers" / spec["slug"]
    out.mkdir(parents=True, exist_ok=True)
    Image.open(spec["landscape"]).save(out / f"base-{spec['topic']}.png")
    Image.open(spec["portrait"]).save(out / f"base-{spec['topic']}-portrait.png")
    cover(Image.open(spec["landscape"]), (1146, 860), spec["title"], spec["subtitle"], spec["accent"], False).save(out / f"{spec['slug']}-cover-4x3.png")
    cover(Image.open(spec["landscape"]), (1920, 1080), spec["title"], spec["subtitle"], spec["accent"], False).save(out / f"{spec['slug']}-cover-16x9.png")
    cover(Image.open(spec["portrait"]), (1080, 1920), spec["title"], spec["subtitle"], spec["accent"], True).save(out / f"{spec['slug']}-cover-9x16.png")
