from __future__ import annotations

import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .model import Artifact, Issue, LintReport
from .util import (
    extract_metadata,
    is_semver,
    is_sha256,
    is_utc,
    load_json,
    markdown_body,
    compare_semver,
    parse_utc,
    relative,
    safe_reference,
    semver_tuple,
    sha256_file,
)


REQUIRED_DIRECTORIES = ("INBOX", "WORKING", "CANON", "RECEIPTS", "RETRACTIONS", "HANDOFFS", "ARCHIVE")
MANAGED_STATES = {
    "WORKING": "working",
    "CANON": "canon",
    "HANDOFFS": "handoff",
    "ARCHIVE": "archive",
}
REQUIRED_ARTIFACT_FIELDS = (
    "schema",
    "artifact_id",
    "lineage_id",
    "title",
    "state",
    "version",
    "created_utc",
    "updated_utc",
)
SELF_REVIEW_CLASSES = {"writer-self-check", "self", "same-writer"}
OBJECT_MODES = {"canonical", "proxy", "mixed", "not-applicable"}
HANDOFF_HEADING_GROUPS: dict[str, tuple[str, ...]] = {
    "objective and scope": ("objective", "objectives", "scope", "scopes"),
    "current canon": ("current canon", "authority", "authorities"),
    "verified work": ("verified", "completed"),
    "unknowns or contradictions": ("unknown", "unknowns", "contradiction", "contradictions"),
    "proposed next actions": ("next action", "next actions", "proposed"),
    "stop conditions": ("stop condition", "stop conditions", "stop rule", "stop rules"),
}


def receipt_applicability_key(receipt: dict[str, Any]) -> str:
    declared = receipt.get("applicability_id")
    if isinstance(declared, str) and declared.strip():
        return "id:" + declared.strip()
    scope = re.sub(r"\s+", " ", str(receipt.get("scope", "")).strip().casefold())
    return "scope:" + scope


