import csv
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "received_audio_20260718_1309"
RENAMED = ROOT / "work" / "calibration_originals_renamed"
PROCESSED = ROOT / "work" / "calibration_processed_wav"
TOOLS = ROOT / "work" / "audio_tools"
ZIP_BASE = ROOT / "outputs" / "yoruba_calibration_processed"
MANIFEST = PROCESSED / "processed_manifest.csv"
sys.path.insert(0, str(TOOLS))
import imageio_ffmpeg  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 24000


def decode_metrics(path):
    cmd = [FFMPEG, "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    x = np.frombuffer(proc.stdout, dtype="<i2").astype(np.float64)
    peak = np.max(np.abs(x)) / 32768 if len(x) else 0
    rms = np.sqrt(np.mean(x * x)) / 32768 if len(x) else 0
    to_db = lambda v: -120.0 if v <= 0 else 20 * np.log10(v)
    return len(x) / SR, float(to_db(peak)), float(to_db(rms)), float(np.mean(np.abs(x) >= 32760) * 100)


RENAMED.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

rows = []
for idx in range(1, 21):
    expected = f"speaker01_{idx:04d}.m4a"
    source_name = "speaker_0008.m4a" if idx == 8 else expected
    source = SOURCE / source_name
    renamed = RENAMED / expected
    shutil.copy2(source, renamed)
    output = PROCESSED / f"speaker01_{idx:04d}.wav"
    filters = (
        "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:"
        "stop_periods=-1:stop_duration=0.25:stop_threshold=-45dB,"
        "loudnorm=I=-23:TP=-3:LRA=7"
    )
    cmd = [
        FFMPEG, "-y", "-v", "error", "-i", str(renamed), "-af", filters,
        "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(output),
    ]
    subprocess.run(cmd, check=True)
    duration, peak_dbfs, rms_dbfs, clipped_pct = decode_metrics(output)
    rows.append({
        "prompt_id": idx,
        "original_filename": source_name,
        "corrected_original_filename": expected,
        "processed_filename": output.name,
        "duration_s": round(duration, 3),
        "peak_dbfs": round(peak_dbfs, 3),
        "rms_dbfs": round(rms_dbfs, 3),
        "clipped_pct": round(clipped_pct, 6),
    })

with MANIFEST.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

zip_path = Path(shutil.make_archive(str(ZIP_BASE), "zip", PROCESSED))
for row in rows:
    print(row)
print(zip_path)
