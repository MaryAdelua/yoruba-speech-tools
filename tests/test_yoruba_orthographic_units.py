import csv
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yoruba_orthographic_units import word_spans, words_and_syllables


def test_combining_tone_marks_do_not_split_words():
    text = unicodedata.normalize("NFC", "Ṣé ẹ̀fọ́ náà ti sè dáadáa?")
    words = [text[a:b] for a, b in word_spans(text)]
    assert words == ["Ṣé", "ẹ̀fọ́", "náà", "ti", "sè", "dáadáa"]


def test_compound_toned_word_remains_one_word():
    text = "Mu kọ́kọ́rọ́ náà wá fún mi."
    assert [word["text"] for word in words_and_syllables(text)][1] == "kọ́kọ́rọ́"


def test_all_rebuilt_words_equal_authoritative_whitespace_units():
    with (ROOT / "dataset/candidate_collection/training_batch_01.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rebuilt = {row["prompt_id"]: row for row in map(json.loads, (ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl").read_text(encoding="utf-8").splitlines())}
    for row in rows:
        text = unicodedata.normalize("NFC", row["yoruba"])
        expected = [text[a:b] for a, b in word_spans(text)]
        assert [word["text"] for word in rebuilt[row["prompt_id"]]["words"]] == expected
