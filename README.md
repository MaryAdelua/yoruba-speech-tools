# Yoruba Speech Tools: Evaluation and Pronunciation Research

Research by Mary Adelua on meaning-preserving Yoruba speech generation. This repository contains **two connected phases of one research programme**: an earlier evaluation and tone-prompt study, followed by a pronunciation-resource and model-adaptation continuation.

The continuation asks whether verified data and controlled model integration can address limitations observed in the earlier study. It does not replace the earlier results or establish that adaptation improves Yoruba speech.

## Start here

| Phase | Question and contribution | Evidence and status |
| --- | --- | --- |
| **1. Speech evaluation and tone-prompt study** | Measure transcript, tone, meaning and naturalness separately; test concise tone guidance in existing voice systems. | [Benchmark](benchmark/README.md), [evaluation protocol](evaluation/EVALUATION_PROTOCOL.md), [cross-system pilot](evaluation/results/pilot_03_cross_system_comparison.md), [tone-prompt report](intervention/TONE_AWARE_INTERVENTION_REPORT.md). Completed diagnostic pilot; the null result is retained. |
| **2. Pronunciation resource and model-adaptation continuation** | Build verified pronunciation/alignment resources, portable metadata and model-independent adapters; investigate a controlled MMS-TTS adaptation experiment. | [Verified dataset card](dataset/VERIFIED_ALIGNMENT_DATASET_CARD.md), [integration toolkit](integration/README.md), [Condition A report](experiment_01/CONDITION_A_IMPLEMENTATION_REPORT.md), [pause handoff](PAUSE_HANDOFF.md). Paused as of 19 July 2026; full Condition B and Condition C have not started. |

This overview was reconciled on 24 October 2026 against the dated records below. Existing folders and research artifacts remain in place.

## Phase 1 — evaluation and the null prompting result

The earlier work assembled 120 controlled single-speaker Yoruba recordings, audio-quality checks, Unicode-safe orthographic H/M/L tone annotations, frame-level pYIN F0 tracks, utterance contours and 17 meaning-relevant contrast groups. The recordings were listening-verified by the fluent speaker; this is not independent multi-rater validation.

Matched ChatGPT Voice and Microsoft Copilot Voice pilots evaluated speech quality. A concise functional-load tone cue then tested whether prompting could improve the matched ChatGPT baseline.

Across **nine valid matched pairs**, exact transcript accuracy, tone correctness and naturalness were unchanged; strict meaning recovery decreased from **33.3% to 22.2%**. The [intervention report](intervention/TONE_AWARE_INTERVENTION_REPORT.md) retains individual improvements and regressions, unusable-trial exclusions and the null aggregate finding.

These are small, single-rater, non-blinded diagnostic results. They are not provider rankings, population estimates or proof that a proposed training method will work.

## Phase 2 — a continuation through verified resources and controlled adaptation

### Resource and alignment work

A separate 30-item collection produced **29 verified recordings**, with one excluded item and one corrected transcript. The [verified dataset card](dataset/VERIFIED_ALIGNMENT_DATASET_CARD.md) records 178 verified word boundaries and 321 verified syllable boundaries. Automatic estimates, corrections and the human-verified layer remain separate.

**Boundary annotation is not model evaluation:** human alignment review establishes where words and syllables occur in reference recordings. It does not show that synthesized speech improved. Orthographic tone labels are also not complete surface-tone measurements, and automatic phoneme candidates are not verified phoneme labels.

The continuation includes:

- [Resource specification](dataset/PRONUNCIATION_RESOURCE_SPEC.md), [split/leakage policy](dataset/SPLIT_AND_LEAKAGE_POLICY.md) and [portable release guidance](dataset/PORTABLE_RELEASE.md).
- [Model-independent integration adapters](integration/README.md), Unicode-safe text processing and provenance-aware loss masks.
- [Model-selection audit](experiment_01/PHASE_1_MODEL_SELECTION.md) and a frozen controlled experiment using Meta MMS-TTS Yoruba.

The earlier 120 diagnostic prompts are benchmark-excluded for unbiased adaptation evidence. The verified batch is a single-speaker proof-of-concept seed, not a general-purpose Yoruba corpus.

### Model experiment: dated status

The [19 July 2026 pause handoff](PAUSE_HANDOFF.md) is the current status reference. Earlier preflight and implementation reports retain their historical gates; they do not override the later handoff.

| Stage | What is supported by the record | What is not established |
| --- | --- | --- |
| **Condition A: unmodified baseline** | Three held-out items generated; unchanged model weights; byte-identical offline rerun; human ratings complete. See [implementation report](experiment_01/CONDITION_A_IMPLEMENTATION_REPORT.md). | A three-item, single-rater, non-blinded pilot cannot establish population performance. Naturalness was partial; pronunciation-related ratings had a ceiling effect. |
| **Condition B: technical validation** | Zero-update GPU preflight and separately approved **10 optimizer updates** completed. The handoff records no perceived regression and small perceived improvements on the three comparison items. | Ten updates are technical validation, not the full Condition B result or a validated improvement claim. |
| **Condition B: full feasibility run** | Frozen approval allows at most 300 updates; [approval record](execution/condition_b/full_training_approval.json) retained. | **Not started.** Project remains paused; a new continuation decision is required. |
| **Condition C** | A possible later research condition. | **Not started and not approved** in the Condition B record. |

The historical local CUDA/checkpoint blockers were resolved for technical validation. The handoff records a later managed-environment restriction on initiating external private-audio processing; it is not a claim that the code or GPU validation failed. No training or external audio processing is initiated by these documentation changes.

## Code and lightweight checks

Python tools cover text/tone representations, alignment review, portable metadata validation, integration adapters and approval-gated experiment runners. The code also contains tests; recorded GPU validation is separate from local text checks.

For a dependency-free check of the Unicode/tone and pronunciation components, from the repository root:

```bash
git clone https://github.com/MaryAdelua/yoruba-speech-tools.git
cd yoruba-speech-tools
python3 -m unittest discover -s tests -p 'test_tone_parser.py' -v
python3 -m unittest discover -s tests -p 'test_yoruba_pronunciation.py' -v
```

Use Python 3.10 or newer. These commands do not load model weights, read private audio or start training. They cover only those two test modules, not the complete integration or GPU workflow. Other scripts have data, dependency and approval requirements described in their own guides.

## Evidence, limitations and data access

- **Demonstrated:** reproducible diagnostic comparisons, a preserved null prompting result, verified reference alignment, portable metadata and adapters, an unmodified-model baseline and limited technical training validation.
- **Not yet demonstrated:** full Condition B/C outcomes, generalizable adaptation gains, independent blinded multi-rater evaluation, a finished validated speech model or a publicly releasable voice dataset.
- Participant audio, private bundles and checkpoints must remain outside Git. A public code repository does not authorize redistribution of voice recordings. Signed release, dataset-license and other gates remain in the [release checklist](dataset/RELEASE_CHECKLIST.md).
- [Human evaluation](experiment_01/CONDITION_A_IMPLEMENTATION_REPORT.md), [alignment authority](dataset/VERIFIED_ALIGNMENT_DATASET_CARD.md) and [technical execution status](PAUSE_HANDOFF.md) answer different questions; none substitutes for the others.
- Results, frozen splits, recipes, hashes and original research records are preserved. No experiment was rerun or result changed for this overview.
