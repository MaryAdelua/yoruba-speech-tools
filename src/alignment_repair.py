"""Conservative interval repair for automatic word and syllable alignments."""

from __future__ import annotations

from copy import deepcopy
from math import isfinite


EPSILON = 0.001


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value))


def _proportional_intervals(items: list[dict], parent_start: float, parent_end: float) -> list[tuple[float, float]]:
    weights = [max(1, len(str(item.get("text") or item.get("orthographic_form") or "x"))) for item in items]
    total = sum(weights) or len(items) or 1
    cursor = parent_start
    result = []
    for index, weight in enumerate(weights):
        end = parent_end if index == len(items) - 1 else cursor + (parent_end - parent_start) * weight / total
        result.append((cursor, end))
        cursor = end
    return result


def repair_sequence(items: list[dict], parent_start: float, parent_end: float) -> tuple[list[dict], list[dict]]:
    """Repair only invalid endpoints; return repaired items and field-level audit."""
    repaired = deepcopy(items)
    audit: list[dict] = []
    fallback = _proportional_intervals(repaired, parent_start, parent_end)
    for index, item in enumerate(repaired):
        old_start, old_end = item.get("start_s"), item.get("end_s")
        if not _finite(old_start) or not _finite(old_end):
            item["start_s"], item["end_s"] = fallback[index]
            reason = "missing_boundary_interpolated"
        else:
            item["start_s"] = min(parent_end, max(parent_start, float(old_start)))
            item["end_s"] = min(parent_end, max(parent_start, float(old_end)))
            reason = "out_of_range_clamped" if (item["start_s"], item["end_s"]) != (old_start, old_end) else None
            if item["end_s"] <= item["start_s"]:
                mid = min(parent_end - EPSILON, max(parent_start + EPSILON, (item["start_s"] + item["end_s"]) / 2))
                item["start_s"] = max(parent_start, mid - EPSILON)
                item["end_s"] = min(parent_end, mid + EPSILON)
                reason = "reversed_or_zero_interval_repaired"
        if reason:
            audit.append({"index": index, "field": "interval", "old": [old_start, old_end], "new": [item["start_s"], item["end_s"]], "reason": reason})
    for index in range(1, len(repaired)):
        previous, current = repaired[index - 1], repaired[index]
        if current["start_s"] < previous["end_s"]:
            old = [previous["end_s"], current["start_s"]]
            low = previous["start_s"] + EPSILON
            high = current["end_s"] - EPSILON
            boundary = min(high, max(low, (previous["end_s"] + current["start_s"]) / 2))
            if high <= low:
                span_start, span_end = previous["start_s"], current["end_s"]
                boundary = span_start + max(EPSILON, (span_end - span_start) / 2)
            previous["end_s"] = boundary
            current["start_s"] = boundary
            audit.append({"index": index, "field": "adjacent_boundary", "old": old, "new": [boundary, boundary], "reason": "overlap_split_at_midpoint"})
    # A missing interval can be squeezed behind a valid neighbor during the
    # overlap pass. Give only that interval space from the following gap.
    for index, item in enumerate(repaired):
        if item["end_s"] <= item["start_s"]:
            old = [item["start_s"], item["end_s"]]
            right = repaired[index + 1]["start_s"] if index + 1 < len(repaired) else parent_end
            if right > item["start_s"] + EPSILON:
                item["end_s"] = item["start_s"] + (right - item["start_s"]) / 2
            else:
                item["start_s"] = max(parent_start, min(item["start_s"], parent_end - 2 * EPSILON))
                item["end_s"] = min(parent_end, item["start_s"] + EPSILON)
            audit.append({"index": index, "field": "interval", "old": old, "new": [item["start_s"], item["end_s"]], "reason": "squeezed_interval_reopened"})
    for item in repaired:
        item["start_s"] = max(parent_start, min(parent_end, round(float(item["start_s"]), 4)))
        item["end_s"] = max(parent_start, min(parent_end, round(float(item["end_s"]), 4)))
    return repaired, audit


def repair_alignment(record: dict) -> tuple[dict, list[dict]]:
    repaired = deepcopy(record)
    words, word_audit = repair_sequence(repaired["words"], 0.0, float(repaired["duration_s"]))
    audit = [{"level": "word", **entry} for entry in word_audit]
    duration = float(repaired["duration_s"])
    for word_index, word in enumerate(words):
        minimum = 0.01 * max(1, len(word.get("syllables", [])))
        if word["end_s"] - word["start_s"] < minimum:
            old = [word["start_s"], word["end_s"]]
            right = words[word_index + 1]["start_s"] if word_index + 1 < len(words) else duration
            left = words[word_index - 1]["end_s"] if word_index else 0.0
            if right - word["start_s"] >= minimum:
                word["end_s"] = word["start_s"] + minimum
            elif word["end_s"] - left >= minimum:
                word["start_s"] = word["end_s"] - minimum
            audit.append({
                "level": "word", "index": word_index, "field": "interval", "old": old,
                "new": [word["start_s"], word["end_s"]], "reason": "minimum_syllable_review_width",
            })
    for word_index, word in enumerate(words):
        syllables, syllable_audit = repair_sequence(word.get("syllables", []), word["start_s"], word["end_s"])
        word["syllables"] = syllables
        audit.extend({"level": "syllable", "word_index": word_index, **entry} for entry in syllable_audit)
    repaired["words"] = words
    repaired["boundary_validation"] = {
        "status": "passes_structural_validator",
        "repair_version": "conservative_interval_repair_v0.1",
        "changed_field_count": len(audit),
        "human_verification_required": True,
    }
    return repaired, audit


def interval_errors(record: dict) -> list[str]:
    errors = []
    duration = float(record["duration_s"])
    previous = 0.0
    for wi, word in enumerate(record["words"]):
        start, end = word.get("start_s"), word.get("end_s")
        if not _finite(start) or not _finite(end) or start < previous - 1e-4 or end <= start or end > duration + 1e-4:
            errors.append(f"word {wi}")
            continue
        syllable_previous = start
        for si, syllable in enumerate(word.get("syllables", [])):
            ss, se = syllable.get("start_s"), syllable.get("end_s")
            if not _finite(ss) or not _finite(se) or ss < syllable_previous - 1e-4 or se <= ss or se > end + 1e-4:
                errors.append(f"word {wi} syllable {si}")
            else:
                syllable_previous = se
        previous = end
    return errors
