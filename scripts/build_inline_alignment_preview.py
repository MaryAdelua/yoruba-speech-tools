"""Build the thread-scoped one-item inline review preview."""

from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIS = Path(r"C:\Users\adelu\.codex\visualizations\2026\07\18\019f7607-dbca-7b41-80e3-5ef365d625ae\yoruba-alignment-review.html")


def main() -> None:
    record = json.loads((ROOT / "alignment/automatic/omnilingual_ctc_training_batch_01.jsonl").read_text(encoding="utf-8").splitlines()[0])
    audio = base64.b64encode((ROOT / record["audio_path"]).read_bytes()).decode("ascii")
    words = json.dumps(record["words"], ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__TEXT__", record["text_nfc"]).replace("__AUDIO__", audio).replace("__WORDS__", words).replace("__DURATION__", str(record["duration_s"]))
    VIS.write_text(html, encoding="utf-8", newline="\n")
    print(VIS, VIS.stat().st_size)


TEMPLATE = r'''<style>.ya{font:15px/1.4 system-ui;color:#14213d;background:#f8fafc;padding:20px;border-radius:16px}.ya h2{margin:0 0 5px}.ya .muted{color:#64748b}.ya .card{background:white;border:1px solid #dbe3ec;border-radius:12px;padding:16px;margin-top:14px}.ya canvas{width:100%;height:190px;background:#f8fafc;border-radius:9px;touch-action:none}.ya audio{width:100%}.ya .row{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:8px;align-items:center;margin:6px 0}.ya input{width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:7px}.ya button{background:#0f766e;color:white;border:0;border-radius:8px;padding:9px 13px;font-weight:700}.ya .gold{color:#92400e;font-weight:700}</style><section class="ya"><h2>Yoruba alignment review — YT0001</h2><div class="muted">Interactive preview. Automatic boundaries are suggestions; export is a separate human record.</div><div class="card"><div style="font-size:24px;font-weight:700">__TEXT__</div><audio controls src="data:audio/wav;base64,__AUDIO__"></audio><canvas id="yac" width="950" height="190"></canvas><div class="muted">Drag a gold boundary, then confirm the numbers below.</div></div><div class="card" id="yar"></div><div class="card"><label>Reviewer <input id="yarev" value="Mary Adelua"></label> <button id="yaexp">Export this verified correction</button> <span id="yast" class="gold"></span></div></section><script>const yaw=__WORDS__,yad=__DURATION__,yac=document.getElementById('yac'),yax=yac.getContext('2d');function yarender(){document.getElementById('yar').innerHTML=yaw.map((w,i)=>`<div class="row"><b>${w.text}</b><label>Start <input data-i="${i}" data-k="start_s" type="number" step=".01" value="${Number(w.start_s??0).toFixed(3)}"></label><label>End <input data-i="${i}" data-k="end_s" type="number" step=".01" value="${Number(w.end_s??.2).toFixed(3)}"></label></div>`).join('');document.querySelectorAll('#yar input').forEach(e=>e.onchange=()=>{yaw[+e.dataset.i][e.dataset.k]=+e.value;yadraw()});yadraw()}function yadraw(){yax.clearRect(0,0,yac.width,yac.height);yax.fillStyle='#e2e8f0';for(let i=0;i<190;i+=10)yax.fillRect(0,i,yac.width,1);yaw.forEach((w,i)=>{const p=(w.start_s??0)/yad*yac.width;yax.strokeStyle='#f59e0b';yax.beginPath();yax.moveTo(p,0);yax.lineTo(p,190);yax.stroke();yax.fillStyle='#14213d';yax.fillText(w.text,p+4,15+(i%2)*15)})}let yadr=null;yac.onpointerdown=e=>{const q=e.offsetX/yac.clientWidth*yad;let b={d:99};yaw.forEach((w,i)=>['start_s','end_s'].forEach(k=>{let d=Math.abs((w[k]??0)-q);if(d<b.d)b={d,i,k}}));yadr=b};yac.onpointermove=e=>{if(!yadr)return;yaw[yadr.i][yadr.k]=Math.max(0,Math.min(yad,e.offsetX/yac.clientWidth*yad));yadraw()};yac.onpointerup=()=>{yadr=null;yarender()};document.getElementById('yaexp').onclick=()=>{let p=0,ok=true;yaw.forEach(w=>{if((w.start_s??0)<p||(w.end_s??0)<=w.start_s||(w.end_s??0)>yad)ok=false;p=w.end_s});if(!ok){document.getElementById('yast').textContent=' Fix invalid or overlapping times.';return}const row={schema_version:'0.1',prompt_id:'YT0001',review_status:'human_verified',reviewer:document.getElementById('yarev').value,reviewed_at:new Date().toISOString(),automatic_alignment_method:'omnilingual_asr_ctc_token_match_v0.1',words:yaw},blob=new Blob([JSON.stringify(row)+'\n'],{type:'application/jsonl'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='YT0001-manual-alignment.jsonl';a.click();document.getElementById('yast').textContent=' Exported separately.'};yarender();</script>'''

if __name__ == "__main__":
    main()
