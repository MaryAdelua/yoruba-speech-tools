import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from explore_human_acoustics import deltas
class AssociationTests(unittest.TestCase):
 def test_identity_and_missing_contour_bins(self):
  row={'duration_s':2,'pyin_voiced_percent':50,'pyin_relative_width90_st':4,'relative_contour_bins_st':[1,None,3],'screened_contour_bins_st':[None,None,None],'voiced_runs_per_second':2,'pitch_disagreement_median_st':.1,'voicing_disagreement_percent':5}
  result=deltas(row,row)
  self.assertEqual(result['duration_ratio'],1);self.assertEqual(result['coarse_relative_contour_difference_st'],0)
  self.assertEqual(result['coarse_contour_common_bins'],2);self.assertIsNone(result['screened_coarse_contour_difference_st'])
  self.assertEqual(result['screened_common_bins'],0)
 def test_signed_differences_and_common_bins_only(self):
  n={'duration_s':2,'pyin_voiced_percent':50,'pyin_relative_width90_st':4,'relative_contour_bins_st':[1,None,3],'screened_contour_bins_st':[1,None,None],'voiced_runs_per_second':2,'pitch_disagreement_median_st':.1,'voicing_disagreement_percent':5}
  a={**n,'duration_s':4,'pyin_voiced_percent':40,'pyin_relative_width90_st':3,'relative_contour_bins_st':[3,100,1]}
  d=deltas(n,a);self.assertEqual(d['duration_ratio'],2);self.assertEqual(d['voiced_percent_delta_pp'],-10);self.assertEqual(d['relative_width90_delta_st'],-1);self.assertEqual(d['coarse_relative_contour_difference_st'],2)
if __name__=='__main__':unittest.main()
