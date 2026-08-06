import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_SRT = ROOT / "source_zh-CN.srt"
METADATA = ROOT / "third_story_proxy_metadata.json"
MANIFEST = ROOT / "evidence_manifest.json"
OUTPUT = ROOT / "third_story_original_dialogue_proxy.srt"

TIME_RE = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")


def seconds(value: str) -> float:
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def timestamp(value: float) -> str:
    ms = max(0, round(value * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def read_srt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    matches = list(TIME_RE.finditer(text))
    rows = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        lines = [line.strip() for line in text[match.end():end].splitlines() if line.strip()]
        if lines and lines[-1].isdigit():
            lines = lines[:-1]
        rows.append({
            "start": seconds(match.group(1)),
            "end": seconds(match.group(2)),
            "text": "\n".join(lines),
        })
    return rows


def main() -> None:
    cues = read_srt(SOURCE_SRT)
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source_by_asset = {
        item.get("id"): item
        for item in manifest
        if item.get("kind") == "source" and item.get("id")
    }
    output_rows = []
    for segment in metadata["segments"]:
        if segment["kind"] != "source":
            continue
        item = source_by_asset[segment["asset"]]
        original_start = seconds(item["start"])
        original_end = seconds(item["end"])
        proxy_start = float(segment["start"])
        for cue in cues:
            if cue["end"] <= original_start or cue["start"] >= original_end:
                continue
            start = max(cue["start"], original_start) - original_start + proxy_start
            end = min(cue["end"], original_end) - original_start + proxy_start
            if end > start and cue["text"]:
                output_rows.append((start, end, cue["text"]))
    output_rows.sort(key=lambda row: (row[0], row[1]))
    rows = []
    for index, (start, end, text) in enumerate(output_rows, 1):
        rows.extend([str(index), f"{timestamp(start)} --> {timestamp(end)}", text, ""])
    OUTPUT.write_text("\n".join(rows), encoding="utf-8")
    print(OUTPUT)
    print(f"cues={len(output_rows)}")


if __name__ == "__main__":
    main()
