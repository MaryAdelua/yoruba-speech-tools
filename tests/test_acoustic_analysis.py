import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from acoustic_analysis import analyze, sha256, write_outputs


class AcousticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def audio(self, y, name="input.wav"):
        path = self.root/name
        sf.write(path, y, 24000, subtype="FLOAT")
        return path

    def sine(self, amplitude=.2):
        return amplitude*np.sin(2*np.pi*200*np.arange(24000)/24000)

    def test_known_pitch_duration_and_preservation(self):
        path = self.audio(self.sine())
        original = sha256(path)
        report, frames = analyze(path)
        self.assertEqual(sha256(path), original)
        self.assertEqual(report["summary"]["duration_s"], 1)
        self.assertEqual(len(frames), 100)
        self.assertAlmostEqual(report["summary"]["median_f0_hz"], 200, delta=3)
        self.assertGreater(report["summary"]["voiced_frames_percent"], 90)
        self.assertAlmostEqual(np.median([f["relative_pitch_semitones"] for f in frames if f["voiced"]]), 0, places=6)
        self.assertTrue(all(f["timestamp_s"] < 1 for f in frames))

    def test_silence_and_serializable_outputs(self):
        report, frames = analyze(self.audio(np.zeros(24000)))
        self.assertEqual(report["summary"]["voiced_frame_count"], 0)
        self.assertIsNone(report["summary"]["median_f0_hz"])
        self.assertTrue(all(f["f0_hz"] is None and f["rms_dbfs"] is None for f in frames))
        paths = write_outputs(report, frames, self.root/"out")
        parsed = json.loads(paths["json"].read_text())
        self.assertTrue(all(x["status"] == "UNSCORED" and x["score"] is None for x in parsed["scores"].values()))
        self.assertGreater(paths["png"].stat().st_size, 1000)
        self.assertEqual(len(paths["csv"].read_text().splitlines()), 101)
        with self.assertRaises(FileExistsError):
            write_outputs(report, frames, self.root/"out")

    def test_amplitude_change(self):
        _, quiet = analyze(self.audio(self.sine(.1), "quiet.wav"))
        _, loud = analyze(self.audio(self.sine(.2), "loud.wav"))
        difference = np.median([b["rms_dbfs"]-a["rms_dbfs"] for a,b in zip(quiet,loud)])
        self.assertAlmostEqual(difference, 20*np.log10(2), places=5)
        self.assertAlmostEqual(quiet[50]["rms_dbfs"], 20*np.log10(.1/np.sqrt(2)), delta=.1)

    def test_missing_invalid_empty_short_and_stereo(self):
        with self.assertRaises(FileNotFoundError):
            analyze(self.root/"missing.wav")
        broken = self.root/"broken.wav"
        broken.write_text("not audio")
        with self.assertRaises(ValueError):
            analyze(broken)
        for y in (np.zeros(0), np.zeros(100), np.zeros((24000,2))):
            with self.assertRaises(ValueError):
                analyze(self.audio(y))


if __name__ == "__main__":
    unittest.main()
