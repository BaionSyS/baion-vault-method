from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SEMVER_PRERELEASE_ID = r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_BUILD_ID = r"[0-9A-Za-z-]+"
SEMVER_RE = re.compile(
    rf"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    rf"(?:-({SEMVER_PRERELEASE_ID}(?:\.{SEMVER_PRERELEASE_ID})*))?"
    rf"(?:\+({SEMVER_BUILD_ID}(?:\.{SEMVER_BUILD_ID})*))?$"
)
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
METADATA_RE = re.compile(r"\A\ufeff?\s*<!--\s*bvm\s*\r?\n(?P<body>.*?)\r?\n-->\s*", re.DOTALL)


class DuplicateKeyError(ValueError):
    """Raised when strict JSON contains a duplicate object member."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def strict_json_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_strict_object,
        parse_constant=_reject_json_constant,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = strict_json_loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def extract_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = METADATA_RE.match(text)
    if not match:
        raise ValueError("managed Markdown must begin with a '<!-- bvm' strict-JSON metadata block")
    data = strict_json_loads(match.group("body"))
    if not isinstance(data, dict):
        raise ValueError("metadata JSON must be an object")
    return data


def markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = METADATA_RE.match(text)
    return text[match.end():] if match else text


def iter_markdown_files(base: Path) -> list[Path]:
    """Discover managed Markdown case-insensitively.

    A file named ``NOTES.MD`` is still Markdown; matching only the lowercase
    ``.md`` glob would let it escape linting, so compare the folded suffix.
    """
    return sorted(
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() == ".md"
    )


def reference_dedup_key(reference: Any) -> Any:
    """Collapse aliased spellings of one vault path to a single dedup key.

    Uniqueness checks over declared references must treat ``./a/b.md``,
    ``a//b.md``, and ``a/b.md`` as the same path; comparing raw strings would
    let an alias slip a duplicate past the check. Non-strings are returned
    unchanged so upstream type validation still fires.
    """
    if not isinstance(reference, str):
        return reference
    return PurePosixPath(reference).as_posix()


def is_semver(value: Any) -> bool:
    return isinstance(value, str) and bool(SEMVER_RE.fullmatch(value))


def semver_tuple(value: str) -> tuple[int, int, int, str]:
    """Return a compatibility tuple; use compare_semver for precedence decisions."""
    match = SEMVER_RE.fullmatch(value)
    if not match:
        raise ValueError(value)
    core_and_pre = value.split("+", 1)[0]
    prerelease = core_and_pre.split("-", 1)[1] if "-" in core_and_pre else ""
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), prerelease


def compare_semver(left: str, right: str) -> int:
    """Compare SemVer precedence, ignoring build metadata."""

    def parse(value: str) -> tuple[tuple[int, int, int], list[str] | None]:
        match = SEMVER_RE.fullmatch(value)
        if not match:
            raise ValueError(value)
        core_and_pre = value.split("+", 1)[0]
        core_text, sep, pre_text = core_and_pre.partition("-")
        core = tuple(int(part) for part in core_text.split("."))
        return core, pre_text.split(".") if sep else None

    left_core, left_pre = parse(left)
    right_core, right_pre = parse(right)
    if left_core != right_core:
        return (left_core > right_core) - (left_core < right_core)
    if left_pre is None and right_pre is None:
        return 0
    if left_pre is None:
        return 1
    if right_pre is None:
        return -1
    for left_id, right_id in zip(left_pre, right_pre):
        if left_id == right_id:
            continue
        left_numeric = left_id.isdigit()
        right_numeric = right_id.isdigit()
        if left_numeric and right_numeric:
            left_num, right_num = int(left_id), int(right_id)
            return (left_num > right_num) - (left_num < right_num)
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return (left_id > right_id) - (left_id < right_id)
    return (len(left_pre) > len(right_pre)) - (len(left_pre) < len(right_pre))


def is_utc(value: Any) -> bool:
    return parse_utc(value) is not None


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def safe_reference(root: Path, reference: Any) -> tuple[Path | None, str | None]:
    """Resolve a vault-root-relative POSIX path without allowing escape."""

    if not isinstance(reference, str) or not reference.strip():
        return None, "reference must be a non-empty string"
    if "\\" in reference:
        return None, "reference must use forward slashes"
    pure = PurePosixPath(reference)
    if pure.is_absolute() or ".." in pure.parts:
        return None, "reference must stay inside the vault and may not contain '..'"
    candidate = (root / Path(*pure.parts)).resolve(strict=False)
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, "reference escapes the vault root"
    return candidate, None


def relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)
