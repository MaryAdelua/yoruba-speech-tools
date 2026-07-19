import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from heuristic_alignment import allocate_intervals, validate_intervals


class HeuristicAlignmentTests(unittest.TestCase):
    def test_weighted_allocation_is_contiguous(self):
        intervals = allocate_intervals([{"weight": 1}, {"weight": 2}], 0.5, 3.5)
        self.assertEqual(intervals[0]["start_s"], 0.5)
        self.assertEqual(intervals[-1]["end_s"], 3.5)
        self.assertEqual(intervals[0]["end_s"], intervals[1]["start_s"])
        self.assertEqual(validate_intervals(intervals, 0.5, 3.5), [])

    def test_invalid_parent_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate_intervals([{"weight": 1}], 1.0, 1.0)


if __name__ == "__main__":
    unittest.main()
