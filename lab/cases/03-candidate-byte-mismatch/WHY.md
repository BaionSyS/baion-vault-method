# Why this vault fails — and why the repair looks the way it does

## The failure

At promotion time the method freezes an exact byte copy of the promoted
artifact under `RECEIPTS/candidates/`. That snapshot is the tamper-evidence
seal: later, anyone can confirm that what sits in CANON is what was
actually reviewed and promoted.

In the broken vault, someone "corrected" the frozen snapshot afterward —
it now claims 52 packets while canon says 48. `BVM033` reports two
failures on the promotion binding:

- `candidate_sha256 differs from candidate bytes` — the snapshot no longer
  matches the hash recorded at promotion, and
- `candidate bytes differ from promoted artifact bytes` — the seal and the
  sealed object disagree.

Either line alone would mean the promotion can no longer vouch for itself.

## The repair

Restore the frozen candidate to the exact bytes of the promoted artifact.
One file changes, and it changes *back* — a frozen snapshot is history, and
history is repaired by restoration, never by a fresh edit.

If the *new* number (52) were actually correct, the right move would not be
to touch the snapshot at all: it would be a superseding v1.1.0 artifact
with its own evidence, review, freeze, and promotion. Scenario 2 in the
lab walks that judgment call.

## What passing does NOT prove

A byte-identical candidate proves the promoted bytes are the reviewed
bytes. It does not prove 48 is the true count — only that nobody swapped
the claim after it was reviewed.
