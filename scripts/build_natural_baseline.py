"""Natural corpus descriptive baseline. No linguistic scoring or audio modification."""
import argparse,collections,csv,hashlib,html,json,os,random,sys
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from acoustic_analysis import sha256
from validate_acoustic_measurements import compare,PRAAT,summary,csvout
import parselmouth
OUT=ROOT/'work/slr86/natural-baseline-001'

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def dist(values):
    a=np.asarray([v for v in values if v is not None and np.isfinite(v)],dtype=float)
    if not len(a):return {'n':0,'min':None,'p05':None,'p25':None,'median':None,'p75':None,'p95':None,'max':None,'sd':None}
    return dict(zip(('n','min','p05','p25','median','p75','p95','max','sd'),[len(a),float(a.min()),*map(float,np.percentile(a,[5,25,50,75,95])),float(a.max()),float(a.std())]))
def review_flags(r):
    q=r['text_quality'];f=[]
    if any(k not in 'aeiouẹọ' for k in q['vowel_counts']):f.append('unusual_underdot_requires_review')
    if q['conflicting_tone_units']:f.append('conflicting_tone_marks')
    if q['unmarked_vowel_units']:f.append('unmarked_vowels_mid_or_unspecified')
    f+=['source_annotation:'+a for a in q['annotations']]
    return f

def prepare(manifest):
    OUT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(860220);chosen={};reasons=collections.defaultdict(list)
    def add(r,why):chosen[r['source_item_id']]=r;reasons[r['source_item_id']].append(why)
    for speaker in sorted({r['speaker_id'] for r in manifest}):
        pool=sorted([r for r in manifest if r['speaker_id']==speaker],key=lambda r:r['source_item_id'])
        add(rng.choice(pool),'seeded_speaker_coverage')
    for r in manifest:
        if 'unusual_underdot_requires_review' in review_flags(r):add(r,'flagged_unicode')
    rate=lambda r:r['text_quality']['explicit_tone_units']/r['text_quality']['vowel_units']
    for r,why in [(min(manifest,key=lambda r:r['duration_s']),'shortest'),(max(manifest,key=lambda r:r['duration_s']),'longest'),(min(manifest,key=rate),'lowest_explicit_mark_density_not_proven_incomplete'),(max(manifest,key=rate),'highest_explicit_mark_density')]:add(r,why)
    while len(chosen)<20:
        remaining=[r for r in manifest if r['source_item_id'] not in chosen]
        counts=collections.Counter(r['speaker_id'] for r in chosen.values())
        mincount=min(counts[r['speaker_id']] for r in remaining)
        pool=[r for r in remaining if counts[r['speaker_id']]==mincount]
        add(rng.choice(sorted(pool,key=lambda r:r['source_item_id'])),'seeded_balanced_fill')
    rows=[]
    for r in sorted(chosen.values(),key=lambda r:r['source_item_id']):
        q=r['text_quality']
        rows.append({'source_id':r['source_item_id'],'speaker_id':r['speaker_id'],'duration_s':r['duration_s'],
          'audio':'../audio/'+r['source_item_id']+'.wav','sha256':r['sha256'],'exact_transcript':r['transcript_original'],
          'flags':review_flags(r),'selection_reasons':reasons[r['source_item_id']],
          'explicit_mark_rate':rate(r),'vowel_counts':q['vowel_counts'],'nasal_spelling_candidates':q['nasal_vowel_spelling_candidates'],
          'review_status':'pending','judgment':None,'reviewer':None,'confidence':None,'notes':'','problem_intervals':[]})
    dump(OUT/'qc_sample.json',{'seed':860220,'items':rows,'listening_status':'NOT_PERFORMED_BY_AUTOMATION','note':'No automatic linguistic match judgments. Original transcripts retained.'})
    cards=[]
    for r in rows:
        e=html.escape
        options=''.join('<option>'+x+'</option>' for x in ['transcript matches audio','minor uncertainty','mismatch','cannot determine'])
        cards.append(f'''<article data-id="{r['source_id']}"><h2>{r['source_id']}</h2><p>Speaker {r['speaker_id']} · {r['duration_s']:.3f} seconds</p><audio controls preload="none" src="{r['audio']}"></audio><p lang="yo" class="transcript">{e(r['exact_transcript'])}</p><p>{e(', '.join(r['flags']))}</p><label>Review <select><option value="">Pending — not reviewed</option>{options}</select></label><label>Confidence <select class="confidence"><option value="">Not supplied</option><option>low</option><option>medium</option><option>high</option></select></label><label>Notes / problematic time intervals <textarea></textarea></label></article>''')
    page='''<!doctype html><meta charset="utf-8"><title>SLR86: 20-clip listening QC</title><style>body{font:17px system-ui;max-width:1000px;margin:30px auto;background:#f4f5f7;color:#172331}article{background:white;padding:22px;margin:20px 0;border:1px solid #ccd4de;border-radius:10px}.transcript{font-size:23px}audio{width:100%}label{display:block;margin:12px 0}textarea{display:block;width:95%;height:70px}button,select,input{font:inherit;padding:8px}</style><h1>Natural Yorùbá: bounded listening review</h1><p>20 reproducibly selected clips across all 12 speakers. Listen before choosing a judgment. Source text is unchanged. No linguistic matches have been automatically certified. Lower explicit tone-mark density does not prove incomplete marking.</p><label>Reviewer <input id="reviewer"></label><button id="export">Export review JSON</button><p id="status">Changes remain in this page until exported. Save the downloaded JSON beside qc_sample.json. Do not close before exporting.</p>'''+''.join(cards)+'''<script>document.getElementById('export').onclick=()=>{const items=[...document.querySelectorAll('article')].map(a=>({source_id:a.dataset.id,review_status:a.querySelector('select').value?'reviewed':'pending',judgment:a.querySelector('select').value||null,confidence:a.querySelector('.confidence').value||null,notes:a.querySelector('textarea').value}));const b=new Blob([JSON.stringify({reviewer:document.getElementById('reviewer').value||null,created_at:new Date().toISOString(),items},null,2)],{type:'application/json'});const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download='qc_human_review.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);document.getElementById('status').textContent='Review JSON exported. Preserve it alongside the sample.'};</script>'''
    (OUT/'qc_review.html').write_text(page,encoding='utf-8')
    tone=[]
    for r in manifest:
        serious=any(f in review_flags(r) for f in ('unusual_underdot_requires_review','conflicting_tone_marks'))
        tone.append({'source_id':r['source_item_id'],'category':'unsuitable_without_additional_review' if serious else 'partially_marked_or_uncertain',
          'explicit_mark_rate':rate(r),'strong_marking_candidate':rate(r)>=.70 and not serious,
          'reason':'Unusual orthography requires review' if serious else 'Source-provided; lexical tone and audio alignment not human verified. Unmarked vowels may be mid tone.',
          'suitable_confirmed':False})
    dump(OUT/'tone_subset.json',{'categories':{'suitable_for_lexical_tone_analysis':0,**dict(collections.Counter(r['category'] for r in tone))},'criterion':'Conservative ground-truth eligibility, not tone correctness. Explicit density >=70% is only a review-priority heuristic, not a suitability test.','items':tone})
    dump(OUT/'future_segmental_features.json',{'status':'PLANNED_NOT_RUN','features':[{'name':n,'value':None,'validated_for_yoruba_nasality':False} for n in ['A1-P0','A1-P1','F1 bandwidth','spectral tilt','segment duration','spectral trajectories']], 'required_context':['speaker and recording conditions','vowel identity and segment boundaries','formant/harmonic estimation reliability','native-listener nasality annotations','phonetic confounds and validation'], 'no_automatic_diagnosis':True})
    return rows

