import json
from pathlib import Path

kept = [(87.266, 409.466), (558.533, 1028.566), (1028.566, 1346.8)]
people = []
for line in Path(r"L:\workspace\yinghe-shijie\outputs\tmp_detect_people.txt").read_text(encoding="utf-8").splitlines()[1:]:
    if "-" in line:
        start, end = line.split("-", 1)
        people.append((float(start), float(end)))

margin = 1.0
base = []
for keep_start, keep_end in kept:
    cursor = keep_start
    for person_start, person_end in people:
        if person_end <= keep_start or person_start >= keep_end:
            continue
        person_start = max(keep_start, person_start)
        person_end = min(keep_end, person_end)
        cut_start = max(keep_start, person_start - margin)
        cut_end = min(keep_end, person_end + margin)
        if cut_start > cursor + 0.08:
            base.append((cursor, cut_start))
        cursor = max(cursor, cut_end)
    if keep_end > cursor + 0.08:
        base.append((cursor, keep_end))

base = [(start, end) for start, end in base if end - start >= 0.25]
late = [(start, end) for start, end in base if start >= 558.0]
target = 1109.45
clips = list(base)
duration = sum(end - start for start, end in clips)
while duration < target:
    for start, end in late:
        remaining = target - duration
        length = end - start
        if remaining <= 0:
            break
        if length <= remaining + 0.05:
            clips.append((start, end))
            duration += length
        else:
            clips.append((start, start + remaining))
            duration += remaining
            break

result = []
for index, (start, end) in enumerate(clips, 1):
    result.append({
        "source_start": f"{int(start // 3600):02}:{int(start % 3600 // 60):02}:{start % 60:06.3f}",
        "source_end": f"{int(end // 3600):02}:{int(end % 3600 // 60):02}:{end % 60:06.3f}",
    })
print(json.dumps(result, ensure_ascii=False, indent=4))
print(f"clips={len(result)} duration={duration:.3f}", file=__import__("sys").stderr)
