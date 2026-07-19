# Architecture-independent integration toolkit

This toolkit converts the verified Yoruba alignment dataset into one canonical model-neutral record and two dry-run adapter representations. It does not import, initialize, train, or modify a speech model.

## Canonical contract

Each record preserves exact NFC Yoruba text, portable audio provenance, grapheme character spans, verified word and syllable boundaries, orthographic H/M/L tone units, supervision masks, and annotation provenance. A stable target-identity hash proves that adapters consume the same underlying targets.

Enabled supervision:

- text/audio pairs;
- verified word boundaries;
- verified syllable boundaries;
- orthographic tone features derived from authoritative text.

Disabled supervision:

- surface-tone loss, because context-conditioned surface tone is not annotated;
- phoneme loss, because the broad IPA layer remains partly automatic and has not completed full linguistic review.

## Dry-run adapters

`text-sequence-v1` represents a text-encoder-style system. It outputs grapheme units, exact character spans, word and syllable IDs, and orthographic tone IDs.

`acoustic-frame-v1` represents an aligned acoustic or codec-style system. It expands verified boundaries onto a 50 Hz frame timeline and emits word, syllable, tone, and validity masks.

These are model-interface examples, not claims about the internals of any proprietary system.

## Run

```powershell
python scripts/build_integration_dry_run.py
```

Outputs are written to `artifacts/integration_dry_run/`. Success requires 29 Unicode round trips, 29 cross-adapter target-identity matches, valid masks, and `model_weights_updated=false`.

## Host-model integration

An implementation for a specific model should translate one of these adapter records into that model's tensors while preserving `target_identity_sha256`, provenance, and loss masks. Tokenizers that merge multiple graphemes must map host tokens back to the supplied character spans; they must not strip Yoruba diacritics.

## First model binding

The first validated binding targets `facebook/mms-tts-yor`. Run
`scripts/validate_mms_yoruba_interface.py` with the official tokenizer files
to reproduce the interface audit. The resulting artifact records the model's
normalized text view, filtered punctuation, unknown-token count, and the exact
mapping from VITS input positions to source graphemes, syllables, and H/M/L
labels. It does not load model weights or train a model.
