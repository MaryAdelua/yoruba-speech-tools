# Omnilingual CTC alignment

## Purpose and authority

This layer supplies acoustically derived boundary estimates for the 30-item
Yoruba pronunciation batch. It does not replace the verified transcript,
pronunciation annotation, or a fluent speaker's judgment. Automatic output is
always labeled `requires_human_verification`; manual corrections live in a
separate append-only layer.

## Backend

Native `omnilingual-asr` depends on Fairseq2 and currently lacks a practical
native-Windows wheel path. This project therefore runs the same Omnilingual ASR
300M CTC model through the Sherpa-ONNX Windows CPU runtime. The pinned model is
`csukuangfj/sherpa-onnx-omnilingual-asr-1600-languages-300M-ctc-int8-2025-11-12`.
Model and token-file SHA-256 values are recorded in the generated summary. The
downloaded model is working material and is excluded from Git; its Apache-2.0
license is retained beside it.

## Method

1. Decode each waveform with Omnilingual ASR CTC and retain character-token
   timestamps.
2. Normalize the verified transcript to NFC, lowercase only for matching, and
   retain a reversible normalized-character-to-original-span map. Tone marks,
   underdots, capitalization, and punctuation remain unchanged in `text_nfc`.
3. Minimum-edit align decoded characters to verified reference characters.
4. Project matched acoustic timestamps to words and syllables. Unmatched
   syllables may be interpolated only inside an acoustically supported word and
   are explicitly labeled `within_word_interpolation`; unresolved units remain
   null.
5. Report confidence as exact matched reference characters divided by reference
   characters. This is a transparent matching diagnostic, not a calibrated
   probability.

## Reproduce

```powershell
py -3 -m venv ..\work\omni-aligner-env
..\work\omni-aligner-env\Scripts\pip.exe install sherpa-onnx==1.13.4 soundfile numpy huggingface_hub
..\work\omni-aligner-env\Scripts\python.exe scripts\run_omnilingual_ctc_alignment.py
..\work\omni-aligner-env\Scripts\python.exe scripts\build_omnilingual_alignment_review.py
```

Download the model repository above into
`work/models/omnilingual-asr-ctc-300m-int8/` before running. Regeneration
refuses to overwrite the automatic file unless `--overwrite` is explicit.

## Review and export

Open `alignment/review/yoruba-alignment-review.html`, listen, drag boundary
lines or edit numeric times, and mark an item human-verified. Exported JSONL is
validated and appended with `scripts/import_manual_alignment_corrections.py`.
Only imported human-verified records are eligible for a verified training
manifest. Low-confidence records must receive special attention; confidence is
not an acceptance rule.

The reviewer saves progress automatically in browser storage, resumes at the
next pending item, displays all 30 states, accepts prior JSONL exports or a
progress backup, and exports only new or changed verified records. An exact
record cannot be exported twice in one review state, and the importer also
deduplicates identical prompt/boundary content independently of timestamps.

After importing each exported batch, rebuild the reviewer so repository-level
progress is embedded:

```powershell
..\work\omni-aligner-env\Scripts\python.exe scripts\import_manual_alignment_corrections.py <export.jsonl>
..\work\omni-aligner-env\Scripts\python.exe scripts\build_omnilingual_alignment_review.py
```

When all 30 are present, create the downstream dataset and checksum manifest:

```powershell
..\work\omni-aligner-env\Scripts\python.exe scripts\finalize_verified_alignments.py
```

Finalization fails closed if even one prompt is missing or invalid. The first
legacy export covered the word-boundary reviewer; its syllable timing loss is
masked in the final dataset unless it is re-reviewed with the current
word-and-syllable interface.

## Structural boundary repair

The raw CTC projection is preserved as
`alignment/automatic/omnilingual_ctc_training_batch_01.raw.jsonl`. A separate
conservative repair pass makes the review suggestions structurally editable:

- CTC token timestamps include short left/right padding. Independently
  projected adjacent words or syllables can therefore overlap by a few frames.
- Repeated or shared graphemes can map more than one syllable to intersecting
  token spans.
- Low-confidence reference matches leave some units unresolved (`null`).
- Rounding at the waveform endpoint can place the final boundary fractionally
  beyond the recorded duration.

The repair clamps only out-of-range endpoints, splits an overlap at its
midpoint, and proportionally initializes missing intervals. Every changed field
is retained in `omnilingual_ctc_boundary_repair_audit.jsonl`. These are
automatic structural repairs, not linguistic or human-verified corrections.

The original word tokenizer was subsequently replaced because the generic
word-character regular expression treated decomposed Yoruba tone marks as word
terminators. The current tokenizer explicitly retains Unicode combining marks,
apostrophes, and internal hyphens and derives units from the authoritative NFC
transcript. Twenty-three affected records were rebuilt using the already saved
CTC token timestamps. See `automatic/UNICODE_WORD_SEGMENTATION_REPORT.md` and
`automatic/unicode_word_segmentation_audit.jsonl`.

## Transcript/audio mismatch policy

Boundary review must stop when the recording says different words from the
displayed transcript. The reviewer provides a dedicated mismatch action that
captures the expected and observed NFC text and selects either
`corrected_transcript_pending_realignment` or `exclude_from_dataset`. Such an
item is skipped by the boundary queue without being marked verified. The first
disposition blocks finalization until the authoritative transcript and acoustic
alignment are rebuilt; the second is omitted and disclosed in the final
manifest.

YT0013 exposed a malformed CSV row: the Yoruba continuation had shifted into
the English field. The speaker-confirmed full transcript is now `Ẹ jọ̀wọ́, dín
ohun náà kù.`. Its metadata and acoustic alignment were rebuilt while the
original discrepancy remains in
`dataset/corrections/transcript_audio_mismatches.jsonl`.

## Audio-ID mapping correction

A speaker-led audit localized a one-position offset to YT0018–YT0022. The
pre-fix YT0018 contains the same utterance content as YT0017 but is not a
byte-identical file. Pre-fix YT0019 belongs to YT0018, YT0020 to YT0019,
YT0021 to YT0020, and YT0022 to YT0021. No recording for the YT0022 transcript
was found; YT0023 onward returns to the correct sequence.

The corrected active mapping reuses those source recordings for YT0018–YT0021,
re-runs their acoustic alignment, and excludes YT0022 as missing audio. Original
files and alignments are retained under `work/training_batch_01_mapping_pre_fix_2026-07-19`
and `automatic/omnilingual_ctc_training_batch_01.pre_audio_mapping_fix.jsonl`.
The machine-readable evidence and hashes are in
`dataset/corrections/audio_mapping_audit_yt0017_yt0023.json`.

The review application preserves completed work outside the affected range.
Because old boundary verification for YT0018–YT0022 referred to the wrong
waveforms, those five local states are intentionally invalidated; YT0018–YT0021
must be reviewed against their corrected audio, while YT0022 is automatically
tracked as an excluded missing-audio item.

## Integration contract

Speech-model developers receive immutable NFC Yoruba text, original audio,
automatic acoustic evidence, verified word/syllable times, confidence and
provenance fields, and orthographic pronunciation/tone annotations. Loaders
should prefer a latest accepted manual record, fall back to automatic estimates
only for exploratory use, and mask unresolved or unverified timing losses.
