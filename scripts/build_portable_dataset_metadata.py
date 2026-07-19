"""Build release-neutral portable metadata for the frozen Yoruba benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmark" / "benchmark_manifest.csv"
TONE_ANNOTATIONS = ROOT / "benchmark" / "tone_annotations.jsonl"
OUTPUT_DIR = ROOT / "dataset" / "manifests"
OUTPUT_JSONL = OUTPUT_DIR / "utterances.jsonl"
CHECKSUMS = OUTPUT_DIR / "metadata_checksums.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    with BENCHMARK.open("r", encoding="utf-8-sig", newline="") as handle:
        benchmark = {row["prompt_id"]: row for row in csv.DictReader(handle)}
    with TONE_ANNOTATIONS.open("r", encoding="utf-8-sig") as handle:
        annotations = {row["prompt_id"]: row for row in map(json.loads, handle)}

    if benchmark.keys() != annotations.keys():
        raise ValueError("benchmark and tone annotation prompt IDs differ")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for prompt_id in sorted(benchmark):
        row = benchmark[prompt_id]
        annotation = annotations[prompt_id]
        tone_units = []
        for index, unit in enumerate(annotation["tone_units"]):
            tone_units.append(
                {
                    "unit_index": index,
                    "grapheme": unit["grapheme"],
                    "base_vowel": unit["base_vowel"],
                    "tone": unit["tone"],
                    "character_start": unit["character_start"],
                    "character_end": unit["character_end"],
                    "word_index": None,
                    "start_s": None,
                    "end_s": None,
                    "timing_status": "pending",
                    "annotation_provenance": "derived",
                    "meaning_risk_weight": None,
                    "meaning_risk_review_status": "not_used",
                }
            )
        records.append(
            {
                "schema_version": "0.2",
                "utterance_id": f"speaker01_{prompt_id}",
                "speaker_id": "speaker01",
                "language": "yo",
                "text": row["yoruba"],
                "english_meaning": row["english_meaning"],
                "research_purpose": row["research_purpose"],
                "contrast_group_ids": [x for x in row["contrast_group_ids"].split(";") if x],
                "split": "diagnostic",
                "split_group_id": "frozen-calibration-120",
                "benchmark_exclusion": True,
                "audio": {
                    "path": row["audio_filename"],
                    "sample_rate_hz": int(row["sample_rate_hz"]),
                    "channels": int(row["channels"]),
                    "sample_format": row["sample_format"],
                    "duration_s": float(row["processed_duration_s"]),
                    "peak_dbfs": float(row["processed_peak_dbfs"]),
                    "rms_dbfs": float(row["processed_rms_dbfs"]),
                },
                "tone_units": tone_units,
                "verification": {
                    "transcript": "verified",
                    "naturalness": "verified",
                    "tone_annotation_type": "orthographic",
                    "pronunciation_annotation_status": "orthography_only",
                },
                "surface_tone_status": "not_annotated",
                "release_status": "metadata_only_pending_signed_release",
            }
        )

    with OUTPUT_JSONL.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    sources = [BENCHMARK, TONE_ANNOTATIONS, OUTPUT_JSONL, ROOT / "dataset" / "annotation_schema.json"]
    with CHECKSUMS.open("w", encoding="ascii", newline="\n") as handle:
        for path in sources:
            handle.write(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n")

    print(f"records={len(records)}")
    print(f"manifest={OUTPUT_JSONL}")
    print(f"checksums={CHECKSUMS}")


if __name__ == "__main__":
    main()
