from faster_whisper import WhisperModel

model = WhisperModel('small', device='cpu', compute_type='int8')

expected = {
    'YT0028': 'Ẹlẹ́dẹ̀ náà sáré kọjá ọgbà.',
    'YT0029': 'Afẹ́fẹ́ tútù ń fẹ́ láti ìlà-oòrùn.',
    'YT0030': 'Ọ̀rẹ́ rẹ̀ fi ìwé sí orí àpótí.',
}

for pid, text in expected.items():
    path = f'condition_c_results/condition_c_{pid}.wav'
    segments, info = model.transcribe(
        path, language='yo', beam_size=1, condition_on_previous_text=False,
        no_speech_threshold=0.6,
    )
    transcript = ' '.join(seg.text for seg in segments).strip()
    print(f'{pid} expected: {text}', flush=True)
    print(f'{pid} whisper:  {transcript!r} (lang_prob={info.language_probability:.2f})', flush=True)
    print(flush=True)

path = 'condition_c_results/condition_c_baseline_english.wav'
segments, info = model.transcribe(path, language='en', beam_size=1, condition_on_previous_text=False, no_speech_threshold=0.6)
transcript = ' '.join(seg.text for seg in segments).strip()
print(f'baseline expected: This is the voice model before any Yoruba training.')
print(f'baseline whisper:  {transcript!r} (lang_prob={info.language_probability:.2f})')
