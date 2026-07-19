"""Architecture-independent Yoruba pronunciation integration records."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from pathlib import Path

from yoruba_pronunciation import annotate_utterance, grapheme_clusters

TONE_IDS = {"L": 0, "M": 1, "H": 2}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def stable_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _containing(items: list[dict], start: int, end: int) -> int | None:
    for index, item in enumerate(items):
        if item["character_start"] <= start and end <= item["character_end"]:
            return index
    return None


def build_canonical_record(alignment: dict) -> dict:
    text = alignment["text_nfc"]
    if text != unicodedata.normalize("NFC", text):
        raise ValueError(f"{alignment['prompt_id']}: authoritative text is not NFC")
    derived = annotate_utterance(text)
    if [word["text"] for word in derived["words"]] != [word["text"] for word in alignment["words"]]:
        raise ValueError(f"{alignment['prompt_id']}: pronunciation and verified word segmentation disagree")

    syllables = []
    local_to_global: dict[tuple[int, int], int] = {}
    for verified_word, derived_word in zip(alignment["words"], derived["words"]):
        if len(verified_word["syllables"]) != len(derived_word["syllables"]):
            raise ValueError(f"{alignment['prompt_id']}: verified and derived syllable counts disagree for {verified_word['text']}")
        for verified_syllable, derived_syllable in zip(verified_word["syllables"], derived_word["syllables"]):
            global_index = len(syllables)
            local_to_global[(verified_word["word_index"], verified_syllable["syllable_index"])] = global_index
            syllables.append({
                "syllable_index": global_index,
                "word_index": verified_word["word_index"],
                "word_syllable_index": verified_syllable["syllable_index"],
                "orthographic_form": verified_syllable["orthographic_form"],
                "character_start": derived_syllable["character_start"],
                "character_end": derived_syllable["character_end"],
                "start_s": verified_syllable["start_s"],
                "end_s": verified_syllable["end_s"],
                "boundary_source": verified_syllable["boundary_source"],
                "boundary_confidence": verified_syllable["confidence"],
            })

    tone_units = []
    tone_by_syllable: dict[int, str] = {}
    for tone in derived["tone_units"]:
        global_syllable = local_to_global.get((tone["word_index"], tone["syllable_index"]))
        if global_syllable is None:
            raise ValueError(f"{alignment['prompt_id']}: tone unit cannot be mapped to a syllable")
        tone_by_syllable[global_syllable] = tone["tone"]
        syllable = syllables[global_syllable]
        tone_units.append({
            "tone_unit_index": len(tone_units),
            "grapheme": tone["grapheme"],
            "base_vowel": tone["base_vowel"],
            "tone": tone["tone"],
            "tone_id": TONE_IDS[tone["tone"]],
            "character_start": tone["character_start"],
            "character_end": tone["character_end"],
            "word_index": tone["word_index"],
            "syllable_index": global_syllable,
            "start_s": syllable["start_s"],
            "end_s": syllable["end_s"],
            "annotation_type": "orthographic",
            "annotation_provenance": "derived_from_verified_text",
            "loss_mask": 1,
        })

    words = [{
        "word_index": word["word_index"], "text": word["text"],
        "character_start": word["character_start"], "character_end": word["character_end"],
        "start_s": word["start_s"], "end_s": word["end_s"],
        "boundary_source": word["boundary_source"], "boundary_confidence": word["confidence"],
    } for word in alignment["words"]]
    graphemes = []
    for index, cluster in enumerate(grapheme_clusters(text)):
        word_index = _containing(derived["words"], cluster["start"], cluster["end"])
        syllable_index = _containing(syllables, cluster["start"], cluster["end"])
        tone = tone_by_syllable.get(syllable_index) if syllable_index is not None else None
        graphemes.append({
            "grapheme_index": index, "text": cluster["text"],
            "character_start": cluster["start"], "character_end": cluster["end"],
            "word_index": word_index, "syllable_index": syllable_index,
            "orthographic_tone": tone, "orthographic_tone_id": TONE_IDS[tone] if tone else -1,
            "orthographic_tone_mask": int(tone is not None),
        })

    phoneme_candidates = []
    for word in derived["words"]:
        for phoneme in word["phonemes"]:
            phoneme_candidates.append({
                "phoneme_index": len(phoneme_candidates), "word_index": word["word_index"],
                "symbol": phoneme["phoneme"], "source_grapheme": phoneme["source_grapheme"],
                "character_start": phoneme["character_start"], "character_end": phoneme["character_end"],
                "provenance": "automatic_rule", "loss_mask": 0,
            })

    target_identity = {
        "text_nfc": text, "words": words, "syllables": syllables, "tone_units": tone_units,
        "supervision_masks": {"audio_pair": 1, "word_boundaries": 1, "syllable_boundaries": 1,
                              "orthographic_tone": 1, "surface_tone": 0, "phonemes": 0},
    }
    return {
        "schema_version": "1.0", "record_type": "yoruba_canonical_integration_record",
        "utterance_id": alignment["utterance_id"], "prompt_id": alignment["prompt_id"],
        "speaker_id": alignment["speaker_id"], "language": "yo", "split": alignment["split"],
        "split_group_id": alignment["split_group_id"], "text_nfc": text,
        "audio_path": alignment["audio_path"], "duration_s": alignment["duration_s"],
        "graphemes": graphemes, "words": words, "syllables": syllables,
        "tone_units": tone_units, "phoneme_candidates": phoneme_candidates,
        "supervision_masks": target_identity["supervision_masks"],
        "target_identity_sha256": stable_hash(target_identity),
        "provenance": {"text": "human_verified", "word_boundaries": "human_verified",
                       "syllable_boundaries": "human_verified", "orthographic_tone": "derived_from_verified_text",
                       "surface_tone": "not_annotated", "phonemes": "automatic_unverified"},
    }


def text_sequence_adapter(record: dict) -> dict:
    return {
        "adapter_version": "text-sequence-v1", "architecture_style": "text_encoder_sequence",
        "utterance_id": record["utterance_id"], "text_nfc": record["text_nfc"],
        "input_units": [unit["text"] for unit in record["graphemes"]],
        "character_spans": [[unit["character_start"], unit["character_end"]] for unit in record["graphemes"]],
        "word_ids": [unit["word_index"] if unit["word_index"] is not None else -1 for unit in record["graphemes"]],
        "syllable_ids": [unit["syllable_index"] if unit["syllable_index"] is not None else -1 for unit in record["graphemes"]],
        "orthographic_tone_ids": [unit["orthographic_tone_id"] for unit in record["graphemes"]],
        "orthographic_tone_mask": [unit["orthographic_tone_mask"] for unit in record["graphemes"]],
        "phoneme_loss_mask": 0, "surface_tone_loss_mask": 0,
        "target_identity_sha256": record["target_identity_sha256"],
    }


def acoustic_frame_adapter(record: dict, frame_hz: int = 50) -> dict:
    frame_count = math.ceil(record["duration_s"] * frame_hz)
    word_ids, syllable_ids, tone_ids, boundary_mask = [], [], [], []
    tone_by_syllable = {unit["syllable_index"]: unit["tone_id"] for unit in record["tone_units"]}
    for frame_index in range(frame_count):
        time_s = (frame_index + 0.5) / frame_hz
        word_id = next((word["word_index"] for word in record["words"] if word["start_s"] <= time_s < word["end_s"]), -1)
        syllable_id = next((unit["syllable_index"] for unit in record["syllables"] if unit["start_s"] <= time_s < unit["end_s"]), -1)
        word_ids.append(word_id)
        syllable_ids.append(syllable_id)
        tone_ids.append(tone_by_syllable.get(syllable_id, -1))
        boundary_mask.append(int(syllable_id >= 0))
    return {
        "adapter_version": "acoustic-frame-v1", "architecture_style": "aligned_acoustic_sequence",
        "utterance_id": record["utterance_id"], "frame_hz": frame_hz, "frame_count": frame_count,
        "word_ids": word_ids, "syllable_ids": syllable_ids, "orthographic_tone_ids": tone_ids,
        "aligned_supervision_mask": boundary_mask, "surface_tone_loss_mask": 0,
        "target_identity_sha256": record["target_identity_sha256"],
    }
