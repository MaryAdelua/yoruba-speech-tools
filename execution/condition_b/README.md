# Condition B execution bundle

This bundle prepares—but does not automatically run—the frozen Condition B experiment.

## Recommended RunPod setup

1. Wait for explicit environment and private-data transfer approval.
2. Create one Linux Pod with an RTX A5000 24 GB. If unavailable, use L4 24 GB; never use less than
   the frozen 12 GB minimum.
3. Allocate at least 30 GB container disk and use private temporary storage.
4. Build `execution/condition_b/Dockerfile`, then record the resolved immutable image digest.
5. Transfer the repository and private audio only through the provider's authenticated private path.
6. Run `python scripts/run_condition_b_training.py --validate-only`, followed by
   `python execution/condition_b/preflight_environment.py`. Neither command trains.
7. Record the preflight JSON, source revisions, image digest, package inventory, archive/checkpoint
   hashes, GPU information, and `nvidia-smi` output.
8. Only after the separate execution approval is present, run the ten-update GPU technical check that
   counts within the frozen 300-update budget.
9. Download and verify outputs locally, then destroy temporary remote storage as approved.

## Safety properties

- The Docker default command runs only the no-update environment preflight.
- The frozen recipe remains `training_authorized=false` and is never edited by the runner.
- `--train` requires a separate approval record bound to exact recipe and dataset hashes.
- `--technical-validation` requires the distinct ten-update approval, hard-limits the run to exactly
  10 optimizer updates, and cannot authorize full training or protected-test evaluation.
- The runner checks test isolation, source commits, archive size, checkpoint presence, image digest,
  CUDA, and VRAM before creating the production backend.
- The full MMS training archive is not downloaded during local preparation.

The production runner is `scripts/run_condition_b_training.py`. The implementation-audit blockers
and ten-update validation gate were resolved. Full Condition B has a separate approval record at
`execution/condition_b/full_training_approval.json`, but the project was paused before full training
started. See `PAUSE_HANDOFF.md`. Condition C remains unapproved and must not be started.
