import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_ten_update_approval_is_narrow_and_hash_bound():
    from src.condition_b_training import validate_approval

    approval = ROOT / "execution/condition_b/ten_update_validation_approval.json"
    recipe = ROOT / "experiment_01/condition_b_recipe.json"
    dataset = ROOT / "dataset/verified/training_batch_01_verified_alignments.jsonl"
    record = validate_approval(approval, recipe, dataset, "ten_update_technical_validation_only")
    assert record["maximum_optimizer_updates"] == 10
    assert record["full_training_approved"] is False
    with pytest.raises(PermissionError):
        validate_approval(approval, recipe, dataset, "full_condition_b_training")


def test_execution_bundle_defaults_to_preflight_only():
    dockerfile = (ROOT / "execution/condition_b/Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["python", "execution/condition_b/preflight_environment.py"]' in dockerfile
    assert "train.py" not in dockerfile
    assert "G_100000.pth" not in dockerfile
    assert "full_model/yor.tar.gz" not in dockerfile


def test_execution_source_commits_match_recipe():
    recipe = json.loads((ROOT / "experiment_01/condition_b_recipe.json").read_text(encoding="utf-8"))
    dockerfile = (ROOT / "execution/condition_b/Dockerfile").read_text(encoding="utf-8")
    assert recipe["implementation"]["vits_repository_commit"] in dockerfile
    assert recipe["implementation"]["mms_repository_commit"] in dockerfile
    assert recipe["training_authorized"] is False


def test_local_execution_preflight_blocks_training():
    report = json.loads(
        (ROOT / "artifacts/experiment_01/condition_b/execution_environment_preflight.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["purpose"] == "environment_preflight_only"
    assert report["training_started"] is False
    assert report["approval_gate_active"] is True
    assert report["checks"]["dataset_hash_matches"] is True
    assert report["checks"]["test_ids_match"] is True
    assert isinstance(report["checks"]["cuda_available"], bool)
    assert report["environment_validation_passed"] is False
    assert report["checks"]["container_digest_recorded"] is False
