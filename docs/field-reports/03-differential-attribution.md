# Field report 03 — A differential probe corrected attribution

## Initial claim

A parity failure involving lax parsing was attributed to the wrong implementation lineage during a multi-implementation review. For part of the review window, the written diagnosis named one lineage as the source of the divergence.

## Missing gate

The aggregate result showed that the implementations disagreed, but it did not expose a minimal per-lineage outcome for the triggering case. Review discussion filled the missing attribution from expectation and memory.

## Catch

A small differential corpus and probe reported each lineage independently on the same locked input. The probe reversed the attribution: the originally blamed implementation was behaving as intended, and a different lineage was accepting the invalid case.

## Correction

The earlier attribution was preserved as a superseded record, the defect owner was corrected, and the shared conformance corpus was expanded so the same divergence could be found automatically on every run.

## Enforcement added

- Aggregate pass/fail is not enough for attribution; emit per-unit and per-lineage results.
- Lock the smallest case that distinguishes the implementations.
- Run all lineages through one comparison contract before naming the defect owner.
- Convert a review catch into a permanent corpus case and CI check.
- Preserve the prior attribution so the correction path remains visible.

## What the gate saved

The differential probe prevented effort from being spent repairing the wrong implementation and converted an hours-long interpretive error into a deterministic regression test.
