#!/usr/bin/env python3
"""在 AI 封面底图上稳定叠加中文主标题和副标题。"""
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
    parser.add_argument("--theme", default="", help="可选的简短主题标签。")
    parser.add_argument("--series-title", default="", help="电视剧或节目名称；与 --episode 一起显示在封面上。")
    parser.add_argument("--episode", default="", help="集数，例如：第9集。")
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
        series_title = options.series_title.strip()
        episode = options.episode.strip()
        metadata = ""
        if series_title and episode:
            metadata = f"《{series_title}》  {episode}"
        elif series_title:
            metadata = f"《{series_title}》"
        elif episode:
            metadata = episode
        theme_index = 1 + len(subhead_lines)
        metadata_index = theme_index + (1 if theme else 0)
        texts = (options.headline.strip(), *subhead_lines, *([theme] if theme else []), *([metadata] if metadata else []))
        for text in texts:
            handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False)
            handle.write(text)
            handle.close()
            files.append(Path(handle.name))
        font_path, headline_path, subhead_path = escape_path(font), escape_path(files[0]), escape_path(files[1])
        theme_path = escape_path(files[theme_index]) if theme else None
        metadata_path = escape_path(files[metadata_index]) if metadata else None
        drama_cover = bool(metadata)
    # 使用相对坐标，让生成的 16:9 封面即使每次像素尺寸略有不同也保持可读。
        if options.layout == "right":
            filters = (
                "drawbox=x=iw*0.53:y=ih*0.06:w=iw*0.43:h=ih*0.82:color=black@0.12:t=fill,"
                + (f"drawbox=x=iw*0.56:y=ih*0.07:w=iw*0.36:h=ih*0.07:color=0x07111D@0.88:t=fill,"
                   f"drawtext=fontfile='{font_path}':textfile='{metadata_path}':fontcolor=0xBFEFFF:bordercolor=black:borderw=3:fontsize=h*0.050:x=w*0.745-text_w/2:y=h*0.082," if metadata_path else "")
                + f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=10:fontsize=h*({'0.115' if drama_cover else '0.115'}):x=w*0.745-text_w/2:y=h*({'0.165' if drama_cover else '0.16'}),"
                + "drawbox=x=iw*0.61:y=ih*0.445:w=iw*0.27:h=ih*0.012:color=0x56C6FF:t=fill,"
                + f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=white:bordercolor=black:borderw=7:fontsize=h*({'0.080' if drama_cover else '0.075'}):x=w*0.745-text_w/2:y=h*0.52"
            )
            if len(subhead_lines) > 1:
                subhead_second_path = escape_path(files[2])
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{subhead_second_path}':fontcolor=white:"
                    f"bordercolor=black:borderw=7:fontsize=h*({'0.080' if drama_cover else '0.075'}):x=w*0.745-text_w/2:y=h*0.66"
                )
            if theme_path:
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{theme_path}':fontcolor=0x8EDBFF:"
                    "bordercolor=black:borderw=3:fontsize=h*0.036:x=w*0.57:y=h*0.82"
                )
        elif options.layout == "portrait":
            filters = (
                "drawbox=x=iw*0.04:y=ih*0.03:w=iw*0.92:h=ih*0.57:color=black@0.28:t=fill,"
                + (f"drawbox=x=iw*0.10:y=ih*0.045:w=iw*0.80:h=ih*0.075:color=0x07111D@0.88:t=fill,"
                   f"drawtext=fontfile='{font_path}':textfile='{metadata_path}':fontcolor=0xBFEFFF:bordercolor=black:borderw=3:fontsize=h*0.040:x=(w-text_w)/2:y=h*0.060," if metadata_path else "")
                + f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=10:fontsize=h*({'0.082' if drama_cover else '0.064'}):x=(w-text_w)/2:y=h*({'0.145' if drama_cover else '0.085'}),"
                + "drawbox=x=iw*0.20:y=ih*0.335:w=iw*0.60:h=ih*0.008:color=0x56C6FF:t=fill,"
                + f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=white:bordercolor=black:borderw=7:fontsize=h*({'0.068' if drama_cover else '0.062'}):x=(w-text_w)/2:y=h*({'0.395' if drama_cover else '0.315'})"
            )
            if len(subhead_lines) > 1:
                subhead_second_path = escape_path(files[2])
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{subhead_second_path}':fontcolor=white:"
                    f"bordercolor=black:borderw=7:fontsize=h*({'0.068' if drama_cover else '0.062'}):x=(w-text_w)/2:y=h*({'0.495' if drama_cover else '0.405'})"
                )
            if theme_path:
                filters += (
                    f",drawtext=fontfile='{font_path}':textfile='{theme_path}':fontcolor=0x8EDBFF:"
                    "bordercolor=black:borderw=3:fontsize=h*0.030:x=(w-text_w)/2:y=h*0.505"
                )
        else:
            filters = (
                "drawbox=x=iw*0.04:y=ih*0.03:w=iw*0.92:h=ih*0.31:color=black@0.66:t=fill,"
                + (f"drawtext=fontfile='{font_path}':textfile='{metadata_path}':fontcolor=0xBFEFFF:bordercolor=black:borderw=3:fontsize=h*0.042:x=(w-text_w)/2:y=h*0.055," if metadata_path else "")
                + f"drawtext=fontfile='{font_path}':textfile='{headline_path}':fontcolor=white:bordercolor=black:borderw=8:fontsize=h*({'0.115' if drama_cover else '0.10'}):x=(w-text_w)/2:y=h*({'0.105' if drama_cover else '0.065'}),"
                + f"drawtext=fontfile='{font_path}':textfile='{subhead_path}':fontcolor=0xD7E8FF:bordercolor=black:borderw=6:fontsize=h*({'0.068' if drama_cover else '0.058'}):x=(w-text_w)/2:y=h*({'0.225' if drama_cover else '0.165'})"
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
