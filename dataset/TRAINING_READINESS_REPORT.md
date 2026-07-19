# Training-readiness report

## Assessment

**Current level: L0 metadata-only; technically verified diagnostic seed.**

The project has 120 standardized, single-speaker reference recordings with verified transcripts and naturalness, orthographic H/M/L tone units, acoustic summaries, and a completed listening review. The regenerated version 0.2 manifest passes automated validation for all 120 records.

It is not yet an externally training-ready release because audio rights are not documented in a signed release, audio is not distributed with release checksums, the evaluated prompts lack an independent train/test boundary, and phoneme/syllable alignment is not human-verified.

## Completed assets

- 120 stable utterance IDs and canonical audio metadata;
- speaker-verified Yoruba transcript and English meaning per item;
- Unicode-safe orthographic tone units;
- standardized mono 24 kHz PCM profile;
- audio quality and F0 analysis artifacts;
- correction history and complete listening verification;
- frozen cross-system pronunciation benchmark evidence;
- schema 0.2 provenance, split, and benchmark-exclusion fields;
- architecture-independent staged integration protocol.

## Blocking work before adaptation training

1. Obtain the signed speaker release and select an audio/metadata license.
2. Decide whether the current 120 items remain diagnostic-only. The recommended answer is yes.
3. Collect or designate separate train, development, and concealed test material.
4. Define the versioned Yoruba phoneme inventory and generate auditable G2P labels.
5. Human-review test-set phonemes, syllables, and lexical tones.
6. Verify alignments for the pronunciation-supervision subset.
7. Add final audio hashes, duplicate detection, and coverage statistics.

## Expansion priorities

The next recordings should fill measured coverage gaps and include multiple speakers. Reserve complete speakers and lexical/contrast families for testing. A large number of near-duplicate sentences from the same speaker would add duration without establishing generalization.

## Recommended first proof of concept

After the gates pass, run the four matched conditions in `method/PROOF_OF_CONCEPT_PROTOCOL.md`. The first comparison is host baseline versus ordinary Yoruba data adaptation. Only add explicit phoneme/tone features and auxiliary losses if the simpler approach leaves systematic pronunciation errors.

## Evidence required for a useful result

The project can claim practical improvement only when a held-out evaluation shows lower segmental or lexical-tone error and better fluent-listener intelligibility than the same host model without the resource. F0 similarity, training loss, or success on memorized calibration sentences is not sufficient.

