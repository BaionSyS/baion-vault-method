# Recommended practices

These practices are useful but are not all required for v0.1 structural conformance.

- Use UTC timestamps in filenames when ordering matters.
- Prefer one durable artifact per bounded claim or decision.
- Record `Known`, `Unknown`, and `Required before promotion` sections.
- Run three review passes for handoffs and thread closeout.
- Keep raw execution output immutable after a receipt hashes it.
- Record the checker version in release or handoff receipts.
- Use dry-run and explicit-scope modes for aggregating tools.
- Pin third-party CI actions to immutable commit SHAs.
- Review the actual staged-file list before commit.
- Preserve null and failed results when they constrain the next decision.
- Keep a compact index of current lineages rather than treating modification time as authority.

An organization may adopt these as local requirements. Doing so should add enforcement rather than merely stronger prose.
