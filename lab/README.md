# Vault Lab — break the method, on purpose

The rest of this repository tells you what the BAION Vault Method is. The
lab exists so you can watch it **fail** — five specific ways — and watch
each failure get caught by the same checker that guards real vaults.

```sh
lab/start.sh          # guided run (15–25 minutes, interactive)
lab/start.sh --check  # non-interactive fixture verification (what CI runs)
```

Requirements: POSIX shell and Python 3.11+. Standard library only, no
install, no network, nothing written outside `lab/output/`.

## What the guided run does

For each of five cases you get the same arc:

1. **The rule on trial** — one MUST from [SPEC.md](../SPEC.md).
2. **Predict** — you guess what the checker will say before it runs.
3. **Break** — the real `bvm-lint` runs against a small broken vault.
4. **Why** — what actually rotted, and why the diagnostic is the right one.
5. **The repair** — the exact byte diff between the broken and fixed vault.
6. **Prove it** — the checker runs green on the repaired vault, followed by
   a reminder of what green does *not* prove.

Every fixture is the fictional **Cedar Lane community garden seed
inventory** — small enough to read in full, real enough to rot in the same
ways real project state rots.

## The five cases

| Case | What rots | Primary diagnostic |
|---|---|---|
| [01-missing-review](cases/01-missing-review/WHY.md) | canon reviewed only by its own writer | `BVM031` |
| [02-missing-reference](cases/02-missing-reference/WHY.md) | citation to a receipt that does not exist | `BVM016` |
| [03-candidate-byte-mismatch](cases/03-candidate-byte-mismatch/WHY.md) | frozen snapshot edited after promotion | `BVM033` |
| [04-active-receipt-conflict](cases/04-active-receipt-conflict/WHY.md) | pass and fail receipts, no supersession | `BVM024` |
| [05-review-byte-mismatch](cases/05-review-byte-mismatch/WHY.md) | silent edit voids review, freeze, promotion | `BVM037` |

Each case directory holds `broken-vault/`, `fixed-vault/`, `WHY.md`, and a
machine-readable `EXPECTED.json`. The two vaults differ only in the files
the repair requires — diff them yourself.

Both modes are fail-closed and anti-rigging: every broken vault must
produce **exactly** the diagnostics its `EXPECTED.json` declares (an
unexpected extra finding fails the run), and every fixed vault must pass
`--strict` with zero findings. The guided run asserts all five case pairs
through the same path `--check` uses before narrating anything, and exits
nonzero on any expectation drift — the on-screen verdicts are computed
from the live checker output, never scripted.

## After the cases

- **Judgment scenarios** (`lab/scenarios/`) — four situations the checker
  cannot decide for you: shared-source convergence, edit-vs-supersede,
  proxy-vs-governed-object, and green-checker-vs-true-claim.
- **The challenge** ([challenge/README.md](challenge/README.md)) — violate
  a specific MUST in SPEC.md while `bvm-lint --strict` stays green.
  Verified catches are credited in the
  [Hall of Catches](challenge/HALL_OF_CATCHES.md).
- **Field report** ([FIELD_REPORT.md](FIELD_REPORT.md)) — five minutes to
  tell us what you predicted, what surprised you, and what was confusing.

## The contract this lab is built to

The lab is governed by a sealed build specification:
`BAION_VAULT_LAB_V1_REFINED_BUILD_SPEC` v0.3.0, 2026-07-16, SHA-256
`2afb782d8607e8db0c795b0b57fe0a42ad8182c266a58124efba0362aee7c143`
(a vault record; the vault is not public, the hash is the fixed point).
The two required verbatim statements from that contract are what you see
in every run:

The opening boundary, before any case:

> This lab contains fictional records. No AI model is running. The checker
> tests structural conformance; it does not determine whether a claim is
> true.

The final bounded claim, emitted exactly once and only when every
expectation held:

> PASS means the checker found no declared structural violation in these
> fixtures. It does not prove the seed inventory claim is true, complete,
> safe, or decision-grade.

A failed run must never emit that sentence. No badge, certification, or
score exists here.

## Regenerating fixtures (maintainers)

`lab/tools/build_fixtures.py` rebuilds every case deterministically; all
hashes are computed from the bytes written, never typed in. If you change
a fixture, regenerate and rerun `lab/start.sh --check`.
