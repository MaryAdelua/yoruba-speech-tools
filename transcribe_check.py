from faster_whisper import WhisperModel

model = WhisperModel('small', device='cpu', compute_type='int8')

expected = {
    'YT0028': 'Ẹlẹ́dẹ̀ náà sáré kọjá ọgbà.',
    'YT0029': 'Afẹ́fẹ́ tútù ń fẹ́ láti ìlà-oòrùn.',
    'YT0030': 'Ọ̀rẹ́ rẹ̀ fi ìwé sí orí àpótí.',
}

files = {
    'Condition B (fine-tuned)': 'condition_b_results/speaker01_{}.wav',
    'Condition A (baseline)': 'condition_b_results/condition_a_baseline/condition_a_{}.wav',
}

for label, pattern in files.items():
    print(f'=== {label} ===', flush=True)
    for pid, text in expected.items():
        path = pattern.format(pid)
        segments, info = model.transcribe(
            path, language='yo', beam_size=1, condition_on_previous_text=False,
            no_speech_threshold=0.6,
        )
        transcript = ' '.join(seg.text for seg in segments).strip()
        print(f'{pid} expected: {text}', flush=True)
        print(f'{pid} whisper:  {transcript!r} (lang_prob={info.language_probability:.2f})', flush=True)
    print(flush=True)
