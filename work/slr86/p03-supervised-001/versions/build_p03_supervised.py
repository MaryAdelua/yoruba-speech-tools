"""p03 five-recording supervised alignment with descriptive spectral frames."""
import json,hashlib,os,sys,shutil,datetime
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from build_natural_baseline import dump
from validate_acoustic_measurements import csvout
from tone_parser import tone_sequence
B=ROOT/'work/slr86';OUT=B/'p03-supervised-001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def spectral(y,sr):
 n=round(sr*.025);hop=round(sr*.01);rows=[];win=np.hanning(n);fullfreq=np.fft.rfftfreq(n,1/sr);band=fullfreq<=4000;freq=fullfreq[band]
 for start in range(0,len(y)-n+1,hop):
  x=y[start:start+n];power=(abs(np.fft.rfft(x*win))**2)[band];total=power.sum();mag=np.sqrt(power)
  row={'timestamp_s':(start+n/2)/sr,'window_start_s':start/sr,'window_end_s':(start+n)/sr,'rms_dbfs':float(10*np.log10(np.mean(x*x))) if np.any(x) else None,'spectral_centroid_hz':float((freq*mag).sum()/mag.sum()) if mag.sum() else None,'spectral_rolloff85_hz':float(freq[min(np.searchsorted(np.cumsum(power),.85*total),len(freq)-1)]) if total else None,'high_low_band_power_db':float(10*np.log10(power[(freq>=1000)&(freq<=4000)].sum()/power[(freq>=100)&(freq<1000)].sum())) if power[(freq>=1000)&(freq<=4000)].sum()>0 and power[(freq>=100)&(freq<1000)].sum()>0 else None}
  rows.append(row)
 return rows

