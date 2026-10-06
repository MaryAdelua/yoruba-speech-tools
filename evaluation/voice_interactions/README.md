# One-interaction voice evaluator, V0.1

This additive Python pipeline scores semantic correctness, task completion, and
Yoruba language adherence independently from 0–4. It uses a transcription API
and a structured LLM judge, not a human rating form or word-matching heuristic.
Scores are provisional until checked against native-speaker labels. Pronunciation,
tone realization, naturalness, internal speech recognition, and multi-turn
understanding are explicitly unscored. No overall score is calculated.

The development case is **one interaction**. Three draft response variants help
check that the judge distinguishes correct Yoruba, incorrect content, and correct
English. These are not three new interaction cases or proof of broad reliability.

## First real recording

Start a fresh voice conversation with your chosen product and say:

> Mo ní ọsàn mẹ́ta, mo sì ra méjì sí i. Ọsàn mélòó ni mo ní lápapọ̀? Dá mi lóhùn ní èdè Yorùbá nínú gbólóhùn kan.

Meaning: I have three oranges and buy two more. How many oranges do I have in
total? Answer in Yoruba in one sentence.

Confirm this script sounds natural and matches your intended meaning. Tell us
any correction before the run; the case is marked `reference_reviewed: false`
until confirmed. A possible correct answer is “O ní ọsàn márùn-ún lápapọ̀.”
Do not give that answer to the product, and do not record yourself impersonating
its reply. We need the reply it actually produces, including any English/errors.

Record BOTH sides of the same exchange, as two files:

- `user.wav`: your complete spoken request as delivered to the product.
- `assistant.wav`: the product's complete actual spoken response.

Preferred format: mono WAV, 16-bit PCM, 24 kHz. Other PCM sample rates and stereo
WAV are accepted. M4A and MP3 under 25 MB per file also work with the transcription
adapter; use the true extension, not a renamed file. Compressed audio does not
receive local waveform diagnostics in V0.1. Ordinary phone/computer recording
quality is sufficient; avoid music, overlapping voices, and clipped beginnings.
Record system audio for the assistant if possible. Do not normalize or clean up
its words. Keep about half a second of padding at either end.

If you can only capture one combined recording, retain it and provide the time
where the AI starts speaking. The first runner needs separately split files and
does not attempt diarization. Retain the original capture for provenance.

Place the files in `work/voice_eval/incoming/` under this repository. In this
workspace the exact location is:

`C:\Users\adelu\Documents\Codex\2026-10-01\i\outputs\yoruba-speech-tools\work\voice_eval\incoming`

Also provide product name, voice name if known, mode/version if shown, and capture
date. No private personal facts are needed for this test. After the first run,
check the two transcripts and give your own judgments on the three dimensions;
that validation is necessary to assess evaluator reliability, not to operate it.

## Run

Requires Python 3.10+; the new pipeline uses only the standard library and the
repository's existing Unicode word segmentation. No training environment, GPU,
model download, or extra Python package is needed for this API-backed version.

From the repository root:

```powershell
python -m unittest discover -s tests -p test_voice_eval.py -v

# Offline report plumbing only; the result clearly says fixture_replay.
python scripts/evaluate_interaction.py --replay evaluation/voice_interactions/replay_fixture.json --out work/voice_eval/replay-001.json

# Real audio: OPENAI_API_KEY must already be set in your local environment.
# Replace MODEL_ID with an accessible Responses model supporting Structured Outputs.
python scripts/evaluate_interaction.py --user-audio work/voice_eval/incoming/user.wav --assistant-audio work/voice_eval/incoming/assistant.wav --judge-model MODEL_ID --product "Product / voice / mode / date" --out work/voice_eval/run-001.json

# Three live scoring calls, no audio; preliminary validation of the same case.
python scripts/validate_voice_judge.py --judge-model MODEL_ID --out work/voice_eval/judge-check-001.json
```

Do not paste API keys into chat or save them in tracked files. The live provider
sends the two audio clips to OpenAI transcription and the resulting transcripts
plus case criteria to OpenAI's Responses API. Calls may incur API charges. The
judge request uses `store: false`; this is not a promise of zero service retention.
No audio is uploaded by the offline tests or replay mode. Nothing is sent to the
product being evaluated: this tool evaluates a capture you already made.

If `python` is not on PATH, this workstation's available interpreter is:

`C:\Users\adelu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

Use `& 'full-path-to-python.exe'` in place of `python` in PowerShell. The supplied
`run_voice_eval.ps1` launcher resolves Python on this workstation or through PATH:

```powershell
.\run_voice_eval.ps1 --replay evaluation/voice_interactions/replay_fixture.json --out work/voice_eval/replay-002.json
```

An optional `--transcripts file.json` mode accepts `{"user":"...","assistant":"..."}`
instead of audio and still runs the real judge. Reports explicitly label this
`text_only`, not an audio evaluation. This also permits comparison against manually
corrected transcripts without silently replacing the original ASR evidence.

## Interpretation and validation

- `provisional`: scored with reviewed reference and no flagged evidence problem;
  this still does not mean the evaluator is calibrated.
- `needs_review`: draft reference, request/transcript mismatch, uncertain judgment,
  audio-quality flag, or an unscorable dimension. Scores are conditional evidence.
- `not_evaluable`: missing transcript content, not automatically product failure.
- `fixture_replay_not_a_model_evaluation`: hand-authored values replayed offline.
- Provider errors fail the command with no fabricated scores. Existing report
  paths are refused before API calls; choose a fresh output filename each run.

The recognizer receives no reference answer, reference transcript, or forced
Yoruba language hint. This avoids steering an English reply into a Yoruba
transcription. Recognition accuracy for these recordings is unverified; language
or diacritic errors may originate in ASR. `request_match` checks evaluator evidence
against the reference and is NOT a product speech-understanding score. Responses
are data, not judge instructions. The local validator requires bounded scores
and exact quotes from the observed reply, but valid quotes do not prove the
judgment itself is correct.

The first validation sequence is: review the case, run the three draft response
variants through a live judge, record the actual interaction, inspect transcription
errors, and compare the automated scores with a fluent speaker's labels. Repeat
the same judge validation to observe instability before claiming reliability.
Do not tune repeatedly on protected training-experiment test IDs YT0028–YT0030.

## Existing work preserved

New evaluator code lives in `src/voice_eval/`, separate from the frozen pronunciation
and training workflows. Unicode segmentation reuses `yoruba_orthographic_units`.
Audio diagnostics follow the existing evaluator's RMS/clipping definitions but
do not import its CLI (which executes on import), impose a 24 kHz scoring rule,
or compare answer duration with the user's request. No legacy datasets or ratings
are regenerated. Local recordings, transcripts, and reports under `work/voice_eval/`
are ignored by Git.

API contracts checked against the official documentation:
- https://developers.openai.com/api/docs/guides/speech-to-text
- https://developers.openai.com/api/docs/guides/structured-outputs

The default transcription model is configurable through `--transcription-model`.
Choose the judge explicitly with `--judge-model`; the returned model ID, request
ID, usage, rubric hash, case hash, and audio hashes are retained in the report.
