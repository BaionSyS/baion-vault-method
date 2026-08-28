# Linter reference

`bvm-lint` is the reference structural checker for BVM v0.1. It reads vault files but does not execute vault-provided code. JSON is parsed strictly: duplicate members and nonstandard constants such as `NaN` and `Infinity` are rejected.

## Commands

```bash
bvm-lint VAULT_ROOT
bvm-lint --json VAULT_ROOT
bvm-lint --strict VAULT_ROOT
bvm-lint --explain BVM033
bvm-lint --version
```

Exit status:

- `0`: no structural errors; with `--strict`, no warnings either.
- `1`: one or more structural errors, or warnings under `--strict`.
- `2`: command-line usage error.

## Stable issue codes

| Code | Meaning |
|---|---|
| `BVM001` | A required BVM path is missing or has the wrong file type. |
| `BVM002` | `vault.toml` is malformed, lacks required identity fields, or declares a method version outside the compatible `0.1.x` series. |
| `BVM003` | `INDEX.json` is malformed or missing required index fields. |
| `BVM004` | `vault.toml` contains a key outside the declared set (`schema`, `name`, `method_version`). Unknown keys are errors, not lenience: a silently ignored key reads as configuration the checker accepted. |
| `BVM010` | Managed Markdown lacks a valid strict-JSON BVM metadata block. |
| `BVM011` | Two artifacts use the same `artifact_id`. |
| `BVM012` | An artifact declares an unknown state. |
| `BVM013` | Artifact state and managed directory disagree. |
| `BVM014` | Artifact version is not semantic-version syntax. |
| `BVM015` | A durable timestamp is invalid or temporally inconsistent. |
| `BVM016` | A vault reference is unsafe, missing, or leaves the vault. |
| `BVM017` | Required artifact metadata is missing or mistyped. |
| `BVM018` | An artifact repeats an evidence or review reference. |
| `BVM020` | A receipt is malformed, ambiguous, or uses an unsupported schema. |
| `BVM021` | An evidence source or executed object is missing or unsafe. |
| `BVM022` | A declared source or object hash differs from the referenced bytes. |
| `BVM023` | An artifact cites an explicitly superseded evidence receipt. |
| `BVM024` | Active receipts for one canonical subject and applicability boundary contradict without explicit supersession. |
| `BVM025` | Receipt identity, subject, kind, status, timestamp, or a required field is invalid. |
| `BVM026` | Receipt supersession or review chronology is inconsistent. |
| `BVM030` | A canon artifact lacks evidence receipts. |
| `BVM031` | A canon artifact lacks a qualifying non-self review bound to its exact bytes. |
| `BVM032` | A canon artifact lacks a promotion receipt. |
| `BVM033` | A promotion receipt disagrees with the artifact, frozen candidate, receipt sets, or bound receipt bytes. |
| `BVM034` | A canon artifact is not reachable as current from `INDEX.json`. |
| `BVM035` | More than one live canon artifact exists for one lineage. |
| `BVM036` | A promotion or index timestamp predates a required input. |
| `BVM037` | A review receipt is not bound to the exact artifact path and bytes. |
| `BVM040` | A supersession target is missing or belongs to a different lineage. |
| `BVM041` | The artifact supersession graph contains a cycle. |
| `BVM042` | A superseding artifact does not have a greater semantic version. |
| `BVM043` | A current canon predecessor is not preserved in `ARCHIVE`. |
| `BVM044` | An archived artifact is orphaned from supersession and retraction history. |
| `BVM050` | A retraction record is malformed or incomplete. |
| `BVM051` | A retraction does not preserve and hash-identify the archived original. |
| `BVM052` | A declared retraction replacement is invalid, unbound, or outside current canon. |
| `BVM053` | A retraction timestamp predates the artifact or replacement it describes. |
| `BVM060` | A negative result lacks a positive-control receipt in its evidence set. |
| `BVM061` | The cited positive-control receipt is not a passing positive control. |
| `BVM062` | An aggregate claim has an invalid or incomplete unit declaration. |
| `BVM063` | An aggregate unit lacks a matching passing `unit-check` receipt. |
| `BVM064` | A negative-existence claim lacks an authoritative-search receipt. |
| `BVM065` | An authoritative-search receipt lacks authority, procedure, or boundary. |
| `BVM070` | A canonical-object-dependent claim lacks an executed-object receipt. |
| `BVM071` | The executed-object receipt is not passing and hash-bound. |
| `BVM072` | A proxy is attempting to inherit a claim about the canonical object. |
| `BVM080` | An index entry does not resolve to matching current canon. |
| `BVM081` | An index lineage or version disagrees with the current artifact. |
| `BVM082` | An index entry does not bind the current promotion receipt by path and SHA-256. |
| `BVM090` | A handoff omits continuity sections or durable current-state and authority references. |

Repository verification checks that the implementation, `src/bvm_lint/codes.py`, `schemas/diagnostics.json`, and this table remain in parity.

## High-value checks

### Frozen promotion candidate

A promotion receipt points to a candidate snapshot under `RECEIPTS/candidates/`. The snapshot must be byte-identical to the promoted canon artifact, and both declared hashes must match. The receipt also carries exact SHA-256 maps for every evidence and review receipt. `INDEX.json` binds the resulting promotion receipt by path and SHA-256. This prevents an artifact or its approval inputs from being edited while retaining an apparently current trail.

### Exact review binding

A review receipt records the root-relative artifact path and SHA-256. It must postdate the artifact's declared `updated_utc`. A passing review of a different path, prior byte sequence, or pre-final version does not satisfy the canon gate.

### Receipt supersession

A corrected evidence receipt may supersede only a receipt with the same `subject_id`, `kind`, and applicability boundary, and its `captured_utc` must be later. Supersession chains must be acyclic. Artifacts that continue citing the superseded receipt fail.

### Applicability-scoped contradiction checks

Evidence receipts may declare an `applicability_id`; otherwise the checker derives a conservative fallback boundary from normalized `scope` text. Active `pass` and `fail` receipts for the same canonical `subject_id`, `kind`, and applicability boundary conflict until one explicitly supersedes the other. Different boundaries are not collapsed into a false contradiction. The scope fallback is textual, not semantic understanding.

### Canonical-object receipt

When `requires_canon_object` is true, the artifact must cite a passing `executed-object` receipt whose object path and object hash resolve. Labeling the artifact as `proxy` is an error.

### Negative-result and absence gates

A negative result requires a passing positive control. A negative-existence claim additionally requires an `authoritative-search` receipt that records the authority, procedure, and boundary.

### Handoff continuity

A managed handoff must contain the required semantic sections and metadata arrays named `current_state` and `authority_sources`. Those arrays must resolve to durable files, and `current_state` must include `INDEX.json` or a managed Markdown artifact whose declared state is `canon`.

## JSON report

`--json` emits `bvm-lint-report/0.1` with checker version, pass/fail state, counts, and sorted findings. Store that report with a release when a machine-readable conformance receipt is useful.

## Deliberate limits

The linter does not decide whether evidence supports a claim, whether a reviewer was genuinely independent, whether a primary source is authoritative, whether an execution environment was complete, or whether an operator decision was wise. A clean report means the declared governance structure is internally consistent within the implemented checks.
