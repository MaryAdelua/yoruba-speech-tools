import csv
import shutil
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = ROOT / "work" / "ffmpeg_batch2.exe"
BENCHMARK_SOURCE = ROOT / "work" / "yoruba_voice_benchmark_v0_1"
BENCHMARK_TARGET = ROOT / "work" / "yoruba_voice_benchmark_v0_2"
ALIGNMENT_SOURCE = ROOT / "work" / "yoruba_alignment_v0_14"
ALIGNMENT_TARGET = ROOT / "work" / "yoruba_alignment_v0_15"
BENCHMARK_ZIP = ROOT / "outputs" / "yoruba_voice_benchmark_v0_2_corrected.zip"
ALIGNMENT_ZIP = ROOT / "outputs" / "yoruba_alignment_v0_15_corrected.zip"
PROMPT_ID = "0205"
TRIM_SECONDS = 1.0

for path in (BENCHMARK_TARGET, ALIGNMENT_TARGET, BENCHMARK_ZIP, ALIGNMENT_ZIP):
    if path.exists():
        raise RuntimeError(f"Correction output already exists: {path}")

shutil.copytree(BENCHMARK_SOURCE, BENCHMARK_TARGET)
shutil.copytree(ALIGNMENT_SOURCE, ALIGNMENT_TARGET)

audio = BENCHMARK_TARGET / "audio_wav_24k" / "speaker01_0205.wav"
temporary = audio.with_name("speaker01_0205.trimmed.wav")
with wave.open(str(audio), "rb") as handle:
    original_duration = handle.getnframes() / handle.getframerate()
target_duration = original_duration - TRIM_SECONDS
if target_duration <= 0:
    raise RuntimeError("Requested trim would remove the entire recording")

result = subprocess.run(
    [
        str(FFMPEG),
        "-v", "error",
        "-y",
        "-i", str(audio),
        "-t", f"{target_duration:.6f}",
        "-ac", "1",
        "-ar", "24000",
        "-c:a", "pcm_s16le",
        str(temporary),
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)
if result.returncode:
    raise RuntimeError(result.stderr.decode(errors="replace"))

with wave.open(str(temporary), "rb") as handle:
    corrected_duration = handle.getnframes() / handle.getframerate()
    if handle.getnchannels() != 1 or handle.getframerate() != 24000 or handle.getsampwidth() != 2:
        raise RuntimeError("Corrected recording has unexpected audio format")
if abs(corrected_duration - target_duration) > 0.01:
    raise RuntimeError("Corrected recording duration differs from the requested trim")
temporary.replace(audio)

manifest = BENCHMARK_TARGET / "benchmark_manifest.csv"
with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
    benchmark_rows = list(csv.DictReader(handle))
for row in benchmark_rows:
    row["transcript_alignment_status"] = "verified_by_speaker"
    if row["prompt_id"] == PROMPT_ID:
        row["processed_duration_s"] = f"{corrected_duration:.3f}"
        row["trimmed_end_s"] = f"{TRIM_SECONDS:.1f}"
        row["transcript_alignment_status"] = "verified_by_speaker_audio_trimmed"
with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(benchmark_rows[0].keys()))
    writer.writeheader()
    writer.writerows(benchmark_rows)

correction_log = f"""# Audio correction log

## Recording 0205

- Human review: transcript matched and pronunciation sounded natural
- Issue: small amount of noise after the spoken sentence
- Action: removed the final {TRIM_SECONDS:.1f} second
- Original duration: {original_duration:.3f} seconds
- Corrected duration: {corrected_duration:.3f} seconds
- Re-recording: not required
- Original preservation: the unmodified audio remains in benchmark v0.1
"""
(BENCHMARK_TARGET / "CORRECTION_LOG.md").write_text(correction_log, encoding="utf-8")

queue = ALIGNMENT_TARGET / "listening_verification_queue.csv"
with queue.open("r", encoding="utf-8-sig", newline="") as handle:
    alignment_rows = list(csv.DictReader(handle))
for row in alignment_rows:
    if row["prompt_id"] == PROMPT_ID:
        row["notes_or_correction"] = "none"
with queue.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(alignment_rows[0].keys()))
    writer.writeheader()
    writer.writerows(alignment_rows)

(ALIGNMENT_TARGET / "LISTENING_VERIFICATION_STATUS.md").write_text(
    """# Listening verification status

- Verified by the fluent speaker: **120 of 120**
- Pending: **0 of 120**
- Verified transcript mismatches: **none**
- Verified unnatural pronunciations: **none**
- Outstanding corrections: **none**
- Re-recordings required: **none**
- Resolved corrections: **1 (`0205`: final 1 second trimmed to remove trailing noise)**

Human listening verification and the identified audio correction are complete.
""",
    encoding="utf-8",
)
(ALIGNMENT_TARGET / "CORRECTION_LOG.md").write_text(correction_log, encoding="utf-8")

shutil.make_archive(str(BENCHMARK_ZIP.with_suffix("")), "zip", BENCHMARK_TARGET)
shutil.make_archive(str(ALIGNMENT_ZIP.with_suffix("")), "zip", ALIGNMENT_TARGET)
print(f"original_duration={original_duration:.3f}")
print(f"corrected_duration={corrected_duration:.3f}")
print(BENCHMARK_ZIP)
print(ALIGNMENT_ZIP)
