#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED = (
    "README.md",
    "SPEC.md",
    "PUBLISHING.md",
    "LICENSE",
    "pyproject.toml",
    "verify_repo.sh",
    "src/bvm_lint/lint.py",
    "src/bvm_lint/codes.py",
    "tests/test_conformance.py",
    "examples/tutorial-vault/README.md",
    "schemas/diagnostics.json",
    "scripts/check_diagnostic_parity.py",
    "templates/artifact.md",
    "docs/field-reports/README.md",
)
EXPECTED_FIELD_REPORTS = {
    "README.md",
    "01-partial-source-window.md",
    "02-budget-bound-null-not-wall.md",
    "03-differential-attribution.md",
    "04-negative-existence.md",
}
ACTION_RE = re.compile(r"uses:\s+[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@([0-9a-f]{40})(?:\s+#.*)?$")
CODE_RE = re.compile(r"BVM\d{3}")


class DuplicateKeyError(ValueError):
    pass


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def load_strict_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=reject_json_constant,
    )


def code_explanations(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "EXPLANATIONS":
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return set(value)
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "EXPLANATIONS" for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return set(value)
    raise ValueError("EXPLANATIONS mapping not found")


def render_difference(label: str, expected: set[str], actual: set[str]) -> str | None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if not missing and not extra:
        return None
    parts: list[str] = []
    if missing:
        parts.append("missing " + ", ".join(missing))
    if extra:
        parts.append("extra " + ", ".join(extra))
    return f"{label}: " + "; ".join(parts)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []

    for rel in REQUIRED:
        if not (root / rel).exists():
            failures.append(f"missing declared release component: {rel}")

    generated_debris_names = {"__pycache__", ".coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    debris = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.name in generated_debris_names or path.suffix == ".pyc"
    ]
    if debris:
        failures.append("generated Python debris present: " + ", ".join(debris[:10]))

    for form in sorted((root / ".github/ISSUE_TEMPLATE").glob("*.yml")):
        if form.name == "config.yml":
            continue
        text = form.read_text(encoding="utf-8")
        if not re.search(r"(?m)^description:[ \t]*\S", text):
            failures.append(f"{form.relative_to(root)}: issue form is missing a top-level description")
        if re.search(r"(?m)^about:", text):
            failures.append(f"{form.relative_to(root)}: 'about' is for legacy Markdown templates, not YAML issue forms")

    workflow = root / ".github/workflows/verify.yml"
    if workflow.is_file():
        for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
            if "uses:" in line and not ACTION_RE.search(line.strip()):
                failures.append(
                    f"{workflow.relative_to(root)}:{number}: action is not pinned to a 40-character commit SHA"
                )

    field_report_dir = root / "docs/field-reports"
    if field_report_dir.is_dir():
        actual_reports = {path.name for path in field_report_dir.glob("*.md")}
        difference = render_difference("field-report release set", EXPECTED_FIELD_REPORTS, actual_reports)
        if difference:
            failures.append(difference)

    license_path = root / "LICENSE"
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8")
        if "MIT License" not in license_text:
            failures.append("LICENSE does not contain the declared MIT License")
    if (root / "LICENSES").exists():
        failures.append("unexpected LICENSES directory: the release uses one root MIT license")

    stale_license_terms = ("CC BY-NC-ND", "CC-BY-NC-ND", "path-based license", "License: mixed", "LICENSES/")
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or ".git" in path.parts
            or path.name == "LICENSE"
            or path == root / "scripts/check_release_surface.py"
        ):
            continue
        if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".cff", ".txt", ".sh"} and path.name != "Makefile":
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        for term in stale_license_terms:
            if term in body:
                failures.append(f"{path.relative_to(root)}: stale mixed-license term: {term}")

    for path in sorted(root.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            load_strict_json(path)
        except (ValueError, UnicodeError, OSError) as exc:
            failures.append(f"{path.relative_to(root)}: invalid strict JSON: {exc}")

    try:
        declared_codes = code_explanations(root / "src/bvm_lint/codes.py")
        diagnostic_data = load_strict_json(root / "schemas/diagnostics.json")
        diagnostic_codes = set(diagnostic_data) if isinstance(diagnostic_data, dict) else set()
        implemented_codes = set(CODE_RE.findall((root / "src/bvm_lint/lint.py").read_text(encoding="utf-8")))
        reference_codes = set(CODE_RE.findall((root / "docs/linter-reference.md").read_text(encoding="utf-8")))
        for label, actual in (
            ("schemas/diagnostics.json parity", diagnostic_codes),
            ("linter implementation parity", implemented_codes),
            ("docs/linter-reference.md parity", reference_codes),
        ):
            difference = render_difference(label, declared_codes, actual)
            if difference:
                failures.append(difference)
    except (ValueError, SyntaxError, OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        failures.append(f"cannot verify diagnostic-code parity: {exc}")

    if failures:
        print("RELEASE SURFACE CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("RELEASE SURFACE CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
