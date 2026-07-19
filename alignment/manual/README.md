# Manual alignment layer

Human corrections are append-only records stored separately from automatic
alignments. The review tool exports JSONL; import it with:

```powershell
..\work\omni-aligner-env\Scripts\python.exe scripts\import_manual_alignment_corrections.py <export.jsonl>
```

The importer validates prompt identity, reviewer status, duration limits, and
monotonic word boundaries. It never edits `alignment/automatic/`. A verified
training manifest should be built from the latest accepted manual record while
retaining the automatic record as provenance.

The same export/import workflow accepts `transcript_audio_mismatch` records.
These are stored separately in `dataset_item_issues.jsonl`, never as
verified alignments. A reviewer chooses either correction/re-alignment or
dataset exclusion. Pending corrections block finalization; exclusions are
listed explicitly in the final manifest and receive no training loss.

The generic `dataset_item_issues.jsonl` layer also records non-transcript
problems such as missing audio. YT0022 is represented there with
`issue_type=missing_audio` and `disposition=exclude_from_dataset`.
