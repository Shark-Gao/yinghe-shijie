import json
import sys


def seconds(value: str) -> float:
    h, m, s = value.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def main() -> None:
    manifest_path, plan_path = sys.argv[1:3]
    manifest = json.load(open(manifest_path, encoding='utf-8'))
    plan = json.load(open(plan_path, encoding='utf-8'))
    rows = []
    gaps = []
    last_end = -1.0
    max_overrun = 0.0
    for measured, planned in zip(manifest['segments'], plan['narration']['segments']):
        start = seconds(measured['start'])
        end = start + float(measured['audio_duration'])
        planned_end = seconds(planned['end'])
        rows.append((measured['id'], start, end, planned_end))
        max_overrun = max(max_overrun, end - planned_end)
        if last_end >= 0:
            gaps.append(start - last_end)
        last_end = max(last_end, end)
    print('segments', len(rows))
    print('last_end', round(last_end, 3))
    print('tail', round(232.367 - last_end, 3))
    print('max_overrun', round(max_overrun, 3))
    print('max_gap', round(max(gaps), 3))
    print('min_gap', round(min(gaps), 3))
    print('first', [(r[0], round(r[2] - r[1], 3), round(r[3] - r[1], 3)) for r in rows[:3]])
    print('last', [(r[0], round(r[2] - r[1], 3), round(r[3] - r[1], 3)) for r in rows[-3:]])


if __name__ == '__main__':
    main()
