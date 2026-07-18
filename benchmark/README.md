# Yoruba Voice Benchmark v0.1

This package contains 120 controlled, single-speaker Yoruba reference recordings for research on meaning-preserving Yoruba speech synthesis and voice-model evaluation.

## Intended use

- evaluate lexical-tone and meaning preservation in synthesized Yoruba speech;
- develop tone-aware or meaning-risk-weighted training objectives;
- create forced-choice listening tests and error analyses;
- compare voice models on questions, commands, negation, connected speech, and voice-assistant utterances.

This is a controlled reference/evaluation corpus, not sufficient by itself to train a general-purpose Yoruba voice model.

## Audio processing

- source: M4A recordings made by one fluent Yoruba speaker;
- output: mono, 24 kHz, 16-bit PCM WAV;
- edge silence: detected in 20 ms frames below -45 dBFS, with 200 ms retained padding;
- level: active-speech RMS targeted to -23 dBFS, gain limited to +15/-12 dB and peak limited to -2 dBFS;
- originals were not modified.

## Files

- `audio_wav_24k/`: standardized recordings;
- `benchmark_manifest.csv`: transcripts, meanings, processing metadata, and contrast memberships;
- `tone_annotations.jsonl`: Unicode-safe orthographic vowel/tone units and H/M/L sequences;
- `contrast_groups.csv`: provisional meaning-relevant contrast sets;
- `CONSENT_STATUS.md`: release and consent limitations.

## Important limitations

- Tone labels are orthographic, not measured surface F0 contours.
- Transcript-to-audio alignment has not yet been independently listening-verified.
- Contrast groups are provisional and require fluent-speaker/linguist review.
- This single-speaker set cannot establish population-wide naturalness or intelligibility.
