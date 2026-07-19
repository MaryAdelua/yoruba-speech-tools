# Project pause handoff

Paused on 2026-07-19 at Mary Adelua's request. Do not start Condition B training or Condition C without a new continuation decision from Mary.

## Current state

- The Yoruba dataset, verified alignments, portable release materials, architecture-independent integration toolkit, and frozen Experiment 1 protocol are complete in the repository.
- Condition A baseline generation and human ratings are complete.
- The Condition B implementation, immutable container, MMS/VITS checkpoint validation, zero-update GPU preflight, and approved 10-update technical validation are complete.
- The 10-update outputs showed no perceived regression and small perceived improvements on YT0028, YT0029, and YT0030. This is validation evidence only, not the full Condition B result.
- The frozen full Condition B feasibility run is approved for at most 300 optimizer updates in `execution/condition_b/full_training_approval.json`, but **has not started**.
- Condition C **has not started** and is explicitly unapproved in the Condition B approval record.

## Safety confirmations

- YT0028, YT0029, and YT0030 are the protected test IDs.
- The RunPod training bundle contains 26 train/development WAV files and excludes protected-test audio.
- Production preprocessing and data loaders exclude the protected test split by construction.
- Existing production records report `protected_test_items_seen: 0`.
- No full Condition B training output directory or full-run checkpoint exists.
- `artifacts/experiment_01/condition_b/local_runner_smoke/training_summary.json` is a synthetic CPU orchestration test, not MMS training and not private-audio training.
- The only real optimizer run completed so far is the separately approved 10-update technical validation. It reported `protected_test_items_seen: 0`.

## Frozen settings that must not change

- Recipe: `experiment_01/condition_b_recipe.json`
- Recipe SHA-256: `09c5d642bd87e8c345d03e08ef362145ca507494314ebdf2126b589519ce3cbf`
- Dataset: `dataset/verified/training_batch_01_verified_alignments.jsonl`
- Dataset SHA-256: `4fbb4b3f977b9733245cbc4c2013245a92a0ade284001fc6d9e30f208a228946`
- Split: 23 train, 3 development, protected test YT0028-YT0030
- Maximum optimizer updates: 300
- Minimum updates before early stopping: 100
- Development evaluation and checkpoint save interval: 25 updates
- Early-stopping patience: 4 evaluations
- Minimum relative development improvement: 0.5%
- Checkpoint selection: lowest mean development reconstruction objective
- Optimizers: AdamW for generator and discriminator
- Learning rate: 1e-5 for both
- Micro-batch size: 2; gradient accumulation: 4; effective batch size: 8
- Seed: 1234; evaluation synthesis seed: 555
- Mixed precision: fp16
- No augmentation, auxiliary losses, prompt changes, split changes, test-set selection, or Condition C activity

## Environment and dependencies

- Container image: `ghcr.io/maryadelua/yoruba-speech-tools-condition-b:dc492eba18ee3223d1f796a080fe13fe422b9a1c`
- Immutable image digest: `sha256:1e99ed087aa8f913405b78cb15e96ed09cd0e0105c2f131b7db986ba8a9031fe`
- PyTorch: 2.1.2
- CUDA runtime: 12.1
- Required GPU memory: at least 12 GB; validated on NVIDIA L4 23,034 MiB
- VITS root: `/opt/vits`
- VITS commit: `2e561ba58618d021b5b8323d3765880f7e0ecfdb`
- Fairseq root: `/opt/fairseq`
- Fairseq/MMS commit: `3d262bb25690e4eb2e7d3c1309b1e9c406ca4b99`
- MMS archive: `/workspace/yor.tar.gz`
- MMS archive SHA-256: `90b9a983f645d0cdd9f4c0321994cfc23faafbc6916865ad75864faef8d57ba8`
- MMS model directory: `/workspace/mms_yoruba/yor`
- Approval: `execution/condition_b/full_training_approval.json`

## Resume entrypoint

The production entrypoint is `python scripts/run_condition_b_training.py --train`. It requires the approval, MMS archive, model directory, VITS root, Fairseq root, output directory, and work directory shown above. The frozen recipe and dataset use their repository defaults.

Because the current managed Codex environment prohibits an agent from initiating or indirectly assembling external processing of private voice recordings, the complete runnable RunPod command is intentionally not reproduced here. An authorized human operator must assemble it from `python scripts/run_condition_b_training.py --help` and the exact paths above. This restriction is the current blocker; it is not a code, model, data, or GPU blocker.

## RunPod pause state

- The current pod uses temporary container storage and has no persistent volume.
- Files restored to the pod will be lost when it is stopped.
- The required code archive, private 26-WAV validation bundle, approval, 10-update outputs, hashes, and metadata are backed up on Mary's computer under the pause-backup path reported in the shutdown checklist.
- The public 920 MB MMS archive and extracted checkpoints do not need to be downloaded from the pod; they can be reproducibly downloaded again and verified by the hashes above.

## Existing validation evidence

- Zero-update preflight: passed.
- Ten-update technical validation: 10 optimizer updates, 33.96 seconds on NVIDIA L4.
- Ten-update checkpoint SHA-256: `4ff7e7e11e076f39cbe0c521c88689b87f0da609891187bdb8957163a1406291`.
- Ten-update checkpoint itself was not downloaded; only its hash, logs, provenance, summaries, and generated comparison WAVs were preserved locally.
- Condition B full training: not started.
- Condition C: not started.

## Files requiring special handling

- Never commit private audio, private bundles, model archives, checkpoints, credentials, SSH keys, tokens, or API keys.
- `work/condition_b_10update_bundle.zip` contains private audio and belongs only in the local persistent backup.
- The MMS archive and extracted model files remain reproducible public dependencies and should not be committed.
- If a future run creates a full checkpoint or logs on temporary RunPod storage, download them before stopping that future pod.
