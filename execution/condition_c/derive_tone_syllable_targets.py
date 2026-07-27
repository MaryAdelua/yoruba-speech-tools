#!/usr/bin/env python3
"""Derive per-syllable H/M/L tone labels and target durations from the
already-verified word/syllable alignment data in the training manifest.

No new annotation is invented: tone is read directly off the orthographic
diacritics already present in each syllable's `orthographic_form` (acute =
High, grave = Low, unmarked = Mid -- standard Yoruba orthographic convention),
and target durations come directly from the verified `start_s`/`end_s`
syllable timings already reviewed by Mary. This produces the training targets
Condition C's tone/syllable-boundary auxiliary losses supervise against; it
does not touch the frozen manifest itself.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

HIGH_MARKS = set("áéíóúÁÉÍÓÚ") | {"́"}  # precomposed acute + combining acute
LOW_MARKS = set("àèìòùÀÈÌÒÙ") | {"̀"}   # precomposed grave + combining grave
TONE_LABELS = {"L": 0, "M": 1, "H": 2}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def syllable_tone(orthographic_form: str) -> str:
    has_high = any(ch in HIGH_MARKS for ch in orthographic_form)
    has_low = any(ch in LOW_MARKS for ch in orthographic_form)
    if has_high and has_low:
        raise ValueError(f"Syllable {orthographic_form!r} carries both a high and low mark")
    if has_high:
        return "H"
    if has_low:
        return "L"
    return "M"


def vocab_token_positions(text: str, symbol_to_id: dict[str, int]) -> list[int | None]:
    """For each raw character index in `text`, the position it lands at in the
    *filtered* (lowercased, vocab-only) sequence MMSVocabulary.encode() builds,
    or None if that character is dropped (out of vocabulary)."""
    positions: list[int | None] = []
    next_position = 0
    for character in text.lower():
        if character in symbol_to_id:
            positions.append(next_position)
            next_position += 1
        else:
            positions.append(None)
    return positions


def with_blanks_index(filtered_index: int) -> int:
    """MMSVocabulary interleaves a blank before/after every real token: token i
    of the filtered sequence lands at index 2*i + 1 of the with-blanks sequence."""
    return filtered_index * 2 + 1


def derive_row_targets(row: dict, symbol_to_id: dict[str, int], hop_length: int, sampling_rate: int) -> dict:
    text = row["text_nfc"]
    positions = vocab_token_positions(text, symbol_to_id)
    syllables = []
    for word in row["words"]:
        cursor = word["character_start"]
        for syllable in word["syllables"]:
            form = syllable["orthographic_form"]
            start_char, end_char = cursor, cursor + len(form)
            cursor = end_char
            if text[start_char:end_char] != form:
                raise ValueError(
                    f"{row['prompt_id']}: syllable {form!r} does not match text_nfc[{start_char}:{end_char}]"
                    f"={text[start_char:end_char]!r}"
                )
            token_positions = [positions[i] for i in range(start_char, end_char) if positions[i] is not None]
            if not token_positions:
                raise ValueError(f"{row['prompt_id']}: syllable {form!r} has no in-vocabulary characters")
            token_start = with_blanks_index(min(token_positions))
            token_end = with_blanks_index(max(token_positions))
            duration_s = syllable["end_s"] - syllable["start_s"]
            target_frames = duration_s * sampling_rate / hop_length
            tone = syllable_tone(form)
            syllables.append({
                "word_index": word["word_index"],
                "syllable_index": syllable["syllable_index"],
                "orthographic_form": form,
                "tone": tone,
                "tone_id": TONE_LABELS[tone],
                "token_start_with_blanks": token_start,
                "token_end_with_blanks": token_end,
                "target_duration_s": duration_s,
                "target_duration_frames": target_frames,
            })
    return {"prompt_id": row["prompt_id"], "split": row["split"], "syllables": syllables}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("dataset/verified/training_batch_01_verified_alignments.jsonl"))
    parser.add_argument("--vocab", type=Path, required=True)
    parser.add_argument("--hop-length", type=int, default=256)
    parser.add_argument("--sampling-rate", type=int, default=16000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-protected-test", action="store_true",
                         help="Only for inspection/reporting; Condition C training must not read this for train/dev rows.")
    args = parser.parse_args()

    vocab_symbols = args.vocab.read_text(encoding="utf-8").splitlines()
    symbol_to_id = {symbol: index for index, symbol in enumerate(vocab_symbols)}

    rows = load_jsonl(args.dataset)
    targets = []
    for row in rows:
        if row["split"] == "test" and not args.include_protected_test:
            continue
        targets.append(derive_row_targets(row, symbol_to_id, args.hop_length, args.sampling_rate))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(targets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_syllables = sum(len(t["syllables"]) for t in targets)
    tone_counts = {"L": 0, "M": 0, "H": 0}
    for t in targets:
        for s in t["syllables"]:
            tone_counts[s["tone"]] += 1
    print(json.dumps({
        "rows": len(targets), "total_syllables": total_syllables, "tone_distribution": tone_counts,
    }, indent=2))


if __name__ == "__main__":
    main()
