# Vault Lab field report

A field report is an **operating observation, not independent
certification** — it tells this project whether the method generalizes
beyond its home repository and whether its overhead earns its keep.
**Negative and null results are welcome**; "we tried it for a week and
dropped it because X" is among the most useful reports we can receive.

**Do not include** secrets, private vault content, client names,
unpublished research, personal data, or proprietary files. Describe your
project by type and size, never by confidential identity.

Copy the template into a **Field Report** discussion on the repository
(or an issue if Discussions are unavailable). Answer what you can —
a blank line is honest; a guessed number is not.

```markdown
## Operating evidence

- BVM version/tag or checker commit (`python -m bvm_lint --version`):
- Project type and approximate size (files/records — no confidential identity):
- Trial duration (how long you ran the method):
- Setup time (zero to first passing check):
- Approximate time added per promotion:
- Number and type of catches (what the checker stopped, and which codes):
- False positives or confusing diagnostics:
- Important misses (violations you know it should have caught but did not):
- Rules you bypassed or abandoned (and why):
- Did the method change a decision? (which one, how):
- What should be removed, simplified, or automated:
- Quotation permission: [ may quote with name / may quote anonymously /
  aggregate statistics only / do not quote ]

## Experience notes (optional)

- What you build / operate day to day, and what made you try the lab:
- Which lab case or judgment scenario mapped to something you have
  actually seen in a real project (human or AI-assisted)?
- Do you disagree with any "method answer"? Make the case — disagreement
  here is signal, not noise.
- Where did the lab confuse you, stall, or say something wrong?
  (OS / Python version if anything misbehaved):
```

Reminders that govern every report:

- Negative and null results are welcome.
- No secrets, private vault content, client names, unpublished research,
  personal data, or proprietary files.
- A field report is an operating observation, not independent
  certification.

## Where to send it

- Preferred: a **Field Report** discussion on the repository.
- Challenge attempts (you think you broke the method) go through the
  [attack report issue form](../.github/ISSUE_TEMPLATE/attack.yml) instead —
  see [challenge/README.md](challenge/README.md) for the rules.
