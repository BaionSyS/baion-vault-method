# Promotion, supersession, and retraction

## Promotion

Promotion answers: “What does this project accept now, and why?” It requires evidence, a qualifying exact-byte review, a byte-identical frozen candidate, a promotion receipt, and an index update.

The promotion receipt binds:

- the artifact and candidate paths and bytes;
- the complete evidence and review path sets;
- the exact bytes of every cited evidence and review receipt;
- the promotion time and decision authority.

`INDEX.json` then identifies and hashes that same promotion receipt. The result is a dependency chain:

```text
source bytes → evidence receipt bytes → artifact/candidate bytes
             → review receipt bytes   → promotion receipt bytes → INDEX.json
```

A mutation anywhere in the declared chain invalidates downstream conformance until the changed state is reviewed and rebound. This does not make the chain tamper-proof; version control, signatures, or external publication records can add outer tamper evidence.

The frozen candidate prevents a subtle failure: reviewing one byte sequence and later promoting a quietly edited one under the same title.

## Supersession

Supersession answers: “What replaced the prior artifact?” The new artifact shares a lineage, has greater Semantic Versioning precedence, points to its predecessor, and explains the delta. The predecessor remains available in `ARCHIVE`.

Receipt supersession is narrower. A new evidence receipt may replace only one with the same subject, kind, and applicability boundary; it must be later and cannot form a cycle.

## Retraction

Retraction answers: “What accepted or influential claim must no longer be relied upon?” The correction record identifies the exact prior bytes by hash, preserves the original under `ARCHIVE`, and explains the failure mode. Deleting or rewriting the old file would destroy the evidence needed to understand propagation and correction.

When a replacement is named, the replacement must be current canon in the same lineage, its hash must match, and the retraction time must not predate the replacement artifact or its promotion.

## A retraction can be corrected

Corrections are claims too. If later inspection shows that a retraction was based on a partial source window or invalid test, add a new correction record and preserve the earlier one. Do not rewrite the sequence into a falsely clean history.

## Current-state resolution

`INDEX.json` names current canon and binds the controlling promotion receipt. Historical search results must be interpreted through promotion, supersession, and retraction pointers before they are treated as controlling state. A newer timestamp without applicable, non-superseded provenance does not outrank an older verified record.
