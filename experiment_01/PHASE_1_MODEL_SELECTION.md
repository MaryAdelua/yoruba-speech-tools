# Experiment 1 — Phase 1 model selection

## Decision

Use **Meta MMS-TTS Yoruba (`facebook/mms-tts-yor`)** as the first proof-of-concept test bed.
It is a Yoruba-specific checkpoint in the multilingual MMS family, uses VITS, has 36.3 million
parameters, and exposes a stochastic duration predictor. Phase 1 validates only its tokenizer and
integration interface; no weights are downloaded, loaded, or updated and no training has begun.

This is a research test-bed choice, not a recommendation that downstream organizations adopt the
checkpoint itself. Its CC BY-NC 4.0 checkpoint license excludes commercial use. The dataset contract,
feature projections, loss definitions, and evaluation protocol remain architecture-independent and
can be implemented in a differently licensed production model.

## Candidate comparison

| Candidate | Yoruba starting point | Fine-tuning / intervention access | Consumer-hardware fit | License consideration | Decision |
|---|---|---|---|---|---|
| Meta MMS-TTS Yoruba | Explicit Yoruba checkpoint; no language extrapolation required | VITS text encoder and duration pathway are suitable attachment points; full training requires the MMS/original-VITS training stack or a custom loop | Best: 36.3M parameters and a roughly 145 MB safetensors file | Checkpoint is CC BY-NC 4.0 | **Selected for Experiment 1** |
| IMS Toucan | Yoruba is explicitly listed in the supported language inventory | Excellent training recipes and controllable duration/pitch/energy modules | Training expects a CUDA GPU; broader system is more complex | Apache 2.0 | Strong replication target, but its default phoneme/IPA frontend would introduce supervision not yet human-verified in this dataset |
| Coqui XTTS-v2 | Yoruba is not one of the 16 documented languages | Current XTTS implementation documents inference and GPT-encoder training, not the clean auxiliary hooks required here | Feasible for inference, less suitable for this controlled adaptation | XTTS checkpoint uses the Coqui Public Model License | Rejected for the first experiment |

## Why MMS is the most rigorous first test

1. **It starts from an actual Yoruba checkpoint.** A failure cannot be dismissed as choosing a model
   with no declared Yoruba capacity.
2. **It is small enough for a constrained pilot.** Tokenization and inference can be checked on CPU;
   later fine-tuning can use a modest GPU without redesigning the experiment.
3. **Its character vocabulary represents Yoruba orthography.** The interface audit confirms the
   checkpoint retains underdotted vowels/consonants and high/low tone forms rather than romanizing
   them. Its tokenizer lowercases and removes out-of-vocabulary punctuation, but does not use uroman
   or a phonemizer.
4. **Its VITS structure supports the planned controls.** The existing text encoder supports the
   unchanged baseline path, and its duration pathway gives a defined place for syllable-duration
   supervision. Orthographic tone can be projected to encoder token positions without enabling the
   unverified phoneme or surface-tone labels.

## Integration contract

The canonical toolkit remains the source of truth. The model adapter performs the following steps:

1. Read `artifacts/integration_dry_run/canonical_records.jsonl` and verify each target-identity hash.
2. Feed `text_nfc` through the official MMS Yoruba tokenizer. Preserve the original NFC text in the
   dataset; model normalization is recorded as a derived view, never written back over it.
3. Project every nonblank MMS content token to the toolkit's source character, grapheme, syllable,
   and H/M/L tone ID. The VITS blank tokens receive loss mask zero for auxiliary linguistic targets.
4. For a tone-aware condition, attach a small trainable tone embedding or tone-classification head
   at the VITS text-encoder sequence. Use only `orthographic_tone_id` where the mask is one.
5. For a syllable-aware condition, aggregate predicted token durations by projected syllable ID and
   compare them with the human-verified syllable durations converted to the model's acoustic time
   base. Punctuation and silence remain outside that loss unless explicitly specified later.
6. Keep the original VITS reconstruction/adversarial objectives unchanged, then add auxiliary terms
   only in the predeclared experimental conditions. The adapter never enables `phonemes` or
   `surface_tone`, whose toolkit masks remain zero.

## Phase 1 validation result

`artifacts/experiment_01/mms_yoruba_interface_validation.json` is the machine-readable audit. It
checks all 29 canonical records with the official tokenizer, records filtered punctuation, rejects
unknown model tokens, and verifies that each annotated tone-bearing syllable reaches at least one
model content token. It also stores the exact token-to-source projection needed by later conditions.

Passing this interface audit means the selected model is compatible with the available verified
supervision. It does **not** demonstrate pronunciation improvement; that question belongs to the
matched training and held-out evaluation phases.

## Known limitations and gates before training

- The checkpoint license limits this proof of concept to non-commercial research.
- The Transformers package provides convenient inference classes, but not a turnkey MMS-VITS
  fine-tuning recipe. The training implementation must therefore pin and document the MMS/original
  VITS stack or provide a tested custom loop.
- No NVIDIA GPU is exposed in the current local task. Before training, record the actual training
  device, memory, software versions, batch size, and gradient-accumulation policy.
- The 29-record resource is a feasibility dataset, not evidence for broad production quality.
- Phase 1 does not download weights, synthesize speech, or begin Condition A.

## Official sources

- MMS Yoruba model card: https://huggingface.co/facebook/mms-tts-yor
- MMS model documentation: https://huggingface.co/docs/transformers/model_doc/mms
- VITS model documentation: https://huggingface.co/docs/transformers/model_doc/vits
- MMS training assets and instructions: https://github.com/facebookresearch/fairseq/tree/main/examples/mms
- IMS Toucan repository and training documentation: https://github.com/DigitalPhonetics/IMS-Toucan
- IMS Toucan Yoruba language listing: https://github.com/DigitalPhonetics/IMS-Toucan/blob/MassiveScaleToucan/Utility/language_list.md
- Coqui XTTS documentation: https://github.com/coqui-ai/TTS/blob/dev/docs/source/models/xtts.md
