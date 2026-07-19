# Concise tone-aware intervention report

## Research question

Does adding a short HIGH/MID/LOW cue and English meaning for the sentence's meaning-critical Yoruba word improve ChatGPT Voice relative to the same voice reading the same sentence from ordinary text?

## Intervention

The ordinary ChatGPT Pilot 3 served as the baseline. The intervention retained each target sentence but added one concise functional-load cue, for example:

> Say exactly: “Yàrá náà mọ́.” Cue: Yàrá is LOW-HIGH and means room. Nothing else.

The first feasibility version used a full sentence-wide tone plan. It caused truncation and incomplete outputs, so it was rejected before pronunciation evaluation. The concise version used 14–17 word prompts and produced ten usable outputs.

## Guided-condition results

| Metric | Result |
|---|---:|
| Usable guided responses | 10/10 (100.0%) |
| Exact transcript match | 1/10 (10.0%) |
| Partial transcript match | 5/10 (50.0%) |
| No transcript match | 4/10 (40.0%) |
| No added speech | 10/10 (100.0%) |
| Natural Yoruba pronunciation | 0/10 (0.0%) |
| Tone correctness | 4/10 (40.0%) |
| Strict meaning recovery | 2/10 (20.0%) |
| Meaning definitely not recovered | 4/10 (40.0%) |
| Meaning uncertain | 4/10 (40.0%) |

## Matched A/B comparison

Response `0163` is excluded from the paired comparison because its baseline ChatGPT clip was technically unusable. Nine sentences therefore have valid ratings under both conditions.

| Metric | Ordinary-text baseline | Concise tone guidance | Change |
|---|---:|---:|---:|
| Exact transcript match | 1/9 (11.1%) | 1/9 (11.1%) | 0.0 points |
| Partial transcript match | 5/9 (55.6%) | 4/9 (44.4%) | −11.1 points |
| Natural Yoruba pronunciation | 0/9 (0.0%) | 0/9 (0.0%) | 0.0 points |
| Tone correctness | 4/9 (44.4%) | 4/9 (44.4%) | 0.0 points |
| Strict meaning recovery | 3/9 (33.3%) | 2/9 (22.2%) | −11.1 points |
| No added speech | 9/9 (100.0%) | 9/9 (100.0%) | 0.0 points |

## Item-level movement

- `0161` improved from incorrect tone and unrecovered meaning to correct tone and recovered meaning.
- `0162` improved from a partial to an exact transcript while retaining tone and meaning success.
- `0169` regressed from exact wording and recovered meaning to partial wording and uncertain meaning.
- `0191` regressed from correct tone and uncertain meaning to incorrect tone and unrecovered meaning.
- `0144` retained a correct tone judgment but regressed from recovered to uncertain meaning.
- The remaining paired items showed no categorical improvement in the primary outcomes.

The intervention moved which items succeeded rather than improving aggregate performance.

## Conclusion

The concise functional-load cue **did not improve ChatGPT Voice on this pilot**. In the matched analysis, exact transcript accuracy, tone correctness, and naturalness were unchanged. Strict meaning recovery decreased by 11.1 percentage points.

This is a useful null result. Explicit textual tone labels are understood well enough to help isolated items, but they do not reliably control the acoustic realization of Yoruba speech in this black-box voice system. Prompt engineering alone is therefore not supported as the solution.

The result strengthens the case for architecture-level intervention: explicit tone-bearing-unit supervision, pitch-contour objectives, functional-load weighting, and meaning-sensitive model selection during TTS training.

## What developers can use

1. The concise prompts provide a reproducible black-box control experiment.
2. The item-level results identify both gains and regressions, preventing selective reporting.
3. The long-prompt feasibility failure shows that control representations must be compatible with real-time voice interfaces.
4. The null aggregate effect establishes a baseline that a trainable tone-aware model must exceed.
5. The paired benchmark separates transcript, tone, meaning, and naturalness rather than treating pronunciation as one undifferentiated score.

## Limitations

This pilot contains nine valid matched pairs, one ChatGPT voice configuration, one prompt order, and one fluent Yoruba evaluator who knew the target sentence and condition. The comparison is not randomized or blinded, and no inferential significance claim is justified. A stronger study should use multiple generations per item, randomized condition order, blinded playback, independent fluent speakers, and a trainable open TTS baseline.

## Decision

Do not continue tuning black-box prompts on the same ten items. Preserve this as a null prompting result and move to the model-development contribution: implement the functional-load-weighted tone objective on an open Yoruba TTS baseline when suitable training data and compute are available.

