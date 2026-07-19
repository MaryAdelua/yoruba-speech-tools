"""Build the matched tone-aware prompting intervention for Pilot 3."""

from __future__ import annotations

import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pronunciation_guide import concise_guided_prompt, guided_prompt, word_tone_plan


SOURCE = ROOT / "evaluation" / "chatgpt_voice_pilot_03.csv"
OUTPUT_CSV = ROOT / "intervention" / "tone_aware_pilot_03.csv"
OUTPUT_MD = ROOT / "intervention" / "TONE_AWARE_PILOT_03_RECORDING.md"
CONCISE_CSV = ROOT / "intervention" / "tone_aware_pilot_03_concise.csv"
CONCISE_MD = ROOT / "intervention" / "TONE_AWARE_PILOT_03_CONCISE_RECORDING.md"


FOCUS = {
    "0161": ("kọ́", "H", "built"),
    "0162": ("kọ", "M", "wrote"),
    "0163": ("kọ̀", "L", "refused"),
    "0164": ("Yàrá", "L-H", "room"),
    "0165": ("yára", "H-M", "quickly"),
    "0169": ("fọ", "M", "wash"),
    "0170": ("fọ́", "H", "break"),
    "0191": ("Ìlú", "L-H", "town"),
    "0192": ("ìlù", "L-L", "drum"),
    "0144": ("ẹ̀kọ́", "L-H", "school/learning"),
}


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    output_rows = []
    for row in rows:
        focus_word, focus_tones, focus_meaning = FOCUS[row["prompt_id"]]
        output_rows.append(
            {
                **row,
                "condition": "tone_aware_guidance",
                "word_tone_plan": word_tone_plan(row["yoruba"]),
                "focus_word": focus_word,
                "focus_tones": focus_tones,
                "focus_meaning": focus_meaning,
                "guided_prompt": guided_prompt(
                    row["yoruba"], focus_word, focus_tones, focus_meaning
                ),
                "concise_guided_prompt": concise_guided_prompt(
                    row["yoruba"], focus_word, focus_tones, focus_meaning
                ),
            }
        )

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    lines = [
        "# Tone-aware Pilot 3 intervention — ChatGPT Voice",
        "",
        "## Experimental purpose",
        "",
        "This is the guided condition in a matched A/B test. Use the same ChatGPT voice used for the ordinary-text Pilot 3 baseline. Do not alter the prompts.",
        "",
        "## Recording procedure",
        "",
        "1. Use the same ChatGPT voice and mode as the baseline.",
        "2. Start one continuous screen recording with system audio.",
        "3. Paste each complete guided prompt separately.",
        "4. Wait until the voice finishes, then wait silently for five seconds.",
        "5. Do not speak, correct errors, or retry outputs.",
        "6. Upload the resulting MP4 to Codex.",
        "",
        "## Guided prompts",
        "",
    ]
    for row in output_rows:
        lines.extend(
            [
                f"### Prompt {row['order']} — {row['prompt_id']}",
                "",
                row["guided_prompt"],
                "",
            ]
        )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    concise_fields = [
        "order",
        "prompt_id",
        "yoruba",
        "english_meaning",
        "contrast_group_id",
        "research_purpose",
        "focus_word",
        "focus_tones",
        "focus_meaning",
        "concise_guided_prompt",
    ]
    with CONCISE_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=concise_fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in concise_fields} for row in output_rows)

    concise_lines = [
        "# Concise tone-aware Pilot 3 intervention — ChatGPT Voice",
        "",
        "## Why this version is shorter",
        "",
        "The first sentence-wide guide caused truncation. This version changes only one variable: it gives a short tone-and-meaning cue for the sentence’s meaning-critical word. The requested spoken sentence is unchanged.",
        "",
        "## Recording procedure",
        "",
        "1. Use the same ChatGPT voice and mode as the baseline.",
        "2. Start one continuous screen recording with system audio.",
        "3. Paste each complete prompt separately.",
        "4. Let the response finish, then wait silently for five seconds.",
        "5. Do not speak, correct, or retry an output.",
        "6. Upload the resulting MP4 to Codex.",
        "",
        "## Concise guided prompts",
        "",
    ]
    for row in output_rows:
        concise_lines.extend(
            [
                f"### Prompt {row['order']} — {row['prompt_id']}",
                "",
                row["concise_guided_prompt"],
                "",
            ]
        )
    CONCISE_MD.write_text("\n".join(concise_lines), encoding="utf-8")

    print(f"items={len(output_rows)}")
    print(f"csv={OUTPUT_CSV}")
    print(f"recording_sheet={OUTPUT_MD}")
    print(f"concise_csv={CONCISE_CSV}")
    print(f"concise_recording_sheet={CONCISE_MD}")


if __name__ == "__main__":
    main()
