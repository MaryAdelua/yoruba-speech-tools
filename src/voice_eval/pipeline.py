"""One interaction to one auditable JSON report, preserving original recordings."""

import hashlib
import json
import math
import struct
import unicodedata
import wave
from datetime import datetime, timezone
from pathlib import Path

from yoruba_orthographic_units import word_spans
from . import VERSION
from .rubric import DIMENSIONS, RUBRIC, RUBRIC_VERSION, validate_judgment


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_case(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if value.get("schema_version") != "0.1" or value.get("expected_language") != "yo":
        raise ValueError("Case must have schema_version 0.1 and expected_language yo")
    for field in ("case_id", "reference_user_text", "expected_intent"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"Case requires {field}")
    criteria = value.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(c, str) and c.strip() for c in criteria):
        raise ValueError("Case requires nonempty acceptance_criteria")
    if type(value.get("reference_reviewed")) is not bool:
        raise ValueError("Case requires reference_reviewed boolean")
    if value.get("task_type") != "conversational_reply":
        raise ValueError("V0.1 evaluates conversational replies only")
    return value


def inspect_audio(path):
    path = Path(path)
    if path.suffix.lower() not in {".wav", ".m4a", ".mp3"}:
        raise ValueError("Use WAV, M4A, or MP3 for V0.1")
    size = path.stat().st_size
    if not 0 < size < 25_000_000:
        raise ValueError("Each recording must be nonempty and smaller than 25 MB")
    result = {"filename": path.name, "bytes": size, "sha256": digest(path.read_bytes()),
              "technical_checks": "not_decoded_compressed_audio", "flags": []}
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as audio:
                channels, width, rate, frames = audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()
                raw = audio.readframes(frames)
        except (wave.Error, EOFError):
            raise ValueError("WAV must be readable uncompressed PCM") from None
        if width != 2 or channels not in {1, 2} or rate <= 0 or frames <= 0 or len(raw) != frames * channels * width:
            raise ValueError("WAV must contain complete nonempty 16-bit PCM, mono or stereo")
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        rms = math.sqrt(sum(x*x for x in samples) / len(samples)) / 32768
        clipping = sum(abs(x) >= 32760 for x in samples) / len(samples) * 100
        result.update(technical_checks="pcm_checked", duration_s=frames/rate,
                      sample_rate_hz=rate, channels=channels, rms_dbfs=20*math.log10(max(rms, 1e-12)),
                      clipped_sample_pct=clipping)
        if rms == 0:
            raise ValueError("WAV contains digital silence; no interaction to score")
        if result["rms_dbfs"] < -45:
            result["flags"].append("very_quiet")
        if clipping > 0.1:
            result["flags"].append("clipping")
    return result


def evaluate(case, user, assistant, judge, *, mode, audio=None, product=None):
    user = dict(user, raw_text=user["text"], text=unicodedata.normalize("NFC", user["text"]).strip())
    assistant = dict(assistant, raw_text=assistant["text"], text=unicodedata.normalize("NFC", assistant["text"]).strip())
    report = {
        "schema_version": "0.1", "evaluator_version": VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode, "case_id": case["case_id"], "case": case,
        "case_sha256": digest(json.dumps(case, sort_keys=True, ensure_ascii=False).encode()),
        "product": product or "unspecified", "audio": audio or {},
        "transcripts": {"user": user, "assistant": assistant},
        "rubric_version": RUBRIC_VERSION, "rubric_sha256": digest(RUBRIC.encode()),
        "validation_status": "not_human_validated",
        "not_scored": {
            "pronunciation": "Not implemented; transcript text cannot establish pronunciation or tones.",
            "naturalness": "Deferred pending native-speaker calibration.",
            "speech_understanding": "Internal product recognition is unobserved; request match only checks evaluator evidence.",
            "multi_turn_understanding": "Single-turn V0.1.",
        },
        "limitations": ["ASR errors may affect scores; compare transcripts with the recordings.",
                        "Automated scores are provisional, not validated Yoruba capability measurements.",
                        "No overall score; the three dimensions are independent."],
        "diagnostics": {"assistant_word_count": len(word_spans(assistant["text"]))},
    }
    if not user["text"] or not assistant["text"]:
        report.update(status="not_evaluable", judge=None, request_match="uncertain",
                      request_match_reason="Empty input or response transcript", uncertainties=["No text evidence"],
                      dimensions={key: {"status": "not_evaluable", "score": None, "evidence": "",
                                        "reason": "Empty transcript is not proof of product failure"} for key in DIMENSIONS})
        return report
    payload = {"case": case, "observed_user_transcript": user["text"], "assistant_transcript": assistant["text"]}
    result, provenance = judge(payload)
    result = validate_judgment(result, assistant["text"])
    needs_review = (not case["reference_reviewed"] or result["request_match"] != "matches"
                    or bool(result["uncertainties"]) or any(x["flags"] for x in (audio or {}).values())
                    or any(x["status"] != "scored" for x in result["dimensions"].values()))
    report.update(result, judge=provenance, status="needs_review" if needs_review else "provisional")
    if mode == "fixture_replay":
        report["status"] = "fixture_replay_not_a_model_evaluation"
    return report


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects earlier runs and accidental input/output collisions.
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
