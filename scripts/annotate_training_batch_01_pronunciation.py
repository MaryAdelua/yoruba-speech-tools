"""Generate automatic pronunciation annotations and a fluent-review queue."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yoruba_pronunciation import annotate_utterance  # noqa: E402


SOURCE = ROOT / "dataset" / "candidate_collection" / "training_batch_01.csv"
OUTPUT = ROOT / "dataset" / "annotations" / "training_batch_01_pronunciation.jsonl"
REVIEW = ROOT / "dataset" / "annotations" / "training_batch_01_review_queue.csv"
INVENTORY = ROOT / "dataset" / "annotations" / "YORUBA_PHONEME_INVENTORY_0_1.md"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    annotations = []
    review_rows = []
    for row in rows:
        annotation = annotate_utterance(row["yoruba"])
        annotation.update({
            "prompt_id": row["prompt_id"],
            "split": row["split"],
            "audio_path": f"audio_wav_24k/speaker01_{row['prompt_id']}.wav",
            "speaker_text_review": "approved",
        })
        annotations.append(annotation)
        for flagged in annotation["review_flags"]:
            review_rows.append({
                "prompt_id": row["prompt_id"],
                "word_index": flagged["word_index"],
                "word": flagged["word"],
                "automatic_flags": "; ".join(flagged["flags"]),
                "phoneme_or_syllable_correct": "pending",
                "preferred_annotation": "",
                "review_notes": "",
            })
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for annotation in annotations:
            handle.write(json.dumps(annotation, ensure_ascii=False, sort_keys=True) + "\n")
    fields = list(review_rows[0]) if review_rows else ["prompt_id", "word_index", "word", "automatic_flags", "phoneme_or_syllable_correct", "preferred_annotation", "review_notes"]
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review_rows)
    print(f"utterances={len(annotations)}")
    print(f"tone_units={sum(len(a['tone_units']) for a in annotations)}")
    print(f"words={sum(len(a['words']) for a in annotations)}")
    print(f"review_queue_rows={len(review_rows)}")


if __name__ == "__main__":
    main()

