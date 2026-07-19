#!/usr/bin/env python3
"""Fail-closed runtime audit for Condition B. This script never trains."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
RECIPE_PATH = ROOT / "experiment_01/condition_b_recipe.json"
DATASET_PATH = ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl"
OUTPUT_PATH = ROOT / "artifacts/experiment_01/condition_b/execution_environment_preflight.json"
APPROVAL_PATH = ROOT / "execution/condition_b/environment_validation_approval.json"
CHECKPOINT_REPORT_PATH = ROOT / "artifacts/experiment_01/condition_b/checkpoint_verification.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit(path: Path) -> str | None:
    if not path.is_dir():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> None:
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    checkpoint_report = (
        json.loads(CHECKPOINT_REPORT_PATH.read_text(encoding="utf-8"))
        if CHECKPOINT_REPORT_PATH.is_file() else {}
    )
    records = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    gpu = None
    if torch.cuda.is_available():
        properties = torch.cuda.get_device_properties(0)
        gpu = {
            "name": properties.name,
            "memory_gb": properties.total_memory / 1024**3,
            "cuda_runtime": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
        }

    checks = {
        "recipe_is_frozen": recipe["status"] == "frozen_pending_user_approval",
        "training_gate_remains_closed": recipe["training_authorized"] is False
        and approval.get("training_approved") is False
        and approval.get("ten_update_validation_approved") is False,
        "environment_validation_is_approved": approval.get("environment_validation_approved") is True
        and approval.get("scope") == "gpu_environment_validation_only"
        and approval.get("recipe_sha256") == sha256_file(RECIPE_PATH)
        and approval.get("dataset_sha256") == sha256_file(DATASET_PATH),
        "dataset_hash_matches": sha256_file(DATASET_PATH) == recipe["data"]["dataset_sha256"],
        "split_counts_match": {
            split: sum(record["split"] == split for record in records)
            for split in ("train", "development", "test")
        } == {"train": 23, "development": 3, "test": 3},
        "test_ids_match": [record["prompt_id"] for record in records if record["split"] == "test"]
        == recipe["data"]["protected_test_prompt_ids"],
        "cuda_available": gpu is not None,
        "gpu_memory_meets_minimum": gpu is not None
        and gpu["memory_gb"] >= recipe["compute"]["minimum_gpu_memory_gb"],
        "vits_commit_matches": git_commit(Path("/opt/vits"))
        == recipe["implementation"]["vits_repository_commit"],
        "fairseq_commit_matches": git_commit(Path("/opt/fairseq"))
        == recipe["implementation"]["mms_repository_commit"],
        "container_digest_recorded": os.environ.get("CONTAINER_IMAGE_DIGEST", "").startswith("sha256:"),
        "generator_checkpoint_loaded": checkpoint_report.get("generator_checkpoint_loaded") is True,
        "discriminator_checkpoint_loaded": checkpoint_report.get("discriminator_checkpoint_loaded") is True,
        "checkpoint_verification_had_zero_updates": checkpoint_report.get("optimizer_updates") == 0,
    }
    result = {
        "schema_version": "1.0",
        "purpose": "environment_preflight_only",
        "training_started": False,
        "recipe_sha256": sha256_file(RECIPE_PATH),
        "dataset_sha256": sha256_file(DATASET_PATH),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "gpu": gpu,
        "checks": checks,
        "environment_validation_passed": all(checks.values()),
        "training_gate_active": checks["training_gate_remains_closed"],
        "approval_gate_active": checks["training_gate_remains_closed"],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
