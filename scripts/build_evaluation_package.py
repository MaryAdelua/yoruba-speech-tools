import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmark" / "benchmark_manifest.csv"
F0_SUMMARY = ROOT / "tone-analysis" / "utterance_f0_summary.csv"
EVALUATION = ROOT / "evaluation"

with BENCHMARK.open("r", encoding="utf-8-sig", newline="") as handle:
    benchmark_rows = list(csv.DictReader(handle))
with F0_SUMMARY.open("r", encoding="utf-8-sig", newline="") as handle:
    f0_by_id = {row["prompt_id"]: row for row in csv.DictReader(handle)}

items_fields = [
    "prompt_id",
    "yoruba",
    "english_meaning",
    "research_purpose",
    "orthographic_tone_sequence",
    "contrast_group_ids",
    "is_controlled_contrast",
]
items = []
targets = []
for row in benchmark_rows:
    f0 = f0_by_id.get(row["prompt_id"], {})
    items.append(
        {
            "prompt_id": row["prompt_id"],
            "yoruba": row["yoruba"],
            "english_meaning": row["english_meaning"],
            "research_purpose": row["research_purpose"],
            "orthographic_tone_sequence": row["orthographic_tone_sequence"],
            "contrast_group_ids": row["contrast_group_ids"],
            "is_controlled_contrast": "yes" if row["contrast_group_ids"] else "no",
        }
    )
    targets.append(
        {
            "prompt_id": row["prompt_id"],
            "reference_duration_s": row["processed_duration_s"],
            "reference_f0_median_hz": f0.get("f0_median_hz", ""),
            "reference_f0_range_st": f0.get("f0_range_p90_p10_st", ""),
            "reference_voiced_ratio": f0.get("voiced_ratio", ""),
            "orthographic_tone_sequence": row["orthographic_tone_sequence"],
            "contrast_group_ids": row["contrast_group_ids"],
            "reference_status": row["transcript_alignment_status"],
        }
    )

with (EVALUATION / "evaluation_items.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=items_fields)
    writer.writeheader()
    writer.writerows(items)

with (EVALUATION / "reference_acoustic_targets.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(targets[0].keys()))
    writer.writeheader()
    writer.writerows(targets)

system_fields = ["system_id", "provider", "model", "voice", "generation_date", "settings", "notes"]
with (EVALUATION / "system_manifest_template.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=system_fields)
    writer.writeheader()
    writer.writerow({field: "" for field in system_fields})

human_fields = [
    "system_id",
    "prompt_id",
    "audio_filename",
    "transcript_match",
    "pronunciation_natural",
    "tone_correct",
    "meaning_recovered",
    "naturalness_1_5",
    "notes",
]
with (EVALUATION / "human_rating_template.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=human_fields)
    writer.writeheader()
    for row in items:
        writer.writerow({"prompt_id": row["prompt_id"], "audio_filename": f"{row['prompt_id']}.wav"})

print(f"evaluation_items={len(items)}")
print(f"controlled_contrast_items={sum(row['is_controlled_contrast'] == 'yes' for row in items)}")
