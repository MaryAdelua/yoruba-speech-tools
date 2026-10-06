"""Bounded cross-condition descriptive analysis. No fitting or correctness score."""
import argparse,collections,hashlib,importlib.metadata,json,os,shutil,sys,datetime
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from explore_human_acoustics import describe,DIMS
from build_natural_baseline import dist,dump
from validate_acoustic_measurements import csvout
B=ROOT/'work/slr86';OUT=B/'cross-model-comparison-001'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CONFIG={'version':'cross-model-descriptive-1.0','conditions':['natural','mini_tts','realtime'],'amplitude':'Whole-file digital RMS = 20 log10(sqrt(mean(sample^2))); no gain normalization. Not calibrated SPL or perceptual loudness.','active_proxy':'Nonoverlapping 20-ms blocks above -50/-40/-30 dBFS; sample-weighted duration and RMS, no trimming of audio. Not validated speech activity detection.','speaking_duration':'Unavailable without verified speech boundaries; report voiced frame-cell duration and threshold sensitivity only.','normalization':'Existing 12*log2(F0/own-utterance voiced median), separately per estimator. Not speaker population normalization or lexical-tone correctness.','aggregation':'Six sentence means per AI condition (two takes each); natural has one recording per sentence. No independent N=24 claim.','confounds':['Model and voice change together: coral versus marin','Different endpoint/instructions and uncontrolled synthesis calibration','Natural speakers/channels differ','One unblinded listener, six repeated texts','Matching repeat numbers across models is bookkeeping, not shared seeds'],'no_training':True,'no_combined_or_correctness_score':True}
def amplitude(path,frames):
 y,sr=sf.read(path,always_2d=True);assert y.shape[1]==1 and np.isfinite(y).all();y=y[:,0]
 def db(x):return float(10*np.log10(np.mean(x*x))) if len(x) and np.any(x) else None
 out={'whole_rms_dbfs':db(y),'peak_dbfs':float(20*np.log10(np.max(abs(y)))),'digital_rail_samples':int(np.sum((y>=32767/32768)|(y<=-1))),'verified_speaking_duration_s':None}
 out['crest_factor_db']=out['peak_dbfs']-out['whole_rms_dbfs']
 block=max(1,round(sr*.02));blocks=[y[i:i+block] for i in range(0,len(y),block)];levels=[db(x) for x in blocks]
 out['active_block_rms_width90_db']=float(np.percentile([l for l in levels if l is not None and l>-40],95)-np.percentile([l for l in levels if l is not None and l>-40],5)) if any(l is not None and l>-40 for l in levels) else None
 for threshold in [-50,-40,-30]:
  active=[x for x,l in zip(blocks,levels) if l is not None and l>threshold];label='active_above_'+str(abs(threshold))
  out[label+'_s']=sum(len(x) for x in active)/sr;out[label+'_rms_dbfs']=db(np.concatenate(active)) if active else None
 times=np.array([f['timestamp_s'] for f in frames]);edges=np.r_[0,(times[:-1]+times[1:])/2,len(y)/sr];edges=np.clip(edges,0,len(y)/sr)
 out['pyin_voiced_duration_proxy_s']=float(sum(b-a for a,b,f in zip(edges[:-1],edges[1:],frames) if f['voiced']))
 out['median_frame_rms_dbfs']=dist([f['rms_dbfs'] for f in frames])['median']
 return out

