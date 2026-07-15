from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .codes import EXPLANATIONS
from .lint import lint_vault


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bvm-lint",
        description="Check BAION Vault Method v0.1 structural conformance.",
    )
    parser.add_argument("root", nargs="?", help="vault root to inspect")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON lint report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as a nonzero result")
    parser.add_argument("--explain", metavar="CODE", help="explain a stable BVM issue code")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.explain:
        code = args.explain.upper()
        explanation = EXPLANATIONS.get(code)
        if explanation is None:
            parser.error(f"unknown issue code: {code}")
        print(f"{code}: {explanation}")
        return 0
    if not args.root:
        parser.error("root is required unless --explain or --version is used")

    report = lint_vault(Path(args.root))
    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        for issue in sorted(report.issues):
            print(f"{issue.severity.upper()} {issue.code} {issue.path}: {issue.message}")
        if report.passed:
            print(f"PASS: structural conformance established for {args.root}")
        else:
            print(f"FAIL: {len(report.errors)} error(s), {len(report.warnings)} warning(s) in {args.root}")
        print(
            "checked "
            f"{report.artifacts} artifact(s), "
            f"{report.evidence_receipts} evidence receipt(s), "
            f"{report.review_receipts} review receipt(s), "
            f"{report.promotion_receipts} promotion receipt(s), "
            f"{report.retractions} retraction(s)"
        )

    if not report.passed:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
