import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_yt0013_authoritative_transcript_matches_speaker_report():
    with (ROOT / "dataset/candidate_collection/training_batch_01.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(item for item in csv.DictReader(handle) if item["prompt_id"] == "YT0013")
    assert row["yoruba"] == "Ẹ jọ̀wọ́, dín ohun náà kù."
    assert row["english_meaning"] == "Please lower the volume."
    assert row["recording_filename"] == "speaker01_YT0013.wav"


def test_yt0013_alignment_was_rebuilt_from_corrected_transcript():
    records = [json.loads(line) for line in (ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl").read_text(encoding="utf-8").splitlines()]
    row = next(item for item in records if item["prompt_id"] == "YT0013")
    assert row["text_nfc"] == "Ẹ jọ̀wọ́, dín ohun náà kù."
    assert row["transcript_correction"]["status"] == "resolved_and_realigned"
    assert [word["text"] for word in row["words"]] == ["Ẹ", "jọ̀wọ́", "dín", "ohun", "náà", "kù"]


def test_reviewer_contains_mismatch_dispositions():
    html = (ROOT / "alignment/review/yoruba-alignment-review.html").read_text(encoding="utf-8")
    assert "Flag transcript/audio mismatch" in html
    assert "corrected_transcript_pending_realignment" in html
    assert "exclude_from_dataset" in html
