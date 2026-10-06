"""Create fresh v2 human-review sessions; preserve prior artifacts and all signals."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'work/slr86';N=DATA/'natural-baseline-001';P=DATA/'paired-ai-001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
GUIDANCE='''<section class="confidence-help"><p><strong>Reviewer confidence means: how sure are you about what you heard and the judgment you selected. It does NOT mean how sure you are about the technical/acoustic cause of the problem.</strong></p><ul><li>High = I am sure of my judgment</li><li>Medium = I think this is correct but there is some ambiguity</li><li>Low = I am genuinely unsure</li></ul></section>'''
def main():
 targets=[N/'natural_qc_review_v2.html',P/'paired_native_listener_review_v2.html',P/'structured_review_v2.js']
 if any(p.exists() for p in targets):raise RuntimeError('V2 files already exist; refuse to reset an active session')
 protected=[p for base in (N,P,DATA/'audio') for p in base.rglob('*') if p.is_file()]+[DATA/'natural_reference.jsonl']
 before={str(p):sha(p) for p in protected}
 natural=(N/'qc_review.html').read_text(encoding='utf-8')
 natural=natural.replace('<title>SLR86: 20-clip listening QC</title>','<title>Natural QC review v2</title>')
 natural=natural.replace('</h1>',' — v2</h1>'+GUIDANCE+'<p>Fresh session: previous reviews are superseded. Leave unreviewed fields blank. Export this session as natural_qc_review_v2.json.</p>',1)
 natural=natural.replace('Export review JSON','Export Review JSON').replace("a.download='qc_human_review.json'","a.download='natural_qc_review_v2.json'")
 natural=natural.replace("JSON.stringify({reviewer:","JSON.stringify({review_version:2,review_session_id:'natural_qc_review_v2',confidence_definition:'certainty about what was heard and the selected judgment, not certainty about technical/acoustic cause',reviewer:")
 (N/'natural_qc_review_v2.html').write_text(natural,encoding='utf-8')
 paired=(P/'listening_review.html').read_text(encoding='utf-8')
 paired=paired.replace('<title>Structured paired Yorùbá review</title>','<title>Paired native-listener review v2</title>')
 paired=paired.replace('</h1>',' — v2</h1>'+GUIDANCE+'<p>Fresh v2 session. Previous reviews are superseded and are not imported into this form.</p>',1)
 paired=paired.replace('src="structured_review.js"','src="structured_review_v2.js"')
 paired=paired.replace('"schema_version": "paired-native-review-1.0"','"schema_version": "paired-native-review-1.0", "review_version": 2, "review_session_id": "paired_native_listener_review_v2"')
 (P/'paired_native_listener_review_v2.html').write_text(paired,encoding='utf-8')
 js=(P/'structured_review.js').read_text(encoding='utf-8')
 js=js.replace("'yoruba-paired-native-review-1.0:'","'yoruba-paired-native-review-v2:'")
 js=js.replace('return {schema_version:definition.schema_version','return {review_version:2,review_session_id:"paired_native_listener_review_v2",confidence_definition:"certainty about what was heard and the selected judgment, not certainty about technical/acoustic cause",schema_version:definition.schema_version')
 js=js.replace("a.download='paired_native_listener_review.json'","a.download='paired_native_listener_review_v2.json'")
 (P/'structured_review_v2.js').write_text(js,encoding='utf-8')
 old=[N/'qc-ingest-001/qc_human_review.original.json',P/'human-acoustic-001/review.original.json']
 policy={'active_review_version':2,'reason':'User misunderstood confidence; both human-review stages must be redone from blank sessions.','confidence_definition':'Certainty about what was heard and the selected judgment, not certainty about technical/acoustic cause.','superseded_reviews':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'status':'superseded','use_in_subsequent_analysis':False} for p in old], 'active_sessions':{'natural':'natural_qc_review_v2','paired':'paired_native_listener_review_v2'},'new_exports_received':False,'analysis_policy':'Use only completed v2 exports from BOTH stages; earlier exports and human-derived conclusions are audit history only unless explicitly requested. Audio, measurements and approved sentence identities remain unchanged.'}
 dump(DATA/'human_review_revision_policy.json',policy)
 for d in (N/'qc-ingest-001',P/'human-acoustic-001'):
  dump(d/'SUPERSEDED.json',{'status':'superseded','scope':'Human review and human-derived findings; raw acoustic artifacts remain valid historical measurements.','replacement':'v2 reviews pending','reason':policy['reason']})
 dump(N/'natural_qc_review_v2.session.json',{'review_version':2,'session_id':'natural_qc_review_v2','status':'awaiting_review','ratings_initialized':'blank','sample_source':'qc_sample.json','sample_sha256':sha(N/'qc_sample.json')})
 dump(P/'paired_native_listener_review_v2.session.json',{'review_version':2,'session_id':'paired_native_listener_review_v2','status':'awaiting_review','ratings_initialized':'blank','draft_storage':'new v2 namespace; no old draft migration','definition_source':'review_form_definition.json','definition_sha256':sha(P/'review_form_definition.json')})
 assert all(sha(Path(p))==h for p,h in before.items())
 dump(DATA/'human_review_v2_preservation_check.json',{'previous_files_checked':len(before),'all_previous_files_unchanged':True,'sha256_before_and_after':before,'acoustic_extraction_rerun':False,'audio_regenerated':False})
 print('Created v2 pages; all '+str(len(before))+' pre-existing data files byte-identical. Earlier reviews superseded by sidecar metadata, originals untouched.')
if __name__=='__main__':main()
