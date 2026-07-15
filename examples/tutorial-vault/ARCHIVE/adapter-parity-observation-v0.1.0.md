<!-- bvm
{
  "schema": "bvm-artifact/0.1",
  "artifact_id": "artifact.adapter-parity.v0_1_0",
  "lineage_id": "lineage.adapter-parity",
  "title": "Adapter parity observation v0.1.0",
  "state": "archive",
  "version": "0.1.0",
  "created_utc": "2026-07-15T12:00:00Z",
  "updated_utc": "2026-07-15T12:20:00Z",
  "evidence": [
    "RECEIPTS/evidence/probe-v1.json",
    "RECEIPTS/evidence/positive-control-v1.json"
  ],
  "result": "negative",
  "positive_control_receipt": "RECEIPTS/evidence/positive-control-v1.json",
  "object_mode": "mixed"
}
-->
# Adapter parity observation v0.1.0

## Claim at the time

No divergence was observed between the reference and candidate normalizers, so the two adapters were treated as equivalent for the tested domain.

## Scope that was actually tested

The corpus contained two valid JSON objects. It did not contain duplicate object keys or other malformed-input cases.

## Why this artifact is archived and retracted

The claim was broader than the corpus. A later differential probe added duplicate-key cases and made the missing boundary visible. The original bytes remain here so the correction can be audited.

## Positive control

The harness detected an intentionally injected byte difference. That showed the comparison path could detect one known mismatch, but it did not prove that the corpus covered every relevant failure class.
