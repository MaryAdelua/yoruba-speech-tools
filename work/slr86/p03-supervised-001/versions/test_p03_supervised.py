import unittest,sys,json,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_p03_supervised import spectral,OUT
class P03(unittest.TestCase):
 def test_spectral_gain_and_sample_rate(self):
  med=[]
  for sr in [24000,48000]:
   y=.1*np.sin(2*np.pi*200*np.arange(sr)/sr);a=spectral(y,sr);b=spectral(y/2,sr)
   self.assertAlmostEqual(a[0]['rms_dbfs']-b[0]['rms_dbfs'],6.0206,places=3)
   self.assertAlmostEqual(a[0]['spectral_centroid_hz'],b[0]['spectral_centroid_hz'],places=6)
   med.append(a[0]['spectral_centroid_hz'])
  self.assertLess(abs(med[0]-med[1]),1)
  self.assertIsNone(spectral(np.zeros(24000),24000)[0]['spectral_centroid_hz'])
 def test_intact_five_recordings(self):
  p=json.loads((OUT/'annotation_package.json').read_text(encoding='utf-8'));self.assertEqual(len(p['records']),5)
  for r in p['records']:
   self.assertEqual(len(r['segments']),17)
   self.assertTrue(all(s['boundary_review']=='unverified' for s in r['segments']))
   end=0
   for s in r['segments']:
    self.assertLessEqual(end,s['start_s']);self.assertLess(s['start_s'],s['end_s']);end=s['end_s']
   self.assertLessEqual(end,r['duration_s'])
  for f in json.loads((OUT/'provenance.json').read_text())['inputs']:self.assertEqual(hashlib.sha256(Path(f['path']).read_bytes()).hexdigest(),f['sha256'])
if __name__=='__main__':unittest.main()
