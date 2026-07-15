# Enforcement model

A rule is only as strong as the place where violation is stopped.

## Enforcement classes

1. **Mechanical invariant** — deterministic code rejects invalid state.
2. **Separate review surface** — another reviewer examines exact bytes and declared scope.
3. **Primary-source or governed-object check** — the relevant object is directly queried, inspected, measured, or executed.
4. **Writer self-discipline** — the writer remembers the rule.

The first three can fail, but they create evidence and friction outside the original writer. The fourth is useful and insufficient as the sole canon gate.

## Enforcer different from writer

The principle does not require every reviewer to be human. It requires the primary gate not to be only the same generative act that produced the claim. A deterministic linter, separately scoped review, or direct execution can supply that separation.

## Reviewer convergence is not independence

Two reviewers can agree because both received the same partial source window, stale summary, or false premise. Count shared-source reviews as multiple review surfaces but one factual anchor until a primary-source trace or genuinely distinct evidence path exists.

## Machinery before aspiration

A prose rule such as “preserve the old version” is weak until the checker rejects an orphaned archive artifact or missing retraction hash. New core requirements should normally ship with:

- a failing fixture;
- a stable diagnostic code;
- a passing correction fixture;
- documentation of what the check still cannot prove.
