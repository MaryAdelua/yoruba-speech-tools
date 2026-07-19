# Meaning-Preserving Yoruba Voice Research

This repository contains the research design, preprocessing code, annotation tools, acoustic pitch-analysis workflow, and alignment metadata for a controlled Yoruba voice-model benchmark.

## Research question

Can explicit syllable-tone supervision and meaning-risk-weighted contrastive objectives reduce meaning-changing Yoruba pronunciation errors in modern voice models without reducing naturalness?

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

The prompt intervention is retained as a reproducible null result. The project will not repeatedly tune prompts on the same test items. The next technical stage, when separately authorized, is an architecture-level tone objective on a trainable open Yoruba TTS baseline.

## Repository scope

The repository tracks code, manifests, reports, recording sheets, and reproducible research metadata. Participant audio and generated ZIP archives are intentionally excluded from Git until a signed voice/data release and distribution plan are complete.

## Important limitation

Word-, syllable-, and vowel-level acoustic timestamps remain pending. The project does not report lexical Tone Error Rate until Yoruba-capable alignment and manual review are complete.

The current voice-system and intervention results are single-rater diagnostic findings from a small, non-blinded pilot. They are not population-level estimates or provider rankings.

## Data and consent

The speaker authorized research and commercial use in the project conversation. A signed release is still required before public redistribution or commercial dataset publication. See the consent status inside the local benchmark package.
