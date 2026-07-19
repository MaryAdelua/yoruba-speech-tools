# Yoruba voice benchmark evaluation protocol

## Purpose

Evaluate whether a voice system can speak Yoruba accurately enough to preserve the intended words, lexical tones, sentence meaning, and naturalness.

## Required system output

Generate one WAV file for every row in `evaluation_items.csv`. Name each file `<prompt_id>.wav`, for example `0101.wav`. Use mono, 24 kHz, 16-bit PCM when possible. Do not add music, explanations, or sound effects.

## Automatic checks

The evaluator reports:

- prompt coverage;
- WAV readability and audio format;
- duration and duration ratio against the verified reference;
- peak and RMS level;
- clipped-sample percentage;
- empty, unusually short, and unusually long outputs.

These are diagnostic metrics, not a pronunciation score.

## Human outcomes

Each generated recording is rated without exposing the reference recording during the first pass.

1. **Transcript match:** Are all intended Yoruba words spoken, with no additions or omissions?
2. **Pronunciation naturalness:** Does the pronunciation sound natural to a fluent Yoruba speaker?
3. **Tone correctness:** Are lexical and grammatical tones realized correctly?
4. **Meaning recovery:** Does the listener recover the intended English meaning or contrast choice?
5. **Naturalness:** A 1–5 mean-opinion score.

## Primary research metrics

- **Tone Contrast Preservation Accuracy (TCPA):** accuracy on items in the 17 controlled contrast groups.
- **Meaning Recovery Accuracy:** proportion of items whose intended meaning is recovered.
- **Transcript Accuracy:** proportion with every intended word present and no extra word.
- **Naturalness MOS:** mean 1–5 rating with uncertainty intervals.

## Important limitation

Syllable Tone Error Rate is not reported yet. The benchmark has orthographic H/M/L targets and utterance-level F0, but manually verified word, syllable, and vowel-nucleus time boundaries are still pending. Whole-utterance F0 similarity must not be presented as lexical-tone accuracy.

## Comparison design

For each tested system:

- keep prompt text identical;
- record the model name, voice, date, settings, and generation method;
- randomize and blind system identity during human review;
- use the same fluent-speaker questions for every system;
- eventually add at least two independent fluent Yoruba raters for publication-quality claims.

The current single-speaker review is suitable for prototype diagnostics, not population-level perceptual claims.
