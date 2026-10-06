"""Exploratory human/acoustic association, fixed 12-take approved pilot. No fitting/scoring."""
import argparse,collections,datetime,hashlib,importlib.metadata,json,os,shutil,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build_natural_baseline import dist,dump
from validate_acoustic_measurements import csvout
from audit_natural_baseline import runs
BASE=ROOT/'work/slr86/paired-ai-001';OUT=BASE/'human-acoustic-001'
DIMS=['lexical_tone_realization','segmental_pronunciation','perceived_nasality','prosody_intonation','rhythm_fluency','overall_yoruba_naturalness','reviewer_confidence']
CONFIG={'version':'human-acoustic-exploration-1.0','temporal_bins':10,'contour_method':'Median own-utterance-relative pYIN F0 in 10 equal fractional-duration bins; no interpolation. Compare only bins with voiced estimates in both clips. This is not syllable alignment or tone error.', 'screen_method':'Existing agreement_screen_pass mask from baseline; compare same-bin medians using original unfiltered utterance F0 normalization. May be sparse or biased.','group_summary':'Per-dimension category counts and feature medians/ranges only; no correlations, p-values, fitted model or aggregate rating. No nasality/acoustic association attempted.','dependencies':'Six sentences, two repeated generations each; not twelve independent linguistic items. One listener; low confidence retained, not reinterpreted.'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def describe(raw,duration):
 f=raw['frames'];voiced=runs(f,duration);unvoiced=runs([{**x,'voiced':not x['voiced']} for x in f],duration)
 pr=dist([x['f0_hz'] for x in raw['praat_native_frames']]);py=dist([x['f0_hz'] for x in f]);relative=dist([x['relative_pitch_semitones'] for x in f]);prarel=dist([x['praat_relative_semitones'] for x in f])
 paired=[x for x in f if x['signed_difference_semitones'] is not None];matched=[x for x in f if x['praat_voiced'] is not None]
 bins=[];screenbins=[]
 for b in range(CONFIG['temporal_bins']):
  values=[x for x in f if b/10<=x['timestamp_s']/duration<(b+1)/10]
  bins.append(dist([x['relative_pitch_semitones'] for x in values])['median']);screenbins.append(dist([x['relative_pitch_semitones'] for x in values if x['agreement_screen_pass']])['median'])
 changes=[abs(b['relative_pitch_semitones']-a['relative_pitch_semitones']) for a,b in zip(f,f[1:]) if a['f0_hz'] and b['f0_hz']]
 flags=collections.Counter(flag for x in f for flag in x['flags'].split('|') if flag)
 out={'duration_s':duration,'pyin_median_hz':py['median'],'pyin_min_hz':py['min'],'pyin_max_hz':py['max'],'pyin_p05_hz':py['p05'],'pyin_p95_hz':py['p95'],
  'praat_median_hz':pr['median'],'praat_min_hz':pr['min'],'praat_max_hz':pr['max'],'praat_p05_hz':pr['p05'],'praat_p95_hz':pr['p95'],
  'pyin_relative_p05_st':relative['p05'],'pyin_relative_p95_st':relative['p95'],'pyin_relative_width90_st':relative['p95']-relative['p05'] if relative['n'] else None,
  'praat_relative_p05_st':prarel['p05'],'praat_relative_p95_st':prarel['p95'],
  'pyin_voiced_percent':100*sum(x['voiced'] for x in f)/len(f),'praat_native_voiced_percent':100*sum(x['voiced'] for x in raw['praat_native_frames'])/len(raw['praat_native_frames']),
  'voiced_runs':len(voiced),'voiced_runs_per_second':len(voiced)/duration,'voiced_run_median_s':dist([x['duration_s'] for x in voiced])['median'],
  'unvoiced_runs':len(unvoiced),'unvoiced_run_median_s':dist([x['duration_s'] for x in unvoiced])['median'],'unvoiced_run_max_s':dist([x['duration_s'] for x in unvoiced])['max'],
  'median_adjacent_voiced_step_st':dist(changes)['median'],
  'pitch_disagreement_median_st':dist([abs(x['signed_difference_semitones']) for x in paired])['median'],
  'voicing_disagreement_percent':100*sum(x['voiced']!=x['praat_voiced'] for x in matched)/len(matched),
  'agreement_screen_percent':100*sum(x['agreement_screen_pass'] for x in f)/len(f),
  'flag_counts':dict(flags),'relative_contour_bins_st':bins,'screened_contour_bins_st':screenbins,
  'voiced_intervals':voiced,'unvoiced_intervals':unvoiced}
 return out

def deltas(n,a):
 def distance(key):
  pairs=[(x,y) for x,y in zip(n[key],a[key]) if x is not None and y is not None]
  return (float(np.mean([abs(x-y) for x,y in pairs])) if pairs else None,len(pairs))
 raw,count=distance('relative_contour_bins_st');screen,scount=distance('screened_contour_bins_st')
 return {'duration_ratio':a['duration_s']/n['duration_s'],'duration_delta_s':a['duration_s']-n['duration_s'],
  'voiced_percent_delta_pp':a['pyin_voiced_percent']-n['pyin_voiced_percent'],
  'relative_width90_delta_st':a['pyin_relative_width90_st']-n['pyin_relative_width90_st'],
  'coarse_relative_contour_difference_st':raw,'coarse_contour_common_bins':count,'screened_coarse_contour_difference_st':screen,'screened_common_bins':scount,
  'voiced_runs_per_second_delta':a['voiced_runs_per_second']-n['voiced_runs_per_second'],
  'pitch_disagreement_median_st':a['pitch_disagreement_median_st'],'voicing_disagreement_percent':a['voicing_disagreement_percent']}

def main():
 global OUT
 parser=argparse.ArgumentParser();parser.add_argument('review',type=Path);args=parser.parse_args();review=read(args.review)
 from review_revision import require_current
 require_current(review,'paired')
 if review.get('review_version')==2:OUT=BASE/'human-acoustic-v2'
 OUT.mkdir(exist_ok=True);original=OUT/'review.original.json'
 if original.exists() and original.read_bytes()!=args.review.read_bytes():raise ValueError('Existing review differs; use new analysis version')
 definition=read(BASE/'review_form_definition.json');defs={s['sentence_id']:s for s in definition['items']};gen={x['generation_id']:x for x in read(BASE/'generation_manifest.json')};comparisons={x['source_id']:x for x in read(BASE/'paired_comparisons.json')['pairs']}
 assert len(review['items'])==6 and len({s['sentence_id'] for s in review['items']})==6
 joined=[];pairedrows=[];wide=[];repeat=[];seen=set();inputs=[args.review,BASE/'paired_comparisons.json',BASE/'review_form_definition.json',BASE/'generation_manifest.json']
 for item in review['items']:
  s=defs[item['sentence_id']];assert item['source_clip_id']==s['source_clip_id'] and item['exact_yoruba_text']==s['exact_text']
  natural_path=ROOT/'work/slr86/audio'/(s['source_clip_id']+'.wav');assert sha(natural_path)==s['natural_audio_sha256']==item['natural_reference']['audio_sha256']
  nrpath=ROOT/'work/slr86/natural-baseline-001/clips'/s['source_clip_id']/'raw.json';nr=read(nrpath);inputs.append(nrpath);n=describe(nr,s['natural_duration_s'])
  assert nr['report']['source']['sha256']==s['natural_audio_sha256'];w={'sentence_id':s['sentence_id'],'source_id':s['source_clip_id'],'exact_text':s['exact_text']}
  def addtable(label,features):
   plain={k:v for k,v in features.items() if not isinstance(v,(list,dict))};pairedrows.append({'sentence_id':s['sentence_id'],'source_id':s['source_clip_id'],'recording':label,**plain,'flag_counts':json.dumps(features['flag_counts'])})
   w.update({label+'_'+k:v for k,v in plain.items()})
  addtable('natural',n);annotations=item['ai_annotations'];assert len(annotations)==2
  for a in annotations:
   gid=a['ai_generation_id'];assert gid not in seen;seen.add(gid);g=gen[gid]
   assert a['sentence_id']==s['sentence_id'] and a['source_clip_id']==s['source_clip_id']==g['source_id']
   for key,expected in [('provider',g['provider']),('model_snapshot',g['requested_model_snapshot']),('voice',g['request']['voice']),('audio_sha256',g['audio_sha256']),('repeat_generation_id',g['repeat_generation_id'])]:assert a[key]==expected
   assert a['reviewer_identifier']==review['reviewer_identifier'];assert sha(ROOT/g['audio_path'])==g['audio_sha256'];assert g['request']['input']==s['exact_text']
   for dim in DIMS:assert a['ratings'][dim] in definition['rating_options'][dim]
   assert set(a['issue_tags'])<=set(definition['issue_tags'])
   for t in a['problematic_time_intervals']:assert 0<=t['start_s']<t['end_s']<=g['duration_s']
   rp=BASE/'measurements'/gid/'raw.json';raw=read(rp);inputs.append(rp);assert raw['report']['source']['sha256']==g['audio_sha256']
   ai=describe(raw,g['duration_s']);difference=deltas(n,ai);label='ai'+str(g['repeat_generation_id']);addtable(label,ai)
   joined.append({'sentence_id':s['sentence_id'],'exact_yoruba_text':s['exact_text'],'natural_reference_source_clip':s['source_clip_id'],'ai_generation_id':gid,'generation_provenance':g,'human_annotation':a,'natural_reference_annotation':item['natural_reference'],'natural_acoustic_measurements':comparisons[s['source_clip_id']]['natural'],'ai_acoustic_measurements':next(x['measurements'] for x in comparisons[s['source_clip_id']]['ai'] if x['generation_id']==gid),'natural_descriptors':n,'ai_descriptors':ai,'paired_descriptive_differences':difference,'source_frame_artifacts':[str(nrpath.relative_to(ROOT)),str(rp.relative_to(ROOT))]})
  wide.append(w);aa=sorted(annotations,key=lambda a:a['repeat_generation_id']);repeat.append({'sentence_id':s['sentence_id'],'dimension_comparisons':{dim:{'generation_1':aa[0]['ratings'][dim],'generation_2':aa[1]['ratings'][dim],'same':aa[0]['ratings'][dim]==aa[1]['ratings'][dim]} for dim in DIMS},'tags_generation_1':aa[0]['issue_tags'],'tags_generation_2':aa[1]['issue_tags']})
 assert seen==set(gen) and len(joined)==12
 if review.get('review_version')==2:
  qcpath=ROOT/'work/slr86/natural-baseline-001/qc-ingest-v2/qc_review_joined.json'
  qc={r['source_id']:r for r in read(qcpath)};inputs.append(qcpath)
  for r in joined:
   r['natural_transcript_qc_v2']=qc[r['natural_reference_source_clip']]
   r['natural_reference_requires_review']=qc[r['natural_reference_source_clip']]['judgment']!='transcript matches audio'
 original.write_bytes(args.review.read_bytes());dump(OUT/'analysis_config.json',CONFIG);dump(OUT/'joined_annotation_measurements.json',joined)
 flat=[]
 for r in joined:
  a=r['human_annotation'];flat.append({'sentence_id':r['sentence_id'],'source_id':r['natural_reference_source_clip'],'exact_yoruba_text':r['exact_yoruba_text'],'ai_generation_id':r['ai_generation_id'],'model_snapshot':a['model_snapshot'],'voice':a['voice'],'reviewer':a['reviewer_identifier'],'annotation_timestamp':a['annotation_timestamp'],**a['ratings'],'issue_tags':json.dumps(a['issue_tags'],ensure_ascii=False),'notes':a['notes'],'time_intervals':json.dumps(a['problematic_time_intervals'],ensure_ascii=False),**{'paired_'+k:v for k,v in r['paired_descriptive_differences'].items()},**{'natural_'+k:v for k,v in r['natural_descriptors'].items() if not isinstance(v,(list,dict))},**{'ai_'+k:v for k,v in r['ai_descriptors'].items() if not isinstance(v,(list,dict))}})
 csvout(OUT/'joined_annotation_measurements.csv',flat);csvout(OUT/'sentence_level_paired_comparison.csv',wide);csvout(OUT/'paired_recording_descriptors.csv',pairedrows)
 csvout(OUT/'generation_review_summary.csv',[{k:r[k] for k in ['sentence_id','ai_generation_id',*DIMS,'issue_tags','notes','time_intervals']} for r in flat]);dump(OUT/'repeat_comparison.json',repeat)
 counts={d:{choice:sum(r['human_annotation']['ratings'][d]==choice for r in joined) for choice in definition['rating_options'][d]} for d in DIMS}
 tags={t:sum(t in r['human_annotation']['issue_tags'] for r in joined) for t in definition['issue_tags']}
 summary={'rating_counts':counts,'issue_tag_counts':tags,'takes_with_any_tags':sum(bool(r['human_annotation']['issue_tags']) for r in joined),'takes_with_notes':sum(bool(r['human_annotation']['notes']) for r in joined),'takes_with_intervals':sum(bool(r['human_annotation']['problematic_time_intervals']) for r in joined),'natural_references_with_new_notes':sum(bool(s['natural_reference']['notes']) for s in review['items']),'cautions':['All 12 reviewer confidence entries are low, preserved verbatim. No confidence-weighting applied.','Unchecked optional issue tags mean not selected, not absence of the problem.','No new natural-reference ratings were supplied; prior transcript matching is not a pronunciation rating.','12 takes are clustered within 6 sentences, one listener, one model/voice; category imbalance and saturated ratings prevent predictive validation.']}
 summary['cautions'][0]='Reviewer confidence is preserved exactly as exported; no confidence weighting or reinterpretation is applied.'
 summary['cautions'][-1]='12 takes are clustered within 6 sentences, one listener, one model/voice; inspect category counts and variability before interpreting associations.'
 dump(OUT/'review_summary.json',summary)
 association={}
 for dim in DIMS[:-1]:
  if dim=='perceived_nasality':association[dim]={'status':'PERCEPTUAL_ONLY','counts':counts[dim],'acoustic_association':'NOT_ATTEMPTED: F0 does not measure nasality','future_features':['A1-P0/A1-P1-type harmonic/formant relationships','F1 bandwidth','spectral tilt','vowel/segment duration and spectral trajectories'],'requirements':'Verified vowel/segment alignment, robust formant/harmonic tracking, speaker/channel controls, native interval labels; features exploratory, not validated Yorùbá nasality measures.'};continue
  categories=sorted({r['human_annotation']['ratings'][dim] for r in joined});groups={}
  for category in categories:
   subset=[r for r in joined if r['human_annotation']['ratings'][dim]==category]
   groups[category]={'n_takes':len(subset),'n_sentences':len({r['sentence_id'] for r in subset}),'generation_ids':[r['ai_generation_id'] for r in subset],'features':{key:dist([r['paired_descriptive_differences'][key] for r in subset]) for key in ['duration_ratio','duration_delta_s','voiced_percent_delta_pp','relative_width90_delta_st','coarse_relative_contour_difference_st','screened_coarse_contour_difference_st','voiced_runs_per_second_delta','pitch_disagreement_median_st','voicing_disagreement_percent']}}
  association[dim]={'status':'NO_RATING_VARIATION' if len(categories)==1 else 'DESCRIPTIVE_ONLY_IMBALANCED_GROUPS','groups':groups,'no_statistical_or_predictive_claim':True}
 dump(OUT/'exploratory_associations.json',association)
 os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'));import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 ids=[r['ai_generation_id'].replace('_coral','') for r in joined]
 overall_categories=sorted({r['human_annotation']['ratings']['overall_yoruba_naturalness'] for r in joined})
 palette=dict(zip(overall_categories,plt.get_cmap('tab10').colors));colors=[palette[r['human_annotation']['ratings']['overall_yoruba_naturalness']] for r in joined]
 fig,axes=plt.subplots(2,3,figsize=(15,9))
 for ax,key,title in zip(axes.flat,['duration_ratio','voiced_percent_delta_pp','relative_width90_delta_st','coarse_relative_contour_difference_st','pitch_disagreement_median_st','voiced_runs_per_second_delta'],['Duration / natural duration','Voiced-frame difference (percentage points)','Relative pitch 5–95% width difference (st)','Coarse contour-bin difference (st; unaligned)','pYIN–Praat median disagreement (st)','Voiced runs per second: AI minus natural']):
  values=[r['paired_descriptive_differences'][key] for r in joined];ax.scatter(range(12),values,c=colors);ax.set_xticks(range(12),ids,rotation=80,fontsize=8);ax.set_title(title,fontsize=10);ax.axhline(1 if key=='duration_ratio' else 0,color='grey',lw=.6);ax.grid(alpha=.2)
 from matplotlib.lines import Line2D
 fig.legend(handles=[Line2D([0],[0],marker='o',ls='',color=palette[c],label=f'Human: {c} ({counts["overall_yoruba_naturalness"][c]})') for c in overall_categories],loc='upper center',bbox_to_anchor=(.5,.96),ncol=2)
 fig.suptitle('Exploratory measurements and one listener’s overall category — no fitted prediction',y=.995);fig.tight_layout(rect=[0,0,1,.91]);fig.savefig(OUT/'human_acoustic_patterns.png',dpi=150,bbox_inches='tight');plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(15,8));xx=(np.arange(10)+.5)/10
 for ax,s in zip(axes.flat,review['items']):
  group=[r for r in joined if r['sentence_id']==s['sentence_id']];ax.plot(xx,group[0]['natural_descriptors']['relative_contour_bins_st'],label='Natural',color='black')
  for r in group:ax.plot(xx,r['ai_descriptors']['relative_contour_bins_st'],label='AI '+str(r['human_annotation']['repeat_generation_id']))
  ax.set(title=s['sentence_id'],xlabel='Fraction of file duration (not syllable aligned)',ylabel='Own-utterance relative pitch (semitones)');ax.legend(fontsize=8)
 fig.suptitle('Coarse relative-pitch trajectories; missing bins retained; no tone interpretation');fig.tight_layout();fig.savefig(OUT/'relative_contour_bins.png',dpi=150);plt.close(fig)
 versiondir=OUT/'versions';versiondir.mkdir(exist_ok=True)
 scripts=['scripts/explore_human_acoustics.py','scripts/generate_paired_ai.py','scripts/analyze_paired_ai.py','scripts/validate_acoustic_measurements.py','scripts/build_natural_baseline.py','scripts/audit_natural_baseline.py','src/acoustic_analysis.py']
 versionrecords=[]
 for name in scripts:
  p=ROOT/name;dest=versiondir/name.replace('/','__');shutil.copyfile(p,dest);versionrecords.append({'path':name,'sha256':sha(p),'snapshot':dest.name})
 for p in [BASE/'configuration.json',OUT/'analysis_config.json']:
  shutil.copyfile(p,versiondir/p.name)
 git=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
 dump(OUT/'reproducibility.json',{'script_snapshots':versionrecords,'git_head':git.stdout.strip() if git.returncode==0 else None,'git_note':'Working files may be uncommitted; copied scripts and hashes are authoritative.','packages':{k:importlib.metadata.version(k) for k in ['numpy','librosa','praat-parselmouth','soundfile','matplotlib']},'input_artifacts':[{'path':str(p),'sha256':sha(p)} for p in inputs],'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':CONFIG})
 dump(OUT/'validation.json',{'joined':12,'sentences':6,'source_text_ids_provenance_audio_hashes_verified':True,'original_review_preserved':sha(original)==sha(args.review),'trained_model':False,'combined_score':False,'new_audio_generated':False,'nasality_acoustic_inference':False})
 print(json.dumps(summary,indent=2,ensure_ascii=False));print('All exploratory outputs saved to',OUT)
if __name__=='__main__':main()
