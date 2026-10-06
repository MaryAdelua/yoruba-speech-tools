SUPERVISED ALIGNMENT REVIEW DRAFT — ONE RECORDING

Reference: ó ní ọ̀sán márùn-ún
This is the user's intended form, not a certified phonetic transcript. The user's
reference accents are preserved without replacing them with the earlier draft.
Reference H/M/L labels are derived from the written vowels with the existing
tone_parser. The segmentation is an explicit seven-unit review hypothesis, not
a claim that seven distinct syllables were correctly realized in the recording.
In particular, the final rùn/ún division is not acoustically established.

Current human/native-listener annotation (supersedes earlier narrower summary):
As a native Yorùbá speaker, I perceive the entire AI-generated utterance as unnatural. The entire utterance has an unusually nasal/nasalized quality, not merely the final word. The tonal/melodic realization sounds unnatural for Yorùbá. Some consonant/nasal portions appear unusually prominent or lengthened. Although the lexical content is recognizable, recognizable/correct text must NOT be treated as evidence of correct pronunciation.
Scope: entire utterance. Not an acoustically proven diagnosis. Confidence and
localized intervals were not supplied. Previous wording is retained in history.

Lexical-tone reference labels, segmental/nasal observations, and utterance-level
prosody are kept separate in alignment.json. All quality scores remain UNSCORED.

Open review.html for the plot, whole-utterance playback and proposed-unit playback
with 80 ms context. It plays the ORIGINAL assistant.wav at normal rate; no audio
copies or processed clips are created. Playback controls are a listening aid,
not sample-accurate segmentation. Segment playback itself can create misleading
perceptual boundaries, so listen to the full utterance first.

All boundaries require native review. Most anchors originate from earlier local
CTC token events (anchor_evidence.json), which are not phonetic boundaries and
contain recognition errors. We reused these without rerunning ASR. At 1.78 s,
the final rùn/ún boundary is only a placeholder to support a review conversation.
Do not use its per-unit statistics as separate verified nuclei. The continuous
final interval 1.64–1.90 s remains intact in the waveform and raw measurements.

CSV statistics include every available F0 estimate whose center falls in the
proposed interval [start,end). No F0 value is discarded or rewritten. They are
descriptive summaries, not certified reliable F0. The associated_frames.csv
retains estimator probabilities, Praat strength, disagreements, source flags,
and an additional indicator for pYIN windows crossing a proposed boundary.
Praat windows also overlap boundaries; its native measurement grid remains in
the Milestone 2 artifacts. This pilot is not vowel-nucleus alignment.

Relative pitch retains Milestone 2 normalization, 12*log2(F0/estimator median):
pYIN 99.0923065 Hz; Praat 100.4921190 Hz. These are full-clip provisional baselines.
No fixed-Hz H/M/L bins, tone correctness, nasal duration estimate, or naturalness
metric is computed. Original timing, nasal phenomena and low-confidence outputs
are preserved; source hash matches the prior measurements.

Files:
alignment.png — waveform, spectrogram, raw and relative F0, proposed boundaries.
review.html — local audio/visual inspection page using the original recording.
alignment.json — reference, exact human annotation, provenance, per-unit summaries.
syllables.csv — per-unit descriptive table; all boundaries unverified.
associated_frames.csv — unaltered frame evidence plus interval association.
anchor_evidence.json — earlier recognizer evidence and source-time conversion.

Reproduce from repository root with a NEW output directory:
.venv-acoustics\Scripts\python.exe -X utf8 scripts/build_supervised_alignment.py --output-dir work/voice_eval/supervised-alignment-review-next
Edit only the explicit reference boundary config after native review:
evaluation/voice_interactions/supervised_alignment_001.json
Do not mark boundaries confirmed based solely on successful artifact generation.

Implementation checks: reference tone marks, uncertainty retention, half-open
interval assignment, raw frame preservation, overlap flags and invalid boundaries.
No automated tone-error classification or subsequent milestone was attempted.
