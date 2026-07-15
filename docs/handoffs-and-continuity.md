# Handoffs and continuity

AI-assisted projects often fail at thread boundaries rather than during a single task. BVM handoffs make continuity inspectable.

## Minimum handoff content

- objective and scope;
- current canon paths;
- verified receipts produced;
- unresolved contradictions;
- unknown or missing artifacts;
- operator decisions and their source;
- proposed next actions;
- stop conditions;
- files changed.

## Durable metadata

A managed handoff also carries:

```json
{
  "current_state": [
    "INDEX.json",
    "CANON/example-v1.0.0.md"
  ],
  "authority_sources": [
    "RECEIPTS/promotions/promote-example-v1.json",
    "RETRACTIONS/retract-example-v0.2.0.json"
  ]
}
```

Those arrays make “resume from the records” machine-checkable. Every path must resolve, and `current_state` must include `INDEX.json` or a managed Markdown artifact whose declared state is `canon`.

## Transcript rule

A transcript can establish what was said or authorized. It is not proof that an external claim within the transcript is true. The handoff points from conversational state to the evidence appropriate for each factual claim.

## No private-memory dependency

A new agent should be able to resume from durable artifacts without relying on hidden memory. When the handoff and current receipts disagree, the contradiction is surfaced rather than smoothed over.

## Stop rather than substitute

A handoff should name the boundary at which work must stop. Missing canonical objects, unresolved authority, absent receipts, or contradictory current state are reasons to stop and report the gap—not invitations to invent continuity.
