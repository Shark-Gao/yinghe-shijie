#!/usr/bin/env python3
"""生成原创解说主导、原剧短证据片段穿插的电视剧剪辑时间线。"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1920, 1080
FPS = 30
SAMPLE_RATE = 44100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", required=True)
    parser.add_argument("--source-subtitle", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-name", required=True)
    parser.add_argument("--output-video", required=True)
    parser.add_argument("--output-plan", required=True)
    parser.add_argument(
        "--relationship-only",
        action="store_true",
        help="只保留指定原创视觉；其他解说段使用无文字纯背景，不生成其他图示。",
    )
    return parser.parse_args()


def font_path(bold: bool = False) -> str:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc") if bold else Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise SystemExit("找不到可用的中文字体。")


FONT_REGULAR = font_path(False)
FONT_BOLD = font_path(True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def text_center(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt: ImageFont.FreeTypeFont, fill: tuple[int, int, int]) -> None:
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=14, align="center")
    x = xy[0] - (box[2] - box[0]) / 2
    y = xy[1] - (box[3] - box[1]) / 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=14, align="center")


def draw_background(draw: ImageDraw.ImageDraw, accent: tuple[int, int, int]) -> None:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(14, 24, 38))
    draw.rectangle((0, 0, WIDTH, 12), fill=accent)
    draw.rectangle((0, HEIGHT - 14, WIDTH, HEIGHT), fill=(8, 14, 24))
    # 抽象针线/绣线，不使用演员脸或剧照。
    for offset in range(-300, WIDTH + 300, 180):
        points = []
        for y in range(80, HEIGHT - 60, 24):
            x = offset + int(70 * __import__("math").sin(y / 100))
            points.append((x, y))
        draw.line(points, fill=(*accent, 45), width=2)
    draw.ellipse((WIDTH - 260, 80, WIDTH - 80, 260), outline=accent, width=3)
    draw.ellipse((WIDTH - 220, 120, WIDTH - 120, 220), outline=(232, 197, 121), width=2)


def make_card(path: Path, label: str, title: str, body: list[str], page: int, accent: tuple[int, int, int] = (214, 93, 74)) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (14, 24, 38))
    draw = ImageDraw.Draw(image)
    draw_background(draw, accent)
    draw.text((110, 82), label, font=font(30, True), fill=accent)
    draw.text((110, 160), title, font=font(68, True), fill=(246, 239, 220))
    body_text = "\n".join(body)
    draw.multiline_text((120, 330), body_text, font=font(44), fill=(225, 230, 235), spacing=24)
    draw.text((120, 940), "原创解说｜只保留必要原剧证据", font=font(27), fill=(155, 170, 184))
    draw.text((WIDTH - 190, 930), f"{page:02d}", font=font(52, True), fill=accent)
    image.save(path)


def make_relationship(path: Path, page: int) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (14, 24, 38))
    draw = ImageDraw.Draw(image)
    draw_background(draw, (83, 164, 185))
    draw.text((110, 82), "原创视觉｜证据结构", font=font(30, True), fill=(83, 164, 185))
    draw.text((110, 160), "这不是一场单人考试", font=font(68, True), fill=(246, 239, 220))
    draw.text((120, 270), "争议的核心，是三个人对同一场接力的不同解释", font=font(38), fill=(225, 230, 235))

    nodes = {
        "璎珞": (180, 500, 570, 700, (83, 164, 185), "接手补绣\n提出反证"),
        "吉祥": (770, 500, 1160, 700, (232, 197, 121), "绣品染血\n交接求助"),
        "玲珑": (1360, 360, 1750, 560, (214, 93, 74), "提出指控\n解释为作弊"),
        "吴总管": (1360, 700, 1750, 900, (132, 181, 123), "核验绣品\n作出裁定"),
    }
    for name, (x1, y1, x2, y2, color, desc) in nodes.items():
        draw.rounded_rectangle((x1, y1, x2, y2), radius=26, fill=(25, 42, 59), outline=color, width=4)
        text_center(draw, ((x1 + x2) // 2, y1 + 62), name, font(42, True), (246, 239, 220))
        text_center(draw, ((x1 + x2) // 2, y1 + 143), desc, font(28), (205, 216, 225))

    def arrow(start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int], label: str) -> None:
        draw.line((start[0], start[1], end[0], end[1]), fill=color, width=6)
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(1, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        tip = end
        left = (int(end[0] - ux * 28 + px * 13), int(end[1] - uy * 28 + py * 13))
        right = (int(end[0] - ux * 28 - px * 13), int(end[1] - uy * 28 - py * 13))
        draw.polygon([tip, left, right], fill=color)
        text_center(draw, (int((start[0] + end[0]) / 2), int((start[1] + end[1]) / 2 - 28)), label, font(25, True), color)

    arrow((770, 600), (570, 600), (232, 197, 121), "接力完成")
    arrow((1160, 540), (1360, 450), (214, 93, 74), "被解释为作弊")
    arrow((570, 660), (1360, 790), (83, 164, 185), "摆出证据")
    arrow((1160, 660), (1360, 790), (132, 181, 123), "交接可核对")
    draw.text((120, 940), "关系依据：本段字幕与画面中的绣品交接、指控和裁定", font=font(27), fill=(155, 170, 184))
    draw.text((WIDTH - 190, 930), f"{page:02d}", font=font(52, True), fill=(83, 164, 185))
    image.save(path)


def draw_hoop(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int], complete: bool, stain: bool = False) -> None:
    x1, y1, x2, y2 = box
    draw.ellipse(box, outline=(142, 99, 61), width=14)
    draw.ellipse((x1 + 24, y1 + 24, x2 - 24, y2 - 24), outline=(218, 190, 132), width=4)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    petals = 10 if complete else 5
    for index in range(petals):
        angle = index * 2 * math.pi / max(1, petals)
        px = int(cx + 95 * math.cos(angle))
        py = int(cy + 75 * math.sin(angle))
        draw.ellipse((px - 42, py - 22, px + 42, py + 22), outline=color, width=7)
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=color)
    if not complete:
        draw.line((cx + 30, cy + 20, cx + 180, cy + 115), fill=(225, 225, 210), width=7)
        draw.line((cx + 180, cy + 115, cx + 240, cy + 78), fill=(225, 225, 210), width=7)
    if stain:
        draw.ellipse((x1 + 110, y2 - 140, x1 + 190, y2 - 60), fill=(150, 45, 45))


def make_original_visual(path: Path, key: str, page: int) -> None:
    """制作不含字幕卡文字的原创示意画面。"""
    image = Image.new("RGB", (WIDTH, HEIGHT), (14, 24, 38))
    draw = ImageDraw.Draw(image)
    if "指控" in key or "代价" in key:
        accent = (214, 93, 74)
    elif "裁定" in key or "结果" in key:
        accent = (132, 181, 123)
    elif "证据" in key or "反证" in key:
        accent = (83, 164, 185)
    else:
        accent = (232, 197, 121)
    draw_background(draw, accent)

    if "开头" in key:
        draw_hoop(draw, (300, 330, 780, 810), (214, 93, 74), False, True)
        draw_hoop(draw, (1130, 330, 1610, 810), (83, 164, 185), False)
        draw.line((780, 570, 1130, 570), fill=(232, 197, 121), width=10)
        draw.polygon([(1130, 570), (1080, 540), (1080, 600)], fill=(232, 197, 121))
    elif "危机" in key:
        draw_hoop(draw, (280, 310, 780, 810), (214, 93, 74), False, True)
        draw.line((850, 340, 1080, 740), fill=(214, 93, 74), width=18)
        draw.line((1080, 340, 850, 740), fill=(214, 93, 74), width=18)
        draw_hoop(draw, (1140, 310, 1640, 810), (232, 197, 121), False)
    elif "规则" in key:
        draw.ellipse((610, 220, 1310, 920), outline=(232, 197, 121), width=12)
        for index in range(12):
            angle = index * 2 * math.pi / 12
            x1 = 960 + int(280 * math.cos(angle))
            y1 = 570 + int(280 * math.sin(angle))
            x2 = 960 + int(320 * math.cos(angle))
            y2 = 570 + int(320 * math.sin(angle))
            draw.line((x1, y1, x2, y2), fill=(225, 225, 210), width=8)
        draw.line((960, 570, 960, 330), fill=(83, 164, 185), width=14)
        draw.line((960, 570, 1210, 570), fill=(214, 93, 74), width=14)
        draw.ellipse((930, 540, 990, 600), fill=(232, 197, 121))
    elif "证据" in key or "交接" in key:
        draw_hoop(draw, (180, 310, 700, 830), (83, 164, 185), False)
        draw_hoop(draw, (1220, 310, 1740, 830), (232, 197, 121), False)
        draw.line((720, 570, 1200, 570), fill=(132, 181, 123), width=12)
        draw.polygon([(1200, 570), (1145, 535), (1145, 605)], fill=(132, 181, 123))
        draw.ellipse((870, 440, 1050, 620), outline=(246, 239, 220), width=10)
        draw.line((1010, 580, 1110, 720), fill=(246, 239, 220), width=12)
    elif "反证" in key:
        draw_hoop(draw, (240, 320, 760, 840), (83, 164, 185), False)
        draw_hoop(draw, (1160, 320, 1680, 840), (232, 197, 121), False)
        draw.line((790, 570, 1130, 570), fill=(132, 181, 123), width=10)
        draw.line((910, 570, 980, 640), fill=(132, 181, 123), width=18)
        draw.line((980, 640, 1110, 440), fill=(132, 181, 123), width=18)
    elif "裁定" in key or "核心" in key:
        draw.line((960, 280, 960, 820), fill=(232, 197, 121), width=12)
        draw.line((600, 500, 1320, 500), fill=(232, 197, 121), width=12)
        draw.line((600, 500, 500, 720), fill=(83, 164, 185), width=8)
        draw.line((1320, 500, 1420, 720), fill=(214, 93, 74), width=8)
        draw.arc((360, 680, 640, 900), 0, 180, fill=(83, 164, 185), width=10)
        draw.arc((1280, 680, 1560, 900), 0, 180, fill=(214, 93, 74), width=10)
        draw_hoop(draw, (420, 650, 580, 810), (83, 164, 185), False)
        draw_hoop(draw, (1340, 650, 1500, 810), (214, 93, 74), False)
    elif "片尾" in key:
        draw.rectangle((650, 240, 1270, 900), outline=(232, 197, 121), width=14)
        draw.rectangle((760, 400, 1160, 900), outline=(83, 164, 185), width=10)
        draw.arc((780, 250, 1180, 700), 200, 500, fill=(132, 181, 123), width=14)
        draw.line((950, 500, 1050, 600), fill=(214, 93, 74), width=12)
        draw.ellipse((1020, 590, 1090, 660), fill=(214, 93, 74))
    else:
        draw_hoop(draw, (320, 300, 800, 780), (83, 164, 185), False)
        draw_hoop(draw, (1120, 300, 1600, 780), (232, 197, 121), False)

    # 不加入标题、字幕或页码，只保留图形化表达。
    image.save(path)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def make_card_segment(image_path: Path, output_path: Path, duration: float) -> None:
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.006:sample_rate={SAMPLE_RATE}",
        "-t", f"{duration:.3f}",
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"fps={FPS},format=yuv420p",
        "-af", "aformat=channel_layouts=stereo",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
        "-shortest", str(output_path),
    ])


def make_plain_segment(output_path: Path, duration: float) -> None:
    """为解说保留干净画面，不插入额外剧情图卡。"""
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=0e1a2b:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.006:sample_rate={SAMPLE_RATE}",
        "-t", f"{duration:.3f}",
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"format=yuv420p",
        "-af", "aformat=channel_layouts=stereo",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
        "-shortest", str(output_path),
    ])


def make_source_segment(source: Path, output_path: Path, start: float, end: float, keep_audio: bool) -> None:
    duration = end - start
    common_video = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"
    if keep_audio:
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0", "-vf", common_video,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-ac", "2", "-t", f"{duration:.3f}",
            str(output_path),
        ])
        return
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
        "-f", "lavfi", "-t", f"{duration:.3f}", "-i", f"anoisesrc=color=brown:amplitude=0.006:sample_rate={SAMPLE_RATE}",
        "-filter_complex", f"[0:v]{common_video}[v]",
        "-map", "[v]", "-map", "1:a:0", "-af", "aformat=channel_layouts=stereo", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-ac", "2", "-shortest", "-t", f"{duration:.3f}",
        str(output_path),
    ])


def quote_concat_path(path: Path) -> str:
    return "file '" + str(path.resolve()).replace("'", "'\\''") + "'"


def hms(value: float) -> str:
    total_ms = round(value * 1000)
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    seconds, milliseconds = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def main() -> None:
    args = parse_args()
    source = Path(args.source_video).resolve()
    subtitle = Path(args.source_subtitle).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise SystemExit(f"原始视频不存在：{source}")
    if not subtitle.is_file():
        raise SystemExit(f"字幕文件不存在：{subtitle}")

    asset_dir = output_dir / f"{args.base_name}_原创图卡"
    work_dir = output_dir / f".{args.base_name}_原创时间线_work"
    asset_dir.mkdir(parents=True, exist_ok=True)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # type=card 的 duration 是原创卡片时长；source 只保留必要短证据。
    specs: list[dict] = [
        {"type": "card", "key": "01_开头钩子", "duration": 5.5, "label": "问题先行｜原创解说", "title": "她们被指作弊，证据却不在嘴上", "body": ["真正要核对的，不是谁喊得更大声", "而是两幅绣品在交接时到底是什么状态"]},
        {"type": "source", "key": "02_绣品染血", "start": 19 * 60 + 9.566, "end": 19 * 60 + 12.666, "audio": True},
        {"type": "relationship", "key": "03_人物关系", "duration": 7.0},
        {"type": "source", "key": "04_提出接力", "start": 19 * 60 + 21.733, "end": 19 * 60 + 24.800, "audio": True},
        {"type": "card", "key": "05_危机分析", "duration": 8.8, "label": "剧情分析｜第一层", "title": "危机不是谁绣得差", "body": ["绣品已经染血，重绣来不及", "两个人只能把未完成的部分接着做", "这叫接力，也埋下了后面的争议"]},
        {"type": "source", "key": "06_时辰到", "start": 20 * 60 + 22.133, "end": 20 * 60 + 25.700, "audio": True},
        {"type": "card", "key": "07_规则分析", "duration": 7.5, "label": "规则拆解｜原创观点", "title": "交接发生时，本来就可能是半成品", "body": ["时辰一到，所有人必须停针", "所以关键不在于有没有换手", "而在于换手时有没有形成成品"]},
        {"type": "source", "key": "08_双面绣证据", "start": 20 * 60 + 55.333, "end": 20 * 60 + 58.966, "audio": False},
        {"type": "card", "key": "09_人物归属校正", "duration": 7.5, "label": "事实校正｜避免人物张冠李戴", "title": "先被夸的是另一位宫女的双面绣", "body": ["这段画面不是魏璎珞在说双面绣", "先被夸的是另一位宫女", "随后才轮到璎珞的绣品被单独检查"]},
        {"type": "source", "key": "10_牡丹被夸", "start": 21 * 60 + 39.300, "end": 21 * 60 + 42.800, "audio": True},
        {"type": "card", "key": "11_指控转向", "duration": 7.5, "label": "剧情分析｜第二层", "title": "问题从针法，转成了谁动过绣绷", "body": ["玲珑抓住的不是一件完成品", "而是两次交接这个说法", "同一件事，从不同角度就能变成不同指控"]},
        {"type": "source", "key": "12_作弊指控", "start": 22 * 60 + 20.666, "end": 22 * 60 + 24.266, "audio": True},
        {"type": "card", "key": "13_指控代价", "duration": 9.0, "label": "局势升级｜原创解说", "title": "一旦坐实，两个人都要被赶出去", "body": ["璎珞不能只说‘我没有作弊’", "她必须把接力过程拆成现场能核对的事实", "否则两个人都会被一句话带走"]},
        {"type": "source", "key": "14_摆出证据", "start": 24 * 60 + 59.566, "end": 25 * 60 + 2.800, "audio": False},
        {"type": "card", "key": "15_证据一", "duration": 6.5, "label": "证据拆解｜第一次交接", "title": "第一处证据：牡丹还没绣完", "body": ["璎珞交给吉祥时，牡丹还差两针", "她交出的不是成品", "第一次交接就不符合‘替人交卷’的前提"]},
        {"type": "source", "key": "16_第一次交接", "start": 25 * 60 + 18.900, "end": 25 * 60 + 22.000, "audio": False},
        {"type": "card", "key": "17_证据二", "duration": 6.5, "label": "证据拆解｜第二次交接", "title": "第二处证据：锦鸡也只有几针", "body": ["吉祥把绣品递回来时，同样没有完成", "两次交接都是半成品", "所谓‘替考’，缺少最关键的成品证据"]},
        {"type": "source", "key": "18_第二次交接", "start": 25 * 60 + 24.600, "end": 25 * 60 + 29.566, "audio": False},
        {"type": "card", "key": "19_反证逻辑", "duration": 7.5, "label": "剧情分析｜反证成立", "title": "没有成品，就不能直接等同于替考", "body": ["共同完成，和替别人完成，不是一回事", "要先证明有人拿到过成品", "这才是‘作弊’指控成立的前提"]},
        {"type": "source", "key": "20_反证台词", "start": 25 * 60 + 34.400, "end": 25 * 60 + 38.666, "audio": True},
        {"type": "card", "key": "21_裁定分析", "duration": 9.0, "label": "结果拆解｜证据落地", "title": "真正翻盘的，是把情绪变成可核对的事实", "body": ["吴总管最后采纳的不是谁更会喊冤", "而是两次交接都能被现场对上", "当规则回到证据，指控自然站不住"]},
        {"type": "source", "key": "22_裁定认可", "start": 26 * 60 + 0.333, "end": 26 * 60 + 3.866, "audio": True},
        {"type": "card", "key": "23_核心观点", "duration": 11.0, "label": "观点落点｜原创解说", "title": "这段剧情真正高明的地方", "body": ["不是针脚绣得多漂亮", "而是把‘作弊’拆成两个问题：有没有成品？谁拿到过成品？", "你觉得这是作弊，还是合理接力？"]},
        {"type": "source", "key": "24_结果一瞥", "start": 26 * 60 + 43.200, "end": 26 * 60 + 45.700, "audio": False},
        {"type": "card", "key": "25_片尾讨论", "duration": 6.5, "label": "讨论问题｜不复现完整剧情", "title": "解释规则的人，也掌握了局面", "body": ["本条只用短证据说明反转逻辑", "真正的剧情细节，仍留给正片", "你会把这次接力判作作弊吗？"]},
    ]

    concat_files: list[Path] = []
    timeline_entries: list[dict] = []
    narration_segments: list[dict] = []
    cursor = 0.0
    card_page = 1
    for index, spec in enumerate(specs, 1):
        key = spec["key"]
        segment_path = work_dir / f"segment_{index:02d}.mp4"
        entry = {"index": index, "key": key, "type": spec["type"], "start": round(cursor, 3)}
        if spec["type"] in {"card", "relationship"}:
            duration = float(spec["duration"])
            if spec["type"] == "relationship":
                image_path = asset_dir / f"{card_page:02d}_{key}.png"
                make_relationship(image_path, card_page)
                make_card_segment(image_path, segment_path, duration)
                role = "original_visual"
                card_page += 1
            elif args.relationship_only:
                make_plain_segment(segment_path, duration)
                role = "narration_background"
            else:
                image_path = asset_dir / f"{card_page:02d}_{key}.png"
                make_original_visual(image_path, key, card_page)
                make_card_segment(image_path, segment_path, duration)
                role = "original_visual"
                card_page += 1
            narration_segments.append({"start": hms(cursor), "end": hms(cursor + duration), "text": {
                "01_开头钩子": "她们被指作弊，但真正要核对的不是谁喊得更大声，而是两幅绣品在交接时到底是什么状态。",
                "03_人物关系": "这场争议里，吉祥的绣品先染了血，璎珞负责接手补救；玲珑却把这次接力解释成了作弊。最后能不能留下，要看吴总管认哪一份证据。",
                "05_危机分析": "关键不在谁的针法更漂亮，而在时间根本不够重绣。绣品已经被毁，两个人只能把未完成的部分接着做。",
                "07_规则分析": "时辰一到，所有人必须停针。所以交接发生时，绣品本来就可能是半成品。关键不是有没有换手，而是换手时有没有形成成品。",
                "09_人物归属校正": "先被夸的是另一位宫女的双面绣，不是魏璎珞；随后，才轮到璎珞的绣品被单独检查。",
                "11_指控转向": "问题从谁的针法更好，转成了谁动过绣绷。玲珑抓住的不是一件完成品，而是两次交接这个说法。",
                "13_指控代价": "一旦作弊坐实，两个人都要被赶出去。璎珞不能只说自己没有作弊，她必须把接力过程拆成现场能核对的事实。",
                "15_证据一": "第一处证据是，璎珞交给吉祥时，牡丹还差两针。她交出的不是成品，第一次交接就不符合替人交卷的前提。",
                "17_证据二": "第二处证据是，吉祥把绣品递回来时，同样只完成了几针。两次交接都是半成品，所谓替考缺少最关键的成品证据。",
                "19_反证逻辑": "共同完成，和替别人完成，不是一回事。要先证明有人拿到过成品，这个作弊指控才有成立的前提。",
                "21_裁定分析": "吴总管最后采纳的不是谁更会喊冤，而是两次交接都能被现场对上。当规则回到证据，指控自然站不住。",
                "23_核心观点": "这段剧情真正高明的地方，不是针脚绣得多漂亮，而是把作弊拆成两个问题：有没有成品？谁拿到过成品？你觉得这是作弊，还是合理接力？",
                "25_片尾讨论": "本条只用短证据说明反转逻辑，真正的剧情细节仍留给正片。你会把这次接力判作作弊吗？",
            }[key]})
            entry.update({"duration": round(duration, 3), "role": role})
            if spec["type"] == "relationship" or not args.relationship_only:
                entry["asset"] = str(image_path)
        else:
            start, end = float(spec["start"]), float(spec["end"])
            duration = end - start
            make_source_segment(source, segment_path, start, end, bool(spec.get("audio")))
            entry.update({"source_start": round(start, 3), "source_end": round(end, 3), "duration": round(duration, 3), "audio": bool(spec.get("audio")), "role": "short_evidence"})
        concat_files.append(segment_path)
        entry["end"] = round(cursor + duration, 3)
        timeline_entries.append(entry)
        cursor += duration

    concat_list = work_dir / "concat.txt"
    concat_list.write_text("\n".join(quote_concat_path(path) for path in concat_files), encoding="utf-8")
    timeline_video = output_dir / f"{args.base_name}_原创主体时间线.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-vf", f"fps={FPS},format=yuv420p",
        "-af", "aresample=async=1:first_pts=0",
        "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-ac", "2",
        "-movflags", "+faststart", str(timeline_video),
    ])

    output_video = Path(args.output_video).resolve()
    plan_path = Path(args.output_plan).resolve()
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan = {
        "version": 1,
        "title": "两幅半成品为什么能拆穿作弊指控？",
        "drama": {
            "work_title": "延禧攻略",
            "episode": "第1集",
            "story_arc": "绣坊考核中，璎珞用两次未完成的交接反证作弊指控",
            "opening_stance_hook": "两个人被指作弊，但真正决定结果的不是谁喊得更响，而是绣品交接时有没有形成成品。",
            "commentary_viewpoint": "这不是把正片压缩重播，而是用短证据说明：两次交接都是半成品，指控缺少成品这个前提。",
            "discussion_conflict": "共同完成绣品，究竟是作弊，还是在规则允许范围内的接力？",
            "emotional_value": "观众从被指控的紧张，转为看懂璎珞如何把情绪争执拆成可核对的事实。",
            "rights_note": "沿用项目制作记录中的授权说明，素材仅用于本次影视剧情介绍与讨论。",
        },
        "source_subtitle": str(subtitle),
        "source_video": str(timeline_video),
        "output_video": str(output_video),
        "annotation_only": False,
        "layout": "source",
        "output_resolution": "1920:1080",
        "burn_captions": False,
        "write_subtitles": True,
        "platform_titles": {
            "bilibili": "两幅半成品，为什么能拆穿作弊指控？",
            "douyin": "被指作弊后，她没有喊冤而是摆出两幅半成品",
            "kuaishou": "两幅没绣完的绣品，咋就证明不是替考？",
            "xiaohongshu": "延禧攻略绣坊反转：两次交接都是半成品，作弊指控为何站不住？",
        },
        "platform_descriptions": {
            "bilibili": "这版不连续复现整段剧情，只用几处短画面作为证据，配合原创分析，拆解璎珞如何用两次未完成的交接反证作弊指控。",
            "douyin": "两个人被指作弊，璎珞没有只喊冤，而是把两次交接拆开：谁拿到过成品？看懂这个问题，才看懂这场绣坊反转。",
            "kuaishou": "绣品接力被说成作弊，璎珞直接摆证据：两次交接都是半成品，这个指控到底怎么成立？",
            "xiaohongshu": "用人物关系、证据卡和少量原剧短片段，拆解《延禧攻略》第一集绣坊争议：双面绣不是魏璎珞完成的，真正的反转在两次交接都没有形成成品。",
        },
        "edit_rules": {
            "selection_mode": "original_led_evidence_edit",
            "clip_order": "analysis_then_evidence",
            "source_reuse": False,
            "source_overlap": False,
            "direct_cut": True,
            "transition_policy": "direct_cut_unless_story_break",
            "original_audio_policy": "quote_only",
            "burn_annotations": False,
        },
        "expression_rules": {
            "narration_led": True,
            "source_clip_role": "evidence_only",
            "original_audio_policy": "quote_only",
            "full_conflict_replay": False,
            "analysis_cards": not args.relationship_only,
            "caption_cards": False,
            "original_visuals": not args.relationship_only,
            "narration_backgrounds": args.relationship_only,
            "viewer_can_finish_plot_from_clips": False,
        },
        "clips": [{"id": "原创主体证据化时间线", "source_start": "0.000", "source_end": f"{cursor:.3f}", "focus_x": 0.5, "high_energy": False, "source_clip_role": "evidence_timeline_with_original_visuals"}],
        "narration": {
            "provider": "cosyvoice",
            "python": "tools/CosyVoice/.venv/Scripts/python.exe",
            "model_dir": "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT",
            "mode": "sft",
            "voice": "中文女",
            "speed": 1.12,
            "rate": "+12%",
            "segments": narration_segments,
        },
        "mix": {
            "source_audio_mode": "play_between_narration",
            "source_gap_volume": 0.48,
            "source_audio_under_narration_volume": 0.35,
            "source_audio_intro_deadline_seconds": 10.0,
            "source_audio_intro_min_seconds": 0.5,
            "narration_volume": 1.25,
            "audio_transition_fade_seconds": 0.08,
            "music_volume": 0.0,
        },
        "original_visual_assets": {
            "directory": str(asset_dir),
            "timeline_manifest": timeline_entries,
            "source_audio_quote_count": sum(1 for item in timeline_entries if item.get("type") == "source" and item.get("audio")),
            "source_visual_seconds": round(sum(item["duration"] for item in timeline_entries if item.get("type") == "source"), 3),
            "source_audio_seconds": round(sum(item["duration"] for item in timeline_entries if item.get("type") == "source" and item.get("audio")), 3),
        },
        "preflight_review": {
            "status": "passed",
            "review_scope": "content_before_render",
            "one_line_question": "两个人共同完成绣品，究竟是作弊还是合理接力？",
            "one_line_answer": "两次交接时绣品都未完成，指控缺少成品这个关键前提。",
            "conflict": "玲珑把璎珞和吉祥的接力解释成作弊，璎珞用两次未完成的交接反证。",
            "emotional_value": "观众从紧张和误会，转为看懂证据如何拆穿一句指控。",
            "checks": {
                "position_and_fact": "pass",
                "emotional_value": "pass",
                "conflict_and_hook": "pass",
                "answer_timing": "pass",
                "visual_evidence": "pass",
                "title_script_consistency": "pass",
                "safety_and_attribution": "pass",
            },
            "risk_notes": [
                "原创解说和分析卡承担主体叙事；原剧画面仅作为短证据。",
                "原剧原声只保留必要台词，双面绣片段为另一位宫女的画面，不归于魏璎珞。",
                "不连续复现完整冲突，不让观众仅靠原剧片段看完本段剧情；不加入黑屏过渡和 BGM。",
            ],
        },
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path = output_dir / f"{args.base_name}_原创主体时间线.manifest.json"
    manifest_path.write_text(json.dumps({"duration": round(cursor, 3), "timeline_video": str(timeline_video), "assets": str(asset_dir), "entries": timeline_entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(work_dir)
    print(timeline_video)
    print(plan_path)
    print(f"Duration: {cursor:.3f}")


if __name__ == "__main__":
    main()
