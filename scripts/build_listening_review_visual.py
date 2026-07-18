import argparse
import base64
import csv
import json
import subprocess
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--output", default="yoruba-listening-review.html")
parser.add_argument("--ids", default="0122,0101,0102,0103,0104")
parser.add_argument("--batch-label", default="first")
parser.add_argument("--compress-audio", action="store_true")
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
VIS = Path(r"C:\Users\adelu\.codex\visualizations\2026\07\18\019f7607-dbca-7b41-80e3-5ef365d625ae")
OUT = VIS / args.output
MANIFEST = ROOT / "work" / "yoruba_voice_benchmark_v0_1" / "benchmark_manifest.csv"
AUDIO_DIR = ROOT / "work" / "yoruba_voice_benchmark_v0_1" / "audio_wav_24k"
IDS = args.ids.split(",")

with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
    by_id = {row["prompt_id"]: row for row in csv.DictReader(handle)}

items = []
for prompt_id in IDS:
    row = by_id[prompt_id]
    wav = AUDIO_DIR / Path(row["audio_filename"]).name
    if args.compress_audio:
        compressed_dir = ROOT / "work" / "listening_review_mp3"
        compressed_dir.mkdir(parents=True, exist_ok=True)
        audio_path = compressed_dir / f"{prompt_id}.mp3"
        ffmpeg = ROOT / "work" / "ffmpeg_batch2.exe"
        result = subprocess.run(
            [str(ffmpeg), "-v", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "24000", "-b:a", "64k", str(audio_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        mime = "audio/mpeg"
    else:
        audio_path = wav
        mime = "audio/wav"
    encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    items.append({
        "id": prompt_id,
        "yoruba": row["yoruba"],
        "english": row["english_meaning"],
        "audio": f"data:{mime};base64,{encoded}",
    })

data = json.dumps(items, ensure_ascii=False)

fragment = f'''<div id="yoruba-listening-review">
  <div class="viz-row" aria-live="polite">
    <span class="viz-badge" id="review-progress">1 of {len(IDS)}</span>
    <span class="text-muted text-small" id="review-id">Recording 0122</span>
  </div>

  <section class="card" aria-labelledby="review-yoruba">
    <h2 id="review-yoruba"></h2>
    <p class="text-muted" id="review-english"></p>
    <audio id="review-audio" controls preload="metadata" style="width:100%"></audio>

    <div class="viz-controls" aria-label="Transcript match">
      <label class="form-label" for="match-select">Does the recording match the Yoruba sentence?</label>
      <select class="form-select" id="match-select">
        <option value="">Choose</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
        <option value="unsure">Unsure</option>
      </select>
    </div>

    <div class="viz-controls" aria-label="Pronunciation naturalness">
      <label class="form-label" for="natural-select">Does the pronunciation sound natural?</label>
      <select class="form-select" id="natural-select">
        <option value="">Choose</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
        <option value="unsure">Unsure</option>
      </select>
    </div>

    <label class="form-label" for="review-notes">Correction or note</label>
    <textarea class="form-control" id="review-notes" rows="2"></textarea>
  </section>

  <div class="viz-controls">
    <button type="button" class="btn" id="review-prev"><i data-lucide="chevron-left" aria-hidden="true"></i> Previous</button>
    <button type="button" class="btn btn-primary" id="review-next">Save and next <i data-lucide="chevron-right" aria-hidden="true"></i></button>
    <button type="button" class="btn" id="review-send">Send completed answers to Codex</button>
  </div>

  <p class="text-small text-muted" id="review-status">Listen once or twice, then choose your answers.</p>

  <script>
    (() => {{
      const root = document.getElementById('yoruba-listening-review');
      const items = {data};
      const answers = Object.fromEntries(items.map(item => [item.id, {{ match: '', natural: '', notes: '' }}]));
      let index = 0;

      const el = id => root.querySelector('#' + id);
      const progress = el('review-progress');
      const idLabel = el('review-id');
      const yoruba = el('review-yoruba');
      const english = el('review-english');
      const audio = el('review-audio');
      const match = el('match-select');
      const natural = el('natural-select');
      const notes = el('review-notes');
      const prev = el('review-prev');
      const next = el('review-next');
      const send = el('review-send');
      const status = el('review-status');

      function saveCurrent() {{
        const item = items[index];
        answers[item.id] = {{ match: match.value, natural: natural.value, notes: notes.value.trim() }};
      }}

      function render() {{
        const item = items[index];
        const answer = answers[item.id];
        progress.textContent = `${{index + 1}} of ${{items.length}}`;
        idLabel.textContent = `Recording ${{item.id}}`;
        yoruba.textContent = item.yoruba;
        english.textContent = item.english;
        audio.src = item.audio;
        match.value = answer.match;
        natural.value = answer.natural;
        notes.value = answer.notes;
        prev.disabled = index === 0;
        next.innerHTML = index === items.length - 1 ? 'Save answer' : 'Save and next <i data-lucide="chevron-right" aria-hidden="true"></i>';
        status.textContent = 'Listen once or twice, then choose your answers.';
        if (window.lucide) window.lucide.createIcons({{ attrs: {{ width: 16, height: 16 }} }});
      }}

      prev.addEventListener('click', () => {{
        saveCurrent();
        if (index > 0) index -= 1;
        render();
      }});

      next.addEventListener('click', () => {{
        saveCurrent();
        if (index < items.length - 1) {{
          index += 1;
          render();
        }} else {{
          status.textContent = 'This review batch is saved in the tool. Send the answers when ready.';
        }}
      }});

      send.addEventListener('click', async () => {{
        saveCurrent();
        const incomplete = items.filter(item => !answers[item.id].match || !answers[item.id].natural);
        if (incomplete.length) {{
          status.textContent = `Please answer both questions for: ${{incomplete.map(item => item.id).join(', ')}}.`;
          return;
        }}
        const lines = items.map(item => {{
          const a = answers[item.id];
          return `${{item.id}}: transcript=${{a.match}}, natural=${{a.natural}}, notes=${{a.notes || 'none'}}`;
        }});
        const prompt = `Listening verification results for the {args.batch_label} Yoruba review batch:\\n${{lines.join('\\n')}}\\nPlease record these results in the alignment package and tell me what needs correction or re-recording.`;
        if (window.openai && window.openai.sendFollowUpMessage) {{
          await window.openai.sendFollowUpMessage({{ prompt, title: 'Send listening-review results?' }});
          status.textContent = 'Results sent to Codex.';
        }} else {{
          status.textContent = 'Sending is unavailable here. Copy your five answers into the chat.';
        }}
      }});

      render();
    }})();
  </script>
</div>
'''

root_id = OUT.stem
fragment = fragment.replace("yoruba-listening-review", root_id)
OUT.write_text(fragment, encoding="utf-8")
print(OUT)
print(OUT.stat().st_size)
