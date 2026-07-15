# Project governance

## Status

BVM v0.1 is maintained as a reference methodology. The project does not yet claim standards-body status, universal applicability, or independent certification authority.

## Decision rule

Changes are evaluated in this order:

1. Does the change address a demonstrated failure mode or adoption need?
2. Is the requirement core, recommended, or organization-specific?
3. Can the requirement be enforced mechanically?
4. Does the checker reject a fixture that should fail?
5. Does the change preserve correction history and avoid retroactive rewriting?
6. Is the public claim no broader than the shipped evidence?

## Versioning

- Patch releases clarify prose or fix checker defects without intentionally changing the conformance contract.
- Minor releases add backward-compatible receipt types, checks, or recommended profiles.
- Major releases may change required structure or conformance semantics.

A checker behavior change that turns a previously passing vault into a failing vault must be called out in the changelog even if the change is classified as a bug fix.

## Method changes

A new core rule should normally be accompanied by:

- a field report or minimal reproducer;
- a named enforcement site;
- a fixture that fails before the change;
- a migration path;
- an explicit statement of what the rule still cannot prove.

## Maintainer authority

Maintainers decide what enters this repository. A maintainer decision establishes repository governance state; it does not establish external factual truth.
