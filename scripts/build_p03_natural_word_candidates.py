"""Build provisional natural-reference word cuts; never claim verified alignment."""
import datetime,hashlib,html,json,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'work/slr86';OUT=B/'p03-natural-words-001'
SPECS=[('Kò',.995,1.185,['u01'],'Listener accepted earlier opening cut'),('kúkú',1.185,1.48,['u02','u03'],'Listener accepted earlier whole-word cut; internal boundary unverified'),('sírú',1.48,1.765,['u04','u05'],None),('ọlọ́run',1.765,2.025,['u06','u07','u08'],None),('Ọba',2.025,2.42,['u09','u10'],None),('tí',2.69,2.845,['u11'],None),('kò',2.845,3.01,['u12'],None),('ṣeé',3.01,3.22,['u13','u14'],None),('pè',3.22,3.465,['u15'],None),('lẹ́jọ́',3.465,4.4,['u16','u17'],None)]
def main():
 OUT.mkdir(exist_ok=True)
 src=B/'audio/yof_02121_01178327964.wav';original=src.read_bytes()
 pkg=json.loads((B/'p03-supervised-001/annotation_package.json').read_text(encoding='utf-8'));record=pkg['records'][0]
 with wave.open(str(src),'rb') as w:params=w.getparams();rate=w.getframerate();width=w.getsampwidth()*w.getnchannels();pcm=w.readframes(w.getnframes())
 rows=[]
 for i,(text,a,b,ids,accepted) in enumerate(SPECS,1):
  first=round(a*rate);last=round(b*rate);name=f'w{i:02d}.wav';chunk=pcm[first*width:last*width]
  with wave.open(str(OUT/name),'wb') as w:w.setparams(params);w.writeframes(chunk)
  with wave.open(str(OUT/name),'rb') as w:assert w.readframes(w.getnframes())==chunk
  row={'id':f'w{i:02d}','written_unit':text,'reference_ids':ids,'start_sample':first,'end_sample':last,'start_s':first/rate,'end_s':last/rate,'audio_file':name,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest(),'status':'LISTENER_ACCEPTED_USABILITY' if accepted else 'UNVERIFIED_PROPOSAL','prior_feedback':accepted,'exact_alignment_verified':False,'method':'Waveform/spectrogram transition inspection with provisional sequential word association; not forced alignment or listening verification. Word association may be wrong, especially around connected vowels.','measurements':{key:[f for f in record[key] if first/rate<=f['timestamp_s']<last/rate] for key in ['frames','praat_native_frames','spectral_frames']}}
  rows.append(row)
 assert src.read_bytes()==original
 manifest={'schema_version':'natural-word-proposals-1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recording_id':record['id'],'source_audio_sha256':hashlib.sha256(original).hexdigest(),'provenance':record['provenance'],'normalization':pkg['normalization'],'processing':'Exact PCM slices only. No gain changes, denoising, time stretching, or resampling. Original and earlier clips preserved.','scores':'UNIMPLEMENTED','items':rows}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 page='<!doctype html><meta charset="utf-8"><title>Natural recording — word review</title><style>body{font:21px system-ui;max-width:800px;margin:35px auto;padding:18px}article{border:1px solid #ccd;padding:20px;margin:18px 0;border-radius:12px}audio{width:100%}.status{font-size:16px;color:#43576a}</style><h1>Natural recording: word clips</h1><p>Listen and tell me your judgments aloud. If a clip contains the wrong word or cuts it badly, say “bad cut” and skip its tone/pronunciation questions. You do not need to edit timing.</p><p><b>Only the first two cuts have passed your usability check.</b> The remaining word labels and boundaries are proposals, not confirmed alignment. A cut problem is not evidence of a speech error.</p><p lang="yo">Kò kúkú sírú ọlọ́run, Ọba tí kò ṣeé pè lẹ́jọ́.</p><audio controls src="../audio/yof_02121_01178327964.wav"></audio>'
 for i,r in enumerate(rows,1):
  status='Previously accepted as usable' if r['prior_feedback'] else 'Proposed cut — not yet listening-verified'
  page+=f'<article><h2>{i}. <span lang="yo">{html.escape(r["written_unit"])}</span></h2><p class="status">{status}</p><audio controls preload="metadata" src="{r["audio_file"]}"></audio><p>Does it contain the displayed word? If usable: does the pronunciation sound natural, does the tone sound right, and how sure are you?</p></article>'
 page+='<p>Voice-session notes are saved separately by the assistant when acknowledged as saved. This page itself does not record your voice or save answers. No automatic scores.</p>'
 (OUT/'index.html').write_text(page,encoding='utf-8')
 (OUT/'validation.json').write_text(json.dumps({'clip_count':len(rows),'exact_pcm_slice_checks_passed':True,'source_unchanged':True,'first_two_previously_accepted':True,'remaining_word_associations_verified':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2),encoding='utf-8')
 print('Built 10 word candidates; exact PCM checks passed; 8 remain unverified.')
if __name__=='__main__':main()
