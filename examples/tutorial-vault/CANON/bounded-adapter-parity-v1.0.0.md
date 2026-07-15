<!-- bvm
{
  "schema": "bvm-artifact/0.1",
  "artifact_id": "artifact.adapter-parity.v1_0_0",
  "lineage_id": "lineage.adapter-parity",
  "title": "Bounded adapter parity result v1.0.0",
  "state": "canon",
  "version": "1.0.0",
  "created_utc": "2026-07-15T13:00:00Z",
  "updated_utc": "2026-07-15T13:12:00Z",
  "evidence": [
    "RECEIPTS/evidence/input-corpus-v2.json",
    "RECEIPTS/evidence/probe-v2.json",
    "RECEIPTS/evidence/executed-reference-object.json",
    "RECEIPTS/evidence/executed-candidate-object.json",
    "RECEIPTS/evidence/unit-valid-order.json",
    "RECEIPTS/evidence/unit-nested.json",
    "RECEIPTS/evidence/unit-duplicate-key.json",
    "RECEIPTS/evidence/unit-nested-duplicate.json"
  ],
  "reviews": [
    "RECEIPTS/reviews/independent-review-v1.json"
  ],
  "promotion_receipt": "RECEIPTS/promotions/promote-v1.json",
  "supersedes": "ARCHIVE/adapter-parity-observation-v0.1.0.md",
  "result": "positive",
  "requires_canon_object": true,
  "object_mode": "canonical",
  "executed_object_receipt": "RECEIPTS/evidence/executed-reference-object.json",
  "aggregate": {
    "units": [
      "valid-order",
      "nested",
      "duplicate-key",
      "nested-duplicate"
    ],
    "unit_receipts": {
      "valid-order": "RECEIPTS/evidence/unit-valid-order.json",
      "nested": "RECEIPTS/evidence/unit-nested.json",
      "duplicate-key": "RECEIPTS/evidence/unit-duplicate-key.json",
      "nested-duplicate": "RECEIPTS/evidence/unit-nested-duplicate.json"
    }
  }
}
-->
# Bounded adapter parity result v1.0.0

## Canonical claim

For the four cases in `WORKING/corpus/corpus-v2.tsv`, the reference and candidate normalizers agree byte-for-byte on accepted values and both reject duplicate object keys.

This claim is intentionally bounded to the hash-bound corpus bytes, both included object byte sequences, and the recorded execution output. It is not a claim about every JSON implementation or every malformed input.

## Correction from v0.1.0

The prior observation used only valid inputs and generalized beyond its test domain. Version 1.0.0 adds duplicate-key cases, executes the canonical reference object, and preserves the old artifact through a retraction record.

## Known

- The current four-case probe passes.
- Each declared aggregate unit has a passing unit-check receipt.
- The corpus bytes match the input-snapshot receipt.
- The canonical reference object's bytes match its executed-object receipt.
- The candidate object's bytes match its executed-object receipt.
- Those two recorded objects agree in the included v2 probe output.

## Unknown

- Behavior on JSON features not represented in the corpus.
- Cross-language behavior.
- Security properties of either implementation.

## Promotion boundary

The project accepts only the bounded claim above. Expanding or editing the corpus requires a new input receipt and unit receipts. Changing either executed object invalidates its object receipt, review binding, candidate snapshot, and promotion hash.
