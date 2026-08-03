#!/usr/bin/env python3
"""为电视剧解说生成原创分析卡和字幕卡。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
BG = (18, 20, 27)
WHITE = (246, 242, 232)
MUTED = (184, 184, 181)
GOLD = (214, 164, 76)
RED = (166, 58, 52)
BLUE = (74, 163, 206)
GREEN = (102, 166, 120)


def font_path(bold: bool = False) -> str:
    candidates = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]
        if bold
        else [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("找不到中文字体，请安装微软雅黑或宋体。")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path(bold), size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).split("\n"):
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and draw.textbbox((0, 0), candidate, font=fnt)[2] > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines or [""]


def draw_gradient_background(image: Image.Image, accent: tuple[int, int, int]) -> None:
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            glow = max(0.0, 1.0 - (((x - WIDTH * 0.72) / WIDTH) ** 2 + ((y - HEIGHT * 0.42) / HEIGHT) ** 2) ** 0.5)
            edge = max(0.0, 1.0 - x / WIDTH) * 0.12
            pixels[x, y] = tuple(
                min(255, int(BG[i] + accent[i] * glow * 0.16 + (30 if i == 0 else 0) * edge))
                for i in range(3)
            )


def add_frame(draw: ImageDraw.ImageDraw, accent: tuple[int, int, int]) -> None:
    draw.rectangle((68, 68, WIDTH - 68, HEIGHT - 68), outline=(*accent, 110), width=3)
    draw.line((104, 178, 440, 178), fill=accent, width=8)


def draw_header(draw: ImageDraw.ImageDraw, item: dict, accent: tuple[int, int, int]) -> None:
    tag = str(item.get("tag") or "原创剧情分析")
    draw.text((108, 108), tag, font=font(34, True), fill=accent)
    draw.text((108, 226), str(item.get("title") or ""), font=font(76, True), fill=WHITE)


def draw_analysis(draw: ImageDraw.ImageDraw, item: dict, accent: tuple[int, int, int]) -> None:
    body = str(item.get("body") or "")
    lines = wrap_text(draw, body, font(48), 1450)
    y = 410
    for line in lines:
        draw.text((112, y), line, font=font(48), fill=WHITE)
        y += 76
    for index, bullet in enumerate(item.get("bullets") or []):
        y += 56 if index == 0 else 24
        draw.rounded_rectangle((118, y + 8, 146, y + 36), radius=12, fill=accent)
        for line in wrap_text(draw, str(bullet), font(38), 1370):
            draw.text((178, y), line, font=font(38), fill=MUTED)
            y += 58


def draw_relationship(draw: ImageDraw.ImageDraw, item: dict, accent: tuple[int, int, int]) -> None:
    nodes = item.get("nodes") or []
    x_positions = [180, 760, 1340]
    y = 515
    boxes: list[tuple[int, int, int, int]] = []
    for idx, node in enumerate(nodes[:3]):
        x = x_positions[idx]
        box = (x, y, x + 380, y + 190)
        boxes.append(box)
        color = [RED, GOLD, BLUE][idx]
        draw.rounded_rectangle(box, radius=24, fill=(34, 36, 46), outline=color, width=5)
        draw.text((x + 28, y + 26), str(node.get("name") or ""), font=font(42, True), fill=color)
        for line in wrap_text(draw, str(node.get("role") or ""), font(30), 320):
            draw.text((x + 28, y + 88), line, font=font(30), fill=WHITE)
            y_text = y + 88 + 42 * (wrap_text(draw, str(node.get("role") or ""), font(30), 320).index(line) + 1)
    for left, right in zip(boxes, boxes[1:]):
        x1, y1, x2, y2 = left
        x3, y3, _, _ = right
        cy = (y1 + y2) // 2
        draw.line((x2 + 20, cy, x3 - 30, cy), fill=accent, width=6)
        draw.polygon([(x3 - 30, cy), (x3 - 52, cy - 14), (x3 - 52, cy + 14)], fill=accent)
    if item.get("footer"):
        draw.text((112, 850), str(item["footer"]), font=font(38, True), fill=accent)


def render(item: dict, output: Path) -> None:
    kind = str(item.get("kind") or "analysis")
    accent_name = str(item.get("accent") or "gold").lower()
    accent = {"gold": GOLD, "red": RED, "blue": BLUE, "green": GREEN}.get(accent_name, GOLD)
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw_gradient_background(image, accent)
    draw = ImageDraw.Draw(image)
    add_frame(draw, accent)
    draw_header(draw, item, accent)
    if kind == "relationship":
        draw_relationship(draw, item, accent)
    else:
        draw_analysis(draw, item, accent)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    specs = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    for item in specs:
        item_id = str(item["id"])
        render(item, output_dir / f"{item_id}.png")
        print(output_dir / f"{item_id}.png")


if __name__ == "__main__":
    main()
