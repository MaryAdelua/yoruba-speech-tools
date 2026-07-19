"""Auditable first-pass Yoruba grapheme, phoneme, syllable, and tone annotation.

The output is a broad orthography-derived pronunciation representation. It is
not a claim about narrow phonetic realization or connected-speech surface tone.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import unicodedata

from tone_parser import extract_tone_units


VOWELS = {"a", "e", "ẹ", "i", "o", "ọ", "u"}
IPA = {
    "a": "a", "b": "b", "d": "d", "e": "e", "ẹ": "ɛ",
    "f": "f", "g": "ɡ", "gb": "ɡ͡b", "h": "h", "i": "i",
    "j": "dʒ", "k": "k", "l": "l", "m": "m", "n": "n",
    "o": "o", "ọ": "ɔ", "p": "k͡p", "r": "ɾ", "s": "s",
    "ṣ": "ʃ", "t": "t", "u": "u", "w": "w", "y": "j",
}


def base_grapheme(grapheme: str) -> str:
    decomposed = unicodedata.normalize("NFD", grapheme.lower())
    base = decomposed[0]
    return unicodedata.normalize("NFC", base + ("\u0323" if "\u0323" in decomposed else ""))


def grapheme_clusters(text: str, offset: int = 0) -> list[dict]:
    clusters = []
    i = 0
    while i < len(text):
        j = i + 1
        while j < len(text) and unicodedata.combining(text[j]):
            j += 1
        clusters.append({"text": text[i:j], "start": offset + i, "end": offset + j})
        i = j
    return clusters


def word_tokens(text: str) -> list[dict]:
    tokens = []
    start = None
    for i, char in enumerate(text):
        valid = char.isalpha() or unicodedata.combining(char) or (char == "-" and start is not None)
        if valid and start is None:
            start = i
        elif not valid and start is not None:
            end = i
            token = text[start:end].rstrip("-")
            if token:
                tokens.append({"text": token, "start": start, "end": start + len(token)})
            start = None
    if start is not None:
        token = text[start:].rstrip("-")
        if token:
            tokens.append({"text": token, "start": start, "end": start + len(token)})
    return tokens


def phonemes_for_word(word: dict) -> tuple[list[dict], list[str]]:
    clusters = [c for c in grapheme_clusters(word["text"], word["start"]) if c["text"] != "-"]
    units = []
    flags = []
    i = 0
    while i < len(clusters):
        current = base_grapheme(clusters[i]["text"])
        if i + 1 < len(clusters) and current == "g" and base_grapheme(clusters[i + 1]["text"]) == "b":
            source = "gb"
            end = clusters[i + 1]["end"]
            i += 2
        else:
            source = current
            end = clusters[i]["end"]
            i += 1
        ipa = IPA.get(source)
        if ipa is None:
            flags.append(f"unmapped_grapheme:{source}")
            ipa = "?"
        units.append({
            "source_grapheme": source,
            "phoneme": ipa,
            "character_start": clusters[i - 1]["start"] if source != "gb" else clusters[i - 2]["start"],
            "character_end": end,
            "annotation_provenance": "automatic_rule",
            "is_vowel": source in VOWELS,
        })
    # In Yoruba orthography, n after a vowel represents nasalization when it
    # occurs word-finally or before another consonant. Before a vowel it is an
    # onset (for example, inú -> i-nú). Keep this explicit and reviewable.
    normalized = []
    for index, unit in enumerate(units):
        next_unit = units[index + 1] if index + 1 < len(units) else None
        if (
            unit["source_grapheme"] == "n"
            and normalized
            and normalized[-1]["is_vowel"]
            and (next_unit is None or not next_unit["is_vowel"])
        ):
            previous = normalized[-1]
            previous["source_grapheme"] += "n"
            previous["phoneme"] += "̃"
            previous["character_end"] = unit["character_end"]
            previous["nasalization_source"] = "orthographic_vowel_plus_n"
            flags.append("nasal_vowel_requires_review")
            continue
        normalized.append(unit)
    units = normalized
    if "-" in word["text"]:
        flags.append("compound_boundary_requires_review")
    return units, sorted(set(flags))


def syllables_for_word(word: dict, phonemes: list[dict]) -> tuple[list[dict], list[str]]:
    flags = []
    syllables: list[list[dict]] = []
    pending_onset: list[dict] = []
    for unit in phonemes:
        if unit["is_vowel"]:
            syllables.append(pending_onset + [unit])
            pending_onset = []
        else:
            pending_onset.append(unit)
    if pending_onset:
        if not syllables and len(pending_onset) == 1 and pending_onset[0]["source_grapheme"] == "n":
            pending_onset[0]["phoneme"] = "N̩"
            syllables.append(pending_onset)
            flags.append("syllabic_n_requires_review")
        elif syllables:
            syllables[-1].extend(pending_onset)
            flags.append("coda_or_nasalization_requires_review")
        else:
            flags.append("no_vowel_nucleus")
    output = []
    for index, units in enumerate(syllables):
        output.append({
            "syllable_index": index,
            "orthographic_form": "".join(u["source_grapheme"] for u in units),
            "phonemes": [u["phoneme"] for u in units],
            "character_start": min(u["character_start"] for u in units),
            "character_end": max(u["character_end"] for u in units),
            "timing_status": "pending",
            "start_s": None,
            "end_s": None,
            "annotation_provenance": "automatic_rule",
        })
    return output, sorted(set(flags))


def annotate_utterance(text: str) -> dict:
    text = unicodedata.normalize("NFC", text)
    words = []
    review_flags = []
    for word_index, token in enumerate(word_tokens(text)):
        phonemes, phoneme_flags = phonemes_for_word(token)
        syllables, syllable_flags = syllables_for_word(token, phonemes)
        flags = sorted(set(phoneme_flags + syllable_flags))
        if flags:
            review_flags.append({"word_index": word_index, "word": token["text"], "flags": flags})
        words.append({
            "word_index": word_index,
            "text": token["text"],
            "character_start": token["start"],
            "character_end": token["end"],
            "phonemes": phonemes,
            "syllables": syllables,
            "review_flags": flags,
        })

    tone_units = []
    for index, tone in enumerate(extract_tone_units(text)):
        word_index = next((w["word_index"] for w in words if w["character_start"] <= tone.character_start < w["character_end"]), None)
        syllable_index = None
        if word_index is not None:
            syllable_index = next((s["syllable_index"] for s in words[word_index]["syllables"] if s["character_start"] <= tone.character_start < s["character_end"]), None)
        unit = asdict(tone)
        unit.update({
            "tone_unit_index": index,
            "word_index": word_index,
            "syllable_index": syllable_index,
            "tone_type": "orthographic",
            "surface_tone_status": "not_annotated",
            "timing_status": "pending",
            "start_s": None,
            "end_s": None,
            "annotation_provenance": "derived_from_verified_text",
        })
        tone_units.append(unit)

    # A standalone orthographic nasal may be syllabic and tone-bearing.
    for word in words:
        if len(word["phonemes"]) == 1 and word["phonemes"][0]["phoneme"] == "N̩":
            decomposed = unicodedata.normalize("NFD", word["text"])
            tone = "H" if "\u0301" in decomposed else "L" if "\u0300" in decomposed else "M"
            tone_units.append({
                "tone_unit_index": -1,
                "grapheme": word["text"],
                "base_vowel": "syllabic_nasal",
                "tone": tone,
                "character_start": word["character_start"],
                "character_end": word["character_end"],
                "word_index": word["word_index"],
                "syllable_index": 0,
                "tone_type": "orthographic",
                "surface_tone_status": "not_annotated",
                "timing_status": "pending",
                "start_s": None,
                "end_s": None,
                "annotation_provenance": "derived_from_verified_text",
            })
    tone_units.sort(key=lambda unit: unit["character_start"])
    for index, unit in enumerate(tone_units):
        unit["tone_unit_index"] = index

    return {
        "annotation_version": "0.1-auto",
        "text_nfc": text,
        "phoneme_inventory": "yoruba-broad-ipa-0.1",
        "words": words,
        "tone_units": tone_units,
        "review_flags": review_flags,
        "pronunciation_status": "automatic_unverified",
        "surface_tone_status": "not_annotated",
        "alignment_status": "pending",
    }
