import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "work/training_batch_01_wav_24k"
BACKUP = ROOT / "work/training_batch_01_mapping_pre_fix_2026-07-19"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_corrected_audio_files_follow_offset_evidence():
    for target, source in {18: 19, 19: 20, 20: 21, 21: 22}.items():
        assert digest(ACTIVE / f"speaker01_YT{target:04d}.wav") == digest(BACKUP / f"speaker01_YT{source:04d}.wav")


def test_yt0022_is_missing_and_quarantined_not_served():
    assert not (ACTIVE / "speaker01_YT0022.wav").exists()
    assert (ACTIVE / "speaker01_YT0022.missing-recording-quarantine.wav").exists()
    issues = [json.loads(line) for line in (ROOT / "alignment/manual/dataset_item_issues.jsonl").read_text(encoding="utf-8").splitlines()]
    issue = next(row for row in issues if row["prompt_id"] == "YT0022")
    assert issue["issue_type"] == "missing_audio"
    assert issue["disposition"] == "exclude_from_dataset"


def test_alignment_mapping_and_asr_evidence_are_corrected():
    records = {row["prompt_id"]: row for row in map(json.loads, (ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl").read_text(encoding="utf-8").splitlines())}
    assert records["YT0018"]["audio_mapping"]["source_pre_fix_id"] == "YT0019"
    assert "osukpa" in records["YT0018"]["decoded_text_nfc"]
    assert "nkọrin" in records["YT0019"]["decoded_text_nfc"]
    assert "tutu" in records["YT0020"]["decoded_text_nfc"]
    assert "ofurufu" in records["YT0021"]["decoded_text_nfc"]
    assert records["YT0022"]["audio_status"] == "missing_recording"


def test_duplicate_is_content_level_not_byte_identical():
    audit = json.loads((ROOT / "dataset/corrections/audio_mapping_audit_yt0017_yt0023.json").read_text(encoding="utf-8"))
    assert audit["duplicate_content"] == ["pre-fix YT0017", "pre-fix YT0018"]
    assert audit["duplicate_files_byte_identical"] is False
    assert audit["missing_recording"] == "YT0022"
