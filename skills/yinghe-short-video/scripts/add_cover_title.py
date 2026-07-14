#!/usr/bin/env python3
"""Add deterministic Chinese headline and subhead overlays to an AI cover image."""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--subhead", required=True)
    parser.add_argument("--theme", default="", help="Optional short subject label.")
    parser.add_argument("--layout", choices=("center", "right", "portrait"), default="right")
    return parser.parse_args()


def escape_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def main() -> None:
    options = args()
    source, output = Path(options.input).resolve(), Path(options.output).resolve()
    if not source.is_file():
        raise SystemExit(f"Cover source does not exist: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    font = Path("C:/Windows/Fonts/msyhbd.ttc")
    if not font.is_file():
        raise SystemExit("Microsoft YaHei Bold font is required.")
    files: list[Path] = []
    try:
        subhead_lines = [line.strip() for line in options.subhead.replace("\\n", "\n").splitlines() if line.strip()]
        if not subhead_lines:
            raise SystemExit("Subhead cannot be empty.")
        theme = options.theme.strip()
        texts = (options.headline.strip(), *subhead_lines, *([theme] if theme else []))
        for text in texts:
            handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False)
            handle.write(text)
            handle.close()
            files.append(Path(handle.name))
        font_path, headline_path, subhead_path = escape_path(font), escape_path(files[0]), escape_path(files[1])
        theme_path = escape_path(files[-1]) if theme else None
        # Use relative coordinates so a generated 16:9 cover remains readable
        # even when its exact pixel dimensions differ between generations.
        if options.layout == "right":
            filters = (
                "drawbox=x=iw*0.53:y=ih*0.10:w=iw*0.43:h=ih*0.75:color=black@0.10:t=fill,"
                f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=10:fontsize=h*0.115:x=w*0.57:y=h*0.16,"
                "drawbox=x=iw*0.61:y=ih*0.445:w=iw*0.27:h=ih*0.012:color=0x56C6FF:t=fill,"
                f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=white:bordercolor=black:borderw=7:fontsize=h*0.075:x=w*0.57:y=h*0.52"
            )
            if len(subhead_lines) > 1:
                subhead_second_path = escape_path(files[2])
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{subhead_second_path}':fontcolor=white:"
                    "bordercolor=black:borderw=7:fontsize=h*0.075:x=w*0.57:y=h*0.66"
                )
            if theme_path:
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{theme_path}':fontcolor=0x8EDBFF:"
                    "bordercolor=black:borderw=3:fontsize=h*0.036:x=w*0.57:y=h*0.82"
                )
        elif options.layout == "portrait":
            filters = (
                "drawbox=x=iw*0.04:y=ih*0.04:w=iw*0.92:h=ih*0.52:color=black@0.26:t=fill,"
                f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=10:fontsize=h*0.064:x=(w-text_w)/2:y=h*0.085,"
                "drawbox=x=iw*0.20:y=ih*0.255:w=iw*0.60:h=ih*0.008:color=0x56C6FF:t=fill,"
                f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=white:bordercolor=black:borderw=7:fontsize=h*0.062:x=(w-text_w)/2:y=h*0.315"
            )
            if len(subhead_lines) > 1:
                subhead_second_path = escape_path(files[2])
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{subhead_second_path}':fontcolor=white:"
                    "bordercolor=black:borderw=7:fontsize=h*0.062:x=(w-text_w)/2:y=h*0.405"
                )
            if theme_path:
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{theme_path}':fontcolor=0x8EDBFF:"
                    "bordercolor=black:borderw=3:fontsize=h*0.030:x=(w-text_w)/2:y=h*0.505"
                )
        else:
            filters = (
                "drawbox=x=iw*0.04:y=ih*0.04:w=iw*0.92:h=ih*0.24:color=black@0.66:t=fill,"
                f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=8:fontsize=h*0.10:x=(w-text_w)/2:y=h*0.065,"
                f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=0xD7E8FF:bordercolor=black:borderw=6:fontsize=h*0.058:x=(w-text_w)/2:y=h*0.165"
            )
            if theme_path:
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{theme_path}':fontcolor=0x8EDBFF:"
                    "bordercolor=black:borderw=3:fontsize=h*0.035:x=(w-text_w)/2:y=h*0.235"
                )
        subprocess.run(["ffmpeg", "-y", "-i", str(source), "-vf", filters, "-frames:v", "1", "-update", "1", str(output)], check=True)
    finally:
        for path in files:
            path.unlink(missing_ok=True)
    print(output)


if __name__ == "__main__":
    main()
