# Yoruba voice benchmark preprocessing report

## Result

- Recordings processed: **120 of 120**
- Missing recordings: **none**
- Standardized audio: **mono, 24 kHz, 16-bit PCM WAV**
- Source audio duration: **536.4 seconds**
- Processed audio duration: **388.8 seconds**
- Processed duration range: **2.12-5.70 seconds per recording**
- Processed peak range: **-10.99 to -2.00 dBFS**
- Applied gain range: **-6.30 to +10.19 dB**
- Digital clipping after processing: **none**
- Orthographic tone annotation rows: **120**
- Provisional contrast groups: **17**
- Package validation: **PASS**

## Processing method

The original M4A files were preserved. Working copies were decoded, converted to mono 24 kHz PCM WAV, trimmed only at utterance edges using a -45 dBFS activity threshold with 200 milliseconds of retained padding, and normalized toward -23 dBFS active-speech RMS. Gain was bounded and output peaks were limited to -2 dBFS.

## Annotation method

The package contains Unicode-safe first-pass orthographic tone labels. Accented vowels receive H or L; unmarked vowels receive M. The parser explicitly recognizes the Yoruba vowels `ẹ` and `ọ`. These labels describe written tone and are not yet surface F0 measurements.

## Release limitations

- Transcript-to-audio correspondence has not yet been independently listening-verified.
- Contrast groups require final fluent-speaker or Yoruba-linguist review.
- A signed voice/data release should be obtained before public redistribution or commercial dataset release.
- This is a controlled single-speaker reference benchmark, not sufficient by itself to train a general-purpose Yoruba voice model.
