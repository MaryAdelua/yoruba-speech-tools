#!/usr/bin/env python3
"""Validate the MMS Yoruba tokenizer against canonical integration records.

This is an interface-only check. It never loads or updates model weights.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from transformers import VitsTokenizer


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def grapheme_for_offset(record: dict, offset: int) -> dict | None:
    return next(
        (unit for unit in record["graphemes"] if unit["character_start"] <= offset < unit["character_end"]),
        None,
    )


def validate_record(record: dict, tokenizer: VitsTokenizer) -> dict:
    text = record["text_nfc"]
    normalized = tokenizer.normalize_text(text)
    kept = [(offset, character) for offset, character in enumerate(normalized) if character in tokenizer.encoder]
    prepared, _ = tokenizer.prepare_for_tokenization(text)
    if prepared != "".join(character for _, character in kept).strip():
        raise ValueError(f"{record['prompt_id']}: tokenizer preparation could not be reproduced")

    encoded = tokenizer(text, add_special_tokens=False)
    unknown_count = encoded["input_ids"].count(tokenizer.unk_token_id)
    content_tokens = tokenizer.convert_ids_to_tokens(encoded["input_ids"])[1::2]
    if content_tokens != list(prepared):
        raise ValueError(f"{record['prompt_id']}: blank-token projection is inconsistent")

    projected = []
    for model_index, (offset, character) in enumerate(kept):
        unit = grapheme_for_offset(record, offset)
        projected.append({
            "model_content_index": model_index,
            "model_input_index": model_index * 2 + 1,
            "character": character,
            "source_character_offset": offset,
            "grapheme_index": None if unit is None else unit["grapheme_index"],
            "syllable_index": None if unit is None else unit["syllable_index"],
            "orthographic_tone_id": -1 if unit is None else unit["orthographic_tone_id"],
            "orthographic_tone_mask": 0 if unit is None else unit["orthographic_tone_mask"],
        })

    tone_units = [unit for unit in projected if unit["orthographic_tone_mask"]]
    mapped_syllables = {unit["syllable_index"] for unit in tone_units}
    expected_syllables = {unit["syllable_index"] for unit in record["tone_units"]}
    return {
        "utterance_id": record["utterance_id"],
        "prompt_id": record["prompt_id"],
        "normalized_model_text": prepared,
        "input_token_count_with_blanks": len(encoded["input_ids"]),
        "content_token_count": len(content_tokens),
        "unknown_token_count": unknown_count,
        "filtered_source_characters": [
            {"offset": index, "character": character}
            for index, character in enumerate(normalized)
            if character not in tokenizer.encoder
        ],
        "tone_supervised_content_token_count": len(tone_units),
        "mapped_tone_syllable_count": len(mapped_syllables),
        "expected_tone_syllable_count": len(expected_syllables),
        "all_tone_syllables_mapped": mapped_syllables == expected_syllables,
        "token_projection": projected,
        "target_identity_sha256": record["target_identity_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tokenizer = VitsTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    records = read_jsonl(args.records)
    results = [validate_record(record, tokenizer) for record in records]
    filtered = Counter(
        item["character"] for result in results for item in result["filtered_source_characters"]
    )
    summary = {
        "schema_version": "1.0",
        "validation_type": "model_interface_only",
        "model_id": "facebook/mms-tts-yor",
        "model_architecture": "VITS",
        "model_weights_loaded": False,
        "model_weights_updated": False,
        "training_started": False,
        "record_count": len(results),
        "records_without_unknown_tokens": sum(result["unknown_token_count"] == 0 for result in results),
        "records_with_all_tone_syllables_mapped": sum(
            result["all_tone_syllables_mapped"] for result in results
        ),
        "content_token_count": sum(result["content_token_count"] for result in results),
        "tone_supervised_content_token_count": sum(
            result["tone_supervised_content_token_count"] for result in results
        ),
        "filtered_characters": dict(sorted(filtered.items())),
        "tokenizer_contract": {
            "normalization": "lowercase; remove characters outside checkpoint vocabulary",
            "add_blank": tokenizer.add_blank,
            "is_uroman": tokenizer.is_uroman,
            "phonemize": tokenizer.phonemize,
            "vocabulary_size": tokenizer.vocab_size,
        },
        "records": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
