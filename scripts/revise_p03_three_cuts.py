"""Revise only trailing playback context of three listener-flagged natural cuts."""
import json,wave,hashlib,datetime,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'work/slr86';OLD=B/'p03-mms-alignment-001';OUT=B/'p03-three-cut-revision-001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True)
 data=json.loads((OLD/'alignment.json').read_text(encoding='utf-8'));r=next(x for x in data['records'] if x['id']=='p03_natural')
 all_old={str(p):sha(p) for p in OLD.rglob('*.wav')}
 src=B/'audio/yof_02121_01178327964.wav';source_sha=sha(src)
 with wave.open(str(src),'rb') as w:params=w.getparams();sr=w.getframerate();width=w.getnchannels()*w.getsampwidth();raw=w.readframes(w.getnframes())
 items=[]
 for old in r['items']:
  if old['id'] not in ['w03','w06','w07']:continue
  # Retain model-aligned word extent, reduce only the unverified trailing context to 10 ms.
  first=round(old['playback_start_s']*sr);last=round((old['ctc_end_s']+.010)*sr)
  assert first<last<round(old['playback_end_s']*sr)
  name=old['id']+'_revised.wav';chunk=raw[first*width:last*width]
  with wave.open(str(OUT/name),'wb') as w:w.setparams(params);w.setnframes(last-first);w.writeframes(chunk)
  with wave.open(str(OUT/name),'rb') as w:assert w.readframes(w.getnframes())==chunk
  items.append({'id':old['id'],'written_unit':old['written_unit'],'source_recording':'p03_natural','source_audio_sha256':source_sha,'previous_audio':'../p03-mms-alignment-001/'+old['audio_file'],'previous_audio_sha256':sha(OLD/old['audio_file']),'audio_file':name,'audio_sha256':sha(OUT/name),'previous_start_s':old['playback_start_s'],'previous_end_s':old['playback_end_s'],'playback_start_s':first/sr,'playback_end_s':last/sr,'removed_trailing_context_s':old['playback_end_s']-last/sr,'ctc_start_s':old['ctc_start_s'],'ctc_end_s':old['ctc_end_s'],'measurements':old['measurements'],'status':'REVISED_PROPOSAL_AWAITING_LISTENING_CHECK','reason':'Native listener reports following-word overlap. Reduced trailing playback context; model alignment itself unchanged. CTC extent may still be imperfect; no claim of verified linguistic boundary.','confidence':None})
 assert sha(src)==source_sha and all(sha(Path(p))==h for p,h in all_old.items())
 report={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'items':items,'method':'Exact original PCM slice with same start and shorter playback end, retaining CTC extent plus 10ms. No gain, resampling, denoising or time change.','original_audio_preserved':True,'all_previous_50_cuts_preserved':True,'accepted_cuts_changed':False,'acoustic_features_recomputed':False,'scores':'UNIMPLEMENTED','script_sha256':sha(Path(__file__))}
 (OUT/'revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 page='<meta charset="utf-8"><title>Three revised natural-word cuts</title><style>body{font:21px system-ui;max-width:800px;margin:35px auto;padding:20px}article{border:1px solid #cbd5df;padding:20px;margin:18px 0;border-radius:12px}audio{width:100%}small{color:#46576a}</style><h1>Check only these three cuts</h1><p>The seven accepted cuts are unchanged. These versions have a slightly shorter ending to reduce the following-word overlap you reported.</p><p>For each: does it contain the whole displayed word without part of the next one? Say usable, still overlaps, cut off, or unsure. No tone or pronunciation grading yet.</p><details><summary>Full natural sentence for context</summary><audio controls preload="none" src="../audio/yof_02121_01178327964.wav"></audio></details>'
 for item in items:
  label=item['written_unit']+(' (later occurrence)' if item['id']=='w07' else '')
  page+=f'<article><h2 lang="yo">{html.escape(label)}</h2><p>Revised cut</p><audio controls preload="metadata" src="{item["audio_file"]}"></audio><details><summary>Previous cut for comparison</summary><audio controls preload="none" src="{item["previous_audio"]}"></audio></details></article>'
 page+='<p><small>These remain proposals. Original recordings, earlier cuts, measurements and your prior feedback are preserved. Spoken judgments are saved by the assistant only when confirmed as saved; this page does not record your voice.</small></p>'
 (OUT/'index.html').write_text(page,encoding='utf-8')
 print(json.dumps({'cuts':[{k:i[k] for k in ['written_unit','playback_start_s','playback_end_s','removed_trailing_context_s']} for i in items],'previous_audio_checks':len(all_old),'original_unchanged':True},ensure_ascii=False))
if __name__=='__main__':main()
