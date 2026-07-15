# Tutorial vault

This fictional project demonstrates a complete BVM correction cycle without relying on private material.

## Story

1. `ARCHIVE/adapter-parity-observation-v0.1.0.md` recorded a negative result: no adapter divergence was found in a two-case corpus.
2. A positive control showed that the harness could detect one injected byte mismatch. That was necessary, but the corpus still omitted malformed duplicate-key inputs.
3. The v2 probe added two duplicate-key cases, ran the canonical reference object, and emitted per-unit evidence.
4. `CANON/bounded-adapter-parity-v1.0.0.md` was reviewed by exact hash, frozen as an exact candidate snapshot, and promoted with evidence and an index update.
5. The original overbroad observation was then retracted without deleting it. The retraction binds both the old artifact and its promoted replacement by SHA-256.

## Run it

From the repository root:

```bash
python examples/tutorial-vault/WORKING/tools/run_probe.py --check
python examples/tutorial-vault/WORKING/tools/run_positive_control.py --check
PYTHONPATH=src python -m bvm_lint examples/tutorial-vault --strict
```

## What this example teaches

- A positive control is necessary for a negative result but does not prove corpus completeness.
- Aggregate claims enumerate units and bind each unit to a passing receipt.
- The old artifact remains readable after retraction.
- The canon claim is narrower than “these implementations are equivalent.”
- Editing the canon artifact, candidate snapshot, review binding, corpus input, reference object, or candidate object makes lint fail.
- A handoff points to durable state rather than relying on agent memory.
