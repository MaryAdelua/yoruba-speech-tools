"""Framework-neutral NumPy reference for portable Yoruba tone losses.

This module validates semantics and numerical behavior. Production integrations
should implement equivalent differentiable operations in their host framework.
"""

from __future__ import annotations

import numpy as np


EPSILON = 1e-8


def _log_softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    return shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))


def weighted_tone_cross_entropy(
    tone_logits: np.ndarray,
    tone_targets: np.ndarray,
    tone_mask: np.ndarray,
    meaning_risk_weights: np.ndarray,
) -> float:
    """Return normalized meaning-risk-weighted H/M/L cross entropy."""
    logits = np.asarray(tone_logits, dtype=np.float64)
    targets = np.asarray(tone_targets, dtype=np.int64)
    mask = np.asarray(tone_mask, dtype=np.float64)
    weights = np.asarray(meaning_risk_weights, dtype=np.float64)
    if logits.shape[:-1] != targets.shape or logits.shape[-1] != 3:
        raise ValueError("tone_logits must have shape tone_targets + (3,)")
    if mask.shape != targets.shape or weights.shape != targets.shape:
        raise ValueError("mask and weights must match tone_targets")
    if np.any((targets < 0) | (targets > 2)) or np.any(weights < 0):
        raise ValueError("targets must be 0..2 and weights must be nonnegative")
    active = mask * weights
    denominator = float(np.sum(active))
    if denominator <= 0:
        return 0.0
    log_probs = _log_softmax(logits)
    losses = -np.take_along_axis(log_probs, targets[..., None], axis=-1)[..., 0]
    return float(np.sum(losses * active) / (denominator + EPSILON))


def masked_huber_f0(
    predicted_normalized_f0: np.ndarray,
    reference_normalized_f0: np.ndarray,
    voiced_mask: np.ndarray,
    unit_mask: np.ndarray,
    delta: float = 1.0,
) -> float:
    """Return Huber loss over voiced frames inside valid tone-bearing units."""
    predicted = np.asarray(predicted_normalized_f0, dtype=np.float64)
    reference = np.asarray(reference_normalized_f0, dtype=np.float64)
    voiced = np.asarray(voiced_mask, dtype=np.float64)
    valid = np.asarray(unit_mask, dtype=np.float64)
    if not (predicted.shape == reference.shape == voiced.shape == valid.shape):
        raise ValueError("all F0 arrays and masks must have identical shapes")
    if delta <= 0:
        raise ValueError("delta must be positive")
    active = voiced * valid
    denominator = float(np.sum(active))
    if denominator <= 0:
        return 0.0
    absolute = np.abs(predicted - reference)
    loss = np.where(absolute <= delta, 0.5 * absolute**2, delta * (absolute - 0.5 * delta))
    return float(np.sum(loss * active) / (denominator + EPSILON))

