# Experiment 1 — frozen Condition B training recipe

## Decision and approval state

Condition B will use Meta's full Yoruba MMS checkpoint with the original trainable VITS generator and
Multi-Period Discriminator. The Transformers wrapper is prohibited for training. The condition is
ordinary verified text/audio adaptation with the existing orthographic frontend and original VITS
losses only. Tone, syllable, phoneme, surface-prosody, and contrastive auxiliaries are prohibited.

The executable settings are frozen in `condition_b_recipe.json`. Its status is
`frozen_pending_user_approval`; no training or full-checkpoint download is authorized yet.

## Initialization and modules

Initialize `G_100000.pth` and `D_100000.pth` from Meta's 919,869,645-byte full Yoruba archive. Train
all generator and Multi-Period Discriminator modules. Create fresh optimizers instead of restoring
pretrained optimizer moments, which could dominate this 71-second adaptation set.

## Frozen optimization settings

| Setting | Value |
|---|---:|
| Optimizers | AdamW for generator and discriminator |
| Learning rate | 1e-5 for both |
| Betas / epsilon | (0.8, 0.99) / 1e-9 |
| Weight decay | 1e-4 |
| Scheduler / warmup | constant / none |
| Micro-batch / accumulation | 2 / 4 |
| Effective batch | 8 clips |
| Update ratio | 1 generator : 1 discriminator |
| Maximum updates | 300 |
| Minimum before early stopping | 100 updates |
| Gradient-norm cap | 5.0 |
| Precision | FP16 |
| Training / synthesis seed | 1234 / 555 |

The original VITS learning rate is 2e-4. This recipe lowers it twenty-fold because the model already
speaks Yoruba and there are only 23 training clips. The 300-update cap never overrides early stopping.

## Audio and loss

Deterministically resample 24 kHz sources to 16 kHz with TorchAudio's Hann-windowed sinc resampler.
Do not trim, denoise, loudness-normalize, augment, or oversample. Use 1024-sample FFT/window,
256-sample hop, 80 mel channels, 0–8000 Hz range, and 8192-sample segments.

Retain the original VITS mel L1 (weight 45), duration, KL (weight 1), feature-matching, generator
adversarial, and discriminator objectives. No additional loss is allowed.

## Development selection and overfitting safeguards

Evaluate all three development clips every 25 updates. Select the lowest mean
`45*mel_L1 + duration_nll + KL`; log but exclude adversarial and feature-matching losses from
selection. Require 0.5% relative improvement. Stop after four non-improving evaluations, but not
before update 100. Restore the best development checkpoint and retain best, last, provenance, and
logs. Flag a train/development reconstruction gap above 25% without consulting the protected test set.

Additional safeguards are the low learning rate, hard update cap, fresh optimizers, one frozen seed,
no sweeps or augmentation, and immutable Condition A settings. One seed supports a feasibility pilot
only; confirmatory work requires multiple seeds.

## Compute requirement

Use Linux with one NVIDIA GPU. The minimum is 12 GB VRAM (for example RTX 3060 12 GB); 16 GB is
recommended (for example a cloud T4). L4 or A10 24 GB provides more margin but must retain the frozen
batch settings. Estimated runtime is 30–120 minutes after setup, subject to a logged projection from
the first ten updates. CPU training is prohibited.

## Permitted implementation patch

The original trainer assumes multi-GPU CUDA, evaluates one development example, and lacks accumulation
and early stopping. The project patch may add only single-GPU launch, deterministic resampling,
four-step accumulation, 5.0 gradient clipping, complete three-item development evaluation, frozen
selection/stopping, and provenance. It may not alter architecture, losses, tokenizer, splits, or test
criteria. Resolved source commits and source-tree hashes must be recorded before execution.

## Scientific limitation

Condition A reached ceiling on pronunciation, tone, intelligibility, and meaning; naturalness was
partial. The three protected test items can therefore detect regression and possible naturalness
improvement, but cannot show improvement above 100% on the other binary endpoints.

## Official basis

- Meta MMS full-checkpoint instructions: https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md
- Meta MMS Yoruba model card: https://huggingface.co/facebook/mms-tts-yor
- Original VITS code: https://github.com/jaywalnut310/vits
- Original VITS configuration: https://github.com/jaywalnut310/vits/blob/main/configs/ljs_base.json
- Original VITS trainer: https://github.com/jaywalnut310/vits/blob/main/train.py

No training begins until Mary Adelua approves this exact recipe.
