"""Same descriptive pYIN/Praat instruments for approved paired AI recordings."""
import csv,html,json,os,sys
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'src'))
from validate_acoustic_measurements import compare,summary,csvout,PRAAT
from build_natural_baseline import dist,dump
from audit_natural_baseline import runs
from acoustic_analysis import sha256
OUT=ROOT/'work/slr86/paired-ai-001';NAT=ROOT/'work/slr86/natural-baseline-001'

def metrics(frames,raw,duration):
 a=summary(frames,0,duration);matched=a['matched_frames'];both=a['both_voiced']
 return {'duration_s':duration,'pyin_f0_hz':dist([f['f0_hz'] for f in frames]),'praat_native_f0_hz':dist([f['f0_hz'] for f in raw]),
  'pyin_voiced_percent':100*sum(f['voiced'] for f in frames)/len(frames),'praat_native_voiced_percent':100*sum(f['voiced'] for f in raw)/len(raw),
  'pyin_utterance_relative_st':dist([f['relative_pitch_semitones'] for f in frames]),'praat_utterance_relative_st':dist([f['praat_relative_semitones'] for f in frames]),
  'rms_dbfs':dist([f['rms_dbfs'] for f in frames]),'voiced_frame_runs':runs(frames,duration),
  'estimator_agreement':a,'voicing_disagreement_percent':100*a['voicing_disagreements']/matched if matched else None,
  'both_within_half_semitone_percent':100*a['both_within_half_semitone']/both if both else None,
  'timing_note':'Frame-cell intervals only, not phoneme or syllable alignment; unvoiced is not necessarily silence.'}

