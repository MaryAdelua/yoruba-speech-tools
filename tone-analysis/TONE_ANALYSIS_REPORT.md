# Yoruba acoustic tone-analysis report

## Corpus-level pitch results

- Recordings analyzed: **120 of 120**
- Pitch method: **librosa pYIN**, 24 kHz audio, 10 ms hop, 65-500 Hz search range
- Total voiced F0 frames: **18,934**
- Speaker pooled median F0: **230.3 Hz**
- Speaker pooled 5th-95th percentile F0: **161.0-490.8 Hz**
- Median utterance voiced-frame ratio: **0.477**
- Utterances below 0.25 voiced-frame ratio: **0122**
- Controlled contrast groups screened: **17**

## What these results establish

The package now contains reproducible frame-level F0 tracks, speaker-normalized semitone contours, utterance summaries, and whole-utterance contour distances for the controlled contrast groups. These outputs are suitable for quality screening, visualization, baseline feature construction, and planning a tone-aware loss.

## What these results do not establish

This analysis does **not** yet measure lexical-tone accuracy. The recordings have orthographic H/M/L sequences, but individual words and vowel nuclei do not yet have acoustic time boundaries. Whole-utterance contour differences can be caused by sentence length, focus, emotion, or segmental context. Therefore, the contrast distances are explicitly labeled as screening results and must not be reported as Tone Error Rate or pronunciation accuracy.

## Required next stage

1. Listening-verify transcript-to-audio correspondence.
2. Align each utterance to word, syllable, and vowel-nucleus boundaries.
3. Associate each measured F0 interval with its orthographic H/M/L target.
4. Normalize for declination and local tonal context.
5. Compute syllable-level tone separability and error metrics with manual review of alignment failures.
