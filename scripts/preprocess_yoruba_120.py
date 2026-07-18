import csv
import json
import math
import shutil
import subprocess
import sys
import unicodedata
import wave
from dataclasses import asdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
INPUT_AUDIO = ROOT / "work" / "yoruba_targeted_120_master"
INPUT_MANIFEST = ROOT / "outputs" / "yoruba_targeted_120_MASTER_manifest.csv"
FFMPEG = ROOT / "work" / "ffmpeg_batch2.exe"
PACKAGE = ROOT / "work" / "yoruba_voice_benchmark_v0_1"
AUDIO_OUT = PACKAGE / "audio_wav_24k"
MANIFEST_OUT = PACKAGE / "benchmark_manifest.csv"
ANNOTATIONS_OUT = PACKAGE / "tone_annotations.jsonl"
CONTRASTS_OUT = PACKAGE / "contrast_groups.csv"
README_OUT = PACKAGE / "README.md"
CONSENT_OUT = PACKAGE / "CONSENT_STATUS.md"
OUTPUT_ZIP = ROOT / "outputs" / "yoruba_voice_benchmark_v0_1.zip"

sys.path.insert(0, str(ROOT / "work" / "yoruba_voice_research" / "src"))
from tone_parser import extract_tone_units, tone_sequence  # noqa: E402

SAMPLE_RATE = 24000
FRAME_MS = 20
SILENCE_THRESHOLD_DBFS = -45.0
EDGE_PADDING_MS = 200
TARGET_ACTIVE_RMS_DBFS = -23.0
MAX_GAIN_DB = 15.0
MIN_GAIN_DB = -12.0
PEAK_CEILING_DBFS = -2.0


def dbfs(value):
    return -120.0 if value <= 0 else 20.0 * math.log10(value / 32768.0)


def decode_m4a(path):
    command = [
        str(FFMPEG), "-v", "error", "-i", str(path), "-f", "s16le",
        "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1",
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"Could not decode {path.name}: {result.stderr.decode(errors='replace')}")
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float64)


def active_bounds(samples):
    frame = max(1, SAMPLE_RATE * FRAME_MS // 1000)
    count = math.ceil(len(samples) / frame)
    active = []
    for index in range(count):
        chunk = samples[index * frame:(index + 1) * frame]
        rms = float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) else 0.0
        if dbfs(rms) >= SILENCE_THRESHOLD_DBFS:
            active.append(index)
    if not active:
        return 0, len(samples)
    padding = SAMPLE_RATE * EDGE_PADDING_MS // 1000
    start = max(0, active[0] * frame - padding)
    end = min(len(samples), (active[-1] + 1) * frame + padding)
    return start, end


def active_samples(samples):
    threshold = 32768.0 * (10 ** (SILENCE_THRESHOLD_DBFS / 20.0))
    selected = samples[np.abs(samples) >= threshold]
    return selected if len(selected) else samples


def normalize(samples):
    active = active_samples(samples)
    active_rms = float(np.sqrt(np.mean(active * active))) if len(active) else 0.0
    requested_gain = TARGET_ACTIVE_RMS_DBFS - dbfs(active_rms)
    gain_db = min(MAX_GAIN_DB, max(MIN_GAIN_DB, requested_gain))
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak > 0:
        peak_limited_gain = PEAK_CEILING_DBFS - dbfs(peak)
        gain_db = min(gain_db, peak_limited_gain)
    scaled = samples * (10 ** (gain_db / 20.0))
    scaled = np.clip(np.rint(scaled), -32768, 32767).astype("<i2")
    return scaled, gain_db


def write_wav(path, samples):
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())


def metrics(samples):
    values = samples.astype(np.float64)
    peak = float(np.max(np.abs(values))) if len(values) else 0.0
    rms = float(np.sqrt(np.mean(values * values))) if len(values) else 0.0
    return {
        "duration_s": round(len(values) / SAMPLE_RATE, 3),
        "peak_dbfs": round(dbfs(peak), 3),
        "rms_dbfs": round(dbfs(rms), 3),
    }


