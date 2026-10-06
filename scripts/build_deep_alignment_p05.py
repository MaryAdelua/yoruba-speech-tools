"""One sentence, three unchanged recordings: inspectable provisional alignment."""
import json,sys,hashlib,os,collections
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import find_peaks
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from validate_acoustic_measurements import csvout
from build_natural_baseline import dist,dump
BASE=ROOT/'work/slr86';OUT=BASE/'deep-alignment-p05-001';OUT.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
units=[('Ẹlẹ́dẹ̀','Ẹ','M'),('Ẹlẹ́dẹ̀','lẹ́','H'),('Ẹlẹ́dẹ̀','dẹ̀','L'),('náà','náà','HL'),('bí','bí','H'),('ọmọ','ọ','M'),('ọmọ','mọ','M'),('mẹ́fà','mẹ́','H'),('mẹ́fà','fà','L'),('péré','pé','H'),('péré','ré','H')]
# ná-à contains two orthographic tone-bearing vowels. Represent separately; vowel hiatus vs long-vowel realization remains for review.
units[3:4]=[('náà','ná','H'),('náà','à','L')]
source='yom_00295_01260038205';specs=[('natural',BASE/'audio'/f'{source}.wav',BASE/'natural-baseline-001/clips'/source/'raw.json')]+[(f'mini_tts_r0{i}',BASE/'paired-ai-001/audio'/f'p05_coral_r0{i}.wav',BASE/'paired-ai-001/measurements'/f'p05_coral_r0{i}'/'raw.json') for i in [1,2]]
recordings=[];table=[];allframes=[]
for name,path,rawpath in specs:
 raw=json.loads(rawpath.read_text(encoding='utf-8'));frames=raw['frames'];y,sr=sf.read(path);duration=len(y)/sr
 assert hashlib.sha256(path.read_bytes()).hexdigest()==raw['report']['source']['sha256']
 t=np.array([f['timestamp_s'] for f in frames]);rms=np.array([f['rms_dbfs'] if f['rms_dbfs'] is not None else -120 for f in frames]);active=np.flatnonzero(rms>max(-55,float(np.max(rms))-35))
 start=max(0,float(t[active[0]])-.02);end=min(duration,float(t[active[-1]])+.02);width=(end-start)/len(units)
 # Candidate boundaries near equal-duration anchors, snapped to local energy minima. NOT forced alignment.
 minima=find_peaks(-rms)[0];bounds=[start]
 for k in range(1,len(units)):
  target=start+k*width;candidates=[j for j in minima if abs(t[j]-target)<width*.35 and t[j]>bounds[-1]+.03]
  bounds.append(float(t[min(candidates,key=lambda j:rms[j])]) if candidates else target)
 bounds.append(end);segments=[]
 for i,(word,syll,tone) in enumerate(units):
  a,b=bounds[i:i+2];selected=[f for f in frames if a<=f['timestamp_s']<b];flags=collections.Counter(z for f in selected for z in f['flags'].split('|') if z)
  row={'recording':name,'unit_id':i+1,'word':word,'reference_unit':syll,'expected_orthographic_tone':tone,'tone_basis':'explicit acute/grave' if tone!='M' else 'unmarked vowel: provisional orthographic M, completeness not independently confirmed','start_s':a,'end_s':b,'duration_s':b-a,'boundary_status':'UNVERIFIED_ACOUSTIC_SEED_REQUIRES_NATIVE_REVIEW','flags':json.dumps(dict(flags)),'reliable_frames':sum(f['agreement_screen_pass'] for f in selected),'total_frames':len(selected)}
  for label,key in [('pyin_hz','f0_hz'),('praat_hz','praat_f0_hz'),('pyin_relative_st','relative_pitch_semitones'),('praat_relative_st','praat_relative_semitones')]:row[label+'_median']=dist([f[key] for f in selected])['median']
  row['window_crosses_boundary_frames']=sum(f['window_start_s']<a or f['window_end_s']>b for f in selected)
  table.append(row);segments.append(row)
  allframes.extend({'recording':name,'unit_id':i+1,**f} for f in selected)
 envelope=[]
 for j in range(0,len(y),max(1,sr//200)):
  chunk=y[j:j+max(1,sr//200)];envelope.append([j/sr,float(np.min(chunk)),float(np.max(chunk))])
 record={'id':name,'audio_url':'../'+str(path.relative_to(BASE)).replace('\\','/'),'audio_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration_s':duration,'source_frames':str(rawpath.relative_to(ROOT)),'segments':segments,'frames':frames,'waveform_envelope':envelope};recordings.append(record)
 fig,axes=plt.subplots(3,1,figsize=(16,9),sharex=True)
 axes[0].plot(np.arange(len(y))/sr,y,lw=.3);axes[0].set_ylabel('Waveform amplitude')
 for ax,keys in [(axes[1],['f0_hz','praat_f0_hz']),(axes[2],['relative_pitch_semitones','praat_relative_semitones'])]:
  for key,label in zip(keys,['pYIN','Praat']):ax.plot(t,[np.nan if f[key] is None else f[key] for f in frames],'.-',lw=.7,ms=2,label=label)
  bad=[f['timestamp_s'] for f in frames if not f['agreement_screen_pass']];ax.plot(bad,[0]*len(bad),'|',color='gray',alpha=.25,label='screen not passed (not error)');ax.legend(fontsize=8)
 axes[1].set_ylabel('F0 Hz');axes[2].set_ylabel('Relative semitones');axes[2].set_xlabel('Time (s)')
 for ax in axes:
  for b in bounds:ax.axvline(b,color='gray',ls='--',lw=.7)
 for seg in segments:axes[0].text((seg['start_s']+seg['end_s'])/2,.98,seg['reference_unit']+' / '+seg['expected_orthographic_tone'],transform=axes[0].get_xaxis_transform(),ha='center',va='top',fontsize=10)
 fig.suptitle(name+' — UNVERIFIED boundary proposals, not observed phoneme labels');fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=140);plt.close(fig)
data={'sentence_id':'p05','exact_reference_text':'Ẹlẹ́dẹ̀ náà bí ọmọ mẹ́fà péré.','status':'SUPERVISED_REVIEW_PENDING','boundary_method':'Equal-duration anchors snapped to nearby RMS minima (within 35% of unit spacing); active extent from RMS threshold. Heuristic proposals only, not linguistic forced alignment; unvoiced is not silence. No audio modification.','tone_note':'Expected labels describe spelling only; unmarked M is tentative. ná-à has two vowel/tone-bearing units H,L; their surface realization and internal boundary require review. No phoneme boundaries or correctness inferred.','normalization':'12*log2(F0/own-utterance voiced median) separately for each estimator; preserve raw F0.','recordings':recordings,'all_correctness_scores':'UNIMPLEMENTED'}
dump(OUT/'alignment.json',data);csvout(OUT/'provisional_unit_measurements.csv',table);csvout(OUT/'associated_frames.csv',allframes)
html='''<!doctype html><meta charset="utf-8"><title>p05 supervised alignment</title><style>body{font:16px system-ui;max-width:1450px;margin:auto;padding:24px}article{border:1px solid #bbb;padding:18px;margin:20px 0}svg{width:100%;height:420px;background:#f8fafc}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:5px}input[type=number]{width:90px}button{padding:8px}audio{width:100%}.warning{background:#fff0ca;padding:15px}</style><h1>p05 · Ẹlẹ́dẹ̀ náà bí ọmọ mẹ́fà péré.</h1><p class="warning">Supervised review pending. Dashed boundaries are heuristic starting points, NOT verified alignment. Expected tones describe reference spelling, not observed correctness. Edit boundaries while listening; ná-à needs particular scrutiny. A small or missing pitch estimate does not prove an error. No phoneme boundary is claimed.</p><p>Raw F0 and relative pitch use existing pYIN/Praat measurements unchanged. Relative pitch = 12 log₂(F0 / own-utterance median), separately per estimator. Blue: pYIN; orange: Praat; gray ticks: reliability screen not passed.</p><label>Reviewer <input id="reviewer"></label><button id="export">Export alignment review JSON</button><p id="status">Edits stay in this page until exported. Export before closing.</p><main></main><script id="data" type="application/json">'''+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'''</script><script src="alignment_review.js"></script>'''
(OUT/'alignment_review.html').write_text(html,encoding='utf-8')
print('Created three-recording supervised p05 package; all boundaries explicitly unverified.')

(OUT/'alignment_review.js').write_text((ROOT/'src/deep_alignment_review.js').read_text(encoding='utf-8'),encoding='utf-8')
