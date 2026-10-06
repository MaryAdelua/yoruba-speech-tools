"""Authorized six-text, two-repeat API TTS pilot; raw audio and exact requests retained."""
import argparse,datetime,hashlib,json,os,sys,urllib.request,urllib.error,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/slr86/paired-ai-001'
SOURCE=ROOT/'work/slr86/natural-baseline-001/qc-ingest-001/paired_sentence_proposals.json'
CONFIG={'provider':'OpenAI','model':'gpt-4o-mini-tts-2025-12-15','voice':'coral','voice_version':None,'voice_version_status':'not_exposed_by_provider','response_format':'wav','speed':1.0,'instructions':'Read the supplied Yoruba text exactly as written. Do not add, omit, translate, paraphrase, or correct any words.','seed':None,'seed_status':'not_exposed','configuration_id':'openai-mini-tts-20251215-coral-v1'}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 p=argparse.ArgumentParser();p.add_argument('--generate',action='store_true');args=p.parse_args()
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'audio').mkdir(exist_ok=True);(OUT/'requests').mkdir(exist_ok=True)
 proposals=json.loads(SOURCE.read_text(encoding='utf-8'))['items'];assert len(proposals)==6
 dump(OUT/'configuration.json',CONFIG)
 dump(OUT/'approval.json',{'status':'USER_APPROVED','scope':'Exactly six source texts, two independent generations per sentence with fixed available configuration; no training or correctness scores','proposal_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'natural_reference_interpretation':'Clean paired reference items, not perfect or exclusive definitions of correct Yoruba pronunciation.','configuration_selection':'Existing API access; pinned available TTS snapshot and one fixed built-in coral voice. Existing MMS experiment config found but no runnable local model installation. Not an exhaustive voice catalog sweep.'})
 if not args.generate:return
 key=os.environ.get('OPENAI_API_KEY','').strip()
 if not key:raise RuntimeError('OPENAI_API_KEY unavailable; value never logged')
 records=[]
 for n,s in enumerate(proposals,1):
  for repeat in (1,2):
   rid=f'p{n:02d}_coral_r{repeat:02d}';path=OUT/'audio'/(rid+'.wav');meta=OUT/'requests'/(rid+'.json')
   payload={k:CONFIG[k] for k in ('model','voice','response_format','speed','instructions')};payload['input']=s['exact_yoruba_text']
   if meta.exists():
    record=json.loads(meta.read_text(encoding='utf-8'))
    if record['request']!=payload:raise RuntimeError('Existing request differs; use new run directory')
    if record['status']!='complete':raise RuntimeError('Prior ambiguous/failed request; inspect before explicit retry, no silent regeneration')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['audio_sha256']:raise RuntimeError('Cached audio hash mismatch')
   else:
    if path.exists():raise RuntimeError('Orphan audio; preserve and inspect')
    record={'generation_id':rid,'repeat_generation_id':repeat,'source_id':s['source_id'],'speaker_id':s['speaker_id'],'request':payload,
      'input_utf8_sha256':hashlib.sha256(payload['input'].encode('utf-8')).hexdigest(),'provider':'OpenAI','voice_version':None,'resolved_model_version':None,
      'requested_model_snapshot':CONFIG['model'],'client_request_id':str(uuid.uuid4()),'generation_started_at':now(),'status':'request_started','audio_path':str(path.relative_to(ROOT)).replace('\\','/')}
    dump(meta,record)
    req=urllib.request.Request('https://api.openai.com/v1/audio/speech',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Client-Request-Id':record['client_request_id']},method='POST')
    try:
     with urllib.request.urlopen(req,timeout=180) as response:
      audio=response.read(20_000_001)
      if len(audio)>20_000_000:raise RuntimeError('Unexpected output size')
      record['provider_request_id']=response.headers.get('x-request-id');record['content_type']=response.headers.get('Content-Type')
     path.write_bytes(audio)
     import soundfile as sf
     y,sr=sf.read(path,always_2d=True)
     if y.shape[1]!=1 or not len(y):raise RuntimeError('Unexpected audio format')
     record.update({'status':'complete','generation_completed_at':now(),'audio_sha256':hashlib.sha256(audio).hexdigest(),'audio_bytes':len(audio),'sample_rate_hz':sr,'duration_s':len(y)/sr,'channels':1,'raw_provider_response_preserved':True})
     dump(meta,record)
    except Exception as e:
     record.update({'status':'failed_or_ambiguous','error_type':type(e).__name__,'http_status':e.code if isinstance(e,urllib.error.HTTPError) else None});dump(meta,record)
     raise RuntimeError('Generation failed; safe status recorded without credentials or response body') from None
   records.append(record);print(rid+' complete',flush=True)
   dump(OUT/'generation_manifest.json',records)
if __name__=='__main__':main()
