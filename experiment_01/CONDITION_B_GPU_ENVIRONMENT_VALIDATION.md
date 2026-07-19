# Condition B GPU environment-validation report

Date: 2026-07-19  
Scope: environment validation only; no ten-update validation or training authorized.

## Result

The complete zero-update GPU environment gate **passed** on RunPod pod
`8mlpfc4fv503q1` using the frozen immutable image
`ghcr.io/maryadelua/yoruba-speech-tools-condition-b@sha256:9b3abd67c288a422598da70827c3a2e8d4ddc565659725830c175dd44cebe321`.
The runtime was Python 3.10.13, PyTorch 2.1.2, CUDA 12.1, and cuDNN 8902 on an
NVIDIA L4. The pod was stopped after validation and returned to `$0.00/hr`.

## Checks completed

- NVIDIA L4 detected with 22.03 GiB GPU memory; the 12 GiB requirement passed.
- Frozen recipe and dataset hashes matched the approval record.
- Train/development/test counts remained 23/3/3 and protected test IDs were unchanged.
- Pinned VITS commit `2e561ba58618d021b5b8323d3765880f7e0ecfdb` matched.
- Pinned fairseq commit `3d262bb25690e4eb2e7d3c1309b1e9c406ca4b99` matched.
- Full MMS Yoruba archive downloaded at 919,869,645 bytes; archive and component hashes were recorded.
- `G_100000.pth` and `D_100000.pth` both loaded on the L4.
- The approved bundle hash matched `b0e2072cf4474c7b85e0ef6fa54a8c52effc914289ae21b6d11032ac5136b699`.
- The bundle contained exactly 26 train/development WAV files and no protected-test audio.
- No optimizer was created; updates, forward passes, dataset reads, and protected-test accesses were all zero.
- The frozen split remained 23 train, 3 development, and 3 protected-test records.
- The GPU pod was stopped after validation and showed `$0.00/hr` compute cost.

## Build issue discovered and repaired

The pinned VITS `monotonic_align/setup.py` names its native extension `monotonic_align.core`, while the repository does not initially contain that nested package directory. A direct `build_ext --inplace` therefore fails or places the extension where the outer package cannot import it. The project Dockerfile now creates the expected nested package directory, builds the extension in place, and verifies its import during image construction.

## Gate status

The environment-validation blocker is resolved. The zero-update preflight does not authorize the
ten-update technical validation or full Condition B training. Those actions remain behind their
separate approval gates.
