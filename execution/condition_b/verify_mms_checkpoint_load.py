#!/usr/bin/env python3
"""Load both original checkpoints without data, forward passes, or optimizer updates."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--vits-root", type=Path, default=Path("/opt/vits"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    recipe = json.loads((ROOT / "experiment_01/condition_b_recipe.json").read_text(encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("Checkpoint validation requires the approved CUDA environment")
    sys.path.insert(0, str(args.vits_root))
    models = importlib.import_module("models")
    utils = importlib.import_module("utils")
    config = json.loads((args.model_dir / "config.json").read_text(encoding="utf-8"))
    vocab = (args.model_dir / "vocab.txt").read_text(encoding="utf-8").splitlines()
    acoustic = recipe["acoustic_configuration"]
    generator = models.SynthesizerTrn(
        len(vocab), acoustic["filter_length"] // 2 + 1,
        acoustic["segment_size_samples"] // acoustic["hop_length"], **config["model"],
    ).cuda()
    discriminator = models.MultiPeriodDiscriminator(config["model"]["use_spectral_norm"]).cuda()
    generator_path = args.model_dir / recipe["initialization"]["generator_checkpoint"]
    discriminator_path = args.model_dir / recipe["initialization"]["discriminator_checkpoint"]
    utils.load_checkpoint(generator_path, generator, None)
    utils.load_checkpoint(discriminator_path, discriminator, None)
    report = {
        "schema_version": "1.0", "purpose": "checkpoint_load_only",
        "training_started": False, "optimizer_created": False, "optimizer_updates": 0,
        "forward_passes": 0, "dataset_items_read": 0, "protected_test_items_seen": 0,
        "generator_checkpoint_loaded": True, "discriminator_checkpoint_loaded": True,
        "generator_checkpoint_sha256": sha256_file(generator_path),
        "discriminator_checkpoint_sha256": sha256_file(discriminator_path),
        "gpu": torch.cuda.get_device_name(0),
        "allocated_memory_bytes_after_load": torch.cuda.memory_allocated(0),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
