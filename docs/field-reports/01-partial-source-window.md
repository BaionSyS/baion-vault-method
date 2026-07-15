# Field report 01 — A correction built from a partial source window

## Initial claim

Two AI review surfaces concluded that a documented mechanism was absent from the canonical implementation. A correction was prepared on the assumption that the documentation had overstated what the system actually did.

## Missing gate

Both reviews inspected the same incomplete source window. They interpreted a downstream function without tracing the relevant value to its upstream producer and did not read the canonical source file through the later implementation block.

Their agreement was real review convergence, but it was not independent factual confirmation.

## Catch

A complete read of the canonical source and a dependency trace showed that the mechanism was present. The proposed correction—not the original documentation—was wrong.

## Correction

The false correction was retracted. The original description was restored, the mistaken correction remained preserved in the history, and the failure mode was written into the operating ledger so the retract-and-undo chain could be audited.

## Enforcement added

- Read the complete relevant source object rather than a convenient excerpt.
- Trace derived values to their producer before interpreting downstream behavior.
- Treat reviewers sharing one source window as one factual anchor.
- Bind implementation claims to the canonical object, not to recollection or prose about it.
- Preserve a correction when the correction itself is later retracted.

## What the gate saved

Without the full-source gate, correct code could have been modified to match an incorrect AI diagnosis, while the resulting history looked cleaner—and less truthful—than what actually happened.
