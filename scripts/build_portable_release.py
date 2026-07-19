"""Build a deterministic private Yoruba pronunciation release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import unicodedata
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl"
SOURCE_MANIFEST = ROOT / "dataset/verified/training_batch_01_verified_alignment_manifest.json"
AUDIO_ROOT = ROOT / "work/training_batch_01_wav_24k"
DEFAULT_OUTPUT = ROOT / "release_candidates/yoruba-pronunciation-resource-v0.1-rc1"

DOCUMENTS = {
    ROOT / "dataset/VERIFIED_ALIGNMENT_DATASET_CARD.md": "docs/DATASET_CARD.md",
    ROOT / "dataset/DATA_STATEMENT.md": "docs/DATA_STATEMENT.md",
    ROOT / "dataset/PRONUNCIATION_ANNOTATION_GUIDE.md": "docs/PRONUNCIATION_ANNOTATION_GUIDE.md",
    ROOT / "dataset/SPLIT_AND_LEAKAGE_POLICY.md": "docs/SPLIT_AND_LEAKAGE_POLICY.md",
    ROOT / "method/INTEGRATION_GUIDE.md": "docs/INTEGRATION_GUIDE.md",
    ROOT / "method/LOSS_SPECIFICATION.md": "docs/LOSS_SPECIFICATION.md",
    ROOT / "governance/PLAIN_LANGUAGE_CONSENT_SUMMARY.md": "governance/PLAIN_LANGUAGE_CONSENT_SUMMARY.md",
    ROOT / "governance/release_record.yaml": "governance/release_record.yaml",
    ROOT / "alignment/manual/manual_correction.schema.json": "schemas/manual_correction.schema.json",
    ROOT / "dataset/annotation_schema.json": "schemas/annotation_schema.json",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wav_metadata(path: Path) -> dict:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
        return {
            "sample_rate_hz": rate,
            "channels": handle.getnchannels(),
            "sample_width_bits": handle.getsampwidth() * 8,
            "frame_count": frames,
            "duration_s": round(frames / rate, 6),
        }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replace", action="store_true", help="Replace an existing generated candidate directory.")
    args = parser.parse_args()
    output = args.output.resolve()
    allowed_root = (ROOT / "release_candidates").resolve()
    if allowed_root not in output.parents:
        raise SystemExit(f"Output must be inside {allowed_root}")
    if output.exists():
        if not args.replace:
            raise SystemExit(f"Output already exists: {output}; pass --replace to regenerate it")
        shutil.rmtree(output)

    rows = read_jsonl(DATASET)
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    portable_rows = []
    for row in rows:
        source_audio = ROOT / row["audio_path"]
        target_name = f"{row['utterance_id']}.wav"
        target_audio = output / "audio" / target_name
        target_audio.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_audio, target_audio)
        portable = dict(row)
        portable["text_nfc"] = unicodedata.normalize("NFC", portable["text_nfc"])
        portable["audio_path"] = f"audio/{target_name}"
        portable["audio"] = {**wav_metadata(target_audio), "sha256": sha256(target_audio)}
        portable_rows.append(portable)

    write_jsonl(output / "data/utterances.jsonl", portable_rows)
    for source, destination in DOCUMENTS.items():
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(ROOT / "scripts/validate_portable_release.py", output / "validate_release.py")

    release_manifest = {
        "schema_version": "1.0",
        "release_id": "yoruba-pronunciation-resource-v0.1-rc1",
        "release_status": "private_release_candidate_not_for_redistribution",
        "public_release_blockers": ["signed_speaker_release", "explicit_dataset_license", "privacy_and_misuse_review", "persistent_release_identifier"],
        "attribution_name": "Mary Adelua",
        "language": "yo",
        "speaker_count": 1,
        "record_count": len(portable_rows),
        "excluded_recordings": source_manifest["excluded_recordings"],
        "corrected_transcripts": source_manifest["corrected_transcripts"],
        "word_boundary_coverage": source_manifest["word_boundary_coverage"],
        "syllable_boundary_coverage": source_manifest["syllable_boundary_coverage"],
        "data_file": "data/utterances.jsonl",
        "validator": "validate_release.py",
    }
    manifest_path = output / "release_manifest.json"
    manifest_path.write_text(json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    readme = """# Yoruba Pronunciation Resource v0.1-rc1

Private, validation-ready release candidate containing 29 human-verified Standard Yoruba recordings and architecture-independent word and syllable alignments.

## Important release status

This package is **not authorized for public redistribution**. A signed speaker release, explicit dataset license, privacy/misuse review, and persistent release identifier remain required.

## Validate

Run `python validate_release.py .` from this directory. A valid package reports `VALID` and verifies every checksum, WAV property, Unicode transcript, exclusion, and boundary.

## Primary data

- `data/utterances.jsonl`: portable training/evaluation records
- `audio/`: mono 24 kHz, 16-bit PCM WAV recordings
- `release_manifest.json`: release status, coverage, corrections, and exclusions
- `docs/`: dataset and integration documentation
- `schemas/`: annotation schemas
- `governance/`: current consent status and risk summary
"""
    (output / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    checksum_rows = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "CHECKSUMS.sha256"):
        checksum_rows.append(f"{sha256(path)}  {path.relative_to(output).as_posix()}")
    (output / "CHECKSUMS.sha256").write_text("\n".join(checksum_rows) + "\n", encoding="ascii", newline="\n")
    print(f"built={output} records={len(portable_rows)}")


if __name__ == "__main__":
    main()
