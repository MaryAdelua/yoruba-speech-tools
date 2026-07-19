"""Low-confidence duration-weighted alignment for manual-review initialization."""

from __future__ import annotations


def allocate_intervals(items: list[dict], start_s: float, end_s: float, weight_key: str = "weight") -> list[dict]:
    """Allocate contiguous intervals in proportion to positive item weights."""
    if end_s <= start_s:
        raise ValueError("end_s must be greater than start_s")
    if not items:
        return []
    weights = [max(float(item.get(weight_key, 1.0)), 0.01) for item in items]
    total = sum(weights)
    duration = end_s - start_s
    cursor = start_s
    output = []
    for index, (item, weight) in enumerate(zip(items, weights)):
        item_end = end_s if index == len(items) - 1 else cursor + duration * weight / total
        output.append({**item, "start_s": round(cursor, 4), "end_s": round(item_end, 4)})
        cursor = item_end
    return output


def validate_intervals(intervals: list[dict], start_s: float, end_s: float, tolerance: float = 1e-3) -> list[str]:
    errors = []
    cursor = start_s
    for index, interval in enumerate(intervals):
        if interval["start_s"] < start_s - tolerance or interval["end_s"] > end_s + tolerance:
            errors.append(f"interval {index} lies outside parent")
        if interval["start_s"] < cursor - tolerance:
            errors.append(f"interval {index} overlaps previous interval")
        if interval["end_s"] <= interval["start_s"]:
            errors.append(f"interval {index} has nonpositive duration")
        cursor = interval["end_s"]
    return errors

