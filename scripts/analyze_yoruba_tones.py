import csv
import gzip
import itertools
import json
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tone_tools_final"))

import librosa
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "work" / "yoruba_voice_benchmark_v0_1"
AUDIO = BENCHMARK / "audio_wav_24k"
MANIFEST = BENCHMARK / "benchmark_manifest.csv"
CONTRASTS = BENCHMARK / "contrast_groups.csv"
ANALYSIS = ROOT / "work" / "yoruba_tone_analysis_v0_1"
TRACKS_OUT = ANALYSIS / "f0_tracks.csv.gz"
SUMMARY_OUT = ANALYSIS / "utterance_f0_summary.csv"
CONTRAST_OUT = ANALYSIS / "contrast_contour_screening.csv"
REPORT_OUT = ANALYSIS / "TONE_ANALYSIS_REPORT.md"
README_OUT = ANALYSIS / "README.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_tone_analysis_v0_1.zip"

SR = 24000
FMIN = 65.0
FMAX = 500.0
FRAME_LENGTH = 2048
HOP_LENGTH = 240
CONTOUR_BINS = 20


def nanmedian(values):
    values = np.asarray(values, dtype=float)
    return float(np.nanmedian(values)) if np.any(np.isfinite(values)) else float("nan")


def percentile(values, q):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(np.percentile(values, q)) if len(values) else float("nan")


def contour_bins(times, f0, duration, bins=CONTOUR_BINS):
    result = np.full(bins, np.nan, dtype=float)
    if duration <= 0:
        return result
    positions = np.clip(times / duration, 0, 0.999999)
    indices = np.floor(positions * bins).astype(int)
    for index in range(bins):
        values = f0[(indices == index) & np.isfinite(f0)]
        if len(values):
            result[index] = np.median(values)
    finite = np.flatnonzero(np.isfinite(result))
    if len(finite) >= 2:
        result = np.interp(np.arange(bins), finite, result[finite])
    return result


def contour_rmse(a, b):
    mask = np.isfinite(a) & np.isfinite(b)
    return float(np.sqrt(np.mean((a[mask] - b[mask]) ** 2))) if np.any(mask) else float("nan")


if ANALYSIS.exists():
    raise RuntimeError(f"Analysis directory already exists: {ANALYSIS}")
ANALYSIS.mkdir(parents=True)

with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
    manifest = list(csv.DictReader(handle))
with CONTRASTS.open("r", encoding="utf-8-sig", newline="") as handle:
    contrast_groups = list(csv.DictReader(handle))

if len(manifest) != 120:
    raise RuntimeError(f"Expected 120 benchmark rows, found {len(manifest)}")

raw = []
all_f0 = []
for index, row in enumerate(manifest, start=1):
    path = BENCHMARK / row["audio_filename"]
    y, sample_rate = librosa.load(path, sr=None, mono=True)
    if sample_rate != SR:
        raise RuntimeError(f"Unexpected sample rate for {path.name}: {sample_rate}")
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=FMIN,
        fmax=FMAX,
        sr=SR,
        frame_length=FRAME_LENGTH,
        hop_length=HOP_LENGTH,
        fill_na=np.nan,
    )
    times = librosa.times_like(f0, sr=SR, hop_length=HOP_LENGTH)
    duration = len(y) / SR
    valid = np.isfinite(f0) & (f0 >= FMIN) & (f0 <= FMAX)
    cleaned = np.where(valid, f0, np.nan)
    all_f0.extend(cleaned[valid].tolist())
    raw.append({
        "row": row,
        "times": times,
        "f0": cleaned,
        "voiced_prob": voiced_prob,
        "duration": duration,
    })
    if index % 20 == 0:
        print(f"Tracked {index}/120", flush=True)

pooled = np.asarray(all_f0, dtype=float)
if len(pooled) < 100:
    raise RuntimeError("Too few voiced F0 frames for speaker normalization")
speaker_median = float(np.median(pooled))
speaker_p05 = float(np.percentile(pooled, 5))
speaker_p95 = float(np.percentile(pooled, 95))

summaries = []
contours = {}
with gzip.open(TRACKS_OUT, "wt", encoding="utf-8", newline="") as handle:
    fieldnames = ["prompt_id", "time_s", "f0_hz", "f0_semitones_relative_to_speaker_median", "voiced_probability"]
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    for item in raw:
        row = item["row"]
        prompt_id = row["prompt_id"]
        times = item["times"]
        f0 = item["f0"]
        valid = np.isfinite(f0)
        semitones = np.where(valid, 12.0 * np.log2(f0 / speaker_median), np.nan)
        contour = contour_bins(times, semitones, item["duration"])
        contours[prompt_id] = contour
        voiced_ratio = float(np.mean(valid))
        normalized_time = times[valid] / item["duration"] if item["duration"] else np.array([])
        voiced_st = semitones[valid]
        slope = float(np.polyfit(normalized_time, voiced_st, 1)[0]) if len(voiced_st) >= 3 else float("nan")
        first = voiced_st[normalized_time < 1 / 3]
        middle = voiced_st[(normalized_time >= 1 / 3) & (normalized_time < 2 / 3)]
        final = voiced_st[normalized_time >= 2 / 3]
        summaries.append({
            "prompt_id": prompt_id,
            "audio_filename": row["audio_filename"],
            "yoruba": row["yoruba"],
            "orthographic_tone_sequence": row["orthographic_tone_sequence"],
            "contrast_group_ids": row["contrast_group_ids"],
            "duration_s": round(item["duration"], 3),
            "total_frames": len(f0),
            "voiced_frames": int(np.sum(valid)),
            "voiced_ratio": round(voiced_ratio, 4),
            "f0_median_hz": round(nanmedian(f0), 3),
            "f0_p10_hz": round(percentile(f0, 10), 3),
            "f0_p90_hz": round(percentile(f0, 90), 3),
            "f0_range_p90_p10_st": round(12 * math.log2(percentile(f0, 90) / percentile(f0, 10)), 3),
            "start_median_st": round(nanmedian(first), 3),
            "middle_median_st": round(nanmedian(middle), 3),
            "end_median_st": round(nanmedian(final), 3),
            "global_slope_st_per_utterance": round(slope, 3),
            "contour_20bin_st": ";".join("" if not np.isfinite(value) else f"{value:.3f}" for value in contour),
        })
        for time_s, hz, st, probability in zip(times, f0, semitones, item["voiced_prob"]):
            writer.writerow({
                "prompt_id": prompt_id,
                "time_s": f"{time_s:.4f}",
                "f0_hz": "" if not np.isfinite(hz) else f"{hz:.3f}",
                "f0_semitones_relative_to_speaker_median": "" if not np.isfinite(st) else f"{st:.3f}",
                "voiced_probability": "" if not np.isfinite(probability) else f"{probability:.4f}",
            })

