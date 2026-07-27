"""Approval-gated Condition C runner: Condition B plus orthographic tone and
syllable-boundary auxiliary supervision -- same MMS/VITS checkpoint, same
recordings, split, training budget, seed, checkpoint rules, and evaluation
criteria as Condition B. The only intended experimental change is the two
auxiliary losses.

Reuses Condition B's dataset handling, VITS backend, and training controller
unmodified (they are architecture/data-loading code, not condition-specific).
Only the recipe/approval validation is duplicated here rather than bent to fit
both conditions in one file, since the frozen Condition B validators
intentionally hardcode "condition B" as a safety property.
"""

from __future__ import annotations

import json
from pathlib import Path

import torch

from condition_b_training import (  # noqa: F401  (re-exported for entrypoint convenience)
    EXPECTED_SPLITS,
    MMSVocabulary,
    OriginalVITSBackend,
    PROTECTED_TEST_IDS,
    SplitPlan,
    YorubaTextAudioDataset,
    collate_text_audio,
    prepare_resampled_audio,
    run_training_controller,
    seed_everything,
    sha256_file,
)


def load_and_validate_recipe(path: Path) -> dict:
    recipe = json.loads(path.read_text(encoding="utf-8"))
    if recipe["condition"] != "C" or recipe["training_authorized"] is not False:
        raise ValueError("Expected the immutable, approval-gated Condition C recipe")
    if recipe["implementation"]["transformers_training_wrapper_allowed"] is not False:
        raise ValueError("Transformers training is prohibited")
    objectives = recipe["objectives"]
    if not (objectives["orthographic_tone_auxiliary"] and objectives["syllable_boundary_auxiliary"]):
        raise ValueError("Condition C must enable exactly the tone and syllable-boundary auxiliary objectives")
    unexpected_auxiliary = [
        key for key, value in objectives.items()
        if key.endswith("_auxiliary") and value
        and key not in ("orthographic_tone_auxiliary", "syllable_boundary_auxiliary")
    ]
    if unexpected_auxiliary:
        raise ValueError(f"Condition C has unintended auxiliary objectives enabled: {unexpected_auxiliary}")
    return recipe


