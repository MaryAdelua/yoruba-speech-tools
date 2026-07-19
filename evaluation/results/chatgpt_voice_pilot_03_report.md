# ChatGPT Voice Pilot 3 benchmark report

## Result

ChatGPT Voice remained unreliable for natural and meaning-preserving Yoruba speech. Among nine scorable responses, only one exactly matched the intended words, four received a correct tone judgment, and three clearly preserved the intended meaning. None sounded naturally pronounced to the fluent Yoruba evaluator.

Response `0163` is excluded from model-performance denominators because the extracted clip did not contain an evaluable ChatGPT voice response.

## Pilot 3 metrics

| Metric | Result | Interpretation |
|---|---:|---|
| Usable extracted responses | 9/10 (90.0%) | One technical extraction failure |
| Exact transcript match | 1/9 (11.1%) | Every intended word was judged present |
| Partial transcript match | 5/9 (55.6%) | Some but not all intended content was realized |
| No transcript match | 3/9 (33.3%) | Intended wording was not adequately realized |
| No added speech | 9/9 (100.0%) | No scorable response contained unwanted speech |
| Natural Yoruba pronunciation | 0/9 (0.0%) | Every scorable response sounded unnatural |
| Tone correctness | 4/9 (44.4%) | Fluent-speaker utterance-level judgment |
| Strict meaning recovery | 3/9 (33.3%) | “Unsure” is treated as unsuccessful recovery |
| Meaning definitely not recovered | 4/9 (44.4%) | Intended meaning was judged absent |
| Meaning uncertain | 2/9 (22.2%) | Listener could not confidently recover meaning |

In the conservative all-prompts analysis, exact transcript match was 1/10 (10.0%), tone correctness was 4/10 (40.0%), and strict meaning recovery was 3/10 (30.0%).

## Comparison with Pilot 2

| Metric | Pilot 2 | Pilot 3 | Change |
|---|---:|---:|---:|
| Exact transcript match | 3/9 (33.3%) | 1/9 (11.1%) | −22.2 percentage points |
| Natural Yoruba pronunciation | 0/9 (0.0%) | 0/9 (0.0%) | No change |
| Tone correctness | 3/9 (33.3%) | 4/9 (44.4%) | +11.1 percentage points |
| Strict meaning recovery | 3/9 (33.3%) | 3/9 (33.3%) | No change |
| No added speech | 9/9 (100.0%) | 9/9 (100.0%) | No change |

Pilot 3 had fewer exact transcripts but slightly more positive tone judgments. Meaning recovery and naturalness did not improve. Because each pilot has only nine scorable responses, these differences are descriptive rather than statistically reliable.

## Combined ChatGPT results

Across Pilots 2 and 3, 18 responses were scorable:

- exact transcript match: 4/18 (22.2%);
- natural Yoruba pronunciation: 0/18 (0.0%);
- tone correctness: 7/18 (38.9%);
- strict meaning recovery: 6/18 (33.3%);
- no added speech: 18/18 (100.0%).

The combined result shows strong instruction following but poor Yoruba voice realization. Most responses contained incomplete or incorrect word realizations, and none achieved natural Yoruba pronunciation.

## Item-level findings

| ID | Transcript | Natural | Tone | Meaning | Main finding |
|---|---|---|---|---|---|
| 0161 | No | No | No | No | Pronunciation was wrong |
| 0162 | Partial | No | Yes | Yes | Meaning survived despite a pronunciation error |
| 0163 | N/A | N/A | N/A | N/A | Technical extraction failure; excluded from model scoring |
| 0164 | Partial | No | No | No | Only `Yàrá` was pronounced properly |
| 0165 | Partial | No | No | Unsure | `Dé síbí` was improperly pronounced |
| 0169 | Yes | No | Yes | Yes | The only exact transcript; pronunciation remained unnatural |
| 0170 | No | No | No | No | Pronunciation failed, especially `ife náà` |
| 0191 | Partial | No | Yes | Unsure | `Ìlú` was not pronounced well |
| 0192 | No | No | No | No | Pronunciation and intonation failed |
| 0144 | Partial | No | Yes | Yes | `Ilé ẹ̀kọ́` was pronounced incorrectly |

## Research implications

Pilot 3 reinforces that transcript-level generation is not enough for Yoruba voice quality. Even responses whose tones or meanings were judged successful frequently contained audible pronunciation errors. Training and model selection should therefore separately evaluate word completeness, segmental pronunciation, lexical tone, sentence intonation, first-hearing meaning recovery, and fluent-speaker naturalness.

The next benchmark stage should run the identical Pilot 3 prompts on other voice systems. Recordings should be assigned anonymous system codes before human review, with the same questions and denominator rules retained for direct comparison.

## Limitations

This is a diagnostic study with ten prompts, one voice configuration, one fluent Yoruba evaluator, and one unusable extraction. The evaluator knew the target text. Publication-quality claims require blinded randomized playback, more items, multiple voice systems, and at least two independent fluent Yoruba raters.

