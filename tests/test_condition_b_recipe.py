import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_condition_b_recipe_is_frozen_but_not_authorized():
    recipe = json.loads((ROOT / "experiment_01/condition_b_recipe.json").read_text(encoding="utf-8"))
    assert recipe["status"] == "frozen_pending_user_approval"
    assert recipe["training_authorized"] is False
    assert recipe["implementation"]["transformers_training_wrapper_allowed"] is False
    assert recipe["initialization"]["generator_checkpoint"] == "G_100000.pth"
    assert recipe["initialization"]["discriminator_checkpoint"] == "D_100000.pth"
    assert recipe["initialization"]["load_pretrained_optimizer_state"] is False


def test_condition_b_recipe_contains_no_auxiliary_supervision():
    recipe = json.loads((ROOT / "experiment_01/condition_b_recipe.json").read_text(encoding="utf-8"))
    objectives = recipe["objectives"]
    assert objectives["original_vits_only"] is True
    assert objectives["orthographic_tone_auxiliary"] is False
    assert objectives["syllable_boundary_auxiliary"] is False
    assert objectives["phoneme_auxiliary"] is False
    assert objectives["surface_tone_auxiliary"] is False
    assert recipe["trainable_modules"]["auxiliary_heads"] == "none"


def test_condition_b_recipe_protects_test_and_freezes_budget():
    recipe = json.loads((ROOT / "experiment_01/condition_b_recipe.json").read_text(encoding="utf-8"))
    assert recipe["data"]["protected_test_prompt_ids"] == ["YT0028", "YT0029", "YT0030"]
    assert recipe["evaluation"]["test_prompt_ids"] == ["YT0028", "YT0029", "YT0030"]
    assert recipe["evaluation"]["condition_a_audio_and_ratings_immutable"] is True
    optimization = recipe["optimization"]
    assert optimization["learning_rate_generator"] == 1e-5
    assert optimization["learning_rate_discriminator"] == 1e-5
    assert optimization["micro_batch_size"] == 2
    assert optimization["gradient_accumulation_steps"] == 4
    assert optimization["effective_batch_size"] == 8
    assert optimization["max_optimizer_updates"] == 300
    assert recipe["checkpoint_selection"]["early_stopping_patience_evaluations"] == 4
    assert recipe["compute"]["minimum_gpu_memory_gb"] == 12
