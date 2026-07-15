from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, order=True)
class Issue:
    """One stable, machine-readable lint finding."""

    code: str
    severity: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class Artifact:
    path: Path
    relative_path: str
    metadata: dict[str, Any]
    sha256: str

    @property
    def artifact_id(self) -> str:
        return str(self.metadata.get("artifact_id", ""))

    @property
    def lineage_id(self) -> str:
        return str(self.metadata.get("lineage_id", ""))

    @property
    def kind(self) -> str:
        return str(self.metadata.get("kind", ""))

    @property
    def state(self) -> str:
        return str(self.metadata.get("state", ""))

    @property
    def version(self) -> str:
        return str(self.metadata.get("version", ""))


@dataclass
class LintReport:
    root: Path
    checker_version: str
    issues: list[Issue] = field(default_factory=list)
    artifacts: int = 0
    evidence_receipts: int = 0
    review_receipts: int = 0
    promotion_receipts: int = 0
    retractions: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "bvm-lint-report/0.1",
            "checker_version": self.checker_version,
            "root": str(self.root),
            "passed": self.passed,
            "counts": {
                "artifacts": self.artifacts,
                "evidence_receipts": self.evidence_receipts,
                "review_receipts": self.review_receipts,
                "promotion_receipts": self.promotion_receipts,
                "retractions": self.retractions,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "issues": [issue.to_dict() for issue in sorted(self.issues)],
        }
