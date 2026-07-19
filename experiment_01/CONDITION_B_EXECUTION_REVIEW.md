# Condition B reproducibility and execution review

## Recommendation

Use one **RunPod Pod with an RTX A5000 24 GB**, Linux, and at least 30 GB temporary disk. RunPod's
official pricing page listed this GPU at **$0.27/hour** on 2026-07-19. Allow 1–3 billable hours for
environment verification, the frozen 300-update maximum, evaluation, and artifact download: estimated
GPU charge **$0.27–$0.81**, with a **$2 contingency budget** for setup or storage overhead.

This is the lowest-cost practical reproducible option. Kaggle and Colab can cost $0, but neither
guarantees a specific GPU or stable availability; Colab explicitly says GPU types and usage limits
vary. Use RunPod Secure Cloud rather than Community Cloud if the approved data-handling policy requires
provider-controlled infrastructure. Do not upload participant audio until the execution environment
and the outstanding release/data-handling gate are approved.

## Comparison as of 2026-07-19

| Option | Qualifying hardware | Expected cash cost | Reproducibility and practicality | Decision |
|---|---|---:|---|---|
| Local computer | No NVIDIA GPU is exposed here | Not applicable | Cannot execute the frozen CUDA recipe; purchasing hardware for one pilot is not economical | Reject for this run |
| Google Colab | Often T4 or better, but type is not guaranteed | Potentially $0; paid compute-unit cost varies | Easy notebook setup, but dynamic GPU type, limits, disconnects, and runtime images weaken reproducibility | Free fallback only |
| Kaggle | Official tooling lists P100 or T4, both 16 GB | $0 when quota is available | Meets memory requirement, but quota/availability and notebook constraints are not guaranteed | Lowest cash cost, not lowest operational risk |
| RunPod | A5000 24 GB listed at $0.27/hr; L4 24 GB at $0.39/hr | $0.27–$0.81 for 1–3 hours | Exact Linux image, persistent working directory, controllable shutdown, sufficient VRAM | **Recommended** |
| Lambda | RTX 6000 24 GB $0.69/hr; V100 16 GB $0.79/hr | $0.69–$2.37 | Strong VM environment, but materially more expensive for this short pilot | Good alternative |
| Paperspace | A4000 16 GB $0.76/hr | $0.76–$2.28, potentially plus plan/storage | Adequate VM; A4000 access is associated with paid subscription tiers in the pricing table | More expensive |

The cost estimate covers GPU runtime, not taxes, deposits, retained disks, or data egress. Provider
availability and prices must be rechecked immediately before launch.

## Frozen source and environment controls

- MMS/fairseq source commit: `3d262bb25690e4eb2e7d3c1309b1e9c406ca4b99`
- Original VITS source commit: `2e561ba58618d021b5b8323d3765880f7e0ecfdb`
- Base environment: PyTorch 2.1.2, CUDA 12.1, cuDNN 8, Python 3.10 on Linux
- Full Yoruba archive expected size: 919,869,645 bytes
- Dataset manifest SHA-256: `4fbb4b3f977b9733245cbc4c2013245a92a0ade284001fc6d9e30f208a228946`

The setup must record the container-image digest, downloaded archive SHA-256, GPU/driver details,
resolved source-tree hashes, installed package inventory, and recipe hash before training. A mismatch
must stop execution rather than update the recipe.

## Remaining reproducibility limitations

1. The archive's cryptographic digest is not published in the repository and must be recorded after
   the approved download; the known byte count alone is not a cryptographic integrity check.
2. Original VITS contains a compiled monotonic-alignment extension. The prepared Linux/CUDA container
   avoids the current Windows/CPU incompatibility, but compilation must pass the runtime preflight.
3. FP16 CUDA kernels can retain limited device-dependent variation even with deterministic settings.
   Hardware, driver, CUDA, and cuDNN versions must therefore be logged.
4. The three-item development and test subsets are statistically weak; the recipe is a feasibility
   pilot, not a confirmatory study.
5. Condition A has ceiling scores on pronunciation, tone, intelligibility, and meaning. Only
   naturalness has observed room to improve on the frozen test subset.

## Official pricing and platform sources

- RunPod pricing: https://www.runpod.io/pricing
- Google Colab resource policy: https://research.google.com/colaboratory/faq.html
- Kaggle GPU identifiers and notebook execution tooling: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
- Lambda pricing: https://lambda.ai/pricing
- Paperspace pricing: https://docs.digitalocean.com/products/paperspace/pricing/

No training is authorized by this review.
