# Roadmap

The roadmap records candidates, not commitments.

## Candidate v0.2 work

- Add a first-class reconciliation record for contradictory applicable receipts.
- Add parity tests between JSON Schemas and every equivalent Python validation path.
- Add optional signed-receipt profiles without treating signatures as truth.
- Add a safe migration command for metadata and receipt-version changes.
- Add fixtures for multi-repository, data-pipeline, and long-running agent workflows.
- Add a machine-readable conformance manifest that records checker version and profile.
- Test adoption outside the originating environment and publish both friction and failure reports.
  The Vault Lab (`lab/`) is the first instrument for this: guided break/repair cases, judgment scenarios, a beat-the-checker challenge, and a field-report template.
- Evaluate whether semantic trigger declarations can be reviewed mechanically without pretending the checker understands claims.

## Conditions before using “standard”

The project should not adopt standards language until there is evidence of independent use, external conformance review, stable version governance, and meaningful operation outside the originating environment.
