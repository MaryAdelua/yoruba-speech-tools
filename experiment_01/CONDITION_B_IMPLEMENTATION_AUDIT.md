# Condition B implementation audit

**Audit result: RUNNER IMPLEMENTED; GPU EXECUTION REMAINS UNAUTHORIZED**

The repository now contains an approval-gated Condition B training runner around the original
MMS/VITS generator, discriminator, and loss functions. It does not use the Transformers inference
wrapper and does not add tone, syllable, phoneme, or surface-prosody objectives.

## Implemented safeguards

- verifies the frozen recipe and exact dataset SHA-256;
- enforces the 23/3/3 split and protects YT0028–YT0030 from preprocessing, loaders, optimization,
  checkpoint selection, and early stopping;
- requires a separate approval record whose recipe and dataset hashes match;
- validates pinned VITS/fairseq commits, archive byte count, model files, CUDA, 12 GB VRAM, and the
  immutable container digest;
- derives 16 kHz audio with the frozen Hann-sinc settings without altering sources or manifests;
- loads the original generator/discriminator and both full checkpoints, then creates fresh optimizers;
- uses only the frozen original VITS losses, accumulation, FP16, finite-value aborts, and norm cap;
- runs deterministic development selection every 25 updates, early stopping, atomic best/last saves,
  best restoration, and the overfitting-gap warning;
- records source-tree, container, package, GPU, archive, checkpoint, dataset, and recipe provenance.

## Local validation evidence

The synthetic CPU orchestration dry run completed 150 optimizer updates, used four micro-batches per
update, selected update 50, stopped through the frozen rule, restored the selected checkpoint, and saw
zero protected-test items. It explicitly loaded neither Condition B weights nor Condition B audio.
Evidence: `artifacts/experiment_01/condition_b/local_runner_smoke/training_summary.json`.

Both runner files pass Python bytecode compilation and the working-tree whitespace check. The current
bundled Windows interpreter does not include PyTorch, so the smoke run could not be repeated after the
final deterministic-evaluation hardening. This is an environment limitation, not authorization to
install dependencies or train locally.

## Remaining blockers before GPU training

1. Approve transfer of the private participant audio to the selected external GPU provider.
2. Create the separate approval JSON bound to the frozen recipe and dataset hashes.
3. Build the Linux container, record its digest, and compile the VITS monotonic-alignment extension.
4. Acquire and hash the full MMS Yoruba archive; verify both checkpoint loads.
5. Pass the no-update preflight on one NVIDIA GPU with at least 12 GB VRAM.
6. Run an approved ten-update technical validation, counted within the 300-update budget, to confirm
   deterministic CUDA support, peak memory, finite numerics, and runtime.

No real Condition B optimizer update has occurred. The protected test set, dataset, evaluation
criteria, split, and frozen recipe have not changed.
