#!/usr/bin/env python3
"""根据两张 PNG 嘴型图创建轻量级口型同步头像叠加层。

This is intentionally a 2.5D proof-of-concept: it follows voice energy to
switch between closed and open mouth art, adds a very small breathing motion,
then composites the result over a source video.  It does not replace a rigged
VRM/Live2D character renderer.
"""

from __future__ import annotations

import argparse
import math
import subprocess
from array import array
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="带中文解说音频的源 MP4。")
    parser.add_argument("--closed", required=True, help="角色闭嘴状态的 RGBA PNG。")
    parser.add_argument("--open", required=True, help="角色说话状态的 RGBA PNG。")
    parser.add_argument("--output", required=True, help="新 MP4 输出路径，不覆盖源文件。")
    parser.add_argument("--height", type=int, default=390, help="角色像素高度，默认 390。")
    parser.add_argument("--margin", type=int, default=28, help="顶部/右侧边距，默认 28 像素。")
    parser.add_argument("--fps", type=int, default=30, help="头像动画帧率，默认 30。")
    parser.add_argument("--motion", type=float, default=0.008, help="轻微缩放运动量；使用 0 表示平面 2D 叠加。")
    return parser.parse_args()


def media_size_and_duration(source: Path) -> tuple[int, int, float]:
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=width,height:format=duration", "-of", "default=nw=1:nk=1", str(source),
        ],
        check=True, capture_output=True, text=True,
    )
    values = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    if len(values) < 3:
        raise SystemExit(f"Unable to read video dimensions and duration: {source}")
    return int(values[0]), int(values[1]), float(values[-1])


def read_audio_energy(source: Path, fps: int, duration: float) -> list[float]:
    """根据 16kHz 单声道音频解码，返回每个输出帧的 RMS 能量。"""
    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    samples = array("h")
    samples.frombytes(decoded)
    if not samples:
        return [0.0] * max(1, round(duration * fps))
    sample_rate = 16000
    frame_count = max(1, round(duration * fps))
    energies: list[float] = []
    for frame_index in range(frame_count):
        start = round(frame_index * sample_rate / fps)
        end = min(len(samples), round((frame_index + 1) * sample_rate / fps))
        if end <= start:
            energies.append(0.0)
            continue
        square_sum = sum(value * value for value in samples[start:end])
        energies.append(math.sqrt(square_sum / (end - start)))
    return energies


def speaking_frames(energies: list[float]) -> list[bool]:
    ordered = sorted(energies)
    floor = ordered[max(0, round((len(ordered) - 1) * 0.18))]
    ceiling = ordered[max(0, round((len(ordered) - 1) * 0.88))]
    threshold = max(120.0, floor + (ceiling - floor) * 0.24)
    result: list[bool] = []
    held = 0
    for energy in energies:
        if energy >= threshold:
            held = 2
        else:
            held = max(0, held - 1)
        result.append(held > 0)
    return result


def render_avatar_video(
    closed_path: Path,
    open_path: Path,
    output: Path,
    source_video: Path,
    duration: float,
    fps: int,
    height: int,
    motion: float,
    x: int,
    y: int,
) -> None:
    closed = Image.open(closed_path).convert("RGBA")
    opened = Image.open(open_path).convert("RGBA")
    canvas_width = round(height * 0.78)
    canvas_width += canvas_width % 2
    canvas_height = height + 16
    canvas_height += canvas_height % 2
    energies = read_audio_energy(SOURCE_FOR_AUDIO, fps, duration)
    speaking = speaking_frames(energies)
    command = [
        "ffmpeg", "-y", "-i", str(source_video),
        "-f", "rawvideo", "-pixel_format", "rgba", "-video_size", f"{canvas_width}x{canvas_height}",
        "-framerate", str(fps), "-i", "-",
        "-filter_complex", f"[0:v][1:v]overlay={x}:{y}:format=auto[v]",
        "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index, is_speaking in enumerate(speaking):
            source = opened if is_speaking else closed
            scale = 1.0 + motion * math.sin(index * 2 * math.pi / (fps * 2.8))
            target_height = round(height * scale)
            target_width = round(source.width * target_height / source.height)
            sprite = source.resize((target_width, target_height), Image.Resampling.LANCZOS)
            frame = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            x = (canvas_width - target_width) // 2
            y = canvas_height - target_height
            frame.alpha_composite(sprite, (x, y))
            assert process.stdin is not None
            process.stdin.write(frame.tobytes())
    finally:
        if process.stdin:
            process.stdin.close()
    if process.wait() != 0:
        raise SystemExit("Avatar overlay video rendering failed.")


def main() -> None:
    args = parse_args()
    source = Path(args.source).resolve()
    closed = Path(args.closed).resolve()
    opened = Path(args.open).resolve()
    output = Path(args.output).resolve()
    for path in (source, closed, opened):
        if not path.is_file():
            raise SystemExit(f"Missing input: {path}")
    if args.height < 160 or args.margin < 0 or args.fps < 12 or args.motion < 0:
        raise SystemExit("Use --height >= 160, --margin >= 0, --fps >= 12, and --motion >= 0.")
    width, video_height, duration = media_size_and_duration(source)
    if args.height + args.margin > video_height:
        raise SystemExit("Avatar height plus margin exceeds the source-video height.")
    output.parent.mkdir(parents=True, exist_ok=True)
    overlay_width = round(args.height * 0.78)
    overlay_width += overlay_width % 2
    x = width - overlay_width - args.margin
    global SOURCE_FOR_AUDIO
    SOURCE_FOR_AUDIO = source
    render_avatar_video(closed, opened, output, source, duration, args.fps, args.height, args.motion, x, args.margin)
    print(output)


if __name__ == "__main__":
    SOURCE_FOR_AUDIO = Path()
    main()
