#!/usr/bin/env python3
"""Acquire and hash the frozen English MMS archive. This module never imports the trainer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPE = ROOT / "experiment_01/condition_c_recipe.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if root != target and root not in target.parents:
            raise ValueError(f"Unsafe archive member: {member.name}")
    archive.extractall(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    initialization = json.loads(RECIPE.read_text(encoding="utf-8"))["initialization"]
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    if not args.archive.is_file():
        temporary = args.archive.with_suffix(args.archive.suffix + ".partial")
        with urllib.request.urlopen(initialization["archive_url"]) as response, temporary.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        os.replace(temporary, args.archive)
    if args.archive.stat().st_size != initialization["expected_archive_bytes"]:
        raise ValueError("English MMS archive byte count does not match the frozen recipe")
    archive_sha = sha256_file(args.archive)
    args.extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive, "r:gz") as archive:
        safe_extract(archive, args.extract_dir)
    names = ("config.json", "vocab.txt", initialization["generator_checkpoint"],
             initialization["discriminator_checkpoint"])
    files = {}
    for name in names:
        candidates = list(args.extract_dir.rglob(name))
        if len(candidates) != 1:
            raise ValueError(f"Expected exactly one extracted {name}; found {len(candidates)}")
        files[name] = {"path": str(candidates[0]), "sha256": sha256_file(candidates[0]),
                       "bytes": candidates[0].stat().st_size}
    report = {
        "schema_version": "1.0", "purpose": "checkpoint_acquisition_only",
        "training_started": False, "optimizer_updates": 0,
        "archive_url": initialization["archive_url"], "archive_bytes": args.archive.stat().st_size,
        "archive_expected_bytes": initialization["expected_archive_bytes"],
        "archive_sha256": archive_sha, "files": files,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