CONTRAST_GROUPS = [
    ("C01", "oko-family", "lexical_tone_and_vowel", [101, 102, 103, 104]),
    ("C02", "owo-family", "lexical_tone_and_vowel", [105, 106, 137, 138, 139]),
    ("C03", "igba-family", "lexical_tone", [107, 108, 140, 141]),
    ("C04", "ara-family", "lexical_tone", [131, 132, 133]),
    ("C05", "eko-family", "lexical_tone", [142, 143, 144]),
    ("C06", "ko-family", "lexical_tone", [161, 162, 163]),
    ("C07", "yara-family", "lexical_tone", [164, 165]),
    ("C08", "fo-family", "lexical_tone", [169, 170]),
    ("C09", "ilu-family", "lexical_tone", [191, 192]),
    ("C10", "iya-family", "lexical_tone", [193, 194]),
    ("C11", "market-polarity", "affirmative_negative", [145, 146]),
    ("C12", "arrival-aspect", "completed_not_yet", [147, 148]),
    ("C13", "waking-question", "question_statement", [149, 150]),
    ("C14", "book-focus", "focused_neutral", [151, 152]),
    ("C15", "light-control", "on_off_command", [199, 200]),
    ("C16", "hearing-polarity", "affirmative_negative", [205, 206]),
    ("C17", "speaker-focus", "focused_negative", [211, 212]),
]


if PACKAGE.exists():
    raise RuntimeError(f"Package directory already exists: {PACKAGE}")
AUDIO_OUT.mkdir(parents=True)

with INPUT_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
    manifest = list(csv.DictReader(handle))
if len(manifest) != 120:
    raise RuntimeError(f"Expected 120 manifest rows, found {len(manifest)}")

expected_names = [f"speaker01_{number:04d}.m4a" for number in range(101, 221)]
actual_names = [row["filename"] for row in manifest]
if actual_names != expected_names:
    raise RuntimeError("Master manifest does not contain the exact 0101-0220 sequence")

group_map = {}
for group_id, label, contrast_type, ids in CONTRAST_GROUPS:
    for prompt_id in ids:
        group_map.setdefault(prompt_id, []).append(group_id)

processed_rows = []
annotation_rows = []
for row in manifest:
    source = INPUT_AUDIO / row["filename"]
    if not source.exists():
        raise FileNotFoundError(source)
    prompt_id = int(source.stem.split("_")[-1])
    decoded = decode_m4a(source)
    source_metrics = metrics(decoded.astype("<i2"))
    start, end = active_bounds(decoded)
    trimmed = decoded[start:end]
    normalized, gain_db = normalize(trimmed)
    wav_name = source.with_suffix(".wav").name
    wav_path = AUDIO_OUT / wav_name
    write_wav(wav_path, normalized)
    output_metrics = metrics(normalized)
    text = unicodedata.normalize("NFC", row["yoruba"])
    units = extract_tone_units(text)
    groups = group_map.get(prompt_id, [])
    processed_rows.append({
        "prompt_id": f"{prompt_id:04d}",
        "audio_filename": f"audio_wav_24k/{wav_name}",
        "source_filename": row["filename"],
        "yoruba": text,
        "english_meaning": row["english_meaning"],
        "research_purpose": row["research_purpose"],
        "orthographic_tone_sequence": tone_sequence(text),
        "contrast_group_ids": ";".join(groups),
        "sample_rate_hz": SAMPLE_RATE,
        "channels": 1,
        "sample_format": "PCM_S16LE",
        "source_duration_s": source_metrics["duration_s"],
        "processed_duration_s": output_metrics["duration_s"],
        "trimmed_start_s": round(start / SAMPLE_RATE, 3),
        "trimmed_end_s": round((len(decoded) - end) / SAMPLE_RATE, 3),
        "normalization_gain_db": round(gain_db, 3),
        "processed_peak_dbfs": output_metrics["peak_dbfs"],
        "processed_rms_dbfs": output_metrics["rms_dbfs"],
        "transcript_alignment_status": "recorded_from_prompt_not_listening_verified",
    })
    annotation_rows.append({
        "prompt_id": f"{prompt_id:04d}",
        "yoruba": text,
        "tone_sequence": tone_sequence(text),
        "tone_units": [asdict(unit) for unit in units],
        "annotation_type": "orthographic",
        "surface_tone_status": "not_annotated",
    })

