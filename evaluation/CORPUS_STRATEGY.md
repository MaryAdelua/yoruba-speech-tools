# Corpus-first multidimensional evaluation strategy

Research review: 2026-10-02. Metadata, papers and license pages were inspected;
no corpus audio was downloaded or audited. Published counts are release-specific,
not measurements of local files. Unknown fields below remain unknown.

## Evidence and objective

Natural-reference corpora describe acceptable variation; native-listener ratings
provide perceptual validation of AI speech. These are different evidence types.
Neither corpus membership nor acoustic similarity certifies correct pronunciation.
No requirement exists to recruit speakers to record every AI sentence. A small
listener panel will later validate predictions, not evaluate every future output.

Question: do tone + segmental + nasality-related + prosody + timing features predict
native-listener judgments better than a reproducible lexical-tone-only baseline?
Semantic/content correctness and overall perceived naturalness remain separate
targets. Overall naturalness is not automatically an average of the other targets.

## Candidate comparison

### OpenSLR SLR86 — first choice

36 speakers (19 female, 17 male), 4:01:31, 3,583 utterances. Sentence-level read
speech across several text genres; curated tone-bearing transcripts and speaker
IDs in filenames. Age range 21–43 is reported in aggregate; do not infer individual
ages. Audio: 48 kHz mono 16-bit PCM WAV, recorded in offices with quality checks.
CC BY-SA 4.0 explicitly covers the resource: research permitted with attribution
and applicable share-alike conditions. Useful small multi-speaker starting point;
Standard Yoruba/read-style bias, residual noise and annotated disfluencies remain.
Sources: https://www.openslr.org/86/ and
https://www.isca-archive.org/interspeech_2020/gutkin20_interspeech.pdf

### OpenBibleTTS — separate formal-domain candidate

Yoruba: 89.91 hours, 30,625 verse clips, two reported narrator labels. Speaker labels
are automatic, not independently verified identities. Verse transcripts and book,
chapter, verse, duration and speaker IDs are supplied. Mono audio; sampling rate
varies by language, Yoruba format and tone-mark completeness need item inspection.
CC BY-SA 4.0 is stated on the release. Research is permitted subject to its terms.
Formal scripture, narrow narrator diversity and automatic segmentation limit use
as conversational reference. Do not infer pronunciation perfection from narration.
Sources: https://huggingface.co/datasets/multilingual-tts/open-bible/blob/main/README.md
and https://arxiv.org/html/2606.09553v1

### BibleTTS / OpenSLR SLR129 — distinct from OpenBibleTTS

Published aligned Yoruba: 33.3 hours, 10,228 verses, one speaker. Original unaligned
source: 93.6 hours. Release describes studio 48 kHz, 24-bit mono FLAC and verse
transcripts; orthographic marks require release-item auditing. Speaker demographics
are limited. CC BY-SA release permits research under attribution/share-alike terms.
Automatic alignment is imperfect. Same open.bible ancestry means potential audio
overlap with OpenBibleTTS: these cannot be treated as independent speakers/data.
Sources: https://www.openslr.org/129/ and
https://www.isca-archive.org/interspeech_2022/meyer22c_interspeech.pdf

### IroyinSpeech — strong content fit, official audio license unresolved here

The paper's table totals 42h11m: 26h ASR from 80 volunteers, 10h11m TTS from two
voices, and 6h Common Voice; do not add another six hours to that table. Contemporary
news/fiction, sentence clips, corrected diacritics; speaker/dialect/gender/age
information is described, with per-item availability to verify. Studio recording
and editing are reported; exact delivered codec/sample rate remain unverified.
Read speech and removed disfluencies limit conversational/rhythm conclusions.
The paper explicitly licenses source TEXT CC BY 4.0; the project code is MIT.
Neither establishes full AUDIO licensing. Official project links to ELRA, whose
resource terms could not be retrieved in this review. Hold official audio import.
Sources: https://aclanthology.org/2024.lrec-main.812.pdf and
https://github.com/Niger-Volta-LTI/yoruba-voice

A third-party validated subset lists CC BY 4.0, about 3.07k clips and 98 client IDs,
with tone marks visible in examples. Do not equate it with the full studio corpus
or assume its uploader's label resolves original rights. Duration, codec, source
release and permission chain need verification before use:
https://huggingface.co/datasets/Tundragoon/IroyinSpeech

### Additional candidates

