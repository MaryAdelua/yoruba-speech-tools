"""Ingest bounded human QC as a separate immutable evidence overlay; no text repair."""
import argparse,collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/slr86/natural-baseline-001'
CHOICES={'transcript matches audio','minor uncertainty','mismatch','cannot determine'}
PROPOSALS={
'yof_01208_01850003899':('ọ; nasal spellings in Wọ́n/Àdùnní; n consonants; repeated ja/ti sequence','Short utterance for inspectable alignment, nasal segments and rhythm.'),
'yof_02436_02038636916':('o/ọ; ẹ; m/n; syllabic ń; nasal spelling environments','Compact vowel-contrast and nasal-context example; relatively low estimator voicing disagreement.'),
'yof_02121_01178327964':('e/ẹ and o/ọ; s/ṣ; acute/grave-marked vowels','Contrasting vowel and consonant spellings with varied tone marks and a longer phrase.'),
'yof_09697_01103354325':('e/ẹ; ọ; syllabic ń; nasal spelling in rán; ilé-ìwé','Longer clean utterance for phrase-level timing and vowel/nasal comparisons.'),
'yom_00295_01260038205':('e/ẹ; ọ; m/n consonants; repeated ẹ vowels and acute/grave marks','Compact e/ẹ comparison with relatively dense explicit tone marking.'),
'yom_07508_00859742057':('o/ọ; syllabic ń; nasal spelling in súnkún/tọ̀san; plain s','Short nasal-rich counterpart for segment duration and pitch-context inspection.')}

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('review',type=Path);args=parser.parse_args()
    original=args.review.read_bytes();review=json.loads(original.decode('utf-8-sig'))
    from review_revision import require_current
    require_current(review,'natural')
    sample=json.loads((BASE/'qc_sample.json').read_text(encoding='utf-8'))['items'];byid={r['source_id']:r for r in sample}
    rows=review['items'];ids=[r['source_id'] for r in rows]
    if len(ids)!=len(set(ids)) or set(ids)!=set(byid):raise ValueError('Review IDs must match all 20 sampled IDs exactly, without duplicates')
    for r in rows:
        if r['review_status']!='reviewed' or r['judgment'] not in CHOICES:raise ValueError('Incomplete or invalid judgment')
        if r['confidence'] not in ('low','medium','high',None) or not isinstance(r['notes'],str):raise ValueError('Invalid confidence/notes')
        audio=ROOT/'work/slr86/audio'/(r['source_id']+'.wav')
        if hashlib.sha256(audio.read_bytes()).hexdigest()!=byid[r['source_id']]['sha256']:raise ValueError('Reviewed source audio has changed')
    out=BASE/('qc-ingest-v2' if review.get('review_version')==2 else 'qc-ingest-001');out.mkdir(exist_ok=True)
    dst=out/'qc_human_review.original.json'
    if dst.exists() and dst.read_bytes()!=original:raise ValueError('Existing review differs; use a new versioned ingestion directory')
    dst.write_bytes(original)
    joined=[]
    for r in rows:
        joined.append({**byid[r['source_id']],**r,'reviewer':review['reviewer'],'review_created_at':review['created_at'],
         'evidence_type':'human_listener_judgment_not_acoustic_diagnosis','orthographic_flags_resolved':False,
         'note_on_flags':'Audio/text match does not automatically resolve unusual Unicode or establish exhaustive tone completeness.'})
    counts={c:sum(r['judgment']==c for r in rows) for c in sorted(CHOICES)}
    groups={'vowel_quality_e_ẹ':[],'consonant_s_ṣ':[],'source_event_annotation':[],'other':[]}
    issue_ids={'yof_09697_00099367593':'vowel_quality_e_ẹ','yom_08421_00493295037':'consonant_s_ṣ','yom_01523_01346428924':'source_event_annotation'}
    for r in rows:
        if r['notes']:groups[issue_ids.get(r['source_id'],'other')].append({'source_id':r['source_id'],'judgment':r['judgment'],'confidence':r['confidence'],'verbatim_note':r['notes']})
    dump(out/'qc_review_joined.json',joined)
    if review.get('review_version')==2:
        dump(out/'summary.json',{'review_version':2,'reviewer':review['reviewer'],'counts':counts,'input_sha256':hashlib.sha256(original).hexdigest(),
             'notes':[{'source_id':r['source_id'],'judgment':r['judgment'],'confidence':r['confidence'],'verbatim_note':r['notes']} for r in rows if r['notes']],
             'use_prior_human_reviews':False,'paired_set':'Previously approved six sentence identities retained; reassess eligibility from v2 findings rather than regenerate selections.'})
        print(json.dumps({'counts':counts,'output':str(out),'review_version':2}));return
    dump(out/'summary.json',{'reviewer':review['reviewer'],'created_at':review['created_at'],'input_sha256':hashlib.sha256(original).hexdigest(),
      'validated_ids':20,'counts':counts,'notes_by_issue_type':groups,'o_ọ_issue_reports':0,
      'recurrence':'Each reported issue type occurs once; no repeated specific confusion established in this 20-item sample.',
      'baseline_policy':'Retain all original 120 audio/measurements as descriptive corpus. Withhold 3 disputed items from clean paired references; keep uncertainty annotations. Two unusual Unicode items also deferred, despite positive listening judgments.',
      'baseline_recomputed':False,'tone_completeness':'Not separately audited. Do not promote utterance-level match to exhaustive lexical-tone ground truth.'})
    reliability={r['source_id']:r for r in json.loads((BASE/'reliability_detail.json').read_text())['clips']}
    pilot={r['source_item_id']:r for r in map(json.loads,(ROOT/'work/slr86/pilot_manifest.jsonl').read_text(encoding='utf-8').splitlines())}
    proposals=[]
    for item,(features,reason) in PROPOSALS.items():
        r=next(x for x in joined if x['source_id']==item)
        assert r['judgment']=='transcript matches audio' and r['confidence']=='high' and not r['notes']
        assert not any('source_annotation:' in f or 'unusual_underdot' in f for f in r['flags'])
        q=pilot[item]['text_quality'];a=reliability[item]
        assert not a['possible_octave_frames'] and not a['pyin_near_floor_frames']
        proposals.append({'source_id':item,'speaker_id':r['speaker_id'],'exact_yoruba_text':r['exact_transcript'],'duration_s':r['duration_s'],
          'audio_sha256':r['sha256'],'audio_path':str((ROOT/'work/slr86/audio'/(item+'.wav')).relative_to(ROOT)).replace('\\','/'),
          'qc_judgment':r['judgment'],'qc_confidence':r['confidence'],'tone_mark_completeness':'Not exhaustively verified; unmarked vowels can be mid tone, not automatically missing.',
          'explicit_marked_vowel_units':q['explicit_tone_units'],'written_vowel_units':q['vowel_units'],'explicit_mark_density':r['explicit_mark_rate'],
          'phonetic_features':features,'feature_evidence':'Orthographic features for planned comparison; not segment-aligned acoustic findings.',
          'selection_reason':reason,'acoustic_reliability':a,'status':'PROPOSED_PENDING_USER_APPROVAL','ai_generation':'NOT_AUTHORIZED_OR_RUN'})
    dump(out/'paired_sentence_proposals.json',{'selection':'Six distinct speakers; high-confidence matches; no notes, source-event tags, unusual underdots, observed near-floor or octave flags. Not claimed acoustically perfect. Four released female/two male speaker IDs; not population balanced.',
      'items':proposals,'scope':'One matching text per natural recording; preserve source text exactly; later alignment must account for content and speaker normalization.'})
    print(json.dumps({'counts':counts,'output':str(out),'proposals':proposals},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
