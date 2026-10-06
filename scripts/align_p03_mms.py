"""Local multilingual CTC word alignment. Outputs remain unverified proposals."""
import os,json,hashlib,datetime,wave,unicodedata,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'work/slr86';OUT=B/'p03-mms-alignment-001'
os.environ['TORCH_HOME']=str(B/'alignment-model-cache')
import torch,torchaudio,soundfile as sf

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);torch.set_num_threads(4)
 pkg=json.loads((B/'p03-supervised-001/annotation_package.json').read_text(encoding='utf-8'))
 words=pkg['exact_reference_text'].split();clean=[w.strip(',.') for w in words]
 tokens=[''.join(c for c in unicodedata.normalize('NFD',w.lower()) if 'a'<=c<='z') for w in clean]
 bundle=torchaudio.pipelines.MMS_FA;model=bundle.get_model();tokenizer=bundle.get_tokenizer();aligner=bundle.get_aligner()
 records=[]
 for rec in pkg['records']:
  path=(B/'p03-supervised-001'/rec['audio_url']).resolve();digest=sha(path)
  y,sr=sf.read(path,dtype='float32');waveform=torch.from_numpy(y).unsqueeze(0)
  analysis=torchaudio.functional.resample(waveform,sr,bundle.sample_rate)
  with torch.inference_mode():emission,_=model(analysis);spans=aligner(emission[0],tokenizer(tokens))
  ratio=analysis.shape[1]/emission.shape[1]/bundle.sample_rate
  out=OUT/rec['id'];out.mkdir(exist_ok=True)
  with wave.open(str(path),'rb') as w:params=w.getparams();pcm=w.readframes(w.getnframes());width=w.getnchannels()*w.getsampwidth()
  items=[]
  for i,(text,token,ss) in enumerate(zip(clean,tokens,spans)):
   start=ss[0].start*ratio;end=ss[-1].end*ratio
   # Midpoints in CTC gaps plus bounded padding are playback context, not inferred phoneme extents.
   prev=spans[i-1][-1].end*ratio if i else 0;following=spans[i+1][0].start*ratio if i+1<len(spans) else len(y)/sr
   a=max(0,start-.06,(prev+start)/2 if i else 0);b=min(len(y)/sr,end+.06,(end+following)/2 if i+1<len(spans) else len(y)/sr)
   if rec['id']=='p03_natural' and i<2:a,b=[(.995,1.185),(1.185,1.48)][i]
   first=round(a*sr);last=round(b*sr);name=f'w{i+1:02d}.wav'
   with wave.open(str(out/name),'wb') as w:w.setparams(params);w.setnframes(last-first);w.writeframes(pcm[first*width:last*width])
   with wave.open(str(out/name),'rb') as w:assert w.readframes(w.getnframes())==pcm[first*width:last*width]
   items.append({'id':f'w{i+1:02d}','written_unit':text,'alignment_token':token,'ctc_start_s':start,'ctc_end_s':end,'playback_method':'previously listener-accepted cut' if rec['id']=='p03_natural' and i<2 else 'CTC extent plus up to 60ms context bounded by neighboring-token midpoints','playback_start_s':first/sr,'playback_end_s':last/sr,'alignment_token_spans':[{'start_s':s.start*ratio,'end_s':s.end*ratio,'model_path_probability':s.score} for s in ss],'audio_file':rec['id']+'/'+name,'measurements':{key:[f for f in rec[key] if start<=f['timestamp_s']<end] for key in ['frames','praat_native_frames','spectral_frames']},'status':'LISTENER_ACCEPTED_CUT_USABILITY' if rec['id']=='p03_natural' and i<2 else 'MODEL_PROPOSAL_NOT_HUMAN_VERIFIED','note':'CTC path probability is not pronunciation confidence or correctness. Reference text is imposed; output cannot verify transcript truth.'})
  assert sha(path)==digest
  records.append({'id':rec['id'],'source_audio_sha256':digest,'provenance':rec['provenance'],'items':items})
  print(rec['id'],[(x['written_unit'],round(x['ctc_start_s'],2),round(x['ctc_end_s'],2)) for x in items],flush=True)
 data={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'TorchAudio MMS_FA pretrained CTC forced alignment','torch':torch.__version__,'torchaudio':torchaudio.__version__,'reference_text':pkg['exact_reference_text'],'alignment_only_text_transform':'NFD lowercase ASCII letters only, preserving original words/diacritics separately. Tone marks and underdots are not modeled. This lossy adapter is exclusively for timing proposals, never tone/phoneme correctness.','audio_transform':'16kHz in-memory resample for aligner only; original unchanged; playback exact original PCM slices; existing acoustic features unchanged.','human_validation':'PENDING','scores':'UNIMPLEMENTED','records':records,'script_sha256':sha(Path(__file__))}
 (OUT/'alignment.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 page='<meta charset="utf-8"><title>Speech-aligned word proposals</title><style>body{font:20px system-ui;max-width:900px;margin:30px auto;padding:20px}article{border:1px solid #bbb;padding:16px;margin:15px 0}audio{width:100%}</style><h1>Speech-aligned word proposals</h1><p>These new cuts come from a speech alignment model, not visual guesses. They still need listening verification. No automatic correctness scores. Original recordings and previous reviews are preserved.</p>'
 for rec in records:
  page+='<details '+('open' if rec['id']=='p03_natural' else '')+'><summary>'+html.escape({'p03_natural':'Natural human reference','p03_coral_r01':'mini-TTS take 1','p03_coral_r02':'mini-TTS take 2','p03_gpt-realtime-2.1_marin_r01':'Realtime take 1','p03_gpt-realtime-2.1_marin_r02':'Realtime take 2'}[rec['id']])+'</summary>'
  page+='<p>Listen to the full sentence first:</p><audio controls preload=\"none\" src=\"../'+str((B/'p03-supervised-001'/next(r['audio_url'] for r in pkg['records'] if r['id']==rec['id'])).resolve().relative_to(B)).replace('\\','/')+'\"></audio>'
  for item in rec['items']:page+=f'<article><h2>{html.escape(item["written_unit"])}</h2><audio controls preload="none" src="{item["audio_file"]}"></audio></article>'
  page+='</details>'
 (OUT/'index.html').write_text(page,encoding='utf-8')
if __name__=='__main__':main()
