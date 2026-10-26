# Yoruba Voice Research

Research prototype for meaning-preserving Yoruba speech synthesis. This guide introduces the initial parser and research proposal; see the [project overview](../README.md) for the two connected research phases and the [19 July 2026 pause handoff](../PAUSE_HANDOFF.md) for the later experiment status.

The initial proposal investigates a functional-load-weighted, tone-contrastive objective for an end-to-end Yoruba TTS model, together with a benchmark of lexical-tone preservation. It is a research objective, not a demonstrated adaptation result.

## Code and specification

- [`src/tone_parser.py`](../src/tone_parser.py): Unicode-safe extraction of Yoruba vowel nuclei and H/M/L orthographic tone labels.
- [`tests/test_tone_parser.py`](../tests/test_tone_parser.py): executable unit tests for marked Yoruba text.
- [Technical research specification](../artifacts/yoruba_voice_research_specification.md): initial proposal dated 18 July 2026. Its planned conditions and next steps are historical; consult the pause handoff for the later frozen experiment and completed technical validation.
- [Benchmark guide](README.md): metadata, processing details and private-audio limitations.

## Run the parser tests

From the repository root, using Python 3.10 or newer:

```bash
python3 -m unittest discover -s tests -p 'test_tone_parser.py' -v
```

On Windows, use `py -3` in place of `python3`. This command runs only the parser tests; it does not load audio, model weights or start training.

The parser is an orthographic baseline. It does not yet model elision, assimilation, downstep, tonal coarticulation, or surface-tone realization.
