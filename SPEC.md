# BAION Vault Method — Core Specification v0.1

**Status:** method v0.1.1, released; public reference methodology. Ships in repository release v0.3.0 (see CHANGELOG.md); the method contract last changed in v0.1.1, which closed the vault.toml key set (BVM004).

**Version:** 0.1.1

**Prepared:** 2026-07-15

**Normative language:** **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express requirement strength within this specification.

## 1. Purpose and boundary

BVM defines a file-based state contract for projects in which humans and AI agents create, inspect, execute, review, correct, and promote artifacts. Its purpose is to prevent plausible output from silently becoming accepted project state without evidence and explicit authority.

BVM governs the **state and provenance of bounded claims**. It does not determine whether an AI system is conscious, a scientific theory is true, legal advice is correct, a system is safe, or a business decision is wise.

## 2. Core entities

- An **artifact** is a durable file carrying a claim, decision, handoff, or historical record.
- A **receipt** is a durable record of an observation, execution, search, review, or promotion event.
- A **lineage** is the ordered history of artifacts representing one evolving subject.
- A **candidate** is the frozen byte-for-byte artifact submitted to review and promotion.
- **Canon** is current accepted project state for a bounded lineage. Canon is not universal truth.
- The **index** names the current canon artifact for each live lineage.
- The **governed object** is the actual implementation, dataset, registry, source, model, binary, or configured environment on which a claim depends.
- A **proxy** is any substitute, reimplementation, mock, summary, cached description, harness, or remembered representation of the governed object.

An AI agent MAY draft any of these records. An AI agent MUST NOT make unsupported recollection or fluent synthesis equivalent to established state.

## 3. Required structure

A structurally conforming v0.1 vault MUST contain:

```text
vault.toml
INDEX.json
INBOX/
WORKING/
CANON/
RECEIPTS/
RETRACTIONS/
HANDOFFS/
ARCHIVE/
```

`RECEIPTS` MAY be subdivided, but candidate snapshots used for promotion MUST be below `RECEIPTS/candidates/`.

`vault.toml` MUST declare `schema = "bvm-vault/0.1"`, a non-empty vault `name`, and a Semantic Versioning `method_version` in the compatible `0.1.x` series, and MUST NOT contain any other key. Unknown keys are a conformance error, not an extension point: a checker that ignored them would hand back a `PASS` for configuration it never honoured. A later method series requires a corresponding schema and checker contract rather than silently claiming v0.1 conformance.

`INBOX` MAY contain unmanaged capture material. Markdown under `WORKING`, `CANON`, `HANDOFFS`, and `ARCHIVE` is managed and subject to this specification.

## 4. States

### 4.1 INBOX

Untriaged capture. Presence in `INBOX` MUST NOT be represented as acceptance or verification.

### 4.2 WORKING

Provisional work. A working artifact MAY be incomplete, contradicted, or awaiting evidence. Its metadata state MUST be `working`.

### 4.3 CANON

Current accepted project state. A canon artifact MUST satisfy section 12 and its metadata state MUST be `canon`.

### 4.4 ARCHIVE

Preserved non-current state. Archive status does not by itself mean “wrong”; it means “not current.” Its metadata state MUST be `archive`. Every managed archive artifact MUST be reachable from a supersession or retraction record.

### 4.5 RETRACTION

A retraction is a separate correction record. The retracted artifact MUST remain in `ARCHIVE`, and the record MUST identify its exact bytes by SHA-256. Retraction is not deletion.

### 4.6 HANDOFF

A continuity artifact. Its metadata state MUST be `handoff`, and its body MUST contain the semantic sections required by section 19.

## 5. Authority domains

BVM separates authority domains that are often conflated:

1. **Authorization and conversation state.** A transcript or signed decision can establish what was requested, approved, rejected, or said.
2. **External factual state.** A primary source, direct measurement, authoritative registry, or executed governed object is required when the claim depends on the outside world.
3. **Project-accepted state.** The indexed canon artifact establishes what the project currently accepts within its declared boundary.
4. **Provisional reasoning.** Working notes establish only that a hypothesis, draft, or proposal exists.

A transcript MUST NOT be used as proof that an external factual statement is true merely because it was stated. Canon MUST NOT be described as universal truth merely because the project promoted it.

## 6. No-gap-fill rule

When required evidence is missing, state MUST remain `unknown`, `unverified`, `inconclusive`, or equivalently bounded. A writer MUST NOT manufacture a path, result, source, date, execution, approval, quote, prior decision, or absent file to complete a narrative.

A missing artifact MUST be reported as missing. A failed inspection MUST be reported as failed. An ambiguous result MUST remain ambiguous until evidence resolves it.

## 7. Governed-object and proxy rule

When a claim depends on the behavior or contents of a specific object, the governed object MUST be inspected or executed. Its identity MUST be bound by a receipt when the claim enters canon.

A proxy MAY be used for exploration, but it MUST be labeled through `object_mode` and MUST NOT inherit a claim about the governed object. `requires_canon_object: true` combined with `object_mode: proxy` is nonconforming.

If the governed object is unavailable, verification MUST stop at that boundary. The artifact MAY record the attempted procedure and the missing dependency.

