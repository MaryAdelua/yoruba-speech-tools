# Condition B GPU environment-validation report

Date: 2026-07-19  
Scope: environment validation only; no ten-update validation or training authorized.

## Result

The checkpoint and GPU portions passed, but the complete environment gate remains **closed**. RunPod launched its current PyTorch template (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`) rather than the frozen Condition B container. The runtime was therefore Python 3.12.3, PyTorch 2.8.0+cu128, and CUDA 12.8, and no immutable digest for the frozen image was available. The fail-closed preflight correctly returned exit code 2 for `container_digest_recorded=false`.

## Checks completed

- NVIDIA L4 detected with 22.04 GiB GPU memory; the 12 GiB requirement passed.
- Frozen recipe and dataset hashes matched the approval record.
- Train/development/test counts remained 23/3/3 and protected test IDs were unchanged.
- Pinned VITS commit `2e561ba58618d021b5b8323d3765880f7e0ecfdb` matched.
- Pinned fairseq commit `3d262bb25690e4eb2e7d3c1309b1e9c406ca4b99` matched.
- Full MMS Yoruba archive downloaded at 919,869,645 bytes; archive and component hashes were recorded.
- `G_100000.pth` and `D_100000.pth` both loaded on the L4.
- No optimizer was created; updates, forward passes, dataset reads, and protected-test accesses were all zero.
- The GPU pod was stopped after validation and showed `$0.00/hr` compute cost.

## Build issue discovered and repaired

The pinned VITS `monotonic_align/setup.py` names its native extension `monotonic_align.core`, while the repository does not initially contain that nested package directory. A direct `build_ext --inplace` therefore fails or places the extension where the outer package cannot import it. The project Dockerfile now creates the expected nested package directory, builds the extension in place, and verifies its import during image construction.

## Remaining blocker

Build the corrected project Dockerfile as an immutable image in an environment that permits Docker builds (or CI), push it to a registry, deploy that exact digest on RunPod, and rerun the no-update preflight with `CONTAINER_IMAGE_DIGEST=sha256:...`. Only after that passes should separate approval be requested for the ten-update validation. Full Condition B training remains unauthorized.
