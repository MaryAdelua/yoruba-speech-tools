# One-file acoustic measurements (Milestone 1)

This is an independent, offline signal analyzer. It does not call an LLM or infer
pronunciation from transcripts. Existing semantic evaluation is unchanged.

## Run from the repository root

```powershell
python -m venv .venv-acoustics
.\.venv-acoustics\Scripts\python.exe -m pip install -r requirements-acoustics.txt
.\.venv-acoustics\Scripts\python.exe scripts/analyze_audio.py work/voice_eval/incoming/assistant.wav --output-dir work/voice_eval/acoustics-001
.\.venv-acoustics\Scripts\python.exe -m unittest discover -s tests -p test_acoustic_analysis.py -v
```

Supply a new output directory for each run; existing result files are not overwritten.
The analyzer hashes the input before and after reading. Mono audio is required;
multichannel recordings are rejected rather than silently averaged. The existing
assistant.wav is already mono 24 kHz PCM, so no analysis copy is necessary.
Decoding to floating-point samples in memory changes no source bytes. There is no
resampling, gain adjustment, trimming, silence removal or denoising.

## Measurements and conventions

- librosa pYIN uses a configurable 65–500 Hz search range, 2048-sample window and
  10 ms hop by default. At 24 kHz this window spans 85.33 ms, so estimates overlap.
- Frame timestamps are window centers relative to the input clip. Pitch estimation
  uses zero padding at the edges; those frames are explicitly marked. A center at
  or beyond the recording end is excluded.
- CSV columns include timestamp, actual window bounds, edge-padding flag, raw F0,
  voiced decision, voicing probability, relative semitones, RMS and RMS dBFS.
- Unvoiced F0 and relative pitch are missing (blank CSV fields), never zero or
  interpolated. Voicing probability is the estimator's output, not confidence in
  linguistic accuracy. Unvoiced includes consonants, silence and tracking failures.
- RMS uses the same centered window, restricted to real samples at file edges.
  dBFS = 20 log10(RMS), with full-scale amplitude 1. Exact silence has RMS 0 and
  undefined/infinite-negative dBFS, serialized as null/blank, not a finite floor.
  These values are not calibrated sound-pressure level or perceived loudness.
- Relative pitch = 12 log2(F0 / median voiced F0 of this utterance). This provisional
  content-dependent baseline is documented in JSON. Raw Hz is retained. Neither
  representation assigns Yoruba H/M/L labels. Future speaker comparison requires
  aligned linguistic content and better speaker baselines.
- JSON summaries include duration, frame count, voiced percentage, median, minimum,
  maximum, max-minus-min range, and 5th/95th percentiles of voiced F0 estimates.
- PNG shows raw F0, relative semitones and a voiced/unvoiced strip over the full clip.
- Lexical-tone accuracy, pronunciation, prosody, fluency and overall speech scores
  always have status UNSCORED and null values.

## Existing recording provenance

The adjacent incoming/split_manifest.json maps assistant.wav to original recording
seconds 12.6–20.8. Add 12.6 to analyzer timestamps to locate them in the combined
recording. The split boundary was estimated automatically, not human-verified.
Source separation is upstream of this analyzer; no further splitting is performed.

## Scope of checks

Tests cover a 200 Hz sine, duration/timestamps, preservation, digital silence,
doubled amplitude (+6.0206 dB), invalid inputs, strict JSON, and artifact creation.
These are implementation checks, not validation of Yoruba tone detection. Search
limits, capture noise, short speech and octave tracking errors can affect estimates.
No cross-estimator comparison, reference alignment or scoring is implemented here.

## Milestone 2 instrument-validation runner

`scripts/validate_acoustic_measurements.py` adds an independent Praat raw
autocorrelation estimator through praat-parselmouth 0.4.7 (embedded Praat 6.1.38).
It does not change the Milestone 1 analyzer. This version does not claim to use
modern Praat filtered autocorrelation.

```powershell
.\.venv-acoustics\Scripts\python.exe scripts/validate_acoustic_measurements.py work/voice_eval/incoming/assistant.wav --output-dir work/voice_eval/measurement-validation-002
```

The runner is a recording-specific validation protocol: 0.8–1.9 seconds is the
provisional region being investigated, not an automatically discovered or verified
speech boundary. The recording-level regional summaries assume this 8.2-second
input. It preserves every measurement and adds flags without applying a confidence
cutoff. Nearest-frame pairing allows at most 5 ms offset and never interpolates
over unvoiced gaps. Native Praat timestamps and candidate strengths are retained.

Ten generated signals (six constant frequencies, silence, amplitude step, F0
step, short burst) are checked with both estimators. Steady-region acceptance is
at least 95% coverage, at most 50 cents p95 error, and zero false voiced frames
in steady digital silence. +/-100 ms around transitions is excluded from these
checks but preserved in CSV and separate boundary counts. Passing does not validate
boundary accuracy, natural-speech voicing, Yoruba tones or noise robustness.
The complete settings, thresholds, hashes and results are in validation.json.
