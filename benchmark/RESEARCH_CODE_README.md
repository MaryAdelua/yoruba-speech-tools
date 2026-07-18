# Yoruba Voice Research

Research prototype for meaning-preserving Yoruba speech synthesis.

The initial contribution is a functional-load-weighted, tone-contrastive objective for an end-to-end Yoruba TTS model, together with a benchmark that measures whether lexical tone contrasts survive synthesis.

## Current contents

- `src/tone_parser.py`: Unicode-safe extraction of Yoruba vowel nuclei and H/M/L orthographic tone labels.
- `tests/test_tone_parser.py`: executable unit tests for marked Yoruba text.
- The technical research specification is in the user-facing `outputs` folder.

## Run the parser tests

```powershell
python -m unittest discover -s tests -v
```

The parser is an orthographic baseline. It does not yet model elision, assimilation, downstep, tonal coarticulation, or surface-tone realization.
