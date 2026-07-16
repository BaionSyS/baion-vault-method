#!/usr/bin/env python3
"""Vault Lab fixture generator — rebuilds lab/cases/* deterministically.

Maintainer tool, not part of the guided run. Every SHA-256 in the fixtures
is computed from the actual bytes written here, so the broken vaults fail
for exactly the declared reason and the fixed vaults pass ``--strict``.
All names, counts, and dates describe the fictional Cedar Lane community
garden; timestamps are fixed constants so regeneration is byte-stable.

Usage: python3 lab/tools/build_fixtures.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
CASES = LAB_ROOT / "cases"

# One fictional day, ordered so every SPEC timing rule holds in fixed vaults.
T_CREATED = "2026-07-12T09:00:00Z"
T_FAIL_COUNT = "2026-07-12T09:02:00Z"
T_UPDATED = "2026-07-12T09:05:00Z"
T_COUNTED = "2026-07-12T09:10:00Z"
T_GERMINATION = "2026-07-12T09:11:00Z"
T_REVIEWED = "2026-07-12T09:15:00Z"
T_PROMOTED = "2026-07-12T09:20:00Z"
T_INDEX = "2026-07-12T09:25:00Z"
# Case 05 fixed variant: the honest re-freeze after an edit.
T_UPDATED_2 = "2026-07-12T09:30:00Z"
T_REVIEWED_2 = "2026-07-12T09:35:00Z"
T_PROMOTED_2 = "2026-07-12T09:40:00Z"
T_INDEX_2 = "2026-07-12T09:45:00Z"

ARTIFACT_PATH = "CANON/shelf-count-v1.0.0.md"
CANDIDATE_PATH = "RECEIPTS/candidates/shelf-count-v1.0.0.md"
ARTIFACT_ID = "artifact.shelf-count.v1_0_0"
LINEAGE_ID = "lineage.shelf-count"

COUNT_SHEET = """Cedar Lane community garden - seed cabinet shelf count
Counted: 2026-07-12, morning shift

Tomato .......... 6 packets
Carrot .......... 5 packets
Lettuce ......... 5 packets
Squash .......... 4 packets
Bean ............ 4 packets
Pepper .......... 4 packets
Radish .......... 4 packets
Kale ............ 4 packets
Basil ........... 3 packets
Sunflower ....... 3 packets
Okra ............ 3 packets
Collard ......... 3 packets

Total: 48 labeled packets across 12 species.
"""

FIRST_COUNT_SHEET = """Cedar Lane community garden - seed cabinet shelf count
Counted: 2026-07-12, first attempt (before re-shelving)

Loose packets were found on the potting bench, outside the cabinet.
Cabinet total at this attempt: 44 labeled packets. Does not match the
44 + 4 bench packets until re-shelving is done. Count FAILED against
the checkout ledger; recount scheduled after re-shelving.
"""

GERMINATION_LOG = """Cedar Lane community garden - germination spot check
Checked: 2026-07-12, morning shift

Sampled 10 seeds from the oldest tomato packet on damp paper towel,
seven days. 8 of 10 sprouted. Passes the garden's 7-of-10 floor for
keeping a packet on the shelf.
"""

BODY = """# Cedar Lane seed cabinet shelf count v1.0.0

## Canonical claim

The seed cabinet at the Cedar Lane community garden holds 48 labeled
packets across 12 species, per the July 2026 shelf count.

The claim is bounded to the hash-bound count sheet bytes in
`RECEIPTS/data/shelf-count-v1.txt`. It says nothing about packets checked
out to members, seed viability, or any later date.

## Known

- The recount after re-shelving matches the checkout ledger.
- The {tomato} germination spot check passed the garden's floor.

## Unknown

- Whether packets checked out to members will come back.
- Viability of species other than the sampled {tomato} packet.
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump_json(obj: dict) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def artifact_bytes(metadata: dict, body: str) -> bytes:
    block = json.dumps(metadata, indent=2)
    return f"<!-- bvm\n{block}\n-->\n{body}".encode("utf-8")


