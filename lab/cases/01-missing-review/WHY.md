# Why this vault fails — and why the repair looks the way it does

## The failure

The Cedar Lane shelf count was promoted to CANON, and there *is* a review
receipt on file. But its `reviewer_class` is `writer-self-check`: the person
who wrote the claim also signed off on it. The method does not count a
self-check as a review, so the canon artifact has **zero qualifying
reviews** and `bvm-lint` reports `BVM031`.

This is the quietest way a review gate rots: the paperwork exists, the
folder looks complete, and only the *class* of the reviewer is wrong.

## The repair

The fixed vault changes the review's `reviewer_class` to
`separate-instance` — the record of an actual second set of eyes. Notice
what else had to move:

- the promotion receipt's `reviews_sha256` entry, because the review file's
  bytes changed, and
- `INDEX.json`'s `promotion_sha256`, because the promotion receipt's bytes
  changed.

That ripple is the method working as designed: every layer is bound to the
exact bytes of the layer below it, so you cannot change one record quietly.

## What passing does NOT prove

A green run proves the review chain is structurally sound. It does not
prove the reviewer was diligent, or that 48 packets is the true count.
Structural conformance is the floor, not the claim (SPEC.md section 22).
