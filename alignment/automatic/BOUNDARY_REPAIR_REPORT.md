# Automatic boundary repair report

All 30 review records now pass the structural interval validator. The original
Omnilingual CTC output remains preserved in
`omnilingual_ctc_training_batch_01.raw.jsonl`; the repaired review source is
`omnilingual_ctc_training_batch_01.jsonl`.

The failures came from four mechanical properties of the first projection:

1. token padding caused small overlaps between independently derived adjacent
   intervals;
2. repeated/shared grapheme matches produced intersecting syllable spans;
3. unmatched low-confidence words or syllables had null boundaries; and
4. timestamp rounding occasionally crossed the waveform endpoint.

Repairs are intentionally conservative: valid timestamps remain unchanged,
overlaps are split at their midpoint, missing spans are initialized
proportionally, and out-of-range values are clamped. The machine-readable audit
records every old and new value. Human review remains required for acceptance.