def extract(r):
    item=r['source_item_id'];d=OUT/'clips'/item;d.mkdir(parents=True,exist_ok=True)
    path=ROOT/'work/slr86/audio'/(item+'.wav')
    if sha256(path)!=r['sha256']:raise ValueError('Source changed: '+item)
    if (d/'raw.json').exists():
        saved=json.loads((d/'raw.json').read_text(encoding='utf-8'))
        if saved['report']['source']['sha256']!=r['sha256']:raise ValueError('Cached source mismatch')
        return saved
    report,frames,praat,pbase=compare(path,frame_length=4096)
    for f in frames:
        flags=f['flags'].split('|') if f['flags'] else []
        if f['edge_padded']:flags.append('edge_window')
        if f['f0_hz'] and f['f0_hz']>=500/1.05:flags.append('near_pyin_ceiling')
        if f['praat_f0_hz'] and (f['praat_f0_hz']<=65*1.05 or f['praat_f0_hz']>=500/1.05):flags.append('praat_near_search_limit')
        # Agreement mask is an engineering screen, not calibrated measurement confidence.
        f['agreement_screen_pass']=bool(f['f0_hz'] and f['praat_f0_hz'] and not flags and f['voicing_probability']>=.5 and f['praat_strength']>=.45 and abs(f['signed_difference_semitones'])<=.5)
        f['flags']='|'.join(flags)
    data={'source_id':item,'speaker_id':r['speaker_id'],'report':report,'frames':frames,'praat_native_frames':praat}
    dump(d/'raw.json',data);csvout(d/'praat_native_frames.csv',praat)
    return data