def count_receipt(files: dict[str, bytes], *, supersedes: bool) -> dict:
    receipt = {
        "applicability_id": "shelf-count.2026-07",
        "captured_utc": T_COUNTED,
        "kind": "count-check",
        "receipt_id": "receipt.shelf-count.v1",
        "schema": "bvm-receipt/0.1",
        "scope": "Recount of the seed cabinet after re-shelving, checked against the checkout ledger.",
        "source": "RECEIPTS/data/shelf-count-v1.txt",
        "source_sha256": sha256_bytes(files["RECEIPTS/data/shelf-count-v1.txt"]),
        "status": "pass",
        "subject_id": ARTIFACT_ID,
    }
    if supersedes:
        receipt["supersedes_receipt"] = "RECEIPTS/evidence/shelf-count-v0.json"
    return receipt


def first_count_receipt(files: dict[str, bytes]) -> dict:
    return {
        "applicability_id": "shelf-count.2026-07",
        "captured_utc": T_FAIL_COUNT,
        "kind": "count-check",
        "receipt_id": "receipt.shelf-count.v0",
        "schema": "bvm-receipt/0.1",
        "scope": "First count of the seed cabinet, before re-shelving the bench packets.",
        "source": "RECEIPTS/data/shelf-count-v0.txt",
        "source_sha256": sha256_bytes(files["RECEIPTS/data/shelf-count-v0.txt"]),
        "status": "fail",
        "subject_id": ARTIFACT_ID,
    }


def germination_receipt(files: dict[str, bytes]) -> dict:
    return {
        "applicability_id": "germination.tomato.2026-07",
        "captured_utc": T_GERMINATION,
        "kind": "germination-check",
        "receipt_id": "receipt.germination.v1",
        "schema": "bvm-receipt/0.1",
        "scope": "Ten-seed spot check of the oldest tomato packet against the 7-of-10 floor.",
        "source": "RECEIPTS/data/germination-log-v1.txt",
        "source_sha256": sha256_bytes(files["RECEIPTS/data/germination-log-v1.txt"]),
        "status": "pass",
        "subject_id": ARTIFACT_ID,
    }


def review_receipt(artifact_sha: str, *, review_id: str, reviewer_class: str,
                   reviewed_utc: str) -> dict:
    return {
        "artifact": ARTIFACT_PATH,
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": artifact_sha,
        "notes": "Pass for the bounded shelf-count claim. Checked the count sheet totals, the ledger reconciliation story, and the stated unknowns.",
        "review_id": review_id,
        "reviewed_utc": reviewed_utc,
        "reviewer_class": reviewer_class,
        "schema": "bvm-review/0.1",
        "scope": "Exact artifact bytes against the hash-bound count sheet and receipts.",
        "verdict": "pass",
    }


