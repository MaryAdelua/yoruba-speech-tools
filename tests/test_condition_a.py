import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_condition_a_is_an_unmodified_three_item_baseline():
    config = json.loads((ROOT / "experiment_01/condition_a_config.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / "artifacts/experiment_01/condition_a/generation_manifest.json").read_text(encoding="utf-8")
    )
    assert config["condition_definition"] == "unmodified host baseline"
    assert config["training"] == {
        "enabled": False, "updates": 0, "trainable_parameters": 0, "auxiliary_supervision": False
    }
    assert [item["prompt_id"] for item in manifest["outputs"]] == ["YT0028", "YT0029", "YT0030"]
    assert manifest["model_weights_unchanged"] is True
    assert manifest["training_started"] is False
    assert manifest["training_updates"] == 0
    assert all(item["finite"] and not item["silent"] for item in manifest["outputs"])
    assert all((ROOT / "artifacts" / item["output_audio"]).is_file() for item in manifest["outputs"])


def test_condition_a_revised_human_scores_are_recorded():
    path = ROOT / "artifacts/experiment_01/condition_a/human_evaluation_items.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    outcomes = [
        "segmental_pronunciation", "lexical_tone", "intelligibility",
        "meaning_recovery",
    ]
    assert len(rows) == 3
    assert all(row[field] == "yes" for row in rows for field in outcomes)
    assert all(row["naturalness"] == "partial" for row in rows)
    assert all(row["notes"] == "the naturalness can be better" for row in rows)

    summary = json.loads(
        (ROOT / "artifacts/experiment_01/condition_a/human_evaluation_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["evaluation_status"] == "complete_single_rater_pilot"
    assert summary["condition_b_started"] is False
    assert all(summary["outcomes"][field]["rate"] == 1.0 for field in outcomes)
    assert summary["outcomes"]["naturalness"]["strict_yes_rate"] == 0.0
    assert summary["outcomes"]["naturalness"]["partial_or_better_rate"] == 1.0
