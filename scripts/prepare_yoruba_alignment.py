import csv
import json
import shutil
import sys
import unicodedata
import wave
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "work" / "yoruba_voice_benchmark_v0_1"
TONE_ANALYSIS = ROOT / "work" / "yoruba_tone_analysis_v0_1"
MANIFEST = BENCHMARK / "benchmark_manifest.csv"
F0_SUMMARY = TONE_ANALYSIS / "utterance_f0_summary.csv"
PACKAGE = ROOT / "work" / "yoruba_alignment_v0_1"
UTTERANCES_OUT = PACKAGE / "utterance_alignment.csv"
UNITS_OUT = PACKAGE / "word_vowel_alignment_inventory.jsonl"
REVIEW_OUT = PACKAGE / "listening_verification_queue.csv"
METHOD_OUT = PACKAGE / "ALIGNMENT_METHOD.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_alignment_v0_1.zip"

sys.path.insert(0, str(ROOT / "work" / "yoruba_voice_research" / "src"))
from tone_parser import extract_tone_units  # noqa: E402


def word_spans(text):
    spans = []
    start = None
    for index, char in enumerate(text + " "):
        is_word = char.isalpha() or unicodedata.combining(char) or char in {"'", "’", "-"}
        if is_word and start is None:
            start = index
        elif not is_word and start is not None:
            spans.append((text[start:index], start, index))
            start = None
    return spans


if PACKAGE.exists():
    raise RuntimeError(f"Alignment package already exists: {PACKAGE}")
PACKAGE.mkdir(parents=True)

with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
    manifest = list(csv.DictReader(handle))
with F0_SUMMARY.open("r", encoding="utf-8-sig", newline="") as handle:
    f0_by_id = {row["prompt_id"]: row for row in csv.DictReader(handle)}

if len(manifest) != 120 or len(f0_by_id) != 120:
    raise RuntimeError("Expected 120 benchmark and F0-summary rows")

utterance_rows = []
unit_rows = []
review_rows = []
for row in manifest:
    prompt_id = row["prompt_id"]
    wav_path = BENCHMARK / row["audio_filename"]
    with wave.open(str(wav_path), "rb") as handle:
        duration = handle.getnframes() / handle.getframerate()
    text = unicodedata.normalize("NFC", row["yoruba"])
    words = word_spans(text)
    tones = extract_tone_units(text)
    word_items = []
    for word_index, (word, start, end) in enumerate(words):
        word_tones = [unit for unit in tones if start <= unit.character_start < end]
        word_items.append({
            "word_index": word_index,
            "word": word,
            "character_start": start,
            "character_end": end,
            "orthographic_tone_sequence": "".join(unit.tone for unit in word_tones),
            "vowel_nuclei": [asdict(unit) for unit in word_tones],
            "start_s": None,
            "end_s": None,
            "timing_status": "pending_yoruba_capable_alignment",
        })
    utterance_rows.append({
        "prompt_id": prompt_id,
        "audio_filename": row["audio_filename"],
        "utterance_start_s": "0.000",
        "utterance_end_s": f"{duration:.3f}",
        "boundary_source": "wav_file_extent_after_edge_silence_trimming",
        "yoruba": text,
        "english_meaning": row["english_meaning"],
        "word_count": len(words),
        "vowel_nucleus_count": len(tones),
        "orthographic_tone_sequence": row["orthographic_tone_sequence"],
        "contrast_group_ids": row["contrast_group_ids"],
        "utterance_alignment_status": "complete",
        "word_alignment_status": "pending",
        "vowel_alignment_status": "pending",
    })
    unit_rows.append({
        "prompt_id": prompt_id,
        "audio_filename": row["audio_filename"],
        "utterance_start_s": 0.0,
        "utterance_end_s": round(duration, 3),
        "yoruba": text,
        "words": word_items,
    })
    f0 = f0_by_id[prompt_id]
    priority = 1 if row["contrast_group_ids"] else 2
    if float(f0["voiced_ratio"]) < 0.25:
        priority = 0
    review_rows.append({
        "review_priority": priority,
        "prompt_id": prompt_id,
        "audio_filename": row["audio_filename"],
        "yoruba_expected": text,
        "english_meaning": row["english_meaning"],
        "contrast_group_ids": row["contrast_group_ids"],
        "voiced_ratio": f0["voiced_ratio"],
        "transcript_matches_audio": "",
        "all_words_spoken": "",
        "pronunciation_natural": "",
        "notes_or_correction": "",
        "review_status": "pending",
    })

with UTTERANCES_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(utterance_rows[0].keys()))
    writer.writeheader()
    writer.writerows(utterance_rows)

with UNITS_OUT.open("w", encoding="utf-8", newline="\n") as handle:
    for item in unit_rows:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")

review_rows.sort(key=lambda item: (int(item["review_priority"]), int(item["prompt_id"])))
with REVIEW_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(review_rows[0].keys()))
    writer.writeheader()
    writer.writerows(review_rows)

METHOD_OUT.write_text(
    """# Yoruba Alignment v0.1

## Completed alignment

All 120 processed WAV files have exact utterance-level boundaries. Each begins at 0.000 seconds and ends at the WAV duration after conservative edge-silence trimming.

The package also contains a Unicode-safe inventory of every word and orthographic vowel nucleus, including its H/M/L target and character offsets. Word and vowel timestamps are intentionally `null` until a Yoruba-capable acoustic alignment is run and reviewed.

## Why lower-level timestamps are pending

An English forced aligner is not valid for Yoruba. Meta's `facebook/mms-1b-all` ASR model supports 1,100+ languages and provides language adapters, while PyTorch documents CTC forced alignment for multilingual speech. However, the MMS 1B checkpoint is approximately 3.86 GB, requires substantial inference resources, and is licensed CC-BY-NC 4.0. This project is intended for commercial adoption, so no MMS-derived boundaries are included in the benchmark release without a separate licensing decision.

Primary references:

- https://huggingface.co/facebook/mms-1b-all
- https://docs.pytorch.org/audio/2.1.0/tutorials/forced_alignment_for_multilingual_data_tutorial.html

## Listening-verification gate

Use `listening_verification_queue.csv` with the audio in the benchmark package. The fluent speaker or another qualified Yoruba listener should mark:

1. whether the recording matches the transcript;
2. whether every word is present;
3. whether the pronunciation sounds natural;
4. any correction or recording problem.

Priority 0 is an acoustic-coverage flag, priority 1 contains controlled contrast items, and priority 2 contains the remaining coverage sentences.

## Next defensible alignment options

1. Run a commercially compatible Yoruba CTC/phoneme aligner once an appropriate checkpoint and license are verified.
2. Use manual Praat alignment for the controlled contrast words first, followed by vowel-nucleus review against the F0 tracks.
3. Keep automatically proposed boundaries separate from manually accepted boundaries and report alignment confidence/failure rates.

Do not compute Syllable Tone Error Rate until vowel-nucleus boundaries have been acoustically assigned and reviewed.
""",
    encoding="utf-8",
)

if ZIP_OUT.exists():
    raise RuntimeError(f"Output ZIP already exists: {ZIP_OUT}")
shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", PACKAGE)

print(json.dumps({
    "utterances_aligned": len(utterance_rows),
    "word_units": sum(int(row["word_count"]) for row in utterance_rows),
    "vowel_nuclei": sum(int(row["vowel_nucleus_count"]) for row in utterance_rows),
    "listening_review_rows": len(review_rows),
    "zip": str(ZIP_OUT),
}, indent=2))