def build_vault(*, evidence_paths: list[str], extra_receipts: dict[str, dict],
                supersedes_first_count: bool = False,
                include_first_count: bool = False,
                include_germination: bool = False,
                reviewer_class: str = "separate-instance",
                body: str | None = None,
                promotion_path: str = "RECEIPTS/promotions/promote-v1.json",
                promotion_id: str = "promotion.shelf-count.v1",
                review_path: str = "RECEIPTS/reviews/independent-review-v1.json",
                review_id: str = "review.shelf-count.v1",
                updated_utc: str = T_UPDATED,
                reviewed_utc: str = T_REVIEWED,
                promoted_utc: str = T_PROMOTED,
                index_utc: str = T_INDEX) -> dict[str, bytes]:
    """Assemble one complete, internally hash-consistent Cedar Lane vault."""
    files: dict[str, bytes] = {
        "vault.toml": (
            'schema = "bvm-vault/0.1"\n'
            'name = "cedar-lane-seed-inventory"\n'
            'method_version = "0.1.0"\n'
        ).encode("utf-8"),
        "INBOX/.gitkeep": b"",
        "WORKING/.gitkeep": b"",
        "HANDOFFS/.gitkeep": b"",
        "ARCHIVE/.gitkeep": b"",
        "RETRACTIONS/.gitkeep": b"",
        "RECEIPTS/data/shelf-count-v1.txt": COUNT_SHEET.encode("utf-8"),
    }
    if include_first_count:
        files["RECEIPTS/data/shelf-count-v0.txt"] = FIRST_COUNT_SHEET.encode("utf-8")
        files["RECEIPTS/evidence/shelf-count-v0.json"] = dump_json(first_count_receipt(files))
    if include_germination:
        files["RECEIPTS/data/germination-log-v1.txt"] = GERMINATION_LOG.encode("utf-8")
        files["RECEIPTS/evidence/germination-check-v1.json"] = dump_json(germination_receipt(files))
    files["RECEIPTS/evidence/shelf-count-v1.json"] = dump_json(
        count_receipt(files, supersedes=supersedes_first_count))
    for rel, receipt in extra_receipts.items():
        files[rel] = dump_json(receipt)

    metadata = {
        "schema": "bvm-artifact/0.1",
        "artifact_id": ARTIFACT_ID,
        "lineage_id": LINEAGE_ID,
        "title": "Cedar Lane seed cabinet shelf count v1.0.0",
        "state": "canon",
        "version": "1.0.0",
        "created_utc": T_CREATED,
        "updated_utc": updated_utc,
        "evidence": evidence_paths,
        "reviews": [review_path],
        "promotion_receipt": promotion_path,
    }
    artifact = artifact_bytes(metadata, (body or BODY).format(tomato="tomato"))
    files[ARTIFACT_PATH] = artifact
    files[CANDIDATE_PATH] = artifact
    artifact_sha = sha256_bytes(artifact)

    files[review_path] = dump_json(review_receipt(
        artifact_sha, review_id=review_id, reviewer_class=reviewer_class,
        reviewed_utc=reviewed_utc))

    promotion = {
        "artifact": ARTIFACT_PATH,
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": artifact_sha,
        "candidate": CANDIDATE_PATH,
        "candidate_sha256": artifact_sha,
        "decision_by": "cedar-lane-coordinator",
        "evidence": evidence_paths,
        "evidence_sha256": {
            rel: sha256_bytes(files[rel]) for rel in evidence_paths if rel in files
        },
        "promoted_from": "working",
        "promoted_utc": promoted_utc,
        "promotion_id": promotion_id,
        "reviews": [review_path],
        "reviews_sha256": {review_path: sha256_bytes(files[review_path])},
        "schema": "bvm-promotion/0.1",
    }
    # A deliberately dangling evidence reference (case 02) still needs a map
    # entry so the only structural gaps are the ones the case teaches.
    for rel in evidence_paths:
        if rel not in files:
            promotion["evidence_sha256"][rel] = sha256_bytes(b"missing-referenced-receipt")
    files[promotion_path] = dump_json(promotion)

    files["INDEX.json"] = dump_json({
        "lineages": {
            LINEAGE_ID: {
                "current": ARTIFACT_PATH,
                "promotion": promotion_path,
                "promotion_sha256": sha256_bytes(files[promotion_path]),
                "status": "current",
                "version": "1.0.0",
            }
        },
        "schema": "bvm-index/0.1",
        "updated_utc": index_utc,
    })
    return files


def write_tree(root: Path, files: dict[str, bytes]) -> None:
    if root.exists():
        shutil.rmtree(root)
    for rel, data in sorted(files.items()):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def refresh_index(files: dict[str, bytes]) -> None:
    """Re-bind INDEX.json to the current promotion bytes after a mutation."""
    index = json.loads(files["INDEX.json"].decode("utf-8"))
    entry = index["lineages"][LINEAGE_ID]
    entry["promotion_sha256"] = sha256_bytes(files[entry["promotion"]])
    files["INDEX.json"] = dump_json(index)


def rebind_promotion_review(files: dict[str, bytes],
                            promotion_path: str = "RECEIPTS/promotions/promote-v1.json",
                            review_path: str = "RECEIPTS/reviews/independent-review-v1.json") -> None:
    """Re-hash the review inside the promotion after the review file changed."""
    promotion = json.loads(files[promotion_path].decode("utf-8"))
    promotion["reviews_sha256"][review_path] = sha256_bytes(files[review_path])
    files[promotion_path] = dump_json(promotion)
    refresh_index(files)


