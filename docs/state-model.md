# State model

BVM separates **where an artifact lives**, **what the project accepts**, and **what the evidence establishes**.

## Folder state

- `INBOX`: captured, unmanaged.
- `WORKING`: proposed or incomplete.
- `CANON`: current accepted project state.
- `ARCHIVE`: preserved non-current managed state.
- `HANDOFFS`: continuity records.
- `RETRACTIONS`: correction records about archived artifacts.

## Claim state

An artifact may describe a result as positive, negative, mixed, inconclusive, unknown, or another bounded term. Folder state does not determine claim truth. A canon negative is still a bounded accepted interpretation, not metaphysical proof of absence.

## Receipt state

Receipts can pass, fail, record an observation, or remain inconclusive. Applicability and supersession decide whether they control a current claim. Newest timestamp alone does not.

## Lineage state

`INDEX.json` points to one current canon artifact per live lineage. Older lineage artifacts remain reachable through supersession and retraction links. The index answers “what does the project currently accept?” It does not erase prior state.

## Transition summary

```text
INBOX → WORKING → FROZEN CANDIDATE → CANON
                   evidence + review       │
                                            ├─ normal evolution → ARCHIVE via supersession
                                            └─ withdrawn claim  → ARCHIVE + RETRACTION
```
