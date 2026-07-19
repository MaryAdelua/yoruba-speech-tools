import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_portable_dataset_metadata import validate_record


class PortableMetadataValidationTests(unittest.TestCase):
    def valid_record(self):
        return {
            "schema_version": "0.2",
            "utterance_id": "speaker01_0001",
            "speaker_id": "speaker01",
            "language": "yo",
            "text": "kọ́",
            "audio": {"sample_rate_hz": 24000, "channels": 1, "sample_format": "PCM_S16LE"},
            "split": "diagnostic",
            "split_group_id": "group-1",
            "benchmark_exclusion": True,
            "tone_units": [{"unit_index": 0, "tone": "H", "character_start": 1, "character_end": 2, "annotation_provenance": "derived", "meaning_risk_weight": None}],
            "verification": {},
        }

    def test_valid_record(self):
        self.assertEqual(validate_record(self.valid_record()), [])

    def test_invalid_tone_is_rejected(self):
        record = self.valid_record()
        record["tone_units"][0]["tone"] = "X"
        self.assertTrue(any("invalid tone" in error for error in validate_record(record)))

    def test_noncanonical_audio_is_rejected(self):
        record = self.valid_record()
        record["audio"]["sample_rate_hz"] = 16000
        self.assertTrue(any("canonical" in error for error in validate_record(record)))

    def test_benchmark_item_cannot_enter_training_split(self):
        record = self.valid_record()
        record["split"] = "train"
        self.assertTrue(any("cannot be assigned to train" in error for error in validate_record(record)))


if __name__ == "__main__":
    unittest.main()
