# Portable release candidate

The portable package is generated locally with:

```powershell
python scripts/build_portable_release.py --replace
python scripts/validate_portable_release.py release_candidates/yoruba-pronunciation-resource-v0.1-rc1
```

It contains 29 approved recordings, portable relative audio paths, SHA-256 audio checksums, verified word and syllable boundaries, the corrected YT0013 transcript, and the explicit YT0022 missing-audio exclusion.

The generated directory is intentionally ignored by Git because it contains participant audio. Its release status is `private_release_candidate_not_for_redistribution` until the signed speaker release, explicit dataset license, privacy/misuse review, and persistent release identifier are complete.

The validator uses only the Python standard library. It checks package checksums, WAV format, duration agreement, NFC Yoruba text, unique identifiers, exclusions, and all word/syllable timestamp constraints. This allows speech-model teams to verify the resource before writing a model-specific adapter.
