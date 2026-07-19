"""Offline validation for a portable Yoruba pronunciation release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
import wave
from pathlib import Path, PurePosixPath


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.package.resolve()
    errors: list[str] = []

    manifest_path = root / "release_manifest.json"
    data_path = root / "data/utterances.jsonl"
    checksum_path = root / "CHECKSUMS.sha256"
    for required in (manifest_path, data_path, checksum_path, root / "README.md"):
        if not required.is_file():
            fail(errors, f"missing required file: {required.relative_to(root)}")
    if errors:
        raise SystemExit("INVALID\n" + "\n".join(errors))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in data_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if manifest.get("release_status") != "private_release_candidate_not_for_redistribution":
        fail(errors, "release status is not the required private-candidate status")
    if len(rows) != manifest.get("record_count"):
        fail(errors, "record count does not match release manifest")
    ids = [row.get("prompt_id") for row in rows]
    if len(ids) != len(set(ids)):
        fail(errors, "duplicate prompt_id values")
    if "YT0022" in ids or manifest.get("excluded_recordings") != ["YT0022"]:
        fail(errors, "YT0022 exclusion is not preserved")

    for row in rows:
        prompt_id = row.get("prompt_id", "unknown")
        audio_rel = row.get("audio_path", "")
        pure = PurePosixPath(audio_rel)
        if pure.is_absolute() or ".." in pure.parts or not audio_rel.startswith("audio/"):
            fail(errors, f"{prompt_id}: non-portable audio path")
            continue
        audio_path = root / Path(*pure.parts)
        if not audio_path.is_file():
            fail(errors, f"{prompt_id}: audio file missing")
            continue
        if sha256(audio_path) != row.get("audio", {}).get("sha256"):
            fail(errors, f"{prompt_id}: audio checksum mismatch")
        with wave.open(str(audio_path), "rb") as handle:
            if (handle.getframerate(), handle.getnchannels(), handle.getsampwidth()) != (24000, 1, 2):
                fail(errors, f"{prompt_id}: WAV must be mono 24 kHz 16-bit PCM")
            duration = handle.getnframes() / handle.getframerate()
        if abs(duration - float(row.get("duration_s", -1))) > 0.02:
            fail(errors, f"{prompt_id}: duration mismatch")
        text = row.get("text_nfc", "")
        if not text or text != unicodedata.normalize("NFC", text):
            fail(errors, f"{prompt_id}: transcript is empty or not NFC")
        previous_word_end = 0.0
        for word in row.get("words", []):
            start, end = float(word["start_s"]), float(word["end_s"])
            if start < previous_word_end - 0.001 or end <= start or end > duration + 0.001:
                fail(errors, f"{prompt_id}: invalid word boundary for {word.get('text')}")
            previous_word_end = end
            previous_syllable_end = start
            for syllable in word.get("syllables", []):
                syllable_start, syllable_end = float(syllable["start_s"]), float(syllable["end_s"])
                if syllable_start < previous_syllable_end - 0.001 or syllable_end <= syllable_start or syllable_end > end + 0.001:
                    fail(errors, f"{prompt_id}: invalid syllable boundary for {syllable.get('orthographic_form')}")
                previous_syllable_end = syllable_end

    for line in checksum_path.read_text(encoding="ascii").splitlines():
        expected, relative = line.split("  ", 1)
        target = root / Path(*PurePosixPath(relative).parts)
        if not target.is_file() or sha256(target) != expected:
            fail(errors, f"package checksum mismatch: {relative}")

    if errors:
        raise SystemExit("INVALID\n" + "\n".join(errors))
    print(f"VALID records={len(rows)} excluded=YT0022 word_coverage=100% syllable_coverage=100%")


if __name__ == "__main__":
    main()
