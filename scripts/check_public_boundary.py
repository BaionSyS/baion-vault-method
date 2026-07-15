#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".cff", ".txt", ".sh"}
FORBIDDEN = {
    "private operating-vault name": re.compile("BAION" + "_VAULT_HOT", re.IGNORECASE),
    "runtime mount path": re.compile(r"/(?:mnt|home|Users)/"),
    "private-key material": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "credential assignment": re.compile(r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]+"),
    "unpublished program codename": re.compile("D" + "ICE"),
}
EXCLUDED = {"scripts/check_public_boundary.py"}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if rel in EXCLUDED or (path.suffix and path.suffix not in TEXT_SUFFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{rel}:{line}: {label}")
    if failures:
        print("PUBLICATION BOUNDARY CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PUBLICATION BOUNDARY CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
