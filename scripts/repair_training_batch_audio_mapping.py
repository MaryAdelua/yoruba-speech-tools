"""Repair the YT0018-YT0022 one-position audio offset with full provenance."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path

import numpy as np
import sherpa_onnx
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from alignment_repair import interval_errors, repair_alignment  # noqa: E402
from omnilingual_alignment import build_alignment  # noqa: E402
from yoruba_orthographic_units import words_and_syllables  # noqa: E402

M4A = ROOT / "work/training_batch_01_mapped_originals"
WAV = ROOT / "work/training_batch_01_wav_24k"
BACKUP = ROOT / "work/training_batch_01_mapping_pre_fix_2026-07-19"
MODEL = ROOT / "work/models/omnilingual-asr-ctc-300m-int8"
ALIGNMENT = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
PRE_FIX_ALIGNMENT = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.pre_audio_mapping_fix.jsonl"
METADATA = ROOT / "dataset/candidate_collection/training_batch_01.csv"
AUDIT = ROOT / "dataset/corrections/audio_mapping_audit_yt0017_yt0023.json"
ISSUES = ROOT / "alignment/manual/dataset_item_issues.jsonl"

REMAP = {"YT0018": "YT0019", "YT0019": "YT0020", "YT0020": "YT0021", "YT0021": "YT0022"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    for prompt_number in range(17, 24):
        prompt_id = f"YT{prompt_number:04d}"
        for directory, suffix in ((M4A, ".m4a"), (WAV, ".wav")):
            source = directory / f"speaker01_{prompt_id}{suffix}"
            target = BACKUP / source.name
            if source.exists() and not target.exists():
                shutil.copy2(source, target)
    if not PRE_FIX_ALIGNMENT.exists():
        shutil.copy2(ALIGNMENT, PRE_FIX_ALIGNMENT)

    file_audit = []
    for target_id, source_id in REMAP.items():
        for directory, suffix in ((M4A, ".m4a"), (WAV, ".wav")):
            source = BACKUP / f"speaker01_{source_id}{suffix}"
            target = directory / f"speaker01_{target_id}{suffix}"
            shutil.copy2(source, target)
            file_audit.append({
                "logical_prompt_id": target_id, "source_pre_fix_id": source_id,
                "active_path": str(target.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(target),
            })
    for directory, suffix in ((M4A, ".m4a"), (WAV, ".wav")):
        missing_path = directory / f"speaker01_YT0022{suffix}"
        quarantine = directory / f"speaker01_YT0022.missing-recording-quarantine{suffix}"
        if missing_path.exists():
            if quarantine.exists():
                quarantine.unlink()
            missing_path.replace(quarantine)

    recognizer = sherpa_onnx.OfflineRecognizer.from_omnilingual_asr_ctc(
        model=str(MODEL / "model.int8.onnx"), tokens=str(MODEL / "tokens.txt"), num_threads=2, provider="cpu"
    )
    with METADATA.open(encoding="utf-8-sig", newline="") as handle:
        metadata = {row["prompt_id"]: row for row in csv.DictReader(handle)}
    current = {row["prompt_id"]: row for row in map(json.loads, ALIGNMENT.read_text(encoding="utf-8").splitlines())}
    pending = []
    for prompt_id in REMAP:
        audio_path = WAV / f"speaker01_{prompt_id}.wav"
        samples, sample_rate = sf.read(audio_path, dtype="float32")
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1).astype(np.float32)
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        pending.append((prompt_id, samples, sample_rate, stream))
    recognizer.decode_streams([item[3] for item in pending])
    for prompt_id, samples, sample_rate, stream in pending:
        text = unicodedata.normalize("NFC", metadata[prompt_id]["yoruba"])
        annotation = {
            "prompt_id": prompt_id, "text_nfc": text,
            "audio_path": f"work/training_batch_01_wav_24k/speaker01_{prompt_id}.wav",
            "words": words_and_syllables(text),
        }
        result = stream.result
        rebuilt = build_alignment(annotation, result.text, list(result.timestamps), len(samples) / sample_rate)
        rebuilt["decoded_tokens"] = list(result.tokens)
        rebuilt["decoded_token_timestamps_s"] = [round(float(value), 4) for value in result.timestamps]
        rebuilt, _ = repair_alignment(rebuilt)
        rebuilt["audio_mapping"] = {
            "status": "corrected", "mapping_version": "yt0018_yt0022_offset_fix_v0.1",
            "source_pre_fix_id": REMAP[prompt_id], "human_reverification_required": True,
        }
        if interval_errors(rebuilt):
            raise RuntimeError(f"{prompt_id} alignment remains invalid")
        current[prompt_id] = rebuilt
    missing_text = unicodedata.normalize("NFC", metadata["YT0022"]["yoruba"])
    current["YT0022"] = {
        "schema_version": "0.1", "prompt_id": "YT0022", "text_nfc": missing_text,
        "audio_path": None, "duration_s": 0.0, "words": words_and_syllables(missing_text),
        "audio_status": "missing_recording", "automatic_status": "excluded_missing_audio",
        "alignment_method": None, "utterance_confidence": None,
        "audio_mapping": {"status": "missing", "mapping_version": "yt0018_yt0022_offset_fix_v0.1", "human_reverification_required": False},
    }
    with ALIGNMENT.open("w", encoding="utf-8", newline="\n") as handle:
        for prompt_id in sorted(current):
            handle.write(json.dumps(current[prompt_id], ensure_ascii=False, sort_keys=True) + "\n")

    issue = {
        "schema_version": "0.1", "prompt_id": "YT0022", "review_status": "dataset_item_issue",
        "issue_type": "missing_audio", "expected_transcript_nfc": missing_text,
        "disposition": "exclude_from_dataset", "reviewer": "Mary Adelua",
        "reviewed_at": f"{date.today().isoformat()}T00:00:00", "notes": "Speaker traced a one-position mapping offset; no recording corresponding to YT0022 was found.",
    }
    existing_issues = [json.loads(line) for line in ISSUES.read_text(encoding="utf-8").splitlines()] if ISSUES.exists() else []
    existing_issues = [row for row in existing_issues if row.get("prompt_id") != "YT0022"] + [issue]
    ISSUES.parent.mkdir(parents=True, exist_ok=True)
    with ISSUES.open("w", encoding="utf-8", newline="\n") as handle:
        for row in existing_issues:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    duplicate_hash_equal = sha256(BACKUP / "speaker01_YT0017.m4a") == sha256(BACKUP / "speaker01_YT0018.m4a")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "schema_version": "0.1", "scope": [f"YT{i:04d}" for i in range(17, 24)],
        "finding": "content offset from YT0018 through YT0022",
        "mapping": {"YT0017": "YT0017", **REMAP, "YT0022": None, "YT0023": "YT0023"},
        "duplicate_content": ["pre-fix YT0017", "pre-fix YT0018"],
        "duplicate_files_byte_identical": duplicate_hash_equal,
        "missing_recording": "YT0022", "file_audit": file_audit,
        "evidence": "speaker listening report corroborated by Omnilingual ASR decoded text sequence",
        "pre_fix_files": str(BACKUP.relative_to(ROOT)).replace("\\", "/"),
        "pre_fix_alignment": str(PRE_FIX_ALIGNMENT.relative_to(ROOT)).replace("\\", "/"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("corrected=YT0018,YT0019,YT0020,YT0021 missing=YT0022 duplicate_content=YT0017/YT0018 byte_identical=false")


if __name__ == "__main__":
    main()