class VaultLinter:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.report = LintReport(root=self.root, checker_version=__version__)
        self.artifacts_by_path: dict[str, Artifact] = {}
        self.artifacts_by_id: dict[str, Artifact] = {}
        self.evidence: dict[str, dict[str, Any]] = {}
        self.reviews: dict[str, dict[str, Any]] = {}
        self.promotions: dict[str, dict[str, Any]] = {}
        self.retractions: dict[str, dict[str, Any]] = {}
        self.superseded_receipt_paths: set[str] = set()
        self.incoming_supersession: set[str] = set()
        self.retracted_paths: set[str] = set()
        self.index: dict[str, Any] | None = None

    def issue(self, code: str, path: str | Path, message: str, severity: str = "error") -> None:
        rendered = path if isinstance(path, str) else relative(self.root, path)
        self.report.issues.append(Issue(code=code, severity=severity, path=rendered, message=message))

    def run(self) -> LintReport:
        if not self.root.exists() or not self.root.is_dir():
            self.issue("BVM001", ".", f"vault root does not exist or is not a directory: {self.root}")
            return self.report
        self._check_structure()
        self._load_config()
        self._load_index()
        self._load_artifacts()
        self._load_receipts()
        self._load_retractions()
        self._validate_receipt_supersession()
        self._validate_artifacts()
        self._validate_supersession_graph()
        self._validate_retractions()
        self._validate_archive_reachability()
        self._validate_index()
        self._validate_active_receipt_conflicts()
        self.report.artifacts = len(self.artifacts_by_path)
        self.report.evidence_receipts = len(self.evidence)
        self.report.review_receipts = len(self.reviews)
        self.report.promotion_receipts = len(self.promotions)
        self.report.retractions = len(self.retractions)
        return self.report

    def _check_structure(self) -> None:
        for filename in ("vault.toml", "INDEX.json"):
            path = self.root / filename
            if not path.is_file():
                self.issue("BVM001", filename, "required file is missing")
        for dirname in REQUIRED_DIRECTORIES:
            path = self.root / dirname
            if not path.is_dir():
                self.issue("BVM001", dirname, "required directory is missing")

    def _load_config(self) -> None:
        path = self.root / "vault.toml"
        if not path.is_file():
            return
        try:
            with path.open("rb") as handle:
                config = tomllib.load(handle)
        except (tomllib.TOMLDecodeError, OSError) as exc:
            self.issue("BVM002", path, f"cannot parse vault.toml: {exc}")
            return
        if config.get("schema") != "bvm-vault/0.1":
            self.issue("BVM002", path, "schema must be 'bvm-vault/0.1'")
        if not isinstance(config.get("name"), str) or not config.get("name", "").strip():
            self.issue("BVM002", path, "name must be a non-empty string")
        method_version = config.get("method_version")
        if not is_semver(method_version):
            self.issue("BVM002", path, "method_version must be semantic versioning syntax")
        elif semver_tuple(method_version)[:2] != (0, 1):
            self.issue(
                "BVM002",
                path,
                "method_version must be compatible with schema bvm-vault/0.1 (expected 0.1.x)",
            )

    def _load_index(self) -> None:
        path = self.root / "INDEX.json"
        if not path.is_file():
            return
        try:
            data = load_json(path)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self.issue("BVM003", path, f"cannot parse INDEX.json: {exc}")
            return
        if data.get("schema") != "bvm-index/0.1":
            self.issue("BVM003", path, "schema must be 'bvm-index/0.1'")
        if not is_utc(data.get("updated_utc")):
            self.issue("BVM003", path, "updated_utc must be valid UTC")
        if not isinstance(data.get("lineages"), dict):
            self.issue("BVM003", path, "lineages must be an object")
        self.index = data

    def _load_artifacts(self) -> None:
        for directory, expected_state in MANAGED_STATES.items():
            base = self.root / directory
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.md")):
                rel = relative(self.root, path)
                try:
                    metadata = extract_metadata(path)
                except (ValueError, json.JSONDecodeError, UnicodeError, OSError) as exc:
                    self.issue("BVM010", path, str(exc))
                    continue
                artifact = Artifact(path=path, relative_path=rel, metadata=metadata, sha256=sha256_file(path))
                self.artifacts_by_path[rel] = artifact
                for field in REQUIRED_ARTIFACT_FIELDS:
                    if not isinstance(metadata.get(field), str) or not str(metadata.get(field)).strip():
                        self.issue("BVM017", path, f"required field '{field}' must be a non-empty string")
                if metadata.get("schema") != "bvm-artifact/0.1":
                    self.issue("BVM017", path, "schema must be 'bvm-artifact/0.1'")
                artifact_id = artifact.artifact_id
                if artifact_id:
                    if artifact_id in self.artifacts_by_id:
                        first = self.artifacts_by_id[artifact_id].relative_path
                        self.issue("BVM011", path, f"artifact_id '{artifact_id}' already used by {first}")
                    else:
                        self.artifacts_by_id[artifact_id] = artifact
                state = artifact.state
                if state not in set(MANAGED_STATES.values()):
                    self.issue("BVM012", path, f"unknown state '{state}'")
                elif state != expected_state:
                    self.issue("BVM013", path, f"state '{state}' does not match directory {directory} ({expected_state})")
                if not is_semver(artifact.version):
                    self.issue("BVM014", path, f"invalid semantic version '{artifact.version}'")
                created = parse_utc(metadata.get("created_utc"))
                updated = parse_utc(metadata.get("updated_utc"))
                if created is None:
                    self.issue("BVM015", path, "created_utc must be valid UTC in YYYY-MM-DDTHH:MM:SSZ form")
                if updated is None:
                    self.issue("BVM015", path, "updated_utc must be valid UTC in YYYY-MM-DDTHH:MM:SSZ form")
                if created is not None and updated is not None and updated < created:
                    self.issue("BVM015", path, "updated_utc predates created_utc")
                object_mode = metadata.get("object_mode")
                if object_mode is not None and object_mode not in OBJECT_MODES:
                    self.issue("BVM017", path, f"object_mode must be one of {sorted(OBJECT_MODES)}")
                result = metadata.get("result")
                if result is not None and result not in {"positive", "negative", "mixed", "inconclusive"}:
                    self.issue("BVM017", path, "result must be positive, negative, mixed, or inconclusive when present")
                requires_object = metadata.get("requires_canon_object")
                if requires_object is not None and not isinstance(requires_object, bool):
                    self.issue("BVM017", path, "requires_canon_object must be a boolean when present")
                claim_type = metadata.get("claim_type")
                if claim_type is not None and (not isinstance(claim_type, str) or not claim_type.strip()):
                    self.issue("BVM017", path, "claim_type must be a non-empty string when present")
                if artifact.state == "handoff":
                    self._validate_handoff_sections(artifact)
                    self._validate_handoff_metadata(artifact)

    def _validate_handoff_sections(self, artifact: Artifact) -> None:
        headings = [
            re.sub(r"\s+", " ", match.group(1).strip().lower())
            for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", markdown_body(artifact.path))
        ]
        missing: list[str] = []
        for label, aliases in HANDOFF_HEADING_GROUPS.items():
            if not any(
                any(
                    re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", heading)
                    for alias in aliases
                )
                for heading in headings
            ):
                missing.append(label)
        if missing:
            self.issue("BVM090", artifact.path, "missing handoff section(s): " + ", ".join(missing))

    def _validate_handoff_metadata(self, artifact: Artifact) -> None:
        resolved: dict[str, list[str]] = {}
        for field in ("current_state", "authority_sources"):
            value = artifact.metadata.get(field)
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(item, str) and item.strip() for item in value)
                or len(value) != len(set(value))
            ):
                self.issue("BVM090", artifact.path, f"handoff metadata '{field}' must be a non-empty array of unique paths")
                continue
            resolved[field] = []
            for reference in value:
                target, error = safe_reference(self.root, reference)
                if error or target is None or not target.is_file():
                    detail = error or f"path does not exist: {reference}"
                    self.issue("BVM090", artifact.path, f"invalid {field} reference: {detail}")
                    continue
                resolved[field].append(relative(self.root, target))
        current_state = resolved.get("current_state", [])
        has_durable_current_state = any(
            reference == "INDEX.json"
            or (
                reference in self.artifacts_by_path
                and self.artifacts_by_path[reference].state == "canon"
            )
            for reference in current_state
        )
        if current_state and not has_durable_current_state:
            self.issue("BVM090", artifact.path, "current_state must include INDEX.json or a managed CANON artifact")

    def _load_receipts(self) -> None:
        base = self.root / "RECEIPTS"
        if not base.is_dir():
            return
        seen_ids: dict[str, str] = {}
        for path in sorted(base.rglob("*.json")):
            rel = relative(self.root, path)
            rel_parts = Path(rel).parts
            if len(rel_parts) >= 2 and rel_parts[1] in {"data", "candidates"}:
                continue
            try:
                data = load_json(path)
            except (ValueError, json.JSONDecodeError, UnicodeError, OSError) as exc:
                self.issue("BVM020", path, f"cannot parse receipt: {exc}")
                continue
            schema = data.get("schema")
            identifier: Any = None
            if schema == "bvm-receipt/0.1":
                self.evidence[rel] = data
                identifier = data.get("receipt_id")
                self._validate_evidence_receipt(path, data)
            elif schema == "bvm-review/0.1":
                self.reviews[rel] = data
                identifier = data.get("review_id")
                self._validate_review_receipt(path, data)
            elif schema == "bvm-promotion/0.1":
                self.promotions[rel] = data
                identifier = data.get("promotion_id")
                self._validate_promotion_receipt_shape(path, data)
            else:
                self.issue("BVM020", path, f"unsupported receipt schema '{schema}'")
                continue
            if isinstance(identifier, str) and identifier:
                if identifier in seen_ids:
                    self.issue("BVM025", path, f"receipt identifier '{identifier}' already used by {seen_ids[identifier]}")
                else:
                    seen_ids[identifier] = rel

    def _validate_evidence_receipt(self, path: Path, data: dict[str, Any]) -> None:
        required = ("receipt_id", "subject_id", "kind", "captured_utc", "status", "scope", "source", "source_sha256")
        for field in required:
            if not isinstance(data.get(field), str) or not str(data.get(field)).strip():
                self.issue("BVM025", path, f"required evidence field '{field}' must be a non-empty string")
        if not is_utc(data.get("captured_utc")):
            self.issue("BVM025", path, "captured_utc must be valid UTC")
        if data.get("status") not in {"pass", "fail", "observed", "inconclusive"}:
            self.issue("BVM025", path, "status must be pass, fail, observed, or inconclusive")
        applicability_id = data.get("applicability_id")
        if applicability_id is not None and (not isinstance(applicability_id, str) or not applicability_id.strip()):
            self.issue("BVM025", path, "applicability_id must be a non-empty string when present")
        self._validate_hashed_reference(path, data.get("source"), data.get("source_sha256"), "source")
        kind = data.get("kind")
        if kind == "executed-object":
            for field in ("object", "object_sha256"):
                if not isinstance(data.get(field), str) or not str(data.get(field)).strip():
                    self.issue("BVM025", path, f"executed-object receipt requires '{field}'")
            self._validate_hashed_reference(path, data.get("object"), data.get("object_sha256"), "executed object")
        if kind == "unit-check" and (not isinstance(data.get("unit_id"), str) or not data.get("unit_id", "").strip()):
            self.issue("BVM025", path, "unit-check receipt requires a non-empty unit_id")
        if kind == "authoritative-search":
            for field in ("authority", "procedure", "boundary"):
                if not isinstance(data.get(field), str) or not data.get(field, "").strip():
                    self.issue("BVM065", path, f"authoritative-search receipt requires '{field}'")

    def _validate_hashed_reference(self, path: Path, reference: Any, declared_hash: Any, label: str) -> None:
        if not is_sha256(declared_hash):
            self.issue("BVM025", path, f"{label.replace(' ', '_')}_sha256 must be a lowercase SHA-256 hex digest")
        target, error = safe_reference(self.root, reference)
        if error:
            self.issue("BVM021", path, f"invalid {label}: {error}")
        elif target is not None and not target.is_file():
            self.issue("BVM021", path, f"{label} does not exist: {reference}")
        elif target is not None and is_sha256(declared_hash):
            actual = sha256_file(target)
            if actual != declared_hash:
                self.issue("BVM022", path, f"{label} hash mismatch: declared {declared_hash}, actual {actual}")

    def _validate_review_receipt(self, path: Path, data: dict[str, Any]) -> None:
        required = (
            "review_id", "artifact_id", "artifact", "artifact_sha256", "reviewer_class",
            "verdict", "reviewed_utc", "scope", "notes",
        )
        for field in required:
            if not isinstance(data.get(field), str) or not str(data.get(field)).strip():
                self.issue("BVM025", path, f"required review field '{field}' must be a non-empty string")
        if data.get("verdict") not in {"pass", "fail", "conditional"}:
            self.issue("BVM025", path, "verdict must be pass, fail, or conditional")
        if not is_utc(data.get("reviewed_utc")):
            self.issue("BVM025", path, "reviewed_utc must be valid UTC")
        if not is_sha256(data.get("artifact_sha256")):
            self.issue("BVM025", path, "artifact_sha256 must be a lowercase SHA-256 hex digest")

    def _validate_promotion_receipt_shape(self, path: Path, data: dict[str, Any]) -> None:
        required_strings = (
            "promotion_id", "artifact_id", "artifact", "artifact_sha256", "candidate",
            "candidate_sha256", "promoted_from", "promoted_utc", "decision_by",
        )
        for field in required_strings:
            if not isinstance(data.get(field), str) or not str(data.get(field)).strip():
                self.issue("BVM025", path, f"required promotion field '{field}' must be a non-empty string")
        if data.get("promoted_from") not in {"working", "archive"}:
            self.issue("BVM025", path, "promoted_from must be 'working' or 'archive'")
        if not is_utc(data.get("promoted_utc")):
            self.issue("BVM025", path, "promoted_utc must be valid UTC")
        for field in ("artifact_sha256", "candidate_sha256"):
            if not is_sha256(data.get(field)):
                self.issue("BVM025", path, f"{field} must be a lowercase SHA-256 hex digest")
        for field in ("evidence", "reviews"):
            value = data.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                self.issue("BVM025", path, f"{field} must be an array of non-empty vault-root-relative paths")
            elif len(value) != len(set(value)):
                self.issue("BVM025", path, f"{field} must not contain duplicate paths")
        for field in ("evidence_sha256", "reviews_sha256"):
            value = data.get(field)
            if (
                not isinstance(value, dict)
                or not all(isinstance(key, str) and key.strip() and is_sha256(digest) for key, digest in value.items())
            ):
                self.issue("BVM025", path, f"{field} must map non-empty receipt paths to lowercase SHA-256 digests")

    def _load_retractions(self) -> None:
        base = self.root / "RETRACTIONS"
        if not base.is_dir():
            return
        seen: set[str] = set()
        for path in sorted(base.rglob("*.json")):
            rel = relative(self.root, path)
            try:
                data = load_json(path)
            except (ValueError, json.JSONDecodeError, UnicodeError, OSError) as exc:
                self.issue("BVM050", path, f"cannot parse retraction: {exc}")
                continue
            if data.get("schema") != "bvm-retraction/0.1":
                self.issue("BVM050", path, "schema must be 'bvm-retraction/0.1'")
            rid = data.get("retraction_id")
            if not isinstance(rid, str) or not rid:
                self.issue("BVM050", path, "retraction_id must be a non-empty string")
            elif rid in seen:
                self.issue("BVM050", path, f"duplicate retraction_id '{rid}'")
            else:
                seen.add(rid)
            for field in ("artifact", "artifact_sha256", "retracted_utc", "reason"):
                if not isinstance(data.get(field), str) or not str(data.get(field)).strip():
                    self.issue("BVM050", path, f"required retraction field '{field}' must be a non-empty string")
            if "replacement" not in data:
                self.issue("BVM050", path, "replacement must be present as a path or null")
            if data.get("preserve_original") is not True:
                self.issue("BVM051", path, "preserve_original must be true")
            if not is_sha256(data.get("artifact_sha256")):
                self.issue("BVM050", path, "artifact_sha256 must be a lowercase SHA-256 hex digest")
            if not is_utc(data.get("retracted_utc")):
                self.issue("BVM050", path, "retracted_utc must be valid UTC")
            replacement = data.get("replacement")
            replacement_hash = data.get("replacement_sha256")
            if replacement is not None:
                if not isinstance(replacement, str) or not replacement.strip():
                    self.issue("BVM050", path, "replacement must be a non-empty path or null")
                if not is_sha256(replacement_hash):
                    self.issue("BVM050", path, "replacement_sha256 is required when replacement is a path")
            elif replacement_hash is not None:
                self.issue("BVM050", path, "replacement_sha256 must be null or absent when replacement is null")
            self.retractions[rel] = data

    def _validate_receipt_supersession(self) -> None:
        edges: dict[str, str] = {}
        for rel, data in self.evidence.items():
            prior = data.get("supersedes_receipt")
            if prior is None:
                continue
            target, error = safe_reference(self.root, prior)
            if error:
                self.issue("BVM016", rel, f"invalid supersedes_receipt: {error}")
                continue
            prior_rel = relative(self.root, target) if target else str(prior)
            prior_data = self.evidence.get(prior_rel)
            if prior_data is None:
                self.issue("BVM016", rel, f"supersedes_receipt does not identify an evidence receipt: {prior}")
                continue
            if (
                data.get("subject_id") != prior_data.get("subject_id")
                or data.get("kind") != prior_data.get("kind")
                or receipt_applicability_key(data) != receipt_applicability_key(prior_data)
            ):
                self.issue(
                    "BVM025",
                    rel,
                    "a receipt may supersede only the same subject_id, kind, and applicability boundary",
                )
                continue
            current_time = parse_utc(data.get("captured_utc"))
            prior_time = parse_utc(prior_data.get("captured_utc"))
            if current_time is None or prior_time is None or current_time <= prior_time:
                self.issue("BVM026", rel, "superseding receipt must have a later captured_utc than the receipt it replaces")
                continue
            edges[rel] = prior_rel
            self.superseded_receipt_paths.add(prior_rel)

        for start in edges:
            seen: set[str] = set()
            current = start
            while current in edges:
                if current in seen:
                    self.issue("BVM026", start, "receipt supersession graph contains a cycle")
                    break
                seen.add(current)
                current = edges[current]

    def _reference_list(self, artifact: Artifact, field: str) -> list[str]:
        value = artifact.metadata.get(field, [])
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            self.issue("BVM017", artifact.path, f"{field} must be an array of paths")
            return []
        if len(value) != len(set(value)):
            self.issue("BVM018", artifact.path, f"{field} contains duplicate references")
        return value

    def _resolve_known(self, artifact: Artifact, reference: Any, known: dict[str, dict[str, Any]], label: str) -> tuple[str | None, dict[str, Any] | None]:
        target, error = safe_reference(self.root, reference)
        if error:
            self.issue("BVM016", artifact.path, f"invalid {label} reference: {error}")
            return None, None
        rel = relative(self.root, target) if target else str(reference)
        if rel not in known:
            self.issue("BVM016", artifact.path, f"{label} does not resolve to a recognized record: {reference}")
            return rel, None
        return rel, known[rel]

    def _validate_artifacts(self) -> None:
        for artifact in self.artifacts_by_path.values():
            evidence_refs = self._reference_list(artifact, "evidence")
            review_refs = self._reference_list(artifact, "reviews")
            resolved_evidence: list[str] = []
            resolved_reviews: list[str] = []
            qualifying_reviews = 0

            for ref in evidence_refs:
                rel, receipt = self._resolve_known(artifact, ref, self.evidence, "evidence receipt")
                if rel:
                    resolved_evidence.append(rel)
                    if rel in self.superseded_receipt_paths:
                        self.issue("BVM023", artifact.path, f"evidence receipt has been superseded: {rel}")
                if receipt and receipt.get("subject_id") != artifact.artifact_id:
                    self.issue("BVM025", artifact.path, f"evidence receipt subject_id must equal artifact_id: {ref}")

            for ref in review_refs:
                rel, review = self._resolve_known(artifact, ref, self.reviews, "review receipt")
                if rel:
                    resolved_reviews.append(rel)
                if review:
                    if review.get("artifact_id") != artifact.artifact_id:
                        self.issue("BVM025", artifact.path, f"review receipt artifact_id does not match: {ref}")
                    review_target, error = safe_reference(self.root, review.get("artifact"))
                    review_rel = relative(self.root, review_target) if review_target else ""
                    if error or review_rel != artifact.relative_path or review.get("artifact_sha256") != artifact.sha256:
                        self.issue("BVM037", artifact.path, f"review receipt is not bound to exact artifact bytes: {ref}")
                    else:
                        reviewed = parse_utc(review.get("reviewed_utc"))
                        updated = parse_utc(artifact.metadata.get("updated_utc"))
                        if reviewed is not None and updated is not None and reviewed < updated:
                            self.issue("BVM026", artifact.path, f"review receipt predates the reviewed artifact bytes: {ref}")
                        elif review.get("verdict") == "pass" and review.get("reviewer_class") not in SELF_REVIEW_CLASSES:
                            qualifying_reviews += 1

            if artifact.metadata.get("result") == "negative":
                ref = artifact.metadata.get("positive_control_receipt")
                if not isinstance(ref, str) or not ref or ref not in evidence_refs:
                    self.issue("BVM060", artifact.path, "negative result requires positive_control_receipt included in evidence")
                else:
                    _, receipt = self._resolve_known(artifact, ref, self.evidence, "positive-control receipt")
                    if not receipt or receipt.get("kind") != "positive-control" or receipt.get("status") != "pass":
                        self.issue("BVM061", artifact.path, "positive_control_receipt must cite a passing positive-control evidence receipt")

            if artifact.metadata.get("claim_type") == "negative-existence":
                ref = artifact.metadata.get("authoritative_search_receipt")
                if not isinstance(ref, str) or not ref or ref not in evidence_refs:
                    self.issue("BVM064", artifact.path, "negative-existence claim requires authoritative_search_receipt included in evidence")
                else:
                    _, receipt = self._resolve_known(artifact, ref, self.evidence, "authoritative-search receipt")
                    if not receipt or receipt.get("kind") != "authoritative-search" or receipt.get("status") not in {"pass", "observed"}:
                        self.issue("BVM065", artifact.path, "authoritative_search_receipt must cite a completed authoritative-search receipt")
                    elif any(not isinstance(receipt.get(field), str) or not receipt.get(field, "").strip() for field in ("authority", "procedure", "boundary")):
                        self.issue("BVM065", artifact.path, "authoritative search must record authority, procedure, and boundary")

            if artifact.metadata.get("requires_canon_object") is True:
                if artifact.metadata.get("object_mode") not in {"canonical", "mixed"}:
                    self.issue(
                        "BVM072",
                        artifact.path,
                        "requires_canon_object=true requires object_mode='canonical' or 'mixed'; a proxy cannot inherit the claim",
                    )
                ref = artifact.metadata.get("executed_object_receipt")
                if not isinstance(ref, str) or not ref or ref not in evidence_refs:
                    self.issue("BVM070", artifact.path, "requires_canon_object=true requires executed_object_receipt included in evidence")
                else:
                    _, receipt = self._resolve_known(artifact, ref, self.evidence, "executed-object receipt")
                    if (
                        not receipt
                        or receipt.get("kind") != "executed-object"
                        or receipt.get("status") != "pass"
                        or not is_sha256(receipt.get("object_sha256"))
                    ):
                        self.issue("BVM071", artifact.path, "executed_object_receipt must cite a passing, hash-bound executed-object receipt")

            self._validate_aggregate(artifact, evidence_refs)

            if artifact.state == "canon":
                if not resolved_evidence:
                    self.issue("BVM030", artifact.path, "canon artifact requires at least one evidence receipt")
                if qualifying_reviews == 0:
                    self.issue("BVM031", artifact.path, "canon artifact requires at least one passing non-self review bound to exact bytes")
                promotion_ref = artifact.metadata.get("promotion_receipt")
                if not isinstance(promotion_ref, str) or not promotion_ref:
                    self.issue("BVM032", artifact.path, "canon artifact requires promotion_receipt")
                else:
                    _, promotion = self._resolve_known(artifact, promotion_ref, self.promotions, "promotion receipt")
                    if promotion:
                        self._validate_promotion_for_artifact(artifact, promotion, resolved_evidence, resolved_reviews)

    def _validate_aggregate(self, artifact: Artifact, evidence_refs: list[str]) -> None:
        aggregate = artifact.metadata.get("aggregate")
        if aggregate is None:
            return
        if not isinstance(aggregate, dict):
            self.issue("BVM062", artifact.path, "aggregate must be an object")
            return
        units = aggregate.get("units")
        unit_receipts = aggregate.get("unit_receipts")
        if (
            not isinstance(units, list)
            or not units
            or not all(isinstance(unit, str) and unit.strip() for unit in units)
            or len(units) != len(set(units))
        ):
            self.issue("BVM062", artifact.path, "aggregate.units must be a non-empty array of unique strings")
            return
        if not isinstance(unit_receipts, dict) or set(unit_receipts) != set(units):
            self.issue("BVM062", artifact.path, "aggregate.unit_receipts must map every declared unit exactly once")
            return
        for unit in units:
            ref = unit_receipts.get(unit)
            if not isinstance(ref, str) or ref not in evidence_refs:
                self.issue("BVM063", artifact.path, f"unit '{unit}' receipt must be included in evidence")
                continue
            _, receipt = self._resolve_known(artifact, ref, self.evidence, f"unit receipt for {unit}")
            if (
                not receipt
                or receipt.get("kind") != "unit-check"
                or receipt.get("status") != "pass"
                or receipt.get("unit_id") != unit
            ):
                self.issue("BVM063", artifact.path, f"unit '{unit}' must cite a passing unit-check receipt with matching unit_id")

    def _validate_promotion_for_artifact(
        self,
        artifact: Artifact,
        promotion: dict[str, Any],
        evidence: list[str],
        reviews: list[str],
    ) -> None:
        failures: list[str] = []
        if promotion.get("artifact_id") != artifact.artifact_id:
            failures.append("artifact_id differs")
        artifact_target, artifact_error = safe_reference(self.root, promotion.get("artifact"))
        artifact_rel = relative(self.root, artifact_target) if artifact_target else ""
        if artifact_error or artifact_rel != artifact.relative_path:
            failures.append("artifact path differs")
        if promotion.get("artifact_sha256") != artifact.sha256:
            failures.append("artifact_sha256 differs from current bytes")

        promotion_evidence = promotion.get("evidence")
        if not isinstance(promotion_evidence, list) or not all(isinstance(item, str) for item in promotion_evidence):
            failures.append("evidence list is invalid")
        elif len(promotion_evidence) != len(set(promotion_evidence)):
            failures.append("evidence list contains duplicates")
        elif set(promotion_evidence) != set(evidence):
            failures.append("evidence list differs from artifact metadata")

        promotion_reviews = promotion.get("reviews")
        if not isinstance(promotion_reviews, list) or not all(isinstance(item, str) for item in promotion_reviews):
            failures.append("reviews list is invalid")
        elif len(promotion_reviews) != len(set(promotion_reviews)):
            failures.append("reviews list contains duplicates")
        elif set(promotion_reviews) != set(reviews):
            failures.append("reviews list differs from artifact metadata")

        for label, expected, map_field in (
            ("evidence", evidence, "evidence_sha256"),
            ("review", reviews, "reviews_sha256"),
        ):
            digest_map = promotion.get(map_field)
            if not isinstance(digest_map, dict) or set(digest_map) != set(expected):
                failures.append(f"{map_field} keys differ from the artifact {label} set")
                continue
            for rel in expected:
                declared = digest_map.get(rel)
                target, error = safe_reference(self.root, rel)
                if error or target is None or not target.is_file():
                    failures.append(f"{label} receipt does not resolve for hashing: {rel}")
                    continue
                actual = sha256_file(target)
                if declared != actual:
                    failures.append(f"{map_field} mismatch for {rel}")

        candidate, candidate_error = safe_reference(self.root, promotion.get("candidate"))
        if candidate_error or candidate is None or not candidate.is_file():
            failures.append("candidate snapshot does not resolve")
        else:
            candidate_rel = relative(self.root, candidate)
            if not candidate_rel.startswith("RECEIPTS/candidates/"):
                failures.append("candidate snapshot is outside RECEIPTS/candidates")
            actual_candidate_hash = sha256_file(candidate)
            if promotion.get("candidate_sha256") != actual_candidate_hash:
                failures.append("candidate_sha256 differs from candidate bytes")
            if candidate.read_bytes() != artifact.path.read_bytes():
                failures.append("candidate bytes differ from promoted artifact bytes")

        promoted = parse_utc(promotion.get("promoted_utc"))
        updated = parse_utc(artifact.metadata.get("updated_utc"))
        if promoted is not None and updated is not None and promoted < updated:
            self.issue("BVM036", artifact.path, "promotion predates artifact updated_utc")
        for rel in evidence:
            captured = parse_utc(self.evidence.get(rel, {}).get("captured_utc"))
            if promoted is not None and captured is not None and promoted < captured:
                self.issue("BVM036", artifact.path, f"promotion predates evidence receipt: {rel}")
        for rel in reviews:
            reviewed = parse_utc(self.reviews.get(rel, {}).get("reviewed_utc"))
            if promoted is not None and reviewed is not None and promoted < reviewed:
                self.issue("BVM036", artifact.path, f"promotion predates review receipt: {rel}")
        if failures:
            self.issue("BVM033", artifact.path, "; ".join(failures))

    def _validate_supersession_graph(self) -> None:
        edges: dict[str, str] = {}
        for artifact in self.artifacts_by_path.values():
            ref = artifact.metadata.get("supersedes")
            if ref is None:
                continue
            target, error = safe_reference(self.root, ref)
            if error:
                self.issue("BVM040", artifact.path, error)
                continue
            target_rel = relative(self.root, target) if target else str(ref)
            predecessor = self.artifacts_by_path.get(target_rel)
            if predecessor is None:
                self.issue("BVM040", artifact.path, f"supersedes target is not a managed artifact: {ref}")
                continue
            edges[artifact.relative_path] = target_rel
            self.incoming_supersession.add(target_rel)
            if predecessor.lineage_id != artifact.lineage_id:
                self.issue("BVM040", artifact.path, f"supersedes target has lineage '{predecessor.lineage_id}', expected '{artifact.lineage_id}'")
            if is_semver(artifact.version) and is_semver(predecessor.version):
                if compare_semver(artifact.version, predecessor.version) <= 0:
                    self.issue("BVM042", artifact.path, f"version {artifact.version} must be greater than predecessor {predecessor.version}")
            if artifact.state == "canon" and predecessor.state != "archive":
                self.issue("BVM043", artifact.path, "a current canon predecessor must be preserved in ARCHIVE")

        for start in edges:
            seen: set[str] = set()
            current = start
            while current in edges:
                if current in seen:
                    self.issue("BVM041", start, "supersession graph contains a cycle")
                    break
                seen.add(current)
                current = edges[current]

    def _validate_retractions(self) -> None:
        for rel, data in self.retractions.items():
            retracted_time = parse_utc(data.get("retracted_utc"))
            target, error = safe_reference(self.root, data.get("artifact"))
            if error:
                self.issue("BVM051", rel, error)
                continue
            target_rel = relative(self.root, target) if target else ""
            target_artifact = self.artifacts_by_path.get(target_rel)
            if target is None or not target.is_file() or target_artifact is None or target_artifact.state != "archive":
                self.issue("BVM051", rel, f"retracted artifact must be a preserved managed ARCHIVE artifact: {data.get('artifact')}")
            else:
                self.retracted_paths.add(target_rel)
                if is_sha256(data.get("artifact_sha256")):
                    actual = sha256_file(target)
                    if actual != data.get("artifact_sha256"):
                        self.issue("BVM051", rel, f"retracted artifact hash mismatch: declared {data.get('artifact_sha256')}, actual {actual}")
                target_updated = parse_utc(target_artifact.metadata.get("updated_utc"))
                if retracted_time is not None and target_updated is not None and retracted_time < target_updated:
                    self.issue("BVM053", rel, "retracted_utc predates the archived artifact updated_utc")

            replacement = data.get("replacement")
            if replacement is not None:
                repl, repl_error = safe_reference(self.root, replacement)
                repl_rel = relative(self.root, repl) if repl else ""
                repl_artifact = self.artifacts_by_path.get(repl_rel)
                if repl_error or repl is None or not repl.is_file() or repl_artifact is None or repl_artifact.state != "canon":
                    self.issue("BVM052", rel, f"replacement must resolve to a managed CANON artifact: {replacement}")
                else:
                    declared = data.get("replacement_sha256")
                    actual = sha256_file(repl)
                    if declared != actual:
                        self.issue("BVM052", rel, f"replacement hash mismatch: declared {declared}, actual {actual}")
                    if target_artifact is not None and target_artifact.lineage_id != repl_artifact.lineage_id:
                        self.issue("BVM052", rel, "replacement lineage differs from retracted artifact lineage")
                    replacement_updated = parse_utc(repl_artifact.metadata.get("updated_utc"))
                    replacement_promotion_ref = repl_artifact.metadata.get("promotion_receipt")
                    replacement_promotion_target, replacement_promotion_error = safe_reference(
                        self.root, replacement_promotion_ref
                    )
                    replacement_promotion_rel = (
                        relative(self.root, replacement_promotion_target)
                        if replacement_promotion_target is not None
                        else ""
                    )
                    replacement_promotion = (
                        self.promotions.get(replacement_promotion_rel)
                        if not replacement_promotion_error
                        else None
                    )
                    replacement_promoted = (
                        parse_utc(replacement_promotion.get("promoted_utc"))
                        if replacement_promotion
                        else None
                    )
                    if (
                        retracted_time is not None
                        and replacement_updated is not None
                        and retracted_time < replacement_updated
                    ):
                        self.issue("BVM053", rel, "retracted_utc predates the replacement artifact updated_utc")
                    if (
                        retracted_time is not None
                        and replacement_promoted is not None
                        and retracted_time < replacement_promoted
                    ):
                        self.issue("BVM053", rel, "retracted_utc predates the replacement promotion")

    def _validate_archive_reachability(self) -> None:
        for artifact in self.artifacts_by_path.values():
            if artifact.state != "archive":
                continue
            if artifact.relative_path not in self.incoming_supersession and artifact.relative_path not in self.retracted_paths:
                self.issue("BVM044", artifact.path, "archive artifact is not referenced by a supersession or retraction record")

    def _validate_index(self) -> None:
        if self.index is None or not isinstance(self.index.get("lineages"), dict):
            return
        lineages: dict[str, Any] = self.index["lineages"]
        indexed_paths: set[str] = set()
        index_updated = parse_utc(self.index.get("updated_utc"))
        for lineage_id, entry in lineages.items():
            if not isinstance(entry, dict):
                self.issue("BVM080", "INDEX.json", f"lineage '{lineage_id}' entry must be an object")
                continue
            current = entry.get("current")
            target, error = safe_reference(self.root, current)
            if error:
                self.issue("BVM080", "INDEX.json", f"lineage '{lineage_id}': {error}")
                continue
            rel = relative(self.root, target) if target else str(current)
            artifact = self.artifacts_by_path.get(rel)
            if artifact is None or artifact.state != "canon":
                self.issue("BVM080", "INDEX.json", f"lineage '{lineage_id}' current path is not a canon artifact: {current}")
                continue
            indexed_paths.add(rel)
            if artifact.lineage_id != lineage_id:
                self.issue("BVM081", "INDEX.json", f"index key '{lineage_id}' disagrees with artifact lineage '{artifact.lineage_id}'")
            if entry.get("version") != artifact.version:
                self.issue("BVM081", "INDEX.json", f"lineage '{lineage_id}' version disagrees with artifact")
            if entry.get("status") != "current":
                self.issue("BVM080", "INDEX.json", f"lineage '{lineage_id}' status must be 'current'")

            artifact_promotion_ref = artifact.metadata.get("promotion_receipt")
            index_promotion_ref = entry.get("promotion")
            index_promotion_hash = entry.get("promotion_sha256")
            promotion_target, promotion_error = safe_reference(self.root, index_promotion_ref)
            promotion_rel = relative(self.root, promotion_target) if promotion_target else ""
            if (
                promotion_error
                or promotion_rel not in self.promotions
                or index_promotion_ref != artifact_promotion_ref
                or not is_sha256(index_promotion_hash)
                or promotion_target is None
                or not promotion_target.is_file()
                or sha256_file(promotion_target) != index_promotion_hash
            ):
                self.issue(
                    "BVM082",
                    "INDEX.json",
                    f"lineage '{lineage_id}' does not bind the artifact's current promotion receipt by path and SHA-256",
                )

            artifact_updated = parse_utc(artifact.metadata.get("updated_utc"))
            if index_updated is not None and artifact_updated is not None and index_updated < artifact_updated:
                self.issue("BVM036", "INDEX.json", f"index predates current artifact for lineage '{lineage_id}'")
            promotion = self.promotions.get(promotion_rel) if not promotion_error else None
            promotion_time = parse_utc(promotion.get("promoted_utc")) if promotion else None
            if index_updated is not None and promotion_time is not None and index_updated < promotion_time:
                self.issue("BVM036", "INDEX.json", f"index predates promotion for lineage '{lineage_id}'")

        canon_by_lineage: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in self.artifacts_by_path.values():
            if artifact.state == "canon":
                canon_by_lineage[artifact.lineage_id].append(artifact)
                if artifact.relative_path not in indexed_paths:
                    self.issue("BVM034", artifact.path, "canon artifact is not current in INDEX.json")
        for lineage, artifacts in canon_by_lineage.items():
            if len(artifacts) > 1:
                paths = ", ".join(sorted(a.relative_path for a in artifacts))
                self.issue("BVM035", paths, f"lineage '{lineage}' has multiple canon artifacts")

    def _validate_active_receipt_conflicts(self) -> None:
        canon_by_subject = {
            artifact.artifact_id: artifact
            for artifact in self.artifacts_by_path.values()
            if artifact.state == "canon" and artifact.artifact_id
        }
        groups: dict[tuple[str, str, str], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for rel, receipt in self.evidence.items():
            if rel in self.superseded_receipt_paths:
                continue
            subject_id = receipt.get("subject_id")
            kind = receipt.get("kind")
            if not isinstance(subject_id, str) or subject_id not in canon_by_subject:
                continue
            if not isinstance(kind, str) or not kind.strip():
                continue
            boundary = receipt_applicability_key(receipt)
            groups[(subject_id, kind, boundary)].append((rel, receipt))

        for (subject_id, kind, boundary), records in groups.items():
            statuses = {record.get("status") for _, record in records} & {"pass", "fail"}
            if len(statuses) > 1:
                paths = ", ".join(sorted(rel for rel, _ in records))
                artifact = canon_by_subject[subject_id]
                self.issue(
                    "BVM024",
                    artifact.path,
                    f"active '{kind}' receipts contradict within applicability '{boundary}' "
                    f"without explicit supersession: {paths}",
                )


def lint_vault(root: str | Path) -> LintReport:
    return VaultLinter(Path(root)).run()
