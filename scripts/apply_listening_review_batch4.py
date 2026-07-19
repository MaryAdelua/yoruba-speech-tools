import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "yoruba_alignment_v0_4"
TARGET = ROOT / "work" / "yoruba_alignment_v0_5"
QUEUE = TARGET / "listening_verification_queue.csv"
SUMMARY = TARGET / "LISTENING_VERIFICATION_STATUS.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_alignment_v0_5.zip"
APPROVED = {"0145", "0146", "0147", "0148", "0149", "0150", "0151", "0152", "0161", "0162"}

if TARGET.exists() or ZIP_OUT.exists():
    raise RuntimeError("Alignment v0.5 already exists")
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
if len(verified) != 30:
    raise RuntimeError(f"Expected 30 verified rows, found {len(verified)}")

SUMMARY.write_text(
    """# Listening verification status

- Verified by the fluent speaker: **30 of 120**
- Pending: **90 of 120**
- Verified transcript mismatches: **none**
- Verified unnatural pronunciations: **none**
- Corrections required: **none**
- Re-recordings required: **none**

The fourth review batch covered ten affirmation/negation, question/statement, focus, and `kọ́/kọ` contrast recordings. All ten matched their transcripts and sounded natural.
""",
    encoding="utf-8",
)

shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", TARGET)
print(ZIP_OUT)
