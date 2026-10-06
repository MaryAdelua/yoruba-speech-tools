"""Evaluate a single captured interaction; see evaluation/voice_interactions/README.md."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from voice_eval.pipeline import evaluate, inspect_audio, load_case, write_report
from voice_eval.providers import OpenAIProvider, ProviderError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=ROOT / "evaluation/voice_interactions/oranges_001.json")
    parser.add_argument("--user-audio", type=Path)
    parser.add_argument("--assistant-audio", type=Path)
    parser.add_argument("--transcripts", type=Path, help="Explicit text-only mode: JSON with user and assistant strings")
    parser.add_argument("--replay", type=Path, help="Offline fixture replay only; does not run a judge or ASR")
    parser.add_argument("--judge-model", help="Required for live scoring; use a Responses Structured Outputs model")
    parser.add_argument("--transcription-model", default="gpt-4o-transcribe")
    parser.add_argument("--product", default="unspecified", help="Product, voice, version/mode, and capture date")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise ValueError("Output already exists; choose a new report filename")
        case = load_case(args.case)
        audio = {}
        if args.replay:
            if args.transcripts or args.user_audio or args.assistant_audio or args.judge_model:
                raise ValueError("Replay cannot be combined with live inputs")
            fixture = json.loads(args.replay.read_text(encoding="utf-8-sig"))
            user = {"text": fixture["user"], "source": "fixture"}
            assistant = {"text": fixture["assistant"], "source": "fixture"}
            judge = lambda payload: (fixture["judgment"], {"provider": "fixture_replay", "model": None})
            mode = "fixture_replay"
        else:
            if not args.judge_model:
                raise ValueError("Live scoring requires --judge-model and OPENAI_API_KEY")
            if args.transcripts:
                if args.user_audio or args.assistant_audio:
                    raise ValueError("Choose audio mode or transcripts mode, not both")
                transcripts = json.loads(args.transcripts.read_text(encoding="utf-8-sig"))
                if not all(isinstance(transcripts.get(k), str) for k in ("user", "assistant")):
                    raise ValueError("Transcripts JSON requires user and assistant strings")
                user = {"text": transcripts["user"], "source": "supplied_text_not_verified_audio"}
                assistant = {"text": transcripts["assistant"], "source": "supplied_text_not_verified_audio"}
                mode = "text_only"
            else:
                if not args.user_audio or not args.assistant_audio:
                    raise ValueError("Audio mode requires both --user-audio and --assistant-audio")
                audio = {"user": inspect_audio(args.user_audio), "assistant": inspect_audio(args.assistant_audio)}
                mode = "audio"
            provider = OpenAIProvider(args.judge_model, args.transcription_model)
            if mode == "audio":
                user = provider.transcribe(args.user_audio)
                assistant = provider.transcribe(args.assistant_audio)
            judge = provider.judge
        report = evaluate(case, user, assistant, judge, mode=mode, audio=audio, product=args.product)
        write_report(args.out, report)
        print(json.dumps({"status": report["status"], "report": str(args.out.resolve())}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ProviderError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
