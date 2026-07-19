"""Generate silent, tone-aware pronunciation plans for Yoruba voice prompts.

The guide represents orthographic tone targets. It does not claim to model
surface-tone processes such as downstep, elision, or coarticulation.
"""

from __future__ import annotations

import unicodedata

from tone_parser import tone_sequence


def words(text: str) -> list[str]:
    """Return NFC-normalized Yoruba word tokens without punctuation."""
    tokens: list[str] = []
    current: list[str] = []
    for character in text:
        if character.isalpha() or (current and unicodedata.combining(character)):
            current.append(character)
        elif current:
            tokens.append(unicodedata.normalize("NFC", "".join(current)))
            current = []
    if current:
        tokens.append(unicodedata.normalize("NFC", "".join(current)))
    return tokens


def _token_tones(word: str) -> str:
    tones = tone_sequence(word)
    if tones:
        return tones

    # Yoruba syllabic nasals can bear tone even though the vowel-nucleus parser
    # intentionally excludes consonants.
    decomposed = unicodedata.normalize("NFD", word)
    if any(character in {"\u0301", "\u0300"} for character in decomposed):
        return "H" if "\u0301" in decomposed else "L"
    return "M"


def word_tone_plan(text: str) -> str:
    """Return a compact word-to-orthographic-tone representation."""
    parts = []
    for word in words(text):
        tones = "-".join(_token_tones(word))
        parts.append(f"{word}[{tones}]")
    return " | ".join(parts)


def guided_prompt(
    sentence: str,
    focus_word: str,
    focus_tones: str,
    intended_meaning: str,
) -> str:
    """Build a prompt whose instructions and tone plan must remain unspoken."""
    plan = word_tone_plan(sentence)
    return (
        "Read aloud only the Yoruba sentence after OUTPUT. Say no instructions, "
        "labels, explanations, or symbols. Silently follow this Yoruba pronunciation "
        "plan: H means high pitch, M means mid level pitch, and L means low pitch. "
        "Preserve the underdotted vowels ẹ and ọ. Keep every written word. "
        f"WORD TONES: {plan}. "
        f"MEANING-CRITICAL TARGET: {focus_word}[{focus_tones}] means “{intended_meaning}”. "
        f"OUTPUT: {sentence}"
    )


def concise_guided_prompt(
    sentence: str,
    focus_word: str,
    focus_tones: str,
    intended_meaning: str,
) -> str:
    """Build a short functional-load cue for fragile voice interfaces.

    Only the meaning-critical word is annotated. This keeps the intervention
    focused while minimizing truncation and instruction leakage.
    """
    tone_names = {"H": "HIGH", "M": "MID", "L": "LOW"}
    spoken_tones = "-".join(tone_names[tone] for tone in focus_tones.split("-"))
    return (
        f"Say exactly: “{sentence}” "
        f"Cue: {focus_word} is {spoken_tones} and means {intended_meaning}. "
        "Nothing else."
    )
