"""Validate a review-tool export and append only new manual correction records."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from omnilingual_alignment import validate_manual_correction  # noqa: E402

AUTOMATIC = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
DESTINATION = ROOT / "alignment/manual/training_batch_01_manual_corrections.jsonl"
ISSUE_DESTINATION = ROOT / "alignment/manual/dataset_item_issues.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    automatic = {x["prompt_id"]: x for x in read_jsonl(AUTOMATIC)}
    incoming = read_jsonl(args.export)
    alignments = [record for record in incoming if record.get("review_status") == "human_verified"]
    issues = [record for record in incoming if record.get("review_status") in {"transcript_audio_mismatch", "dataset_item_issue"}]
    unknown = [record for record in incoming if record.get("review_status") not in {"human_verified", "transcript_audio_mismatch", "dataset_item_issue"}]
    existing = read_jsonl(DESTINATION) if DESTINATION.exists() else []
    def content_key(record: dict) -> tuple[str, str]:
        words = json.dumps(record.get("words", []), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return record["prompt_id"], hashlib.sha256(words.encode("utf-8")).hexdigest()
    existing_keys = {content_key(x) for x in existing}
    errors = []
    for record in alignments:
        if record.get("prompt_id") not in automatic:
            errors.append(f"{record.get('prompt_id')}: no automatic source")
            continue
        errors.extend(f"{record['prompt_id']}: {e}" for e in validate_manual_correction(record, automatic[record["prompt_id"]]))
    for record in issues:
        prompt_id = record.get("prompt_id")
        if prompt_id not in automatic:
            errors.append(f"{prompt_id}: no automatic source")
        if record.get("issue_type", "transcript_audio_mismatch") == "transcript_audio_mismatch" and not record.get("observed_transcript_nfc", "").strip():
            errors.append(f"{prompt_id}: observed_transcript_nfc is required")
        if record.get("disposition") not in {"corrected_transcript_pending_realignment", "exclude_from_dataset"}:
            errors.append(f"{prompt_id}: invalid mismatch disposition")
    if unknown:
        errors.append(f"unsupported review_status in {len(unknown)} record(s)")
    if errors:
        raise SystemExit("\n".join(errors))
    new = []
    seen = set(existing_keys)
    for record in alignments:
        key = content_key(record)
        if key not in seen:
            new.append(record)
            seen.add(key)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with DESTINATION.open("a", encoding="utf-8", newline="\n") as f:
        for record in new:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    existing_issues = read_jsonl(ISSUE_DESTINATION) if ISSUE_DESTINATION.exists() else []
    def issue_key(record: dict) -> tuple[str, str, str]:
        return record["prompt_id"], record.get("issue_type", "transcript_audio_mismatch") + ":" + record.get("observed_transcript_nfc", ""), record.get("disposition", "")
    seen_issues = {issue_key(record) for record in existing_issues}
    new_issues = []
    for record in issues:
        key = issue_key(record)
        if key not in seen_issues:
            new_issues.append(record)
            seen_issues.add(key)
    if new_issues:
        ISSUE_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        with ISSUE_DESTINATION.open("a", encoding="utf-8", newline="\n") as handle:
            for record in new_issues:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"validated={len(incoming)} alignments_appended={len(new)} issues_appended={len(new_issues)}")


if __name__ == "__main__":
    main()
