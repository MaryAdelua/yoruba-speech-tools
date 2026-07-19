# System S02 Pilot 3 benchmark report

## Result

System S02 produced limited Yoruba capability but was not dependable. Of ten responses, only one exactly matched the intended words and only one sounded naturally pronounced. Five received a correct tone judgment, while four clearly preserved the intended meaning.

Unlike the ChatGPT capture, all ten S02 responses were technically usable.

## Benchmark metrics

| Metric | Result | Interpretation |
|---|---:|---|
| Usable extracted responses | 10/10 (100.0%) | Every requested output was evaluable |
| Exact transcript match | 1/10 (10.0%) | Every intended word was judged present |
| Partial transcript match | 8/10 (80.0%) | Some but not all intended content was realized |
| No transcript match | 1/10 (10.0%) | Intended wording was not adequately realized |
| No added speech | 10/10 (100.0%) | Every output followed the “say nothing else” instruction |
| Natural Yoruba pronunciation | 1/10 (10.0%) | Only `0162` sounded natural |
| Tone correctness | 5/10 (50.0%) | Fluent-speaker utterance-level judgment |
| Strict meaning recovery | 4/10 (40.0%) | “Unsure” is treated as unsuccessful recovery |
| Meaning definitely not recovered | 4/10 (40.0%) | Intended meaning was judged absent |
| Meaning uncertain | 2/10 (20.0%) | Listener could not confidently recover meaning |

## Item-level findings

| ID | Transcript | Natural | Tone | Meaning | Main finding |
|---|---|---|---|---|---|
| 0161 | Partial | No | No | No | Incomplete or incorrect realization changed the result |
| 0162 | Yes | Yes | Yes | Yes | The only fully successful response |
| 0163 | Partial | No | Yes | Yes | Meaning and tone survived despite incomplete wording and unnatural speech |
| 0164 | Partial | No | No | Unsure | Error around `náà mọ́` weakened meaning recovery |
| 0165 | Partial | No | No | No | `Yára dé síbí` was pronounced incorrectly |
| 0169 | Partial | No | No | No | Pronunciation failure prevented meaning recovery |
| 0170 | No | No | No | No | Pronunciation and content failed |
| 0191 | Partial | No | Yes | Unsure | Tone was acceptable, but pronunciation around `náà` weakened meaning |
| 0192 | Partial | No | Yes | Yes | Meaning survived despite an error around `ìlù` |
| 0144 | Partial | No | Yes | Yes | Meaning survived despite an error around `ilé ẹ̀kọ́` |

## Interpretation

S02 often produced recognizable fragments: eight responses were rated partial rather than completely wrong. However, recognizable fragments did not amount to reliable Yoruba speech. Only one sentence was exact and natural. The results also show why transcript, tone, meaning, and naturalness must remain separate: several utterances preserved tone or meaning despite incomplete wording and unnatural pronunciation.

## Limitations

This is a diagnostic pilot with ten sentences, one voice configuration, and one fluent Yoruba evaluator who knew the target text. Tone correctness is an utterance-level human judgment, not syllable-level acoustic scoring. Publication-quality claims require more items, blinded randomized presentation, and multiple independent fluent Yoruba raters.

