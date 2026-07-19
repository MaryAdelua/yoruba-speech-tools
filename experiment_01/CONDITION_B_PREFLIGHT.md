# Experiment 1 — Condition B preflight

## Status

Condition B has started at the implementation-preflight stage. No model weights have been updated.
The preflight preserves the frozen definition: **matched Yoruba data adaptation with the existing MMS
frontend and no auxiliary supervision**. Conditions C and later features remain disabled.

## What passed

- 23 training items, 3 development items, and 3 protected test items are present.
- Every declared audio file exists locally.
- YT0028–YT0030 remain protected from training and checkpoint selection.
- All transcripts pass the selected MMS Yoruba tokenizer with zero unknown tokens.
- Each record has a stable audio hash and split-group identifier.
- Source audio is 24 kHz mono and must be deterministically resampled to the model's 16 kHz time base.
- The Condition A model commit and held-out evaluation items remain fixed.

The machine-readable result is
`artifacts/experiment_01/condition_b/preflight_manifest.json`.

## Why weight updates have not started

The frozen proof-of-concept protocol names the condition but does not contain executable training
settings. It does not specify the optimizer, learning rate, batch and accumulation policy, update
budget, stopping rule, development selection metric, number of seeds, or trainable modules. Choosing
these during execution would create researcher degrees of freedom and contradict the instruction not
to alter or invent frozen settings.

The selected Hugging Face `VitsModel` interface provides MMS synthesis but not the full adversarial
training system needed for ordinary VITS data adaptation. A defensible end-to-end Condition B requires
Meta's original MMS/VITS generator, discriminator, loss implementation, and compatible checkpoint—or
a separately predeclared custom training implementation. The current checkpoint selection report
anticipated this requirement.

Finally, the local runtime has CPU-only PyTorch. Baseline synthesis is practical on CPU, but VITS GAN
adaptation is not a reasonable consumer-CPU run. The actual training device and memory must be recorded
before the update budget and batch policy can be frozen.

## Scientific constraint from Condition A

Condition A reached ceiling on pronunciation, tone, intelligibility, and meaning across the three
test items. Naturalness was partial for all three. Condition B can therefore demonstrate improved
naturalness or detect regression, but it cannot demonstrate improvement above 100% on the other
binary endpoints using this frozen subset. This limitation does not authorize changing the test set
mid-experiment.

## Required decision before training

Freeze one complete Condition B training recipe and run it unchanged. At minimum it must specify:

1. the original MMS/VITS training implementation and exact revision;
2. the initialization checkpoint and trainable/frozen modules;
3. optimizer, learning rate, batch size, accumulation, and update budget;
4. deterministic 24 kHz to 16 kHz resampling and audio normalization;
5. development-only checkpoint selection and stopping rule;
6. training seeds and number of runs;
7. compute device and memory;
8. retained checkpoints, logs, and failure policy.

No auxiliary tone, syllable, phoneme, surface-prosody, or contrastive objective may enter Condition B.
