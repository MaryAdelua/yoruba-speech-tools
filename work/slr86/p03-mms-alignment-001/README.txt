Local inference with TorchAudio MMS_FA (torch/torchaudio 2.8.0 CPU). No training.
Original tone-marked reference remains unchanged; an explicitly lossy ASCII adapter is used ONLY by the alignment model. This model does not measure Yoruba tone or pronunciation correctness.
All 50 word associations are model proposals except the two reused natural cut-usability judgments. CTC probabilities are internal alignment diagnostics, not calibrated reliability or linguistic scores. Forced alignment assumes the supplied text; it cannot prove the audio contains it.
Analysis resampling to 16 kHz occurs in memory only. Acoustic measurements are reused from original recordings, not recomputed from resampled audio. Playback uses exact original PCM slices, with bounded context padding; measurements use CTC intervals.
The earlier visual word proposals should not be used for linguistic analysis. Old files and human feedback are preserved. This new package awaits native listening validation.
Known warning: TorchAudio alignment API is deprecated after 2.8; versions pinned for reproducibility.
Source: https://docs.pytorch.org/audio/2.8/tutorials/forced_alignment_for_multilingual_data_tutorial.html
