#!/usr/bin/env python3
"""从 MP4 指定时间点抽帧并生成三种尺寸的美食视频封面。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\Dengb.ttf"),
)


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def probe_video(video: Path) -> dict[str, float | int | str]:
    raw = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration",
            "-of",
            "json",
            str(video),
        ]
    )
    data = json.loads(raw)["streams"][0]
    fps = float(Fraction(data["r_frame_rate"]))
    return {
        "width": int(data["width"]),
        "height": int(data["height"]),
        "fps": fps,
        "duration": float(data.get("duration") or 0),
        "r_frame_rate": data["r_frame_rate"],
    }


def parse_time(value: str, fps: float, timecode_fps: float | None = None) -> tuple[float, str]:
    """解析秒数、HH:MM:SS、HH:MM:SS:FF，并返回秒数和安全文件标签。"""
    value = value.strip()
    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}:\d{1,3}", value):
        hours, minutes, seconds, frames = (int(part) for part in value.split(":"))
        frame_base = timecode_fps or fps
        seconds_value = hours * 3600 + minutes * 60 + seconds + frames / frame_base
        label = value.replace(":", "-")
        return seconds_value, label
    if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}(?:\.\d+)?", value):
        hours, minutes, seconds = value.split(":")
        seconds_value = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        label = value.replace(":", "-").replace(".", "_")
        return seconds_value, label
    seconds_value = float(value)
    label = value.replace(".", "_")
    return seconds_value, f"{label}s"


def safe_name(value: str) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value).strip(" .")
    return value or "未命名美食视频"


def select_font() -> Path:
    for candidate in DEFAULT_FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("未找到可用中文粗体字体，请安装微软雅黑或黑体。")


def crop_to_ratio(image: Image.Image, ratio: float, focus_y: float) -> Image.Image:
    source_width, source_height = image.size
    crop_width = source_width
    crop_height = round(source_width / ratio)
    if crop_height > source_height:
        crop_height = source_height
        crop_width = round(source_height * ratio)
    center_y = round(source_height * focus_y)
    top = max(0, min(center_y - crop_height // 2, source_height - crop_height))
    left = max(0, (source_width - crop_width) // 2)
    return image.crop((left, top, left + crop_width, top + crop_height))


def fit_font(text: str, font_path: Path, max_width: int, initial_size: int) -> ImageFont.FreeTypeFont:
    size = initial_size
    while size >= 48:
        font = ImageFont.truetype(str(font_path), size=size)
        width = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)[2]
        if width <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), size=48)


def draw_title(image: Image.Image, text: str, font_path: Path) -> Image.Image:
    canvas = image.convert("RGBA")
    width, height = canvas.size
    title_font = fit_font(text, font_path, round(width * 0.82), round(width * 0.11))
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    box = measure.textbbox((0, 0), text, font=title_font)
    text_height = box[3] - box[1]

    if width / height > 1.4:
        top = round(height * 0.055)
        bottom = top + round(height * 0.24)
    elif width / height > 1.1:
        top = round(height * 0.05)
        bottom = top + round(height * 0.27)
    else:
        top = round(height * 0.055)
        bottom = top + round(height * 0.25)

    plate = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    plate_draw = ImageDraw.Draw(plate)
    margin_x = round(width * 0.055)
    radius = max(10, round(height * 0.018))
    plate_draw.rounded_rectangle(
        (margin_x, top, width - margin_x, bottom),
        radius=radius,
        fill=(0, 0, 0, 150),
        outline=(255, 194, 54, 50),
        width=max(2, round(height * 0.003)),
    )
    canvas = Image.alpha_composite(canvas, plate)

    title = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    title_draw = ImageDraw.Draw(title)
    center_x = width // 2
    center_y = (top + bottom) // 2
    outer_stroke = max(10, round(height * 0.014))
    inner_stroke = max(4, round(height * 0.006))
    shadow_offset = max(5, round(height * 0.01))
    title_draw.text(
        (center_x + shadow_offset, center_y + shadow_offset),
        text,
        anchor="mm",
        font=title_font,
        fill=(0, 0, 0, 180),
        stroke_width=outer_stroke,
        stroke_fill=(0, 0, 0, 180),
    )
    title_draw.text(
        (center_x, center_y),
        text,
        anchor="mm",
        font=title_font,
        fill=(255, 214, 73, 255),
        stroke_width=outer_stroke,
        stroke_fill=(48, 18, 4, 255),
    )
    title_draw.text(
        (center_x, center_y - max(1, round(text_height * 0.01))),
        text,
        anchor="mm",
        font=title_font,
        fill=(255, 218, 87, 255),
        stroke_width=inner_stroke,
        stroke_fill=(184, 91, 9, 255),
    )
    return Image.alpha_composite(canvas, title).convert("RGB")


def extract_frame(video: Path, seconds: float, output: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-ss",
            f"{seconds:.6f}",
            "-frames:v",
            "1",
            "-vf",
            "format=rgb24",
            str(output),
        ]
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="从视频指定时间点生成三种尺寸的美食封面")
    parser.add_argument("video", type=Path, help="源 MP4 路径")
    parser.add_argument("--time", required=True, help="秒数或 HH:MM:SS:FF 时间码")
    parser.add_argument(
        "--timecode-fps",
        type=float,
        help="仅用于 HH:MM:SS:FF；若时间码来自 30fps 编辑器而源视频为 60fps，则填 30",
    )
    parser.add_argument("--text", required=True, help="封面文字，按原样叠加")
    parser.add_argument("--output-dir", type=Path, help="输出目录；默认放到 videos/exports/长视频/<主题>")
    parser.add_argument("--topic", help="输出主题目录名；默认使用视频文件名")
    parser.add_argument("--focus-y", type=float, default=0.62, help="横版裁切焦点，取 0 到 1，默认 0.62")
    args = parser.parse_args()

    video = args.video.resolve()
    if not video.exists():
        parser.error(f"找不到源视频：{video}")
    if not 0 <= args.focus_y <= 1:
        parser.error("--focus-y 必须在 0 到 1 之间")

    info = probe_video(video)
    seconds, time_label = parse_time(args.time, float(info["fps"]), args.timecode_fps)
    if seconds < 0 or seconds > float(info["duration"]):
        parser.error(f"时间点超出视频范围：{seconds:.3f}s / {float(info['duration']):.3f}s")

    topic = safe_name(args.topic or video.stem)
    output_dir = (args.output_dir or ROOT / "videos" / "exports" / "长视频" / topic).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_path = output_dir / f"{topic}_原始帧_{time_label}.png"
    extract_frame(video, seconds, frame_path)
    source = Image.open(frame_path).convert("RGB")
    font_path = select_font()

    specs = (
        ("16x9", 1920, 1080, 16 / 9, min(0.82, args.focus_y + 0.05)),
        ("4x3", 1440, 1080, 4 / 3, min(0.78, args.focus_y)),
        ("3x4", 1080, 1440, 3 / 4, 0.53),
    )
    outputs: list[Path] = []
    for label, width, height, ratio, focus_y in specs:
        cropped = crop_to_ratio(source, ratio, focus_y).resize((width, height), Image.Resampling.LANCZOS)
        cover = draw_title(cropped, args.text, font_path)
        output = output_dir / f"{topic}_封面_{label}.png"
        cover.save(output, format="PNG", optimize=True)
        outputs.append(output)

    manifest = {
        "source_video": str(video),
        "source_frame": str(frame_path),
        "requested_time": args.time,
        "resolved_seconds": round(seconds, 6),
        "source_fps": info["fps"],
        "source_frame_rate": info["r_frame_rate"],
        "cover_text": args.text,
        "cover_sizes": {"16x9": [1920, 1080], "4x3": [1440, 1080], "3x4": [1080, 1440]},
        "cover_assets": [str(path) for path in outputs],
    }
    (output_dir / f"{topic}_封面记录.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for path in [frame_path, *outputs]:
        print(path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(error.stderr or str(error), file=sys.stderr)
        raise SystemExit(error.returncode or 1)
