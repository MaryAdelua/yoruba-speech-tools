"""Acoustic token-to-reference alignment for Yoruba Omnilingual ASR output.

Original NFC orthography is immutable. A separate comparison form is used only
for dynamic-programming alignment, with every comparison character mapped back
to its source grapheme.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


WORD_RE = re.compile(r"[^\W\d_]+(?:[’'][^\W\d_]+)*", re.UNICODE)


@dataclass(frozen=True)
class ComparisonText:
    original_nfc: str
    text: str
    source_spans: tuple[tuple[int, int], ...]


def comparison_text(text: str) -> ComparisonText:
    """Return lowercase letters/spaces plus a reversible source-span map."""
    original = unicodedata.normalize("NFC", text)
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    pending_space = False
    # Python's re has no grapheme token; grouping a base with following marks is enough here.
    i = 0
    while i < len(original):
        j = i + 1
        while j < len(original) and unicodedata.combining(original[j]):
            j += 1
        grapheme = original[i:j]
        if any(ch.isalpha() for ch in grapheme):
            if pending_space and chars:
                chars.append(" ")
                spans.append((i, i))
            pending_space = False
            folded = unicodedata.normalize("NFC", grapheme.lower())
            for ch in folded:
                chars.append(ch)
                spans.append((i, j))
        elif grapheme.isspace() or grapheme in "-–—":
            pending_space = True
        i = j
    return ComparisonText(original, "".join(chars), tuple(spans))


def align_characters(reference: str, hypothesis: str) -> tuple[dict[int, int], int]:
    """Levenshtein-align hypothesis to reference and return ref->hyp matches."""
    n, m = len(reference), len(hypothesis)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[""] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0], back[i][0] = i, "D"
    for j in range(1, m + 1):
        dp[0][j], back[0][j] = j, "I"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            candidates = [
                (dp[i - 1][j - 1] + (reference[i - 1] != hypothesis[j - 1]), "M"),
                (dp[i - 1][j] + 1, "D"),
                (dp[i][j - 1] + 1, "I"),
            ]
            dp[i][j], back[i][j] = min(candidates, key=lambda x: x[0])
    mapping: dict[int, int] = {}
    i, j = n, m
    while i or j:
        op = back[i][j]
        if op == "M":
            if reference[i - 1] == hypothesis[j - 1]:
                mapping[i - 1] = j - 1
            i -= 1
            j -= 1
        elif op == "D":
            i -= 1
        else:
            j -= 1
    return mapping, dp[n][m]


def _token_end(times: list[float], index: int, duration_s: float) -> float:
    if index + 1 < len(times):
        return min(duration_s, max(times[index] + 0.02, times[index + 1]))
    return min(duration_s, times[index] + 0.08)


def build_alignment(annotation: dict, decoded_text: str, timestamps: list[float], duration_s: float) -> dict:
    original = unicodedata.normalize("NFC", annotation["text_nfc"])
    ref = comparison_text(original)
    hyp = comparison_text(decoded_text)
    mapping, distance = align_characters(ref.text, hyp.text)
    words_out = []
    for word in annotation["words"]:
        start, end = word["character_start"], word["character_end"]
        ref_indices = [k for k, span in enumerate(ref.source_spans) if span[0] >= start and span[1] <= end]
        matched = [mapping[k] for k in ref_indices if k in mapping and mapping[k] < len(timestamps)]
        confidence = len(matched) / max(1, len(ref_indices))
        if matched:
            ws = max(0.0, timestamps[min(matched)] - 0.02)
            we = _token_end(timestamps, max(matched), duration_s)
            source = "acoustic_token_match"
        else:
            ws = we = None
            source = "unresolved"
        syllables = []
        raw_syllables = word.get("syllables", [])
        for si, syllable in enumerate(raw_syllables):
            s0, s1 = syllable["character_start"], syllable["character_end"]
            indices = [k for k, span in enumerate(ref.source_spans) if span[0] >= s0 and span[1] <= s1]
            sm = [mapping[k] for k in indices if k in mapping and mapping[k] < len(timestamps)]
            if sm:
                ss = max(0.0, timestamps[min(sm)] - 0.02)
                se = _token_end(timestamps, max(sm), duration_s)
                ss_source = "acoustic_token_match"
            elif ws is not None and raw_syllables:
                ss = ws + (we - ws) * si / len(raw_syllables)
                se = ws + (we - ws) * (si + 1) / len(raw_syllables)
                ss_source = "within_word_interpolation"
            else:
                ss = se = None
                ss_source = "unresolved"
            syllables.append({
                "syllable_index": si, "orthographic_form": syllable["orthographic_form"],
                "start_s": None if ss is None else round(ss, 4),
                "end_s": None if se is None else round(se, 4),
                "confidence": round(len(sm) / max(1, len(indices)), 4), "boundary_source": ss_source,
            })
        words_out.append({
            "word_index": word["word_index"], "text": word["text"],
            "character_start": start, "character_end": end,
            "start_s": None if ws is None else round(ws, 4), "end_s": None if we is None else round(we, 4),
            "confidence": round(confidence, 4), "boundary_source": source, "syllables": syllables,
        })
    return {
        "schema_version": "0.1", "prompt_id": annotation["prompt_id"],
        "text_nfc": original, "comparison_text": ref.text, "decoded_text_nfc": hyp.original_nfc,
        "audio_path": annotation["audio_path"], "duration_s": duration_s,
        "alignment_method": "omnilingual_asr_ctc_token_match_v0.1",
        "confidence_definition": "exact reference-character match ratio after minimum-edit alignment; not a calibrated posterior",
        "utterance_confidence": round(sum(1 for k in mapping if ref.text[k] != " ") / max(1, len(ref.text.replace(" ", ""))), 4),
        "edit_distance": distance, "automatic_status": "requires_human_verification",
        "words": words_out,
    }


def validate_manual_correction(record: dict, automatic: dict) -> list[str]:
    errors: list[str] = []
    if record.get("prompt_id") != automatic.get("prompt_id"):
        errors.append("prompt_id does not match automatic alignment")
    if record.get("review_status") != "human_verified":
        errors.append("review_status must be human_verified")
    duration = float(automatic["duration_s"])
    automatic_words = automatic.get("words", [])
    if len(record.get("words", [])) != len(automatic_words):
        errors.append("word count does not match automatic alignment")
    previous = 0.0
    for idx, word in enumerate(record.get("words", [])):
        start, end = float(word["start_s"]), float(word["end_s"])
        if start < previous or end <= start or end > duration + 1e-3:
            errors.append(f"word {idx} has invalid or non-monotonic boundaries")
        if idx < len(automatic_words) and word.get("text") != automatic_words[idx].get("text"):
            errors.append(f"word {idx} text does not match authoritative transcript")
        previous = end
    return errors
