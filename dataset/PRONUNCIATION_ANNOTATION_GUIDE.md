# Pronunciation annotation guide

## Principles

1. Preserve the speaker-verified Yoruba text as the canonical source.
2. Never infer missing tone marks silently; proposed corrections require fluent review.
3. Keep lexical/orthographic tone separate from observed surface F0.
4. Store automatic outputs with their tool version and confidence.
5. A human-verification label identifies both the reviewer role and review date.

## Tone-bearing units

Create one unit for each vowel nucleus represented in the canonical text. Use `H` for acute, `L` for grave, and `M` for an unmarked vowel. Underdots identify vowel quality and do not themselves specify tone. Character offsets refer to the NFC-normalized canonical text.

For each unit record the grapheme, base vowel, lexical tone, word index, syllable index when available, character span, timing, and provenance. Orthographic tone is a text-derived target; it must not be relabeled as a verified surface tone.

## Phonemes and syllables

Phoneme labels should use a versioned Yoruba inventory. Each phoneme must map back to a word and character span. Syllable records identify onset, nucleus, coda where applicable, and the tone-bearing unit. Ambiguous pronunciations retain alternatives rather than forcing an undocumented choice.

At least one fluent annotator reviews all benchmark phonemes and syllables. A second reviewer should independently review a stratified sample containing all contrast types. Disagreements are retained and adjudicated; only adjudicated labels enter the frozen test set.

## Acoustic alignment

Alignment states are:

- `pending` — no usable boundary;
- `automatic_unverified` — model-derived boundary;
- `human_verified` — boundary inspected against waveform and spectrogram;
- `rejected` — boundary or audio is unusable.

Training code must receive a validity mask and must not treat pending boundaries as ground truth. F0 targets use voiced masks and speaker-normalized log-F0; unvoiced frames are missing observations, not zero pitch.

## Quality labels

Reviewers score these dimensions independently:

- transcript completeness;
- segmental pronunciation, including vowel quality and underdotted letters;
- lexical-tone correctness;
- intelligibility;
- naturalness;
- intended-meaning recovery.

A single overall “good/bad” label is insufficient because it cannot show which training intervention helped.

## Corrections and versioning

Every corrected transcript, boundary, or audio edit receives a new annotation or asset version. The correction log records the old value, new value, reason, reviewer, and date. Released identifiers remain stable.

