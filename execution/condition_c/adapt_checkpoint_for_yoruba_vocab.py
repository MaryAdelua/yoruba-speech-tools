#!/usr/bin/env python3
"""Adapt the English MMS/VITS generator checkpoint to Yoruba's text vocabulary.

The English and Yoruba MMS checkpoints share one uniform VITS architecture
(same inter/hidden/filter channels, same acoustic configuration) -- only the
text vocabulary differs (38 English symbols vs 43 Yoruba symbols). The single
vocab-sized tensor in the whole generator is the text-encoder's embedding
table (`enc_p.emb.weight`, shape [n_vocab, hidden_channels]); every other
generator tensor, and the entire discriminator, is architecture-only and
transfers unmodified.

This script writes a new generator checkpoint with every tensor copied
byte-for-byte from the English checkpoint except that one embedding, which is
reinitialized at the Yoruba vocab size using VITS's own embedding init scheme
(normal_(0, hidden_channels ** -0.5)). It also copies the discriminator
checkpoint through unmodified and writes a Yoruba-vocab config/vocab pair, so
the output directory is a drop-in --model-dir for the existing Condition B/C
training and evaluation entrypoints -- no changes needed in that code.

Never imports the trainer and never touches the private VITS/fairseq repos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import torch


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_vocab(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english-model-dir", type=Path, required=True,
                         help="Extracted eng.tar.gz directory (config.json, vocab.txt, G_100000.pth, D_100000.pth)")
    parser.add_argument("--yoruba-vocab", type=Path, required=True,
                         help="Yoruba vocab.txt (the same one Condition B trains against)")
    parser.add_argument("--output-dir", type=Path, required=True,
                         help="Destination directory usable as --model-dir for Condition C training/evaluation")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    config_path = args.english_model_dir / "config.json"
    english_vocab_path = args.english_model_dir / "vocab.txt"
    generator_path = args.english_model_dir / "G_100000.pth"
    discriminator_path = args.english_model_dir / "D_100000.pth"
    for path in (config_path, english_vocab_path, generator_path, discriminator_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    hidden_channels = config["model"]["hidden_channels"]
    english_vocab = load_vocab(english_vocab_path)
    yoruba_vocab = load_vocab(args.yoruba_vocab)
    if len(english_vocab) != 38:
        raise ValueError(f"Expected the English MMS checkpoint to have 38 symbols; found {len(english_vocab)}")
    if len(yoruba_vocab) != 43:
        raise ValueError(f"Expected the Yoruba vocabulary to have 43 symbols; found {len(yoruba_vocab)}")

    checkpoint = torch.load(generator_path, map_location="cpu", weights_only=False)
    state_dict = checkpoint["model"]

    # Locate the vocab-sized tensor by shape rather than assuming the exact key
    # name is stable across VITS forks, but assert it resolves to exactly the
    # one tensor we expect -- fail loudly on any surprise rather than guessing.
    candidates = [
        key for key, tensor in state_dict.items()
        if tensor.dim() == 2 and tensor.shape[0] == len(english_vocab)
    ]
    if candidates != ["enc_p.emb.weight"]:
        raise RuntimeError(
            f"Expected exactly one vocab-sized tensor named 'enc_p.emb.weight'; found {candidates}"
        )

    original_embedding = state_dict["enc_p.emb.weight"]
    new_embedding = torch.empty(len(yoruba_vocab), hidden_channels, dtype=original_embedding.dtype)
    torch.nn.init.normal_(new_embedding, 0.0, hidden_channels ** -0.5)

    adapted_state_dict = dict(state_dict)
    adapted_state_dict["enc_p.emb.weight"] = new_embedding
    unchanged_keys = [key for key in state_dict if key != "enc_p.emb.weight"]
    for key in unchanged_keys:
        if not torch.equal(adapted_state_dict[key], state_dict[key]):
            raise RuntimeError(f"Unexpected mutation of transferred tensor {key!r}")

    adapted_checkpoint = dict(checkpoint)
    adapted_checkpoint["model"] = adapted_state_dict

    args.output_dir.mkdir(parents=True, exist_ok=True)
    adapted_generator_path = args.output_dir / "G_100000.pth"
    adapted_discriminator_path = args.output_dir / "D_100000.pth"
    adapted_config_path = args.output_dir / "config.json"
    adapted_vocab_path = args.output_dir / "vocab.txt"

    torch.save(adapted_checkpoint, adapted_generator_path)
    shutil.copyfile(discriminator_path, adapted_discriminator_path)
    shutil.copyfile(config_path, adapted_config_path)
    shutil.copyfile(args.yoruba_vocab, adapted_vocab_path)

    report = {
        "schema_version": "1.0", "purpose": "vocab_adaptation_only",
        "training_started": False, "optimizer_updates": 0,
        "source": {
            "archive_language": "eng", "vocab_size": len(english_vocab),
            "generator_sha256": sha256_file(generator_path),
            "discriminator_sha256": sha256_file(discriminator_path),
        },
        "target": {
            "vocab_size": len(yoruba_vocab), "yoruba_vocab_sha256": sha256_file(args.yoruba_vocab),
        },
        "reinitialized_tensors": ["enc_p.emb.weight"],
        "reinitialized_shape": [len(yoruba_vocab), hidden_channels],
        "reinitialization_scheme": "normal_(0.0, hidden_channels ** -0.5), matching VITS's own TextEncoder init",
        "transferred_tensor_count": len(unchanged_keys),
        "transferred_tensors_verified_unchanged": True,
        "discriminator_transferred_unmodified": True,
        "output": {
            "generator_sha256": sha256_file(adapted_generator_path),
            "discriminator_sha256": sha256_file(adapted_discriminator_path),
            "config_sha256": sha256_file(adapted_config_path),
            "vocab_sha256": sha256_file(adapted_vocab_path),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
