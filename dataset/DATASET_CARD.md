# Yoruba Pronunciation Calibration Set

## Version

`0.2-research` — pronunciation-resource metadata checkpoint. Audio redistribution is not yet authorized.

## Summary

This package contains 120 controlled Standard Yoruba utterances recorded by one fluent speaker. It is designed as a pronunciation calibration and diagnostic seed for existing multilingual speech models—not as a standalone corpus for training a general-purpose Yoruba voice.

## Intended contribution

- verified Yoruba transcripts and English meanings;
- controlled lexical-tone and meaning contrasts;
- orthographic H/M/L annotations;
- utterance-level acoustic and quality metadata;
- fluent-speaker transcript and naturalness verification;
- explicit readiness and provenance fields so unverified annotations cannot silently enter training;
- reproducible benchmark and human-rating protocols.

## Data composition

- speakers: 1;
- utterances: 120;
- language: Yoruba (`yo`);
- variety: fluent general Yoruba; this is not a regional-dialect study;
- processed format: mono, 24 kHz, 16-bit PCM WAV;
- controlled contrast groups: 17;
- listening verification: 120/120;
- re-recordings required: 0;
- resolved audio corrections: 1 (`0205`, trailing noise trimmed).

## Recommended uses

- held-out tone and meaning evaluation;
- regression testing for multilingual speech systems;
- calibration experiments and frontend validation with appropriate safeguards;
- validating pronunciation-aware adapters and optional tone objectives;
- model-selection gates for Yoruba pronunciation and meaning preservation.

## Uses requiring caution

The set is too small and too speaker-specific to establish general Yoruba naturalness or population-level performance. It must not be presented as representative of all Yoruba speakers, dialects, ages, genders, or recording environments.

## Current annotation layers

1. verified utterance transcript and English meaning;
2. Unicode-normalized orthographic tone sequence;
3. word and vowel-nucleus inventories with character offsets;
4. meaning-relevant contrast-group membership;
5. utterance-level F0 and audio-quality summaries;
6. human listening-verification status;
7. diagnostic split and benchmark-exclusion metadata.

Phoneme labels and word, syllable, and vowel-nucleus time boundaries are not yet verified. Surface-tone processes such as downstep, assimilation, and elision are not yet annotated. The current manifest is therefore orthography/tone diagnostic data, not full pronunciation-supervision data.

## Consent and release

The speaker authorized research and commercial use in the project conversation. A signed voice/data release is still required before public audio redistribution, commercial dataset publication, or external model training. See `RELEASE_CHECKLIST.md` and the repository consent status.

## Known limitations

- one speaker;
- 120 short utterances;
- single-rater diagnostic model evaluations;
- no verified sub-utterance acoustic timestamps;
- orthographic tone labels are not identical to context-conditioned surface realization;
- participant audio is intentionally excluded from Git.

## Citation status

No formal citation has been assigned. Add a versioned citation, authorship statement, and persistent identifier before public release.
