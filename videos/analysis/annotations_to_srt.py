import json
import sys
from pathlib import Path


def srt_time(value: str) -> str:
    h, m, rest = value.split(':')
    sec, ms = rest.split('.')
    return f'{int(h):02}:{int(m):02}:{int(sec):02},{int(ms):03}'


def main() -> None:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    data = json.loads(source.read_text(encoding='utf-8'))
    rows = []
    for index, item in enumerate(data['annotations'], start=1):
        rows.extend([
            str(index),
            f"{srt_time(item['start'])} --> {srt_time(item['end'])}",
            item['text'],
            '',
        ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(rows), encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
