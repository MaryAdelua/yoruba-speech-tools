import unittest,json,wave,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'work/slr86';OUT=B/'p03-mms-alignment-001'
class AlignmentOutput(unittest.TestCase):
 def test_audio_and_alignment_integrity(self):
  data=json.loads((OUT/'alignment.json').read_text(encoding='utf-8'));old=json.loads((B/'p03-supervised-001/annotation_package.json').read_text(encoding='utf-8'))
  self.assertEqual(data['reference_text'],old['exact_reference_text']);self.assertEqual(len(data['records']),5)
  for rec in data['records']:
   previous=next(r for r in old['records'] if r['id']==rec['id']);src=(B/'p03-supervised-001'/previous['audio_url']).resolve()
   self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),previous['audio_sha256'])
   with wave.open(str(src),'rb') as w:rate=w.getframerate();width=w.getnchannels()*w.getsampwidth();pcm=w.readframes(w.getnframes())
   self.assertEqual(len(rec['items']),10);end=0
   for item in rec['items']:
    self.assertGreaterEqual(item['ctc_start_s'],end);self.assertGreater(item['ctc_end_s'],item['ctc_start_s']);end=item['ctc_end_s']
    a=round(item['playback_start_s']*rate);b=round(item['playback_end_s']*rate)
    self.assertGreater(b,a);self.assertLessEqual(b*width,len(pcm))
    with wave.open(str(OUT/item['audio_file']),'rb') as w:self.assertEqual(w.readframes(w.getnframes()),pcm[a*width:b*width])
    for f in item['measurements']['frames']:self.assertTrue(item['ctc_start_s']<=f['timestamp_s']<item['ctc_end_s'])
 def test_accepted_cuts_preserved(self):
  for new,old in [('w01.wav','u01_candidate.wav'),('w02.wav','kuku_word_candidate.wav')]:self.assertEqual((OUT/'p03_natural'/new).read_bytes(),(B/'p03-alignment-repair-001'/old).read_bytes())
if __name__=='__main__':unittest.main()
