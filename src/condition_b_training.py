"""Approval-gated Condition B runner around the original MMS/VITS components."""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import torch


EXPECTED_SPLITS = {"train": 23, "development": 3, "test": 3}
PROTECTED_TEST_IDS = ["YT0028", "YT0029", "YT0030"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def load_and_validate_recipe(path: Path) -> dict:
    recipe = json.loads(path.read_text(encoding="utf-8"))
    if recipe["condition"] != "B" or recipe["training_authorized"] is not False:
        raise ValueError("Expected the immutable, approval-gated Condition B recipe")
    if recipe["implementation"]["transformers_training_wrapper_allowed"] is not False:
        raise ValueError("Transformers training is prohibited")
    if not recipe["objectives"]["original_vits_only"]:
        raise ValueError("Condition B must use only original VITS objectives")
    auxiliary = [key for key, value in recipe["objectives"].items() if key.endswith("_auxiliary") and value]
    if auxiliary:
        raise ValueError(f"Condition B auxiliary objectives are enabled: {auxiliary}")
    return recipe


@dataclass(frozen=True)
class SplitPlan:
    train: tuple[dict, ...]
    development: tuple[dict, ...]
    test: tuple[dict, ...]

    @classmethod
    def from_manifest(cls, path: Path, recipe: dict) -> "SplitPlan":
        rows = load_jsonl(path)
        groups = {split: tuple(row for row in rows if row["split"] == split) for split in EXPECTED_SPLITS}
        counts = {split: len(value) for split, value in groups.items()}
        if counts != EXPECTED_SPLITS:
            raise ValueError(f"Split counts changed: {counts}")
        test_ids = [row["prompt_id"] for row in groups["test"]]
        if test_ids != PROTECTED_TEST_IDS or test_ids != recipe["data"]["protected_test_prompt_ids"]:
            raise ValueError("Protected test set changed")
        train_groups = {row["split_group_id"] for row in groups["train"]}
        dev_groups = {row["split_group_id"] for row in groups["development"]}
        test_groups = {row["split_group_id"] for row in groups["test"]}
        if train_groups & dev_groups or train_groups & test_groups or dev_groups & test_groups:
            raise ValueError("Split-group leakage detected")
        return cls(groups["train"], groups["development"], groups["test"])

    def optimization_rows(self) -> tuple[dict, ...]:
        if any(row["prompt_id"] in PROTECTED_TEST_IDS for row in self.train + self.development):
            raise ValueError("Protected test item entered optimization or selection")
        return self.train


def validate_approval(path: Path, recipe_path: Path, dataset_path: Path, expected_scope: str) -> dict:
    approval = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "approved": True,
        "approved_by": "Mary Adelua",
        "condition": "B",
        "scope": expected_scope,
        "recipe_sha256": sha256_file(recipe_path),
        "dataset_sha256": sha256_file(dataset_path),
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            raise PermissionError(f"Approval field {key!r} does not match the frozen execution")
    if expected_scope == "ten_update_technical_validation_only":
        if approval.get("maximum_optimizer_updates") != 10:
            raise PermissionError("Technical validation must be limited to exactly 10 updates")
        if approval.get("full_training_approved") is not False:
            raise PermissionError("Technical-validation approval cannot authorize full training")
        if approval.get("protected_test_evaluation_approved") is not False:
            raise PermissionError("Technical validation cannot authorize protected-test evaluation")
    elif expected_scope == "full_condition_b_training":
        if approval.get("full_training_approved") is not True:
            raise PermissionError("Full Condition B training is not approved")
    else:
        raise PermissionError(f"Unsupported approval scope: {expected_scope}")
    return approval


def seed_everything(seed: int, deterministic: bool) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(deterministic)


class MMSVocabulary:
    def __init__(self, path: Path, add_blank: bool = True):
        self.symbols = path.read_text(encoding="utf-8").splitlines()
        self.symbol_to_id = {symbol: index for index, symbol in enumerate(self.symbols)}
        self.add_blank = add_blank

    def encode(self, text: str) -> torch.LongTensor:
        normalized = text.lower()
        filtered = [character for character in normalized if character in self.symbol_to_id]
        sequence = [self.symbol_to_id[character] for character in filtered]
        if self.add_blank:
            with_blanks = [0] * (len(sequence) * 2 + 1)
            with_blanks[1::2] = sequence
            sequence = with_blanks
        if not sequence:
            raise ValueError("MMS vocabulary removed the complete transcript")
        return torch.LongTensor(sequence)


def prepare_resampled_audio(rows: Iterable[dict], output_dir: Path, recipe: dict) -> list[dict]:
    """Create derived 16 kHz PCM files without changing source audio or manifests."""
    try:
        import torchaudio
    except ImportError as exc:
        raise RuntimeError("Frozen preprocessing requires torchaudio") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    derived = []
    data_cfg = recipe["data"]
    for row in rows:
        source = Path(row["audio_path"])
        waveform, sample_rate = torchaudio.load(source, normalize=True)
        if waveform.shape[0] != 1 or sample_rate != data_cfg["source_sample_rate_hz"]:
            raise ValueError(f"{row['prompt_id']}: unexpected source audio properties")
        target = output_dir / f"{row['prompt_id']}.wav"
        resampled = torchaudio.functional.resample(
            waveform,
            sample_rate,
            data_cfg["training_sample_rate_hz"],
            lowpass_filter_width=data_cfg["lowpass_filter_width"],
            rolloff=data_cfg["rolloff"],
            resampling_method=data_cfg["resampling_method"],
        )
        torchaudio.save(target, resampled, data_cfg["training_sample_rate_hz"], encoding="PCM_S", bits_per_sample=16)
        derived.append({
            "prompt_id": row["prompt_id"], "split": row["split"], "text_nfc": row["text_nfc"],
            "source_audio": source.as_posix(), "source_sha256": sha256_file(source),
            "derived_audio": target.as_posix(), "derived_sha256": sha256_file(target),
            "sample_rate_hz": data_cfg["training_sample_rate_hz"],
        })
    return derived


class YorubaTextAudioDataset(torch.utils.data.Dataset):
    def __init__(self, records: list[dict], vocabulary: MMSVocabulary, vits_root: Path, recipe: dict):
        self.records = records
        self.vocabulary = vocabulary
        self.recipe = recipe
        if str(vits_root) not in sys.path:
            sys.path.insert(0, str(vits_root))
        self.mel_processing = importlib.import_module("mel_processing")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError("soundfile is required") from exc
        row = self.records[index]
        audio, sample_rate = sf.read(row["derived_audio"], dtype="float32", always_2d=False)
        if audio.ndim != 1 or sample_rate != self.recipe["acoustic_configuration"]["sampling_rate"]:
            raise ValueError(f"{row['prompt_id']}: invalid derived audio")
        waveform = torch.from_numpy(audio).unsqueeze(0)
        cfg = self.recipe["acoustic_configuration"]
        spectrogram = self.mel_processing.spectrogram_torch(
            waveform, cfg["filter_length"], cfg["sampling_rate"], cfg["hop_length"],
            cfg["win_length"], center=False,
        ).squeeze(0)
        return self.vocabulary.encode(row["text_nfc"]), spectrogram, waveform


def collate_text_audio(batch):
    order = sorted(range(len(batch)), key=lambda index: batch[index][1].shape[1], reverse=True)
    texts, specs, waves = zip(*(batch[index] for index in order))
    text_lengths = torch.LongTensor([item.numel() for item in texts])
    spec_lengths = torch.LongTensor([item.shape[1] for item in specs])
    wave_lengths = torch.LongTensor([item.shape[1] for item in waves])
    text_pad = torch.zeros(len(batch), int(text_lengths.max().item()), dtype=torch.long)
    spec_pad = torch.zeros(len(batch), specs[0].shape[0], int(spec_lengths.max().item()))
    wave_pad = torch.zeros(len(batch), 1, int(wave_lengths.max().item()))
    for index, (text, spec, wave) in enumerate(zip(texts, specs, waves)):
        text_pad[index, : text.numel()] = text
        spec_pad[index, :, : spec.shape[1]] = spec
        wave_pad[index, :, : wave.shape[1]] = wave
    return text_pad, text_lengths, spec_pad, spec_lengths, wave_pad, wave_lengths


@contextlib.contextmanager
def frozen_parameters(module: torch.nn.Module):
    prior = [parameter.requires_grad for parameter in module.parameters()]
    try:
        for parameter in module.parameters():
            parameter.requires_grad_(False)
        yield
    finally:
        for parameter, requires_grad in zip(module.parameters(), prior):
            parameter.requires_grad_(requires_grad)


class OriginalVITSBackend:
    """Original VITS model/loss adapter. Construct only inside the approved CUDA environment."""

    def __init__(self, vits_root: Path, model_dir: Path, recipe: dict, device: torch.device):
        if device.type != "cuda":
            raise RuntimeError("Frozen Condition B production training requires CUDA")
        if str(vits_root) not in sys.path:
            sys.path.insert(0, str(vits_root))
        models = importlib.import_module("models")
        losses = importlib.import_module("losses")
        utils = importlib.import_module("utils")
        mel_processing = importlib.import_module("mel_processing")
        config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
        expected = recipe["acoustic_configuration"]
        for key in ("sampling_rate", "filter_length", "hop_length", "win_length", "n_mel_channels"):
            if config["data"][key] != expected[key]:
                raise ValueError(f"MMS configuration differs for {key}")
        vocabulary = MMSVocabulary(model_dir / "vocab.txt", expected["add_blank"])
        model_cfg = config["model"]
        self.generator = models.SynthesizerTrn(
            len(vocabulary.symbols), expected["filter_length"] // 2 + 1,
            expected["segment_size_samples"] // expected["hop_length"], **model_cfg,
        ).to(device)
        self.discriminator = models.MultiPeriodDiscriminator(model_cfg["use_spectral_norm"]).to(device)
        utils.load_checkpoint(model_dir / recipe["initialization"]["generator_checkpoint"], self.generator, None)
        utils.load_checkpoint(model_dir / recipe["initialization"]["discriminator_checkpoint"], self.discriminator, None)
        opt = recipe["optimization"]
        kwargs = {"betas": tuple(opt["betas"]), "eps": opt["epsilon"], "weight_decay": opt["weight_decay"]}
        self.optimizer_g = torch.optim.AdamW(self.generator.parameters(), lr=opt["learning_rate_generator"], **kwargs)
        self.optimizer_d = torch.optim.AdamW(self.discriminator.parameters(), lr=opt["learning_rate_discriminator"], **kwargs)
        self.scaler = torch.cuda.amp.GradScaler(enabled=opt["mixed_precision"] == "fp16")
        self.losses, self.mel_processing, self.device, self.recipe = losses, mel_processing, device, recipe
        self.optimizer_g.zero_grad(set_to_none=True)
        self.optimizer_d.zero_grad(set_to_none=True)

    def _forward_losses(self, batch, include_adversarial: bool):
        x, x_lengths, spec, spec_lengths, y, _ = [value.to(self.device) for value in batch]
        cfg = self.recipe["acoustic_configuration"]
        obj = self.recipe["objectives"]
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
            output = self.generator(x, x_lengths, spec, spec_lengths)
            y_hat, length_loss, _, ids_slice, _, z_mask, latent = output
            z, z_p, m_p, logs_p, m_q, logs_q = latent
            mel = self.mel_processing.spec_to_mel_torch(
                spec, cfg["filter_length"], cfg["n_mel_channels"], cfg["sampling_rate"],
                cfg["mel_fmin"], cfg["mel_fmax"],
            )
            import commons
            y_mel = commons.slice_segments(mel, ids_slice, cfg["segment_size_samples"] // cfg["hop_length"])
            y_hat_mel = self.mel_processing.mel_spectrogram_torch(
                y_hat.squeeze(1), cfg["filter_length"], cfg["n_mel_channels"], cfg["sampling_rate"],
                cfg["hop_length"], cfg["win_length"], cfg["mel_fmin"], cfg["mel_fmax"],
            )
            y_slice = commons.slice_segments(y, ids_slice * cfg["hop_length"], cfg["segment_size_samples"])
        loss_duration = torch.sum(length_loss.float()) * obj["duration_weight"]
        loss_mel = torch.nn.functional.l1_loss(y_mel.float(), y_hat_mel.float()) * obj["mel_l1_weight"]
        loss_kl = self.losses.kl_loss(z_p, logs_q, m_p, logs_p, z_mask) * obj["kl_weight"]
        result = {"mel": loss_mel, "duration": loss_duration, "kl": loss_kl}
        if include_adversarial:
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
                real_d, fake_d, _, _ = self.discriminator(y_slice, y_hat.detach())
                loss_d, _, _ = self.losses.discriminator_loss(real_d, fake_d)
                with frozen_parameters(self.discriminator):
                    _, fake_g, fmap_real, fmap_fake = self.discriminator(y_slice, y_hat)
                    loss_fm = self.losses.feature_loss(fmap_real, fmap_fake)
                    loss_g, _ = self.losses.generator_loss(fake_g)
            result.update({"discriminator": loss_d, "feature": loss_fm, "generator": loss_g})
        return result

    def accumulate(self, batch, divisor: int) -> dict[str, float]:
        losses = self._forward_losses(batch, include_adversarial=True)
        if not all(torch.isfinite(value).all() for value in losses.values()):
            raise FloatingPointError("Non-finite Condition B loss")
        self.scaler.scale(losses["discriminator"] / divisor).backward()
        generator_total = losses["mel"] + losses["duration"] + losses["kl"] + losses["feature"] + losses["generator"]
        self.scaler.scale(generator_total / divisor).backward()
        return {key: float(value.detach().cpu()) for key, value in losses.items()}

    def step(self, gradient_norm_clip: float) -> dict[str, float]:
        self.scaler.unscale_(self.optimizer_d)
        self.scaler.unscale_(self.optimizer_g)
        norm_d = torch.nn.utils.clip_grad_norm_(self.discriminator.parameters(), gradient_norm_clip)
        norm_g = torch.nn.utils.clip_grad_norm_(self.generator.parameters(), gradient_norm_clip)
        if not torch.isfinite(norm_d) or not torch.isfinite(norm_g):
            raise FloatingPointError("Non-finite gradient norm")
        self.scaler.step(self.optimizer_d)
        self.scaler.step(self.optimizer_g)
        self.scaler.update()
        self.optimizer_d.zero_grad(set_to_none=True)
        self.optimizer_g.zero_grad(set_to_none=True)
        return {"gradient_norm_d": float(norm_d), "gradient_norm_g": float(norm_g)}

    def evaluate(self, batches: Iterable) -> float:
        # The posterior path samples noise. Reusing the frozen training seed for
        # every development pass makes checkpoint selection repeatable without
        # perturbing the training RNG stream.
        cpu_rng = torch.get_rng_state()
        cuda_rng = torch.cuda.get_rng_state_all()
        torch.manual_seed(self.recipe["randomness"]["training_seed"])
        torch.cuda.manual_seed_all(self.recipe["randomness"]["training_seed"])
        self.generator.eval()
        values = []
        try:
            with torch.inference_mode():
                for batch in batches:
                    losses = self._forward_losses(batch, include_adversarial=False)
                    values.append(float((losses["mel"] + losses["duration"] + losses["kl"]).cpu()))
        finally:
            self.generator.train()
            torch.set_rng_state(cpu_rng)
            torch.cuda.set_rng_state_all(cuda_rng)
        if not values:
            raise ValueError("Development loader is empty")
        return sum(values) / len(values)

    def checkpoint_state(self) -> dict:
        return {
            "generator": self.generator.state_dict(), "discriminator": self.discriminator.state_dict(),
            "optimizer_g": self.optimizer_g.state_dict(), "optimizer_d": self.optimizer_d.state_dict(),
            "scaler": self.scaler.state_dict(),
        }

    def load_checkpoint_state(self, state: dict) -> None:
        self.generator.load_state_dict(state["generator"])
        self.discriminator.load_state_dict(state["discriminator"])
        self.optimizer_g.load_state_dict(state["optimizer_g"])
        self.optimizer_d.load_state_dict(state["optimizer_d"])
        self.scaler.load_state_dict(state["scaler"])


@dataclass
class EarlyStoppingState:
    best_metric: float = math.inf
    best_update: int = 0
    non_improving: int = 0

    def observe(self, metric: float, update: int, relative_delta: float) -> bool:
        threshold = self.best_metric * (1.0 - relative_delta)
        improved = not math.isfinite(self.best_metric) or metric < threshold
        if improved:
            self.best_metric, self.best_update, self.non_improving = metric, update, 0
        else:
            self.non_improving += 1
        return improved


def atomic_torch_save(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, path)


def cycle_batches(loader: Iterable) -> Iterator:
    while True:
        yielded = False
        for batch in loader:
            yielded = True
            yield batch
        if not yielded:
            raise ValueError("Training loader is empty")


def run_training_controller(backend, train_loader: Iterable, development_loader: Iterable, recipe: dict,
                            output_dir: Path, recipe_hash: str, dataset_hash: str,
                            max_updates_override: int | None = None) -> dict:
    opt = recipe["optimization"]
    select = recipe["checkpoint_selection"]
    accumulation = opt["gradient_accumulation_steps"]
    max_updates = max_updates_override or opt["max_optimizer_updates"]
    early = EarlyStoppingState()
    iterator = cycle_batches(train_loader)
    log = []
    stopped_early = False
    for update in range(1, max_updates + 1):
        micro_losses = []
        for _ in range(accumulation):
            micro_losses.append(backend.accumulate(next(iterator), accumulation))
        norms = backend.step(opt["gradient_norm_clip"])
        mean_losses = {
            key: sum(item[key] for item in micro_losses) / len(micro_losses)
            for key in micro_losses[0]
        }
        entry = {"update": update, "microbatch_count": accumulation,
                 "mean_training_losses": mean_losses, **norms}
        if update % select["evaluate_every_updates"] == 0:
            metric = backend.evaluate(development_loader)
            improved = early.observe(metric, update, select["minimum_relative_improvement"])
            train_reconstruction = sum(mean_losses.get(key, 0.0) for key in ("mel", "duration", "kl"))
            gap = ((metric - train_reconstruction) / max(abs(train_reconstruction), 1e-12))
            entry.update({"development_metric": metric, "improved": improved,
                          "train_reconstruction_metric": train_reconstruction,
                          "development_train_relative_gap": gap,
                          "overfitting_gap_flag": gap > 0.25})
            state = {
                "schema_version": "1.0", "condition": "B", "update": update,
                "recipe_sha256": recipe_hash, "dataset_sha256": dataset_hash,
                "early_stopping": early.__dict__, "backend": backend.checkpoint_state(),
                "rng": {"python": random.getstate(), "numpy": np.random.get_state(),
                        "torch": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all()},
            }
            atomic_torch_save(state, output_dir / "last.pt")
            if improved:
                atomic_torch_save(state, output_dir / "best.pt")
            if (update >= opt["minimum_optimizer_updates_before_early_stop"]
                    and early.non_improving >= select["early_stopping_patience_evaluations"]):
                stopped_early = True
                log.append(entry)
                break
        log.append(entry)
    best_path = output_dir / "best.pt"
    if not best_path.is_file():
        raise RuntimeError("No development checkpoint was selected")
    best = torch.load(best_path, map_location="cpu", weights_only=False)
    if best["recipe_sha256"] != recipe_hash or best["dataset_sha256"] != dataset_hash:
        raise ValueError("Best checkpoint provenance mismatch")
    backend.load_checkpoint_state(best["backend"])
    summary = {
        "training_started": True, "optimizer_updates": log[-1]["update"],
        "stopped_early": stopped_early, "best_update": early.best_update,
        "best_development_metric": early.best_metric, "microbatches_per_update": accumulation,
        "protected_test_items_seen": 0, "log": log,
    }
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
