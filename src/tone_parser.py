"""Extract Yoruba vowel nuclei and orthographic H/M/L tone labels.

This Unicode-safe component represents lexical/orthographic tone. It does not
attempt to predict context-conditioned surface tone, downstep, or elision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import unicodedata


VOWELS = {"a", "e", "ẹ", "i", "o", "ọ", "u"}
HIGH = "\u0301"
LOW = "\u0300"
UNDERDOT = "\u0323"


@dataclass(frozen=True)
class ToneUnit:
    grapheme: str
    base_vowel: str
    tone: str
    character_start: int
    character_end: int


def _canonical_grapheme(base: str, marks: list[str]) -> str:
    return unicodedata.normalize("NFC", base + "".join(marks))


def extract_tone_units(text: str) -> list[ToneUnit]:
    """Return vowel nuclei with orthographic H, M, or L tone labels."""
    units: list[ToneUnit] = []
    i = 0
    while i < len(text):
        char = text[i]
        decomposed = unicodedata.normalize("NFD", char)
        base = decomposed[0].lower() if decomposed else char.lower()
        marks = list(decomposed[1:])
        j = i + 1
        while j < len(text) and unicodedata.combining(text[j]):
            marks.append(text[j])
            j += 1
        lowered = _canonical_grapheme(base, [mark for mark in marks if mark == UNDERDOT]).lower()
        if lowered in VOWELS:
            tone = "H" if HIGH in marks else "L" if LOW in marks else "M"
            units.append(
                ToneUnit(
                    grapheme=_canonical_grapheme(base, marks),
                    base_vowel=lowered,
                    tone=tone,
                    character_start=i,
                    character_end=j,
                )
            )
        i = max(j, i + 1)
    return units


def tone_sequence(text: str) -> str:
    return "".join(unit.tone for unit in extract_tone_units(text))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    args = parser.parse_args()
    print(json.dumps([asdict(unit) for unit in extract_tone_units(args.text)], ensure_ascii=False, indent=2))