with SUMMARY_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
    writer.writeheader()
    writer.writerows(summaries)

contrast_rows = []
for group in contrast_groups:
    ids = group["prompt_ids"].split(";")
    pairwise = []
    for left, right in itertools.combinations(ids, 2):
        pairwise.append(contour_rmse(contours[left], contours[right]))
    finite = [value for value in pairwise if math.isfinite(value)]
    contrast_rows.append({
        "contrast_group_id": group["contrast_group_id"],
        "label": group["label"],
        "contrast_type": group["contrast_type"],
        "prompt_ids": group["prompt_ids"],
        "utterance_count": len(ids),
        "pair_count": len(pairwise),
        "mean_pairwise_contour_rmse_st": round(float(np.mean(finite)), 3) if finite else "",
        "min_pairwise_contour_rmse_st": round(float(np.min(finite)), 3) if finite else "",
        "max_pairwise_contour_rmse_st": round(float(np.max(finite)), 3) if finite else "",
        "interpretation": "screening_only_no_word_or_syllable_alignment",
    })

with CONTRAST_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(contrast_rows[0].keys()))
    writer.writeheader()
    writer.writerows(contrast_rows)

voiced_ratios = [float(row["voiced_ratio"]) for row in summaries]
low_voicing = [row["prompt_id"] for row in summaries if float(row["voiced_ratio"]) < 0.25]
REPORT_OUT.write_text(
    f"""# Yoruba acoustic tone-analysis report

## Corpus-level pitch results

- Recordings analyzed: **120 of 120**
- Pitch method: **librosa pYIN**, 24 kHz audio, 10 ms hop, 65-500 Hz search range
- Total voiced F0 frames: **{len(pooled):,}**
- Speaker pooled median F0: **{speaker_median:.1f} Hz**
- Speaker pooled 5th-95th percentile F0: **{speaker_p05:.1f}-{speaker_p95:.1f} Hz**
- Median utterance voiced-frame ratio: **{np.median(voiced_ratios):.3f}**
- Utterances below 0.25 voiced-frame ratio: **{', '.join(low_voicing) if low_voicing else 'none'}**
- Controlled contrast groups screened: **{len(contrast_rows)}**

## What these results establish

The package now contains reproducible frame-level F0 tracks, speaker-normalized semitone contours, utterance summaries, and whole-utterance contour distances for the controlled contrast groups. These outputs are suitable for quality screening, visualization, baseline feature construction, and planning a tone-aware loss.

## What these results do not establish

This analysis does **not** yet measure lexical-tone accuracy. The recordings have orthographic H/M/L sequences, but individual words and vowel nuclei do not yet have acoustic time boundaries. Whole-utterance contour differences can be caused by sentence length, focus, emotion, or segmental context. Therefore, the contrast distances are explicitly labeled as screening results and must not be reported as Tone Error Rate or pronunciation accuracy.

## Required next stage

1. Listening-verify transcript-to-audio correspondence.
2. Align each utterance to word, syllable, and vowel-nucleus boundaries.
3. Associate each measured F0 interval with its orthographic H/M/L target.
4. Normalize for declination and local tonal context.
5. Compute syllable-level tone separability and error metrics with manual review of alignment failures.
""",
    encoding="utf-8",
)

README_OUT.write_text(
    """# Yoruba Tone Analysis v0.1

Files:

- `f0_tracks.csv.gz`: frame-level pYIN F0, speaker-relative semitones, and voicing probability;
- `utterance_f0_summary.csv`: utterance-level pitch and contour features;
- `contrast_contour_screening.csv`: whole-utterance pairwise contour screening for 17 controlled groups;
- `TONE_ANALYSIS_REPORT.md`: interpretation and limitations.

The analysis intentionally does not assign acoustic F0 to written tones until forced or manual alignment is available.
""",
    encoding="utf-8",
)

if ZIP_OUT.exists():
    raise RuntimeError(f"Output ZIP already exists: {ZIP_OUT}")
shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", ANALYSIS)

print(json.dumps({
    "recordings": len(summaries),
    "voiced_frames": len(pooled),
    "speaker_median_f0_hz": round(speaker_median, 2),
    "speaker_p05_hz": round(speaker_p05, 2),
    "speaker_p95_hz": round(speaker_p95, 2),
    "contrast_groups": len(contrast_rows),
    "zip": str(ZIP_OUT),
}, indent=2))
