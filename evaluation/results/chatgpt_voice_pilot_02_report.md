# ChatGPT Voice Pilot 2 benchmark report

## Result

ChatGPT Voice did not produce dependable Yoruba speech on this ten-sentence pilot. Of the nine responses that could be evaluated, only three contained the complete intended words, three preserved the intended tone judgment, and three clearly conveyed the intended meaning. None sounded like natural Yoruba pronunciation to the fluent-speaker evaluator.

One response, `0108`, is excluded from model-performance denominators because the extracted clip was cut off and did not contain an evaluable ChatGPT voice response.

## Benchmark metrics

| Metric | Result | Interpretation |
|---|---:|---|
| Usable extracted responses | 9/10 (90.0%) | One technical extraction failure |
| Exact transcript match | 3/9 (33.3%) | All intended words spoken, with no additions or omissions |
| No added speech | 9/9 (100.0%) | The model followed the “say nothing else” instruction on every scorable response |
| Natural Yoruba pronunciation | 0/9 (0.0%) | No scorable response sounded naturally pronounced |
| Tone correctness | 3/9 (33.3%) | Fluent-speaker utterance-level judgment |
| Strict meaning recovery | 3/9 (33.3%) | “Unsure” is treated as unsuccessful recovery |
| Meaning definitely not recovered | 4/9 (44.4%) | Intended meaning was judged absent |
| Meaning uncertain | 2/9 (22.2%) | Listener could not confidently recover the meaning |

For a conservative all-prompts analysis, exact transcript match and strict meaning recovery were both 3/10 (30.0%). This includes the technical failure as unsuccessful. The scorable-response figures above are better measures of the voice model itself.

## Item-level findings

| ID | Transcript | Natural | Tone | Meaning | Main finding |
|---|---|---|---|---|---|
| 0101 | No | No | No | No | Omitted “òpópónà”; tone changed meaning; sentence unfinished |
| 0102 | No | No | No | No | Produced different-sounding words and a different meaning |
| 0103 | No | No | No | No | Pronunciation and word realization did not convey the full sentence |
| 0104 | No | No | No | Unsure | “Oko” (farm) was not properly pronounced; accent did not sound Yoruba |
| 0105 | Yes | No | Yes | Yes | Content survived, but accent and pronunciation remained poor |
| 0106 | Yes | No | Yes | Yes | Content survived, but pronunciation was difficult on first hearing |
| 0107 | No | No | No | Unsure | “Ìgbà” lost its initial consonant; “wo” sounded like “wu” |
| 0108 | No | N/A | N/A | Unsure | Technical extraction failure; exclude from model scoring |
| 0142 | No | No | No | No | “Tuntun” was incorrect and the intended meaning was not conveyed |
| 0143 | Yes | No | Yes | Yes | Words and meaning survived, but intonation and pronunciation were unnatural |

## Error pattern

The strongest pattern is not instruction-following failure: ChatGPT added no extra speech in the nine scorable cases. The weakness is speech realization. Segmental substitutions, omitted material, non-Yoruba accent, and incorrect tone or intonation often caused lexical or sentence meaning to become uncertain or wrong.

The three content-success cases (`0105`, `0106`, and `0143`) are also informative. They show that correct text realization and recoverable meaning do not guarantee natural Yoruba speech. A useful training objective therefore needs separate losses or evaluation targets for:

1. complete phoneme and word realization;
2. Yoruba vowel and consonant contrasts;
3. lexical-tone preservation;
4. sentence-level intonation;
5. fluent-speaker naturalness and first-hearing intelligibility.

## Recommended model-development use

- Use contrastive Yoruba recordings that isolate tone and segmental minimal contrasts, not text-audio pairs alone.
- Add a tone-aware pronunciation representation to the speech generator and preserve tone-bearing units during alignment.
- Penalize word omissions and segmental substitutions separately from tone errors.
- Include first-hearing meaning recovery as a human evaluation outcome; intelligibility can fail even when a transcript appears correct.
- Use fluent Yoruba listeners during model selection, with separate ratings for transcript, tone, meaning, and naturalness.
- Retain failed outputs as hard-negative training or diagnostic examples, especially `0101`, `0102`, `0103`, `0104`, `0107`, and `0142`.

## Scope and limitations

This is a diagnostic pilot, not a population estimate. It contains ten prompts, four controlled contrast families, one ChatGPT voice configuration, and one fluent Yoruba evaluator who knew the target sentences. Tone correctness is a human utterance-level judgment, not a syllable-level acoustic tone error rate. Publication-quality claims require more sentences, multiple voices or systems, randomized blinded presentation, and at least two independent fluent Yoruba raters.

