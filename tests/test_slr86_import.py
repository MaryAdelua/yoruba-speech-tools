import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from slr86_import import inspect_text,select_pilot,RangeFile


class SlrTests(unittest.TestCase):
    def test_selection_reproducible_not_first_items(self):
        items=[{'source_item_id':f'{g}_{s:05}_{i:011}','speaker_id':f'{g}_{s:05}','released_gender_group':g,'text_quality':{'annotations':[]}}
               for g in ('female','male') for s in range(9) for i in range(20)]
        a,s=select_pilot(items);b,t=select_pilot(list(reversed(items)))
        self.assertEqual(a,b);self.assertEqual(len(a),120);self.assertEqual(len(s),12)
        self.assertNotEqual(a,select_pilot(items,seed=42)[0])
        self.assertEqual(len({r['source_item_id'] for r in a}),120)

    def test_text_does_not_restore_tones(self):
        q=inspect_text('e ẹ o ọ á à a [breath]')
        self.assertEqual(q['vowel_units'],7);self.assertEqual(q['explicit_tone_units'],2)
        self.assertEqual(q['unmarked_vowel_units'],5)
        self.assertEqual(q['vowel_counts']['ẹ'],1)
        self.assertEqual(inspect_text('a n')['nasal_vowel_spelling_candidates'],0)
        self.assertEqual(inspect_text('á\u0300')['conflicting_tone_units'],1)

    def test_refuses_full_archive_without_reading_body(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):raise AssertionError('Must not consume full archive')
        r=RangeFile.__new__(RangeFile);r.url='https://example.invalid/a.zip';r.size=1000;r.pos=0;r.used=0;r.budget=1000;r.etag=None;r.log=[]
        with patch('urllib.request.urlopen',return_value=Response()):
            with self.assertRaisesRegex(RuntimeError,'approval'):r.read(10)


if __name__=='__main__':unittest.main()
