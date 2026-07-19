# Open-model proof-of-concept protocol

## Purpose

Use an open-source multilingual TTS model to test whether the resource and integration ladder improve Yoruba pronunciation. The model is a test bed, not the project deliverable.

## Preconditions

- signed release and compatible dataset license;
- new leakage-safe train, development, and held-out test partitions;
- stable text normalization and annotation versions;
- verified pronunciation annotations for the test set;
- predeclared metrics, non-inferiority margin, and stopping rule;
- no tuning on the frozen final test results.

## Conditions

1. unmodified host baseline;
2. matched Yoruba data adaptation;
3. data adaptation plus phoneme/tone frontend;
4. condition 3 plus tone/F0 auxiliary supervision when supported.

Meaning-risk or contrastive weighting is optional and may be added only as a fifth ablation after the simpler conditions are measured.

## Primary outcomes

- phoneme/segmental error on human-verified labels;
- lexical-tone error on verified tone-bearing units;
- blinded listener intelligibility and intended-meaning recovery;
- naturalness with a predeclared non-inferiority margin.

Report bootstrap confidence intervals and item-level errors. Automated ASR or F0 metrics are secondary diagnostics and do not replace fluent-listener evaluation.

## Decision rule

Recommend an integration level only if it improves at least one held-out pronunciation endpoint over the immediately simpler condition without a material regression in intelligibility or naturalness. If ordinary data adaptation performs as well as specialized losses, prefer the simpler method.

## Current status

Protocol only. Training has not started. The current single-speaker 120-item set cannot by itself satisfy the held-out-speaker requirement.

