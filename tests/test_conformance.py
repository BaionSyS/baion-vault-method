from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bvm_lint.lint import lint_vault
from bvm_lint.util import compare_semver


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/tutorial-vault"


def codes(report) -> set[str]:
    return {issue.code for issue in report.errors}


def update_metadata(path: Path, mutate) -> None:
    text = path.read_text(encoding="utf-8")
    prefix = "<!-- bvm\n"
    marker = "\n-->"
    if not text.startswith(prefix) or marker not in text:
        raise AssertionError(f"missing BVM metadata block: {path}")
    end = text.index(marker)
    metadata = json.loads(text[len(prefix):end])
    mutate(metadata)
    body = text[end + len(marker):].lstrip("\n")
    path.write_text(prefix + json.dumps(metadata, indent=2) + marker + "\n" + body, encoding="utf-8")


class ConformanceTests(unittest.TestCase):
    def copy_example(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name) / "vault"
        shutil.copytree(EXAMPLE, root)
        return tmp, root

    def test_complete_example_passes(self) -> None:
        report = lint_vault(EXAMPLE)
        self.assertEqual([], report.errors, report.issues)
        self.assertEqual(3, report.artifacts)
        self.assertGreaterEqual(report.evidence_receipts, 10)

    def test_missing_required_directory_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        shutil.rmtree(root / "RETRACTIONS")
        self.assertIn("BVM001", codes(lint_vault(root)))

    def test_method_version_must_match_vault_schema_series(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "vault.toml"
        text = path.read_text(encoding="utf-8").replace(
            'method_version = "0.1.0"',
            'method_version = "0.2.0"',
        )
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM002", codes(lint_vault(root)))

    def test_unknown_vault_toml_key_is_rejected_not_ignored(self) -> None:
        # The adoption trap from issue #2: the four managed directory names are
        # fixed, a user guesses vault.toml is where that gets relaxed, writes
        # "receipts_dir", and previously got PASS back for a key nothing read.
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "vault.toml"
        with path.open("a", encoding="utf-8") as handle:
            handle.write('receipts_dir = "MY_RECEIPTS"\n')
        self.assertIn("BVM004", codes(lint_vault(root)))

    def test_declared_vault_toml_keys_alone_stay_clean(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        self.assertNotIn("BVM004", codes(lint_vault(root)))

    def test_raw_json_evidence_source_is_not_misread_as_a_receipt(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        (root / "RECEIPTS/data/raw-result.json").write_text('{"value": 1}\n', encoding="utf-8")
        self.assertNotIn("BVM020", codes(lint_vault(root)))

    def test_json_candidate_is_not_misread_as_a_receipt(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        (root / "RECEIPTS/candidates/example.json").write_text('{"candidate": true}\n', encoding="utf-8")
        self.assertNotIn("BVM020", codes(lint_vault(root)))

    def test_invalid_result_value_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata.__setitem__("result", "negativ"))
        self.assertIn("BVM017", codes(lint_vault(root)))

    def test_requires_canon_object_must_be_boolean(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata.__setitem__("requires_canon_object", "true"))
        self.assertIn("BVM017", codes(lint_vault(root)))

    def test_missing_index_version_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "INDEX.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["lineages"]["lineage.adapter-parity"].pop("version")
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM081", codes(lint_vault(root)))

    def test_source_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/data/probe-v2.txt"
        source.write_text(source.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
        self.assertIn("BVM022", codes(lint_vault(root)))

    def test_duplicate_receipt_key_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/probe-v2.json"
        text = path.read_text(encoding="utf-8").replace('"status": "pass",', '"status": "pass",\n  "status": "fail",', 1)
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM020", codes(lint_vault(root)))

    def test_duplicate_metadata_key_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        text = path.read_text(encoding="utf-8").replace('"state": "canon",', '"state": "canon",\n  "state": "working",', 1)
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM010", codes(lint_vault(root)))

    def test_review_must_bind_exact_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        review = root / "RECEIPTS/reviews/independent-review-v1.json"
        data = json.loads(review.read_text(encoding="utf-8"))
        data["artifact_sha256"] = "0" * 64
        review.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = codes(lint_vault(root))
        self.assertIn("BVM037", result)
        self.assertIn("BVM031", result)

    def test_promotion_candidate_must_match_exact_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        candidate = root / "RECEIPTS/candidates/bounded-adapter-parity-v1.0.0.md"
        candidate.write_text(candidate.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assertIn("BVM033", codes(lint_vault(root)))

    def test_proxy_cannot_inherit_canonical_object_claim(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        text = path.read_text(encoding="utf-8").replace('"object_mode": "canonical"', '"object_mode": "proxy"')
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM072", codes(lint_vault(root)))

    def test_negative_claim_requires_control_in_evidence(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "ARCHIVE/adapter-parity-observation-v0.1.0.md"
        update_metadata(
            path,
            lambda metadata: metadata.__setitem__(
                "evidence",
                [ref for ref in metadata["evidence"] if ref != "RECEIPTS/evidence/positive-control-v1.json"],
            ),
        )
        self.assertIn("BVM060", codes(lint_vault(root)))

    def test_aggregate_missing_unit_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(
            path,
            lambda metadata: metadata["aggregate"]["unit_receipts"].pop("nested-duplicate"),
        )
        self.assertIn("BVM062", codes(lint_vault(root)))

    def test_aggregate_unit_receipt_must_match_unit(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/unit-valid-order.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["unit_id"] = "wrong-unit"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM063", codes(lint_vault(root)))

    def test_orphaned_archive_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        orphan = root / "ARCHIVE/orphan-v0.1.0.md"
        text = (root / "ARCHIVE/adapter-parity-observation-v0.1.0.md").read_text(encoding="utf-8")
        text = text.replace('"artifact_id": "artifact.adapter-parity.v0_1_0"', '"artifact_id": "artifact.orphan.v0_1_0"')
        text = text.replace('"lineage_id": "lineage.adapter-parity"', '"lineage_id": "lineage.orphan"')
        orphan.write_text(text, encoding="utf-8")
        self.assertIn("BVM044", codes(lint_vault(root)))

    def test_negative_existence_requires_authoritative_search(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        text = path.read_text(encoding="utf-8").replace('"result": "positive",', '"result": "positive",\n  "claim_type": "negative-existence",')
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM064", codes(lint_vault(root)))

    def test_handoff_requires_continuity_sections(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        text = path.read_text(encoding="utf-8").replace('## Stop conditions', '## Finish')
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_handoff_heading_does_not_accept_unverified_as_verified(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        text = path.read_text(encoding="utf-8").replace(
            "## Verified or completed",
            "## Unverified work",
        )
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_handoff_headings_inside_a_code_fence_do_not_satisfy_sections(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        text = path.read_text(encoding="utf-8")
        # A required heading demoted into a fenced code block is example text,
        # not a real section: BVM090 must still fire (BVM-01 false closure).
        self.assertIn("## Stop conditions", text)
        text = text.replace("## Stop conditions", "```\n## Stop conditions\n```")
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_path_escape_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        text = path.read_text(encoding="utf-8").replace('"RECEIPTS/evidence/probe-v2.json"', '"../../../outside.json"', 1)
        path.write_text(text, encoding="utf-8")
        self.assertIn("BVM016", codes(lint_vault(root)))

    def test_retraction_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RETRACTIONS/retract-adapter-parity-v0.1.0.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["artifact_sha256"] = "0" * 64
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM051", codes(lint_vault(root)))

    def test_index_version_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "INDEX.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["lineages"]["lineage.adapter-parity"]["version"] = "9.9.9"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM081", codes(lint_vault(root)))

    def test_duplicate_artifact_id_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        duplicate = root / "HANDOFFS/tutorial-handoff-v0.1.1.md"
        duplicate.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        self.assertIn("BVM011", codes(lint_vault(root)))


    def test_nonstandard_json_constant_is_rejected(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/probe-v2.json"
        source = path.read_text(encoding="utf-8")
        path.write_text(source.replace('"status": "pass",', '"score": NaN,\n  "status": "pass",', 1), encoding="utf-8")
        self.assertIn("BVM020", codes(lint_vault(root)))

    def test_invalid_semver_prerelease_is_rejected(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata.__setitem__("version", "1.0.0-01"))
        self.assertIn("BVM014", codes(lint_vault(root)))

    def test_semver_precedence_handles_prerelease_and_build_metadata(self) -> None:
        self.assertGreater(compare_semver("1.0.0", "1.0.0-rc.1"), 0)
        self.assertGreater(compare_semver("1.0.0-rc.10", "1.0.0-rc.2"), 0)
        self.assertEqual(compare_semver("1.0.0+build.2", "1.0.0+build.1"), 0)

    def test_version_parity_check_catches_template_drift(self) -> None:
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "release"
        files = (
            "pyproject.toml",
            "README.md",
            "SPEC.md",
            "CHANGELOG.md",
            "CITATION.cff",
            "src/bvm_lint/__init__.py",
            "examples/tutorial-vault/vault.toml",
            "templates/vault.toml",
        )
        for relative_path in files:
            source = ROOT / relative_path
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        template = root / "templates/vault.toml"
        template.write_text(
            template.read_text(encoding="utf-8").replace(
                'method_version = "0.1.0"',
                'method_version = "0.1.1"',
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_version_parity.py"), str(root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("templates/vault.toml", completed.stdout)

    def test_version_parity_check_rejects_method_series_escape(self) -> None:
        # A method version outside the 0.1.x series must fail parity even if
        # every method file agrees on it -- bvm-lint's BVM002 gate would
        # reject the repository's own templates (the defect that made a
        # single-string 0.2.0 bump impossible).
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "release"
        files = (
            "pyproject.toml",
            "README.md",
            "SPEC.md",
            "CHANGELOG.md",
            "CITATION.cff",
            "src/bvm_lint/__init__.py",
            "examples/tutorial-vault/vault.toml",
            "templates/vault.toml",
        )
        for relative_path in files:
            source = ROOT / relative_path
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        spec = root / "SPEC.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                "**Version:** 0.1.0",
                "**Version:** 0.2.0",
            ),
            encoding="utf-8",
        )
        for vault_toml in ("templates/vault.toml", "examples/tutorial-vault/vault.toml"):
            path = root / vault_toml
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    'method_version = "0.1.0"',
                    'method_version = "0.2.0"',
                ),
                encoding="utf-8",
            )
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_version_parity.py"), str(root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("outside the 0.1.x", completed.stdout)

    def test_requires_canonical_object_mode_is_explicit(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata.pop("object_mode"))
        self.assertIn("BVM072", codes(lint_vault(root)))

    def test_promotion_binds_evidence_receipt_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["scope"] += " Edited after promotion."
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertIn("BVM033", codes(lint_vault(root)))

    def test_promotion_binds_review_receipt_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/reviews/independent-review-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["notes"] += " Edited after promotion."
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertIn("BVM033", codes(lint_vault(root)))

    def test_index_binds_promotion_receipt_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/promotions/promote-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["decision_by"] = "different-operator"
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertIn("BVM082", codes(lint_vault(root)))

    def test_promotion_duplicate_inputs_are_rejected_without_crash(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/promotions/promote-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["evidence"].append(data["evidence"][0])
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = codes(lint_vault(root))
        self.assertIn("BVM025", result)
        self.assertIn("BVM033", result)

    def test_malformed_promotion_input_type_is_reported_without_crash(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/promotions/promote-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["evidence"] = None
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = codes(lint_vault(root))
        self.assertIn("BVM025", result)
        self.assertIn("BVM033", result)

    def test_same_applicability_pass_fail_conflict_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe-v2-conflict"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["status"] = "fail"
        target = root / "RECEIPTS/evidence/probe-v2-conflict.json"
        target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertIn("BVM024", codes(lint_vault(root)))

    def test_different_applicability_pass_fail_is_not_false_conflict(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe-other-scope"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["status"] = "fail"
        data["applicability_id"] = "adapter-parity.other-corpus"
        target = root / "RECEIPTS/evidence/probe-other-scope.json"
        target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertNotIn("BVM024", codes(lint_vault(root)))

    def test_receipt_cannot_supersede_a_different_applicability_boundary(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe-v2-superseder"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["applicability_id"] = "adapter-parity.other-corpus"
        data["supersedes_receipt"] = "RECEIPTS/evidence/probe-v2.json"
        target = root / "RECEIPTS/evidence/probe-v2-superseder.json"
        target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertIn("BVM025", codes(lint_vault(root)))

    def test_handoff_requires_durable_authority_metadata(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        update_metadata(path, lambda metadata: metadata.pop("authority_sources"))
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_handoff_current_state_must_point_to_canon_or_index(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        update_metadata(path, lambda metadata: metadata.__setitem__("current_state", ["README.md"]))
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_handoff_current_state_rejects_unmanaged_file_under_canon(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "HANDOFFS/tutorial-handoff-v0.1.0.md"
        update_metadata(
            path,
            lambda metadata: metadata.__setitem__(
                "current_state",
                ["CANON/objects/reference_normalizer.py"],
            ),
        )
        self.assertIn("BVM090", codes(lint_vault(root)))

    def test_review_must_postdate_final_artifact_bytes(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/reviews/independent-review-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["reviewed_utc"] = "2026-07-15T13:11:00Z"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = codes(lint_vault(root))
        self.assertIn("BVM026", result)
        self.assertIn("BVM031", result)

    def test_promotion_must_follow_review(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/promotions/promote-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["promoted_utc"] = "2026-07-15T13:14:00Z"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM036", codes(lint_vault(root)))

    def test_retraction_cannot_predate_replacement(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RETRACTIONS/retract-adapter-parity-v0.1.0.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["retracted_utc"] = "2026-07-15T13:19:00Z"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM053", codes(lint_vault(root)))

    def test_receipt_supersession_requires_same_subject_and_kind(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe.v2.bad-supersession"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["supersedes_receipt"] = "RECEIPTS/evidence/probe-v1.json"
        target = root / "RECEIPTS/evidence/probe-v2-bad-supersession.json"
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM025", codes(lint_vault(root)))

    def test_receipt_supersession_must_move_forward_in_time(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe.v2.stale-correction"
        data["captured_utc"] = "2026-07-15T13:04:00Z"
        data["supersedes_receipt"] = "RECEIPTS/evidence/probe-v2.json"
        target = root / "RECEIPTS/evidence/probe-v2-stale-correction.json"
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM026", codes(lint_vault(root)))

    def test_canon_cannot_cite_superseded_receipt(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe.v2.corrected"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["supersedes_receipt"] = "RECEIPTS/evidence/probe-v2.json"
        target = root / "RECEIPTS/evidence/probe-v2-corrected.json"
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM023", codes(lint_vault(root)))

    def test_active_conflicting_receipts_require_supersession(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        source = root / "RECEIPTS/evidence/probe-v2.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["receipt_id"] = "receipt.probe.v2.conflict"
        data["captured_utc"] = "2026-07-15T13:11:00Z"
        data["status"] = "fail"
        target = root / "RECEIPTS/evidence/probe-v2-conflict.json"
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        artifact = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(artifact, lambda metadata: metadata["evidence"].append("RECEIPTS/evidence/probe-v2-conflict.json"))
        self.assertIn("BVM024", codes(lint_vault(root)))

    def test_duplicate_evidence_reference_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata["evidence"].append(metadata["evidence"][0]))
        self.assertIn("BVM018", codes(lint_vault(root)))

    def test_executed_object_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/objects/reference_normalizer.py"
        path.write_text(path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
        self.assertIn("BVM022", codes(lint_vault(root)))

    def test_candidate_object_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "WORKING/objects/candidate_normalizer.py"
        path.write_text(path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
        self.assertIn("BVM022", codes(lint_vault(root)))

    def test_corpus_input_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "WORKING/corpus/corpus-v2.tsv"
        path.write_text(path.read_text(encoding="utf-8") + "extra\taccept\t{}\n", encoding="utf-8")
        self.assertIn("BVM022", codes(lint_vault(root)))


    def test_positive_control_receipt_must_pass(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/positive-control-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "fail"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM061", codes(lint_vault(root)))

    def test_authoritative_search_requires_boundary(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        receipt_path = root / "RECEIPTS/evidence/authoritative-search.json"
        source = root / "RECEIPTS/data/probe-v2.txt"
        source_hash = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
        receipt = {
            "schema": "bvm-receipt/0.1",
            "receipt_id": "receipt.authoritative-search.v1",
            "subject_id": "artifact.adapter-parity.v1_0_0",
            "kind": "authoritative-search",
            "captured_utc": "2026-07-15T13:11:00Z",
            "status": "observed",
            "scope": "Search the declared authority for counterexamples.",
            "source": "RECEIPTS/data/probe-v2.txt",
            "source_sha256": source_hash,
            "authority": "fictional registry",
            "procedure": "exact lookup",
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        artifact = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        def mutate(metadata):
            metadata["claim_type"] = "negative-existence"
            metadata["authoritative_search_receipt"] = "RECEIPTS/evidence/authoritative-search.json"
            metadata["evidence"].append("RECEIPTS/evidence/authoritative-search.json")
        update_metadata(artifact, mutate)
        self.assertIn("BVM065", codes(lint_vault(root)))

    def test_canonical_object_receipt_must_have_executed_kind(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/evidence/executed-reference-object.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["kind"] = "probe"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM071", codes(lint_vault(root)))

    def test_retraction_replacement_hash_mismatch_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RETRACTIONS/retract-adapter-parity-v0.1.0.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["replacement_sha256"] = "0" * 64
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM052", codes(lint_vault(root)))

    def test_superseding_version_must_increase(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata.__setitem__("version", "0.1.0"))
        self.assertIn("BVM042", codes(lint_vault(root)))

    def test_artifact_supersession_cycle_is_caught(self) -> None:
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "ARCHIVE/adapter-parity-observation-v0.1.0.md"
        def mutate(metadata):
            metadata["version"] = "1.1.0"
            metadata["supersedes"] = "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, mutate)
        self.assertIn("BVM041", codes(lint_vault(root)))


    def test_self_review_class_bypass_via_case_and_whitespace_is_caught(self) -> None:
        # A writer-self-check identity spelled with off-case letters and stray
        # whitespace ("Self ") must still be treated as a self review, so the
        # canon artifact loses its only qualifying non-self review (BVM031).
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "RECEIPTS/reviews/independent-review-v1.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["reviewer_class"] = "Self "
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertIn("BVM031", codes(lint_vault(root)))

    def test_uppercase_markdown_extension_is_not_skipped(self) -> None:
        # A managed file named with an uppercase .MD extension must still be
        # discovered and linted; skipping it would let it escape metadata checks.
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        (root / "CANON" / "STRAY.MD").write_text("no bvm metadata block\n", encoding="utf-8")
        self.assertIn("BVM010", codes(lint_vault(root)))

    def test_aliased_duplicate_reference_is_caught(self) -> None:
        # ./RECEIPTS/... and RECEIPTS/... name the same path; a raw-string dedup
        # would miss the collision, so the alias must still trip BVM018.
        tmp, root = self.copy_example(); self.addCleanup(tmp.cleanup)
        path = root / "CANON/bounded-adapter-parity-v1.0.0.md"
        update_metadata(path, lambda metadata: metadata["evidence"].append("./" + metadata["evidence"][0]))
        self.assertIn("BVM018", codes(lint_vault(root)))


if __name__ == "__main__":
    unittest.main()