def finalize(data):
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    speakers={};cliprows=[];allframes=[]
    for s in sorted({r['speaker_id'] for r in data}):
        clips=[r for r in data if r['speaker_id']==s];frames=[f for r in clips for f in r['frames']]
        py=dist([f['f0_hz'] for f in frames]);pr=dist([f['f0_hz'] for r in clips for f in r['praat_native_frames']])
        speakers[s]={'clips':len(clips),'pyin_hz':py,'praat_native_hz':pr,'duration_s':dist([r['report']['summary']['duration_s'] for r in clips]),
          'clip_median_pyin_hz':dist([r['report']['summary']['median_f0_hz'] for r in clips]),
          'pyin_voiced_percent':100*sum(f['voiced'] for f in frames)/len(frames),
          'agreement_screen_percent_all_frames':100*sum(f['agreement_screen_pass'] for f in frames)/len(frames),
          'normalization':'12*log2(F0 / pooled voiced-frame median for this speaker and estimator); duration-weighted, 10 clips, descriptive sample baseline'}
        for key,base in [('pyin',py['median']),('praat',pr['median'])]:
            values=[f['f0_hz' if key=='pyin' else 'praat_f0_hz'] for f in frames]
            speakers[s][key+'_relative_semitones']=dist([12*np.log2(v/base) for v in values if v and base])
    for r in data:
        d=OUT/'clips'/r['source_id'];frames=r['frames'];s=speakers[r['speaker_id']]
        for f in frames:
            for name,key,basekey in [('pyin','f0_hz','pyin_hz'),('praat','praat_f0_hz','praat_native_hz')]:
                base=s[basekey]['median'];f[name+'_speaker_relative_st']=float(12*np.log2(f[key]/base)) if f[key] and base else None
        csvout(d/'frames.csv',frames)
        dur=r['report']['summary']['duration_s'];agreement=summary(frames,0,dur)
        flags=collections.Counter(flag for f in frames for flag in f['flags'].split('|') if flag)
        rr={**r['report'],'speaker_id':r['speaker_id'],'praat_method':{'settings':PRAAT,'parselmouth_version':parselmouth.VERSION,'praat_version':parselmouth.PRAAT_VERSION,'algorithm':'raw autocorrelation'},
          'alignment':'Nearest native Praat center within 5 ms, no interpolation. Native grid preserved. Missing match is not unvoiced.',
          'speaker_normalization':{'pyin_reference_hz':s['pyin_hz']['median'],'praat_reference_hz':s['praat_native_hz']['median'],'equation':'12*log2(F0 / speaker_estimator_pooled_voiced_median)','scope':'ten clips, pooled frames; no outlier removal'},
          'agreement':agreement,'frame_flag_counts':dict(flags),'rms_dbfs_distribution':dist([f['rms_dbfs'] for f in frames]),
          'agreement_screen_pass_percent':100*sum(f['agreement_screen_pass'] for f in frames)/len(frames)}
        dump(d/'analysis.json',rr)
        cliprows.append({'source_id':r['source_id'],'speaker_id':r['speaker_id'],**r['report']['summary'],
          'praat_median_hz':dist([f['f0_hz'] for f in r['praat_native_frames']])['median'],
          'agreement_screen_percent':rr['agreement_screen_pass_percent'],
          'median_absolute_disagreement_st':agreement['median_absolute_semitones'],
          'flagged_frames':sum(bool(f['flags']) for f in frames),'flags':'|'.join(flags),
          'warnings':'|'.join(r['report']['warnings'])})
        allframes.extend(frames)
        t=[f['timestamp_s'] for f in frames];fig,axes=plt.subplots(2,1,figsize=(10,5),sharex=True)
        for k,label in [('f0_hz','pYIN'),('praat_f0_hz','Praat')]:axes[0].plot(t,[f[k] if f[k] else np.nan for f in frames],'.-',ms=1,lw=.7,label=label)
        for k,label in [('pyin_speaker_relative_st','pYIN'),('praat_speaker_relative_st','Praat')]:axes[1].plot(t,[f[k] if f[k] is not None else np.nan for f in frames],lw=.7,label=label)
        axes[0].set(title=r['source_id']+' — descriptive only; gaps retained',ylabel='F0 (Hz)');axes[0].legend();axes[1].set(ylabel='Speaker-relative semitones',xlabel='Time (s)');fig.tight_layout();fig.savefig(d/'contour.png',dpi=120);plt.close(fig)
    dump(OUT/'speaker_baselines.json',speakers);csvout(OUT/'clip_summary.csv',cliprows)
    csvout(OUT/'speaker_summary.csv',[{'speaker_id':s,'clips':v['clips'],'pyin_median_hz':v['pyin_hz']['median'],'pyin_p05_hz':v['pyin_hz']['p05'],'pyin_p95_hz':v['pyin_hz']['p95'],'praat_median_hz':v['praat_native_hz']['median'],'pyin_voiced_percent':v['pyin_voiced_percent'],'relative_p05_st':v['pyin_relative_semitones']['p05'],'relative_p95_st':v['pyin_relative_semitones']['p95'],'clip_median_f0_sd_hz':v['clip_median_pyin_hz']['sd']} for s,v in speakers.items()])
    both=[f for f in allframes if f['signed_difference_semitones'] is not None];matched=[f for f in allframes if f['praat_voiced'] is not None]
    corpus={'clips':len(data),'speakers':len(speakers),'total_duration_s':sum(r['duration_s'] for r in cliprows),'clip_duration_s':dist([r['duration_s'] for r in cliprows]),
      'pooled_pyin_hz':dist([f['f0_hz'] for f in allframes]),'between_speaker_median_hz':dist([s['pyin_hz']['median'] for s in speakers.values()]),
      'speaker_relative_pyin_st':dist([f['pyin_speaker_relative_st'] for f in allframes]),
      'frame_count':len(allframes),'pyin_voiced_percent':100*sum(f['voiced'] for f in allframes)/len(allframes),
      'matched_frames':len(matched),'both_voiced_frames':len(both),'voicing_disagreement_percent_matched':100*sum(f['voiced']!=f['praat_voiced'] for f in matched)/len(matched),
      'absolute_disagreement_st':dist([abs(f['signed_difference_semitones']) for f in both]),
      'both_voiced_within_half_semitone_percent':100*sum(abs(f['signed_difference_semitones'])<=.5 for f in both)/len(both),
      'agreement_screen_percent_all_frames':100*sum(f['agreement_screen_pass'] for f in allframes)/len(allframes),
      'frame_flag_counts':dict(collections.Counter(flag for f in allframes for flag in f['flags'].split('|') if flag)),
      'qc_status':'20 supplied for human listening; no linguistic judgments invented',
      'limitations':['Small read-speech pilot, not normative Yoruba correctness distributions.','Estimator agreement is not ground truth.','Voicing is not speech activity; unvoiced consonants and silence are not separated.','pYIN probability and Praat strength are different uncalibrated quantities.','RMS is digital amplitude, not calibrated loudness.','Speaker baselines pool voiced frames; longer clips carry more weight.','65–500 Hz search limits can censor extremes; flags retained.','No syllable alignment or validated nasality measures.'],
      'scores':'UNSCORED','sources_preserved':True}
    dump(OUT/'corpus_summary.json',corpus)
    dump(OUT/'problematic_recordings.json',[r for r in cliprows if r['flags'] or r['warnings']])
    fig,axes=plt.subplots(2,2,figsize=(13,9));labels=list(speakers);x=np.arange(len(labels))
    med=np.array([speakers[s]['pyin_hz']['median'] for s in labels]);lo=np.array([speakers[s]['pyin_hz']['p05'] for s in labels]);hi=np.array([speakers[s]['pyin_hz']['p95'] for s in labels])
    axes[0,0].errorbar(x,med,yerr=[med-lo,hi-med],fmt='o',capsize=3);axes[0,0].set_xticks(x,labels,rotation=65);axes[0,0].set(title='Speaker pYIN median and 5–95% voiced-frame range',ylabel='Hz')
    axes[0,1].hist([r['duration_s'] for r in cliprows],bins=16);axes[0,1].set(title='Clip durations',xlabel='Seconds',ylabel='Clips')
    axes[1,0].hist([f['pyin_speaker_relative_st'] for f in allframes if f['pyin_speaker_relative_st'] is not None],bins=70);axes[1,0].set(title='Pooled speaker-relative pitch (frame weighted)',xlabel='Semitones relative to own speaker median',ylabel='Voiced frames')
    axes[1,1].hist([abs(f['signed_difference_semitones']) for f in both],bins=70);axes[1,1].set(title='pYIN–Praat absolute disagreement, both voiced',xlabel='Semitones',ylabel='Frames')
    fig.suptitle('Natural Yorùbá pilot — descriptive distributions, not correctness boundaries');fig.tight_layout();fig.savefig(OUT/'natural_baseline.png',dpi=150);plt.close(fig)
    print(json.dumps(corpus,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    manifest=[json.loads(x) for x in (ROOT/'work/slr86/pilot_manifest.jsonl').read_text(encoding='utf-8').splitlines()]
    validation={r['source_item_id']:r for r in json.loads((ROOT/'work/slr86/audio_validation.json').read_text(encoding='utf-8'))}
    manifest=[{**r,**{k:validation[r['source_item_id']][k] for k in ('duration_s','sha256')}} for r in manifest]
    prepare(manifest)
    if args.prepare_only:return
    data=[]
    for i,r in enumerate(manifest):
        data.append(extract(r));print(f'{i+1}/120 extracted {r["source_item_id"]}',flush=True)
    finalize(data)
if __name__=='__main__':main()
