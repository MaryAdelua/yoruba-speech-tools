# SLR86 bounded pilot import

This pilot imports source-preserved natural read speech, not verified tone targets.
No training, tone restoration, speech scores, or AI recording generation occurs.

## Source and acquisition

Official catalog: https://www.openslr.org/86/
Official EU mirror: https://openslr.trmal.net/resources/86/
License: CC BY-SA 4.0. The original LICENSE, attribution, annotation legend,
transcript indexes, hashes, archive catalogs and HTTP provenance are retained in
`work/slr86/metadata/`. A durable source snapshot is in `data/sources/slr86/`.
Credit Google Inc. and Gutkin et al., *Developing an Open-Source Corpus of Yoruba
Speech*, Interspeech 2020, DOI 10.21437/Interspeech.2020-1096. Preserve attribution,
license and modification notices; shared adaptations require compatible share-alike terms.

The release contains female and male ZIP archives with root-level WAV files,
LICENSE and line_index.tsv. File IDs carry the anonymized speaker prefix, e.g.
`yof_01208`; no external identity inference is made. Gender groups are source labels.
Each ZIP inventory is checked against its official transcript index, and its
internal index and license are compared against the separately published files.

Full archive sizes: female 462,033,045 bytes; male 445,032,517 bytes.
The mirror supports HTTP 206 byte ranges. Python zipfile reads the central directory
and only selected compressed WAV members. Every response must match the requested
Content-Range; a full response is rejected before reading its body. There is no
full-archive fallback. Each read and each archive session have transfer caps.
Acquired WAV bytes are preserved without audio processing, and verified using ZIP
CRC32, SHA256, format checks and full decoding.

## Reproducible selection

Seed 860120, Python random.Random; sort all input pools before sampling. Sample six
eligible speakers per released gender group, then ten clips per speaker without
replacement. Exclude clips tagged [abrupt] or [external]; retain and report [snap],
[breath], [hesitation]. These exclusions bias the pilot toward cleaner material.
This is a small development sample, not a representative population estimate.
The immutable pilot manifest records the exact 120 IDs, transcripts and ZIP members.

## Run

From the repository root using Python with requirements-acoustics.txt and
requirements-import.txt installed:

```powershell
python scripts/import_slr86_pilot.py
python scripts/import_slr86_pilot.py --acquire
python scripts/validate_slr86_pilot.py
python scripts/analyze_natural_manifest.py work/slr86/natural_reference.jsonl --output-dir work/slr86/acoustics --limit 120
```

The importer fetches only small metadata and ZIP directory/index/license members
without --acquire. --acquire permits the selected 120 WAV members only. Cached audio
must pass integrity checks and is never overwritten. Outputs are local and ignored
by Git; retain the complete work/slr86 directory for reproducibility.
The acoustic bridge defaults to a dry run. A later explicit --run performs existing
descriptive pYIN extraction. It preserves the physical analysis window at 48 kHz,
checks source hashes, and writes per-record artifacts. The current 65–500 Hz search
range needs inspection for individual speakers; it is not a validated universal range.
Utterance-median relative pitch is provisional, not a cohort speaker baseline.

## Interpretation and review

Raw text and canonical NFC copies coexist. NFC does not repair orthography. Explicit
tone-mark rates are not completeness or accuracy: unmarked vowels may be mid-tone
or underspecified. Underdots distinguish e/ẹ and o/ọ but their presence does not prove
lexical correctness. Conflicting accents and uncommon underdotted vowels are flagged
without correction. Nasal spelling candidates and heuristic syllable forms describe
written coverage only, not aligned phonemes or acoustic nasality.

The source legend lists five annotation types. Its claimed total 1306 conflicts
with its own 682+625 and the 1307 tags in the released indexes; originals are retained.
Filename/index consistency verifies source pairing, not that a human has listened
to and confirmed every utterance. Records remain source_provided_unreviewed, with
no inherited AI-listener annotation and all assessment dimensions UNSCORED.

Human review is needed before using transcripts as lexical-tone ground truth.
Read speech also differs from spontaneous assistant speech. Acoustic extraction
readiness must not be interpreted as readiness for automatic error classification.
