"""Validate invariants required by pronunciation annotation schema 0.2."""

from __future__ import annotations

import json
from pathlib import Path
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "dataset" / "manifests" / "utterances.jsonl"


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    required = {"schema_version", "utterance_id", "speaker_id", "language", "text", "audio", "tone_units", "verification", "split", "split_group_id", "benchmark_exclusion"}
    missing = required - record.keys()
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
        return errors
    if record["schema_version"] != "0.2" or record["language"] != "yo":
        errors.append("unexpected schema version or language")
    if record.get("split") not in {"train", "development", "diagnostic", "test", "unassigned"}:
        errors.append("invalid split")
    if record.get("benchmark_exclusion") and record.get("split") == "train":
        errors.append("benchmark-excluded record cannot be assigned to train")
    if record["text"] != unicodedata.normalize("NFC", record["text"]):
        errors.append("text is not NFC normalized")
    audio = record["audio"]
    if audio.get("sample_rate_hz") != 24000 or audio.get("channels") != 1 or audio.get("sample_format") != "PCM_S16LE":
        errors.append("audio format is not canonical mono 24 kHz PCM_S16LE")
    previous_end = -1
    for index, unit in enumerate(record["tone_units"]):
        if unit.get("unit_index") != index:
            errors.append(f"tone unit {index} has incorrect index")
        if unit.get("tone") not in {"H", "M", "L"}:
            errors.append(f"tone unit {index} has invalid tone")
        start, end = unit.get("character_start"), unit.get("character_end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > len(record["text"]):
            errors.append(f"tone unit {index} has invalid character offsets")
        if isinstance(start, int) and start < previous_end:
            errors.append(f"tone unit {index} overlaps previous unit")
        previous_end = end if isinstance(end, int) else previous_end
        if unit.get("annotation_provenance") not in {"derived", "automatic", "human_verified"}:
            errors.append(f"tone unit {index} has invalid annotation provenance")
        weight = unit.get("meaning_risk_weight")
        if weight is not None and weight < 0:
            errors.append(f"tone unit {index} has negative meaning-risk weight")
    return errors


def main() -> None:
    failures = []
    count = 0
    with MANIFEST.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            count += 1
            record = json.loads(line)
            errors = validate_record(record)
            if errors:
                failures.append((line_number, record.get("utterance_id"), errors))
    if count != 120:
        failures.append((0, "manifest", [f"expected 120 records, found {count}"]))
    if failures:
        raise SystemExit(json.dumps(failures, ensure_ascii=False, indent=2))
    print(f"validated_records={count}")


if __name__ == "__main__":
    main()
