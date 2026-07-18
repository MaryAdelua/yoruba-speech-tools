import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tone_parser import extract_tone_units, tone_sequence


class ToneParserTests(unittest.TestCase):
    def test_high_low_mid(self):
        self.assertEqual(tone_sequence("áaà"), "HML")

    def test_underdotted_vowels(self):
        units = extract_tone_units("ẹ́ọ̀")
        self.assertEqual([(x.base_vowel, x.tone) for x in units], [("ẹ", "H"), ("ọ", "L")])

    def test_decomposed_unicode(self):
        self.assertEqual(tone_sequence("e\u0323\u0301"), "H")

    def test_calibration_sentence(self):
        self.assertEqual(tone_sequence("Mo ní ìpàdé lọ́la."), "MHLLHHM")


if __name__ == "__main__":
    unittest.main()
