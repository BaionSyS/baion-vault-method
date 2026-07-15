<!-- bvm
{
  "schema": "bvm-artifact/0.1",
  "artifact_id": "handoff.tutorial.v0_1_0",
  "lineage_id": "lineage.handoff.tutorial",
  "title": "Tutorial vault handoff",
  "state": "handoff",
  "version": "0.1.0",
  "created_utc": "2026-07-15T13:30:00Z",
  "updated_utc": "2026-07-15T13:30:00Z",
  "current_state": [
    "INDEX.json",
    "CANON/bounded-adapter-parity-v1.0.0.md"
  ],
  "authority_sources": [
    "INDEX.json",
    "RECEIPTS/promotions/promote-v1.json",
    "RETRACTIONS/retract-adapter-parity-v0.1.0.json"
  ]
}
-->
# Tutorial vault handoff

## Objective and scope

Demonstrate the BVM lifecycle with a fictional parser-parity claim.

## Current canon

`CANON/bounded-adapter-parity-v1.0.0.md` is current for `lineage.adapter-parity`.

## Verified or completed

The v2 probe, hash-bound corpus input, per-unit receipts, positive control, both executed-object receipts, byte-bound review, frozen candidate, promotion receipt, retraction, and index resolve under `bvm-lint`.

## Unknowns or contradictions

No claim is made about untested inputs, other runtimes, or hostile data.

## Proposed next actions

Add a new corpus case only through a new evidence receipt. Update canon only if the bounded claim changes.

## Stop conditions

Stop rather than inferring parity when the canonical object, corpus, candidate snapshot, or receipt source is missing.

## Files changed

This tutorial handoff records the example state only; it does not authorize external changes.
