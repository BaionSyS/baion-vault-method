# Why this vault fails — and why the repair looks the way it does

## The failure

The canon shelf count cites two pieces of evidence: the recount receipt and
a germination-check receipt. The recount receipt exists. The germination
receipt is a **dangling citation** — the artifact and the promotion receipt
both name `RECEIPTS/evidence/germination-check-v1.json`, but the file is
not in the vault.

Two diagnostics fire, and both are correct:

- `BVM016` — the artifact's evidence reference does not resolve to a
  recognized record.
- `BVM033` — the promotion gate cannot re-hash a receipt that is not there,
  so the promotion binding fails too.

The second one is not noise. A citation that cannot be fetched breaks
*every* layer that promised to have verified it. Declaring both codes up
front is the honest description of the blast radius.

## The repair

The fixed vault contains the germination receipt itself (hash-bound to its
log file, `RECEIPTS/data/germination-log-v1.txt`). Nothing else changes:
the artifact, promotion, and index in the broken vault were already written
as if the receipt existed. The repair is exactly one file — the one the
citation promised.

## What passing does NOT prove

A resolving citation proves the receipt exists with the recorded bytes. It
does not prove the ten-seed spot check was done carefully, or that 8-of-10
is a good floor. The checker verifies custody, not competence.
