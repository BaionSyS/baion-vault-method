# Evidence and receipts

A receipt is intentionally narrower than a conclusion. It records what was inspected, searched, measured, or executed; the boundary within which it applies; and the bytes that support that record.

## Three evidence layers

BVM separates three things that are easy to blur:

1. **Source bytes** — the raw output, registry export, log, dataset, probe result, or governed object.
2. **Receipt bytes** — the structured record that identifies the source, scope, status, time, and source hash.
3. **Artifact bytes** — the claim or conclusion that cites the receipt.

A promotion receipt binds all three layers. Changing any bound layer after promotion invalidates the declared current state until the dependent hashes are regenerated and the state is reviewed again.

## Evidence receipt

A v0.1 evidence receipt records:

- `receipt_id`;
- `subject_id`;
- `kind`;
- `captured_utc`;
- `status`;
- `scope`;
- `source`;
- `source_sha256`.

It may also declare `applicability_id`, a stable identifier for the condition, dataset, version, query boundary, or environment to which the receipt applies. When `applicability_id` is absent, the reference checker uses normalized `scope` text as a conservative fallback boundary for contradiction checks.

Useful `kind` values include `primary-source`, `probe`, `positive-control`, `executed-object`, `unit-check`, `authoritative-search`, and `measurement`.

Specialized kinds add fields:

- `executed-object` records the governed object path and object SHA-256; artifact metadata separately declares whether the governed result came from the canonical object, a proxy, a mixed path, or a non-applicable object path;
- `authoritative-search` records the authority, procedure or query, and search boundary;
- `unit-check` identifies the aggregate unit it covers;
- `positive-control` records a known signal used to establish that the detection path can succeed within the stated scope.

## Review receipt

A review receipt records the managed artifact path and SHA-256, reviewer class, scope, verdict, notes, and review time. The reference checker rejects `writer-self-check` as the only canon review, rejects a review bound to different bytes, and rejects a review that predates the artifact's declared final update.

A review receipt establishes that a declared review occurred against identified bytes. It cannot prove cognitive independence, competence, good faith, or the absence of a shared evidence window.

## Promotion receipt

A promotion receipt binds the decision to:

- the exact canon artifact path and SHA-256;
- a frozen candidate under `RECEIPTS/candidates/` and its SHA-256;
- the complete evidence and review path sets;
- an `evidence_sha256` map covering every evidence receipt file;
- a `reviews_sha256` map covering every review receipt file;
- the promotion time and decision authority.

The frozen candidate and canon artifact must be byte-identical. The receipt-path sets and hash-map keys must agree exactly with the artifact metadata. Editing the artifact, candidate, evidence receipts, or review receipts after approval causes conformance to fail.

`INDEX.json` then binds the controlling promotion receipt by both path and SHA-256. That closes the next mutation gap: editing the promotion decision record after indexing also invalidates current state.

## Receipt supersession

A corrected evidence receipt points to the receipt it supersedes. It must preserve the same `subject_id`, `kind`, and applicability boundary, have a later `captured_utc`, and remain outside a cycle. A current artifact cannot cite a stale receipt after a valid correction exists.

Within a declared correction or supersession chain, “freshest valid receipt controls” means more than “newest timestamp wins.” The receipt must be applicable, hash-valid, non-superseded, and compatible with the governing claim boundary. Without explicit supersession, applicable receipts remain active; a pass/fail conflict is surfaced rather than silently resolved by timestamp.

## Contradictory receipts

If active `pass` and `fail` receipts share the same current canon `subject_id`, `kind`, and applicability boundary, lint fails until one is explicitly superseded. Different applicability boundaries are not collapsed into a false contradiction.

Version 0.1 does not adjudicate the substance of the disagreement. It prevents applicable conflict from being silently averaged away.

## Hash discipline

SHA-256 answers an identity question: “Are these the same bytes?” It does not establish that the bytes are true, complete, safe, authentic, authoritative, or interpreted correctly. Domain review must still evaluate the evidence-producing procedure and the claim drawn from it.
