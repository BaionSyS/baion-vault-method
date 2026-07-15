#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / "RECEIPTS/data/positive-control-v1.txt"


def run() -> str:
    baseline = '{"a":1,"b":2}'
    injected = '{"a":1, "b":2}'
    detected = baseline != injected
    return (
        f"control=injected-output-difference detection={'pass' if detected else 'fail'}\n"
        f"SUMMARY controls=1 pass={1 if detected else 0} fail={0 if detected else 1}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = run()
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    if args.check:
        if output != EXPECTED.read_text(encoding="utf-8"):
            print("POSITIVE CONTROL FAIL: generated output differs from receipt source")
            return 1
        print("POSITIVE CONTROL PASS")
        return 0
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
