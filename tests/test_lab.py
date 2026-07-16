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


if __name__ == "__main__":
    unittest.main()
