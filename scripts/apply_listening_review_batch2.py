import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "yoruba_alignment_v0_2"
TARGET = ROOT / "work" / "yoruba_alignment_v0_3"
QUEUE = TARGET / "listening_verification_queue.csv"
SUMMARY = TARGET / "LISTENING_VERIFICATION_STATUS.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_alignment_v0_3.zip"
APPROVED = {"0105", "0106", "0137", "0138", "0139"}

if TARGET.exists() or ZIP_OUT.exists():
    raise RuntimeError("Alignment v0.3 already exists")
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
SUMMARY.write_text(
    """# Listening verification status

## Completed

The fluent speaker has verified recordings `0122`, `0101`-`0106`, and `0137`-`0139`.

- Transcript matched audio: **yes for all ten**
- All words spoken: **yes for all ten**
- Pronunciation natural: **yes for all ten**
- Corrections required: **none**
- Re-recordings required: **none**

## Progress

- Verified: **10 of 120**
- Pending: **110 of 120**
""",
    encoding="utf-8",
)

if len(verified) != 10:
    raise RuntimeError(f"Expected 10 verified rows, found {len(verified)}")
shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", TARGET)
print(ZIP_OUT)
