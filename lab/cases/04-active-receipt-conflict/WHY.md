# Why this vault fails — and why the repair looks the way it does

## The failure

The first shelf count **failed** — four packets were sitting on the potting
bench, so the cabinet did not match the checkout ledger. After re-shelving,
the recount **passed**. Both receipts are on file, same subject, same kind
(`count-check`), same applicability window (`shelf-count.2026-07`).

The broken vault keeps both receipts *active*: neither says anything about
the other. To a future reader — or a future AI session — the vault now
contains a pass and a fail for the same question, with no machine-readable
statement of which one is operative. That is `BVM024`.

Note what the method does **not** ask you to do: delete the failed count.
The fail is real history and it stays.

## The repair

The passing recount gains one field: `supersedes_receipt`, pointing at the
failed first count. The checker verifies the supersession is legitimate —
same subject, same kind, same applicability, and a strictly later
`captured_utc` — and the old receipt becomes inactive history instead of a
live contradiction.

The ripple: the recount receipt's bytes changed, so the promotion's
`evidence_sha256` entry updates, and the promotion's bytes changed, so
`INDEX.json`'s `promotion_sha256` updates.

## What passing does NOT prove

Supersession proves the vault says, explicitly, which measurement is
operative and why the other one is retired. It does not prove the recount
was careful — only that nobody has to guess which count the project
stands on.
