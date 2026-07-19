# Split and leakage policy

## Current restriction

The 120 frozen calibration prompts have already been used repeatedly for model evaluation. They must not be used as both training examples and evidence of final improvement.

## Required future partitions

- **Train:** pronunciation learning and augmentation.
- **Development:** checkpoint selection and loss-weight tuning.
- **Diagnostic:** known pronunciation phenomena, available during development but excluded from headline metrics.
- **Test:** concealed or access-controlled until the method is frozen.

When the corpus has multiple speakers, hold out complete speakers for the primary generalization test. Also group related sentences, lexical items, and tone-contrast families before splitting so near-duplicates cannot cross partitions.

## Existing 120 items

Use them as a public diagnostic/calibration benchmark or, in an explicitly labeled pilot only, as adaptation data with a completely separate evaluation set. Do not report results on these same items as unbiased generalization.

Every exported manifest must include `split`, `benchmark_exclusion`, and `split_group_id`. A release script must reject any training record marked `benchmark_exclusion=true`.

