"""Analyze only successfully generated new conditions; reuse validated instruments."""
import json,sys,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from analyze_paired_ai import metrics
from validate_acoustic_measurements import compare,csvout,PRAAT
from build_natural_baseline import dump
import soundfile as sf
BASE=ROOT/'work/slr86';OUT=BASE/'paired-new-models-001'
def main():
 allrecords=[];rows=[]
 for manifest in sorted(OUT.glob('*/generation_manifest.json')):
  for r in json.loads(manifest.read_text(encoding='utf-8')):
   path=ROOT/r['audio_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['audio_sha256']
   d=manifest.parent/'measurements'/r['generation_id'];d.mkdir(parents=True,exist_ok=True)
   if (d/'raw.json').exists():obj=json.loads((d/'raw.json').read_text(encoding='utf-8'));assert obj['report']['source']['sha256']==r['audio_sha256']
   else:
    sr=sf.info(path).samplerate;report,frames,raw,_=compare(path,frame_length=2*round((2048/24000)*sr/2))
    for f in frames:
     flags=f['flags'].split('|') if f['flags'] else []
     if f['edge_padded']:flags.append('edge_window')
     if f['f0_hz'] and f['f0_hz']>=500/1.05:flags.append('near_pyin_ceiling')
     if f['praat_f0_hz'] and (f['praat_f0_hz']<=65*1.05 or f['praat_f0_hz']>=500/1.05):flags.append('praat_near_search_limit')
     f['agreement_screen_pass']=bool(f['f0_hz'] and f['praat_f0_hz'] and not flags and f['voicing_probability']>=.5 and f['praat_strength']>=.45 and abs(f['signed_difference_semitones'])<=.5)
     f['flags']='|'.join(flags)
    obj={'report':report,'frames':frames,'praat_native_frames':raw};dump(d/'raw.json',obj)
   m=metrics(obj['frames'],obj['praat_native_frames'],r['duration_s'])
   dump(d/'analysis.json',{'generation':r,'measurements':m,'praat_settings':PRAAT,'normalization':'12*log2(F0/own utterance voiced median), separately per estimator; not tone labels','all_correctness_scores':'UNIMPLEMENTED'})
   csvout(d/'frames.csv',obj['frames']);csvout(d/'praat_native_frames.csv',obj['praat_native_frames'])
   rows.append({'generation_id':r['generation_id'],'model':r['requested_model_snapshot'],'duration_s':r['duration_s'],'pyin_median_hz':m['pyin_f0_hz']['median'],'praat_median_hz':m['praat_native_f0_hz']['median'],'voiced_percent':m['pyin_voiced_percent'],'voicing_disagreement_percent':m['voicing_disagreement_percent']});allrecords.append(r);print('Analyzed '+r['generation_id'],flush=True)
 csvout(OUT/'acoustic_summary.csv',rows)
 definition=json.loads((BASE/'paired-ai-001/review_form_definition.json').read_text(encoding='utf-8'))
 baseline=json.loads((BASE/'paired-ai-001/generation_manifest.json').read_text(encoding='utf-8'))
 for s in definition['items']:
  s['ai_generations']=[{'ai_generation_id':r['generation_id'],'repeat_generation_id':r['repeat_generation_id'],'model_snapshot':r['requested_model_snapshot'],'provider':'OpenAI','voice':r['request']['voice'],'voice_version':None,'audio_url':str((ROOT/r['audio_path']).relative_to(OUT)).replace('\\','/'),'audio_sha256':r['audio_sha256'],'duration_s':r['duration_s']} for r in allrecords if r['source_id']==s['source_clip_id']]
 definition.update(review_version=1,review_session_id='paired_new_models_001',conditions=['natural','gpt-4o-mini-tts','gpt-realtime-2.1','gpt-live-1 (blocked: HTTP 403)'])
 dump(OUT/'review_form_definition.json',definition)
 page=(BASE/'paired-ai-001/paired_native_listener_review_v2.html').read_text(encoding='utf-8')
 start=page.index('<script id="definition"');end=page.index('</script>',start)
 page=page[:start]+'<script id="definition" type="application/json">'+json.dumps(definition,ensure_ascii=False).replace('<','\\u003c')+page[end:]
 page=page.replace('structured_review_v2.js','review.js').replace('Paired native-listener review v2','New speech conditions review').replace('<main id="items">','<p>New condition: gpt-realtime-2.1 / marin. GPT-Live is unavailable: HTTP 403 before session start. Previous baseline ratings stay in their accepted v2 export. Model and voice effects are confounded against coral. Exact spoken content still needs listening verification.</p><main id="items">')
 js=(BASE/'paired-ai-001/structured_review_v2.js').read_text(encoding='utf-8').replace('yoruba-paired-native-review-v2:','yoruba-new-models-001:').replace('paired_native_listener_review_v2','paired_new_models_001').replace('review_version:2','review_version:1')
 js=js.replace("'AI generation '+g.repeat_generation_id","g.model_snapshot+' · take '+g.repeat_generation_id")
 # Existing accepted mini-TTS audio is read-only context, not a fresh annotation condition.
 extra={s['sentence_id']:[{'url':'../paired-ai-001/audio/'+Path(r['audio_path']).name,'repeat':r['repeat_generation_id']} for r in baseline if r['source_id']==s['source_clip_id']] for s in definition['items']}
 js+='\nconst baselineAudio='+json.dumps(extra)+'; for(const [sid,clips] of Object.entries(baselineAudio)){const box=document.createElement("section");box.innerHTML="<h3>Existing gpt-4o-mini-tts / coral baseline (accepted v2 review preserved)</h3>"+clips.map(c=>`<p>Take ${c.repeat}</p><audio controls preload="none" src="${c.url}"></audio>`).join("");document.querySelector(`[data-sentence="${sid}"]`).appendChild(box);}\n'
 (OUT/'listening_review.html').write_text(page,encoding='utf-8');(OUT/'review.js').write_text(js,encoding='utf-8')
 dump(OUT/'run_status.json',{'gpt-realtime-2.1':{'generated':len(allrecords),'analyzed':len(rows)},'gpt-live-1':{'generated':0,'status':'BLOCKED','http_status':403,'reason':'Forbidden before WebSocket session; repeated connection-only check also 403'},'audio_modified':False,'training':False,'correctness_scores':'UNIMPLEMENTED'})
if __name__=='__main__':main()
