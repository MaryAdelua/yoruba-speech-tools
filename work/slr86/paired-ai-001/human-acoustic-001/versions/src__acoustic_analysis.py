"""Signal measurements only: no linguistic or speech-quality scoring."""
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(path, *, fmin=65.0, fmax=500.0, frame_length=2048, hop_ms=10.0):
    path = Path(path).resolve()
    before = sha256(path)
    try:
        info = sf.info(path)
        audio, sr = sf.read(path, dtype="float64", always_2d=True)
    except (RuntimeError, sf.LibsndfileError) as exc:
        raise ValueError("Cannot decode audio; supply a valid mono WAV file") from exc
    if audio.shape[1] != 1:
        raise ValueError("Supply mono audio; select a channel explicitly before analysis")
    y = audio[:, 0]
    if not len(y) or not np.all(np.isfinite(y)):
        raise ValueError("Audio must contain finite samples")
    if not (0 < fmin < fmax < sr / 2):
        raise ValueError("Require 0 < fmin < fmax < Nyquist frequency")
    if frame_length < 2 * sr / fmin or frame_length % 2:
        raise ValueError("Use an even frame length spanning at least two lowest-pitch periods")
    if not np.isfinite(hop_ms) or hop_ms <= 0:
        raise ValueError("hop_ms must be positive and finite")
    hop = max(1, round(sr * hop_ms / 1000))
    if len(y) < frame_length:
        raise ValueError("Audio is shorter than one analysis window")
    f0, voiced, probability = librosa.pyin(
        y, sr=sr, fmin=fmin, fmax=fmax, frame_length=frame_length,
        hop_length=hop, center=True, pad_mode="constant", fill_na=np.nan,
    )
    centers = np.arange(len(f0)) * hop
    keep = centers < len(y)
    centers, f0, voiced, probability = centers[keep], f0[keep], voiced[keep], probability[keep]
    valid = voiced & np.isfinite(f0)
    f0 = np.where(valid, f0, np.nan)
    pitch = f0[valid]
    baseline = float(np.median(pitch)) if len(pitch) else None
    relative = 12 * np.log2(f0 / baseline) if baseline else np.full_like(f0, np.nan)
    frames = []
    for i, center in enumerate(centers):
        start, end = max(0, center-frame_length//2), min(len(y), center+frame_length//2)
        rms = float(np.sqrt(np.mean(y[start:end] ** 2)))
        frames.append({
            "timestamp_s": float(center / sr),
            "window_start_s": float(start / sr), "window_end_s": float(end / sr),
            "edge_padded": bool(center-frame_length//2 < 0 or center+frame_length//2 > len(y)),
            "f0_hz": float(f0[i]) if valid[i] else None,
            "voiced": bool(voiced[i]), "voicing_probability": float(probability[i]),
            "relative_pitch_semitones": float(relative[i]) if valid[i] else None,
            "rms_amplitude": rms, "rms_dbfs": 20 * float(np.log10(rms)) if rms > 0 else None,
        })
    warnings = []
    if not len(pitch):
        warnings.append("No voiced F0 estimates; pitch summaries and normalization are unavailable.")
    if np.mean(valid) < .25:
        warnings.append("Less than 25% of frames have voiced F0; silence and unvoiced speech are not distinguished.")
    if len(pitch) and np.any((pitch < fmin*1.05) | (pitch > fmax/1.05)):
        warnings.append("Some F0 estimates lie within 5% of a search limit; inspect range sensitivity.")
    if np.any(np.abs(y) >= 1):
        warnings.append("Samples reach/exceed digital full scale; inspect possible clipping.")
    adjacent = valid[:-1] & valid[1:]
    if np.any(np.abs(np.diff(relative))[adjacent] > 6):
        warnings.append("Adjacent voiced estimates jump by more than 6 semitones; inspect possible tracking errors.")
    if sha256(path) != before:
        raise RuntimeError("Source changed during analysis")
    report = {
        "schema_version": "acoustic-measurements-0.1",
        "source": {"path": str(path), "sha256": before, "unchanged": True,
                   "sample_rate_hz": sr, "channels": 1, "subtype": info.subtype, "samples": len(y)},
        "preprocessing": {"analysis_copy": None, "operations": [],
                          "note": "Decoded to floating-point samples in memory; no resampling, trimming, denoising or gain changes."},
        "method": {"estimator": "librosa.pyin", "fmin_hz": fmin, "fmax_hz": fmax,
                   "frame_length_samples": frame_length, "window_duration_s": frame_length/sr,
                   "hop_length_samples": hop, "hop_duration_s": hop/sr,
                   "center": True, "pitch_edge_padding": "constant zero",
                   "timestamps": "Window centers in seconds relative to input file; centers at/after EOF excluded.",
                   "rms": "Same centered window, clipped to actual samples at edges; 20*log10(RMS), full scale=1. Silence dBFS=null (-infinity).",
                   "dependencies": {name: importlib.metadata.version(name) for name in ("librosa", "numpy", "scipy", "soundfile", "matplotlib")}},
        "normalization": {"method": "12 * log2(f0_hz / reference_f0_hz)", "reference_f0_hz": baseline,
                          "reference_scope": "median of voiced F0 frames in this utterance",
                          "note": "Provisional speaker-relative representation, not a Yoruba tone label or score. Short-utterance medians depend on spoken content; cross-speaker comparisons require alignment and stronger baselines."},
        "summary": {"duration_s": len(y)/sr, "frame_count": len(frames), "voiced_frame_count": int(valid.sum()),
                    "voiced_frames_percent": float(100*np.mean(valid)), "median_f0_hz": baseline,
                    "f0_min_hz": float(pitch.min()) if len(pitch) else None,
                    "f0_max_hz": float(pitch.max()) if len(pitch) else None,
                    "f0_range_hz": float(np.ptp(pitch)) if len(pitch) else None,
                    "f0_p05_hz": float(np.percentile(pitch, 5)) if len(pitch) else None,
                    "f0_p95_hz": float(np.percentile(pitch, 95)) if len(pitch) else None},
        "scores": {name: {"status": "UNSCORED", "score": None, "reason": "No validated scoring method."}
                   for name in ("lexical_tone_accuracy", "pronunciation_accuracy", "prosody", "fluency", "overall_speech")},
        "warnings": warnings,
        "limitations": ["F0 and voicing are estimates, not linguistic correctness judgments.",
                        "Unvoiced frames may contain consonants, silence or tracking failures.",
                        "Voicing probability is not calibrated pronunciation confidence.",
                        "dBFS is digital amplitude, not calibrated sound pressure or perceived loudness.",
                        "10 ms frame spacing does not imply 10 ms independent temporal resolution; consult window duration."],
    }
    return report, frames


def write_outputs(report, frames, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(output_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    paths = {"json": directory/"analysis.json", "csv": directory/"frames.csv", "png": directory/"pitch_contour.png"}
    if any(p.exists() for p in paths.values()):
        raise FileExistsError("Output files already exist; choose a new output directory")
    times = np.array([f["timestamp_s"] for f in frames])
    f0 = np.array([f["f0_hz"] if f["f0_hz"] is not None else np.nan for f in frames])
    rel = np.array([f["relative_pitch_semitones"] if f["relative_pitch_semitones"] is not None else np.nan for f in frames])
    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 2, 1]})
    axes[0].plot(times, f0, ".-", ms=2, lw=1, color="#146a9a")
    axes[0].set_ylabel("Estimated F0 (Hz)")
    axes[0].set_ylim(report["method"]["fmin_hz"], report["method"]["fmax_hz"])
    axes[0].set_title("AI Yoruba audio: acoustic measurements only — all quality scores UNSCORED")
    axes[1].plot(times, rel, ".-", ms=2, lw=1, color="#146a9a")
    axes[1].axhline(0, color="gray", lw=.7)
    axes[1].set_ylabel("Relative pitch\n(semitones)")
    voiced = np.array([f["voiced"] for f in frames])
    edges = np.r_[0, (times[:-1]+times[1:])/2, report["summary"]["duration_s"]]
    axes[2].stairs(voiced.astype(int), edges, fill=True, color="#146a9a", alpha=.6)
    axes[2].set_yticks([0, 1], ["Unvoiced", "Voiced"])
    axes[2].set_ylim(-.1, 1.2)
    axes[2].set_xlabel("Time in input clip (seconds); gaps = no voiced F0, not necessarily silence")
    for ax in axes:
        ax.grid(alpha=.2)
        ax.set_xlim(0, report["summary"]["duration_s"])
    fig.tight_layout()
    fig.savefig(paths["png"], dpi=160)
    plt.close(fig)
    with paths["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frames[0]))
        writer.writeheader()
        writer.writerows(frames)
    report["outputs"] = {key: str(path) for key, path in paths.items()}
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return paths
