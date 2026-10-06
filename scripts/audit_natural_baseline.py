"""Audit and link baseline outputs; derive descriptive timing with explicit grid limits."""
import collections,json,sys
from pathlib import Path
import numpy as np
import soundfile as sf
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_natural_baseline import OUT,dist,dump,sha256

def runs(frames,duration,key='voiced'):
    result=[];start=None
    for i,f in enumerate(frames):
        left=max(0,f['timestamp_s']-.005);right=min(duration,f['timestamp_s']+.005)
        if f[key] and start is None:start=left
        if start is not None and (not f[key] or i==len(frames)-1):
            end=left if not f[key] else right
            result.append({'start_s':start,'end_s':end,'duration_s':end-start});start=None
    return result

def main():
    source=[json.loads(x) for x in (ROOT/'work/slr86/natural_reference.jsonl').read_text(encoding='utf-8').splitlines()]
    qc=json.loads((OUT/'qc_sample.json').read_text(encoding='utf-8'));qcids={r['source_id'] for r in qc['items']}
    validator=jsonschema.Draft202012Validator(json.loads((ROOT/'evaluation/supervised_example.schema.json').read_text(encoding='utf-8')))
    linked=[];signals=[];timing=[];speaker_runs=collections.defaultdict(list)
    reliability=[];screened=collections.defaultdict(list);native_praat=[]
    for record in source:
        item=record['natural_source']['source_item_id'];speaker=record['natural_source']['speaker_id'];d=OUT/'clips'/item
        raw=json.loads((d/'raw.json').read_text(encoding='utf-8'));analysis=json.loads((d/'analysis.json').read_text(encoding='utf-8'))
        path=ROOT/record['audio']['path'];assert sha256(path)==record['audio']['sha256']==analysis['source']['sha256']
        y,sr=sf.read(path);frames=raw['frames'];regions=runs(frames,len(y)/sr);speaker_runs[speaker].extend(r['duration_s'] for r in regions)
        native_praat.extend(raw['praat_native_frames'])
        screened[speaker].extend(f['f0_hz'] for f in frames if f['agreement_screen_pass'])
        matched=[f for f in frames if f['praat_voiced'] is not None]
        both=[f for f in frames if f['signed_difference_semitones'] is not None]
        reliability.append({'source_id':item,'speaker_id':speaker,
          'voicing_disagreement_percent_matched':100*sum(f['voiced']!=f['praat_voiced'] for f in matched)/len(matched),
          'median_absolute_pitch_difference_st':dist([abs(f['signed_difference_semitones']) for f in both])['median'],
          'possible_octave_frames':sum('possible_octave_disagreement' in f['flags'] for f in frames),
          'pyin_near_floor_frames':sum('near_pyin_floor' in f['flags'] for f in frames),
          'agreement_screen_percent':100*sum(f['agreement_screen_pass'] for f in frames)/len(frames)})
        signal={'source_id':item,'speaker_id':speaker,'duration_s':len(y)/sr,'peak_amplitude':float(np.max(abs(y))),
          'whole_clip_rms_dbfs':float(20*np.log10(np.sqrt(np.mean(y*y)))),'digital_rail_samples':int(np.sum((y>=32767/32768)|(y<=-1))),
          'all_zero':bool(np.all(y==0)),'finite':bool(np.isfinite(y).all()),'voiced_runs':regions,
          'voiced_run_duration_s':dist([r['duration_s'] for r in regions]),'timing_interpretation':'pYIN frame-cell runs, half-hop edges, not syllables or verified speech boundaries. Window 85.33 ms; hop 10 ms.'}
        dump(d/'signal_timing.json',signal);timing.append(signal)
        if item in qcids:signals.append({**signal,'linguistic_review_status':'pending','mismatch_finding':None})
        for family in ('lexical_tone','prosody','rhythm_timing'):
            record['acoustic_measurements'].append({'family':family,'path':str((d/'analysis.json').relative_to(ROOT)).replace('\\','/'),'status':'descriptive_only','source_audio_sha256':record['audio']['sha256']})
        record['acoustic_measurements'].append({'family':'nasality_related','path':str((OUT/'future_segmental_features.json').relative_to(ROOT)).replace('\\','/'),'status':'not_implemented','source_audio_sha256':record['audio']['sha256']})
        record['speaker_normalized_measurements'].append({'family':'pitch','artifact_path':str((d/'frames.csv').relative_to(ROOT)).replace('\\','/'),
          'equation':'12*log2(F0 / pooled voiced-frame median for speaker and estimator)','baseline_scope':'ten natural-reference clips, frame weighted; unfiltered and provisional',
          'baseline_reference_ids':[r['example_id'] for r in source if r['natural_source']['speaker_id']==speaker],'status':'provisional'})
        validator.validate(record);linked.append(record)
    (OUT/'natural_reference_with_features.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in linked),encoding='utf-8')
    dump(OUT/'qc_signal_checks.json',{'items':signals,'confirmed_linguistic_mismatches':None,'reason':'Human listening judgments pending. Signal checks cannot establish transcript match.'})
    dump(OUT/'timing_summary.json',{'speaker_voiced_run_duration_s':{s:dist(v) for s,v in speaker_runs.items()},'clips':timing})
    dump(OUT/'reliability_detail.json',{'clips':reliability,
      'praat_native_frame_count':len(native_praat),'praat_native_voiced_percent':100*sum(f['voiced'] for f in native_praat)/len(native_praat),
      'screened_pyin_by_speaker':{s:dist(v) for s,v in screened.items()},
      'screen_definition':'Both voiced; pYIN probability >=0.5; Praat strength >=0.45; difference <=0.5 semitones; no edge/search-limit flags. Engineering heuristic, not calibrated confidence.',
      'interpretation':'Screened sensitivity summaries complement, never replace, raw baseline and frames. Selective screening can bias distributions.'})
    dump(OUT/'baseline_validation.json',{'clips':len(linked),'source_hashes_preserved':True,'linked_schema_records_valid':True,'qc_pending':len(signals),'linguistic_mismatches':'NOT_DETERMINED','scores':'UNSCORED','first_paired_comparison_ready':False,'remaining_gates':['Native listening review of bounded QC sample','Review problematic measurements and intended paired sentences','User approval before AI generation']})
    print('120 source hashes and feature-linked schema records validated; 20 listening judgments pending.')
if __name__=='__main__':main()
