import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_condition_b_preflight_protects_test_and_starts_no_training():
    manifest = json.loads(
        (ROOT / "artifacts/experiment_01/condition_b/preflight_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["condition_definition"] == "matched Yoruba data adaptation; no auxiliary supervision"
    assert manifest["split_counts"] == {"train": 23, "development": 3, "test": 3}
    assert manifest["audio_files_present"] == 29
    assert manifest["records_without_unknown_tokens"] == 29
    assert manifest["training_started"] is False
    assert manifest["training_updates"] == 0
    assert manifest["test_items_exposed_to_training"] == 0
    assert len(manifest["unresolved_training_specification"]) == 8
    test_rows = [record for record in manifest["records"] if record["split"] == "test"]
    assert [record["prompt_id"] for record in test_rows] == ["YT0028", "YT0029", "YT0030"]
    assert all(record["protected_from_training_and_tuning"] for record in test_rows)
    assert all(not record["eligible_for_weight_updates"] for record in test_rows)
