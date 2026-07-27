#!/usr/bin/env python3
"""Generate the frozen unmodified MMS Yoruba baseline for Experiment 1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torch.nn.utils
import torch.nn.utils.parametrizations
import transformers
from transformers import AutoTokenizer, VitsModel

# torch>=2.1 makes transformers' VITS/MMS modeling code build WaveNet conv
# layers with the new parametrize-based weight_norm, whose state_dict keys
# (parametrizations.weight.original0/1) don't match the weight_g/weight_v
# keys the public facebook/mms-tts-yor checkpoint was saved with. Without
# this, most WaveNet weights silently fail to load and are randomly
# reinitialized instead -- from_pretrained warns but does not raise, so this
# must be forced back to the legacy API to get a correct pretrained load.
torch.nn.utils.parametrizations.weight_norm = torch.nn.utils.weight_norm


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def state_sha256(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["condition_definition"] != "unmodified host baseline":
        raise ValueError("Condition A must remain the unmodified host baseline")
    if config["training"] != {
        "enabled": False, "updates": 0, "trainable_parameters": 0, "auxiliary_supervision": False
    }:
        raise ValueError("Condition A training settings were changed")

    all_rows = load_jsonl(args.dataset)
    expected = config["test_prompt_ids"]
    rows = [row for prompt_id in expected for row in all_rows if row["prompt_id"] == prompt_id]
    if [row["prompt_id"] for row in rows] != expected:
        raise ValueError("Frozen test manifest is missing or reordered")
    if any(row["split"] != "test" for row in rows):
        raise ValueError("A non-test item entered Condition A")

    args.output.mkdir(parents=True, exist_ok=True)
    audio_dir = args.output / "audio"
    audio_dir.mkdir(exist_ok=True)

    torch.manual_seed(config["experiment_seed"])
    tokenizer = AutoTokenizer.from_pretrained(config["model_id"], revision=config["model_revision"])
    model, loading_info = VitsModel.from_pretrained(
        config["model_id"], revision=config["model_revision"], output_loading_info=True
    )
    if loading_info["missing_keys"] or loading_info["unexpected_keys"] or loading_info["mismatched_keys"]:
        raise RuntimeError(
            "Checkpoint did not load cleanly onto VitsModel "
            f"(missing={len(loading_info['missing_keys'])}, "
            f"unexpected={len(loading_info['unexpected_keys'])}, "
            f"mismatched={len(loading_info['mismatched_keys'])}); "
            "this would silently substitute random weights for part of the pretrained baseline."
        )
    model.eval()
    if any(parameter.requires_grad is False for parameter in model.parameters()):
        # Pretrained modules may contain frozen parameters; all parameters are made explicitly non-trainable below.
        pass
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    if model.config.sampling_rate != config["sampling_rate_hz"]:
        raise ValueError("Frozen sampling rate differs from the checkpoint")
    for key in ("speaking_rate", "noise_scale", "noise_scale_duration"):
        actual = float(getattr(model.config, key))
        if not math.isclose(actual, float(config["decoding"][key]), rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Frozen {key}={config['decoding'][key]} differs from checkpoint {actual}")

    before_hash = state_sha256(model)
    generated = []
    with torch.inference_mode():
        for row in rows:
            encoded = tokenizer(row["text_nfc"], return_tensors="pt")
            waveform = model(**encoded).waveform.squeeze().detach().cpu().numpy().astype(np.float32)
            output_path = audio_dir / f"condition_a_{row['prompt_id']}.wav"
            sf.write(output_path, waveform, model.config.sampling_rate, subtype="PCM_16")
            peak = float(np.max(np.abs(waveform))) if waveform.size else 0.0
            rms = float(np.sqrt(np.mean(np.square(waveform)))) if waveform.size else 0.0
            generated.append({
                "prompt_id": row["prompt_id"],
                "split_group_id": row["split_group_id"],
                "text_nfc": row["text_nfc"],
                "english_meaning": row["english_meaning"],
                "output_audio": output_path.relative_to(args.output.parent.parent).as_posix(),
                "sampling_rate_hz": model.config.sampling_rate,
                "sample_count": int(waveform.size),
                "duration_s": waveform.size / model.config.sampling_rate,
                "peak": peak,
                "rms": rms,
                "silent": bool(rms < 1e-5),
                "finite": bool(np.isfinite(waveform).all()),
                "sha256": sha256_file(output_path),
                "model_input_ids_sha256": sha256_bytes(
                    np.asarray(encoded["input_ids"], dtype=np.int64).tobytes()
                ),
            })
    after_hash = state_sha256(model)
    if before_hash != after_hash:
        raise RuntimeError("Model weights changed during Condition A")
    if any(item["silent"] or not item["finite"] for item in generated):
        raise RuntimeError("One or more generated outputs failed audio integrity checks")

    manifest = {
        "schema_version": "1.0",
        "experiment": config["experiment"],
        "condition": config["condition"],
        "condition_definition": config["condition_definition"],
        "model_id": config["model_id"],
        "model_revision_requested": config["model_revision"],
        "model_commit": getattr(model.config, "_commit_hash", None),
        "model_weights_sha256_before": before_hash,
        "model_weights_sha256_after": after_hash,
        "model_weights_unchanged": before_hash == after_hash,
        "training_started": False,
        "training_updates": 0,
        "experiment_seed": config["experiment_seed"],
        "dataset_sha256": sha256_file(args.dataset),
        "config_sha256": sha256_file(args.config),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "device": "cpu",
        },
        "outputs": generated,
    }
    (args.output / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (args.output / "human_evaluation_items.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "sample_id", "prompt_id", "audio_path", "text_nfc", "english_meaning",
            "segmental_pronunciation", "lexical_tone", "intelligibility",
            "meaning_recovery", "naturalness", "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, item in enumerate(generated, start=1):
            writer.writerow({
                "sample_id": f"A{index:03d}",
                "prompt_id": item["prompt_id"],
                "audio_path": item["output_audio"],
                "text_nfc": item["text_nfc"],
                "english_meaning": item["english_meaning"],
            })
    print(json.dumps({
        "condition": "A", "outputs": len(generated), "weights_unchanged": before_hash == after_hash,
        "training_started": False, "all_audio_valid": all(not x["silent"] and x["finite"] for x in generated),
    }, indent=2))


if __name__ == "__main__":
    main()
