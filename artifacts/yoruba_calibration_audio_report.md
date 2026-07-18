# Yoruba calibration audio report

## Result

- Files received: **20 of 20**
- Missing prompt IDs: **none**
- Total recorded audio: **87.0 seconds**
- Clip duration range: **3.4-5.8 seconds**
- Average RMS level: **-31.1 dBFS**
- Peak level range: **-15.7 to -5.3 dBFS**

## Automatic checks

- `speaker01_0004.m4a`: low peak level; low average level; long trailing silence
- `speaker01_0005.m4a`: low peak level
- `speaker01_0019.m4a`: low peak level; low average level; long trailing silence
- `speaker01_0020.m4a`: low peak level
- `speaker_0008.m4a`: rename to speaker01_0008.m4a

## Interpretation

These checks evaluate file completeness, decodability, duration, level, digital clipping, and approximate silence. They do not determine whether the spoken Yoruba matches the transcript or whether lexical tones are correct. Those require transcript review and phonetic analysis in the next stage.

Detailed measurements are available in `yoruba_calibration_audio_quality.csv`.
