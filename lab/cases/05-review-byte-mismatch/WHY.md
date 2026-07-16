# Why this vault fails — and why the repair looks the way it does

## The failure

The promoted shelf count spelled a species name "tomatoe". Someone fixed
the typo directly in the CANON file — no timestamp bump, no new review,
nothing else touched. The most innocent edit imaginable.

Three diagnostics fire, and this case declares all three up front, because
they are one event seen from three angles:

- `BVM037` — the review receipt records the hash of the *old* bytes; the
  review is no longer bound to what CANON actually says.
- `BVM031` — with that review voided, the canon artifact has zero
  qualifying reviews.
- `BVM033` — the promotion receipt and frozen candidate still bind the old
  bytes, so the promotion no longer vouches for the file in CANON.

This is the method's central bargain: **canon bytes are review-bound**.
There is no such thing as an edit too small to void the chain — because if
"small" edits were exempt, "small" would become the attack surface.

## The repair

The fixed vault does the same edit honestly:

- `updated_utc` is bumped to the edit time,
- a second review (`independent-review-v2.json`) binds the *new* bytes,
- a fresh candidate freeze and promotion (`promote-v2.json`) bind the new
  bytes, and the index re-binds to the new promotion,
- **the original review and promotion stay on disk as history** — the
  repair adds records, it does not rewrite the old ones.

Compare the broken and fixed trees: the silent edit touched one file; the
honest edit touched five. That cost difference is intentional. It is what
makes silence detectable.

## What passing does NOT prove

The re-review proves a second party saw the current bytes. It does not
prove the edit was wise, or that a typo fix is where this should have
stopped. Whether a change is really "just a typo" is a human judgment —
scenario 2 in the lab is about exactly that line.
