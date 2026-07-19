# Integration guide for existing speech-generation systems

## Goal

Improve Yoruba pronunciation in an existing multilingual model while changing as little of the host system as necessary. Start with the simplest intervention and add specialized supervision only when the error analysis justifies it.

## Integration ladder

### Level 1: Evaluation only

Generate the frozen Yoruba prompts and run the human pronunciation protocol. This identifies segmental, tone, truncation, and naturalness failures before training changes are made.

### Level 2: Data adaptation

Fine-tune or mix consented Yoruba text–audio pairs into the host training pipeline. Preserve complete diacritics, record sampling ratios, and compare against an otherwise matched baseline. This is the first recommended training intervention.

### Level 3: Pronunciation-aware frontend

Add versioned Yoruba phonemes, syllable boundaries, and H/M/L features. Map each feature to host tokens through character spans rather than assuming one tokenizer. Compare grapheme-only and pronunciation-aware frontends using the same data and compute budget.

### Level 4: Auxiliary supervision

If tone errors remain, attach an auxiliary H/M/L classifier and, where aligned acoustic states exist, a voiced-mask normalized-F0 objective. If segmental errors remain, add phoneme prediction or pronunciation-consistency supervision. These objectives are optional components, not requirements of the dataset.

### Level 5: Contrast-focused sampling

Oversample verified contrasts that the baseline confuses, while retaining ordinary sentences to prevent overfitting to minimal pairs. Experimental semantic-risk weighting is permitted only as a separately reported ablation.

## Portable adapter contract

An adapter maps dataset annotations to host-model positions and may expose:

- token-to-character and token-to-tone-unit mappings;
- phoneme and tone targets with validity masks;
- duration-expanded or aligned acoustic regions;
- optional normalized F0 targets and voiced masks;
- provenance and confidence for every non-text label.

The contract makes no assumption about autoregressive versus parallel decoding, mel spectrograms versus codec tokens, or speaker-embedding design.

## Implemented dry-run toolkit

The architecture-independent contract is implemented in
`src/integration_toolkit.py` and documented in `integration/README.md`. The
current dry run emits a text-encoder-style sequence and a 50 Hz aligned
acoustic-frame sequence from the same canonical targets. All 29 records retain
the same target-identity hash across both adapters, and no model weights are
loaded or updated.

Phoneme and surface-tone losses are deliberately masked off. The phoneme layer
has not completed full linguistic review, and context-conditioned surface tone
is not annotated. Verified word/syllable supervision and orthographic tone
features remain enabled.

## Recommended experimental sequence

| Condition | Data | Frontend | Auxiliary loss | Question answered |
|---|---|---|---|---|
| A | Host baseline | Existing | None | How poorly does the original system perform? |
| B | Yoruba pairs | Existing | None | Does verified data alone help? |
| C | Same pairs | Phoneme + tone | None | Does explicit pronunciation representation help? |
| D | Same pairs | Phoneme + tone | Tone/F0 as applicable | Does auxiliary supervision add benefit? |

Keep initialization policy, update budget, sampling, decoding, voice, and evaluation items matched. Run multiple seeds where training variance is material.

## Required reporting

- host model and version;
- exact data version, split, and sampling ratio;
- text normalization, tokenizer, phonemizer, and alignment versions;
- trainable parameters and attachment points;
- objective coefficients and update budget;
- decoding settings and random seeds;
- segmental, tone, intelligibility, meaning, and naturalness results;
- item-level failures and confidence intervals;
- confirmation that test speakers and split groups were not used for training.

## Success rule

The integrated system must improve Yoruba pronunciation against the matched baseline on held-out material. At minimum, it must reduce segmental or lexical-tone errors and improve listener intelligibility without exceeding the predeclared naturalness non-inferiority margin. Acoustic F0 improvement alone is not sufficient.

## Non-training use

Teams that cannot modify a proprietary model can still use the resource for regression testing, model selection, failure triage, and Yoruba-specific release gates.
