#!/usr/bin/env python3
import json
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <benchmark.json>", file=sys.stderr)
        return 1

    payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    benchmarks = payload.get("benchmarks", [])
    if not benchmarks:
        print("No benchmark results found.")
        return 0

    print("Benchmark summary (mean seconds):")
    for item in sorted(benchmarks, key=lambda entry: entry["stats"]["mean"]):
        stats = item["stats"]
        print(
            f"- {item['name']}: "
            f"mean={stats['mean']:.4f}s "
            f"min={stats['min']:.4f}s "
            f"max={stats['max']:.4f}s "
            f"rounds={stats['rounds']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
