# The challenge: beat the checker

**Construct a vault that violates a specific MUST in [SPEC.md](../../SPEC.md)
while `python -m bvm_lint <vault> --strict` exits 0.**

That is the whole game. Not "make the checker crash", not "find a vault it
dislikes" — make it say **PASS** about a vault that provably breaks a rule
the spec states as MUST or MUST NOT.

This is an invitation the project means literally. The checker's value is
exactly the set of violations it cannot miss; every verified catch either
grows that set or forces the spec to state its boundary honestly. Either
outcome makes the method stronger, which is why catches are credited.

## A valid submission has three parts

1. **The clause.** Quote the specific MUST from SPEC.md (section number and
   text) that your vault violates.
2. **The vault.** A minimal reproduction — the smallest tree that shows the
   violation. Fictional content only (invent your own Cedar Lane).
3. **The green run.** The output of `python -m bvm_lint <vault> --strict`
   showing exit status 0 against the current released checker version
   (state the version; `python -m bvm_lint --version`).

Submit through the [attack report issue form](../../.github/ISSUE_TEMPLATE/attack.yml).

## How submissions are judged — four acceptance classes

Every submission gets exactly one of these verdicts, in public:

- **CLASS 1 — Checker gap (a catch).** The MUST is violated, the violation
  is visible in the vault's bytes, and the checker stays green. The best
  outcome: it becomes a new diagnostic (or a fix to an existing one), a
  regression fixture, and a credited row in the
  [Hall of Catches](HALL_OF_CATCHES.md).
- **CLASS 2 — Spec ambiguity (also a catch).** Your vault exposes a MUST
  whose wording is genuinely decidable two ways — the checker enforces one
  honest reading, you demonstrated another. Fix lands in SPEC.md wording;
  credited in the Hall.
- **CLASS 3 — Outside the checker's surface.** The violation is real but
  lives outside vault bytes (an off-vault side channel, a human lying in
  prose, a governed object swapped outside the vault). Not a checker bug —
  the checker only ever sees bytes in the vault — but if the boundary was
  not already stated plainly, we document it. Instructive submissions are
  credited as boundary catches.
- **CLASS 4 — No violation shown.** The vault is green because it is
  actually conformant, or the quoted clause is not a MUST, or the
  reproduction does not demonstrate the claim. Not credited, but if the
  attempt reveals a common misreading, it may still earn a Hall note as a
  near-miss worth learning from.

Rulings quote the clause, show the run, and land within a reasonable time.
If you disagree with a ruling, say so on the issue — rulings are records,
not verdicts from on high, and they have been wrong before.

## Ground rules

- One violation per submission; minimal reproductions rule.
- Attack the *method surface*: vault bytes, receipts, hashes, timestamps,
  the checker's parsing of them. Bugs in Python itself or the filesystem
  are out of scope.
- Fictional values only. No real names, projects, hosts, or credentials.
- The checker and SPEC.md as released are the target. Patching the checker
  and then beating your patch is a different (also fun) game that earns no
  Hall credit.
