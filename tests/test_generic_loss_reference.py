import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "method"))
from generic_loss_reference import masked_huber_f0, weighted_tone_cross_entropy


class GenericLossReferenceTests(unittest.TestCase):
    def test_perfect_tone_predictions_have_small_loss(self):
        logits = np.array([[[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]]])
        loss = weighted_tone_cross_entropy(logits, np.array([[0, 1]]), np.ones((1, 2)), np.ones((1, 2)))
        self.assertLess(loss, 0.001)

    def test_high_risk_error_receives_more_weight(self):
        logits = np.array([[[0.0, 10.0, 0.0], [10.0, 0.0, 0.0]]])
        targets = np.array([[0, 0]])
        mask = np.ones((1, 2))
        high_first = weighted_tone_cross_entropy(logits, targets, mask, np.array([[1.0, 0.25]]))
        low_first = weighted_tone_cross_entropy(logits, targets, mask, np.array([[0.25, 1.0]]))
        self.assertGreater(high_first, low_first)

    def test_fully_masked_losses_are_zero(self):
        logits = np.zeros((1, 1, 3))
        self.assertEqual(weighted_tone_cross_entropy(logits, np.array([[0]]), np.zeros((1, 1)), np.ones((1, 1))), 0.0)
        self.assertEqual(masked_huber_f0(np.ones(2), np.zeros(2), np.zeros(2), np.ones(2)), 0.0)

    def test_masked_huber_matches_expected_quadratic_region(self):
        loss = masked_huber_f0(np.array([0.5, 9.0]), np.array([0.0, 0.0]), np.array([1, 0]), np.array([1, 1]))
        self.assertAlmostEqual(loss, 0.125, places=6)


if __name__ == "__main__":
    unittest.main()