with MANIFEST_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(processed_rows[0].keys()))
    writer.writeheader()
    writer.writerows(processed_rows)

with ANNOTATIONS_OUT.open("w", encoding="utf-8", newline="\n") as handle:
    for item in annotation_rows:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")

with CONTRASTS_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["contrast_group_id", "label", "contrast_type", "prompt_ids"])
    for group_id, label, contrast_type, ids in CONTRAST_GROUPS:
        writer.writerow([group_id, label, contrast_type, ";".join(f"{value:04d}" for value in ids)])

README_OUT.write_text(
    """# Yoruba Voice Benchmark v0.1

This package contains 120 controlled, single-speaker Yoruba reference recordings for research on meaning-preserving Yoruba speech synthesis and voice-model evaluation.

## Intended use

- evaluate lexical-tone and meaning preservation in synthesized Yoruba speech;
- develop tone-aware or meaning-risk-weighted training objectives;
- create forced-choice listening tests and error analyses;
- compare voice models on questions, commands, negation, connected speech, and voice-assistant utterances.

This is a controlled reference/evaluation corpus, not sufficient by itself to train a general-purpose Yoruba voice model.

## Audio processing

- source: M4A recordings made by one fluent Yoruba speaker;
- output: mono, 24 kHz, 16-bit PCM WAV;
- edge silence: detected in 20 ms frames below -45 dBFS, with 200 ms retained padding;
- level: active-speech RMS targeted to -23 dBFS, gain limited to +15/-12 dB and peak limited to -2 dBFS;
- originals were not modified.

## Files

- `audio_wav_24k/`: standardized recordings;
- `benchmark_manifest.csv`: transcripts, meanings, processing metadata, and contrast memberships;
- `tone_annotations.jsonl`: Unicode-safe orthographic vowel/tone units and H/M/L sequences;
- `contrast_groups.csv`: provisional meaning-relevant contrast sets;
- `CONSENT_STATUS.md`: release and consent limitations.

## Important limitations

- Tone labels are orthographic, not measured surface F0 contours.
- Transcript-to-audio alignment has not yet been independently listening-verified.
- Contrast groups are provisional and require fluent-speaker/linguist review.
- This single-speaker set cannot establish population-wide naturalness or intelligibility.
""",
    encoding="utf-8",
)

CONSENT_OUT.write_text(
    """# Consent and release status

The speaker stated in the project conversation that the recordings are her own voice and that commercial use is acceptable.

Before public release, redistribution, commercial model training, or publication as a dataset, obtain a signed voice/data release specifying permitted uses, attribution preference, withdrawal terms, storage, redistribution, synthesized-voice use, and commercial licensing. Chat authorization should not be represented as a completed legal release.
""",
    encoding="utf-8",
)

if OUTPUT_ZIP.exists():
    raise RuntimeError(f"Output ZIP already exists: {OUTPUT_ZIP}")
shutil.make_archive(str(OUTPUT_ZIP.with_suffix("")), "zip", PACKAGE)

print(json.dumps({
    "recordings": len(processed_rows),
    "total_source_seconds": round(sum(float(row["source_duration_s"]) for row in processed_rows), 1),
    "total_processed_seconds": round(sum(float(row["processed_duration_s"]) for row in processed_rows), 1),
    "contrast_groups": len(CONTRAST_GROUPS),
    "output_zip": str(OUTPUT_ZIP),
}, indent=2))
