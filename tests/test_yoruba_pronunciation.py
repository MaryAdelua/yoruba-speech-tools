import sys
from pathlib import Path
import unittest
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from yoruba_pronunciation import annotate_utterance, base_grapheme


class YorubaPronunciationTests(unittest.TestCase):
    def test_underdotted_vowels_remain_distinct(self):
        annotation = annotate_utterance("e ẹ o ọ")
        phonemes = [p["phoneme"] for w in annotation["words"] for p in w["phonemes"]]
        self.assertEqual(phonemes, ["e", "ɛ", "o", "ɔ"])

    def test_gb_and_p_are_yoruba_labial_velars(self):
        annotation = annotate_utterance("gbà pẹ̀")
        phonemes = [[p["phoneme"] for p in w["phonemes"]] for w in annotation["words"]]
        self.assertEqual(phonemes[0][0], "ɡ͡b")
        self.assertEqual(phonemes[1][0], "k͡p")

    def test_tones_map_back_to_words_and_syllables(self):
        annotation = annotate_utterance("ọ̀rẹ́")
        self.assertEqual([u["tone"] for u in annotation["tone_units"]], ["L", "H"])
        self.assertTrue(all(u["word_index"] == 0 for u in annotation["tone_units"]))
        self.assertTrue(all(u["syllable_index"] is not None for u in annotation["tone_units"]))

    def test_nasal_sequence_is_reviewed(self):
        annotation = annotate_utterance("ohùn")
        flags = annotation["words"][0]["review_flags"]
        self.assertIn("nasal_vowel_requires_review", flags)
        self.assertEqual(unicodedata.normalize("NFC", annotation["words"][0]["syllables"][-1]["phonemes"][-1]), "ũ")

    def test_n_before_vowel_is_next_syllable_onset(self):
        annotation = annotate_utterance("inú")
        syllables = annotation["words"][0]["syllables"]
        self.assertEqual([s["orthographic_form"] for s in syllables], ["i", "nu"])

    def test_syllabic_nasal_receives_tone_unit(self):
        annotation = annotate_utterance("ń lọ")
        self.assertEqual(annotation["words"][0]["phonemes"][0]["phoneme"], "N̩")
        self.assertEqual(annotation["tone_units"][0]["tone"], "H")

    def test_alignment_is_not_fabricated(self):
        annotation = annotate_utterance("Yorùbá")
        self.assertEqual(annotation["alignment_status"], "pending")
        self.assertTrue(all(unit["start_s"] is None for unit in annotation["tone_units"]))


if __name__ == "__main__":
    unittest.main()
