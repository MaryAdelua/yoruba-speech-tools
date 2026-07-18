import argparse
import csv
import math
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("--audio-dir", default="work/batch2_received_corrected_names")
parser.add_argument("--out-csv", default="outputs/yoruba_batch2_audio_quality.csv")
parser.add_argument("--out-report", default="outputs/yoruba_batch2_audio_quality_report.md")
parser.add_argument("--batch-label", default="Batch 2")
parser.add_argument("--first-id", type=int, default=131)
parser.add_argument("--last-id", type=int, default=160)
args = parser.parse_args()

AUDIO_DIR = ROOT / args.audio_dir
OUT_CSV = ROOT / args.out_csv
OUT_REPORT = ROOT / args.out_report
FFMPEG = ROOT / "work" / "ffmpeg_batch2.exe"
SR = 16000
QUIET_THRESHOLD = 10 ** (-40 / 20) * 32768


def dbfs(value):
    return -120.0 if value <= 0 else 20 * math.log10(value / 32768.0)


def decode(path):
    command = [FFMPEG, "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float64)


rows = []
for path in sorted(AUDIO_DIR.glob("*.m4a")):
    samples = decode(path)
    absolute = np.abs(samples)
    voiced = np.flatnonzero(absolute >= QUIET_THRESHOLD)
    leading = voiced[0] / SR if len(voiced) else len(samples) / SR
    trailing = (len(samples) - 1 - voiced[-1]) / SR if len(voiced) else len(samples) / SR
    duration = len(samples) / SR
    peak = dbfs(float(absolute.max()))
    rms = dbfs(float(np.sqrt(np.mean(samples * samples))))
    clipped = float(np.mean(absolute >= 32760) * 100)
    quiet = float(np.mean(absolute < QUIET_THRESHOLD) * 100)
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
    prompt_id = int(re.search(r"(\d{4})", path.stem).group(1))
    rows.append({
        "prompt_id": prompt_id,
        "filename": path.name,
        "duration_s": round(duration, 3),
        "peak_dbfs": round(peak, 3),
        "rms_dbfs": round(rms, 3),
        "clipped_pct": round(clipped, 6),
        "quiet_pct": round(quiet, 3),
        "leading_silence_s": round(leading, 3),
        "trailing_silence_s": round(trailing, 3),
        "flags": "; ".join(flags),
    })

with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

ids = {r["prompt_id"] for r in rows}
missing = sorted(set(range(args.first_id, args.last_id + 1)) - ids)
flagged = [r for r in rows if r["flags"]]
lines = [
    f"# Yoruba {args.batch_label} audio-quality report",
    "",
    f"- Files decoded: **{len(rows)} of {args.last_id - args.first_id + 1}**",
    f"- Missing IDs: **{', '.join(map(str, missing)) if missing else 'none'}**",
    f"- Total audio: **{sum(r['duration_s'] for r in rows):.1f} seconds**",
    f"- Duration range: **{min(r['duration_s'] for r in rows):.1f}-{max(r['duration_s'] for r in rows):.1f} seconds**",
    f"- Mean RMS level: **{np.mean([r['rms_dbfs'] for r in rows]):.1f} dBFS**",
    f"- Digital clipping: **{'detected' if any(r['clipped_pct'] > .01 for r in rows) else 'not detected'}**",
    "",
    "## Automatic flags",
    "",
]
if flagged:
    lines.extend(f"- `{r['filename']}`: {r['flags']}" for r in flagged)
else:
    lines.append("- None.")
lines += [
    "",
    "## Scope",
    "",
    "This check measures technical signal quality. It does not verify whether each spoken sentence matches the transcript or whether its Yoruba tones are linguistically correct.",
]
OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
