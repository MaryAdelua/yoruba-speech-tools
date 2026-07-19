# Yoruba Pronunciation Resource Specification

## Objective

Provide data that an existing multilingual speech-generation system can use to learn and test Standard Yoruba pronunciation. The resource is model-neutral: it does not require a particular tokenizer, acoustic representation, decoder, or waveform generator.

## Release units

The resource is organized into three independently usable units.

1. **Reference audio** — consented, quality-controlled speech paired with canonical Yoruba text.
2. **Pronunciation annotations** — grapheme, phoneme, syllable, tone-bearing-unit, and alignment metadata with provenance and confidence.
3. **Frozen pronunciation benchmark** — held-out prompts, listener protocol, system outputs, and item-level scores.

The current 120-utterance, single-speaker collection is a verified calibration and benchmark seed. It is not yet a population-representative training corpus.

## Minimum record contract

Every distributable utterance must contain:

- stable utterance and pseudonymous speaker identifiers;
- NFC-normalized Yoruba text with underdots and tone marks preserved;
- canonical audio path, checksum, duration, sample rate, channel count, and sample format;
- transcript and naturalness review status;
- one record for every orthographic tone-bearing vowel;
- explicit annotation provenance (`derived`, `automatic`, or `human_verified`);
- dataset split and a flag preventing benchmark leakage;
- rights status compatible with the stated use.

## Recommended pronunciation layers

| Layer | Purpose | Current status |
|---|---|---|
| Canonical Yoruba orthography | Text-to-speech input and audit trail | Complete, speaker-verified |
| Grapheme sequence | Frontend debugging | Derivable |
| Phoneme sequence | Cross-tokenizer pronunciation supervision | Specification required |
| Syllable boundaries | Duration and tone-bearing-unit mapping | Pending verification |
| Orthographic H/M/L tone | Lexical-tone supervision | Complete, automatically derived |
| Surface tone realization | Contextual tone and downstep modeling | Pending |
| Word/syllable timestamps | Duration expansion and acoustic alignment | Pending |
| Normalized F0 track | Optional acoustic supervision | Available at frame level; unit alignment pending |
| Human pronunciation score | Release evaluation | Available for collected references; multi-rater system evaluation pending |

## Canonical audio profile

- WAV, mono, 24 kHz, signed 16-bit PCM;
- no clipping or destructive denoising;
- leading and trailing silence policy documented;
- source audio retained privately for traceability;
- SHA-256 checksum computed after the final approved edit;
- corrections logged without silently replacing prior versions.

The audio profile is a release convention, not a claim that every host model must train at 24 kHz. Integrators may resample deterministically and must record that transformation.

## Frontend requirements

The frontend must preserve the distinctions represented by `ẹ`, `ọ`, `ṣ`, acute accents, grave accents, and unmarked mid tone. Unicode normalization must be tested before tokenization. A model may consume graphemes, IPA-like phonemes, or learned tokens, but its adapter must retain a reversible mapping to the original character spans and tone-bearing units.

The phoneme inventory and grapheme-to-phoneme rules must be versioned separately from the utterance manifest. Automatically generated phonemes cannot be labeled human-verified until a fluent reviewer has checked them.

## Training-readiness levels

- **L0 — metadata only:** text and metadata may be inspected; audio cannot be redistributed.
- **L1 — evaluation ready:** rights cleared, reference audio released, frozen items listener-verified.
- **L2 — adaptation ready:** train/dev items have verified text, audio, tone units, checksums, and leakage-safe splits.
- **L3 — pronunciation-supervision ready:** verified phonemes, syllables, and sub-utterance alignment are available.
- **L4 — generalization study ready:** multiple speakers and recording sessions support held-out-speaker evaluation.

The current package is L0 because a signed release and public audio license remain outstanding. Its annotations are approaching L2, but the data cannot be described as externally training-ready until the rights and split gates pass.

## Expansion target

Expansion should be driven by coverage rather than an arbitrary sentence count. Track:

- vowel and consonant coverage by word position;
- `ẹ/ọ/ṣ` and corresponding non-underdotted contrasts;
- H, M, and L tones in varied left and right contexts;
- common tone sequences and connected-speech processes;
- word length, syllable structure, punctuation, and sentence function;
- speaker, session, and recording-condition diversity;
- errors observed in existing multilingual speech systems.

The final training corpus should reserve speakers and lexical/contrast families for evaluation so that improvement cannot be explained by memorizing the benchmark.

