import sys,tempfile,unittest
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_speech_models import amplitude
class SignalDescriptors(unittest.TestCase):
 def test_gain_and_padding(self):
  sr=24000;y=.1*np.sin(2*np.pi*200*np.arange(sr)/sr)
  with tempfile.TemporaryDirectory() as d:
   paths=[Path(d)/f'{i}.wav' for i in range(3)]
   for p,a in zip(paths,[y,y/2,np.r_[y,np.zeros(sr)]]):sf.write(p,a,sr,subtype='FLOAT')
   frames=[{'timestamp_s':i*.01,'voiced':True,'rms_dbfs':-23.01} for i in range(100)]
   a,b,c=[amplitude(p,frames) for p in paths]
   self.assertAlmostEqual(a['whole_rms_dbfs']-b['whole_rms_dbfs'],6.0206,places=3)
   self.assertAlmostEqual(a['whole_rms_dbfs']-c['whole_rms_dbfs'],3.0103,places=3)
   self.assertAlmostEqual(a['active_above_40_rms_dbfs'],c['active_above_40_rms_dbfs'],places=5)
   self.assertAlmostEqual(a['active_above_40_s'],1,places=5)
   self.assertIsNone(a['verified_speaking_duration_s'])
if __name__=='__main__':unittest.main()
