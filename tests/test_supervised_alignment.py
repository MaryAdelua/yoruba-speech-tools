import copy
import json
from pathlib import Path
import sys
import unittest
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_supervised_alignment import build


class SupervisedAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.reference=json.loads((ROOT/"evaluation/voice_interactions/supervised_alignment_001.json").read_text(encoding="utf-8"))

    def test_reference_marks_and_uncertainty(self):
        records,_=build(self.reference,[])
        self.assertEqual("".join(r["expected_reference_tone"] for r in records),"HHLHHLH")
        self.assertEqual(records[2]["reference_syllable"],"ọ̀")
        self.assertTrue(all(r["boundary_status"]=="PROPOSED_REQUIRES_NATIVE_REVIEW" for r in records))
        self.assertIn("FINAL_NASAL_SEQUENCE_UNRESOLVED",records[-1]["flags"])

    def test_boundary_ownership_preserves_raw_frame(self):
        frame={"timestamp_s":"0.94","window_start_s":"0.90","window_end_s":"0.98","f0_hz":"100","praat_f0_hz":"101","relative_pitch_semitones":"0","praat_relative_semitones":"0.1","signed_difference_semitones":"-0.17","flags":"original_flag"}
        original=copy.deepcopy(frame)
        records,frames=build(self.reference,[frame])
        self.assertEqual(frame,original)
        self.assertEqual(len(frames),1)
        self.assertEqual(frames[0]["unit_id"],2)
        self.assertTrue(frames[0]["pyin_window_crosses_proposed_boundary"])
        self.assertEqual(frames[0]["flags"],"original_flag")
        self.assertIsNone(records[0]["pyin_median_hz"])

    def test_invalid_boundary_rejected(self):
        self.reference["reference_units"][1]["start_s"]=.7
        with self.assertRaises(ValueError): build(self.reference,[])


if __name__=="__main__": unittest.main()
