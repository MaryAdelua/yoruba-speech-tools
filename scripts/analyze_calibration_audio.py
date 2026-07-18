import csv
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "work" / "received_audio_20260718_1309"
TOOLS = ROOT / "work" / "audio_tools"
OUT_CSV = ROOT / "outputs" / "yoruba_calibration_audio_quality.csv"
OUT_REPORT = ROOT / "outputs" / "yoruba_calibration_audio_report.md"
sys.path.insert(0, str(TOOLS))
import imageio_ffmpeg  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 16000
SILENCE_THRESHOLD = 10 ** (-40 / 20) * 32768


def dbfs(value):
    return -120.0 if value <= 0 else 20 * math.log10(value / 32768.0)


def analyze(path):
    cmd = [
        FFMPEG, "-v", "error", "-i", str(path), "-vn", "-f", "s16le",
        "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(SR), "pipe:1",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    samples = np.frombuffer(proc.stdout, dtype="<i2").astype(np.float64)
    if not len(samples):
        raise RuntimeError("Decoded audio contains no samples")
    absolute = np.abs(samples)
    peak = float(absolute.max())
    rms = float(np.sqrt(np.mean(samples * samples)))
    quiet = absolute < SILENCE_THRESHOLD
    voiced_idx = np.flatnonzero(~quiet)
    if len(voiced_idx):
        leading = voiced_idx[0] / SR
        trailing = (len(samples) - 1 - voiced_idx[-1]) / SR
    else:
        leading = len(samples) / SR
        trailing = len(samples) / SR
    clip_fraction = float(np.mean(absolute >= 32760))
    return {
        "duration_s": len(samples) / SR,
        "peak_dbfs": dbfs(peak),
        "rms_dbfs": dbfs(rms),
        "clipped_pct": clip_fraction * 100,
        "quiet_pct": float(np.mean(quiet)) * 100,
        "leading_silence_s": leading,
        "trailing_silence_s": trailing,
    }


rows = []
for path in sorted(AUDIO_DIR.glob("*.m4a")):
    match = re.search(r"(\d{4})", path.stem)
    prompt_id = int(match.group(1)) if match else None
    metrics = analyze(path)
    flags = []
    if metrics["duration_s"] < 1.0:
        flags.append("very short")
    if metrics["duration_s"] > 15.0:
        flags.append("very long")
    if metrics["peak_dbfs"] > -0.5 or metrics["clipped_pct"] > 0.01:
        flags.append("possible clipping")
    if metrics["peak_dbfs"] < -12:
        flags.append("low peak level")
    if metrics["rms_dbfs"] < -35:
        flags.append("low average level")
    if metrics["leading_silence_s"] > 2.0:
        flags.append("long leading silence")
    if metrics["trailing_silence_s"] > 2.0:
        flags.append("long trailing silence")
    expected = f"speaker01_{prompt_id:04d}.m4a" if prompt_id is not None else "unknown"
    if path.name != expected:
        flags.append(f"rename to {expected}")
    rows.append({
        "prompt_id": prompt_id,
        "filename": path.name,
        **{key: round(value, 3) for key, value in metrics.items()},
        "flags": "; ".join(flags),
    })

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ids = {row["prompt_id"] for row in rows}
missing = sorted(set(range(1, 21)) - ids)
flagged = [row for row in rows if row["flags"]]
durations = [row["duration_s"] for row in rows]
rms_values = [row["rms_dbfs"] for row in rows]
peak_values = [row["peak_dbfs"] for row in rows]
total_duration = sum(durations)

lines = [
    "# Yoruba calibration audio report",
    "",
    "## Result",
    "",
    f"- Files received: **{len(rows)} of 20**",
    f"- Missing prompt IDs: **{', '.join(map(str, missing)) if missing else 'none'}**",
    f"- Total recorded audio: **{total_duration:.1f} seconds**",
    f"- Clip duration range: **{min(durations):.1f}-{max(durations):.1f} seconds**",
    f"- Average RMS level: **{np.mean(rms_values):.1f} dBFS**",
    f"- Peak level range: **{min(peak_values):.1f} to {max(peak_values):.1f} dBFS**",
    "",
    "## Automatic checks",
    "",
]
if flagged:
    for row in flagged:
        lines.append(f"- `{row['filename']}`: {row['flags']}")
else:
    lines.append("- No automatic quality flags were raised.")
lines += [
    "",
    "## Interpretation",
    "",
    "These checks evaluate file completeness, decodability, duration, level, digital clipping, and approximate silence. They do not determine whether the spoken Yoruba matches the transcript or whether lexical tones are correct. Those require transcript review and phonetic analysis in the next stage.",
    "",
    "Detailed measurements are available in `yoruba_calibration_audio_quality.csv`.",
]
OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(OUT_CSV)
print(OUT_REPORT)
print("\n".join(lines))
