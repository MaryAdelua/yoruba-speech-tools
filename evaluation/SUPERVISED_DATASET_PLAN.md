# Supervised examples: schema and collection plan

## Current strategy update

The corpus-first strategy in [CORPUS_STRATEGY.md](CORPUS_STRATEGY.md) supersedes
the collection assumptions below. Existing licensed natural speech is the default
reference source; newly recorded human versions of every prompt are NOT required.
Natural-reference evidence and later perceptual validation are separate. Version
0.2 supports explicitly typed natural and AI samples, paired/unpaired designs,
and independent nasality and overall-naturalness research targets. The older
five-dimension schema and example are preserved for reproducibility.

The unit of data is one immutable audio recording plus separately versioned
reference text, human observations, acoustic measurements and alignment hypotheses.
Recognizable lexical content does not certify pronunciation. The current reference
is the user's intended form, not a phonetic transcript of the acoustic realization.

## Five independent dimensions

1. Lexical tone accuracy: eventual segment-local tone realization judgments, with
   expected reference tones separate from measured pitch and contextual realization.
2. Segmental pronunciation: consonants, vowels, perceived nasal realization and
   duration. No diagnosis of nasality is established by F0.
3. Prosody/intonation: utterance-level contour, phrasing and perceived naturalness.
4. Fluency/rhythm: timing, pauses, continuity and rhythm, separately annotated.
5. Semantic/content correctness: intended meaning and response content; independent
   of pronunciation and naturalness, and with ASR uncertainty preserved.

Utterance-level naturalness is an additional human observation, not an automatic
overall score or an aggregate of these dimensions. Perceived nasality is stored as
a perceptual observation under segmental pronunciation; it may span the utterance.
General tonal/melodic observations are not automatically converted into localized
lexical-tone errors. Record uncertainty and possible cross-dimensional relevance.

## Schema contract

`supervised_example.schema.json` defines the draft interchange format. Each example
has an immutable audio hash, user/reference provenance, annotation revision history,
five distinct assessment records, human observations, measurement references and
alignment references. Human observations include annotator identity/source,
utterance-versus-interval scope, nullable intervals, confidence with provenance,
and a fixed `human_perception_not_acoustic_diagnosis` evidence type.

Missing confidence is null/not_provided, not low confidence. Missing localized
intervals is null, not an invented 0.8–1.9 interval. The annotator's statement applies
to the utterance even when recording boundaries remain provisional. Record identity
may be pseudonymous; dialect and recording context should be collected voluntarily.
Time intervals, if later supplied, must satisfy 0 <= start < end <= audio duration;
this relational check is required in addition to JSON Schema validation.

Automated scores remain null with UNSCORED status in this pilot schema. Future
scoring requires a new reviewed schema version and validation evidence. A reference
to an earlier semantic judge report must not import its result into other dimensions.
Acoustic measurements include units, settings, source hash and limitations, not
human diagnoses. Alignment records remain hypotheses until explicitly reviewed.

## Incremental dataset plan — no collection expansion yet

1. Finish this one example: preserve the listener's utterance-wide observation,
   review reference segmentation and boundaries, and retain unresolved nasal spans.
2. Pilot the annotation instructions with a small consented set and independent
   native listeners. Collect whole-utterance naturalness, perceived nasality, tone,
   segmental, prosodic and rhythm observations separately; allow unsure/not assessed.
   Annotators may give time intervals but should not be forced to localize a global
   impression. Collect confidence explicitly rather than infer it from wording.
3. Retain individual judgments and disagreements before adjudication. Have listeners
   assess audio before revealing model identity or automated output where feasible;
   use a separate reference-assisted pass for lexical content and tone hypotheses.
4. Later choose balanced prompts and speakers/voices that distinguish expected nasal
   realizations from perceived excess nasality, and lexical tone from broader prosody.
   Include acceptable examples and errors, multiple recording conditions, repeats,
   speaker/dialect metadata and annotation provenance. Do not treat synthetic edits
   as equivalent to naturally occurring model errors.
5. Investigate candidate measurements for perceived nasality only after selecting
   appropriate methods and references. Compare candidates with independent listener
   annotations, controlling for vowel identity, phonetic context, speaker and channel.
   Do not nominate a pitch statistic as a nasality detector. No nasality feature or
   threshold is selected or implemented by this plan.
6. Separate development from held-out validation by speaker/voice and prompt family
   as feasible. Prevent source clips, duplicate utterances and derived versions from
   crossing splits. Preserve existing protected test items and consent restrictions.
7. Validate each detector separately against its own annotation target. Report missing
   evidence and disagreements, not a composite score that hides failure in one area.

Only the schema, one example and documentation are created now. No new recordings,
native-speaker comparison, automatic error classification or final scoring is run.
