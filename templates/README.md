# Templates

Copy these files into a vault and replace every placeholder. Templates are intentionally not lintable as-is: sample identifiers, timestamps, paths, and hashes must be replaced with real values.

Before promotion:

1. freeze the final artifact bytes under `RECEIPTS/candidates/`;
2. review that exact artifact path and SHA-256;
3. make the promotion receipt match the artifact's complete evidence and review path sets;
4. populate `evidence_sha256` and `reviews_sha256` for every cited receipt file;
5. update `INDEX.json` with the promotion path and `promotion_sha256`.

Changing any bound input requires rebuilding the dependent hashes and repeating the applicable review and promotion steps.

Specialized receipt starters are included for positive controls, canonical-object execution, and authoritative searches. Use the generic evidence template only when the specialized fields do not apply.
