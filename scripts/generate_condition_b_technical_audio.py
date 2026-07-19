#!/usr/bin/env python3
"""Generate text-only protected-set audio from the approved update-10 checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from condition_b_training import MMSVocabulary, PROTECTED_TEST_IDS, load_jsonl


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vits-root", type=Path, default=Path("/opt/vits"))
    args = parser.parse_args()

    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    required = {
        "approved": True, "approved_by": "Mary Adelua", "condition": "B",
        "scope": "ten_update_evaluation_audio_only", "required_checkpoint_update": 10,
        "protected_test_prompt_ids": PROTECTED_TEST_IDS,
        "protected_test_audio_access_approved": False,
        "text_only_synthesis_approved": True, "full_training_approved": False,
        "recipe_sha256": sha256_file(args.recipe), "dataset_sha256": sha256_file(args.dataset),
    }
    for key, value in required.items():
        if approval.get(key) != value:
            raise PermissionError(f"Evaluation approval mismatch: {key}")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if checkpoint.get("update") != 10:
        raise ValueError("Evaluation requires the update-10 technical checkpoint")
    if checkpoint.get("recipe_sha256") != sha256_file(args.recipe):
        raise ValueError("Checkpoint recipe provenance mismatch")
    if checkpoint.get("dataset_sha256") != sha256_file(args.dataset):
        raise ValueError("Checkpoint dataset provenance mismatch")

    sys.path.insert(0, str(args.vits_root))
    models = importlib.import_module("models")
    config = json.loads((args.model_dir / "config.json").read_text(encoding="utf-8"))
    vocabulary = MMSVocabulary(args.model_dir / "vocab.txt", recipe["acoustic_configuration"]["add_blank"])
    acoustic = recipe["acoustic_configuration"]
    generator = models.SynthesizerTrn(
        len(vocabulary.symbols), acoustic["filter_length"] // 2 + 1,
        acoustic["segment_size_samples"] // acoustic["hop_length"], **config["model"],
    ).cuda()
    generator.load_state_dict(checkpoint["backend"]["generator"])
    generator.eval()

    rows = {row["prompt_id"]: row for row in load_jsonl(args.dataset)}
    if any(rows[prompt_id]["split"] != "test" for prompt_id in PROTECTED_TEST_IDS):
        raise ValueError("Protected test split changed")
    args.output.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(recipe["randomness"]["evaluation_synthesis_seed"])
    torch.cuda.manual_seed_all(recipe["randomness"]["evaluation_synthesis_seed"])
    decoding = recipe["evaluation"]
    outputs = []
    with torch.inference_mode():
        for prompt_id in PROTECTED_TEST_IDS:
            row = rows[prompt_id]
            text = vocabulary.encode(row["text_nfc"]).unsqueeze(0).cuda()
            lengths = torch.LongTensor([text.shape[1]]).cuda()
            audio = generator.infer(
                text, lengths, noise_scale=decoding["noise_scale"],
                noise_scale_w=decoding["noise_scale_duration"],
                length_scale=decoding["speaking_rate"],
            )[0][0, 0].float().cpu().numpy()
            if not np.isfinite(audio).all() or not audio.size:
                raise RuntimeError(f"Invalid synthesized audio for {prompt_id}")
            path = args.output / f"condition_b_update10_{prompt_id}.wav"
            sf.write(path, audio, acoustic["sampling_rate"], subtype="PCM_16")
            outputs.append({"prompt_id": prompt_id, "text_nfc": row["text_nfc"],
                            "audio_path": path.as_posix(), "sha256": sha256_file(path),
                            "duration_s": len(audio) / acoustic["sampling_rate"]})
    manifest = {
        "schema_version": "1.0", "condition": "B", "checkpoint_update": 10,
        "checkpoint_sha256": sha256_file(args.checkpoint), "synthesis_seed": recipe["randomness"]["evaluation_synthesis_seed"],
        "protected_test_audio_read": 0, "full_training_started": False, "outputs": outputs,
    }
    (args.output / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
