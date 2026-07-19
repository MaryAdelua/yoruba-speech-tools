"""Create low-confidence word/syllable/tone intervals for manual review."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys
import wave

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from heuristic_alignment import allocate_intervals, validate_intervals  # noqa: E402


ANNOTATIONS = ROOT / "dataset" / "annotations" / "training_batch_01_pronunciation_reviewed.jsonl"
AUDIO = ROOT / "work" / "training_batch_01_wav_24k"
OUTPUT = ROOT / "alignment" / "training_batch_01_alignment.jsonl"
REVIEW = ROOT / "alignment" / "training_batch_01_alignment_review.csv"
REPORT = ROOT / "alignment" / "TRAINING_BATCH_01_ALIGNMENT_REPORT.md"
FRAME_MS = 20
ACTIVE_DBFS = -40.0


def active_region(path: Path) -> tuple[float, float, float]:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        frames = handle.getnframes()
        if channels != 1 or width != 2:
            raise ValueError(f"unexpected audio format: {path}")
        samples = np.frombuffer(handle.readframes(frames), dtype="<i2").astype(np.float64)
    frame_size = max(1, int(rate * FRAME_MS / 1000))
    count = len(samples) // frame_size
    framed = samples[: count * frame_size].reshape(count, frame_size)
    rms = np.sqrt(np.mean(framed * framed, axis=1))
    dbfs = np.where(rms > 0, 20 * np.log10(rms / 32768.0), -120.0)
    active = np.flatnonzero(dbfs >= ACTIVE_DBFS)
    duration = len(samples) / rate
    if not len(active):
        return 0.0, duration, duration
    start = max(0.0, active[0] * frame_size / rate)
    end = min(duration, (active[-1] + 1) * frame_size / rate)
    return start, end, duration


def main() -> None:
    with ANNOTATIONS.open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    aligned_records = []
    review_rows = []
    for record in records:
        audio_path = AUDIO / f"speaker01_{record['prompt_id']}.wav"
        speech_start, speech_end, duration = active_region(audio_path)
        word_items = []
        for word in record["words"]:
            weight = max(1, len(word["phonemes"]))
            word_items.append({"word_index": word["word_index"], "text": word["text"], "weight": weight})
        word_intervals = allocate_intervals(word_items, speech_start, speech_end)
        errors = validate_intervals(word_intervals, speech_start, speech_end)
        if errors:
            raise ValueError(f"{record['prompt_id']}: {errors}")

        syllable_intervals = []
        tone_intervals = []
        for word, word_interval in zip(record["words"], word_intervals):
            syllable_items = [
                {
                    "word_index": word["word_index"],
                    "syllable_index": syllable["syllable_index"],
                    "orthographic_form": syllable["orthographic_form"],
                    "weight": max(1, len(syllable["phonemes"])),
                }
                for syllable in word["syllables"]
            ]
            allocated = allocate_intervals(syllable_items, word_interval["start_s"], word_interval["end_s"])
            syllable_intervals.extend(allocated)
            for syllable in allocated:
                matching = [
                    unit for unit in record["tone_units"]
                    if unit["word_index"] == syllable["word_index"] and unit["syllable_index"] == syllable["syllable_index"]
                ]
                for unit in matching:
                    tone_intervals.append({
                        "tone_unit_index": unit["tone_unit_index"],
                        "word_index": unit["word_index"],
                        "syllable_index": unit["syllable_index"],
                        "grapheme": unit["grapheme"],
                        "tone": unit["tone"],
                        "start_s": syllable["start_s"],
                        "end_s": syllable["end_s"],
                    })

        aligned = {
            "alignment_version": "0.1-heuristic",
            "prompt_id": record["prompt_id"],
            "audio_path": str(audio_path.relative_to(ROOT)).replace("\\", "/"),
            "audio_duration_s": round(duration, 4),
            "speech_region": {"start_s": round(speech_start, 4), "end_s": round(speech_end, 4), "method": "energy_threshold_-40_dbfs"},
            "words": word_intervals,
            "syllables": syllable_intervals,
            "tone_units": tone_intervals,
            "alignment_status": "automatic_unverified",
            "confidence": "low",
            "method": "speech_region_plus_phoneme_count_duration_allocation",
            "prohibited_as_verified_training_target": True,
        }
        aligned_records.append(aligned)
        review_rows.append({
            "prompt_id": record["prompt_id"],
            "text": record["text_nfc"],
            "audio_duration_s": round(duration, 3),
            "speech_start_s": round(speech_start, 3),
            "speech_end_s": round(speech_end, 3),
            "word_count": len(word_intervals),
            "boundary_review": "pending",
            "review_notes": "",
        })

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for record in aligned_records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    REPORT.write_text(
        "# Training Batch 01 alignment report\n\n"
        f"- utterances initialized: {len(aligned_records)}/30;\n"
        f"- word intervals: {sum(len(r['words']) for r in aligned_records)};\n"
        f"- syllable intervals: {sum(len(r['syllables']) for r in aligned_records)};\n"
        f"- tone-unit intervals: {sum(len(r['tone_units']) for r in aligned_records)};\n"
        "- method: energy-detected speech span with phoneme-count duration allocation;\n"
        "- status: automatic, unverified, low confidence;\n"
        "- training eligibility: prohibited until boundary review or replacement by a validated forced aligner.\n\n"
        "These intervals initialize a manual review interface. They are not acoustic evidence that a word or tone begins at the estimated boundary.\n",
        encoding="utf-8",
    )
    print(f"utterances={len(aligned_records)}")
    print(f"words={sum(len(r['words']) for r in aligned_records)}")
    print(f"syllables={sum(len(r['syllables']) for r in aligned_records)}")
    print(f"tone_units={sum(len(r['tone_units']) for r in aligned_records)}")


if __name__ == "__main__":
    main()

