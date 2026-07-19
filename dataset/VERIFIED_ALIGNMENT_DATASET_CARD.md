# Yoruba Pronunciation Resource — Verified Alignment Batch

## Version and status

`v0.1-rc1` is a private release candidate. It is not authorized for public redistribution until the signed speaker release, explicit dataset license, privacy/misuse review, and persistent release identifier are complete.

## Purpose

This resource provides training-ready Standard Yoruba pronunciation examples and architecture-independent word and syllable alignments for integration into existing multilingual speech-generation systems. It is a calibration seed and proof-of-concept resource, not a standalone general-purpose Yoruba voice corpus.

## Composition

- language: Yoruba (`yo`);
- speaker: one fluent speaker (`speaker01`), publicly attributed as Mary Adelua when release authorization is complete;
- verified recordings: 29;
- excluded recordings: one (`YT0022`, missing matching audio);
- corrected transcripts: one (`YT0013`, resolved and re-aligned);
- audio: mono, 24 kHz, 16-bit PCM WAV;
- verified word boundaries: 178/178;
- verified syllable boundaries: 321/321.

## Human authority

The fluent speaker reviewed the transcript/audio relationship, naturalness, orthographic word segmentation, and the final word and syllable alignment records. Automatic alignments and repair audits remain available as provenance, but the portable dataset uses the human-verified layer as final authority.

## Intended uses

- verified-data adaptation of multilingual speech models;
- pronunciation-aware frontend integration;
- optional tone or prosody auxiliary supervision experiments;
- Yoruba pronunciation regression testing and error analysis;
- architecture-independent evaluation tooling.

## Limitations

- one speaker and 29 short utterances;
- not representative of all Yoruba speakers, dialects, recording conditions, ages, or genders;
- insufficient by itself to train a general-purpose Yoruba voice;
- orthographic tone is not a complete annotation of context-conditioned surface tone;
- external model improvements must be demonstrated on leakage-safe held-out material.

## Release safeguards

Each record has a SHA-256 audio checksum and portable relative path. The package validator checks checksums, audio format, duration, NFC text, identifiers, exclusions, and all boundary constraints. Audio must remain private until every blocking release gate in `RELEASE_CHECKLIST.md` is complete.
