# Natural SLR86 baseline

Run from the repository root with the acoustic/import dependencies installed:

```powershell
python scripts/build_natural_baseline.py --prepare-only
python scripts/build_natural_baseline.py
python scripts/audit_natural_baseline.py
python -m unittest tests.test_natural_baseline -v
```

Outputs: `work/slr86/natural-baseline-001/`. Source WAVs and import records remain
unchanged. Existing per-clip raw extraction is reused only when its source hash
matches. If changing estimator settings or code, use a new output directory/run
identifier rather than reusing this cache. Summary products are regenerated.

## Listening QC

Seed 860220; choose one random clip per speaker from sorted pools, add both unusual
Unicode cases, global duration extremes and explicit-mark-density extremes, then
fill to 20 from least represented speakers using the same seeded RNG. Exact IDs,
source hashes, reasons and text are in qc_sample.json. Low explicit mark density
does not prove incompleteness. Sample coverage includes e/ẹ, o/ọ and nasal spelling
environments. Unicode/transcript flags are not linguistic mismatch findings.

Open qc_review.html in a browser. Audio URLs point to unchanged neighboring WAVs.
Select transcript matches audio, minor uncertainty, mismatch, or cannot determine;
leave unreviewed items pending. Confidence and notes/time intervals are optional.
Export JSON before closing; fields are not automatically persisted. Exported human
reviews are separate evidence; scripts do not silently import them or correct text.
The automation has not performed native linguistic listening verification. Playback
functionality was tested independently. Only 20 reviews are requested, not all 120.

## Instruments and baselines

pYIN calls the existing analyzer at original 48 kHz, with 4096-sample windows
(85.33 ms, matching prior 2048/24 kHz validation), 10 ms hop, 65–500 Hz range.
No denoising, gain changes, silence removal, resampling or signal filtering occurs.
Praat uses the previously validated raw autocorrelation settings. Its native grid
is retained and matched to pYIN centers within 5 ms without interpolation.

Per-frame CSVs retain raw F0, pYIN probability, Praat candidate strength, RMS/dBFS,
timestamps/window bounds, unvoiced/missing status, relative pitch and flags. Raw
Praat CSVs retain native time centers. Timing intervals describe contiguous voiced
frame cells, not syllables, pauses, or confirmed speech boundaries.

Normalize each estimator separately with `12*log2(F0 / speaker pooled voiced-frame
median)` across that speaker's ten clips. Longer voiced recordings carry more
weight. The original clip-relative representation and raw Hz remain available.
Quantiles, population SD and clip-median distributions describe within/between
speaker variation. None defines a standard speaker or correct tone range.

Flags: pYIN probability below 0.5; search-limit proximity within 5%; padded edge;
voicing disagreement; pitch difference >1 semitone; octave-like difference 11–13
semitones. A separate agreement screen requires both voiced, pYIN probability
>=0.5, Praat strength >=0.45, difference <=0.5 semitone, and no flags. These are
engineering inspection thresholds, not calibrated confidence. Screened sensitivity
summaries do not replace unfiltered baseline distributions or remove raw frames.

## Limits and future work

All transcripts remain source-provided/unreviewed. Two unusual-underdot items need
additional review; the other 118 are uncertain, with zero confirmed lexical-tone
targets. A >=70% explicit-vowel-mark density merely prioritizes 42 candidates for
review. It does not establish tone completeness; unmarked mid tones and syllabic
nasals need linguistic treatment. No marks are restored.

Feature-linked natural_reference records preserve all UNSCORED targets and expose
planned, not-implemented nasality artifacts. Future A1-P0/A1-P1, F1 bandwidth,
spectral tilt and segment trajectories need reliable segment/vowel context, signal
quality, speaker controls and perceptual validation. They have not been measured
or interpreted here. F0 alone cannot diagnose nasal realization.

The read-speech pilot is small, contains tracking uncertainty and differs from
conversational AI speech. Natural distributions are descriptive, not correctness
boundaries. Native QC, flagged-measurement review and user approval of paired text
remain gates before any new AI recording generation.
