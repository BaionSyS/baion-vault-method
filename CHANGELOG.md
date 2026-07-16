# Changelog

All notable public changes are documented here.

## [0.2.0] — released 2026-07-16

### Added

- **Vault Lab v1** (`lab/`) — a local, deterministic teaching and falsification
  environment: five guided break/repair cases against the real checker
  (missing review, missing reference, candidate byte mismatch, active receipt
  conflict, review byte mismatch), four human-judgment scenarios, and a
  checker-escape challenge with a public four-class ruling model and Hall of
  Catches. Entry point: `./lab/start.sh`. Governing specification:
  `BAION_VAULT_LAB_V1_REFINED_BUILD_SPEC` v0.3.0, 2026-07-16, SHA-256
  `2afb782d8607e8db0c795b0b57fe0a42ad8182c266a58124efba0362aee7c143`
  (operator-sealed vault record; quoted contract sections are reproduced in
  `lab/README.md`).
- Fail-closed guided runner: guided mode and `--check` share one assertion
  path; any expectation drift (wrong diagnostic codes, findings on a fixed
  vault, substituted checker) exits nonzero and suppresses the final bounded
  claim. Adversarial regression tests cover the zero-findings-checker and
  unexpected-code cases.
- Lab fixture evidence contracts and field-report template aligned to the
  live Discussions category.

### Changed

- **Version model: release version and method version are now distinct.**
  The release version (this changelog, the badge, `pyproject.toml`,
  `bvm-lint --version`, `CITATION.cff`) names what ships from the repository.
  The method version (`SPEC.md`, `templates/vault.toml`,
  `examples/tutorial-vault/vault.toml`) names the specification contract and
  remains **0.1.0** — the method is unchanged in this release; `SPEC.md`,
  `src/`, and `schemas/` are byte-identical to v0.1.0 except for the SPEC.md
  status line. `scripts/check_version_parity.py` now enforces the two tracks
  separately and pins the method to the `0.1.x` series the checker accepts
  (BVM002 contract). The previous single-string parity made a correct v0.2.0
  release impossible: bumping `method_version` past `0.1.x` causes `bvm-lint`
  to reject the repository's own templates.
- `SPEC.md` status line no longer reads "release candidate"; the method
  version it declares is unchanged.

### Boundaries

- The lab is local and deterministic; it runs no AI model, uses no network,
  and makes no certification claim. PASS means the checker found no declared
  structural violation in fictional fixtures — not that any claim is true.
- Structural conformance only; no factual, scientific, legal, security, or
  safety certification (unchanged from v0.1.0).

## [0.1.0] — released 2026-07-15

### Added

- Core human–AI state-governance specification.
- Zero-dependency `bvm-lint` reference checker.
- Strict JSON metadata with duplicate-member and nonstandard-constant rejection.
- Full Semantic Versioning syntax and precedence checks for supersession.
- Hash-bound evidence sources, governed objects, reviews, candidates, promoted artifacts, retractions, and replacements.
- Promotion-time SHA-256 binding for every evidence and review receipt, plus index-to-promotion binding.
- Applicability-scoped receipt supersession and active-conflict detection.
- Canon gates for negative results, negative-existence claims, aggregate units, and governed-object-dependent claims.
- Archive reachability, preserved correction history, and durable handoff-authority checks.
- Runnable fictional tutorial vault with a complete correction lifecycle.
- Four anonymized field reports covering a partial-source correction, a budget-bound null mislabeled as a wall, a differential-attribution catch, and a skipped authoritative search.
- Tests, commit-pinned CI actions, link validation, diagnostic parity, version parity, release-surface validation, and public-boundary scans.
- One MIT license across the public methodology, checker, examples, schemas, and templates.

### Boundaries

- Structural conformance only; no factual, scientific, legal, security, or safety certification.
- Reference methodology status; not a standard.
- Released with public tag v0.1.0 as the release record.