## 8. Enforcement separation

The primary enforcer for canon promotion MUST differ from the writer. BVM recognizes four enforcement classes:

1. **Mechanical invariant:** a deterministic checker, schema, test, hook, or script rejects invalid state.
2. **Separate review surface:** another human, process, or independently prompted agent examines the artifact.
3. **Primary-source or governed-object check:** the relevant source is queried, read, measured, or executed directly.
4. **Writer self-discipline:** the writer remembers and follows a rule.

Class 4 MAY support the process but MUST NOT be the only canon control. Several reviews using the same incomplete evidence window are separate review surfaces, not independent factual confirmation.

## 9. Evidence receipts

### 9.1 Minimum shape

An evidence receipt MUST identify:

- a unique receipt identifier;
- the subject artifact identifier;
- the receipt kind;
- a UTC capture time;
- a bounded scope;
- a status;
- a vault-relative source path and SHA-256 of the source bytes.

A receipt MAY provide a stable `applicability_id`. When present, it identifies the machine-comparable boundary within which pass/fail receipts may conflict or supersede one another. When absent, the reference checker falls back to normalized scope text; semantic applicability still requires review.

An `executed-object` receipt MUST additionally identify the governed object path and SHA-256. A `unit-check` receipt MUST name its `unit_id`. An `authoritative-search` receipt MUST name its authority, procedure, and boundary.

A hash proves byte identity. It does not prove truth, authenticity, completeness, safety, or reviewer independence.

### 9.2 Applicability

A receipt applies only to the scope it records. Evidence for one version, environment, dataset, query, unit, or function MUST NOT be generalized beyond that scope without another justified transition.

### 9.3 Supersession and current receipt resolution

An evidence receipt MAY identify `supersedes_receipt`. The newer and older receipts MUST share subject, kind, and applicability boundary, and the newer capture time MUST be later. A superseded receipt remains historical but MUST NOT be cited by a conforming current artifact.

Within a declared supersession chain, the controlling receipt is the newest **applicable, provenance-valid, non-superseded** receipt. Timestamp alone is insufficient. Outside a declared supersession chain, applicable active receipts remain active. If active pass/fail receipts contradict one another for current canon and neither explicitly supersedes the other, canon is nonconforming until reconciliation occurs.

## 10. Exact-byte review

A review receipt MUST identify the artifact path, artifact identifier, exact artifact SHA-256, reviewer class, verdict, review time, scope, and notes.

A qualifying canon review MUST:

- have verdict `pass`;
- not use a writer-self-check class;
- resolve to the exact managed artifact path;
- match the artifact's current bytes by SHA-256.

Any byte change after review invalidates the review binding. A review receipt establishes that a declared review occurred against those bytes; it does not prove that the reviewer was independent or correct.

## 11. Frozen candidate

Before promotion, the exact candidate bytes MUST be preserved below `RECEIPTS/candidates/`. The promotion receipt MUST bind both the candidate and the final canon artifact by path and SHA-256, and the two files MUST be byte-identical.

This rule prevents an artifact from being edited after review while retaining stale approval or promotion records.

## 12. Promotion gate

An artifact MUST NOT enter `CANON` until all applicable conditions below are satisfied:

1. It has valid metadata and a stable lineage identifier.
2. At least one evidence receipt resolves; every cited receipt is structurally valid, scoped to the artifact identifier, and not superseded.
3. At least one qualifying non-self review is bound to the exact artifact bytes.
4. The final candidate is frozen under `RECEIPTS/candidates/` and is byte-identical to the canon artifact.
5. The promotion receipt matches the artifact identifier, path, SHA-256, candidate path, candidate SHA-256, complete evidence set, and complete review set.
6. The promotion receipt contains exact SHA-256 maps for every evidence and review receipt, and every digest matches the current receipt bytes.
7. Promotion occurs no earlier than the artifact update, cited evidence captures, and cited reviews.
8. Every declared negative result satisfies section 13.
9. Every declared aggregate satisfies section 14.
10. Every declared negative-existence claim satisfies section 15.
11. Every declared governed-object dependency satisfies section 7.
12. No unresolved active receipt contradiction remains for current canon.
13. `INDEX.json` names the artifact as the sole current canon artifact for its lineage and is no older than the artifact or promotion.
14. A predecessor, when declared, is preserved in `ARCHIVE` and linked through a valid supersession chain.

Promotion is an auditable state transition, not an unrecorded file copy.

## 13. Negative results and positive controls

An artifact with `result: negative` MUST cite `positive_control_receipt`, and that receipt MUST also appear in the artifact's evidence set. It MUST be a passing `positive-control` receipt.

A positive control does not prove the negative result correct. It establishes only that a basic detection path worked within the control's scope.

When a negative result could mean either “the phenomenon is absent” or “the search, optimizer, instrument, or harness failed,” those hypotheses MUST remain separate. A constructive witness can establish reachability; optimizer failure alone cannot establish impossibility.

## 14. Aggregate claims

When an artifact declares `aggregate`, it MUST provide:

