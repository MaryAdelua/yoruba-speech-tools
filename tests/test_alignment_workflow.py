import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_progress_tracks_completed_review_set():
    progress = json.loads((ROOT / "alignment/review/review_progress.json").read_text(encoding="utf-8"))
    assert progress["total"] == 30
    assert progress["imported_verified"] == 29
    assert len(progress["verified_prompt_ids"]) == 29
    assert "YT0001" in progress["verified_prompt_ids"]
    assert "YT0022" not in progress["verified_prompt_ids"]
    assert progress["flagged_prompt_ids"] == ["YT0022"]
    assert progress["remaining"] == 0
    assert progress["final_dataset_status"] == "ready"


def test_finalizer_accepts_complete_manual_layer_with_exclusion():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/finalize_verified_alignments.py")],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "finalized=29" in result.stderr + result.stdout
