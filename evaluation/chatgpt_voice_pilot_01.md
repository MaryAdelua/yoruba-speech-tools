# ChatGPT Voice pilot 01

## Objective

Test ChatGPT Voice on ten meaning-sensitive Yoruba sentences drawn from four controlled tone-contrast families: `oko`, `owo`, `igba`, and `ẹkọ`.

## Keep these settings fixed

- Product: ChatGPT Voice on `chatgpt.com`
- Voice option: record the selected voice name
- Voice mode: record whether ChatGPT shows Live, Advanced, or Standard
- Account plan: record Free, Plus, Pro, or another plan
- Date: record the generation date
- Do not change the voice or mode during the pilot

## Exact prompt to paste into ChatGPT

Read each Yoruba sentence below exactly as written. Speak only the Yoruba sentences. Do not translate them, explain them, announce numbers, or add any words. Pause silently for three seconds after each sentence before reading the next sentence. Preserve every Yoruba vowel and tone mark.

Mo rí ọkọ̀ tuntun ní òpópónà.

Ọdẹ náà gbé ọ̀kọ̀ rẹ̀.

Ọkọ Adé dé láti ibise.

Bàbá mi lọ sí oko ní òwúrọ̀.

Mo fi owó ra oúnjẹ.

Fọ ọwọ́ rẹ kí o tó jẹun.

Ìgbà wo ni o máa dé?

Ìyá fi omi sínú igbá.

Mo kọ́ ẹ̀kọ́ tuntun lónìí.

Ọmọ náà jẹ ẹ̀kọ ní òwúrọ̀.

## Windows capture workflow

1. Open ChatGPT in a desktop browser and start a new chat.
2. Select one ChatGPT voice and keep it unchanged.
3. Paste the exact prompt above.
4. Before playing the spoken response, press `Windows + G` to open Xbox Game Bar.
5. In the Capture panel, start recording. Ensure system audio is included.
6. Play or request the ChatGPT spoken response.
7. Let all ten sentences finish, then stop recording.
8. Upload the resulting video file to Codex. Codex will extract the audio, split the ten sentences, standardize the files, and run the benchmark checks.

Do not use a microphone recording of the computer speaker unless system-audio capture is unavailable; that would mix room acoustics and microphone noise into the model evaluation.

## Expected order and filenames after segmentation

| Order | Prompt ID | Output filename |
|---:|---:|---|
| 1 | 0101 | `0101.wav` |
| 2 | 0102 | `0102.wav` |
| 3 | 0103 | `0103.wav` |
| 4 | 0104 | `0104.wav` |
| 5 | 0105 | `0105.wav` |
| 6 | 0106 | `0106.wav` |
| 7 | 0107 | `0107.wav` |
| 8 | 0108 | `0108.wav` |
| 9 | 0142 | `0142.wav` |
| 10 | 0143 | `0143.wav` |
