"""Build canonical Yoruba batches and two no-training adapter dry runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from integration_toolkit import (  # noqa: E402
    acoustic_frame_adapter, build_canonical_record, read_jsonl, stable_hash, text_sequence_adapter,
)

SOURCE = ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl"
OUTPUT = ROOT / "artifacts/integration_dry_run"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> None:
    canonical = [build_canonical_record(row) for row in read_jsonl(SOURCE)]
    text_batches = [text_sequence_adapter(row) for row in canonical]
    frame_batches = [acoustic_frame_adapter(row) for row in canonical]
    for canonical_row, text_row, frame_row in zip(canonical, text_batches, frame_batches):
        identities = {canonical_row["target_identity_sha256"], text_row["target_identity_sha256"], frame_row["target_identity_sha256"]}
        if len(identities) != 1:
            raise SystemExit(f"{canonical_row['prompt_id']}: adapter target identity mismatch")
        if "".join(text_row["input_units"]) != canonical_row["text_nfc"]:
            raise SystemExit(f"{canonical_row['prompt_id']}: grapheme adapter changed authoritative text")
    write_jsonl(OUTPUT / "canonical_records.jsonl", canonical)
    write_jsonl(OUTPUT / "text_sequence_adapter.jsonl", text_batches)
    write_jsonl(OUTPUT / "acoustic_frame_adapter.jsonl", frame_batches)
    summary = {
        "schema_version": "1.0", "dry_run_only": True, "model_weights_updated": False,
        "record_count": len(canonical), "adapter_count": 2,
        "adapters": ["text-sequence-v1", "acoustic-frame-v1"],
        "target_identity_match_count": len(canonical), "unicode_round_trip_count": len(canonical),
        "word_count": sum(len(row["words"]) for row in canonical),
        "syllable_count": sum(len(row["syllables"]) for row in canonical),
        "tone_unit_count": sum(len(row["tone_units"]) for row in canonical),
        "enabled_supervision": ["audio_pair", "word_boundaries", "syllable_boundaries", "orthographic_tone"],
        "disabled_supervision": ["surface_tone", "phonemes"],
        "canonical_dataset_sha256": stable_hash(canonical),
    }
    (OUTPUT / "dry_run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"dry_run=PASS records={len(canonical)} adapters=2 model_weights_updated=false")


if __name__ == "__main__":
    main()
