#!/usr/bin/env python3
"""Evaluation-only synthesis for Condition C's protected test prompts.

Generates real text-to-speech audio (not teacher-forced reconstruction loss)
from the trained generator checkpoint, using the same decoding settings as
Condition A/B for a fair comparison. Never updates model weights. The tone
classifier head and its extra encoder call are training-only auxiliary
machinery; ordinary inference (generator.infer) doesn't touch them.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from condition_b_training import MMSVocabulary, PROTECTED_TEST_IDS  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", type=Path, default=ROOT / "experiment_01/condition_c_recipe.json")
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--vits-root", type=Path, default=Path("/opt/vits"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    device = torch.device("cuda:0")

    vits_root = args.vits_root.resolve()
    if str(vits_root) not in sys.path:
        sys.path.insert(0, str(vits_root))
    models = importlib.import_module("models")

    config = json.loads((args.model_dir / "config.json").read_text(encoding="utf-8"))
    expected = recipe["acoustic_configuration"]
    for key in ("sampling_rate", "filter_length", "hop_length", "win_length", "n_mel_channels"):
        if config["data"][key] != expected[key]:
            raise ValueError(f"MMS configuration differs for {key}")
    vocabulary = MMSVocabulary(args.model_dir / "vocab.txt", expected["add_blank"])
    model_cfg = config["model"]
    generator = models.SynthesizerTrn(
        len(vocabulary.symbols), expected["filter_length"] // 2 + 1,
        expected["segment_size_samples"] // expected["hop_length"], **model_cfg,
    ).to(device)

    checkpoint = torch.load(args.checkpoint, map_location=device)
    generator.load_state_dict(checkpoint["backend"]["generator"])
    generator.eval()

    rows_all = load_jsonl(args.dataset)
    expected_ids = recipe["data"]["protected_test_prompt_ids"]
    rows = [row for prompt_id in expected_ids for row in rows_all if row["prompt_id"] == prompt_id]
    if [row["prompt_id"] for row in rows] != expected_ids or [row["prompt_id"] for row in rows] != list(PROTECTED_TEST_IDS):
        raise ValueError("Protected test manifest is missing, reordered, or does not match PROTECTED_TEST_IDS")
    if any(row["split"] != "test" for row in rows):
        raise ValueError("A non-test item entered Condition C evaluation")

    decoding = recipe["evaluation"]
    seed = recipe["randomness"]["evaluation_synthesis_seed"]

    args.output.mkdir(parents=True, exist_ok=True)
    audio_dir = args.output / "audio"
    audio_dir.mkdir(exist_ok=True)

    before_hash_sample = next(generator.parameters()).detach().float().sum().item()
    generated = []
    with torch.inference_mode():
        for row in rows:
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            x = vocabulary.encode(row["text_nfc"]).unsqueeze(0).to(device)
            x_lengths = torch.LongTensor([x.shape[1]]).to(device)
            o, *_ = generator.infer(
                x, x_lengths,
                noise_scale=decoding["noise_scale"],
                length_scale=1.0 / decoding["speaking_rate"],
                noise_scale_w=decoding["noise_scale_duration"],
            )
            waveform = o.squeeze().detach().float().cpu().numpy().astype(np.float32)
            output_path = audio_dir / f"condition_c_{row['prompt_id']}.wav"
            sf.write(output_path, waveform, expected["sampling_rate"], subtype="PCM_16")
            peak = float(np.max(np.abs(waveform))) if waveform.size else 0.0
            rms = float(np.sqrt(np.mean(np.square(waveform)))) if waveform.size else 0.0
            generated.append({
                "prompt_id": row["prompt_id"],
                "text_nfc": row["text_nfc"],
                "english_meaning": row["english_meaning"],
                "output_audio": output_path.name,
                "sampling_rate_hz": expected["sampling_rate"],
                "sample_count": int(waveform.size),
                "duration_s": waveform.size / expected["sampling_rate"],
                "peak": peak,
                "rms": rms,
                "silent": bool(rms < 1e-5),
                "finite": bool(np.isfinite(waveform).all()),
            })
    after_hash_sample = next(generator.parameters()).detach().float().sum().item()
    if before_hash_sample != after_hash_sample:
        raise RuntimeError("Model weights changed during Condition C evaluation synthesis")
    if any(item["silent"] or not item["finite"] for item in generated):
        raise RuntimeError("One or more generated outputs failed audio integrity checks")

    manifest = {
        "schema_version": "1.0", "condition": "C", "purpose": "protected_test_evaluation_synthesis",
        "checkpoint_path": str(args.checkpoint), "checkpoint_kind": "development_selected_best",
        "decoding": decoding, "evaluation_synthesis_seed": seed,
        "model_weights_unchanged": before_hash_sample == after_hash_sample,
        "outputs": generated,
    }
    (args.output / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "condition": "C", "outputs": len(generated),
        "weights_unchanged": before_hash_sample == after_hash_sample,
        "all_audio_valid": all(not x["silent"] and x["finite"] for x in generated),
    }, indent=2))


if __name__ == "__main__":
    main()
