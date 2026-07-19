import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "yoruba_alignment_v0_13"
TARGET = ROOT / "work" / "yoruba_alignment_v0_14"
QUEUE = TARGET / "listening_verification_queue.csv"
SUMMARY = TARGET / "LISTENING_VERIFICATION_STATUS.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_alignment_v0_14_complete.zip"
APPROVED = {"0209", "0210", "0213", "0214", "0215", "0216", "0217", "0218", "0219", "0220"}

if TARGET.exists() or ZIP_OUT.exists():
    raise RuntimeError("Completed alignment v0.14 already exists")
shutil.copytree(SOURCE, TARGET)

with QUEUE.open("r", encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

found = set()
for row in rows:
    if row["prompt_id"] in APPROVED:
        row["transcript_matches_audio"] = "yes"
        row["all_words_spoken"] = "yes"
        row["pronunciation_natural"] = "yes"
        row["notes_or_correction"] = "none"
        row["review_status"] = "verified_by_speaker"
        found.add(row["prompt_id"])
if found != APPROVED:
    raise RuntimeError(f"Missing reviewed IDs: {sorted(APPROVED - found)}")

with QUEUE.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

verified = [row for row in rows if row["review_status"] == "verified_by_speaker"]
pending = [row for row in rows if row["review_status"] != "verified_by_speaker"]
if len(verified) != 120 or pending:
    raise RuntimeError(f"Expected 120 verified and 0 pending; found {len(verified)} verified and {len(pending)} pending")

SUMMARY.write_text(
    """# Listening verification status

- Verified by the fluent speaker: **120 of 120**
- Pending: **0 of 120**
- Verified transcript mismatches: **none**
- Verified unnatural pronunciations: **none**
- Corrections required: **1 (`0205`: trim approximately the final 1 second to remove trailing noise)**
- Re-recordings required: **none**

Human listening verification is complete. Every recording matched its transcript, contained all expected words, and sounded natural to the fluent Yoruba speaker. Recording `0205` is linguistically approved but requires a minor end trim to remove trailing noise; it does not need to be recorded again.
""",
    encoding="utf-8",
)

shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", TARGET)
print(ZIP_OUT)
