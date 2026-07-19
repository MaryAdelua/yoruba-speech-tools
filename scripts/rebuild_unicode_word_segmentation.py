"""Rebuild automatic units with Unicode-safe Yoruba orthographic boundaries."""

from __future__ import annotations

import csv
import json
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from alignment_repair import interval_errors, repair_alignment  # noqa: E402
from omnilingual_alignment import build_alignment  # noqa: E402
from yoruba_orthographic_units import words_and_syllables  # noqa: E402

RAW_CTC = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.raw.jsonl"
CURRENT = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
PRE_FIX = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.pre_unicode_word_fix.jsonl"
CSV = ROOT / "dataset/candidate_collection/training_batch_01.csv"
AUDIT = ROOT / "alignment/automatic/unicode_word_segmentation_audit.jsonl"
SUMMARY = ROOT / "alignment/automatic/unicode_word_segmentation_summary.json"
CORRECTIONS = ROOT / "dataset/corrections/transcript_audio_mismatches.jsonl"


def main() -> None:
    if not PRE_FIX.exists():
        shutil.copy2(CURRENT, PRE_FIX)
    raw = {row["prompt_id"]: row for row in map(json.loads, RAW_CTC.read_text(encoding="utf-8").splitlines())}
    old = {row["prompt_id"]: row for row in map(json.loads, PRE_FIX.read_text(encoding="utf-8").splitlines())}
    with CSV.open(encoding="utf-8-sig", newline="") as handle:
        metadata = list(csv.DictReader(handle))
    outputs, audits = [], []
    resolved_corrections = {}
    if CORRECTIONS.exists():
        for correction in map(json.loads, CORRECTIONS.read_text(encoding="utf-8").splitlines()):
            if correction.get("resolution") == "authoritative_transcript_corrected_and_alignment_rebuilt":
                resolved_corrections[correction["prompt_id"]] = correction
    for row in metadata:
        prompt_id = row["prompt_id"]
        source = raw[prompt_id]
        text = unicodedata.normalize("NFC", row["yoruba"])
        annotation = {"prompt_id": prompt_id, "text_nfc": text, "audio_path": source["audio_path"], "words": words_and_syllables(text)}
        rebuilt = build_alignment(annotation, source["decoded_text_nfc"], source["decoded_token_timestamps_s"], source["duration_s"])
        rebuilt["decoded_tokens"] = source["decoded_tokens"]
        rebuilt["decoded_token_timestamps_s"] = source["decoded_token_timestamps_s"]
        rebuilt, boundary_changes = repair_alignment(rebuilt)
        rebuilt["orthographic_segmentation"] = {
            "version": "unicode_combining_mark_safe_v0.1", "source": "authoritative_nfc_transcript",
            "status": "structurally_valid_requires_human_verification",
        }
        if prompt_id in resolved_corrections:
            correction = resolved_corrections[prompt_id]
            rebuilt["transcript_correction"] = {
                "status": "resolved_and_realigned", "issue_type": correction["issue_type"],
                "original_prompt_text_nfc": correction["original_prompt_text_nfc"],
                "corrected_text_nfc": correction["observed_audio_text_nfc"],
                "reported_by": correction["reported_by"], "reported_at": correction["reported_at"],
            }
        errors = interval_errors(rebuilt)
        if errors:
            raise RuntimeError(f"{prompt_id}: {errors}")
        old_words = [word["text"] for word in old[prompt_id]["words"]]
        new_words = [word["text"] for word in rebuilt["words"]]
        audits.append({
            "schema_version": "0.1", "prompt_id": prompt_id, "changed": old_words != new_words,
            "old_words": old_words, "new_words": new_words,
            "old_word_count": len(old_words), "new_word_count": len(new_words),
            "boundary_repair_action_count": len(boundary_changes),
        })
        outputs.append(rebuilt)
    with CURRENT.open("w", encoding="utf-8", newline="\n") as handle:
        for item in outputs:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    with AUDIT.open("w", encoding="utf-8", newline="\n") as handle:
        for item in audits:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    changed = [item for item in audits if item["changed"]]
    SUMMARY.write_text(json.dumps({
        "schema_version": "0.1", "record_count": len(outputs),
        "records_with_word_segmentation_changes": len(changed),
        "changed_prompt_ids": [item["prompt_id"] for item in changed],
        "remaining_structural_validation_errors": 0,
        "pre_fix_alignment": str(PRE_FIX.relative_to(ROOT)).replace("\\", "/"),
        "raw_ctc_alignment": str(RAW_CTC.relative_to(ROOT)).replace("\\", "/"),
        "cause": "Python word-character regex excluded combining tone marks (Unicode category Mn), turning marks into false word boundaries",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"records={len(outputs)} word_segmentation_changed={len(changed)} structural_errors=0")


if __name__ == "__main__":
    main()
