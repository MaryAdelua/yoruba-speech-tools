import json
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from integration_toolkit import acoustic_frame_adapter, build_canonical_record, read_jsonl, text_sequence_adapter


def test_all_verified_records_round_trip_through_both_adapters():
    rows = read_jsonl(ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl")
    assert len(rows) == 29
    for source in rows:
        canonical = build_canonical_record(source)
        text = text_sequence_adapter(canonical)
        frames = acoustic_frame_adapter(canonical)
        assert "".join(text["input_units"]) == source["text_nfc"]
        assert source["text_nfc"] == unicodedata.normalize("NFC", source["text_nfc"])
        assert canonical["target_identity_sha256"] == text["target_identity_sha256"] == frames["target_identity_sha256"]
        assert canonical["supervision_masks"]["phonemes"] == 0
        assert canonical["supervision_masks"]["surface_tone"] == 0
        assert sum(frames["aligned_supervision_mask"]) > 0


def test_dry_run_updates_no_model_weights():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/build_integration_dry_run.py")], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    summary = json.loads((ROOT / "artifacts/integration_dry_run/dry_run_summary.json").read_text(encoding="utf-8"))
    assert summary["record_count"] == 29
    assert summary["adapter_count"] == 2
    assert summary["target_identity_match_count"] == 29
    assert summary["unicode_round_trip_count"] == 29
    assert summary["model_weights_updated"] is False