- a non-empty list of unique unit identifiers under `aggregate.units`;
- an exact map from each unit identifier to one receipt under `aggregate.unit_receipts`;
- each mapped receipt in the artifact's evidence set;
- a passing `unit-check` receipt whose `unit_id` matches the declared unit.

This gate applies only when the author declares an aggregate. The checker cannot infer an omitted unit from prose.

## 15. Negative-existence claims

An artifact with `claim_type: negative-existence` MUST cite an `authoritative_search_receipt` that also appears in its evidence set. The receipt MUST be a completed `authoritative-search` record and name:

- the authority searched;
- the procedure or query;
- the boundary of the search.

Naming an authority in a bibliography without querying it is not verification. A search receipt proves the recorded search occurred against the recorded source bytes; it does not prove the authority was complete.

## 16. Supersession

A superseding artifact MUST:

- share its predecessor's lineage identifier;
- have a higher Semantic Versioning precedence than the predecessor;
- identify the predecessor with a safe, resolving vault-relative path;
- preserve a current canon predecessor in `ARCHIVE`;
- leave the supersession graph acyclic.

A build-metadata-only SemVer change does not increase precedence.

## 17. Retraction

A retraction record MUST contain:

- a unique identifier;
- the path and SHA-256 of a managed `ARCHIVE` artifact;
- a UTC retraction time no earlier than the artifact's update time;
- a reason;
- `preserve_original: true`;
- either a null replacement or the path and SHA-256 of a managed current `CANON` replacement in the same lineage.

The historical artifact MUST NOT be silently rewritten to make the prior claim disappear. A later correction MAY correct an earlier retraction, but the full chain remains available.

## 18. Index and archive reachability

`INDEX.json` MUST contain valid UTC metadata and a lineage map. Each entry MUST resolve to a managed canon artifact whose lineage and version agree with the entry and whose status is `current`. It MUST also identify and SHA-256-bind the same promotion receipt named by the artifact.

There MUST be at most one live canon artifact per lineage. Every live canon artifact MUST be reachable from the index. Every managed archive artifact MUST be reachable from a supersession or retraction record.

## 19. Handoffs and continuity

A managed handoff MUST declare non-empty, unique vault-relative `current_state` and `authority_sources` arrays in metadata. Every path MUST resolve; `current_state` MUST include `INDEX.json` or a managed Markdown artifact whose declared state is `canon`.

A managed handoff MUST also contain headings that cover:

- objective and scope;
- current canon or authority;
- verified or completed work;
- unknowns or contradictions;
- proposed next actions;
- stop conditions.

A handoff SHOULD identify changed files and exact receipt paths. It MUST distinguish verified work from proposals and MUST NOT rely on an agent's private recollection as the only continuity source.

## 20. Tool scope

A tool that aggregates or mutates project state SHOULD expose a read-only check or dry-run mode. It SHOULD record declared scope before mutation and actual changed files afterward.

A canon-moving tool MUST fail closed when its actual mutation scope exceeds its declared scope. The v0.1 reference checker documents this rule but does not inspect arbitrary external tool executions.

## 21. Artifact metadata

Managed Markdown MUST begin with a strict JSON metadata block:

```markdown
<!-- bvm
{
  "schema": "bvm-artifact/0.1",
  "artifact_id": "artifact.example.v0_1_0",
  "lineage_id": "lineage.example",
  "title": "Example",
  "state": "working",
  "version": "0.1.0",
  "created_utc": "2026-07-15T12:00:00Z",
  "updated_utc": "2026-07-15T12:00:00Z"
}
-->
```

The metadata object MUST use strict JSON with no duplicate member names and no nonstandard numeric constants such as `NaN`, `Infinity`, or `-Infinity`. Required string fields are `schema`, `artifact_id`, `lineage_id`, `title`, `state`, `version`, `created_utc`, and `updated_utc`. Handoff artifacts additionally require the authority arrays in section 19. Timestamps use `YYYY-MM-DDTHH:MM:SSZ`. Versions use Semantic Versioning syntax and precedence; build metadata does not increase precedence.

YAML front matter MAY be used by a separate profile, but the v0.1 reference checker does not parse it and such a vault cannot claim reference-checker structural conformance.

## 22. Structural conformance

A vault MAY claim **BVM v0.1 reference-checker structural conformance** only when:

- the `bvm-lint` version used is recorded;
- the checker exits successfully against the vault;
- no required semantic trigger was knowingly omitted merely to evade a gate.

The final condition is a governance requirement, not something the checker can prove.

Structural conformance MUST NOT be represented as factual validation, legal compliance, scientific peer review, safety certification, security certification, or proof of human/reviewer independence.

## 23. Extensions and profiles

An extension MUST NOT weaken a core requirement while claiming full v0.1 conformance. Extension metadata SHOULD use namespaced keys and SHOULD ship fixtures and enforcement code.

Sections 1–23 are the core method. Naming aesthetics, decorative stamps, organization-specific folder depth, preferred review counts beyond the minimum, and other local conventions are non-normative unless they implement a stated gate. See [`docs/recommended-practices.md`](docs/recommended-practices.md) and [`docs/baion-specific-patterns.md`](docs/baion-specific-patterns.md).
