# Technical research specification: meaning-preserving Yoruba voice synthesis

**Status:** Initial specification and novelty review, 18 July 2026
**Scope:** Voice generation only. Yoruba text generation is outside scope.

## 1. Research objective

Develop a training method and evaluation package that developers of multilingual voice models can integrate to reduce meaning-changing Yoruba pronunciation errors, especially lexical-tone errors.

The intended users are speech-model teams at organizations such as OpenAI, Anthropic, Google, Meta, and open-source model developers. The output must therefore be architecture-relevant, reproducible, and separable from any one commercial product.

## 2. What is already known

This project cannot claim that tone or pitch modeling for Yoruba is new.

- Earlier Yoruba synthesis research extracted syllable-aligned F0 contours and developed explicit F0 and target-approximation models. These methods improved pitch modeling in pre-neural or HMM-based systems. [van Niekerk and Barnard, 2013](https://www.isca-archive.org/interspeech_2013/niekerk13_interspeech.html) and [2014](https://www.isca-archive.org/interspeech_2014/niekerk14_interspeech.html)
- ÌròyìnSpeech provides about 42 hours of in-house Yoruba speech plus validated Common Voice recordings, and its authors demonstrated a single-speaker VITS model using approximately five hours. [Ògúnrẹ̀mí et al., 2024](https://aclanthology.org/2024.lrec-main.812/)
- A 2026 user study found that evaluated Yoruba TTS systems remained robotic and suffered from mispronunciation and inconsistent tone handling. [Kausar et al., 2026](https://aclanthology.org/2026.africanlp-main.23.pdf)
- Tone Error Rate has recently been used for Yoruba ASR, but ASR and TTS are different tasks. [Olusanya, 2026](https://aclanthology.org/2026.loreslm-1.14.pdf)
- Recent tonal-speech work has introduced tone-aware contrastive objectives for speech encoders, so a generic claim of “contrastive tone learning” would also be insufficient. [SITA, 2026](https://arxiv.org/abs/2601.09050)

## 3. Proposed contribution

### Provisional research question

Can a **functional-load-weighted, tone-contrastive training objective** reduce meaning-changing tone errors in modern end-to-end Yoruba TTS without reducing naturalness?

### Hypothesis

Given the same TTS architecture and Yoruba training audio, a model trained with explicit syllable-tone supervision and extra weight on meaning-distinguishing tone contrasts will achieve higher tone-contrast preservation and listener meaning accuracy than:

1. the same model trained conventionally; and
2. the same model trained with diacritized text but no explicit tone objective.

### Why this is stronger than “tone-aware TTS”

The model is not rewarded equally for every pitch deviation. It receives stronger supervision where tone has high functional load: locations where changing H, M, or L can change the intended lexical or grammatical interpretation. The experiment therefore targets communication failure, not pitch imitation alone.

Novelty remains **provisional** until the full systematic review is completed. The defensible candidate novelty is the combination of:

- modern end-to-end Yoruba TTS;
- syllable-level tone supervision;
- contrastive separation of tone-differentiated forms;
- functional-load or meaning-risk weighting; and
- meaning-focused Yoruba TTS evaluation.

## 4. Model design

### Baseline architecture

Use VITS first because it is modifiable, end-to-end, and has already served as a Yoruba baseline in ÌròyìnSpeech. The original VITS implementation is publicly available. [VITS repository](https://github.com/jaywalnut310/vits)

MMS-TTS-Yor should be an inference benchmark, not the primary training platform: its released weights/code carry noncommercial restrictions, which conflict with the goal of producing commercially adoptable research artifacts. [MMS documentation](https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md)

### Input representation

For every Yoruba utterance:

1. normalize Unicode to NFC;
2. preserve `ẹ`, `ọ`, `ṣ`, acute accents, and grave accents;
3. segment vowel nuclei/syllables;
4. map orthographic tones to H, M, and L;
5. retain neighboring tone context;
6. store word and utterance boundaries;
7. later add rules or learned labels for elision, assimilation, downstep, and surface realization.

The repository now contains a first Unicode-safe orthographic tone parser. It is intentionally not yet a complete Yoruba phonology engine.

### Training objective

The proposed model uses:

\[
L = L_{VITS} + \lambda_t L_{tone} + \lambda_f L_{F0} + \lambda_c L_{contrast}.
\]

- `L_VITS`: the unchanged acoustic/generative objective.
- `L_tone`: syllable-level H/M/L classification from generated or latent acoustic representations.
- `L_F0`: speaker-normalized F0 contour loss over voiced syllable regions.
- `L_contrast`: separates representations or generated contours for segmentally similar forms with meaning-relevant tone differences.

For syllable `i`, tone loss is weighted by estimated functional load:

\[
L_{tone} = \sum_i w_i CE(\hat{t_i}, t_i), \quad w_i = 1 + \alpha r_i,
\]

where `r_i` is a meaning-risk score derived from minimal contrasts, lexical ambiguity, or benchmark annotations.

## 5. Experimental conditions

Use identical data splits and training budgets.

| System | Diacritized input | Explicit tone loss | F0 loss | Meaning-risk weighting |
|---|---:|---:|---:|---:|
| A. Conventional VITS | Yes | No | No | No |
| B. Tone auxiliary | Yes | Yes | Yes | No |
| C. Proposed | Yes | Yes | Yes | Yes |

Required ablations:

- remove `L_tone`;
- remove `L_F0`;
- remove contrastive loss;
- set every functional-load weight to one;
- compare orthographic versus context-conditioned surface-tone targets.

## 6. Data plan

### Public training data

Primary candidate: a verified single-speaker subset of ÌròyìnSpeech, because the publication reports a successful five-hour VITS baseline. The paper describes its curated text as CC BY 4.0, but the exact license covering each audio subset must be verified before download, redistribution, or model release. This is a release gate, not an assumption.

OpenSLR 86 provides quality-checked Yoruba WAV audio and transcripts and points to a separate license file. Its exact permitted uses must likewise be checked before inclusion. [OpenSLR 86](https://openslr.org/86/)

The recently listed Mozilla Yoruba TTS dataset is not suitable for this project under its displayed restrictions because it prohibits generative-AI use, voice cloning, redistribution, and unapproved commercial use. [Mozilla Data Collective listing](https://mozilladatacollective.com/datasets/cmo1nlaah0071mk077mw0qhpv)

### Participant recordings

The current 20-utterance, 87-second recording is a calibration set. It proves the capture workflow but is too small for training a competitive voice model.

The participant corpus will be used for:

- controlled reference pronunciation;
- high-functional-load tone contrasts;
- held-out evaluation;
- optional speaker adaptation after enough data is collected.

Target for the next collection: 30-60 minutes after the benchmark inventory is finalized. The public corpus provides the main training volume; the participant data provides deliberately controlled contrasts and an independent speaker.

## 7. Evaluation

### Primary outcomes

1. **Tone Contrast Preservation Accuracy (TCPA):** forced-choice accuracy on which intended tone-differentiated item was synthesized.
2. **Syllable Tone Error Rate (STER):** H/M/L substitutions, insertions, and deletions against annotated targets.
3. **Meaning Recovery Accuracy:** listeners select or state the intended interpretation after hearing synthesized speech.

### Secondary outcomes

- speaker-normalized F0 correlation and RMSE;
- segmental intelligibility and vowel-confusion accuracy;
- naturalness MOS;
- speaker similarity where relevant;
- intelligibility of connected speech;
- code-switch performance as a later, separate experiment.

The primary statistical comparison is C versus A on TCPA and meaning recovery. Naturalness is a non-inferiority constraint: improved tone accuracy is not sufficient if speech becomes materially less natural.

### Minimum human-evaluation limitation

The current participant can validate text and provide initial listening judgments, but self-evaluation cannot support a strong perceptual claim. The first prototype can report automatic results and single-rater diagnostics; a publication-quality study will eventually require independent fluent Yoruba listeners.

## 8. Reproducibility package for model developers

The research release should contain:

- tone parser and annotation schema;
- data-preparation scripts;
- tone-balanced and functional-load-weighted sampler;
- VITS patch implementing the auxiliary heads/losses;
- benchmark prompts and split definitions;
- evaluation scripts and confusion matrices;
- training configurations and random seeds;
- ablation results;
- dataset provenance, consent, and license documentation;
- model card and failure analysis.

## 9. Immediate execution plan

### Current session

- Completed: recording calibration and audio-quality verification.
- Completed: initial novelty map.
- Completed: baseline/model and dataset shortlist.
- Completed: first Unicode-safe Yoruba tone parser and unit tests.

### Next implementation block

1. Audit the parser with fluent-speaker corrections.
2. Build a tone-sequence inventory from candidate public transcripts.
3. Draft the high-functional-load benchmark and participant recording list.
4. Verify dataset licenses at the file/subset level.
5. Obtain GPU compute; this computer did not expose a usable NVIDIA training device during the initial check.
6. Reproduce conventional Yoruba VITS.
7. Add tone and F0 auxiliary objectives.
8. Run the controlled three-condition experiment and ablations.

## 10. Decision

Proceed with VITS as the first reproducible baseline and treat the contribution as **meaning-risk-weighted tone preservation**, not generic Yoruba TTS or generic tone modeling. Do not collect the longer participant corpus until the functional-load benchmark inventory has been reviewed by the fluent speaker.
