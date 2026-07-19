"""Create the downstream training alignment dataset only when all 30 are verified."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from omnilingual_alignment import validate_manual_correction  # noqa: E402
from yoruba_orthographic_units import migrate_manual_word_groups  # noqa: E402

AUTO = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
MANUAL = ROOT / "alignment/manual/training_batch_01_manual_corrections.jsonl"
ISSUES = ROOT / "alignment/manual/dataset_item_issues.jsonl"
SOURCE = ROOT / "dataset/candidate_collection/training_batch_01.csv"
OUTPUT = ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl"
MANIFEST = ROOT / "dataset/verified/training_batch_01_verified_alignment_manifest.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    automatic = {x["prompt_id"]: x for x in read_jsonl(AUTO)}
    latest_issues = {}
    for row in read_jsonl(ISSUES) if ISSUES.exists() else []:
        previous = latest_issues.get(row["prompt_id"])
        if previous is None or row["reviewed_at"] > previous["reviewed_at"]:
            latest_issues[row["prompt_id"]] = row
    pending_realignment = sorted(prompt_id for prompt_id, row in latest_issues.items() if row["disposition"] == "corrected_transcript_pending_realignment")
    if pending_realignment:
        raise SystemExit(f"Not finalized: transcript correction and re-alignment pending for: {', '.join(pending_realignment)}")
    excluded = {prompt_id for prompt_id, row in latest_issues.items() if row["disposition"] == "exclude_from_dataset"}
    latest = {}
    for row in read_jsonl(MANUAL) if MANUAL.exists() else []:
        previous = latest.get(row["prompt_id"])
        if previous is None or row["reviewed_at"] > previous["reviewed_at"]:
            latest[row["prompt_id"]] = row
    expected = set(automatic) - excluded
    missing = sorted(expected - set(latest))
    if missing:
        raise SystemExit(f"Not finalized: {len(missing)} recordings still need imported human verification: {', '.join(missing)}")
    errors = []
    for prompt_id in sorted(expected):
        if [word.get("text") for word in latest[prompt_id].get("words", [])] != [word.get("text") for word in automatic[prompt_id].get("words", [])]:
            migrated = migrate_manual_word_groups(latest[prompt_id], automatic[prompt_id])
            if migrated is None:
                errors.append(f"{prompt_id}: legacy word segmentation cannot be migrated safely")
            else:
                latest[prompt_id] = migrated
        errors.extend(f"{prompt_id}: {error}" for error in validate_manual_correction(latest[prompt_id], automatic[prompt_id]))
    if errors:
        raise SystemExit("Finalization failed:\n" + "\n".join(errors))
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        metadata = {r["prompt_id"]: r for r in csv.DictReader(handle)}
    output = []
    for prompt_id in sorted(expected):
        auto, human, meta = automatic[prompt_id], latest[prompt_id], metadata[prompt_id]
        output.append({
            "schema_version": "1.0", "utterance_id": f"speaker01_{prompt_id}", "prompt_id": prompt_id,
            "speaker_id": "speaker01", "language": "yo", "split": meta["split"],
            "split_group_id": meta["split_group_id"], "text_nfc": auto["text_nfc"],
            "english_meaning": meta["english_meaning"], "audio_path": auto["audio_path"],
            "duration_s": auto["duration_s"], "words": human["words"],
            "alignment": {"status": "human_verified", "reviewer": human["reviewer"],
                          "reviewed_at": human["reviewed_at"], "automatic_method": auto["alignment_method"],
                          "automatic_confidence": auto["utterance_confidence"], "manual_notes": human.get("notes", ""),
                          "review_scope": human.get("review_scope", "word_boundaries_legacy_review")},
            "training_use": {"word_boundary_loss_mask": 1,
                             "orthography_is_authoritative": True,
                             "syllable_boundary_loss_mask": int(human.get("review_scope") == "word_and_syllable_boundaries")},
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in output:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    corrected_transcripts = sorted(
        prompt_id for prompt_id, row in automatic.items() if row.get("transcript_correction")
    )
    word_count = sum(len(row["words"]) for row in output)
    syllable_count = sum(len(word.get("syllables", [])) for row in output for word in row["words"])
    verified_syllable_count = sum(
        len(word.get("syllables", []))
        for row in output if row["training_use"]["syllable_boundary_loss_mask"] == 1
        for word in row["words"]
    )
    MANIFEST.write_text(json.dumps({
        "schema_version": "1.0", "record_count": len(output), "verification_status": "complete",
        "excluded_transcript_audio_mismatches": sorted(excluded),
        "excluded_recordings": sorted(excluded), "corrected_transcripts": corrected_transcripts,
        "unresolved_issues": [], "word_boundary_coverage": {"covered": word_count, "total": word_count, "percent": 100.0},
        "syllable_boundary_coverage": {"covered": verified_syllable_count, "total": syllable_count,
                                        "percent": round(100 * verified_syllable_count / syllable_count, 2)},
        "human_authority": True, "source_automatic_sha256": digest(AUTO),
        "source_manual_sha256": digest(MANUAL), "dataset_sha256": digest(OUTPUT),
        "dataset": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"finalized={len(output)} dataset={OUTPUT}")


if __name__ == "__main__":
    main()
