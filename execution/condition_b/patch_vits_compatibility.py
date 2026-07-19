"""Apply narrowly scoped PyTorch 2.1/librosa compatibility fixes to pinned VITS."""

from pathlib import Path
import re
import sys


def replace_exact(path: Path, old: str, new: str, expected: int) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} occurrences, found {count}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    root = Path(sys.argv[1])
    mel = root / "mel_processing.py"
    transforms = root / "transforms.py"

    replace_exact(
        mel,
        "onesided=True)",
        "onesided=True, return_complex=False)",
        2,
    )
    replace_exact(
        mel,
        "librosa_mel_fn(sampling_rate, n_fft, num_mels, fmin, fmax)",
        "librosa_mel_fn(sr=sampling_rate, n_fft=n_fft, n_mels=num_mels, "
        "fmin=fmin, fmax=fmax)",
        2,
    )
    mel_text = mel.read_text(encoding="utf-8")
    pattern = r"(?m)^(?P<indent>[\t ]+)global mel_basis, hann_window$"
    matches = list(re.finditer(pattern, mel_text))
    if len(matches) != 1:
        raise RuntimeError(f"{mel}: expected one mel_spectrogram global line, found {len(matches)}")
    match = matches[0]
    indent = match.group("indent")
    replacement = match.group(0) + "\n" + indent + "y = y.float()"
    mel.write_text(mel_text[:match.start()] + replacement + mel_text[match.end():], encoding="utf-8")
    replace_exact(
        transforms,
        "torch.cumsum(widths, dim=-1)",
        "torch.cumsum(widths.cpu(), dim=-1).to(widths.device)",
        1,
    )
    replace_exact(
        transforms,
        "torch.cumsum(heights, dim=-1)",
        "torch.cumsum(heights.cpu(), dim=-1).to(heights.device)",
        1,
    )


if __name__ == "__main__":
    main()
