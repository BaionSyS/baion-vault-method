#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target_text = raw.strip().split(maxsplit=1)[0].strip("<>")
            if not target_text or target_text.startswith(SKIP_PREFIXES):
                continue
            target_text = unquote(target_text.split("#", 1)[0])
            if not target_text:
                continue
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                failures.append(f"{path.relative_to(root)}: link escapes repository: {raw}")
                continue
            if not target.exists():
                failures.append(f"{path.relative_to(root)}: missing link target: {raw}")
    if failures:
        print("MARKDOWN LINK CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MARKDOWN LINK CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
