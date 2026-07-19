import argparse
import csv
import json
import math
import struct
import wave
from pathlib import Path


def dbfs(value):
    return 20 * math.log10(max(value, 1e-12))


def inspect_wav(path):
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        sample_width = handle.getsampwidth()
        frame_count = handle.getnframes()
        raw = handle.readframes(frame_count)
    if sample_width != 2:
        raise ValueError(f"expected 16-bit PCM, found {sample_width * 8}-bit")
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    if not samples:
        raise ValueError("audio contains no samples")
    peak = max(abs(sample) for sample in samples) / 32768
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples)) / 32768
    clipped = sum(abs(sample) >= 32760 for sample in samples) / len(samples)
    return {
        "channels": channels,
        "sample_rate_hz": sample_rate,
        "sample_width_bits": sample_width * 8,
        "duration_s": frame_count / sample_rate,
        "peak_dbfs": dbfs(peak),
        "rms_dbfs": dbfs(rms),
        "clipped_sample_pct": clipped * 100,
    }


parser = argparse.ArgumentParser()
parser.add_argument("--system-dir", required=True)
parser.add_argument("--targets", default=str(Path(__file__).resolve().parents[1] / "evaluation" / "reference_acoustic_targets.csv"))
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()

system_dir = Path(args.system_dir)
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
with Path(args.targets).open("r", encoding="utf-8-sig", newline="") as handle:
    targets = list(csv.DictReader(handle))

results = []
for target in targets:
    prompt_id = target["prompt_id"]
    candidates = [system_dir / f"{prompt_id}.wav", system_dir / f"speaker01_{prompt_id}.wav"]
    audio = next((candidate for candidate in candidates if candidate.exists()), None)
    row = {
        "prompt_id": prompt_id,
        "audio_filename": "" if audio is None else audio.name,
        "file_present": "yes" if audio else "no",
        "readable": "no",
        "format_pass": "no",
        "reference_duration_s": target["reference_duration_s"],
        "duration_s": "",
        "duration_ratio": "",
        "peak_dbfs": "",
        "rms_dbfs": "",
        "clipped_sample_pct": "",
        "automatic_flags": "missing",
    }
    if audio:
        try:
            metrics = inspect_wav(audio)
            reference_duration = float(target["reference_duration_s"])
            ratio = metrics["duration_s"] / reference_duration
            flags = []
            if metrics["channels"] != 1 or metrics["sample_rate_hz"] != 24000 or metrics["sample_width_bits"] != 16:
                flags.append("format")
            if ratio < 0.5:
                flags.append("very_short")
            elif ratio > 2.0:
                flags.append("very_long")
            if metrics["clipped_sample_pct"] > 0.1:
                flags.append("clipping")
            if metrics["rms_dbfs"] < -45:
                flags.append("very_quiet")
            row.update(
                {
                    "readable": "yes",
                    "format_pass": "yes" if "format" not in flags else "no",
                    "duration_s": f"{metrics['duration_s']:.3f}",
                    "duration_ratio": f"{ratio:.3f}",
                    "peak_dbfs": f"{metrics['peak_dbfs']:.3f}",
                    "rms_dbfs": f"{metrics['rms_dbfs']:.3f}",
                    "clipped_sample_pct": f"{metrics['clipped_sample_pct']:.6f}",
                    "automatic_flags": "none" if not flags else ";".join(flags),
                }
            )
        except Exception as exc:
            row["automatic_flags"] = f"unreadable:{exc}"
    results.append(row)

with (output_dir / "automatic_audio_metrics.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

summary = {
    "expected_files": len(results),
    "present_files": sum(row["file_present"] == "yes" for row in results),
    "readable_files": sum(row["readable"] == "yes" for row in results),
    "format_pass_files": sum(row["format_pass"] == "yes" for row in results),
    "flagged_files": sum(row["automatic_flags"] != "none" for row in results),
    "interpretation": "Automatic results are audio diagnostics only; Yoruba pronunciation, tone, meaning, and naturalness require the human rating workflow.",
}
(output_dir / "automatic_evaluation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
