"""Map, standardize, and quality-check Yoruba pronunciation training batch 01."""

from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "work" / "training_batch_01_received"
MAPPED = ROOT / "work" / "training_batch_01_mapped_originals"
PROCESSED = ROOT / "work" / "training_batch_01_wav_24k"
FFMPEG = ROOT.parent / "work" / "ffmpeg_batch2.exe"
MANIFEST = ROOT / "artifacts" / "yoruba_training_batch_01_audio_quality.csv"
REPORT = ROOT / "artifacts" / "yoruba_training_batch_01_audio_quality_report.md"
SR = 24000
QUIET_THRESHOLD = 10 ** (-40 / 20) * 32768


def dbfs(value: float) -> float:
    return -120.0 if value <= 0 else 20 * math.log10(value / 32768.0)


def decode(path: Path) -> np.ndarray:
    command = [str(FFMPEG), "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float64)


def source_mapping() -> dict[str, Path]:
    mapping = {}
    for path in SOURCE.glob("*.m4a"):
        match = re.fullmatch(r"speaker01_YT(\d+)\.m4a", path.name)
        if not match:
            raise ValueError(f"unexpected filename: {path.name}")
        digits = match.group(1)
        prompt_id = "YT0015" if digits == "00016" else f"YT{int(digits):04d}"
        if prompt_id in mapping:
            raise ValueError(f"duplicate mapping for {prompt_id}")
        mapping[prompt_id] = path
    return mapping


def main() -> None:
    MAPPED.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    mapping = source_mapping()
    expected = {f"YT{i:04d}" for i in range(1, 31)}
    missing = sorted(expected - mapping.keys())
    extra = sorted(mapping.keys() - expected)

    rows = []
    for prompt_id in sorted(mapping):
        source = mapping[prompt_id]
        mapped = MAPPED / f"speaker01_{prompt_id}.m4a"
        shutil.copy2(source, mapped)
        output = PROCESSED / f"speaker01_{prompt_id}.wav"
        filters = (
            "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:"
            "stop_periods=-1:stop_duration=0.25:stop_threshold=-45dB,"
            "loudnorm=I=-23:TP=-3:LRA=7"
        )
        subprocess.run(
            [str(FFMPEG), "-y", "-v", "error", "-i", str(mapped), "-af", filters,
             "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(output)],
            check=True,
        )
        samples = decode(output)
        absolute = np.abs(samples)
        voiced = np.flatnonzero(absolute >= QUIET_THRESHOLD)
        duration = len(samples) / SR
        leading = voiced[0] / SR if len(voiced) else duration
        trailing = (len(samples) - 1 - voiced[-1]) / SR if len(voiced) else duration
        peak = dbfs(float(absolute.max())) if len(samples) else -120.0
        rms = dbfs(float(np.sqrt(np.mean(samples * samples)))) if len(samples) else -120.0
        clipped = float(np.mean(absolute >= 32760) * 100) if len(samples) else 0.0
        flags = []
        if duration < 1.2:
            flags.append("very short")
        if duration > 12:
            flags.append("very long")
        if peak > -0.5 or clipped > 0.01:
            flags.append("possible clipping")
        if peak < -15:
            flags.append("low peak")
        if rms < -36:
            flags.append("low average level")
        if leading > 2:
            flags.append("long leading silence")
        if trailing > 2.5:
            flags.append("long trailing silence")
        rows.append({
            "prompt_id": prompt_id,
            "source_filename": source.name,
            "mapped_filename": mapped.name,
            "processed_filename": output.name,
            "duration_s": round(duration, 3),
            "peak_dbfs": round(peak, 3),
            "rms_dbfs": round(rms, 3),
            "clipped_pct": round(clipped, 6),
            "leading_silence_s": round(leading, 3),
            "trailing_silence_s": round(trailing, 3),
            "automatic_flags": "; ".join(flags),
            "listening_verification": "pending",
        })

    with MANIFEST.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    flagged = [row for row in rows if row["automatic_flags"]]
    lines = [
        "# Yoruba training batch 01 audio-quality report", "",
        f"- Received and decoded: **{len(rows)} of 30**",
        f"- Missing prompt IDs: **{', '.join(missing) if missing else 'none'}**",
        f"- Unexpected prompt IDs: **{', '.join(extra) if extra else 'none'}**",
        "- Filename correction: **speaker01_YT00016.m4a mapped to YT0015**",
        f"- Total standardized audio: **{sum(row['duration_s'] for row in rows):.1f} seconds**",
        f"- Duration range: **{min(row['duration_s'] for row in rows):.2f}–{max(row['duration_s'] for row in rows):.2f} seconds**",
        f"- Digital clipping: **{'detected' if any(row['clipped_pct'] > .01 for row in rows) else 'not detected'}**",
        "", "## Automatic flags", "",
    ]
    lines.extend([f"- `{row['prompt_id']}`: {row['automatic_flags']}" for row in flagged] or ["- None."])
    lines += ["", "## Human-verification status", "", "Transcript, pronunciation, tone, and naturalness listening review is still pending for every received item."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