- NaijaVoices: approximately 600 Yoruba hours; 5,000+ speakers refers to all three
  languages, not Yoruba alone. Utterance audio/text and speaker/gender/age-range
  fields; curated read prompts. Yoruba speaker total, tone-mark coverage and
  delivered audio format need release inspection. CC BY-NC-SA 4.0 plus registration
  terms: noncommercial research use under terms, not blanket commercial clearance.
  Keep outside the default product-oriented pilot unless appropriate rights are
  secured. https://huggingface.co/datasets/naijavoices/naijavoices-dataset
- FLEURS: Yoruba included; approximately ten training hours per language is the
  general description, not a verified Yoruba total. Sentence-level read material,
  raw/normalized transcription and gender fields; exact Yoruba speaker total and
  tone completeness unverified. 16 kHz audio, CC BY 4.0 on the dataset card. A
  speaker-disjoint published split does not imply exported persistent speaker IDs.
  Useful later domain/ASR check, weaker first choice for speaker normalization.
  https://huggingface.co/datasets/google/fleurs
- WAXAL Yoruba is listed under Media Trust TTS, not the spontaneous ASR collection.
  The TTS collection is described as single-speaker read scripts; exact Yoruba
  hours/count, tone completeness and delivered format need manifest/header checks.
  Text, speaker ID and gender fields; CC BY-SA 4.0 for this provider. Additional
  non-Bible read-domain candidate, not evidence of conversational coverage.
  https://huggingface.co/datasets/google/WaxalNLP

License interpretation: CC BY permits reuse with attribution; CC BY-SA adds
share-alike for shared adaptations. Retain license version, source, author and
change notices per item. Do not infer that every derived statistic or model has
the same licensing consequence without reviewing the actual intended release.
https://creativecommons.org/licenses/by-sa/4.0/
https://creativecommons.org/licenses/by/4.0/
Research does not automatically mean noncommercial; NC data needs explicit fit.
No unlabeled mirrors, scraped recordings or code licenses substitute for audio rights.

## Pilot sampling proposal, not a power calculation

Start with SLR86 only: 12 speakers x 10 eligible clips = 120 natural recordings.
Use six speakers from each released gender group where feasible, random selection
with a recorded seed, and variation in duration and annotated segment/tone contexts.
Ten clips per speaker test repeatability and provisional speaker baselines; twelve
speakers allow preliminary between-speaker checks without a large review burden.
At the published roughly four-second clip length, this is about eight audio minutes.
This is an engineering pilot, insufficient for population norms or precise detector
accuracy. Expand in speaker blocks if vowel/context coverage or estimates are unstable.
Prefer allocating additional speakers before simply adding one speaker's many clips.

After the first import works, add a small formal-domain slice: ten eligible verses
per verified OpenBibleTTS narrator (up to 20 clips if two are confirmed). This tests
domain handling, not an independent causal domain effect: narrator and domain are
confounded. Do not pool these into one universal normal distribution. Add Iroyin
ASR speakers for contemporary-domain replication only after official audio terms.

AI pilot proposal: six corpus sentences selected across duration and oral/nasal
contexts x two accessible voice configurations x two independent generations =
24 AI recordings. The factorial design tests content, voice and run variability;
six prompts do not cover all Yoruba contrasts. If only one voice is accessible,
report that constraint rather than invent diversity. Human recordings already
exist for these sentences, enabling paired analysis without new human recording.
Keep assistant.wav as an additional unpaired conversational development example.
Do not use this hypothesis-generating example as a held-out success case.

Unpaired comparisons condition on speaker/voice baseline, vowel/context, domain,
duration and capture channel where data support it. Compare distributions, not
distance from a single supposedly correct contour. Paired comparisons establish
shared intended text, not guaranteed identical realization. Alignment uncertainty
and alternate valid realizations remain explicit. No time warping may overwrite
duration features. Bible-source duplicates must be grouped across releases/splits.

Later perceptual calibration: begin with three independent listeners per AI sample
to expose disagreement rather than rely on one opinion; this is a feasibility
design, not enough to prove consensus. Use the pilot variance to plan a larger
validation set. Blind model identity, retain per-listener responses/confidence,
and separate lexical content from pronunciation, nasality, prosody and rhythm.

## Exploratory nasality features — no extraction implemented

