# Yoruba training collection — Batch 01 candidate review

## Do not record yet

These 30 sentences are candidates, not approved training text. The fluent speaker must first confirm that each Yoruba sentence is correct, natural, and matches the English meaning. Any awkward or overly formal wording should be replaced before recording.

## Collection design

- 24 candidate training sentences (`YT0001`–`YT0024`);
- 3 development sentences (`YT0025`–`YT0027`);
- 3 held-out test sentences (`YT0028`–`YT0030`);
- no exact Yoruba sentence duplicates from the existing 120-item benchmark;
- one recording per sentence;
- filename shown in `training_batch_01.csv`;
- all items currently have `speaker_review_status=pending`.

## Speaker review method

For every row, answer:

- **Text correct?** yes/no
- **Meaning correct?** yes/no
- **Natural Yoruba?** yes/no
- **Correction:** provide the preferred Yoruba wording if any answer is no

Do not approve a sentence merely because its individual words are valid. It must sound like something a fluent speaker would naturally say.

## Recording rule after approval

Record exactly one sentence per audio file, in prompt-ID order, at a comfortable speaking pace. Do not add the English meaning or prompt ID to the recording. If you restart or correct yourself, discard that take and record the entire sentence again.

## Split handling

Training software may use only rows marked `train`. Development rows may guide checkpoint selection. Test rows must remain excluded from training and tuning. Because the same speaker records all splits, this first batch tests unseen sentences, not unseen-speaker generalization.