def main(reviewpath):
 new=read(reviewpath);assert new['review_session_id']=='paired_new_models_001' and new['review_version']==1 and new['reviewer_identifier'].strip()
 oldpath=B/'paired-ai-001/human-acoustic-v2/review.original.json';old=read(oldpath);assert old['review_version']==2
 qcpath=B/'natural-baseline-001/qc-ingest-v2/qc_review_joined.json';qc={r['source_id']:r for r in read(qcpath)}
 defs=read(B/'paired-ai-001/review_form_definition.json');byid={s['sentence_id']:s for s in defs['items']}
 manifests={'mini_tts':B/'paired-ai-001/generation_manifest.json','realtime':B/'paired-new-models-001/gpt-realtime-2.1/generation_manifest.json'}
 inputs=[reviewpath,oldpath,qcpath,B/'paired-ai-001/review_form_definition.json',*manifests.values()];records=[];annotations=[];natural_notes=[]
 for condition,review in [('mini_tts',old),('realtime',new)]:
  gens={g['generation_id']:g for g in read(manifests[condition])};seen=set();assert {s['sentence_id'] for s in review['items']}==set(byid) and len(review['items'])==6
  for s in review['items']:
   ref=byid[s['sentence_id']];assert s['source_clip_id']==ref['source_clip_id'] and s['exact_yoruba_text']==ref['exact_text'];assert s['natural_reference']['audio_sha256']==ref['natural_audio_sha256']
   natural_notes.append({'session':condition,'sentence_id':s['sentence_id'],'annotation':s['natural_reference']})
   assert len(s['ai_annotations'])==2
   for a in s['ai_annotations']:
    gid=a['ai_generation_id'];assert gid in gens and gid not in seen;seen.add(gid);g=gens[gid]
    assert g['source_id']==a['source_clip_id']==ref['source_clip_id'];assert a['sentence_id']==s['sentence_id'];assert a['reviewer_identifier']==review['reviewer_identifier'];assert a['annotation_timestamp'] and a['review_status']=='dimensions_completed'
    for k,v in [('model_snapshot',g['requested_model_snapshot']),('voice',g['request']['voice']),('provider',g['provider']),('audio_sha256',g['audio_sha256']),('repeat_generation_id',g['repeat_generation_id'])]:assert a[k]==v
    for dim in DIMS:assert a['ratings'][dim] in defs['rating_options'][dim]
    assert set(a['issue_tags'])<=set(defs['issue_tags']);assert g['request']['input']==ref['exact_text']
    for t in a['problematic_time_intervals']:assert 0<=t['start_s']<t['end_s']<=g['duration_s']
    audio=ROOT/g['audio_path'];assert sha(audio)==g['audio_sha256']
    rawpath=manifests[condition].parent/'measurements'/gid/'raw.json';raw=read(rawpath);assert raw['report']['source']['sha256']==g['audio_sha256'];inputs.extend([audio,rawpath])
    m={**describe(raw,g['duration_s']),**amplitude(audio,raw['frames'])}
    r={'condition':condition,'sentence_id':s['sentence_id'],'source_id':g['source_id'],'generation_id':gid,'repeat':g['repeat_generation_id'],'exact_text':ref['exact_text'],'provenance':g,'human_annotation':a,'natural_qc_v2':qc[g['source_id']],'metrics':m};records.append(r)
    annotations.append({'condition':condition,'sentence_id':s['sentence_id'],'source_id':g['source_id'],'generation_id':gid,'exact_text':ref['exact_text'],'model':a['model_snapshot'],'voice':a['voice'],'reviewer':a['reviewer_identifier'],'annotation_timestamp':a['annotation_timestamp'],**a['ratings'],'issue_tags':json.dumps(a['issue_tags'],ensure_ascii=False),'notes':a['notes'],'intervals':json.dumps(a['problematic_time_intervals'],ensure_ascii=False)})
  assert seen==set(gens) and len(seen)==12
 for sid,s in byid.items():
  audio=B/'audio'/(s['source_clip_id']+'.wav');rawpath=B/'natural-baseline-001/clips'/s['source_clip_id']/'raw.json';raw=read(rawpath);assert sha(audio)==s['natural_audio_sha256']==raw['report']['source']['sha256'];inputs.extend([audio,rawpath])
  records.append({'condition':'natural','sentence_id':sid,'source_id':s['source_clip_id'],'generation_id':s['source_clip_id'],'repeat':None,'exact_text':s['exact_text'],'metrics':{**describe(raw,s['natural_duration_s']),**amplitude(audio,raw['frames'])},'natural_qc_v2':qc[s['source_clip_id']],'rating_status':'NOT_COLLECTED_FOR_THESE_DIMENSIONS; transcript match is not pronunciation rating'})
 OUT.mkdir(exist_ok=True)
 for name,p in [('realtime_review.original.json',reviewpath),('mini_tts_v2_review.original.json',oldpath)]:
  target=OUT/name
  if target.exists():assert target.read_bytes()==p.read_bytes(),'Use a new analysis revision'
  else:shutil.copyfile(p,target)
 dump(OUT/'config.json',CONFIG);dump(OUT/'joined_cross_model.json',records);csvout(OUT/'joined_cross_model_ratings.csv',annotations);dump(OUT/'natural_reference_observations.json',natural_notes)
 scalar=[k for k,v in records[0]['metrics'].items() if not isinstance(v,(list,dict))]
 csvout(OUT/'cross_model_acoustics.csv',[{k:r[k] for k in ['condition','sentence_id','source_id','generation_id','repeat']}|{k:r['metrics'][k] for k in scalar}|{'reliability_flags':json.dumps(r['metrics']['flag_counts'])} for r in records])
 summary={};repeats=[];sentence=[]
 for condition in CONFIG['conditions']:
  subset=[r for r in records if r['condition']==condition];ann=[r for r in annotations if r['condition']==condition]
  summary[condition]={'n_recordings':len(subset),'total_duration_s':sum(r['metrics']['duration_s'] for r in subset),'rating_counts':{dim:dict(collections.Counter(a[dim] for a in ann)) for dim in DIMS} if ann else 'NOT_COLLECTED','issue_tags':dict(collections.Counter(t for r in subset for t in r.get('human_annotation',{}).get('issue_tags',[]))),'notes':[{'generation_id':a['generation_id'],'note':a['notes']} for a in ann if a['notes']],'clip_metric_distributions':{k:dist([r['metrics'][k] for r in subset]) for k in scalar},'flag_frame_counts':dict(sum((collections.Counter(r['metrics']['flag_counts']) for r in subset),collections.Counter()))}
  for sid in byid:
   group=[r for r in subset if r['sentence_id']==sid];means={k:float(np.mean([r['metrics'][k] for r in group if r['metrics'][k] is not None])) if any(r['metrics'][k] is not None for r in group) else None for k in scalar};sentence.append({'condition':condition,'sentence_id':sid,'n_takes':len(group),**means})
   if len(group)==2:
    a,b=sorted(group,key=lambda r:r['repeat']);repeats.append({'condition':condition,'sentence_id':sid,'rating_agreement':{dim:a['human_annotation']['ratings'][dim]==b['human_annotation']['ratings'][dim] for dim in DIMS},'tags_identical':set(a['human_annotation']['issue_tags'])==set(b['human_annotation']['issue_tags']),'absolute_metric_differences':{k:abs(a['metrics'][k]-b['metrics'][k]) if a['metrics'][k] is not None and b['metrics'][k] is not None else None for k in scalar}})
 dump(OUT/'review_and_acoustic_summary.json',summary);dump(OUT/'repeat_consistency.json',repeats);csvout(OUT/'sentence_level_comparison.csv',sentence)
 differences=[]
 for sid in byid:
  a=next(r for r in sentence if r['condition']=='mini_tts' and r['sentence_id']==sid);b=next(r for r in sentence if r['condition']=='realtime' and r['sentence_id']==sid)
  differences.append({'sentence_id':sid,**{k:b[k]-a[k] if a[k] is not None and b[k] is not None else None for k in scalar}})
 csvout(OUT/'sentence_realtime_minus_mini.csv',differences)
 dump(OUT/'paired_difference_summary.json',{k:{'sentence_mean_delta':dist([r[k] for r in differences]),'lower_in_n_sentences':sum(r[k]<0 for r in differences if r[k] is not None)} for k in scalar})
 dump(OUT/'human_style_observation.json',{'source':'User message, 2026-10-03 America/Chicago','text':'gpt-realtime-2.1 sounded CALMER and LESS LOUD than gpt-4o-mini-tts, without meaningful improvement in lexical tone, pronunciation, prosody, rhythm or overall Yoruba naturalness.','evidence_type':'human_listener_observation_not_acoustic_diagnosis'})
 os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'));import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(2,3,figsize=(15,8));keys=['whole_rms_dbfs','active_above_40_rms_dbfs','duration_s','pyin_voiced_duration_proxy_s','pyin_relative_width90_st','voicing_disagreement_percent']
 titles=['Whole-file RMS (dBFS)','RMS above −40 dBFS gate (sensitivity proxy)','File duration (s)','pYIN voiced duration (s; not speech duration)','Relative pitch 5–95% width (semitones)','pYIN/Praat voicing disagreement (%)']
 for ax,key,title in zip(axes.flat,keys,titles):
  for c,color in [('natural','#555555'),('mini_tts','#d4770c'),('realtime','#1675bd')]:
   values=[r[key] for r in sentence if r['condition']==c];ax.plot(range(1,7),values,'o-',label=c,color=color)
  ax.set(title=title,xlabel='Sentence');ax.grid(alpha=.2)
 axes[0,0].legend();fig.suptitle('Descriptive style comparison · AI points average two takes · no quality score');fig.tight_layout();fig.savefig(OUT/'style_comparison.png',dpi=140);plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(15,8))
 for ax,key in zip(axes.flat,['duration_s','whole_rms_dbfs','pyin_median_hz','pyin_relative_width90_st','voiced_runs_per_second','pitch_disagreement_median_st']):
  for c,color in [('mini_tts','#d4770c'),('realtime','#1675bd')]:ax.plot(range(1,7),[r['absolute_metric_differences'][key] for r in repeats if r['condition']==c],'o-',label=c,color=color)
  ax.set(title='Within-sentence |take 2 − take 1|: '+key,xlabel='Sentence');ax.grid(alpha=.2)
 axes[0,0].legend();fig.tight_layout();fig.savefig(OUT/'repeat_consistency.png',dpi=140);plt.close(fig)
 versions=OUT/'versions';versions.mkdir(exist_ok=True)
 for path in [Path(__file__),ROOT/'scripts/explore_human_acoustics.py',ROOT/'scripts/audit_natural_baseline.py',ROOT/'scripts/build_natural_baseline.py',ROOT/'scripts/validate_acoustic_measurements.py']:
  shutil.copyfile(path,versions/path.name)
 dump(OUT/'provenance.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_hashes':[{'path':str(p),'sha256':sha(p)} for p in inputs],'source_hashes':{p.name:sha(p) for p in versions.iterdir()},'packages':{k:importlib.metadata.version(k) for k in ['numpy','soundfile','matplotlib']},'f0_reextraction':False,'new_audio':False,'scores':False,'training':False,'source_audio_unchanged':True})
 print(json.dumps({c:{k:v for k,v in x.items() if k not in ['clip_metric_distributions','flag_frame_counts']} for c,x in summary.items()},ensure_ascii=False,indent=2))
 print('Saved',OUT)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('review',type=Path);main(p.parse_args().review)
