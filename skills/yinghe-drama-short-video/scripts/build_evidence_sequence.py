#!/usr/bin/env python3
"""把原剧短证据片段与原创图形卡拼成一条可配音的证据化时间线。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def seconds(value: str | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    parts = str(value).split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def make_source_clip(source: Path, item: dict, output: Path) -> float:
    start = seconds(item["start"])
    end = seconds(item["end"])
    duration = end - start
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-vf",
            "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return duration


def make_card(card: Path, duration: float, output: Path) -> float:
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(card),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t",
            f"{duration:.3f}",
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-b:a",
            "160k",
            "-shortest",
            str(output),
        ]
    )
    return duration


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cards-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata", required=True)
    args = parser.parse_args()

    source = Path(args.source).resolve()
    cards_dir = Path(args.cards_dir).resolve()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    output = Path(args.output).resolve()
    metadata_path = Path(args.metadata).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata: list[dict] = []
    timeline = 0.0
    with tempfile.TemporaryDirectory(prefix="drama_evidence_") as temp_dir:
        temp = Path(temp_dir)
        pieces: list[Path] = []
        for index, item in enumerate(manifest, 1):
            kind = str(item["kind"])
            piece = temp / f"piece_{index:03d}.mp4"
            if kind == "source":
                duration = make_source_clip(source, item, piece)
                asset = item.get("id") or f"source_{index:03d}"
            elif kind == "card":
                card = cards_dir / f"{item['card']}.png"
                if not card.is_file():
                    raise SystemExit(f"找不到原创图形卡：{card}")
                duration = float(item["duration"])
                make_card(card, duration, piece)
                asset = item["card"]
            else:
                raise SystemExit(f"不支持的素材类型：{kind}")
            pieces.append(piece)
            metadata.append(
                {
                    "index": index,
                    "kind": kind,
                    "asset": asset,
                    "start": round(timeline, 3),
                    "end": round(timeline + duration, 3),
                    "duration": round(duration, 3),
                }
            )
            timeline += duration

        concat_list = temp / "concat.txt"
        concat_lines = []
        for piece in pieces:
            escaped = piece.as_posix().replace("'", "'\\''")
            concat_lines.append(f"file '{escaped}'")
        concat_list.write_text("\n".join(concat_lines), encoding="utf-8")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", "-movflags", "+faststart", str(output)])

    metadata_path.write_text(json.dumps({"duration": round(timeline, 3), "segments": metadata}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    print(metadata_path)


if __name__ == "__main__":
    main()
