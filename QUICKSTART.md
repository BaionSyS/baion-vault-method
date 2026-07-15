# Quick start

## 1. Install the checker

```bash
git clone https://github.com/BaionSyS/baion-vault-method.git
cd baion-vault-method
python -m pip install -e .
```

Python 3.11 or newer is required. The runtime checker uses only the Python standard library.

## 2. Verify the tutorial vault

```bash
bvm-lint examples/tutorial-vault --strict
```

For machine-readable output:

```bash
bvm-lint examples/tutorial-vault --json
```

Run the executable evidence sources as well:

```bash
python examples/tutorial-vault/WORKING/tools/run_probe.py --check
python examples/tutorial-vault/WORKING/tools/run_positive_control.py --check
```

The linter reads and hashes evidence sources; it intentionally does not execute arbitrary vault-provided code.

## 3. Start a vault

Copy the tutorial vault or create this reference structure:

```text
vault.toml
INDEX.json
INBOX/
WORKING/
CANON/
RECEIPTS/candidates/
RECEIPTS/data/
RECEIPTS/evidence/
RECEIPTS/reviews/
RECEIPTS/promotions/
RETRACTIONS/
HANDOFFS/
ARCHIVE/
```

Use [`templates/`](templates/) as starting points. The templates contain placeholders and are not expected to pass lint unchanged.

## 4. Keep canon empty until the gate is complete

Use this order:

1. Draft the artifact in `WORKING` and leave unknowns visible.
2. Run the relevant source, search, probe, or governed object.
3. Preserve the raw result under a stable path such as `RECEIPTS/data/`.
4. Create evidence receipts that hash the exact source bytes.
5. Add positive-control, per-unit, authoritative-search, or executed-object receipts when the claim shape requires them.
6. Finalize the proposed canon bytes and freeze an exact copy under `RECEIPTS/candidates/`.
7. Review those exact bytes. The review receipt must carry the artifact path and SHA-256.
8. Create a promotion receipt whose artifact, candidate, evidence, and review sets exactly match the artifact metadata. Include SHA-256 maps for every evidence and review receipt.
9. Place the byte-identical artifact in `CANON`; update `INDEX.json` with the promotion path and SHA-256 so current state binds the decision record.
10. Archive and link any predecessor. Create a retraction record when the prior claim is withdrawn rather than merely superseded.
11. Run `bvm-lint --strict` before commit and in CI.

Do not edit the artifact, evidence receipts, review receipts, or promotion receipt after promotion without regenerating every dependent hash through the index. A version-control commit is the recommended outer tamper-evidence layer.

## 5. Declare semantic triggers honestly

The checker does not read prose well enough to infer every claim shape. Metadata activates several important gates:

```json
{
  "result": "negative",
  "positive_control_receipt": "RECEIPTS/evidence/control.json",
  "claim_type": "negative-existence",
  "authoritative_search_receipt": "RECEIPTS/evidence/search.json",
  "requires_canon_object": true,
  "object_mode": "canonical",
  "executed_object_receipt": "RECEIPTS/evidence/executed-object.json"
}
```

Aggregate claims use an explicit unit list and a one-to-one receipt map. Omitting a trigger merely to avoid a gate violates the method even if the checker exits zero.

## 6. Put verification in CI

The included workflow runs:

- the test suite;
- the tutorial's executable probe and positive control;
- structural linting;
- relative-link validation;
- public-boundary, version-parity, diagnostic-parity, and release-surface checks.

Run the same verification locally:

```bash
./verify_repo.sh
```

## 7. Interpret a pass correctly

A pass establishes internal structural consistency for the declared metadata and files. It does not establish that the evidence is persuasive, the source is authoritative, the reviewer is independent, or the claim is true.
