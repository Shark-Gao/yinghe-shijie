import re
from pathlib import Path


def to_seconds(value: str) -> float:
    value = value.replace(',', '.')
    h, m, s = value.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def to_srt_time(value: float) -> str:
    total_ms = round(value * 1000)
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def parse_srt(path: Path):
    content = path.read_text(encoding='utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n\s*\n', content.strip())
    cues = []
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 2 or '-->' not in lines[1]:
            continue
        start_text, end_text = [part.strip() for part in lines[1].split('-->', 1)]
        cues.append((to_seconds(start_text), to_seconds(end_text), lines[2:]))
    return cues


def main() -> None:
    source = Path(r'L:\workspace\yinghe-shijie\videos\analysis\The.Apartment.Job.S01E01\source_zh-CN.srt')
    output = Path(r'L:\workspace\yinghe-shijie\videos\exports\短视频\The.Apartment.Job.S01E01.2026.1080p.NF.WEB-DL.AAC2.0.H.264\素材映射\公寓维修资金_原剧对白_成片时间轴.srt')
    clips = [
        (56 * 60 + 5.361, 56 * 60 + 35.600),
        (56 * 60 + 57.831, 57 * 60 + 57.849),
        (58 * 60 + 15.116, 59 * 60 + 2.000),
        (59 * 60 + 32.402, 60 * 60 + 1.306),
        (60 * 60 + 19.699, 60 * 60 + 51.189),
        (62 * 60 + 4.470, 62 * 60 + 39.302),
    ]
    cues = parse_srt(source)
    rows = []
    output_cursor = 0.0
    index = 1
    for clip_start, clip_end in clips:
        for cue_start, cue_end, text_lines in cues:
            overlap_start = max(cue_start, clip_start)
            overlap_end = min(cue_end, clip_end)
            if overlap_end <= overlap_start or not text_lines:
                continue
            mapped_start = output_cursor + overlap_start - clip_start
            mapped_end = output_cursor + overlap_end - clip_start
            rows.extend([
                str(index),
                f'{to_srt_time(mapped_start)} --> {to_srt_time(mapped_end)}',
                '\n'.join(text_lines),
                '',
            ])
            index += 1
        output_cursor += clip_end - clip_start
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(rows), encoding='utf-8')
    print(output)
    print(f'cues={index - 1}; duration={output_cursor:.3f}')


if __name__ == '__main__':
    main()
