# BAION Vault Method

**A file-based governance layer for human–AI work where agents do not get to invent state.**

> **Agents may propose state. Receipts establish it.**

[![Verify](https://github.com/BaionSyS/baion-vault-method/actions/workflows/verify.yml/badge.svg)](https://github.com/BaionSyS/baion-vault-method/actions/workflows/verify.yml)
[![Version](https://img.shields.io/badge/version-0.3.0-5c677d)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Status:** v0.3.0, released 2026-08-28. Earlier public tags [`v0.2.0`](https://github.com/BaionSyS/baion-vault-method/releases/tag/v0.2.0) and [`v0.1.0`](https://github.com/BaionSyS/baion-vault-method/releases/tag/v0.1.0) remain the records of the prior cuts.

Two versions, on purpose: the **release version** (0.3.0) names what ships from this repository — checker, lab, docs. The **method version** (0.1.1) names the specification contract in [`SPEC.md`](SPEC.md) that vaults declare conformance to via `method_version`. This release tightens the checker and adds one normative sentence to the contract (`vault.toml` carries no undeclared keys); vaults declaring any `0.1.x` remain in-series.

**Break it. Fix it. Try to beat it:** run [`lab/start.sh`](lab/README.md) — the Vault Lab, a five-case guided falsification run against the real checker.

BAION Vault Method (BVM) is a reference methodology for maintaining trustworthy project state when humans and AI agents work in the same file-based environment. It separates proposed work from accepted claims, requires addressable evidence before promotion, preserves corrections without erasing history, and ships an executable checker so structural conformance is a command rather than a feeling.

BVM is **not** a consciousness claim, an AI-safety certification, a substitute for domain expertise, or a universal knowledge-management standard. Method v0.1.0 is a bounded reference method with a bounded checker.

## Try to break it — the Vault Lab

The fastest way to understand the method is to watch it fail. The
[Vault Lab](lab/README.md) walks you through five small vaults that each
violate one MUST — you predict the diagnostic, watch the real checker
catch it, study the exact repair diff, and watch it pass. Four judgment
scenarios then cover what the checker *cannot* decide, and the
[challenge](lab/challenge/README.md) invites you to construct a vault that
violates a SPEC.md MUST while `bvm-lint --strict` stays green — verified
catches are credited in the Hall of Catches.

```bash
lab/start.sh          # guided run, 15-25 minutes
lab/start.sh --check  # non-interactive fixture verification
```

## The problem

AI collaborators can produce useful work quickly. Fluent output can also conceal:

- unsupported gap-filling;
- stale or contradictory project state;
- several reviewers sharing the same incomplete evidence window;
- a proxy, mock, summary, or remembered description substituted for the governed object;
- negative results from an unproven measurement path;
- aggregate claims where one unit was never checked;
- corrections that overwrite the very history needed to audit them.

A folder tree alone does not prevent those failures. BVM treats accepted state as something that must be **established**, not merely written.

## The state contract

1. **Unknown stays unknown.** Missing evidence is not completed with plausible prose.
2. **The governed object outranks its description.** Inspect or execute the canonical source, function, dataset, registry, or binary when the claim depends on it.
3. **A proxy does not inherit the governed object's claim.** Substitutes are labeled and bounded.
4. **The primary enforcer differs from the writer.** Self-reminders are a backup, not the canon gate.
5. **Receipts precede promotion.** Evidence, review, candidate bytes, and the promotion decision remain addressable.
6. **Reviews bind exact bytes.** A review of yesterday's draft does not approve today's edit.
7. **Promotion binds its receipts.** Evidence and review records cannot change after promotion without invalidating current state.
8. **Negative results require a positive control.** “Nothing happened” is uninterpretable until the path detects a known signal.
9. **Aggregate claims enumerate their units.** Every declared unit maps to a passing unit receipt.
10. **Receipt control is explicit.** Applicability, provenance, and declared supersession—not timestamp alone—determine which receipts remain controlling; unresolved applicable conflicts block canon.
11. **Corrections preserve history.** Supersession and retraction retain the prior bytes and verify identity by hash.

The normative requirements are in [`SPEC.md`](SPEC.md).

## What is distinctive here

`WORKING` versus `CANON`, promotion gates, and preserved history have precedents in research and data governance. BVM's sharper contribution is the **AI collaboration contract around them**:

- an agent may draft state but cannot establish it from recall;
- transcripts establish authorization history, not external factual truth;
- a canonical-object claim stops when the real object cannot be inspected or executed;
- multiple AI reviews sharing one evidence window do not become independent factual anchors;
- corrections preserve the failed claim and its hash;
- the repository includes machinery that rejects declared state when its receipts no longer match.

The method is accompanied by anonymized operating reports that preserve real catch-and-correction shapes alongside the fictional tutorial. They are not independent proof that the method generalizes or earns its overhead in every setting.

## Quick start

The checker requires Python 3.11 or newer and has no runtime dependencies outside the standard library. Install it from PyPI:

```bash
pipx install baion-vault-method
bvm-lint --help
```

(`pip install baion-vault-method` works equally; `pipx` keeps the tool isolated.)

Or work from a clone of this repository:

```bash
python -m pip install -e .
bvm-lint examples/tutorial-vault --strict
./verify_repo.sh
```

Expected lint result:

```text
PASS: structural conformance established for examples/tutorial-vault
```

A zero exit code means the checker found no structural violations. It does **not** prove that the underlying claim is true, safe, complete, or persuasive.

See [`QUICKSTART.md`](QUICKSTART.md) for the promotion sequence. A crucial detail is that the final candidate is frozen under `RECEIPTS/candidates/`; the review and promotion records must match the exact promoted bytes.

## Reference structure

```text
VAULT/
├── vault.toml
├── INDEX.json
├── INBOX/
├── WORKING/
├── CANON/
├── RECEIPTS/
│   ├── candidates/
│   ├── data/
│   ├── evidence/
│   ├── reviews/
│   └── promotions/
├── RETRACTIONS/
├── HANDOFFS/
└── ARCHIVE/
```

The directories are not the method by themselves. The method is the set of allowed transitions and the evidence required to cross them.

```text
CAPTURE → WORKING → EVIDENCE + SEPARATE ENFORCEMENT → FROZEN CANDIDATE → CANON
                       ↘ contradiction / failure                 ↘
                         RECONCILE                         SUPERSEDE / RETRACT
                                                               ↓
                                                            ARCHIVE
```

## What ships

- A normative [core specification](SPEC.md).
- A zero-dependency Python checker with stable diagnostic codes.
- Machine-readable schemas and starter templates.
- A runnable [fictional tutorial vault](examples/tutorial-vault/README.md).
- Four anonymized [field reports](docs/field-reports/README.md) derived from real operating catches.
- Tests for valid state and failure paths, pinned CI actions, link validation, and publication-boundary checks.
- A clear split between [core requirements](SPEC.md), [recommended practices](docs/recommended-practices.md), and [BAION-specific patterns](docs/baion-specific-patterns.md).

## What the checker enforces

`bvm-lint` checks declared structure, including:

- strict JSON metadata with duplicate-key and nonstandard-constant rejection;
- state/directory agreement, timestamps, unique identities, and safe vault-relative links;
- source, governed-object, review, candidate, promoted-artifact, retracted-artifact, and replacement hashes;
- exact agreement between an artifact's evidence/review set and its promotion receipt;
- SHA-256 binding of every evidence and review receipt used for promotion;
- SHA-256 binding of the current promotion receipt from `INDEX.json`;
- positive controls for declared negative results;
- authoritative-search receipts for declared negative-existence claims;
- per-unit receipts for declared aggregate claims;
- canonical-object execution requirements and proxy boundaries;
- SemVer-ordered, acyclic supersession with preserved predecessors;
- no orphaned archive artifacts;
- one indexed current canon artifact per lineage;
- required continuity sections in managed handoffs;
- unresolved pass/fail receipt conflicts for current canon.

The checker can only enforce requirements represented in declared metadata. It cannot infer that an author should have marked a claim as negative, aggregate, negative-existence, or canonical-object-dependent. That semantic declaration remains a review responsibility.

See the [linter reference](docs/linter-reference.md) and [conformance limits](docs/conformance-and-limits.md).

## Evidence from operation

The [field reports](docs/field-reports/README.md) preserve four catch shapes:

- shared reviewers reached the same wrong conclusion from one partial source window;
- a budget-bound null result was promoted into “wall” language, then retracted across a preserved claim chain after a larger run produced a witness;
- a differential probe showed that a parsing defect had been attributed to the wrong implementation;
- a negative-existence claim persisted without querying the authority it named.

Private paths, identities, unpublished subject matter, and protected implementation details are removed. The gate, catch, correction, and enforcement lesson remain.

## Start with the smallest useful profile

For a solo human working with one or more AI agents, begin with:

- `WORKING`, `CANON`, `RECEIPTS`, `RETRACTIONS`, `ARCHIVE`, and `INDEX.json`;
- at least one evidence receipt and one separate, exact-byte review for canon promotion;
- a frozen candidate, receipt-hash manifest, and exact-byte promotion receipt;
- a positive control for every declared negative result;
- a retraction record that preserves the prior artifact when a claim is withdrawn;
- `bvm-lint --strict` in CI.

Add richer receipt types and handoff discipline when the work needs them. Complexity that is not enforced is ceremony.

## Maturity and naming

This repository deliberately says **reference methodology**, not **standard**. Standards language would require broader adoption, independent implementations or conformance work, stable external governance, and evidence that the requirements generalize beyond the originating environment. Those conditions have not been earned yet.

## Public boundary

This repository is fresh public authorship. It is not a sanitized dump of a private operating vault. Field reports preserve failure shapes while removing private paths, project identifiers, counterparties, unpublished subject matter, and protected material. See [`PUBLICATION_BOUNDARY.md`](PUBLICATION_BOUNDARY.md).

## Contributing

A strong proposal identifies a concrete failure mode, names the enforcement site, includes a failing fixture, and adds a mechanical check when feasible. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`GOVERNANCE.md`](GOVERNANCE.md) first.

## Citation and licensing

Citation metadata is in [`CITATION.cff`](CITATION.cff). All material included in this public repository is licensed under the [MIT License](LICENSE). Private vault contents and other material not included here are outside this repository’s licensing and distribution boundary.
