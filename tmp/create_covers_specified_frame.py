from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(r"L:\workspace\yinghe-shijie")
INPUT = ROOT / "tmp" / "cover-frames" / "specified-video-frame.jpg"
OUT = ROOT / "covers"
TMP = ROOT / "tmp" / "cover-frames"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_LATIN = r"C:\Windows\Fonts\Dengb.ttf"


def extract_frame():
    # 直接使用从 MP4 时间码导出的原始视频帧，不使用播放器截图。
    frame = Image.open(INPUT).convert("RGB")
    frame = ImageEnhance.Color(frame).enhance(1.22)
    frame = ImageEnhance.Contrast(frame).enhance(1.12)
    frame = ImageEnhance.Brightness(frame).enhance(1.03)
    frame = ImageEnhance.Sharpness(frame).enhance(1.3)
    frame.save(TMP / "指定帧_原图.jpg", quality=96, subsampling=0)
    return frame


def make_background(frame, size):
    background = ImageOps.fit(frame, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.48))
    background = background.filter(ImageFilter.GaussianBlur(24))
    background = ImageEnhance.Brightness(background).enhance(0.52)
    background = ImageEnhance.Color(background).enhance(0.8)
    return background.convert("RGBA")


def add_centered_frame(canvas, frame):
    width, height = canvas.size
    foreground_h = height
    foreground_w = round(frame.width * foreground_h / frame.height)
    foreground = frame.resize((foreground_w, foreground_h), Image.Resampling.LANCZOS).convert("RGBA")
    x = (width - foreground_w) // 2
    canvas.alpha_composite(foreground, (x, 0))


def crop_vertical(frame, size):
    width, height = size
    target_ratio = width / height
    crop_height = int(frame.width / target_ratio)
    # 保留森林背景、刮刀和托盘，主体中心略偏下。
    top = max(0, min(frame.height - crop_height, int(frame.height * 0.08)))
    crop = frame.crop((0, top, frame.width, top + crop_height))
    return crop.resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def add_gradient(canvas):
    width, height = canvas.size
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pixels = overlay.load()
    start = int(height * 0.57)
    for y in range(start, height):
        p = (y - start) / max(1, height - start - 1)
        alpha = int(20 + 225 * p)
        for x in range(width):
            pixels[x, y] = (8, 4, 2, alpha)
    return Image.alpha_composite(canvas, overlay)


def center_text(draw, width, text, y, font, fill, stroke_width=0, stroke_fill=(0, 0, 0, 255)):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = (width - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def render(frame, filename, size, vertical=False):
    if vertical:
        canvas = crop_vertical(frame, size)
    else:
        canvas = make_background(frame, size)
        add_centered_frame(canvas, frame)
    canvas = add_gradient(canvas)
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    badge_font = ImageFont.truetype(FONT_BOLD, max(32, int(height * 0.043)))
    title_font = ImageFont.truetype(FONT_BOLD, max(72, int(height * 0.135)))
    sub_font = ImageFont.truetype(FONT_REGULAR, max(24, int(height * 0.035)))
    latin_font = ImageFont.truetype(FONT_LATIN, max(21, int(height * 0.025)))

    badge = "荒野美食"
    box = draw.textbbox((0, 0), badge, font=badge_font)
    pad_x = int(height * 0.028)
    pad_y = int(height * 0.012)
    badge_w = box[2] - box[0] + pad_x * 2
    badge_h = box[3] - box[1] + pad_y * 2
    badge_x = int(width * 0.055)
    badge_y = int(height * 0.06)
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=max(8, int(height * 0.014)),
        fill=(211, 50, 27, 245),
        outline=(255, 211, 70, 255),
        width=max(2, int(height * 0.003)),
    )
    draw.text((badge_x + pad_x, badge_y + pad_y - 2), badge, font=badge_font, fill=(255, 248, 220, 255))

    center_text(
        draw,
        width,
        "柴火现烤",
        int(height * 0.68),
        title_font,
        (255, 218, 58, 255),
        stroke_width=max(4, int(height * 0.006)),
        stroke_fill=(24, 9, 2, 255),
    )
    center_text(
        draw,
        width,
        "托盘烤肉 · WOOD-FIRED TRAY KEBAB",
        int(height * 0.84),
        sub_font,
        (255, 245, 207, 255),
        stroke_width=2,
        stroke_fill=(18, 8, 2, 255),
    )
    center_text(
        draw,
        width,
        "COOKED IN THE WILD",
        int(height * 0.915),
        latin_font,
        (255, 180, 48, 255),
        stroke_width=1,
        stroke_fill=(18, 8, 2, 255),
    )

    canvas.convert("RGB").save(OUT / filename, quality=96, subsampling=0)


frame = extract_frame()
render(frame, "木柴火烤盘式烤肉_视频指定帧_16x9.jpg", (1920, 1080), vertical=False)
render(frame, "木柴火烤盘式烤肉_视频指定帧_4x3.jpg", (1440, 1080), vertical=False)
render(frame, "木柴火烤盘式烤肉_视频指定帧_3x4.jpg", (1080, 1440), vertical=True)
