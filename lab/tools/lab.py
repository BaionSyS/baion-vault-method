#!/usr/bin/env python3
"""Vault Lab runner — guided break/repair walkthrough and CI check.

Two modes over the same fixtures:

  python3 lab/tools/lab.py            guided, interactive
  python3 lab/tools/lab.py --check    non-interactive verification (CI)

Both run the repository's real checker (``bvm_lint``) on every fixture
vault. ``--check`` is fail-closed and anti-rigging: a broken vault must
produce *exactly* the diagnostic codes its EXPECTED.json declares — any
unexpected extra diagnostic fails the check — and every fixed vault must
pass ``--strict`` with zero findings. Python 3.11+, stdlib only, no
network, and no writes outside lab/output/.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LAB_ROOT.parent
CASES_DIR = LAB_ROOT / "cases"
SCENARIOS_DIR = LAB_ROOT / "scenarios"
OUTPUT_DIR = LAB_ROOT / "output"

sys.path.insert(0, str(REPO_ROOT / "src"))
from bvm_lint.lint import lint_vault  # noqa: E402

CASE_ORDER = (
    "01-missing-review",
    "02-missing-reference",
    "03-candidate-byte-mismatch",
    "04-active-receipt-conflict",
    "05-review-byte-mismatch",
)
SCENARIO_ORDER = (
    "01-shared-source-convergence",
    "02-edit-or-supersede",
    "03-proxy-or-governed-object",
    "04-green-checker-or-true-claim",
)
EXPECTED_REQUIRED_KEYS = {
    "schema", "case_id", "title", "spec_must", "broken_codes", "fixed_codes",
    "primary_code", "primary_path", "prediction_prompt", "does_not_prove",
}
SCENARIO_REQUIRED_KEYS = {
    "schema", "title", "situation", "question", "choices", "answer_key",
    "explanations",
}
# The fixtures must stay inside the fictional Cedar Lane world. Anything on
# this list appearing in a fixture is a leak, and --check fails on it.
FICTION_FORBIDDEN = re.compile(
    r"(?i)example\.com|acme|@[a-z0-9.-]+\.[a-z]{2,}|(?:^|[^a-z])(darpa|kuramoto)(?:[^a-z]|$)"
)

RULE = "-" * 72


def load_strict_json(path: Path) -> dict:
    def no_dupes(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON member: {key}")
            out[key] = value
        return out
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_dupes)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def run_checker(vault: Path):
    """Run the real checker; return (error_codes, rendered issue lines)."""
    report = lint_vault(vault)
    codes = sorted({issue.code for issue in report.issues})
    lines = [
        f"{issue.severity.upper()} {issue.code} {issue.path}: {issue.message}"
        for issue in sorted(report.issues)
    ]
    return codes, lines, report


def vault_diff(broken: Path, fixed: Path) -> list[str]:
    """Unified diff of the repair, computed live from the two trees."""
    broken_files = {p.relative_to(broken).as_posix(): p for p in broken.rglob("*") if p.is_file()}
    fixed_files = {p.relative_to(fixed).as_posix(): p for p in fixed.rglob("*") if p.is_file()}
    lines: list[str] = []
    for rel in sorted(set(broken_files) | set(fixed_files)):
        before = broken_files[rel].read_text(encoding="utf-8").splitlines(keepends=True) if rel in broken_files else []
        after = fixed_files[rel].read_text(encoding="utf-8").splitlines(keepends=True) if rel in fixed_files else []
        if before == after:
            continue
        lines.extend(difflib.unified_diff(
            before, after, fromfile=f"broken-vault/{rel}", tofile=f"fixed-vault/{rel}", n=2))
    return [line.rstrip("\n") for line in lines]


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------

def check_case(case_id: str, problems: list[str]) -> None:
    case_dir = CASES_DIR / case_id
    for required in ("EXPECTED.json", "WHY.md", "broken-vault", "fixed-vault"):
        if not (case_dir / required).exists():
            problems.append(f"{case_id}: missing {required}")
            return
    try:
        expected = load_strict_json(case_dir / "EXPECTED.json")
    except (ValueError, OSError) as exc:
        problems.append(f"{case_id}: EXPECTED.json unreadable: {exc}")
        return
    missing_keys = EXPECTED_REQUIRED_KEYS - set(expected)
    if missing_keys:
        problems.append(f"{case_id}: EXPECTED.json missing keys: {sorted(missing_keys)}")
        return
    declared = sorted(expected["broken_codes"])
    if expected["primary_code"] not in declared:
        problems.append(f"{case_id}: primary_code not in broken_codes")

    broken_codes, broken_lines, _ = run_checker(case_dir / "broken-vault")
    if broken_codes != declared:
        problems.append(
            f"{case_id}: broken-vault produced {broken_codes}, EXPECTED declares {declared} "
            "(exact match required; unexpected diagnostics are a failure)")
    if not any(expected["primary_path"] in line and expected["primary_code"] in line
               for line in broken_lines):
        problems.append(
            f"{case_id}: primary diagnostic {expected['primary_code']} not reported "
            f"on {expected['primary_path']}")

    fixed_codes, _, fixed_report = run_checker(case_dir / "fixed-vault")
    if fixed_codes != sorted(expected["fixed_codes"]) or fixed_report.issues:
        problems.append(f"{case_id}: fixed-vault is not clean under --strict: {fixed_codes}")

    for path in sorted(case_dir.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".json", ".toml", ".txt"}:
            continue
        match = FICTION_FORBIDDEN.search(path.read_text(encoding="utf-8"))
        if match:
            problems.append(
                f"{case_id}: fictional-boundary leak in {path.relative_to(case_dir)}: "
                f"{match.group(0)!r}")


def check_scenarios(problems: list[str]) -> None:
    for scenario_id in SCENARIO_ORDER:
        path = SCENARIOS_DIR / f"{scenario_id}.json"
        if not path.is_file():
            problems.append(f"scenario {scenario_id}: file missing")
            continue
        try:
            data = load_strict_json(path)
        except (ValueError, OSError) as exc:
            problems.append(f"scenario {scenario_id}: unreadable: {exc}")
            continue
        missing = SCENARIO_REQUIRED_KEYS - set(data)
        if missing:
            problems.append(f"scenario {scenario_id}: missing keys {sorted(missing)}")
            continue
        keys = [choice.get("key") for choice in data["choices"]]
        if len(keys) < 2 or len(keys) != len(set(keys)):
            problems.append(f"scenario {scenario_id}: choices must be >=2 with unique keys")
        if data["answer_key"] not in keys:
            problems.append(f"scenario {scenario_id}: answer_key not among choices")
        if set(data["explanations"]) != set(keys):
            problems.append(f"scenario {scenario_id}: explanations must cover every choice exactly")


def check_surfaces(problems: list[str]) -> None:
    for rel in (
        "lab/README.md",
        "lab/FIELD_REPORT.md",
        "lab/challenge/README.md",
        "lab/challenge/HALL_OF_CATCHES.md",
        ".github/ISSUE_TEMPLATE/attack.yml",
    ):
        if not (REPO_ROOT / rel).is_file():
            problems.append(f"missing lab surface: {rel}")


def run_check() -> int:
    problems: list[str] = []
    for case_id in CASE_ORDER:
        check_case(case_id, problems)
    check_scenarios(problems)
    check_surfaces(problems)
    if problems:
        print("VAULT LAB CHECK FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"VAULT LAB CHECK PASS ({len(CASE_ORDER)} cases, "
          f"{len(SCENARIO_ORDER)} scenarios, surfaces present)")
    return 0


# ---------------------------------------------------------------------------
# guided mode
# ---------------------------------------------------------------------------

def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        raise SystemExit(0)


def pause() -> None:
    ask("\n[enter to continue] ")


def show_codes_help() -> None:
    print("If you want a hint, the five codes in play across the lab are:")
    print("  BVM016 reference does not resolve   BVM024 contradicting receipts")
    print("  BVM031 no qualifying review         BVM033 promotion binding broken")
    print("  BVM037 review not bound to bytes")


def guided_case(case_id: str) -> None:
    case_dir = CASES_DIR / case_id
    expected = load_strict_json(case_dir / "EXPECTED.json")
    broken = case_dir / "broken-vault"
    fixed = case_dir / "fixed-vault"

    print(f"\n{RULE}\nCASE {expected['case_id']}: {expected['title']}\n{RULE}")
    print("\n[1/6] THE RULE ON TRIAL\n")
    print(expected["spec_must"])
    print("\nThe vault you are about to check is the fictional Cedar Lane")
    print("community garden's seed inventory. Something in it violates the")
    print("rule above.")

    print("\n[2/6] PREDICT\n")
    print(expected["prediction_prompt"])
    show_codes_help()
    guess = ask("\nYour prediction (code(s), or just enter to skip): ").upper()
    predicted = set(re.findall(r"BVM\d{3}", guess))

    print("\n[3/6] BREAK — running the real checker on broken-vault\n")
    print(f"  $ python -m bvm_lint lab/cases/{case_id}/broken-vault --strict\n")
    codes, lines, _ = run_checker(broken)
    for line in lines:
        print(f"  {line}")
    print(f"\n  exit status: 1 (FAIL) — codes: {', '.join(codes)}")
    if predicted:
        hit = predicted & set(codes)
        verdict = "exactly right" if predicted == set(codes) else (
            f"partial — you named {', '.join(sorted(hit)) or 'none'} of {', '.join(codes)}")
        print(f"  your prediction was {verdict}.")

    print("\n[4/6] WHY\n")
    print((case_dir / "WHY.md").read_text(encoding="utf-8"))
    pause()

    print("[5/6] THE REPAIR — exact diff, broken-vault -> fixed-vault\n")
    for line in vault_diff(broken, fixed):
        print(f"  {line}")

    print("\n[6/6] PROVE IT — running the checker on fixed-vault\n")
    print(f"  $ python -m bvm_lint lab/cases/{case_id}/fixed-vault --strict\n")
    fixed_codes, _, report = run_checker(fixed)
    if not report.issues:
        print("  PASS: structural conformance established — zero findings.")
    else:  # should be unreachable when fixtures are healthy
        print(f"  UNEXPECTED: {fixed_codes}")
    print(f"\n  Remember what green does NOT prove: {expected['does_not_prove']}")
    pause()


def guided_scenario(scenario_id: str) -> None:
    data = load_strict_json(SCENARIOS_DIR / f"{scenario_id}.json")
    print(f"\n{RULE}\nSCENARIO: {data['title']}\n{RULE}\n")
    print(data["situation"])
    print(f"\n{data['question']}\n")
    for choice in data["choices"]:
        print(f"  [{choice['key']}] {choice['label']}")
    keys = {choice["key"] for choice in data["choices"]}
    answer = ""
    while answer not in keys:
        answer = ask("\nYour call: ").lower()
    print()
    marker = "That is the method answer." if answer == data["answer_key"] else (
        f"The method answer is [{data['answer_key']}].")
    print(marker + "\n")
    for choice in data["choices"]:
        key = choice["key"]
        tag = "METHOD" if key == data["answer_key"] else "  no  "
        print(f"[{tag}] ({key}) {data['explanations'][key]}\n")
    pause()


def run_guided() -> int:
    print(RULE)
    print("VAULT LAB — break the BAION Vault Method, on purpose, five ways")
    print(RULE)
    print("""