def main():
 OUT.mkdir(exist_ok=True);os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 definition=read(B/'paired-ai-001/review_form_definition.json');s=next(x for x in definition['items'] if x['sentence_id']=='p03')
 units=[('Kò','Kò'),('kúkú','kú'),('kúkú','kú'),('sírú','sí'),('sírú','rú'),('ọlọ́run,','ọ'),('ọlọ́run,','lọ́'),('ọlọ́run,','run'),('Ọba','Ọ'),('Ọba','ba'),('tí','tí'),('kò','kò'),('ṣeé','ṣe'),('ṣeé','é'),('pè','pè'),('lẹ́jọ́.','lẹ́'),('lẹ́jọ́.','jọ́')]
 assert ''.join(u for _,u in units)==s['exact_text'].replace(' ','').replace(',','').replace('.','')
 source=s['source_clip_id'];spec=[{'id':'p03_natural','audio':B/'audio'/(source+'.wav'),'raw':B/'natural-baseline-001/clips'/source/'raw.json','provenance':{'condition':'natural','source_id':source,'speaker_id':s['speaker_id'],'source_definition':s}}]
 for condition,manifest in [('mini_tts',B/'paired-ai-001/generation_manifest.json'),('realtime',B/'paired-new-models-001/gpt-realtime-2.1/generation_manifest.json')]:
  for g in read(manifest):
   if g['source_id']==source:spec.append({'id':g['generation_id'],'audio':ROOT/g['audio_path'],'raw':manifest.parent/'measurements'/g['generation_id']/'raw.json','provenance':{'condition':condition,'generation':g}})
 records=[];inputs=[]
 for item in spec:
  y,sr=sf.read(item['audio']);raw=read(item['raw']);assert y.ndim==1 and sha(item['audio'])==raw['report']['source']['sha256'];dur=len(y)/sr;frames=raw['frames'];sp=spectral(y,sr)
  d=OUT/item['id'];d.mkdir(exist_ok=True);csvout(d/'spectral_frames.csv',sp);csvout(d/'pitch_frames.csv',frames)
  # No guessed linguistic placement: uniformly spaced editable seeds are explicitly unverified.
  levels=np.array([f['rms_dbfs'] if f['rms_dbfs'] is not None else -120 for f in frames]);active=np.flatnonzero(levels>max(-55,float(levels.max())-35));a=max(0,frames[active[0]]['timestamp_s']-.02);z=min(dur,frames[active[-1]]['timestamp_s']+.02)
  bounds=np.linspace(a,z,len(units)+1);segments=[]
  for i,(word,unit) in enumerate(units):
   tone=tone_sequence(unit);segments.append({'id':f'u{i+1:02d}','reference_ids':[f'u{i+1:02d}'],'word':word,'written_unit':unit,'expected_orthographic_tone':tone,'tone_basis':'Unmarked vowel represented as provisional M; not completeness-confirmed' if 'M' in tone else 'Explicit orthographic tone marks','start_s':round(float(bounds[i]),4),'end_s':round(float(bounds[i+1]),4),'boundary_review':'unverified','tone_review':'unverified','confidence':'','notes':''})
  env=[];hop=max(1,sr//300)
  for j in range(0,len(y),hop):chunk=y[j:j+hop];env.append([j/sr,float(chunk.min()),float(chunk.max())])
  fig,ax=plt.subplots(figsize=(14,3));ax.specgram(y,NFFT=round(sr*.025),Fs=sr,noverlap=round(sr*.015),cmap='magma',vmin=-110,vmax=-20);ax.set(ylim=(0,4000),xlabel='Time (s)',ylabel='Frequency (Hz)',title=item['id']+' · spectrogram, uncalibrated power');fig.tight_layout();fig.savefig(d/'spectrogram.png',dpi=130);plt.close(fig)
  records.append({'id':item['id'],'audio_url':'../'+str(item['audio'].relative_to(B)).replace('\\','/'),'audio_sha256':sha(item['audio']),'duration_s':dur,'sample_rate_hz':sr,'provenance':item['provenance'],'frames':frames,'praat_native_frames':raw['praat_native_frames'],'spectral_frames':sp,'spectrogram_url':item['id']+'/spectrogram.png','waveform':env,'segments':segments})
  inputs.extend([{'path':str(item[k]),'sha256':sha(item[k])} for k in ['audio','raw']])
 data={'schema_version':'p03-supervised-1.0','sentence_id':'p03','source_id':source,'exact_reference_text':s['exact_text'],'seed_method':'Uniform intervals within a rough energy-active extent. These are editor placeholders, NOT linguistic alignment. Confirm/correct by listening; split/merge as appropriate. No interval is verified initially.','tone_note':'Spelling is reference only, not observed pronunciation. M from unmarked vowels is provisional. ṣe-é is a two-vowel scaffold; combine or adjust for actual realization. Final n in run is retained with the vowel, not automatically a separate syllable.','normalization':'Existing 12*log2(F0/own-utterance voiced median), separately per estimator. Raw values retained.','spectral_method':'25 ms Hann-window analysis, 10 ms hop, original sample rate, no preemphasis or audio changes. Centroid and rolloff use the common 0–4000 Hz band at both sample rates (magnitude centroid, 85% power rolloff); high/low = 10log10(power 1000–4000Hz / power 100–1000Hz). Generic spectral descriptors, not nasality/formant/pronunciation scores. Short windows crossing boundaries are flagged in export. Silence/low-energy spectra are not trustworthy phonetic measurements. No A1-P0/A1-P1 or formant bandwidth is inferred.','records':records,'scores':'UNIMPLEMENTED','style_observation':'Withdrawn as model-level finding; clip unidentified; not used here as label or target.'}
 dump(OUT/'annotation_package.json',data)
 page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>p03 supervised interval review</title><style>body{font:16px system-ui;margin:20px;color:#182b3c}header{max-width:1200px}.warning{background:#fff2ce;padding:14px}button,input,select,textarea{font:inherit;padding:6px}audio{width:600px;max-width:100%}svg{width:100%;height:430px;background:#f5f8fb}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #ccd4df;padding:5px;vertical-align:top}input[type=number]{width:95px}.unit{width:95px}.tone{width:65px}textarea{width:180px;height:65px}.scroll{overflow:auto}img{width:100%}.metrics{min-width:250px}#status{position:sticky;top:0;background:#eff5ff;padding:10px}fieldset{margin:12px 0}</style><header><h1>p03 · supervised interval review</h1><h2 lang="yo">'''+s['exact_text']+'''</h2><p class="warning">All starting intervals are UNVERIFIED placeholders, not automatically aligned syllables. Listen, edit, split or merge before confirming. Confirmation means the written unit is associated with that interval—not that its pronunciation or tone is correct. Natural speech is not an exclusive correctness standard.</p><p>Expected tone labels describe the written reference. Unmarked M and vowel sequences need review. No correct/incorrect classification, training or scoring. The withdrawn “calmer / less loud” impression is not a target.</p><label>Reviewer <input id="reviewer"></label> <button id="export">Export p03 review JSON</button><p>Confidence means certainty about the boundary/unit judgment, not its acoustic cause. Export includes raw trajectories, spectral windows and all provenance. Draft autosaves locally; export a portable copy.</p></header><p id="status">Select a recording. No segments verified yet.</p><label>Recording <select id="recording"></select></label><main id="main"></main><script id="data" type="application/json">'''+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'''</script><script src="review.js"></script>'''
 (OUT/'index.html').write_text(page,encoding='utf-8');shutil.copyfile(ROOT/'src/p03_interval_review.js',OUT/'review.js')
 dump(OUT/'provenance.json',{'inputs':inputs,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),'js_sha256':sha(ROOT/'src/p03_interval_review.js'),'no_audio_modification':True,'F0_reextraction':False,'new_spectral_descriptors':True})
 versions=OUT/'versions';versions.mkdir(exist_ok=True)
 for p in [Path(__file__),ROOT/'src/p03_interval_review.js']:shutil.copyfile(p,versions/p.name)
 print('Built five intact recording package; pitch reused; descriptive spectral frames added.')
if __name__=='__main__':main()
