# Contributing

BVM is designed around a simple principle: a rule that matters should have an enforcement site.

## A strong proposal contains

1. A concrete failure mode or adoption need.
2. The bounded claim the change is intended to protect.
3. The enforcement class: mechanical, separate review, primary-source execution, or writer self-discipline.
4. A failing fixture or reproducible example.
5. A checker, test, or explicit reason mechanical enforcement is not feasible.
6. The expected effect on existing conforming vaults.
7. An explicit statement of what the new gate still cannot prove.

Proposals that add ceremony without a named failure mode or enforcement site will usually be declined.

## Change categories

- **Core change:** modifies `SPEC.md` or conformance behavior. Requires tests, migration notes, and a version decision.
- **Checker change:** fixes or adds a mechanical invariant. Requires a failing test first when practical.
- **Recommended practice:** adds non-normative operational guidance.
- **Field report:** documents an anonymized real catch with claim → gate → catch → correction.
- **BAION-specific example:** illustrates an originating practice without making it universal.

## Pull-request checklist

- [ ] The change is fresh public authorship and respects `PUBLICATION_BOUNDARY.md`.
- [ ] Normative and non-normative language are separated.
- [ ] New issue codes are documented in both code and `schemas/diagnostics.json`.
- [ ] Tests cover failure and success paths.
- [ ] Exact-byte fixtures and dependent hashes were regenerated after edits.
- [ ] `./verify_repo.sh` passes.
- [ ] No factual-validation claim is inferred from structural linting.
- [ ] I have the right to submit the contribution under the repository MIT License.

## Licensing of contributions

By submitting a contribution, you agree that it may be distributed under the repository's [MIT License](LICENSE), and you confirm that you have the right to submit it on those terms. Do not contribute private vault material, third-party confidential material, or content whose provenance you cannot establish.

## Commit discipline

Keep specification, fixtures, checker behavior, and tests in the same reviewable change when they form one invariant. Avoid broad staging commands that can sweep unrelated files into a governance change. Inspect the actual changed-file list before commit.
