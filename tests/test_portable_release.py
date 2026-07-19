import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_builder_and_validator(tmp_path):
    output = ROOT / "release_candidates" / "pytest-portable-release"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_portable_release.py"), "--output", str(output), "--replace"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    validation = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_portable_release.py"), str(output)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert validation.returncode == 0, validation.stderr + validation.stdout
    manifest = json.loads((output / "release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["record_count"] == 29
    assert manifest["excluded_recordings"] == ["YT0022"]
    assert len(list((output / "audio").glob("*.wav"))) == 29
