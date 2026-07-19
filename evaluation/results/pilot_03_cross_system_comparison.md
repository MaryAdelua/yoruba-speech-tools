# Pilot 3 cross-system comparison

## Matched result

ChatGPT Voice and System S02 were tested with the same ten Yoruba prompts and the same fluent-speaker questions. Neither system was dependable. S02 produced more partially recognizable responses and one fully natural response, but exact transcript accuracy was essentially the same and low in both systems.

| Metric | ChatGPT Voice | System S02 | S02 difference |
|---|---:|---:|---:|
| Exact transcript match | 1/9 (11.1%) | 1/10 (10.0%) | −1.1 points |
| Partial transcript match | 5/9 (55.6%) | 8/10 (80.0%) | +24.4 points |
| Natural Yoruba pronunciation | 0/9 (0.0%) | 1/10 (10.0%) | +10.0 points |
| Tone correctness | 4/9 (44.4%) | 5/10 (50.0%) | +5.6 points |
| Strict meaning recovery | 3/9 (33.3%) | 4/10 (40.0%) | +6.7 points |
| No added speech | 9/9 (100.0%) | 10/10 (100.0%) | No difference |

ChatGPT has a denominator of nine because one extracted response was technically unusable. These differences are descriptive and are not evidence that one provider is generally superior.

## Shared failure pattern

Both systems followed the output-only instruction but struggled with Yoruba speech realization. Across them, pronunciation and tone errors affected words such as `yára`, `ife`, `ìlú` or `ìlù`, and `ilé ẹ̀kọ́`. The shared pattern supports moving from baseline collection to a technical intervention: a tone-aware pronunciation representation and prompting method tested against the same sentences.

## Next research stage

Stop adding unsupported general-purpose systems to the baseline. Develop the tone-aware intervention, then run an ordinary-text versus pronunciation-guided comparison. The key outcome is whether guidance improves exact wording, lexical-tone preservation, first-hearing meaning recovery, and naturalness within the same voice system.