Each case is a pair of small fictional vaults: one broken, one repaired.
You predict what the checker will say, watch it fail, read why, study the
exact repair diff, and watch it pass. The checker is the repository's real
bvm-lint — nothing here is mocked.

Then four judgment scenarios cover what the checker can NOT decide for
you, and the challenge invites you to break the method yourself.
""")
    for case_id in CASE_ORDER:
        guided_case(case_id)

    print(f"\n{RULE}\nJUDGMENT SCENARIOS — the checker stops here; you do not\n{RULE}")
    if ask("\nRun the four judgment scenarios? [Y/n] ").lower() not in {"n", "no"}:
        for scenario_id in SCENARIO_ORDER:
            guided_scenario(scenario_id)

    print(f"\n{RULE}\nWHERE TO GO NEXT\n{RULE}\n")
    print("- The challenge: violate a specific MUST in SPEC.md while the")
    print("  checker stays green. Rules: lab/challenge/README.md")
    print("- Tell us what happened (five minutes, template provided):")
    print("  lab/FIELD_REPORT.md")
    print("- Verify this lab yourself anytime: lab/start.sh --check\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vault-lab",
        description="Guided break/repair lab for the BAION Vault Method.")
    parser.add_argument("--check", action="store_true",
                        help="non-interactive fixture verification (CI mode)")
    args = parser.parse_args(argv)
    OUTPUT_DIR.mkdir(exist_ok=True)
    if args.check:
        return run_check()
    return run_guided()


if __name__ == "__main__":
    sys.exit(main())
