Project: Yoruba speech synthesis — frozen Condition B full training (300 optimizer updates, not Condition C).
Authorization: Mary Adelua approved resumption 2026-07-20 in condition_b_continuation_approval.json, superseding the 2026-07-19 pause. The original full_training_approval.json (same date, same signer, same recipe/dataset hashes) is the script-level approval file.
Safety guarantees built into the code:
- Docker CMD defaults to read-only preflight — training requires explicit --train flag
- validate_approval() enforces hash-bound approval + scope check before any optimizer step
- 6 independent layers exclude protected test IDs YT0028/YT0029/YT0030 from training data — they never enter a DataLoader
- Recipe is frozen (training_authorized: false), GPU-only, single-GPU, no augmentation, no auxiliary losses
- Hard cap at 300 updates, early stopping, deterministic seeds, no network egress
- Condition C is explicitly unapproved in every record — this run does not touch it
Pod config:
- Image: ghcr.io/maryadelua/yoruba-speech-tools-condition-b:dc492eba18ee3223d1f796a080fe13fe422b9a1c
- Digest: sha256:1e99ed087aa8f913405b78cb15e96ed09cd0e0105c2f131b7db986ba8a9031fe
- GPU: 1x L4 24GB (fallback A5000 > L4 > A10 > T4, min 12GB)
- Cloud: Secure Cloud, disk ≥30GB, persistent volume ~30-40GB at /workspace
- Env: CONTAINER_IMAGE_DIGEST=sha256:1e99ed087aa8f913405b78cb15e96ed09cd0e0105c2f131b7db986ba8a9031fe
- SSH: enabled, Jupyter: not needed
- Pod name: condition-b-full-training
- Est cost: ~$0.27-0.81/hr GPU, total ~$2-3
Command inside pod: python scripts/run_condition_b_training.py --train --approval execution/condition_b/full_training_approval.json
This is a governed, auditable research run — not exploratory or experimental. All hyperparameters, data splits, and hashes were frozen before the pause and verified unchanged at resume.