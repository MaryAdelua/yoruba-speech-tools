"""Merge fluent-speaker review decisions without erasing automatic provenance."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "dataset" / "annotations" / "training_batch_01_pronunciation.jsonl"
REVIEWS = ROOT / "dataset" / "annotations" / "training_batch_01_review_queue.csv"
OUTPUT = ROOT / "dataset" / "annotations" / "training_batch_01_pronunciation_reviewed.jsonl"


def main() -> None:
    with REVIEWS.open(encoding="utf-8-sig", newline="") as handle:
        reviews = list(csv.DictReader(handle))
    if any(row["phoneme_or_syllable_correct"] != "yes" for row in reviews):
        raise ValueError("review queue still contains unapproved items")
    review_map = {(row["prompt_id"], int(row["word_index"])): row for row in reviews}

    records = []
    with AUTO.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            verified_count = 0
            for word in record["words"]:
                review = review_map.get((record["prompt_id"], word["word_index"]))
                if review:
                    word["targeted_review"] = {
                        "status": "human_verified",
                        "reviewer": "speaker01",
                        "review_date": "2026-07-19",
                        "decision": "automatic phoneme and syllable annotation accepted",
                    }
                    verified_count += 1
                else:
                    word["targeted_review"] = {"status": "not_required_by_rule_queue"}
            record["targeted_review_status"] = "complete"
            record["human_verified_flagged_word_count"] = verified_count
            record["pronunciation_status"] = "automatic_with_targeted_fluent_review"
            records.append(record)

    if sum(record["human_verified_flagged_word_count"] for record in records) != len(reviews):
        raise ValueError("not every review decision mapped to an annotation word")
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"utterances={len(records)}")
    print(f"targeted_words_verified={len(reviews)}")
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()

