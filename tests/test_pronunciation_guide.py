import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pronunciation_guide import concise_guided_prompt, guided_prompt, word_tone_plan, words


class PronunciationGuideTests(unittest.TestCase):
    def test_word_tokenization_preserves_yoruba_letters(self):
        self.assertEqual(words("Má fọ́ ife náà."), ["Má", "fọ́", "ife", "náà"])
        self.assertEqual(words("Jọ̀wọ́, yára dé síbí."), ["Jọ̀wọ́", "yára", "dé", "síbí"])

    def test_word_tone_plan(self):
        self.assertEqual(
            word_tone_plan("Adé kọ̀ láti lọ."),
            "Adé[M-H] | kọ̀[L] | láti[H-M] | lọ[M]",
        )

    def test_guided_prompt_keeps_original_output(self):
        sentence = "Ìlú náà tóbi."
        prompt = guided_prompt(sentence, "Ìlú", "L-H", "town")
        self.assertTrue(prompt.endswith(f"OUTPUT: {sentence}"))
        self.assertIn("Ìlú[L-H]", prompt)
        self.assertIn("means “town”", prompt)

    def test_syllabic_nasal_gets_tone(self):
        self.assertIn("ń[H]", word_tone_plan("Ọmọ náà ń lu ìlù."))

    def test_concise_prompt_contains_only_critical_tone_cue(self):
        prompt = concise_guided_prompt("Yàrá náà mọ́.", "Yàrá", "L-H", "room")
        self.assertEqual(
            prompt,
            "Say exactly: “Yàrá náà mọ́.” Cue: Yàrá is LOW-HIGH and means room. Nothing else.",
        )
        self.assertLess(len(prompt.split()), 20)


if __name__ == "__main__":
    unittest.main()
