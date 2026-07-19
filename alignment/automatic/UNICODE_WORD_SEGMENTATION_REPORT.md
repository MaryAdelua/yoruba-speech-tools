# Unicode-safe word segmentation repair

The word layer has been rebuilt from the authoritative NFC Yoruba transcripts.
Twenty-three of the 30 recordings contained at least one token whose spelling
had been split or truncated by the previous tokenizer. All 30 corrected records
now match whitespace/punctuation-delimited orthographic words and pass the word
and syllable interval validator.

The bug came from the regular expression `[^\W\d_]+` used by the first
alignment builder. Some Yoruba vowels are represented by a precomposed
underdotted letter followed by a separate combining tone mark. Python does not
classify that combining mark as a word character, so the match stopped at the
tone mark. In `ẹ̀fọ́`, for example, the grave mark after `ẹ` terminated one
match, producing `ẹ` and `fọ́` instead of the single word `ẹ̀fọ́`.

The replacement tokenizer explicitly treats Unicode combining marks as part of
the current word and normalizes text to NFC without deleting tone or underdot
information. The acoustic token timestamps were reused; no ASR decoding was
rerun. Pre-fix and raw CTC alignments remain preserved, and the full old/new
word inventory is stored in `unicode_word_segmentation_audit.jsonl`.
