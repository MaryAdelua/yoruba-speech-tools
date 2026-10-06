# Approved paired AI pilot

Run 001 uses the six approved source texts in
`work/slr86/natural-baseline-001/qc-ingest-001/paired_sentence_proposals.json`.
Outputs are in `work/slr86/paired-ai-001/`; REPORT.txt documents the completed run.

Generation is explicitly gated by `--generate`:

```powershell
python scripts/generate_paired_ai.py --generate
python scripts/analyze_paired_ai.py
```

The first command issues twelve requests only when outputs are absent. Complete
matching cached requests are reused; ambiguous/failed requests require inspection
and do not silently retry. Never change configuration in place for a completed run.
Use a new run directory when changing texts, settings, model, voice or instruments.
The second command reuses hash-matched raw extraction, then regenerates summaries
and plots. No training code is invoked.

Model: OpenAI gpt-4o-mini-tts-2025-12-15. Voice: coral; version unavailable.
This one fixed configuration was selected after confirming account model access;
it is not an exhaustive sweep of catalog voices or a ChatGPT Voice capture.
Official reference: https://developers.openai.com/api/docs/guides/text-to-speech

Raw WAV response bytes, exact Unicode inputs, request settings, UTC timestamps,
request IDs and hashes are retained. API credentials are read only from the
environment and are not logged. Two separate calls per text support repeat
inspection, without promising independently controllable provider random seeds.

The existing pYIN/Praat pipeline is used at the original sample rate, with the
same physical window and hop durations. Frames retain F0, voicing, probabilities,
strength, dBFS, timestamps and uncertainty flags. Relative pitch for paired plots
uses each utterance's median per estimator, not another speaker's raw Hz target.
Plots preserve full recording times and do not impose syllable alignment.

The neutral listening page labels natural/AI provenance but never preferences.
Rebuild the structured form alone with `python scripts/build_paired_review.py`;
this verifies all 18 audio hashes and does not regenerate speech or acoustics.
Each AI take has independent tone, segmental, nasality, prosody, rhythm, overall
naturalness and confidence fields, optional issue tags, notes and bounded time
intervals. Natural references have separate notes and intervals. All ratings start
null; cannot determine is an explicit judgment. Per-record timestamps track edits,
and export also stores reviewer, sentence/source/generation IDs, exact text, audio
hashes, model snapshot and voice. The study is explicitly exploratory and unblinded.
Drafts autosave in browser local storage, keyed by the audio hashes. Use Export
Review JSON for a portable `paired_native_listener_review.json`; browser storage
can be cleared independently and is not a project-file backup. No combined score
is produced and annotations are not used for training. Serializer tests run with
`node tests/test_paired_review.js`.
Raw playback has no level matching;
recording-channel differences remain a confound. Every requested correctness
dimension remains UNIMPLEMENTED with a null value.

## Exploratory human/acoustic join

`python scripts/explore_human_acoustics.py <exported-review.json>` validates all
six sentence IDs, twelve generation IDs, exact text, provenance, rating enums and
audio hashes before saving a separate `human-acoustic-001` analysis directory.
The original review remains byte-identical. Existing audio and measurements are
read only. A different review requires a new analysis directory/version.

Outputs include full nested and flat joins, six-row wide paired measurements,
18-row recording descriptors, generation/category/tag counts, repeat comparisons,
dimension-specific group summaries, and two plots. Relative contours use ten
equal fractional-duration bins with missing bins retained. This is a coarse
descriptive probe, not linguistic alignment or a tone score. Unvoiced run timing
is not pause timing; detection failures and unvoiced consonants remain confounds.
Screened-bin sensitivity uses the existing engineering reliability mask.

No ratings are recoded into numerical scores; no correlation tests, fitted models,
nasality/F0 associations, training, new generation or composite metrics occur.
Zero-variance dimensions are explicitly marked NO_RATING_VARIATION. All confidence
entries in the first export are low and remain low. Absent optional tags/notes do
not become negative judgments. Source scripts/configurations, package versions and
input hashes are saved in versions/ and reproducibility.json. The narrative
interpretation and next-experiment decision are in REPORT.txt.

Run the targeted descriptor tests with
`python -m unittest tests.test_human_acoustics -v`.
