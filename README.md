# Yoruba pronunciation resource and integration research

This repository develops a training-ready Yoruba pronunciation resource and a model-independent methodology for improving Yoruba pronunciation in existing multilingual speech-generation systems.

## Research question

Can verified Yoruba speech, pronunciation representations, and—when required—explicit tone supervision measurably improve held-out Yoruba pronunciation in an existing multilingual speech model without reducing intelligibility or naturalness?

## Current checkpoint

- 120 controlled single-speaker Yoruba recordings collected;
- audio quality checked and standardized locally;
- Unicode-safe orthographic H/M/L tone annotations generated;
- frame-level pYIN F0 tracks and utterance contours extracted;
- 17 meaning-relevant contrast groups defined;
- utterance-level alignment completed;
- all 120 recordings listening-verified by the fluent speaker;
- one trailing-noise correction completed (`0205`), with no re-recordings required;
- matched ChatGPT Voice and Microsoft Copilot Voice baselines evaluated;
- a concise functional-load tone-prompt intervention implemented and tested;
- prompt-level tone guidance produced **no aggregate improvement** over the matched ChatGPT baseline: exact transcript accuracy, tone correctness, and naturalness were unchanged, while strict meaning recovery decreased from 33.3% to 22.2% on nine valid pairs.

The prompt intervention is retained as a reproducible null result. It shows that prompt wording alone did not repair pronunciation. Future experiments will therefore compare verified data adaptation, a pronunciation-aware frontend, and optional auxiliary supervision in that order.

## Pronunciation resource package

The next phase is organized around a portable dataset and method rather than a standalone voice model:

- `dataset/` contains the resource specification, annotation guide, split/leakage policy, dataset card, release gates, schema, and metadata-only manifest;
- `method/` contains the staged integration guide, optional auxiliary-loss specification, and controlled proof-of-concept protocol;
- an open-source TTS model will be used only after authorization as a proof-of-concept test bed.

The current collection is a verified single-speaker calibration seed, not yet a publicly releasable or population-representative training corpus. See `dataset/PRONUNCIATION_RESOURCE_SPEC.md` for readiness levels and remaining gates.

The current readiness decision and exact blockers are recorded in `dataset/TRAINING_READINESS_REPORT.md`. The 120 previously evaluated prompts are marked diagnostic and benchmark-excluded in schema version 0.2 so they cannot accidentally be used as unbiased training evidence.

The 29-recording human-verified alignment batch can now be assembled as a
private portable release candidate with `scripts/build_portable_release.py` and
checked offline with `scripts/validate_portable_release.py`. The generated
audio package remains local and non-redistributable until the signed release
and license gates are complete. See `dataset/PORTABLE_RELEASE.md`.

An architecture-independent integration dry run is available through
`scripts/build_integration_dry_run.py`. It produces canonical model-neutral
records plus text-sequence and aligned-acoustic-sequence adapters while
preserving exact Yoruba Unicode and enforcing provenance-aware loss masks. No
model is loaded or trained in this phase.

## Experiment 1

Phase 1 selected Meta MMS-TTS Yoruba as the first non-commercial research
test bed. The interface-only audit covered all 29 canonical records with zero
unknown tokenizer symbols and complete mapping of every annotated tone-bearing
syllable. No model weights were loaded or changed, and training has not begun.

See `experiment_01/PHASE_1_MODEL_SELECTION.md` for the candidate comparison,
decision constraints, model-adapter design, and gates before Condition A.

Condition A now contains reproducible unmodified-model outputs for the three
leakage-safe test items. Generation and packaging passed, model weights were
unchanged, and a byte-identical offline rerun succeeded. Primary fluent-listener
ratings are complete as a three-item single-rater pilot: pronunciation, tone,
intelligibility, and meaning were correct; naturalness was partial. See
`experiment_01/CONDITION_A_IMPLEMENTATION_REPORT.md`.

Condition B has now started at preflight. The protected split, audio, hashes,
and MMS tokenizer contract pass, and no weights have been updated. The local
runtime has no CUDA device. See `experiment_01/CONDITION_B_PREFLIGHT.md`.

The complete Condition B recipe is now frozen but not approved for execution.
It uses Meta's original trainable MMS/VITS generator and discriminator, a
conservative small-data update policy, development-only early stopping, and a
12 GB minimum NVIDIA GPU. See `experiment_01/CONDITION_B_TRAINING_RECIPE.md`.

The reviewed execution target is a RunPod RTX A5000 24 GB Pod, currently the
lowest-cost practical reproducible option in the provider comparison. A pinned
Linux/CUDA container and fail-closed environment preflight are available in
`execution/condition_b/`; neither can start training while approval is pending.
See `experiment_01/CONDITION_B_EXECUTION_REVIEW.md`.

A strict implementation audit now confirms that the approval-gated original-
VITS/MMS runner is implemented and its synthetic orchestration test passes.
Real GPU execution remains blocked on data-transfer approval, verified
checkpoint acquisition, the approved Linux/CUDA preflight, and a ten-update
technical validation counted within the frozen budget. See
`experiment_01/CONDITION_B_IMPLEMENTATION_AUDIT.md`.

## Repository scope

The repository tracks code, manifests, reports, recording sheets, and reproducible research metadata. Participant audio and generated ZIP archives are intentionally excluded from Git until a signed voice/data release and distribution plan are complete.

## Important limitation

An Omnilingual ASR CTC acoustic alignment layer is now available for the new
30-item pronunciation batch. It preserves the authoritative NFC Yoruba text,
records token-derived word and syllable estimates with transparent confidence,
and keeps automatic, manual, and verified layers separate. These estimates are
not training-authoritative until a fluent reviewer exports and imports the
human-verified corrections through the local alignment review tool. See
`alignment/OMNILINGUAL_CTC_ALIGNMENT.md`.

The project does not report lexical Tone Error Rate until the relevant acoustic
units have completed this manual boundary review.

The current voice-system and intervention results are single-rater diagnostic findings from a small, non-blinded pilot. They are not population-level estimates or provider rankings.

## Data and consent

The speaker authorized research and commercial use in the project conversation. A signed release is still required before public redistribution or commercial dataset publication. See the consent status inside the local benchmark package.
