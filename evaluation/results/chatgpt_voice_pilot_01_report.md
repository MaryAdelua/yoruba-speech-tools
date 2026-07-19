# ChatGPT Voice pilot 01 benchmark report

**Evaluation date:** 18 July 2026  
**System:** ChatGPT Voice  
**Voice, mode, and account plan:** not recorded  
**Pilot size:** 10 controlled Yoruba sentences  
**Contrast families:** `oko`, `owo`, `igba`, and `ẹkọ`

## Result

ChatGPT Voice did not produce any of the ten requested Yoruba sentences. Pause-based segmentation found 11 spoken chunks, and the fluent Yoruba reviewer classified every chunk as extra speech rather than one of the expected sentences.

This is an **end-to-end task and instruction-adherence failure**. It is not scored as a lexical-tone realization failure because none of the intended items was available for tone evaluation.

## Scores

| Outcome | Result |
|---|---:|
| Requested items | 10 |
| Recognizable requested items produced | 0 |
| Target coverage | 0% |
| Exact transcript matches | 0/10 |
| Extra spoken chunks | 11 |
| End-to-end task success | 0/10 |
| Meaning recovery for requested items | 0/10 by non-production |
| Tone Contrast Preservation Accuracy | Not scorable |
| Syllable Tone Error Rate | Not scorable |
| Naturalness MOS | Not rated |

The `0/10` meaning-recovery result is an end-to-end system score: a listener cannot recover the requested meaning when the requested utterance is absent. It does not assert that the extra speech was unintelligible.

## Capture and segmentation findings

- Source format: Microsoft Game DVR MP4, AAC audio at 48 kHz stereo.
- Source duration: 52.64 seconds.
- Standardized analysis audio: mono, 24 kHz, 16-bit PCM.
- Main spoken region: approximately 10.94–42.68 seconds.
- Detected spoken chunks: 11.
- Combined chunk duration: 23.50 seconds.
- Chunk duration range: 1.53–3.13 seconds.
- Clipped samples: 0% in every chunk.

The capture itself was usable. The failure is therefore not explained by a missing or corrupted audio track.

## Interpretation

The pilot establishes that this ChatGPT Voice run failed before pronunciation comparison: it did not follow the request to speak the supplied Yoruba sentences exactly. Because the system output cannot be aligned to the ten prompt IDs, reference-duration differences, F0-contour differences, lexical-tone accuracy, and controlled contrast preservation cannot be computed responsibly.

This distinction matters. Reporting a tone error rate here would misattribute a generation or instruction-following failure to the acoustic realization of Yoruba tone.

## Limitations

1. The ChatGPT voice name, Voice mode, account plan, and underlying model were not recorded.
2. One continuous ten-sentence request was used. The failure may differ when sentences are requested one at a time.
3. A single fluent Yoruba speaker performed the mapping review.
4. The content of the 11 extra chunks was labeled only as extra, not transcribed.
5. This pilot is one recorded run and must not be generalized to every ChatGPT voice configuration.

## Required follow-up

Run a second ChatGPT pilot with **one Yoruba sentence per turn**, using the same fixed voice and mode. Record the voice name, mode, account plan, and date. This will separate list-level instruction failure from the system's ability to pronounce an individual Yoruba sentence.
