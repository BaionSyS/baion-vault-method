# Publishing v0.1.0

This file is an operator checklist for the first public release. The important boundary is simple: publish this freshly authored repository, not a copy or redaction of a private operating vault.

## Suggested GitHub settings

- **Repository name:** `baion-vault-method`
- **Description:** `A file-based governance layer for human–AI work where agents may propose state, but receipts establish it.`
- **Visibility:** Public
- **Topics:** `ai-agents`, `governance`, `provenance`, `audit-trail`, `research-workflow`, `reproducibility`
- **Default branch:** `main`

Do not describe v0.1.0 as an AI-safety certification, a universal standard, or proof that the field reports generalize. The defensible claim is that this repository ships a reference methodology and a bounded structural checker.

## Pre-publication gate

From the repository root:

```bash
./verify_repo.sh
```

Read the final changed-file list before committing:

```bash
git status --short
git diff --check
git diff --stat
```

The expected verification footer is:

```text
REPOSITORY VERIFY PASS
```

## License gate

The staged release uses one MIT license across the complete public repository. That is broad permission: it favors reuse, modification, redistribution, and forkability over control of derivative methodology text. Before public push, the operator should explicitly confirm that this tradeoff is intended, then verify that `LICENSE`, the README badge, `NOTICE.md`, `CONTRIBUTING.md`, and the changelog all state the same boundary. Any inconsistent license statement is a release failure.

## First push

Create an empty GitHub repository without auto-generating a README, license, or `.gitignore`, then run:

```bash
git init
git add .
git commit -m "release: BAION Vault Method v0.1.0"
git branch -M main
git remote add origin https://github.com/BaionSyS/baion-vault-method.git
git push -u origin main
```

Before the push, confirm that `git status --short` contains only files from this public repository. A broad staging command is acceptable only after that inspection.

## Tag the release

After the `main` workflow passes:

```bash
git tag -a v0.1.0 -m "BAION Vault Method v0.1.0"
git push origin v0.1.0
```

Suggested release title:

```text
BAION Vault Method v0.1.0 — Public Reference Release
```

Suggested release body:

```markdown
BAION Vault Method is a file-based governance layer for human–AI work where agents may propose project state, but durable receipts and explicit promotion establish it.

This first public reference release includes:

- the v0.1 core specification;
- `bvm-lint`, a zero-dependency structural checker;
- strict receipt, review, promotion, supersession, retraction, positive-control, canonical-object, and handoff checks;
- a runnable fictional tutorial vault;
- four anonymized field reports derived from real operating catches;
- schemas, templates, tests, and pinned CI actions;
- one MIT license for the public methodology, checker, examples, schemas, and templates.

Boundary: a passing lint result establishes structural conformance only. It is not factual validation, scientific replication, legal compliance, or AI-safety certification.
```

## Clean-clone verification

After publication, verify what a new reader receives rather than relying on the staging directory:

```bash
cd ..
git clone https://github.com/BaionSyS/baion-vault-method.git baion-vault-method-clean
cd baion-vault-method-clean
python -m pip install -e .
./verify_repo.sh
```

That clean-clone run is the public release receipt. A local staging pass is necessary, but it is not a substitute for verifying the object that actually reached GitHub.

## Suggested launch sentence

> I’m publishing the BAION Vault Method: a file-based governance layer for working with AI agents that are allowed to propose state, but not invent it. The repository includes the method, a runnable reference vault, real anonymized catch-stories, and a checker that turns key rules into failing tests.
