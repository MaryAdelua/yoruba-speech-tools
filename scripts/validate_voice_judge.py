"""Live judge smoke validation using three responses to the same single case.

Runs real scoring calls. A pass is preliminary evidence only, not language-wide
reliability. Requires OPENAI_API_KEY; never runs as part of the offline test suite.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from voice_eval.pipeline import evaluate, load_case, write_report
from voice_eval.providers import OpenAIProvider, ProviderError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise ValueError("Output already exists; choose a new filename")
        root = ROOT / "evaluation/voice_interactions"
        case = load_case(root / "oranges_001.json")
        variants = json.loads((root / "response_variants.json").read_text(encoding="utf-8"))["variants"]
        provider = OpenAIProvider(args.judge_model)
        results = []
        for variant in variants:
            report = evaluate(case, {"text": case["reference_user_text"], "source": "draft_reference"},
                              {"text": variant["assistant"], "source": "draft_response_variant"},
                              provider.judge, mode="text_only")
            checks = {}
            for key, (low, high) in variant["expected_ranges"].items():
                score = report["dimensions"][key]["score"]
                checks[key] = type(score) is int and low <= score <= high
            checks["request_match"] = report["request_match"] == "matches"
            results.append({"variant": variant["id"], "checks": checks, "report": report})
        passed = all(all(row["checks"].values()) for row in results)
        write_report(args.out, {"status": "preliminary_pass" if passed else "needs_investigation",
                               "limitations": "Three draft response variants, one case, one pass. Not a reliability estimate.",
                               "results": results})
        print(json.dumps({"passed": passed, "report": str(args.out.resolve())}))
        return 0 if passed else 1
    except (ValueError, OSError, ProviderError) as exc:
        print(f"Judge validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