class TonalSyllableVITSBackend(OriginalVITSBackend):
    """Condition B's backend plus two auxiliary losses, computed from the
    verified syllable alignment data (see derive_tone_syllable_targets.py):

    Tone: a small linear head reads the text encoder's per-token hidden state
    (enc_p's `x`, before duration expansion), mean-pooled over each syllable's
    token span, and is trained with cross-entropy against the orthographically
    derived H/M/L label. This needs one extra (cheap) encoder-only forward
    pass, since enc_p's raw hidden state isn't part of the main forward()'s
    return tuple (only the duration-expanded, posterior-aligned m_p/logs_p is).

    Syllable boundary: VITS's own `attn` (the monotonic-alignment duration
    target) is `.detach()`-ed inside the original forward() -- a loss built
    directly on it would compute a number but backprop nothing. The actual
    differentiable duration signal is the stochastic duration predictor's own
    reverse-mode (sampling) pass, the same code path VITS already uses at
    inference. This is invoked a second time during training, purely for this
    auxiliary loss, using the same encoder hidden state as the tone head.
    """

    def __init__(self, vits_root, model_dir, recipe: dict, device):
        super().__init__(
            vits_root, model_dir, recipe, device,
            freeze_duration_predictor=recipe["trainable_modules"].get("freeze_duration_predictor", False),
        )
        obj = recipe["objectives"]
        config = json.loads((Path(model_dir) / "config.json").read_text(encoding="utf-8"))
        hidden_channels = config["model"]["hidden_channels"]
        self.tone_head = torch.nn.Linear(hidden_channels, 3).to(device)
        self.optimizer_g.add_param_group({
            "params": self.tone_head.parameters(),
            "lr": recipe["optimization"]["learning_rate_generator"],
        })
        self.tone_weight = obj["orthographic_tone_auxiliary_weight"]
        self.duration_weight_aux = obj["syllable_boundary_auxiliary_weight"]
        self.duration_normalizer = obj["syllable_boundary_auxiliary_normalizer_frames"]
        self.targets_by_prompt_id: dict[str, list[dict]] = {}

    def set_targets(self, targets_by_prompt_id: dict[str, list[dict]]) -> None:
        self.targets_by_prompt_id = targets_by_prompt_id

    def _auxiliary_losses(self, x, x_lengths, prompt_ids: list[str]):
        x_hidden, _m_p, _logs_p, x_mask = self.generator.enc_p(x, x_lengths)
        logw = self.generator.dp(x_hidden, x_mask, reverse=True, noise_scale=1.0)
        predicted_frames_per_token = torch.exp(logw) * x_mask

        tone_losses = []
        duration_losses = []
        for row_index, prompt_id in enumerate(prompt_ids):
            for syllable in self.targets_by_prompt_id.get(prompt_id, []):
                start, end = syllable["token_start_with_blanks"], syllable["token_end_with_blanks"]
                span = x_hidden[row_index, :, start:end + 1]
                pooled = span.mean(dim=1)
                logits = self.tone_head(pooled.float())
                tone_losses.append(
                    torch.nn.functional.cross_entropy(
                        logits.unsqueeze(0), torch.tensor([syllable["tone_id"]], device=self.device),
                    )
                )
                predicted_duration = predicted_frames_per_token[row_index, 0, start:end + 1].sum()
                target_duration = torch.tensor(
                    syllable["target_duration_frames"], device=self.device, dtype=predicted_duration.dtype,
                )
                duration_losses.append(
                    torch.nn.functional.l1_loss(
                        predicted_duration / self.duration_normalizer,
                        target_duration / self.duration_normalizer,
                    )
                )
        tone_loss = torch.stack(tone_losses).mean() if tone_losses else torch.zeros((), device=self.device)
        duration_loss = torch.stack(duration_losses).mean() if duration_losses else torch.zeros((), device=self.device)
        return tone_loss * self.tone_weight, duration_loss * self.duration_weight_aux

    def accumulate(self, batch, divisor: int) -> dict[str, float]:
        *core_batch, prompt_ids = batch
        x, x_lengths = core_batch[0].to(self.device), core_batch[1].to(self.device)
        losses = self._forward_losses(core_batch, include_adversarial=True)
        if not all(torch.isfinite(value).all() for value in losses.values()):
            raise FloatingPointError("Non-finite Condition C loss")
        tone_loss, duration_loss = self._auxiliary_losses(x, x_lengths, prompt_ids)
        if not (torch.isfinite(tone_loss) and torch.isfinite(duration_loss)):
            raise FloatingPointError("Non-finite Condition C auxiliary loss")
        self.scaler.scale(losses["discriminator"] / divisor).backward()
        generator_total = (
            losses["mel"] + losses["duration"] + losses["kl"] + losses["feature"] + losses["generator"]
            + tone_loss + duration_loss
        )
        self.scaler.scale(generator_total / divisor).backward()
        result = {key: float(value.detach().cpu()) for key, value in losses.items()}
        result["tone_auxiliary"] = float(tone_loss.detach().cpu())
        result["syllable_boundary_auxiliary"] = float(duration_loss.detach().cpu())
        return result

    def evaluate(self, batches) -> float:
        # Auxiliary losses are deliberately excluded from checkpoint selection
        # (recipe: selection_excludes) so the selection rule can't be gamed by
        # them; development evaluation reuses the parent's reconstruction-only
        # metric. Batches here carry a trailing prompt_ids element the parent
        # class's _forward_losses doesn't expect; strip it back off.
        stripped = (batch[:-1] for batch in batches)
        return super().evaluate(stripped)


class YorubaTextAudioDatasetWithPromptId(YorubaTextAudioDataset):
    """Identical to the parent dataset, only also returns each item's
    prompt_id, so the training loop can look up its syllable tone/duration
    targets without changing the shared collate tensor layout Condition B relies on."""

    def __getitem__(self, index: int):
        return (*super().__getitem__(index), self.records[index]["prompt_id"])


def collate_text_audio_with_prompt_ids(batch):
    prompt_ids = [item[-1] for item in batch]
    core = collate_text_audio([item[:-1] for item in batch])
    return (*core, prompt_ids)


def validate_approval(path: Path, recipe_path: Path, dataset_path: Path, expected_scope: str) -> dict:
    approval = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "approved": True,
        "approved_by": "Chidi Nneji",
        "condition": "C",
        "scope": expected_scope,
        "recipe_sha256": sha256_file(recipe_path),
        "dataset_sha256": sha256_file(dataset_path),
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            raise PermissionError(f"Approval field {key!r} does not match the frozen execution")
    if expected_scope == "full_condition_c_training":
        if approval.get("full_training_approved") is not True:
            raise PermissionError("Full Condition C training is not approved")
    else:
        raise PermissionError(f"Unsupported approval scope: {expected_scope}")
    return approval
