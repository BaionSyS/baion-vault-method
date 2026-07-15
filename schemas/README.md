# Schemas

These JSON Schemas document the public v0.1 shapes for artifact metadata, evidence receipts, review receipts, promotion receipts, retractions, and the current-state index.

The Python checker is the reference executable conformance behavior for v0.1. The schemas are useful for editor validation, but they do not encode every cross-file invariant, including exact-byte agreement, receipt-hash maps, chronology, lineage reachability, applicability-scoped conflicts, or receipt-set equality.

`diagnostics.json` mirrors the stable public issue-code descriptions. `scripts/check_diagnostic_parity.py` verifies exact parity with `src/bvm_lint/codes.py` and code-set parity with the public linter table.
