#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "WORKING/corpus/corpus-v2.tsv"
EXPECTED = ROOT / "RECEIPTS/data/probe-v2.txt"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> str:
    reference = load_module("tutorial_reference", ROOT / "CANON/objects/reference_normalizer.py")
    candidate = load_module("tutorial_candidate", ROOT / "WORKING/objects/candidate_normalizer.py")
    lines: list[str] = []
    passed = 0
    cases = 0
    for raw in CORPUS.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        case, expected, payload = raw.split("\t", 2)
        cases += 1
        outcomes: dict[str, tuple[str, str | None]] = {}
        for label, module in (("reference", reference), ("candidate", candidate)):
            try:
                output = module.normalize(payload)
                outcomes[label] = ("accept", output)
            except (ValueError, TypeError):
                outcomes[label] = ("reject", None)
        parity = outcomes["reference"] == outcomes["candidate"]
        expectation = all(value[0] == expected for value in outcomes.values())
        ok = parity and expectation
        passed += int(ok)
        result = outcomes["reference"][1]
        suffix = f" result={result}" if result is not None else ""
        lines.append(
            f"case={case} expected={expected} reference={outcomes['reference'][0]} "
            f"candidate={outcomes['candidate'][0]} parity={'pass' if parity else 'fail'} "
            f"expectation={'pass' if expectation else 'fail'}{suffix}"
        )
    lines.append(f"SUMMARY cases={cases} pass={passed} fail={cases-passed}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = run()
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    if args.check:
        expected = EXPECTED.read_text(encoding="utf-8")
        if output != expected:
            print("TUTORIAL PROBE FAIL: generated output differs from receipt source")
            return 1
        print("TUTORIAL PROBE PASS")
        return 0
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