| Candidate | Measurement and evidence | Feasibility/limitations |
|---|---|---|
| A1–P0 / A1–P1, including formant-compensated versions | Difference in amplitude between the first-formant peak and nasal-associated spectral peaks; Chen (1997) | Candidate for aligned stable vowels in mono audio; peak overlap, vowel identity, F0, microphone/codec and formant errors confound it. Not token-level proof. |
| F1 bandwidth and spectral tilt | Resonance broadening and spectral-energy slope; Styler (2017) | Extractable experimentally, but breathiness/voice quality and LPC errors can mimic effects. Speaker/language dependence requires normalization and Yoruba validation. |
| Nasal spectral peaks/zeros and low/high-band energy trajectories | Spectral structure and time course; Carignan's acoustic-feature study | Exploratory, needs context-matched vowel intervals and enough clean data. No fixed ratio establishes excessive nasality. |
| Segment duration and timing of nasal-associated changes | Measured interval duration/trajectories, not degree of nasality | Relevant to perceived lengthening only after boundaries are reviewed; rate, context and phrasing must be controlled. |
| Nasalance | Separate nasal versus oral channel energy | Not directly measurable from our mixed mono assistant recording. It normally requires separated oral/nasal acquisition; do not relabel a spectral proxy as nasalance. |

Sources:
Chen (1997): https://pubmed.ncbi.nlm.nih.gov/9348695/
Styler (2017): https://wstyler.ucsd.edu/files/styler2017_jasa_onacousticalnatureofnasality.pdf
Tool cautions: https://github.com/stylerw/styler_praat_scripts/blob/master/nasality_automeasure/README.md
Carignan study: https://discovery.ucl.ac.uk/10121435/1/JASA_NAF_R2.pdf
Nasalance acquisition: https://doi.org/10.1121/10.0027721

For assistant.wav, exploratory spectra are technically obtainable from the 24 kHz
WAV, but decoding from compressed capture cannot restore lost information. Its
short, quiet signal and unresolved nuclei cannot establish excessive nasality.
Neither denoising nor a global pitch statistic resolves this. Natural nasal vowels
and consonants must not be labeled errors merely because they are nasal.

## Architecture, next data and automation

Schema v0.2 separates natural_reference from ai_generated using a discriminator.
Natural records require dataset/version/item/license, speaker and domain metadata,
transcripts and tone-mark status. AI records require provider/model/voice provenance,
prompt, intended response and independently sourced actual transcript. Unknown
versions remain null. Both carry immutable audio/hash, acoustic artifacts, explicit
speaker-normalization provenance, and human annotations separately from measurements.
Analysis-design links support paired natural IDs or an unpaired reference-cohort ID.
The old schema and existing example remain usable; a versioned AI example is added.

Feature families remain lexical_tone, segmental_phonetic, nasality_related,
prosody, rhythm_timing, plus semantic_content. Overall perceived naturalness is an
independent human target. A lexical-tone baseline slot records method/paper/version,
input requirements and applicability; no baseline has been selected or executed.
Later compare baseline alone versus added families on held-out voices/prompt groups,
with clustered uncertainty and explicit capture/channel controls. No training now.

Next obtain metadata first: SLR86 license, both TSV indexes, annotation legend,
speaker IDs and source revisions; then a bounded selection of the 120 clips after
review of the plan. If the provider only offers whole ZIP archives, selective local
extraction may still require downloading the 462 MB + 445 MB archives. Confirm that
transport cost before acquisition; do not claim streaming guarantees small transfers.
Next verify OpenBibleTTS narrator labels, item format/diacritics, upstream overlap
and license notices before acquiring its small slice. Resolve Iroyin official terms
and delivery specs rather than infer permission from the paper or a mirror.

Already automatable: manifest/schema checks, license-status gating, source hashes,
Unicode preservation, header/duration checks, F0/RMS extraction, flags and review
plots. Later implement seeded selection, duplicate detection and corpus summaries.
Needs listener validation: transcription/diacritics spot checks, uncertain alignment,
acceptable contextual variation, perceived nasality and naturalness, dimension-level
labels and whether feature predictions generalize. Corpus distributions alone do
not provide those perceptual targets. Existing semantic judge remains independent.

assistant.wav remains ai_generated, development-only, unpaired: intended user text,
unverified ASR transcript, uncertain alignment, preserved utterance-wide native
observation, unknown model/voice versions, and no correctness scores. No metadata
upgrade changes Milestones 1–3 audio, measurements, boundary hypotheses or history.
