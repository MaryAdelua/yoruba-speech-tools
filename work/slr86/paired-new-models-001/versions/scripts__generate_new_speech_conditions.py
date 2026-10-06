"""Bounded separate Realtime/Live conditions; no retries or credential logging."""
import argparse,base64,datetime,hashlib,json,os,time,uuid,wave
from pathlib import Path
import websocket
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/slr86';OUT=BASE/'paired-new-models-001'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
INSTRUCTIONS='Read the supplied Yoruba sentence exactly as written, preserving every word. Speak only that sentence once in Yoruba. Do not add greetings, explanations, translations, paraphrases, repetitions, or corrections. After the sentence, remain silent. Do not delegate or call tools.'
def generate(model,s,repeat):
 d=OUT/model;d.mkdir(exist_ok=True);gid=f"{s['sentence_id']}_{model}_marin_r{repeat:02d}";meta=d/(gid+'.json')
 if meta.exists():
  old=json.loads(meta.read_text(encoding='utf-8'))
  if old['status']=='complete' and sha(ROOT/old['audio_path'])==old['audio_sha256']:return old
  raise RuntimeError('Existing incomplete attempt preserved: '+gid)
 live=model=='gpt-live-1';endpoint='wss://api.openai.com/v1/live/sessions' if live else 'wss://api.openai.com/v1/realtime?model='+model
 record={'generation_id':gid,'sentence_id':s['sentence_id'],'source_id':s['source_clip_id'],'repeat_generation_id':repeat,'generation_attempt_id':str(uuid.uuid4()),'provider':'OpenAI','requested_model_snapshot':model,'voice_version':None,'endpoint':endpoint,'api_mode':'Live WebSocket' if live else 'Realtime WebSocket','request':{'input':s['exact_text'],'voice':'marin','instructions':INSTRUCTIONS},'generation_started_at':now(),'status':'started','output_format':'raw signed little-endian PCM16, mono 24000 Hz; lossless WAV container copy','content_verification':'PENDING_NATIVE_LISTENING; provider transcript is not audio ground truth','session_events':[]}
 dump(meta,record);pcm=d/(gid+'.pcm');wav=d/(gid+'.wav');ws=None;chunks=[]
 def send(obj):
  record['session_events'].append({'direction':'client','event':obj if obj['type']!='session.input_audio.append' else {'type':obj['type'],'silent_pcm_samples':2400}});ws.send(json.dumps(obj,ensure_ascii=False))
 def recv():
  event=json.loads(ws.recv());safe={k:v for k,v in event.items() if k!='delta'}
  if 'session' in safe:safe['session']={k:v for k,v in safe['session'].items() if k!='client_secret'}
  if 'delta' in event and 'audio' not in event['type']:safe['delta']=event['delta']
  record['session_events'].append({'direction':'server','received_at':now(),'event':safe})
  if event['type']=='error':
   record['api_error']=event.get('error');raise RuntimeError('API error; see safe attempt metadata')
  return event
 try:
  ws=websocket.create_connection(endpoint,header=['Authorization: Bearer '+os.environ['OPENAI_API_KEY'],'X-Client-Request-Id: '+record['generation_attempt_id']],timeout=25)
  if live:
   send({'type':'session.start','session':{'model':model,'instructions':INSTRUCTIONS,'audio':{'format':{'type':'audio/pcm','rate':24000},'output':{'voice':'marin'}},'delegation':{'type':'client'},'input':[{'type':'message','role':'user','content':[{'type':'input_text','text':s['exact_text']}]}]}})
   e=recv();assert e['type']=='session.started';record['session_id']=e['session']['id']
   send({'type':'session.instructions.append','event_id':'read_exact_sentence','delegation_id':None,'content':'Immediately speak this Yoruba sentence exactly once, then remain silent: '+s['exact_text']})
   # Live needs paced input to advance its timeline. Fixed capture preserves silence, no trimming.
   ws.settimeout(.03);start=time.monotonic();next_chunk=start
   while time.monotonic()-start<30:
    if time.monotonic()>=next_chunk:
     send({'type':'session.input_audio.append','audio':base64.b64encode(bytes(4800)).decode()});next_chunk+=.1
    try:e=recv()
    except websocket.WebSocketTimeoutException:continue
    if e['type']=='session.output_audio.delta':chunks.append(base64.b64decode(e['delta']))
   send({'type':'session.close'});ws.settimeout(15)
   while True:
    e=recv()
    if e['type']=='session.output_audio.delta':chunks.append(base64.b64decode(e['delta']))
    if e['type']=='session.closed':break
   record['capture_note']='Fixed 30-second session with paced silent input; raw output includes silence. No output-audio-done event exists. Do not interpret file duration as utterance speaking duration.'
  else:
   e=recv();record['session_id']=e['session']['id']
   send({'type':'session.update','session':{'type':'realtime','model':model,'instructions':INSTRUCTIONS,'output_modalities':['audio'],'audio':{'input':{'turn_detection':None},'output':{'voice':'marin','format':{'type':'audio/pcm','rate':24000}}}}})
   while recv()['type']!='session.updated':pass
   send({'type':'conversation.item.create','item':{'type':'message','role':'user','content':[{'type':'input_text','text':s['exact_text']}]}})
   send({'type':'response.create','response':{'output_modalities':['audio']}})
   start=time.monotonic()
   while time.monotonic()-start<120:
    e=recv()
    if e['type']=='response.output_audio.delta':chunks.append(base64.b64decode(e['delta']))
    if e['type']=='response.done':
     record['response_id']=e['response']['id'];assert e['response']['status']=='completed';break
   else:raise RuntimeError('Response deadline exceeded')
  data=b''.join(chunks);assert len(data)>0 and len(data)%2==0
  pcm.write_bytes(data)
  with wave.open(str(wav),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(data)
  record.update(status='complete',generation_completed_at=now(),audio_path=str(wav.relative_to(ROOT)).replace('\\','/'),raw_pcm_path=str(pcm.relative_to(ROOT)).replace('\\','/'),audio_sha256=sha(wav),raw_pcm_sha256=sha(pcm),duration_s=len(data)/48000,sample_rate_hz=24000,channels=1)
 except Exception as exc:
  if chunks:pcm.write_bytes(b''.join(chunks))
  record.update(status='failed_or_ambiguous',error_type=type(exc).__name__)
  dump(meta,record);raise RuntimeError(gid+' failed; preserved metadata; no automatic retry') from None
 finally:
  if ws:ws.close()
 dump(meta,record);print(gid+' complete',flush=True);return record
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['gpt-realtime-2.1','gpt-live-1'],required=True);p.add_argument('--limit',type=int,default=12);a=p.parse_args()
 assert os.environ.get('OPENAI_API_KEY');OUT.mkdir(exist_ok=True)
 defs=json.loads((BASE/'paired-ai-001/review_form_definition.json').read_text(encoding='utf-8'))['items'];records=[]
 for s in defs:
  for rep in (1,2):
   if len(records)>=a.limit:break
   records.append(generate(a.model,s,rep));dump(OUT/a.model/'generation_manifest.json',records)
