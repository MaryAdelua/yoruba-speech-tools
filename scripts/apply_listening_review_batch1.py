import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work" / "yoruba_alignment_v0_1"
TARGET = ROOT / "work" / "yoruba_alignment_v0_2"
QUEUE = TARGET / "listening_verification_queue.csv"
SUMMARY = TARGET / "LISTENING_VERIFICATION_STATUS.md"
ZIP_OUT = ROOT / "outputs" / "yoruba_alignment_v0_2.zip"

APPROVED = {"0122", "0101", "0102", "0103", "0104"}

if TARGET.exists():
    raise RuntimeError(f"Target already exists: {TARGET}")
if ZIP_OUT.exists():
    raise RuntimeError(f"Output already exists: {ZIP_OUT}")

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
    raise RuntimeError(f"Could not find all reviewed IDs: {sorted(APPROVED - found)}")

with QUEUE.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

SUMMARY.write_text(
    """# Listening verification status

## Completed

The fluent speaker reviewed recordings `0122`, `0101`, `0102`, `0103`, and `0104`.

- Transcript matched audio: **yes for all five**
- All words spoken: **yes for all five**
- Pronunciation natural: **yes for all five**
- Corrections required: **none**
- Re-recordings required: **none**

## Progress

- Verified: **5 of 120**
- Pending: **115 of 120**

Recording `0122` had previously been prioritized because of low automatic voiced-frame coverage. Speaker verification confirms that it matches the transcript and sounds natural, so it is accepted without re-recording.
""",
    encoding="utf-8",
)

shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", TARGET)
print(ZIP_OUT)
