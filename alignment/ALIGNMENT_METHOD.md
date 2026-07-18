# Yoruba Alignment v0.1

## Completed alignment

All 120 processed WAV files have exact utterance-level boundaries. Each begins at 0.000 seconds and ends at the WAV duration after conservative edge-silence trimming.

The package also contains a Unicode-safe inventory of every word and orthographic vowel nucleus, including its H/M/L target and character offsets. Word and vowel timestamps are intentionally `null` until a Yoruba-capable acoustic alignment is run and reviewed.

## Why lower-level timestamps are pending

An English forced aligner is not valid for Yoruba. Meta's `facebook/mms-1b-all` ASR model supports 1,100+ languages and provides language adapters, while PyTorch documents CTC forced alignment for multilingual speech. However, the MMS 1B checkpoint is approximately 3.86 GB, requires substantial inference resources, and is licensed CC-BY-NC 4.0. This project is intended for commercial adoption, so no MMS-derived boundaries are included in the benchmark release without a separate licensing decision.

Primary references:

- https://huggingface.co/facebook/mms-1b-all
- https://docs.pytorch.org/audio/2.1.0/tutorials/forced_alignment_for_multilingual_data_tutorial.html

## Listening-verification gate

Use `listening_verification_queue.csv` with the audio in the benchmark package. The fluent speaker or another qualified Yoruba listener should mark:

1. whether the recording matches the transcript;
2. whether every word is present;
3. whether the pronunciation sounds natural;
4. any correction or recording problem.

Priority 0 is an acoustic-coverage flag, priority 1 contains controlled contrast items, and priority 2 contains the remaining coverage sentences.

## Next defensible alignment options

1. Run a commercially compatible Yoruba CTC/phoneme aligner once an appropriate checkpoint and license are verified.
2. Use manual Praat alignment for the controlled contrast words first, followed by vowel-nucleus review against the F0 tracks.
3. Keep automatically proposed boundaries separate from manually accepted boundaries and report alignment confidence/failure rates.

Do not compute Syllable Tone Error Rate until vowel-nucleus boundaries have been acoustically assigned and reviewed.
