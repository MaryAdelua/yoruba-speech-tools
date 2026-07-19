import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from omnilingual_alignment import align_characters, build_alignment, comparison_text, validate_manual_correction


def test_comparison_preserves_yoruba_original_and_source_map():
    text = "Ẹlẹ́ṣin náà."
    item = comparison_text(text)
    assert item.original_nfc == unicodedata.normalize("NFC", text)
    assert "ẹ" in item.text and "ṣ" in item.text and "á" in item.text
    assert len(item.text) == len(item.source_spans)


def test_character_alignment_returns_exact_matches():
    mapping, distance = align_characters("ẹṣin dúdú", "ẹṣin dudu")
    assert distance == 2
    assert mapping[0] == 0


def test_acoustic_boundaries_are_projected_and_need_review():
    annotation = {"prompt_id": "YT0001", "text_nfc": "Ẹṣin dúdú.", "audio_path": "x.wav", "words": [
        {"word_index": 0, "text": "Ẹṣin", "character_start": 0, "character_end": 4, "syllables": [{"syllable_index": 0, "orthographic_form": "Ẹ", "character_start": 0, "character_end": 1}]},
        {"word_index": 1, "text": "dúdú", "character_start": 5, "character_end": 9, "syllables": [{"syllable_index": 0, "orthographic_form": "dú", "character_start": 5, "character_end": 7}]},
    ]}
    result = build_alignment(annotation, "ẹṣin dúdú", [0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 0.9, 1.0, 1.1], 1.5)
    assert result["automatic_status"] == "requires_human_verification"
    assert result["words"][0]["start_s"] < result["words"][0]["end_s"]


def test_manual_correction_must_be_verified_and_monotonic():
    auto = {"prompt_id": "YT0001", "duration_s": 2.0, "words": [{"text": "ọkọ"}, {"text": "dúdú"}]}
    record = {"prompt_id": "YT0001", "review_status": "human_verified", "words": [{"text": "ọkọ", "start_s": 0.1, "end_s": 0.8}, {"text": "dúdú", "start_s": 0.9, "end_s": 1.7}]}
    assert validate_manual_correction(record, auto) == []
