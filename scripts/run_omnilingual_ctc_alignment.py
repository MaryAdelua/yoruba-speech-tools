"""Run Omnilingual ASR CTC acoustic alignment for the 30-item Yoruba batch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
import sherpa_onnx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from omnilingual_alignment import build_alignment  # noqa: E402
from yoruba_orthographic_units import words_and_syllables  # noqa: E402

SOURCE = ROOT / "dataset/candidate_collection/training_batch_01.csv"
AUDIO = ROOT / "work/training_batch_01_wav_24k"
MODEL = ROOT / "work/models/omnilingual-asr-ctc-300m-int8"
OUTPUT = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
SUMMARY = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01_summary.json"
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="replace automatic output only; never touches manual or verified data")
    args = parser.parse_args()
    if OUTPUT.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite {OUTPUT}. Pass --overwrite only to regenerate the automatic layer.")
    recognizer = sherpa_onnx.OfflineRecognizer.from_omnilingual_asr_ctc(
        model=str(MODEL / "model.int8.onnx"), tokens=str(MODEL / "tokens.txt"), num_threads=2, provider="cpu"
    )
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    outputs = []
    pending = []
    for row in rows:
        prompt_id = row["prompt_id"]
        audio_path = AUDIO / f"speaker01_{prompt_id}.wav"
        samples, sample_rate = sf.read(audio_path, dtype="float32")
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1).astype(np.float32)
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        pending.append((row, audio_path, samples, sample_rate, stream))
    recognizer.decode_streams([item[4] for item in pending])
    for row, audio_path, samples, sample_rate, stream in pending:
        prompt_id = row["prompt_id"]
        result = stream.result
        annotation = {
            "prompt_id": prompt_id, "text_nfc": unicodedata.normalize("NFC", row["yoruba"]),
            "audio_path": f"work/training_batch_01_wav_24k/{audio_path.name}",
            "words": words_and_syllables(unicodedata.normalize("NFC", row["yoruba"])),
        }
        aligned = build_alignment(annotation, result.text, list(result.timestamps), len(samples) / sample_rate)
        aligned["decoded_tokens"] = list(result.tokens)
        aligned["decoded_token_timestamps_s"] = [round(float(t), 4) for t in result.timestamps]
        outputs.append(aligned)
        print(f"{prompt_id}: confidence={aligned['utterance_confidence']:.3f}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as f:
        for item in outputs:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "schema_version": "0.1", "record_count": len(outputs),
        "model": "csukuangfj/sherpa-onnx-omnilingual-asr-1600-languages-300M-ctc-int8-2025-11-12",
        "backend": f"sherpa-onnx {sherpa_onnx.__version__}",
        "model_sha256": sha256(MODEL / "model.int8.onnx"), "tokens_sha256": sha256(MODEL / "tokens.txt"),
        "mean_utterance_confidence": round(sum(x["utterance_confidence"] for x in outputs) / len(outputs), 4),
        "human_verification_required": True,
        "automatic_output": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "manual_corrections": "alignment/manual/training_batch_01_manual_corrections.jsonl",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
