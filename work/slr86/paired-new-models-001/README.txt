Bounded speech expansion and supervised alignment

Completed: 12 gpt-realtime-2.1 / marin takes (six original texts x two fresh sessions), 55.05 seconds total; raw PCM16 mono 24 kHz and identical-sample WAV containers retained. All analyzed using existing compare() and original agreement-screen logic. See gpt-realtime-2.1/generation_manifest.json and measurements/<generation_id>/{raw.json,analysis.json,frames.csv,praat_native_frames.csv}.

Blocked: gpt-live-1. Documented wss://api.openai.com/v1/live/sessions returned HTTP 403 Forbidden before session startup on the generation attempt and a connection-only diagnostic. No Live audio or substitute model was generated. Its adapter has not been validated against a successful session. Do not blindly rerun the failed attempt: preserve the existing failure and create a new explicit attempt after endpoint access is resolved.

Review: listening_review.html; exports paired_new_models_001.json. New ratings blank; accepted mini-TTS v2 ratings unchanged. Natural and mini-TTS audio are provided as context. Marin vs baseline coral and endpoint differences are confounds; no model ranking is valid here.

Exact input code points preserved. Provider output transcripts differed in underdots for p02 take1 and p03 take1. See content_checks.json. Neither transcript matches nor discrepancies certify spoken realization. All takes need native content verification; no auto-correction or regeneration occurred.

Deep alignment: ../deep-alignment-p05-001/alignment_review.html. p05 reference is Eledẹ text preserved in alignment.json. Three original recordings; twelve orthographic tone-bearing units each. All boundaries are unverified seeds based on equal-duration anchors near energy minima. This is a manual-supervision package, not completed forced alignment. Proposed boundaries, especially the two vowel units in naa, can be wrong. Human review is needed before linguistic analysis. No phoneme boundaries or observed correctness are claimed. Broad interval medians include uncertain and mixed-segment frames; reliability counts and original flags are retained. Some intervals have zero screen-passing frames. Natural-reference tone-mark completeness is not exhaustive ground truth.

Open alignment_review.html to edit intervals, audition them, record confirmation/uncertainty and export deep_alignment_p05_review.json. Export before closing. Static PNGs show original proposals; exported human edits do not overwrite them.

Validation: validation.json confirms distinct sessions/audio, PCM/WAV equivalence, ordered reference intervals, 975 pre-existing files unchanged and both accepted v2 exports unchanged. JS syntax checks passed and both review pages rendered successfully. Source snapshots: versions/. websocket-client 1.9.2 added to the existing acoustic virtual environment. No training, correctness scoring, baseline re-extraction or previous-review mutation.

Official sources retrieved: docs/voice-websockets.md, docs/live-conversations.md, docs/realtime-conversations.md, from https://developers.openai.com/api/docs/guides/ .
