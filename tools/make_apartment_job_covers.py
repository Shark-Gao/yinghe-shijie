#!/usr/bin/env python3
"""根据《公寓黑风暴》海报母版生成三套可复用的竖版封面。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "assets" / "cover_templates" / "the_apartment_job"
DEFAULT_CONFIG = DEFAULT_DIR / "cover_text.json"
DEFAULT_OUTPUT = DEFAULT_DIR / "renders"


def find_font(bold: bool = False) -> str:
    candidates = (
        [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("找不到中文字体，请确认 Windows 已安装微软雅黑或黑体。")


FONT_REGULAR = find_font(False)
FONT_BOLD = find_font(True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def crop_cover(image: Image.Image, size: tuple[int, int], focus_y: float = 0.46) -> Image.Image:
    target_w, target_h = size
    ratio = target_w / target_h
    src_w, src_h = image.size
    src_ratio = src_w / src_h
    if src_ratio > ratio:
        crop_w = int(src_h * ratio)
        left = max(0, min(src_w - crop_w, int((src_w - crop_w) * 0.5)))
        box = (left, 0, left + crop_w, src_h)
    else:
        crop_h = int(src_w / ratio)
        top = int(max(0, min(src_h - crop_h, (src_h - crop_h) * focus_y)))
        box = (0, top, src_w, top + crop_h)
    return image.crop(box).resize(size, Image.Resampling.LANCZOS)


def gradient(size: tuple[int, int], top: tuple[int, int, int, int], bottom: tuple[int, int, int, int], start: float = 0.0, end: float = 1.0) -> Image.Image:
    width, height = size
    layer = Image.new("RGBA", size)
    px = layer.load()
    start_y = int(height * start)
    end_y = max(start_y + 1, int(height * end))
    for y in range(start_y, height):
        t = max(0.0, min(1.0, (y - start_y) / (end_y - start_y)))
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(width):
            px[x, y] = color
    return layer


def horizontal_gradient(size: tuple[int, int], left: tuple[int, int, int, int], right: tuple[int, int, int, int], end: float = 0.5) -> Image.Image:
    width, height = size
    layer = Image.new("RGBA", size)
    px = layer.load()
    end_x = max(1, int(width * end))
    for x in range(width):
        t = max(0.0, min(1.0, x / end_x))
        color = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(4))
        for y in range(height):
            px[x, y] = color
    return layer


def wrap_by_width(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if current and draw.textlength(trial, font=face) > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines or [""]


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, face: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int] | str, stroke: int = 0, stroke_fill: tuple[int, int, int, int] | str = "#000000") -> None:
    draw.text(xy, text, font=face, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, face: ImageFont.FreeTypeFont, max_width: int, fill: tuple[int, int, int, int] | str, line_gap: int = 12, stroke: int = 0, stroke_fill: tuple[int, int, int, int] | str = "#000000") -> int:
    x, y = xy
    lines = wrap_by_width(draw, text, face, max_width)
    box = draw.textbbox((0, 0), "字", font=face)
    line_height = box[3] - box[1] + line_gap
    for line in lines:
        draw_text(draw, (x, y), line, face, fill, stroke, stroke_fill)
        y += line_height
    return y


def make_stage(base: Image.Image, size: tuple[int, int], poster_width_ratio: float = 0.58) -> tuple[Image.Image, Image.Image, int]:
    """用完整海报居中，左右用模糊延展填充，保证男主和原海报标题不被裁掉。"""
    width, height = size
    poster = base.copy().convert("RGB")
    poster_h = height
    poster_w = int(poster_h * poster.width / poster.height)
    poster = poster.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
    background = crop_cover(base, size, 0.43).convert("RGBA")
    background = background.filter(ImageFilter.GaussianBlur(max(10, width // 90)))
    background = ImageEnhance.Brightness(background).enhance(0.38)
    background = ImageEnhance.Color(background).enhance(0.78)
    canvas = background.copy()
    x = (width - poster_w) // 2
    canvas.alpha_composite(poster.convert("RGBA"), (x, 0))
    # 中央海报边缘压暗，文字只放在两侧的延展区或上下安全区。
    canvas.alpha_composite(gradient(size, (6, 11, 24, 150), (6, 11, 24, 0), 0, 0.22))
    return canvas, poster.convert("RGBA"), x


def add_side_panel(canvas: Image.Image, side: str, data: dict, poster_x: int, poster_w: int) -> None:
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    panel_w = max(280, poster_x - 36) if side == "left" else max(280, width - (poster_x + poster_w) - 36)
    x = 54 if side == "left" else poster_x + poster_w + 28
    if side == "right" and x + panel_w > width - 36:
        x = width - panel_w - 36
    # 只保留细线、集数和一句看点，剧名直接使用海报原有标题。
    label_size = max(30, min(42, panel_w // 11))
    topic_size = max(30, min(42, panel_w // 10))
    episode_face = font(label_size, True)
    draw_text(draw, (x, 120), data["episode"], episode_face, "#E9B96B", stroke=1, stroke_fill="#111522")
    episode_width = int(draw.textlength(data["episode"], font=episode_face))
    draw_text(draw, (x + episode_width + 22, 126), data.get("segment", ""), font(max(25, label_size - 3), True), "#F4F1E9", stroke=1, stroke_fill="#111522")
    draw.line((x, 188, x + min(210, panel_w - 16), 188), fill="#D75A3D", width=3)
    draw_wrapped(
        draw,
        (x, 235),
        data["topic"],
        font(topic_size, True),
        panel_w,
        "#F4F1E9",
        line_gap=10,
        stroke=2,
        stroke_fill="#101522",
    )


def render_landscape(base: Image.Image, data: dict) -> Image.Image:
    canvas, _, poster_x = make_stage(base, (1920, 1080), 0.58)
    draw = ImageDraw.Draw(canvas)
    poster_w = int(1080 * base.width / base.height)
    add_side_panel(canvas, "left", data, poster_x, poster_w)
    return canvas.convert("RGB")


def render_four_three(base: Image.Image, data: dict) -> Image.Image:
    canvas, _, poster_x = make_stage(base, (1600, 1200), 0.60)
    draw = ImageDraw.Draw(canvas)
    poster_w = int(1200 * base.width / base.height)
    add_side_panel(canvas, "left", data, poster_x, poster_w)
    return canvas.convert("RGB")


def render_portrait(base: Image.Image, data: dict) -> Image.Image:
    width, height = 1080, 1440
    canvas = crop_cover(base, (width, height), 0.42).convert("RGBA")
    canvas = ImageEnhance.Color(canvas).enhance(0.92)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.06)
    draw = ImageDraw.Draw(canvas)
    # 左上角是海报相对空的区域；不重复叠加剧名，也不覆盖男主。
    canvas.alpha_composite(horizontal_gradient((width, height), (7, 13, 27, 168), (7, 13, 27, 0), 0.43))
    episode_face = font(34, True)
    draw_text(draw, (70, 92), data["episode"], episode_face, "#E9B96B", stroke=1, stroke_fill="#111522")
    episode_width = int(draw.textlength(data["episode"], font=episode_face))
    draw_text(draw, (70 + episode_width + 18, 98), data.get("segment", ""), font(29, True), "#F4F1E9", stroke=1, stroke_fill="#111522")
    draw.line((70, 158, 280, 158), fill="#D75A3D", width=3)
    draw_wrapped(draw, (70, 205), data["topic"], font(46, True), 285, "#F4F1E9", line_gap=8, stroke=2, stroke_fill="#101522")
    return canvas.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poster", type=Path, default=DEFAULT_DIR / "poster_reference_user.png")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--episode", help="覆盖集数文案。")
    parser.add_argument("--segment", help="覆盖故事段落文案。")
    parser.add_argument("--topic", help="覆盖本段主题文案。")
    args = parser.parse_args()
    if not args.poster.is_file():
        raise SystemExit(f"海报文件不存在：{args.poster}")
    data = json.loads(args.config.read_text(encoding="utf-8"))
    if args.episode:
        data["episode"] = args.episode
    if args.segment:
        data["segment"] = args.segment
    if args.topic:
        data["topic"] = args.topic
    args.output_dir.mkdir(parents=True, exist_ok=True)
    base = Image.open(args.poster).convert("RGB")
    renders = [
        ("apartment_job_template_16x9_横版.png", render_landscape),
        ("apartment_job_template_4x3_标准版.png", render_four_three),
        ("apartment_job_template_3x4_竖版.png", render_portrait),
    ]
    for name, renderer in renders:
        renderer(base, data).save(args.output_dir / name, optimize=True)
        print(args.output_dir / name)


if __name__ == "__main__":
    main()
