# Threat model

BVM is designed primarily against accidental and incentive-shaped state corruption in human–AI collaboration.

## In-scope failure classes

- hallucinated or gap-filled project state;
- stale approvals applied to changed bytes;
- source-window truncation;
- proxy substitution;
- untested aggregate units;
- uncalibrated negative results;
- unsupported negative-existence claims;
- contradictory active receipts;
- silent historical rewriting;
- unindexed or duplicate current canon;
- mutation scope exceeding operator intent.

## Partially addressed

- careless reviewers;
- several agents sharing one false premise;
- accidental source tampering;
- ambiguous chronology;
- incomplete handoffs.

The method adds evidence and stop points but cannot eliminate these risks.

## Out of scope for v0.1

- malicious collusion among writers, reviewers, and receipt producers;
- compromised operating systems or filesystems;
- cryptographic signer identity;
- remote-source authenticity;
- secret scanning;
- malware execution containment;
- semantic truth evaluation;
- regulatory certification.

A hostile actor can manufacture internally consistent files. BVM makes state transitions inspectable; it is not a complete trust infrastructure.
