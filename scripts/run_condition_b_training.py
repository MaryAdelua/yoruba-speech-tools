#!/usr/bin/env python3
"""Condition B entrypoint. Validation is local; production training is approval-gated."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from condition_b_training import (
    EXPECTED_SPLITS,
    MMSVocabulary,
    OriginalVITSBackend,
    PROTECTED_TEST_IDS,
    SplitPlan,
    YorubaTextAudioDataset,
    collate_text_audio,
    load_and_validate_recipe,
    prepare_resampled_audio,
    run_training_controller,
    seed_everything,
    sha256_file,
    validate_approval,
)


def git_commit(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def source_tree_sha256(path: Path) -> str:
    """Hash tracked source contents at the pinned commit, independent of checkout metadata."""
    listing = subprocess.run(
        ["git", "-C", str(path), "ls-tree", "-r", "--full-tree", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


class TinyValidationBackend:
    """CPU backend for orchestration tests only; it is not a speech-model substitute."""

    def __init__(self, learning_rate: float):
        self.generator = torch.nn.Linear(2, 1)
        self.discriminator = torch.nn.Linear(1, 1)
        self.optimizer_g = torch.optim.AdamW(self.generator.parameters(), lr=learning_rate)
        self.optimizer_d = torch.optim.AdamW(self.discriminator.parameters(), lr=learning_rate)
        self.optimizer_g.zero_grad(set_to_none=True)
        self.optimizer_d.zero_grad(set_to_none=True)
        self.eval_count = 0

    def accumulate(self, batch, divisor: int):
        x, target = batch
        generated = self.generator(x)
        real_score = self.discriminator(target)
        fake_score = self.discriminator(generated.detach())
        loss_d = ((1 - real_score) ** 2 + fake_score**2).mean()
        loss_d.div(divisor).backward()
        prior = [parameter.requires_grad for parameter in self.discriminator.parameters()]
        for parameter in self.discriminator.parameters():
            parameter.requires_grad_(False)
        loss_g = ((self.generator(x) - target) ** 2).mean()
        loss_g.div(divisor).backward()
        for parameter, requires_grad in zip(self.discriminator.parameters(), prior):
            parameter.requires_grad_(requires_grad)
        return {"discriminator": float(loss_d.detach()), "generator": float(loss_g.detach())}

    def step(self, gradient_norm_clip: float):
        norm_d = torch.nn.utils.clip_grad_norm_(self.discriminator.parameters(), gradient_norm_clip)
        norm_g = torch.nn.utils.clip_grad_norm_(self.generator.parameters(), gradient_norm_clip)
        self.optimizer_d.step()
        self.optimizer_g.step()
        self.optimizer_d.zero_grad(set_to_none=True)
        self.optimizer_g.zero_grad(set_to_none=True)
        return {"gradient_norm_d": float(norm_d), "gradient_norm_g": float(norm_g)}

    def evaluate(self, batches):
        # Two genuine improvements followed by a plateau exercise the frozen early-stop state machine.
        values = [10.0, 9.0, 9.0, 9.0, 9.0, 9.0]
        value = values[min(self.eval_count, len(values) - 1)]
        self.eval_count += 1
        return value

    def checkpoint_state(self):
        return {
            "generator": self.generator.state_dict(), "discriminator": self.discriminator.state_dict(),
            "optimizer_g": self.optimizer_g.state_dict(), "optimizer_d": self.optimizer_d.state_dict(),
        }

    def load_checkpoint_state(self, state):
        self.generator.load_state_dict(state["generator"])
        self.discriminator.load_state_dict(state["discriminator"])
        self.optimizer_g.load_state_dict(state["optimizer_g"])
        self.optimizer_d.load_state_dict(state["optimizer_d"])


def run_smoke(recipe: dict, recipe_path: Path, dataset_path: Path, output: Path) -> None:
    seed_everything(recipe["randomness"]["training_seed"], True)
    backend = TinyValidationBackend(recipe["optimization"]["learning_rate_generator"])
    train = [
        (torch.tensor([[0.0, 1.0]]), torch.tensor([[1.0]])),
        (torch.tensor([[1.0, 0.0]]), torch.tensor([[0.5]])),
    ]
    development = [object(), object(), object()]
    summary = run_training_controller(
        backend, train, development, recipe, output, sha256_file(recipe_path), sha256_file(dataset_path),
        max_updates_override=150,
    )
    summary["validation_mode"] = "synthetic_cpu_orchestration_only"
    summary["condition_b_model_weights_loaded"] = False
    summary["condition_b_audio_used"] = False
    (output / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "log"}, indent=2))


def run_production(args, recipe: dict, split: SplitPlan, *, technical_validation: bool) -> None:
    recipe_path, dataset_path = args.recipe.resolve(), args.dataset.resolve()
    scope = "ten_update_technical_validation_only" if technical_validation else "full_condition_b_training"
    approval = validate_approval(args.approval.resolve(), recipe_path, dataset_path, scope)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    if memory_gb < recipe["compute"]["minimum_gpu_memory_gb"]:
        raise RuntimeError(f"GPU has {memory_gb:.1f} GB; frozen minimum is 12 GB")
    if os.environ.get("CONTAINER_IMAGE_DIGEST", "").startswith("sha256:") is False:
        raise RuntimeError("CONTAINER_IMAGE_DIGEST must record the immutable container digest")
    if git_commit(args.vits_root) != recipe["implementation"]["vits_repository_commit"]:
        raise RuntimeError("VITS commit mismatch")
    if git_commit(args.fairseq_root) != recipe["implementation"]["mms_repository_commit"]:
        raise RuntimeError("fairseq commit mismatch")
    if args.archive.stat().st_size != recipe["initialization"]["expected_archive_bytes"]:
        raise RuntimeError("Full MMS archive byte count mismatch")
    archive_sha = sha256_file(args.archive)
    for name in ("config.json", "vocab.txt", "G_100000.pth", "D_100000.pth"):
        if not (args.model_dir / name).is_file():
            raise FileNotFoundError(args.model_dir / name)

    # Test rows are deliberately not passed to preprocessing or either loader.
    selected = list(split.train + split.development)
    derived = prepare_resampled_audio(selected, args.work_dir / "audio_16k", recipe)
    by_id = {row["prompt_id"]: row for row in derived}
    train_records = [by_id[row["prompt_id"]] for row in split.optimization_rows()]
    dev_records = [by_id[row["prompt_id"]] for row in split.development]
    if {row["prompt_id"] for row in train_records + dev_records} & set(PROTECTED_TEST_IDS):
        raise RuntimeError("Protected test item entered materialized data")
    (args.work_dir / "derived_audio_manifest.json").write_text(
        json.dumps(derived, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    vocabulary = MMSVocabulary(args.model_dir / "vocab.txt", add_blank=True)
    train_dataset = YorubaTextAudioDataset(train_records, vocabulary, args.vits_root, recipe)
    dev_dataset = YorubaTextAudioDataset(dev_records, vocabulary, args.vits_root, recipe)
    seed_generator = torch.Generator().manual_seed(recipe["randomness"]["training_seed"])
    batch_size = recipe["optimization"]["micro_batch_size"]
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, generator=seed_generator,
        collate_fn=collate_text_audio, num_workers=2, pin_memory=True, drop_last=True,
    )
    dev_loader = torch.utils.data.DataLoader(
        # One item per batch makes the frozen mean development metric an equal
        # average of the three clips rather than an average of unequally sized batches.
        dev_dataset, batch_size=1, shuffle=False, collate_fn=collate_text_audio,
        num_workers=2, pin_memory=True, drop_last=False,
    )
    seed_everything(recipe["randomness"]["training_seed"], True)
    provenance = {
        "recipe_sha256": sha256_file(recipe_path), "dataset_sha256": sha256_file(dataset_path),
        "archive_sha256": archive_sha,
        "generator_checkpoint_sha256": sha256_file(args.model_dir / "G_100000.pth"),
        "discriminator_checkpoint_sha256": sha256_file(args.model_dir / "D_100000.pth"),
        "vits_commit": git_commit(args.vits_root), "fairseq_commit": git_commit(args.fairseq_root),
        "vits_source_tree_sha256": source_tree_sha256(args.vits_root),
        "fairseq_source_tree_sha256": source_tree_sha256(args.fairseq_root),
        "container_image_digest": os.environ["CONTAINER_IMAGE_DIGEST"],
        "gpu": torch.cuda.get_device_name(0), "gpu_memory_gb": memory_gb,
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "packages": sorted(
            f"{item.metadata.get('Name') or 'unknown'}=={item.version}"
            for item in importlib.metadata.distributions()
        ),
        "protected_test_items_seen": 0,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "runtime_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    backend = OriginalVITSBackend(args.vits_root, args.model_dir, recipe, torch.device("cuda:0"))
    summary = run_training_controller(
        backend, train_loader, dev_loader, recipe, args.output,
        provenance["recipe_sha256"], provenance["dataset_sha256"],
        max_updates_override=approval["maximum_optimizer_updates"] if technical_validation else None,
        allow_unselected_final_checkpoint=technical_validation,
    )
    if technical_validation and summary["optimizer_updates"] != 10:
        raise RuntimeError("Technical validation did not complete exactly 10 optimizer updates")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--orchestration-smoke-test", action="store_true")
    mode.add_argument("--technical-validation", action="store_true")
    mode.add_argument("--train", action="store_true")
    parser.add_argument("--recipe", type=Path, default=ROOT / "experiment_01/condition_b_recipe.json")
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/experiment_01/condition_b/training")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--vits-root", type=Path, default=Path("/opt/vits"))
    parser.add_argument("--fairseq-root", type=Path, default=Path("/opt/fairseq"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--work-dir", type=Path, default=ROOT / "work/condition_b_runtime")
    args = parser.parse_args()

    recipe = load_and_validate_recipe(args.recipe)
    if sha256_file(args.dataset) != recipe["data"]["dataset_sha256"]:
        raise ValueError("Dataset hash differs from the frozen recipe")
    split = SplitPlan.from_manifest(args.dataset, recipe)
    if args.validate_only:
        print(json.dumps({
            "condition": "B", "recipe_valid": True, "split_counts": EXPECTED_SPLITS,
            "protected_test_ids": PROTECTED_TEST_IDS, "training_started": False,
        }, indent=2))
        return
    if args.orchestration_smoke_test:
        run_smoke(recipe, args.recipe, args.dataset, args.output)
        return
    required = {"approval": args.approval, "archive": args.archive, "model_dir": args.model_dir}
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ValueError(f"Production training arguments missing: {missing}")
    run_production(args, recipe, split, technical_validation=args.technical_validation)


if __name__ == "__main__":
    main()
