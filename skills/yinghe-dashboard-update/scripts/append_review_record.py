#!/usr/bin/env python
"""Append one normalized platform review record to the dashboard history JSON."""

import argparse
import json
from pathlib import Path


PLATFORMS = {"小红书", "抖音", "快手"}


def optional_number(value):
    if value is None:
        return None
    return float(value) if "." in value else int(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to review-history.json")
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    parser.add_argument("--period", required=True)
    parser.add_argument("--plays")
    parser.add_argument("--completion")
    parser.add_argument("--interaction")
    parser.add_argument("--followers")
    parser.add_argument("--note", default="")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    path = Path(args.file)
    if path.exists():
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("History file must contain a JSON array")
    else:
        records = []

    record = {
        "id": f"{args.period}-{args.platform}",
        "platform": args.platform,
        "period": args.period,
        "plays": optional_number(args.plays),
        "completion": optional_number(args.completion),
        "interaction": optional_number(args.interaction),
        "followers": optional_number(args.followers),
        "note": args.note,
    }
    duplicate = [i for i, item in enumerate(records) if item.get("platform") == args.platform and item.get("period") == args.period]
    if duplicate and not args.replace:
        raise ValueError("Record already exists for this platform and period; use --replace to correct it")
    if duplicate:
        records[duplicate[0]] = record
    else:
        records.append(record)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {record['id']}")


if __name__ == "__main__":
    main()
