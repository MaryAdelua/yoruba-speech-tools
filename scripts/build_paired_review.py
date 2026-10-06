"""Render exploratory native-listener forms; never change recordings or infer ratings."""
import hashlib,html,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/slr86/paired-ai-001'
COMMON=['natural/acceptable','somewhat unnatural','clearly problematic','cannot determine']
RATINGS={'lexical_tone_realization':COMMON,'segmental_pronunciation':COMMON,'perceived_nasality':['normal','somewhat excessive/unusual','clearly excessive/unusual','cannot determine'],'prosody_intonation':COMMON,'rhythm_fluency':COMMON,'overall_yoruba_naturalness':['natural','mostly natural','noticeably unnatural','very unnatural','cannot determine'],'reviewer_confidence':['low','medium','high']}
TAGS=['e/ẹ','o/ọ','s/ṣ','lexical tone','nasal quality','consonant realization','vowel realization','unusual duration/stretching','rhythm','intonation/prosody','other']
def build():
 proposals=json.loads((ROOT/'work/slr86/natural-baseline-001/qc-ingest-001/paired_sentence_proposals.json').read_text(encoding='utf-8'))['items']
 generations=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf-8'))
 items=[]
 for i,s in enumerate(proposals,1):
  natural=ROOT/s['audio_path'];assert hashlib.sha256(natural.read_bytes()).hexdigest()==s['audio_sha256']
  ai=[]
  for g in generations:
   if g['source_id']!=s['source_id']:continue
   path=ROOT/g['audio_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==g['audio_sha256']
   ai.append({'ai_generation_id':g['generation_id'],'repeat_generation_id':g['repeat_generation_id'],'model_snapshot':g['requested_model_snapshot'],'provider':g['provider'],'voice':g['request']['voice'],'voice_version':g['voice_version'],'audio_url':'audio/'+path.name,'audio_sha256':g['audio_sha256'],'duration_s':g['duration_s']})
  assert len(ai)==2
  items.append({'sentence_id':f'p{i:02d}','source_clip_id':s['source_id'],'speaker_id':s['speaker_id'],'exact_text':s['exact_yoruba_text'],'natural_audio_url':'../audio/'+natural.name,'natural_audio_sha256':s['audio_sha256'],'natural_duration_s':s['duration_s'],'ai_generations':ai})
 data={'schema_version':'paired-native-review-1.0','study_type':'exploratory_unblinded_paired_review','items':items,'rating_options':RATINGS,'issue_tags':TAGS}
 (OUT/'review_form_definition.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Structured paired Yorùbá review</title><style>
body{font:16px system-ui;max-width:1400px;margin:auto;padding:24px;background:#f3f5f7;color:#172331}header,article{background:white;border:1px solid #ccd4de;border-radius:12px;padding:22px;margin-bottom:24px}h1{margin-top:0}.text{font-size:25px}.players,.forms{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.forms{grid-template-columns:repeat(2,minmax(0,1fr))}audio{width:100%}fieldset{min-width:0;border:1px solid #ccd4de;border-radius:8px;padding:16px}label{display:block;margin:12px 0}select,input,textarea,button{font:inherit;padding:8px;box-sizing:border-box}select,textarea{width:100%}textarea{min-height:80px}button{cursor:pointer}legend{font-weight:700}.tags{display:flex;gap:4px 12px;flex-wrap:wrap}.tags label{margin:4px 0}.interval{display:grid;grid-template-columns:1fr 1fr 2fr auto;gap:8px;align-items:end}.interval input{width:100%}small{color:#435267}.natural{margin:18px 0;padding:16px;background:#f5f7fa}#status{padding:10px 0}#export{background:#174b73;color:white;border:0;border-radius:6px}@media(max-width:800px){.players,.forms{grid-template-columns:1fr}.interval{grid-template-columns:1fr 1fr}body{padding:10px}}
</style><header><h1>Structured paired Yorùbá listening review</h1><p>Exploratory, unblinded native-listener review—not the final blinded perceptual study. Rate each AI generation separately. Natural references are not perfect or exclusive pronunciation standards.</p><p>These are human perceptions, not acoustically proven diagnoses. Dimensions remain separate; no combined score or automated correctness inference is produced. No training uses these annotations.</p><label>Reviewer identifier<input id="reviewer" autocomplete="off" placeholder="Name or pseudonym" required></label><button id="export" type="button">Export Review JSON</button><div id="status" role="status">Draft autosaves in this browser when available. Export JSON to keep a portable copy.</div><p><small>Blank means not reviewed; “cannot determine” is an explicit judgment. Intervals are seconds in the particular recording. Original audio plays without trimming or gain normalization.</small></p></header><main id="items"></main><script id="definition" type="application/json">'''+encoded+'''</script><script src="structured_review.js"></script></html>'''
 (OUT/'listening_review.html').write_text(page,encoding='utf-8')
 (OUT/'structured_review.js').write_text((ROOT/'src/paired_review.js').read_text(encoding='utf-8'),encoding='utf-8')
 print('Structured forms rendered: 6 natural notes sections, 12 independent AI annotation forms. All 18 audio hashes unchanged.')
if __name__=='__main__':build()