def main():
 os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
 import matplotlib
 matplotlib.use('Agg');import matplotlib.pyplot as plt
 records=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf-8'));assert len(records)==12
 proposals=json.loads((NAT/'qc-ingest-001/paired_sentence_proposals.json').read_text(encoding='utf-8'))['items']
 scores={k:{'status':'UNIMPLEMENTED','value':None} for k in ['lexical_tone','pronunciation','nasality','prosody','fluency','overall']}
 data={};table=[];allpairs=[]
 for r in records:
  path=ROOT/r['audio_path'];assert sha256(path)==r['audio_sha256'];d=OUT/'measurements'/r['generation_id'];d.mkdir(parents=True,exist_ok=True)
  if (d/'raw.json').exists():obj=json.loads((d/'raw.json').read_text(encoding='utf-8'));assert obj['report']['source']['sha256']==r['audio_sha256']
  else:
   sr=sf.info(path).samplerate;window=2*round((2048/24000)*sr/2)
   report,frames,raw,base=compare(path,frame_length=window)
   for f in frames:
    flags=f['flags'].split('|') if f['flags'] else []
    if f['edge_padded']:flags.append('edge_window')
    if f['f0_hz'] and f['f0_hz']>=500/1.05:flags.append('near_pyin_ceiling')
    if f['praat_f0_hz'] and (f['praat_f0_hz']<=65*1.05 or f['praat_f0_hz']>=500/1.05):flags.append('praat_near_search_limit')
    f['agreement_screen_pass']=bool(f['f0_hz'] and f['praat_f0_hz'] and not flags and f['voicing_probability']>=.5 and f['praat_strength']>=.45 and abs(f['signed_difference_semitones'])<=.5)
    f['flags']='|'.join(flags)
   report['scores']=scores
   obj={'report':report,'frames':frames,'praat_native_frames':raw};dump(d/'raw.json',obj)
  report=obj['report'];frames=obj['frames'];raw=obj['praat_native_frames'];report['scores']=scores
  m=metrics(frames,raw,r['duration_s']);dump(d/'analysis.json',{'generation':r,'pyin_report':report,'praat_settings':PRAAT,'measurements':m,'scores':scores,'normalization':'12*log2(F0/own utterance voiced median), separately per estimator. Does not erase raw pitch or imply matched syllables.'})
  csvout(d/'frames.csv',frames);csvout(d/'praat_native_frames.csv',raw);data[r['generation_id']]={'frames':frames,'metrics':m};print('Analyzed '+r['generation_id'],flush=True)
 cards=[]
 for i,s in enumerate(proposals,1):
  nr=json.loads((NAT/'clips'/s['source_id']/'raw.json').read_text(encoding='utf-8'))
  natural_path=ROOT/s['audio_path'];assert sha256(natural_path)==s['audio_sha256']
  nm=metrics(nr['frames'],nr['praat_native_frames'],s['duration_s'])
  pair={'source_id':s['source_id'],'exact_text':s['exact_yoruba_text'],'natural':nm,'ai':[],'scores':scores,'alignment':'No lexical or syllable alignment. Contours retain original timestamps; durations include all leading/trailing audio.'}
  fig,axes=plt.subplots(3,2,figsize=(12,8));series=[('Natural reference',nr['frames'])]
  audios=[('Natural reference','../audio/'+s['source_id']+'.wav')]
  for repeat in (1,2):
   rid=f'p{i:02d}_coral_r{repeat:02d}';ai=data[rid];m=ai['metrics'];series.append((f'AI generation {repeat}',ai['frames']));audios.append((f'AI generation {repeat}','audio/'+rid+'.wav'))
   pair['ai'].append({'generation_id':rid,'measurements':m,'descriptive_deltas':{'duration_s':m['duration_s']-nm['duration_s'],'duration_ratio':m['duration_s']/nm['duration_s'],'pyin_median_hz':m['pyin_f0_hz']['median']-nm['pyin_f0_hz']['median'] if m['pyin_f0_hz']['median'] and nm['pyin_f0_hz']['median'] else None},'interpretation':'Differences are measurements, not error or correctness scores.'})
  for label,m in [('natural',nm)]+[(a['generation_id'],a['measurements']) for a in pair['ai']]:
   table.append({'source_id':s['source_id'],'recording':label,'duration_s':m['duration_s'],'pyin_median_hz':m['pyin_f0_hz']['median'],'pyin_min_hz':m['pyin_f0_hz']['min'],'pyin_max_hz':m['pyin_f0_hz']['max'],'praat_median_hz':m['praat_native_f0_hz']['median'],'pyin_voiced_percent':m['pyin_voiced_percent'],'praat_voiced_percent':m['praat_native_voiced_percent'],'median_pitch_disagreement_st':m['estimator_agreement']['median_absolute_semitones'],'voicing_disagreement_percent':m['voicing_disagreement_percent']})
  for row,(label,frames) in enumerate(series):
   t=[f['timestamp_s'] for f in frames]
   for col,keys in enumerate([('f0_hz','praat_f0_hz'),('relative_pitch_semitones','praat_relative_semitones')]):
    for key,est in zip(keys,['pYIN','Praat']):axes[row,col].plot(t,[f[key] if f[key] is not None else np.nan for f in frames],'.-',ms=1,lw=.7,label=est)
    axes[row,col].set(title=label,ylabel='F0 (Hz)' if col==0 else 'Utterance-relative semitones',xlabel='Time (s)');axes[row,col].legend(fontsize=8)
    axes[row,col].set_xlim(0, nm['duration_s'] if row==0 else pair['ai'][row-1]['measurements']['duration_s'])
  fig.suptitle(s['source_id']+' — unaligned descriptive contours');fig.tight_layout();fig.savefig(OUT/f'pair_{i:02d}.png',dpi=130);plt.close(fig)
  allpairs.append(pair)
  players=''.join(f'<div><h3>{label}</h3><audio controls preload="none" src="{url}"></audio></div>' for label,url in audios)
  cards.append(f'<article><h2>Sentence {i}</h2><p class="text" lang="yo">{html.escape(s["exact_yoruba_text"])}</p><p>{s["source_id"]} · {s["speaker_id"]}</p><div class="players">{players}</div><label>Listening notes / time intervals<textarea data-id="{s["source_id"]}"></textarea></label></article>')
 dump(OUT/'paired_comparisons.json',{'configuration':json.loads((OUT/'configuration.json').read_text()),'pairs':allpairs,'scores':scores,'cautions':['Natural references are not perfect or exclusive pronunciation standards.','Inputs were preserved exactly; generated lexical realization still requires listening verification.','Different speakers and recording channels confound raw pitch/amplitude comparison.','Independent requests do not guarantee statistically independent latent samples.','Voice version and provider-internal settings are unavailable.','Normalization is within utterance, not a fixed H/M/L map.']})
 csvout(OUT/'paired_summary.csv',table)
 page='''<!doctype html><meta charset="utf-8"><title>Paired Yorùbá listening review</title><style>body{font:17px system-ui;margin:30px auto;max-width:1200px;background:#f4f5f7;color:#172331;padding:16px}article{background:white;padding:22px;margin:22px 0;border:1px solid #ccd4de;border-radius:10px}.text{font-size:24px}.players{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}audio{width:100%}textarea{display:block;width:98%;height:70px;margin-top:8px}button{padding:10px;font:inherit}@media(max-width:800px){.players{grid-template-columns:1fr}}</style><h1>Paired Yorùbá listening review</h1><p>Six approved texts. Natural reference and two independently requested AI generations. AI: OpenAI gpt-4o-mini-tts-2025-12-15, coral, speed 1.0. Natural references are not perfect or exclusive pronunciation standards. No preference or correctness labels are assigned.</p><p>Original recordings play without gain normalization or trimming. Differences in recording levels may affect perception. Notes remain in this page until exported.</p><button id="export">Export listening notes</button>'''+''.join(cards)+'''<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(a!==b)b.pause()})));document.getElementById('export').onclick=()=>{let items=[...document.querySelectorAll('textarea')].map(a=>({source_id:a.dataset.id,notes:a.value}));let u=URL.createObjectURL(new Blob([JSON.stringify({created_at:new Date().toISOString(),items},null,2)],{type:'application/json'}));let a=document.createElement('a');a.href=u;a.download='paired_listening_notes.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};</script>'''
 from build_paired_review import build
 build()
 dump(OUT/'validation.json',{'approved_texts':6,'independent_requests':12,'audio_files':12,'analyzed':len(data),'natural_hashes_unchanged':True,'raw_audio_preserved':True,'text_verified_against_approved_proposals':all(r['request']['input']==next(s['exact_yoruba_text'] for s in proposals if s['source_id']==r['source_id']) for r in records),'distinct_audio_hashes':len({r['audio_sha256'] for r in records}),'scores':scores})
 print('Paired artifacts complete.',flush=True)
if __name__=='__main__':main()
