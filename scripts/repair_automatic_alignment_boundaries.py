"""Repair invalid automatic intervals while retaining the raw source and audit."""

from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from alignment_repair import interval_errors, repair_alignment  # noqa: E402

SOURCE = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl"
RAW = ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.raw.jsonl"
AUDIT = ROOT / "alignment/automatic/omnilingual_ctc_boundary_repair_audit.jsonl"
SUMMARY = ROOT / "alignment/automatic/omnilingual_ctc_boundary_repair_summary.json"


def main() -> None:
    if not RAW.exists():
        shutil.copy2(SOURCE, RAW)
    source_rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines() if line.strip()]
    repaired_rows, audits = [], []
    before_errors = 0
    for row in source_rows:
        before = interval_errors(row)
        before_errors += len(before)
        repaired, changes = repair_alignment(row)
        after = interval_errors(repaired)
        if after:
            raise RuntimeError(f"{row['prompt_id']} still invalid after repair: {after}")
        repaired_rows.append(repaired)
        audits.append({
            "schema_version": "0.1", "prompt_id": row["prompt_id"],
            "original_error_count": len(before), "changed_field_count": len(changes),
            "changes": changes, "automatic_only": True, "human_verification_required": True,
        })
    with SOURCE.open("w", encoding="utf-8", newline="\n") as handle:
        for row in repaired_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with AUDIT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in audits:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    changed_records = sum(bool(x["changes"]) for x in audits)
    changed_fields = sum(x["changed_field_count"] for x in audits)
    reasons = Counter(change["reason"] for item in audits for change in item["changes"])
    levels = Counter(change["level"] for item in audits for change in item["changes"])
    SUMMARY.write_text(json.dumps({
        "schema_version": "0.1", "record_count": len(repaired_rows),
        "records_with_repairs": changed_records, "original_validation_error_count": before_errors,
        "changed_field_count": changed_fields, "remaining_validation_error_count": 0,
        "repair_actions_by_reason": dict(sorted(reasons.items())),
        "repair_actions_by_level": dict(sorted(levels.items())),
        "repair_policy": "clamp out-of-range endpoints; interpolate missing intervals; split only overlaps at their midpoint",
        "raw_source_preserved": str(RAW.relative_to(ROOT)).replace("\\", "/"),
        "human_verification_required": True,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"records={len(repaired_rows)} repaired_records={changed_records} changed_fields={changed_fields} remaining_errors=0")


if __name__ == "__main__":
    main()
