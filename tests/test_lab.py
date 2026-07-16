"""Vault Lab fixtures must fail and pass for exactly the declared reasons.

These tests duplicate the intent of ``lab/start.sh --check`` inside the
unittest suite so a fixture regression fails CI twice — once here with a
readable assertion, once in the lab's own fail-closed check.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from bvm_lint.lint import lint_vault  # noqa: E402

CASES_DIR = REPO_ROOT / "lab" / "cases"
EXPECTED_CASES = {
    "01-missing-review": ["BVM031"],
    "02-missing-reference": ["BVM016", "BVM033"],
    "03-candidate-byte-mismatch": ["BVM033"],
    "04-active-receipt-conflict": ["BVM024"],
    "05-review-byte-mismatch": ["BVM031", "BVM033", "BVM037"],
}


def error_codes(vault: Path) -> list[str]:
    return sorted({issue.code for issue in lint_vault(vault).issues})


class LabFixtureTests(unittest.TestCase):
    def test_case_directories_match_this_suite(self) -> None:
        on_disk = sorted(p.name for p in CASES_DIR.iterdir() if p.is_dir())
        self.assertEqual(on_disk, sorted(EXPECTED_CASES))

    def test_broken_vaults_fire_exactly_the_declared_codes(self) -> None:
        for case_id, declared in EXPECTED_CASES.items():
            with self.subTest(case=case_id):
                expected = json.loads(
                    (CASES_DIR / case_id / "EXPECTED.json").read_text(encoding="utf-8"))
                self.assertEqual(sorted(expected["broken_codes"]), declared,
                                 "EXPECTED.json disagrees with the test suite")
                self.assertEqual(error_codes(CASES_DIR / case_id / "broken-vault"),
                                 declared)

    def test_fixed_vaults_are_clean_under_strict(self) -> None:
        for case_id in EXPECTED_CASES:
            with self.subTest(case=case_id):
                report = lint_vault(CASES_DIR / case_id / "fixed-vault")
                self.assertEqual([issue.to_dict() for issue in report.issues], [])

    def test_lab_check_mode_passes(self) -> None:
        result = subprocess.run(
            ["sh", str(REPO_ROOT / "lab" / "start.sh"), "--check"],
            capture_output=True, text=True, check=False, cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VAULT LAB CHECK PASS", result.stdout)

    def test_fixture_generator_is_deterministic_and_current(self) -> None:
        """Regenerating fixtures must not change a single committed byte."""
        before = {
            path.relative_to(CASES_DIR).as_posix(): path.read_bytes()
            for path in CASES_DIR.rglob("*") if path.is_file()
        }
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "lab" / "tools" / "build_fixtures.py")],
            capture_output=True, text=True, check=False, cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {
            path.relative_to(CASES_DIR).as_posix(): path.read_bytes()
            for path in CASES_DIR.rglob("*") if path.is_file()
        }
        self.assertEqual(sorted(before), sorted(after))
        for rel, data in before.items():
            self.assertEqual(data, after[rel], f"regeneration changed {rel}")


GUIDED_INPUT = "\n\n\n" * 5 + "n\n"  # per case: predict, WHY pause, prove pause; then skip scenarios
FINAL_CLAIM = ("PASS means the checker found no declared structural violation in "
               "these fixtures. It does not prove the seed inventory claim is "
               "true, complete, safe, or decision-grade.")
BOUNDARY = "This lab contains fictional records."

STUB_LINT_TEMPLATE = '''\
from dataclasses import dataclass


@dataclass(order=True)
class Issue:
    severity: str = "error"
    code: str = "BVM999"
    path: str = "stub/record.md"
    message: str = "stub finding"

    def to_dict(self):
        return {{"code": self.code}}


class Report:
    def __init__(self, issues):
        self.issues = issues


def lint_vault(vault):
    return Report({issues})
'''


def run_lab(repo_root: Path, *args: str, stdin_text: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", str(repo_root / "lab" / "start.sh"), *args],
        input=stdin_text, capture_output=True, text=True, check=False,
        cwd=repo_root)


class LabFailClosedTests(unittest.TestCase):
    """Spec v0.3.0 §6-R C/D + merge gates 5/6/14: the guided run must exit
    nonzero on any expectation drift and emit the exact bounded-claim
    sentence once, only on a fully healthy run. The mutation tests reproduce
    the two adversarial checker substitutions from the 2026-07-16 GPT
    advisory (zero-findings stub; unexpected-BVM999 stub)."""

    def test_healthy_guided_run_exits_zero_and_claims_once(self) -> None:
        result = run_lab(REPO_ROOT, stdin_text=GUIDED_INPUT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count(FINAL_CLAIM), 1, result.stdout)
        self.assertEqual(result.stdout.count(BOUNDARY), 1, result.stdout)

    def test_guided_eof_quit_is_clean_and_makes_no_claim(self) -> None:
        result = run_lab(REPO_ROOT, stdin_text="")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(FINAL_CLAIM, result.stdout)

    def _mutated_tree(self, tmp: str, issues_literal: str) -> Path:
        """Copy the lab into tmp with a stub checker shadowing bvm_lint."""
        import shutil
        root = Path(tmp) / "mutated"
        shutil.copytree(REPO_ROOT / "lab", root / "lab")
        issue_form = root / ".github" / "ISSUE_TEMPLATE" / "attack.yml"
        issue_form.parent.mkdir(parents=True)
        shutil.copy(REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "attack.yml", issue_form)
        stub = root / "src" / "bvm_lint"
        stub.mkdir(parents=True)
        (stub / "__init__.py").write_text("", encoding="utf-8")
        (stub / "lint.py").write_text(
            STUB_LINT_TEMPLATE.format(issues=issues_literal), encoding="utf-8")
        return root

    def _assert_fails_closed(self, root: Path) -> None:
        guided = run_lab(root, stdin_text=GUIDED_INPUT)
        self.assertNotEqual(guided.returncode, 0,
                            "guided run exited 0 under a drifted checker:\n"
                            + guided.stdout + guided.stderr)
        self.assertNotIn(FINAL_CLAIM, guided.stdout)
        check = run_lab(root, "--check")
        self.assertNotEqual(check.returncode, 0,
                            "--check exited 0 under a drifted checker:\n"
                            + check.stdout + check.stderr)

    def test_mutation_zero_findings_checker_fails_closed(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._assert_fails_closed(self._mutated_tree(tmp, "[]"))

    def test_mutation_unexpected_finding_fails_closed(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._assert_fails_closed(self._mutated_tree(tmp, "[Issue()]"))


if __name__ == "__main__":
    unittest.main()
