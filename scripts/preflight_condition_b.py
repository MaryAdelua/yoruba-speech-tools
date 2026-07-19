#!/usr/bin/env python3
"""Validate Condition B inputs without starting adaptation training."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path

import soundfile as sf
import torch
import transformers
from transformers import AutoTokenizer


EXPECTED_SPLITS = {"train": 23, "development": 3, "test": 3}
PROTECTED_TEST_IDS = ["YT0028", "YT0029", "YT0030"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", default="facebook/mms-tts-yor")
    parser.add_argument("--model-revision", default="d359e06b481cb5402e2e4215475b90c07a3f12e2")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in args.dataset.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    counts = Counter(row["split"] for row in rows)
    if dict(counts) != EXPECTED_SPLITS:
        raise ValueError(f"Split counts changed: {dict(counts)}")
    if [row["prompt_id"] for row in rows if row["split"] == "test"] != PROTECTED_TEST_IDS:
        raise ValueError("Protected test set changed")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, revision=args.model_revision, local_files_only=args.local_files_only
    )
    records = []
    for row in rows:
        audio_path = Path(row["audio_path"])
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        info = sf.info(audio_path)
        encoded = tokenizer(row["text_nfc"], add_special_tokens=False)
        unknown_count = encoded["input_ids"].count(tokenizer.unk_token_id)
        if unknown_count:
            raise ValueError(f"{row['prompt_id']}: {unknown_count} unknown model tokens")
        records.append({
            "prompt_id": row["prompt_id"],
            "split": row["split"],
            "split_group_id": row["split_group_id"],
            "text_nfc": row["text_nfc"],
            "audio_path": row["audio_path"],
            "audio_sha256": sha256_file(audio_path),
            "sample_rate_hz": info.samplerate,
            "channels": info.channels,
            "frames": info.frames,
            "duration_s": info.duration,
            "model_token_count": len(encoded["input_ids"]),
            "unknown_token_count": unknown_count,
            "eligible_for_weight_updates": row["split"] == "train",
            "eligible_for_checkpoint_selection": row["split"] == "development",
            "protected_from_training_and_tuning": row["split"] == "test",
        })

    summary = {
        "schema_version": "1.0",
        "experiment": "Experiment 1",
        "condition": "B",
        "condition_definition": "matched Yoruba data adaptation; no auxiliary supervision",
        "status": "preflight_complete_training_not_started",
        "model_id": args.model,
        "model_revision": args.model_revision,
        "dataset_sha256": sha256_file(args.dataset),
        "split_counts": dict(counts),
        "split_duration_s": {
            split: sum(record["duration_s"] for record in records if record["split"] == split)
            for split in EXPECTED_SPLITS
        },
        "audio_files_present": len(records),
        "records_without_unknown_tokens": sum(record["unknown_token_count"] == 0 for record in records),
        "source_sample_rates_hz": sorted({record["sample_rate_hz"] for record in records}),
        "model_sample_rate_hz": 16000,
        "resampling_required": any(record["sample_rate_hz"] != 16000 for record in records),
        "training_started": False,
        "training_updates": 0,
        "test_items_exposed_to_training": 0,
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda_available": torch.cuda.is_available(),
        },
        "unresolved_training_specification": [
            "training implementation and exact MMS/VITS checkpoint format",
            "trainable and frozen modules",
            "optimizer and learning rate",
            "batch size and gradient accumulation",
            "update budget and stopping rule",
            "development checkpoint-selection metric",
            "training seeds and number of runs",
            "checkpoint and artifact retention policy"
        ],
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
