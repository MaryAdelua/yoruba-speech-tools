"""Analyze one mono audio file without modifying it."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from acoustic_analysis import analyze, write_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fmin", type=float, default=65)
    parser.add_argument("--fmax", type=float, default=500)
    parser.add_argument("--frame-length", type=int, default=2048)
    parser.add_argument("--hop-ms", type=float, default=10)
    args = parser.parse_args()
    try:
        report, frames = analyze(args.audio, fmin=args.fmin, fmax=args.fmax,
                                 frame_length=args.frame_length, hop_ms=args.hop_ms)
        paths = write_outputs(report, frames, args.output_dir)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Analysis failed: {exc}\n")
    print(json.dumps({"summary": report["summary"], "warnings": report["warnings"],
                      "outputs": {k: str(v) for k, v in paths.items()}}, indent=2))


if __name__ == "__main__":
    main()
