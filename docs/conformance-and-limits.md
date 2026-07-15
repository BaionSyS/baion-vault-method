# Conformance and limits

## The strongest accurate claim

A passing checker supports this statement:

> This vault passed BAION Vault Method v0.1 reference-checker structural conformance under checker version X.

It does not support “BVM certified,” “factually verified,” “scientifically proven,” “safe,” “legally compliant,” or “independently audited” unless a separate process establishes those claims.

## What is mechanically checked

The checker evaluates declared files, strict metadata, hashes, references, chronology, lineage, candidate and review binding, promotion-time receipt hashes, index-to-promotion binding, applicable gates, preservation links, and index reachability.

That gives the declared state a mechanically checked identity chain. It does not turn the checker into an adjudicator of truth.

## The semantic-trigger boundary

Several gates activate only when metadata declares the claim shape:

- `result: negative`;
- `claim_type: negative-existence`;
- `requires_canon_object: true`;
- `aggregate: {...}`.

The checker cannot reliably infer those meanings from arbitrary prose. An author who omits a truthful trigger can produce a structurally passing but methodologically nonconforming vault. Exact-byte review and human governance must examine trigger completeness.

## Independence boundary

A receipt can say `reviewer_class: separate-instance`. The checker can reject known self-review labels, but it cannot prove organizational independence, distinct evidence windows, absence of collusion, or genuinely independent reasoning.

## Evidence boundary

Hashes prove identity, not truth. A perfectly hash-bound fabricated log remains fabricated. Domain review must assess procedure, source authority, completeness, and interpretation.

## Applicability boundary

A receipt may declare a stable `applicability_id`. When it does not, the checker uses normalized scope text as a conservative contradiction boundary. That fallback is mechanical, not semantic understanding; two differently worded scopes may describe the same real condition, and one broad scope may contain narrower conditions.

## Execution boundary

`bvm-lint` does not execute arbitrary vault code. This is deliberate: structural checking should not become an implicit code-execution channel. Evidence generators run separately, and their outputs become receipt sources.

## Tamper-evidence boundary

The checker detects mismatches in the files it receives. It does not prove that an attacker has not replaced a mutually consistent set of files. Version-control history, signed commits or tags, transparency logs, external deposits, or other publication receipts can provide stronger outer evidence when the threat model requires it.

## Threat boundary

The checker is not a sandbox, malware scanner, secret scanner, signature-verification system, or hostile-filesystem defense. Use it only on material you are permitted to inspect.

## Method overhead

BVM adds cost. It is poorly suited to low-consequence scratch work where preservation and promotion would cost more than a mistake. Use the smallest profile that matches the consequence of false accepted state.
