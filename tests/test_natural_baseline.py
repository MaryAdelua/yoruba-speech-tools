"""Baseline regression tests: measurements, selection and conservative eligibility."""
import json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_natural_baseline as b
from validate_acoustic_measurements import compare

class NaturalBaselineTests(unittest.TestCase):
    def test_quantiles_and_empty(self):
        self.assertEqual(b.dist([])['median'],None)
        self.assertEqual(b.dist([None,100,200,300])['median'],200)
        self.assertAlmostEqual(12*np.log2(200/100),12)
    def test_48khz_known_pitch_and_no_signal_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'tone.wav';sr=48000;t=np.arange(sr)/sr
            sf.write(p,.2*np.sin(2*np.pi*180*t),sr,subtype='PCM_16');before=p.read_bytes()
            report,frames,raw,_=compare(p,frame_length=4096)
            self.assertEqual(p.read_bytes(),before)
            self.assertAlmostEqual(report['method']['window_duration_s'],2048/24000)
            for key in ['f0_hz','praat_f0_hz']:
                values=[f[key] for f in frames if .15<f['timestamp_s']<.85 and f[key]]
                self.assertGreater(len(values),60)
                self.assertLess(abs(1200*np.log2(np.median(values)/180)),30)
            self.assertTrue(any(f['praat_voiced'] is None for f in frames))
    def test_qc_sample_contract(self):
        q=json.loads((b.OUT/'qc_sample.json').read_text(encoding='utf-8'))['items']
        self.assertEqual(len(q),20);self.assertEqual(len({r['speaker_id'] for r in q}),12)
        self.assertTrue({'yof_09697_01759056954','yom_01523_01656064431'}<={r['source_id'] for r in q})
        self.assertTrue(all(r['judgment'] is None for r in q))
        tone=json.loads((b.OUT/'tone_subset.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(tone['categories'].values()),120)
        self.assertEqual(tone['categories']['suitable_for_lexical_tone_analysis'],0)

if __name__=='__main__':unittest.main()
