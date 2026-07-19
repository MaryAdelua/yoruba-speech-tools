# Optional architecture-independent pronunciation losses

## Objective

Provide optional supervision when verified Yoruba data and a pronunciation-aware frontend do not sufficiently improve segmental or tonal pronunciation. These losses are not the primary product and must be tested against a data-only baseline.

## Required adapter outputs

An integrating model supplies:

- `tone_logits`: `[batch, units, 3]` predictions ordered H, M, L;
- `tone_targets`: `[batch, units]` integer labels;
- `tone_mask`: `[batch, units]` valid-unit mask;
- optional `meaning_risk_weights`: `[batch, units]` human-validated nonnegative weights;
- optional predicted and reference normalized F0 values;
- optional contrast embeddings and contrast-group identifiers.

The host architecture decides which internal representation produces these tensors.

## Combined objective

\[
L = L_{base} + \lambda_t L_{tone} + \lambda_f L_{F0} + \lambda_c L_{contrast}.
\]

### Tone classification loss

\[
L_{tone} =
\frac{\sum_i m_i CE(\hat t_i,t_i)}
{\sum_i m_i + \epsilon}.
\]

`m_i` is the valid-unit mask. Experimental risk weights may be added only if human-validated and must be reported as a separate ablation against this unweighted objective.

### Normalized F0 contour loss

Compute F0 in voiced frames, transform it to log scale, and normalize within speaker. Aggregate frame losses only inside aligned tone-bearing regions:

\[
L_{F0} = \frac{\sum_j v_j m_j\,Huber(\hat z_j,z_j)}{\sum_j v_jm_j+\epsilon}.
\]

The adapter must expose the normalization policy and must not treat unvoiced frames as zero-Hz tone targets.

### Contrast loss

For controlled forms sharing a contrast group:

\[
L_{contrast} = \max(0, margin + d(a,p) - d(a,n)).
\]

Positive pairs share the intended form/tone target; negative pairs are segmentally related forms whose tone difference changes meaning. Implementations may substitute supervised contrastive loss if they preserve the same semantics.

## Required ablations

1. host model only;
2. matched Yoruba data adaptation;
3. matched data plus pronunciation-aware frontend;
4. condition 3 plus unweighted tone loss;
5. condition 4 plus F0 loss where supported;
6. any contrast or risk-weighted extension as an optional ablation.

## Numerical requirements

- ignore padded units through masks;
- normalize by the sum of active weights, not batch size;
- return zero for a fully masked auxiliary batch rather than NaN;
- log each component before weighting;
- keep auxiliary coefficients outside the dataset annotations;
- validate gradient scale relative to the host model's base objective.

## Interpretation

This specification defines training signals, not an acoustic theory of all Yoruba surface prosody. Orthographic H/M/L labels should later be compared with context-conditioned surface-tone targets.