def case_01() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Self-review only -> BVM031."""
    fixed = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                        extra_receipts={})
    broken = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                         extra_receipts={}, reviewer_class="writer-self-check")
    return broken, fixed


def case_02() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Cited receipt file missing -> BVM016 (+ BVM033 promotion ripple)."""
    evidence = [
        "RECEIPTS/evidence/shelf-count-v1.json",
        "RECEIPTS/evidence/germination-check-v1.json",
    ]
    fixed = build_vault(evidence_paths=evidence, extra_receipts={},
                        include_germination=True)
    broken = dict(fixed)
    del broken["RECEIPTS/evidence/germination-check-v1.json"]
    return broken, fixed


def case_03() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Frozen candidate edited after promotion -> BVM033."""
    fixed = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                        extra_receipts={})
    broken = dict(fixed)
    broken[CANDIDATE_PATH] = broken[CANDIDATE_PATH].replace(
        b"holds 48 labeled\npackets across 12 species",
        b"holds 52 labeled\npackets across 12 species")
    assert broken[CANDIDATE_PATH] != fixed[CANDIDATE_PATH]
    return broken, fixed


def case_04() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Contradicting active pass/fail counts -> BVM024."""
    fixed = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                        extra_receipts={}, include_first_count=True,
                        supersedes_first_count=True)
    broken = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                         extra_receipts={}, include_first_count=True,
                         supersedes_first_count=False)
    return broken, fixed


def case_05() -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Silent edit after review -> BVM037 + BVM031 + BVM033 dependents."""
    typo_body = BODY.replace("{tomato}", "tomatoe")
    clean_body = BODY.replace("{tomato}", "tomato")
    # The originally promoted state: the body carries a species-name typo.
    original = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                           extra_receipts={}, body=typo_body)

    # Broken: the typo is fixed directly in CANON; nothing else moves.
    broken = dict(original)
    metadata = {
        "schema": "bvm-artifact/0.1",
        "artifact_id": ARTIFACT_ID,
        "lineage_id": LINEAGE_ID,
        "title": "Cedar Lane seed cabinet shelf count v1.0.0",
        "state": "canon",
        "version": "1.0.0",
        "created_utc": T_CREATED,
        "updated_utc": T_UPDATED,
        "evidence": ["RECEIPTS/evidence/shelf-count-v1.json"],
        "reviews": ["RECEIPTS/reviews/independent-review-v1.json"],
        "promotion_receipt": "RECEIPTS/promotions/promote-v1.json",
    }
    broken[ARTIFACT_PATH] = artifact_bytes(metadata, clean_body)

    # Fixed: the same edit done honestly - updated_utc bumped, fresh review of
    # the new bytes, fresh candidate freeze and promotion, index re-bound.
    # The stale first review and promotion stay on disk as history.
    fixed = build_vault(evidence_paths=["RECEIPTS/evidence/shelf-count-v1.json"],
                        extra_receipts={}, body=clean_body,
                        promotion_path="RECEIPTS/promotions/promote-v2.json",
                        promotion_id="promotion.shelf-count.v2",
                        review_path="RECEIPTS/reviews/independent-review-v2.json",
                        review_id="review.shelf-count.v2",
                        updated_utc=T_UPDATED_2, reviewed_utc=T_REVIEWED_2,
                        promoted_utc=T_PROMOTED_2, index_utc=T_INDEX_2)
    fixed["RECEIPTS/reviews/independent-review-v1.json"] = original[
        "RECEIPTS/reviews/independent-review-v1.json"]
    fixed["RECEIPTS/promotions/promote-v1.json"] = original[
        "RECEIPTS/promotions/promote-v1.json"]
    return broken, fixed


BUILDERS = {
    "01-missing-review": case_01,
    "02-missing-reference": case_02,
    "03-candidate-byte-mismatch": case_03,
    "04-active-receipt-conflict": case_04,
    "05-review-byte-mismatch": case_05,
}


def main() -> int:
    for case_id, builder in BUILDERS.items():
        broken, fixed = builder()
        write_tree(CASES / case_id / "broken-vault", broken)
        write_tree(CASES / case_id / "fixed-vault", fixed)
        print(f"wrote {case_id}: broken {len(broken)} files, fixed {len(fixed)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
