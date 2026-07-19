import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alignment_repair import interval_errors, repair_alignment


def test_repair_preserves_valid_intervals_and_fixes_local_overlap():
    record = {"duration_s": 2.0, "words": [
        {"text": "a", "start_s": 0.2, "end_s": 0.8, "syllables": [{"orthographic_form": "a", "start_s": 0.2, "end_s": 0.8}]},
        {"text": "b", "start_s": 0.7, "end_s": 1.3, "syllables": [{"orthographic_form": "b", "start_s": 0.7, "end_s": 1.3}]},
        {"text": "c", "start_s": 1.5, "end_s": 1.9, "syllables": [{"orthographic_form": "c", "start_s": 1.5, "end_s": 1.9}]},
    ]}
    repaired, audit = repair_alignment(record)
    assert interval_errors(repaired) == []
    assert repaired["words"][0]["start_s"] == 0.2
    assert repaired["words"][2]["start_s"] == 1.5
    assert any(x["reason"] == "overlap_split_at_midpoint" for x in audit)


def test_repair_interpolates_missing_and_clamps_out_of_range():
    record = {"duration_s": 1.0, "words": [
        {"text": "aa", "start_s": None, "end_s": None, "syllables": []},
        {"text": "b", "start_s": -0.2, "end_s": 1.4, "syllables": []},
    ]}
    repaired, _ = repair_alignment(record)
    assert interval_errors(repaired) == []
    assert 0 <= repaired["words"][0]["start_s"] < repaired["words"][0]["end_s"]
    assert repaired["words"][-1]["end_s"] <= 1.0
