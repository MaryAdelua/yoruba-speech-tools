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
- 20 of 120 recordings listening-verified by the fluent speaker;
- no verified transcript or naturalness failures so far.

## Repository scope

The repository tracks code, manifests, reports, recording sheets, and reproducible research metadata. Participant audio and generated ZIP archives are intentionally excluded from Git until a signed voice/data release and distribution plan are complete.

## Important limitation

Word-, syllable-, and vowel-level acoustic timestamps remain pending. The project does not report lexical Tone Error Rate until Yoruba-capable alignment and manual review are complete.

## Data and consent

The speaker authorized research and commercial use in the project conversation. A signed release is still required before public redistribution or commercial dataset publication. See the consent status inside the local benchmark package.
