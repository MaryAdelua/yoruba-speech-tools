"""Unicode-safe Yoruba word and broad syllable units."""

from __future__ import annotations

import unicodedata
from copy import deepcopy


def grapheme_clusters(text: str, start: int, end: int) -> list[tuple[int, int, str]]:
    clusters = []
    i = start
    while i < end:
        j = i + 1
        while j < end and unicodedata.combining(text[j]):
            j += 1
        clusters.append((i, j, text[i:j]))
        i = j
    return clusters


def word_spans(text: str) -> list[tuple[int, int]]:
    """Tokenize letters with combining marks and internal apostrophes/hyphens."""
    spans = []
    start = None
    for index, char in enumerate(text):
        internal = char in {"'", "’", "-"} and start is not None
        valid = char.isalpha() or bool(unicodedata.combining(char)) or internal
        if valid and start is None:
            start = index
        elif not valid and start is not None:
            end = index
            while end > start and text[end - 1] in {"'", "’", "-"}:
                end -= 1
            if end > start:
                spans.append((start, end))
            start = None
    if start is not None:
        end = len(text)
        while end > start and text[end - 1] in {"'", "’", "-"}:
            end -= 1
        if end > start:
            spans.append((start, end))
    return spans


def _base(grapheme: str) -> str:
    return unicodedata.normalize("NFD", grapheme.lower())[0]


def syllable_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    clusters = grapheme_clusters(text, start, end)
    nuclei = [index for index, (_, _, grapheme) in enumerate(clusters) if _base(grapheme) in "aeiou"]
    if not nuclei:
        return [(start, end)]
    boundaries = [0]
    for nucleus in nuclei[1:]:
        onset = nucleus
        if nucleus > 0 and _base(clusters[nucleus - 1][2]) not in "aeiou":
            onset = nucleus - 1
            if nucleus > 1 and _base(clusters[nucleus - 2][2]) == "g" and _base(clusters[nucleus - 1][2]) == "b":
                onset = nucleus - 2
        boundaries.append(onset)
    boundaries.append(len(clusters))
    return [(clusters[boundaries[i]][0], clusters[boundaries[i + 1] - 1][1]) for i in range(len(boundaries) - 1)]


def words_and_syllables(text: str) -> list[dict]:
    text = unicodedata.normalize("NFC", text)
    words = []
    for word_index, (start, end) in enumerate(word_spans(text)):
        syllables = []
        for syllable_index, (s0, s1) in enumerate(syllable_spans(text, start, end)):
            syllables.append({
                "syllable_index": syllable_index, "orthographic_form": text[s0:s1],
                "character_start": s0, "character_end": s1,
            })
        words.append({
            "word_index": word_index, "text": text[start:end],
            "character_start": start, "character_end": end, "syllables": syllables,
        })
    return words


def _letters_without_tone(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", text).lower() if char.isalpha() and not unicodedata.combining(char))


def migrate_manual_word_groups(manual: dict, automatic: dict) -> dict | None:
    """Merge legacy split word records when they concatenate to NFC words."""
    old_words = manual.get("words", [])
    new_words = automatic.get("words", [])
    cursor = 0
    migrated = []
    groups = []
    for new_word in new_words:
        target = _letters_without_tone(new_word["text"])
        combined = ""
        group = []
        while cursor < len(old_words) and len(combined) < len(target):
            group.append(old_words[cursor])
            combined += _letters_without_tone(old_words[cursor].get("text", ""))
            cursor += 1
        if combined != target or not group:
            return None
        item = deepcopy(new_word)
        item["start_s"] = group[0]["start_s"]
        item["end_s"] = group[-1]["end_s"]
        migrated.append(item)
        groups.append([word.get("text") for word in group])
    if cursor != len(old_words):
        return None
    result = deepcopy(manual)
    result["words"] = migrated
    result["review_scope"] = "word_boundaries_migrated_orthographic_fix"
    result["orthographic_migration"] = {
        "version": "unicode_word_merge_v0.1", "legacy_word_groups": groups,
        "human_outer_boundaries_preserved": True, "syllable_boundaries": "automatic_requires_review",
    }
    return result
