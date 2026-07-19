# Yoruba pronunciation training Batch 01 completion report

## Outcome

Batch 01 contains 30 new, speaker-approved Yoruba utterances that do not exactly duplicate the frozen 120-item diagnostic benchmark.

- train: 24 utterances;
- development: 3 utterances;
- held-out test: 3 utterances;
- standardized format: mono, 24 kHz, signed 16-bit PCM WAV;
- total standardized duration: 94.4 seconds;
- automatic technical-quality flags: none;
- transcript verification: 30/30 passed;
- pronunciation verification: 30/30 passed;
- lexical-tone verification: 30/30 passed;
- naturalness verification: 30/30 passed;
- re-recordings required: none.

## Correction history

The source file `speaker01_YT00016.m4a` was confirmed as the item intended for `YT0015` and renamed accordingly. The separately supplied `YT0017` completed the original 29-file ZIP.

## Current limitation

This batch is verified at utterance level by the recorded speaker. Phoneme sequences, syllable boundaries, surface-tone labels, and sub-utterance acoustic timestamps are not yet human-verified. The signed release is also pending, so audio remains private and must not be publicly redistributed.

## Next processing stage

Create versioned Yoruba grapheme-to-phoneme and syllable annotations, map orthographic H/M/L targets to tone-bearing units, generate initial automatic alignments, and route uncertain annotations for fluent-speaker review. The three test items must remain excluded from training and tuning.

