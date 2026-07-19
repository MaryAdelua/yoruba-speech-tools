# Tone-aware pronunciation intervention

## Research condition

The preferred intervention adds one short tone-and-meaning cue for the sentence's meaning-critical word. The spoken output remains the original sentence.

An initial feasibility version included a full word-level H/M/L plan. ChatGPT Voice truncated or failed to complete outputs under those longer prompts. Those trials are not pronunciation outcomes and must not be mixed with the baseline. The concise version removes sentence-wide labels to reduce interface load while retaining the functional-load intervention.

The ordinary-text ChatGPT Pilot 3 is condition A. The concise tone-aware prompt set is condition B. The same voice, target sentences, order, capture method, listener questions, and scoring rules must be used in both conditions.

## Primary comparison

- exact transcript match;
- tone correctness;
- strict meaning recovery;
- natural Yoruba pronunciation.

## Interpretation boundary

This is a prompting intervention for black-box voice systems. It is not equivalent to training a TTS model with an explicit tone loss. A positive result would show that structured pronunciation control can improve output without model retraining. A null result would support the need for architecture-level tone supervision.

The HIGH/MID/LOW cue represents the critical word's orthographic target only. It does not yet encode context-conditioned surface tone, downstep, elision, or coarticulation.

## Pilot result

The concise intervention produced ten usable responses but did not improve the nine-item matched comparison. Exact transcript accuracy, tone correctness, and naturalness were unchanged; strict meaning recovery decreased. See `TONE_AWARE_INTERVENTION_REPORT.md`. The project will retain this as a null prompt-level intervention rather than repeatedly tuning prompts on the test set.
